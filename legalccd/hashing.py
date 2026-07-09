"""
legalccd.hashing
----------------
Cálculo de hashes criptográficos sobre archivos y texto.
Diseñado para cadena de custodia de vestigios digitales.

Algoritmos soportados: SHA-256 (por defecto), MD5, SHA-1, SHA-512.
Nota: MD5 y SHA-1 se incluyen por compatibilidad con sistemas
heredados. Para cadena de custodia judicial se recomienda SHA-256.
Referencia normativa: ISO/IEC 27037:2012.
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ALGORITMOS = {
    "SHA-256": "sha256",
    "MD5":     "md5",
    "SHA-1":   "sha1",
    "SHA-512": "sha512",
}

ALGORITMO_POR_DEFECTO = "SHA-256"
CHUNK_SIZE = 65536  # 64 KB — eficiente para archivos grandes


def calcular_hash_archivo(
    ruta: str | Path,
    algoritmos: list[str] | None = None,
    callback_progreso=None,
) -> dict:
    """
    Calcula el hash de un archivo para uno o varios algoritmos.

    Parámetros
    ----------
    ruta : str | Path
        Ruta al archivo.
    algoritmos : list[str] | None
        Lista de nombres de algoritmos (ej. ["SHA-256", "MD5"]).
        Si es None, usa el algoritmo por defecto.
    callback_progreso : callable | None
        Función (bytes_leídos, total_bytes) para actualizar progreso.

    Devuelve
    --------
    dict con claves:
        hashes      : {algoritmo: valor_hex}
        nombre      : nombre del archivo con extensión
        tamaño      : tamaño en bytes
        tamaño_fmt  : tamaño legible (KB, MB…)
        timestamp   : ISO 8601 UTC
        error       : None o mensaje de error
    """
    if algoritmos is None:
        algoritmos = [ALGORITMO_POR_DEFECTO]

    resultado = {
        "hashes": {},
        "nombre": "",
        "tamaño": 0,
        "tamaño_fmt": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }

    ruta = Path(ruta)
    try:
        tamaño = ruta.stat().st_size
        resultado["nombre"] = ruta.name
        resultado["tamaño"] = tamaño
        resultado["tamaño_fmt"] = _formato_tamaño(tamaño)

        hashes_activos = {}
        for algo in algoritmos:
            nombre_interno = ALGORITMOS.get(algo)
            if nombre_interno:
                hashes_activos[algo] = hashlib.new(nombre_interno)

        bytes_leídos = 0
        with open(ruta, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                for h in hashes_activos.values():
                    h.update(chunk)
                bytes_leídos += len(chunk)
                if callback_progreso:
                    callback_progreso(bytes_leídos, tamaño)

        resultado["hashes"] = {
            algo: h.hexdigest() for algo, h in hashes_activos.items()
        }

    except PermissionError:
        resultado["error"] = "Sin permiso para leer el archivo."
    except FileNotFoundError:
        resultado["error"] = "Archivo no encontrado."
    except Exception as e:
        resultado["error"] = str(e)

    return resultado


def calcular_hash_texto(
    texto: str,
    algoritmos: list[str] | None = None,
) -> dict:
    """
    Calcula el hash de una cadena de texto (codificada en UTF-8).

    Parámetros
    ----------
    texto : str
    algoritmos : list[str] | None

    Devuelve
    --------
    dict con claves:
        hashes    : {algoritmo: valor_hex}
        timestamp : ISO 8601 UTC
        error     : None o mensaje de error
    """
    if algoritmos is None:
        algoritmos = [ALGORITMO_POR_DEFECTO]

    resultado = {
        "hashes": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }

    try:
        datos = texto.encode("utf-8")
        for algo in algoritmos:
            nombre_interno = ALGORITMOS.get(algo)
            if nombre_interno:
                resultado["hashes"][algo] = hashlib.new(nombre_interno, datos).hexdigest()
    except Exception as e:
        resultado["error"] = str(e)

    return resultado


def _formato_tamaño(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} bytes"
    elif bytes_ < 1_048_576:
        return f"{bytes_ / 1024:.1f} KB"
    elif bytes_ < 1_073_741_824:
        return f"{bytes_ / 1_048_576:.2f} MB"
    else:
        return f"{bytes_ / 1_073_741_824:.3f} GB"
