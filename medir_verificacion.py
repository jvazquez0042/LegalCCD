"""
medir_verificacion.py  (Experimento E3)
---------------------------------------
Mide la operación con mayor relevancia judicial del sistema: la
VERIFICACIÓN independiente de un registro de custodia ya anclado en la
cadena. Para cada TxID previamente registrado:

  1. t_verificacion_s : latencia de recuperar la transacción y sus
     metadatos desde la red (vía Blockfrost).
  2. metadatos_ok     : si la transacción contiene metadatos con el
     label 1984 de LegalCCD.
  3. integridad_ok    : si el SHA-256 recuperado de la cadena coincide
     exactamente con el hash enviado en su día (cotejo extremo a
     extremo; requiere la columna hash_sha256 de mediciones_cardano_v2.csv;
     para las tx de la v1 se coteja solo el id_registro).

Este experimento sustenta el indicador jurídico central de la tesis:
cualquier tercero, sin acceso al sistema, puede verificar la integridad
del vestigio con el TxID y un explorador público.

Uso (desde la raíz del proyecto LegalCCD):
    python medir_verificacion.py mediciones_cardano_v2.csv
    python medir_verificacion.py mediciones_cardano.csv      # tx de la v1

IMPORTANTE: la red activa en config.json debe coincidir con la red en
la que se registraron las transacciones del CSV.

Salida: verificacion_<nombre_csv_entrada>
"""

import csv
import statistics
import sys
import time
from pathlib import Path

from legalccd.cardano import verificar_txid


def extraer_sha256(metadatos: dict) -> str:
    """Extrae y reconstruye el SHA-256 de los metadatos recuperados."""
    if not metadatos:
        return ""
    hashes = metadatos.get("hashes", {}) or {}
    valor = hashes.get("SHA-256", "")
    if isinstance(valor, list):  # valores fragmentados (>64 bytes)
        valor = "".join(valor)
    return str(valor)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python medir_verificacion.py <csv_de_mediciones>")
        sys.exit(1)

    entrada = Path(sys.argv[1])
    filas_in = [
        r for r in csv.DictReader(entrada.open(encoding="utf-8"))
        if r.get("txid") and r.get("exito", "True") in ("True", "true", "1")
    ]
    print(f"Verificando {len(filas_in)} transacciones de {entrada.name}\n")

    salida = Path(f"verificacion_{entrada.name}")
    filas_out = []
    for i, r in enumerate(filas_in, 1):
        txid = r["txid"]
        t0 = time.perf_counter()
        res = verificar_txid(txid)
        t = round(time.perf_counter() - t0, 3)

        sha_recuperado = extraer_sha256(res.metadatos) if res.exito else ""
        sha_original = r.get("hash_sha256", "")
        if sha_original:
            integridad = "OK" if sha_recuperado == sha_original else "FALLO"
        else:
            # CSV v1: no guardó el hash; cotejo por id de registro
            id_rec = str((res.metadatos or {}).get("id", ""))
            integridad = "OK(id)" if id_rec == r.get("id_registro", "") else "FALLO"

        filas_out.append(
            {
                "n": i,
                "txid": txid,
                "exito": res.exito,
                "t_verificacion_s": t,
                "metadatos_ok": bool(res.metadatos),
                "integridad": integridad,
                "bloque": res.bloque or "",
            }
        )
        print(f"[{i}/{len(filas_in)}] {txid[:16]}...  t={t}s  integridad={integridad}")
        time.sleep(0.3)  # cortesía con la API (límites del plan gratuito)

    with salida.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_out[0].keys()))
        w.writeheader()
        w.writerows(filas_out)

    tiempos = [x["t_verificacion_s"] for x in filas_out if x["exito"]]
    ok_int = sum(1 for x in filas_out if x["integridad"].startswith("OK"))
    print(f"\nVerificadas con éxito: {sum(1 for x in filas_out if x['exito'])}/{len(filas_out)}")
    print(f"Integridad correcta:   {ok_int}/{len(filas_out)}")
    if tiempos:
        print(
            f"Latencia verificación: media={statistics.mean(tiempos):.2f}s  "
            f"mediana={statistics.median(tiempos):.2f}s  "
            f"min={min(tiempos):.2f}  max={max(tiempos):.2f}"
        )
    print(f"Resultados en {salida.resolve()}")


if __name__ == "__main__":
    main()
