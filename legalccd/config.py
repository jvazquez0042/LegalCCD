"""
legalccd.config
---------------
Configuración de LegalCCD v0.2.

Lee config.json de la raíz del proyecto. Ejemplo:
{
    "blockfrost_project_id": "preprodXXXXXXXXXXXXXXXXXXXX",
    "red": "preprod"
}

El project_id se obtiene gratis en https://blockfrost.io
(crear cuenta -> Add project -> Network: Cardano preprod).
"""

import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CONFIG = RAIZ / "config.json"
DIR_CLAVES = RAIZ / "claves"

REDES_VALIDAS = ("preprod", "preview", "mainnet")

URLS_BLOCKFROST = {
    "preprod": "https://cardano-preprod.blockfrost.io/api",
    "preview": "https://cardano-preview.blockfrost.io/api",
    "mainnet": "https://cardano-mainnet.blockfrost.io/api",
}


class ConfigError(Exception):
    """Error de configuración con mensaje orientado al usuario."""


def cargar_config() -> dict:
    """
    Carga y valida config.json.
    Prioridad: variable de entorno BLOCKFROST_PROJECT_ID > config.json.
    """
    cfg = {}
    if RUTA_CONFIG.exists():
        try:
            cfg = json.loads(RUTA_CONFIG.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ConfigError(f"config.json no es un JSON válido: {e}")

    project_id = os.environ.get("BLOCKFROST_PROJECT_ID") or cfg.get(
        "blockfrost_project_id", ""
    )
    red = (cfg.get("red") or "preprod").lower()

    if red not in REDES_VALIDAS:
        raise ConfigError(f"Red '{red}' no válida. Usa una de: {REDES_VALIDAS}")

    if not project_id:
        raise ConfigError(
            "Falta el project_id de Blockfrost.\n"
            "1) Crea una cuenta gratuita en https://blockfrost.io\n"
            "2) Crea un proyecto para la red 'Cardano preprod'\n"
            "3) Copia el project_id en config.json "
            '(campo "blockfrost_project_id")'
        )

    if not project_id.startswith(red):
        raise ConfigError(
            f"El project_id no parece de la red '{red}' "
            f"(debería empezar por '{red}'). Revisa que el proyecto "
            f"de Blockfrost esté creado para 'Cardano {red}'."
        )

    return {
        "project_id": project_id,
        "red": red,
        "base_url": URLS_BLOCKFROST[red],
    }
