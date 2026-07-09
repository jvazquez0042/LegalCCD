"""
legalccd.cardano  (v0.2 - implementación real)
----------------------------------------------
Integración con la red Cardano vía Blockfrost + PyCardano.

Mantiene la API pública de la v0.1:
    registrar_en_cardano(payload) -> ResultadoCardano
    verificar_txid(txid)          -> ResultadoCardano

Diseño (justificación en la especificación técnica y en la tesis):
- El payload se registra como METADATO NATIVO de transacción con el
  label 1984 (reservado por convención para LegalCCD). No se usan
  smart contracts Plutus: para un registro de integridad append-only
  los metadatos nativos son suficientes, más baratos y más simples
  de auditar.
- La transacción es un auto-envío (self-send) del importe mínimo de
  UTxO a la propia dirección del sistema: el único propósito de la
  transacción es anclar los metadatos en la cadena.
- El payload NO contiene datos personales (RGPD by design): solo
  id de registro, id de vestigio, timestamp UTC y hashes.
- Límite del protocolo: cada cadena de texto en metadatos <= 64 bytes.
  SHA-256 en hex son exactamente 64 caracteres ASCII = 64 bytes: OK.
  SHA-512 en hex son 128 caracteres: se fragmenta en una lista de dos
  cadenas de 64 (fragmentación estándar, reversible por concatenación).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

METADATA_LABEL = 1984
MAX_BYTES_METADATO = 64


@dataclass
class ResultadoCardano:
    exito: bool
    txid: Optional[str] = None
    red: str = "preprod"
    mensaje: str = ""
    bloque: Optional[int] = None
    # v0.2: métricas para evaluación experimental
    fee_lovelace: Optional[int] = None          # comisión pagada
    t_envio_s: Optional[float] = None           # latencia de submit
    t_confirmacion_s: Optional[float] = None    # latencia hasta bloque
    metadatos: Optional[dict] = None            # metadatos recuperados (verificación)


# ---------------------------------------------------------------------------
# Utilidades de payload
# ---------------------------------------------------------------------------

def _fragmentar(valor: str) -> "str | list[str]":
    """
    Cardano limita cada string de metadatos a 64 bytes.
    Si el valor excede el límite se devuelve una lista de fragmentos
    de 64 caracteres (convención habitual, p. ej. CIP-25).
    """
    if len(valor.encode("utf-8")) <= MAX_BYTES_METADATO:
        return valor
    return [valor[i : i + MAX_BYTES_METADATO]
            for i in range(0, len(valor), MAX_BYTES_METADATO)]


def preparar_metadatos(payload: dict) -> dict:
    """
    Adapta el payload de Registro.payload_blockchain() al formato de
    metadatos de Cardano (label 1984), fragmentando valores largos.
    """
    hashes = {alg: _fragmentar(h) for alg, h in payload.get("hashes", {}).items()}
    plano = {
        "app": payload.get("app", "LegalCCD"),
        "v": payload.get("v", "0.2"),
        "id": _fragmentar(str(payload.get("id", ""))),
        "vid": _fragmentar(str(payload.get("vid", ""))),
        "ts": str(payload.get("ts", "")),
        "hashes": hashes,
    }
    return {METADATA_LABEL: plano}


# ---------------------------------------------------------------------------
# Contexto de cadena (Blockfrost)
# ---------------------------------------------------------------------------

_contexto_cache = None


def _contexto():
    """Crea (y cachea) el contexto de cadena de PyCardano sobre Blockfrost."""
    global _contexto_cache
    if _contexto_cache is not None:
        return _contexto_cache

    from pycardano import BlockFrostChainContext
    from legalccd.config import cargar_config

    cfg = cargar_config()
    _contexto_cache = BlockFrostChainContext(
        project_id=cfg["project_id"],
        base_url=cfg["base_url"],
    )
    return _contexto_cache


def _api_blockfrost():
    """Cliente Blockfrost de bajo nivel (consultas de verificación)."""
    from blockfrost import BlockFrostApi
    from legalccd.config import cargar_config

    cfg = cargar_config()
    return BlockFrostApi(project_id=cfg["project_id"], base_url=cfg["base_url"]), cfg


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def estado_conexion() -> "tuple[bool, str]":
    """Comprueba la conectividad con la red Cardano vía Blockfrost.

    Devuelve (conectado, mensaje). No lanza excepciones: cualquier fallo
    (sin config, sin red, API caída) se traduce en (False, motivo), para
    que la interfaz pueda reflejar el estado sin interrumpirse.
    """
    try:
        from legalccd.config import cargar_config
        cfg = cargar_config()
        api, _ = _api_blockfrost()
        api.health()  # endpoint /health de Blockfrost
        return True, f"Conectado · {cfg['red']}"
    except Exception as e:  # noqa: BLE001  (queremos degradar con gracia)
        return False, f"Sin conexión ({type(e).__name__})"


def saldo_lovelace() -> int:
    """Saldo disponible (en lovelace; 1 ADA = 1_000_000 lovelace)."""
    from legalccd.config import cargar_config
    from legalccd.wallet import direccion

    cfg = cargar_config()
    contexto = _contexto()
    utxos = contexto.utxos(str(direccion(cfg["red"])))
    return sum(u.output.amount.coin for u in utxos)


def registrar_en_cardano(
    payload: dict,
    esperar_confirmacion: bool = True,
    timeout_confirmacion_s: int = 600,
) -> ResultadoCardano:
    """
    Registra el payload como metadato nativo (label 1984) en una
    transacción de auto-envío y devuelve el TxID.

    Si esperar_confirmacion=True, sondea Blockfrost hasta que la
    transacción aparece en un bloque (o vence el timeout) y devuelve
    también la latencia de confirmación, dato usado en la evaluación
    experimental del sistema.
    """
    try:
        from pycardano import (
            AlonzoMetadata,
            AuxiliaryData,
            Metadata,
            TransactionBuilder,
            TransactionOutput,
        )
        from legalccd.config import cargar_config
        from legalccd.wallet import cargar_wallet, direccion

        cfg = cargar_config()
        contexto = _contexto()
        skey = cargar_wallet()
        addr = direccion(cfg["red"])

        metadatos = preparar_metadatos(payload)
        aux = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadatos)))

        builder = TransactionBuilder(contexto)
        builder.add_input_address(addr)
        builder.auxiliary_data = aux
        # Auto-envío del mínimo práctico; el cambio vuelve a la misma dirección.
        builder.add_output(TransactionOutput(addr, 1_000_000))

        t0 = time.monotonic()
        tx_firmada = builder.build_and_sign([skey], change_address=addr)
        contexto.submit_tx(tx_firmada.to_cbor())
        t_envio = time.monotonic() - t0

        txid = str(tx_firmada.id)
        fee = int(tx_firmada.transaction_body.fee)

        resultado = ResultadoCardano(
            exito=True,
            txid=txid,
            red=cfg["red"],
            fee_lovelace=fee,
            t_envio_s=round(t_envio, 3),
            mensaje=f"Transacción enviada a {cfg['red']}. TxID: {txid}",
        )

        if esperar_confirmacion:
            bloque, t_conf = _esperar_confirmacion(
                txid, t0, timeout_confirmacion_s
            )
            resultado.bloque = bloque
            resultado.t_confirmacion_s = t_conf
            if bloque is not None:
                resultado.mensaje += f" Confirmada en el bloque {bloque}."
            else:
                resultado.mensaje += (
                    " Enviada pero aún sin confirmar dentro del timeout; "
                    "verifícala más tarde con verificar_txid()."
                )
        return resultado

    except Exception as e:  # noqa: BLE001 - mensaje claro hacia la GUI
        return ResultadoCardano(
            exito=False,
            red="preprod",
            mensaje=f"Error al registrar en Cardano: {type(e).__name__}: {e}",
        )


def _esperar_confirmacion(
    txid: str, t0: float, timeout_s: int
) -> tuple[Optional[int], Optional[float]]:
    """Sondea Blockfrost hasta que el TxID aparece en un bloque."""
    from blockfrost import ApiError

    api, _cfg = _api_blockfrost()
    intervalo = 5
    limite = time.monotonic() + timeout_s
    while time.monotonic() < limite:
        try:
            tx = api.transaction(txid)
            t_conf = round(time.monotonic() - t0, 3)
            return int(tx.block_height), t_conf
        except ApiError as e:
            if getattr(e, "status_code", None) == 404:
                time.sleep(intervalo)
                continue
            raise
    return None, None


def verificar_txid(txid: str) -> ResultadoCardano:
    """
    Verifica un TxID en la red: existencia, bloque y metadatos.
    Devuelve los metadatos recuperados para cotejarlos con el
    reporte local (verificación de integridad de la cadena de custodia).
    """
    try:
        from blockfrost import ApiError

        api, cfg = _api_blockfrost()
        try:
            tx = api.transaction(txid)
        except ApiError as e:
            if getattr(e, "status_code", None) == 404:
                return ResultadoCardano(
                    exito=False,
                    txid=txid,
                    red=cfg["red"],
                    mensaje="TxID no encontrado en la red (aún sin "
                            "confirmar o inexistente).",
                )
            raise

        metadatos = None
        try:
            md = api.transaction_metadata(txid)
            for item in md:
                if str(item.label) == str(METADATA_LABEL):
                    metadatos = _a_dict(item.json_metadata)
        except ApiError:
            pass

        return ResultadoCardano(
            exito=True,
            txid=txid,
            red=cfg["red"],
            bloque=int(tx.block_height),
            metadatos=metadatos,
            mensaje=f"Transacción confirmada en el bloque {tx.block_height}.",
        )
    except Exception as e:  # noqa: BLE001
        return ResultadoCardano(
            exito=False,
            txid=txid,
            mensaje=f"Error al verificar TxID: {type(e).__name__}: {e}",
        )


def _a_dict(obj):
    """Convierte los Namespace de blockfrost-python a dict/list planos."""
    if hasattr(obj, "__dict__"):
        return {k: _a_dict(v) for k, v in vars(obj).items()}
    if isinstance(obj, list):
        return [_a_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _a_dict(v) for k, v in obj.items()}
    return obj
