"""
legalccd.registro
-----------------
Modelo de datos para un registro de vestigio digital
y generación del reporte de texto exportable.

Los datos que se guardan en el reporte local pueden incluir
información personal (nombre del actuante, descripción del caso, etc.)
porque el reporte NUNCA se envía a la red blockchain.

Lo que se enviará a Cardano en la v0.2 es exclusivamente:
  - id_registro
  - id_vestigio
  - hashes criptográficos
  - timestamp UTC
  - algoritmos utilizados
Sin ningún dato personal ni contenido del vestigio.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class Registro:
    # Identificación
    id_registro: str = field(default_factory=lambda: "LCD-" + uuid.uuid4().hex[:12].upper())
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Datos del caso (solo reporte local)
    num_caso: str = ""
    desc_caso: str = ""
    fecha_acto: str = ""
    hora_acto: str = ""

    # Datos del vestigio
    id_vestigio: str = ""
    tipo_vestigio: str = ""
    desc_vestigio: str = ""

    # Datos del archivo (si aplica)
    nombre_archivo: str = ""      # con extensión
    tamaño_archivo: str = ""      # formato legible
    tamaño_bytes: int = 0

    # Modo de entrada
    modo_entrada: str = ""        # "archivo" | "texto" | "hash_manual"
    origen_hash: str = ""         # si se introduce manualmente

    # Hashes
    hashes: dict = field(default_factory=dict)  # {algoritmo: hex}

    # Datos del actuante (solo reporte local)
    nombre_actuante: str = ""
    id_profesional: str = ""
    rol: str = ""
    num_control: str = ""

    # Otros datos adicionales (solo reporte local)
    otros_datos: str = ""

    # Estado Cardano (se rellenará en v0.2)
    cardano_txid: Optional[str] = None
    cardano_red: str = "preprod"
    cardano_estado: str = "pendiente"

    def payload_blockchain(self) -> dict:
        """
        Datos que se enviarán a Cardano.
        Sin datos personales ni contenido del vestigio.
        Tamaño optimizado para caber en metadatos nativos de Cardano (< 64 bytes por valor).
        """
        return {
            "app": "LegalCCD",
            "v": "0.2",
            "id": self.id_registro,
            "vid": self.id_vestigio,
            "ts": self.timestamp_utc,
            "hashes": self.hashes,
        }

    def a_dict(self) -> dict:
        return asdict(self)

    def a_json(self) -> str:
        return json.dumps(self.a_dict(), ensure_ascii=False, indent=2)


def generar_reporte_txt(r: Registro) -> str:
    """
    Genera el texto del reporte exportable (.txt).
    Incluye todos los campos cumplimentados.
    """
    SEP = "=" * 62
    SEP2 = "-" * 62
    lineas = []

    def campo(clave, valor):
        if valor:
            lineas.append(f"  {clave:<28} {valor}")

    lineas += [
        SEP,
        "  LEGALCCD — REGISTRO DE VESTIGIO DIGITAL",
        "  Sistema de Cadena de Custodia Digital · v0.2",
        SEP,
        "",
        "  IDENTIFICACIÓN DEL REGISTRO",
        SEP2,
    ]
    campo("ID de registro", r.id_registro)
    campo("Generado (UTC)", r.timestamp_utc)
    if r.fecha_acto or r.hora_acto:
        campo("Fecha y hora del acto", f"{r.fecha_acto}  {r.hora_acto}".strip())

    lineas += ["", "  DATOS DEL CASO", SEP2]
    campo("Número de caso", r.num_caso)
    campo("Descripción del caso", r.desc_caso)

    lineas += ["", "  VESTIGIO DIGITAL", SEP2]
    campo("Identificador del vestigio", r.id_vestigio)
    campo("Tipo", r.tipo_vestigio)
    campo("Descripción", r.desc_vestigio)
    campo("Modo de entrada", r.modo_entrada)

    if r.nombre_archivo:
        lineas += ["", "  ARCHIVO", SEP2]
        campo("Nombre (con extensión)", r.nombre_archivo)
        campo("Tamaño", r.tamaño_archivo)
        campo("Tamaño (bytes exactos)", str(r.tamaño_bytes) if r.tamaño_bytes else "")

    if r.origen_hash:
        campo("Origen del hash", r.origen_hash)

    lineas += ["", "  VALORES HASH", SEP2]
    if r.hashes:
        for algo, valor in r.hashes.items():
            lineas.append(f"  {algo:<28} {valor}")
    else:
        lineas.append("  (sin hashes registrados)")

    lineas += ["", "  ACTUANTE", SEP2]
    campo("Nombre y apellidos", r.nombre_actuante)
    campo("Identificador profesional", r.id_profesional)
    campo("Rol", r.rol)
    campo("Número de control", r.num_control)

    if r.otros_datos:
        lineas += ["", "  OTROS DATOS / OBSERVACIONES", SEP2]
        for linea in r.otros_datos.splitlines():
            lineas.append(f"  {linea}")

    lineas += ["", "  ESTADO EN BLOCKCHAIN", SEP2]
    campo("Red Cardano", r.cardano_red)
    campo("TxID", r.cardano_txid or "pendiente")
    campo("Estado", r.cardano_estado)
    if r.cardano_txid:
        sub = "preprod." if r.cardano_red == "preprod" else ("preview." if r.cardano_red == "preview" else "")
        campo("Verificación pública", f"https://{sub}cardanoscan.io/transaction/{r.cardano_txid}")

    lineas += [
        "",
        SEP,
        "  NOTA DE PRIVACIDAD",
        SEP2,
        "  Este reporte se almacena exclusivamente en local.",
        "  Los hashes son funciones unidireccionales: no permiten",
        "  reconstruir el contenido del vestigio original.",
        "  Los datos personales de este reporte NUNCA se envían",
        "  a la red blockchain.",
        SEP,
    ]

    return "\n".join(lineas)


# Carpeta de autoguardado de reportes (junto a la aplicación)
CARPETA_REGISTROS = Path(__file__).resolve().parent.parent / "REGISTROS"


def guardar_reporte(r: Registro, carpeta: str | Path | None = None) -> Path:
    """
    Guarda el reporte .txt. Devuelve la ruta.
    Si no se indica carpeta, usa ./REGISTROS (autoguardado).
    El nombre incluye fecha y hora local para ordenación cronológica:
        LegalCCD_YYYYMMDD_HHMMSS_<id_registro>_<num_caso>.txt
    """
    carpeta = Path(carpeta) if carpeta else CARPETA_REGISTROS
    carpeta.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_caso = r.num_caso.replace("/", "-").replace(" ", "_") or "sin_caso"
    nombre = f"LegalCCD_{marca}_{r.id_registro}_{nombre_caso}.txt"
    ruta = carpeta / nombre
    ruta.write_text(generar_reporte_txt(r), encoding="utf-8")
    return ruta
