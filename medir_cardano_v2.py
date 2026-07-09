"""
medir_cardano_v2.py  (Experimentos E1 y E2)
-------------------------------------------
Versión ampliada de medir_cardano.py para el estudio experimental
definitivo de la tesis. Cambios respecto a la v1:

  1. SESIONES: cada ejecución se etiqueta (--sesion S1, S2, ...) y se
     AÑADE al CSV acumulado sin sobrescribir. Permite repartir las
     mediciones en distintos días y franjas horarias para capturar la
     variabilidad temporal de la red (requisito de validez externa).
  2. RED: registra la red usada (preprod / preview) leída de
     config.json. Para el experimento E2, cambia "red" a "preview" en
     config.json (necesitas un project_id de Blockfrost para preview y
     fondos del faucet de preview) y ejecuta 30 transacciones.
  3. HASH ENVIADO: guarda el SHA-256 enviado en cada registro para que
     medir_verificacion.py pueda cotejar el metadato recuperado de la
     cadena con el valor original (verificación extremo a extremo).

Plan de sesiones recomendado (E1, preprod):
    S1: 25 tx, día laborable por la mañana   -> python medir_cardano_v2.py 25 30 --sesion S1
    S2: 25 tx, día laborable por la tarde    -> python medir_cardano_v2.py 25 30 --sesion S2
    S3: 25 tx, fin de semana                 -> python medir_cardano_v2.py 25 30 --sesion S3
    (con las 30 tx ya existentes: N total >= 100)

Plan E2 (preview): cambiar red en config.json y:
    P1: 30 tx                                -> python medir_cardano_v2.py 30 30 --sesion P1

Salida: mediciones_cardano_v2.csv (acumulativo)
"""

import csv
import hashlib
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from legalccd.cardano import registrar_en_cardano
from legalccd.config import cargar_config
from legalccd.registro import Registro

CSV_SALIDA = Path("mediciones_cardano_v2.csv")

CAMPOS = [
    "sesion", "red", "n", "exito", "txid", "bloque",
    "t_envio_s", "t_confirmacion_s", "fee_lovelace",
    "id_registro", "hash_sha256", "timestamp", "error",
]


def payload_sintetico(i: int) -> tuple[dict, str]:
    contenido = f"LegalCCD-exp-v2-{i}-{time.time_ns()}".encode()
    h = hashlib.sha256(contenido).hexdigest()
    r = Registro(id_vestigio=f"VD-EXP-{i:03d}", hashes={"SHA-256": h})
    p = r.payload_blockchain()
    p["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return p, h


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(args[0]) if len(args) > 0 else 25
    pausa = int(args[1]) if len(args) > 1 else 30

    sesion = "S?"
    if "--sesion" in sys.argv:
        sesion = sys.argv[sys.argv.index("--sesion") + 1]

    red = cargar_config()["red"]
    print(f"Experimento: {n} tx en {red}, sesión {sesion}, pausa {pausa}s\n")

    nueva = not CSV_SALIDA.exists()
    filas = []
    for i in range(1, n + 1):
        p, h = payload_sintetico(i)
        print(f"[{i}/{n}] enviando registro {p['id']} ...", flush=True)
        res = registrar_en_cardano(p, esperar_confirmacion=True)
        fila = {
            "sesion": sesion,
            "red": red,
            "n": i,
            "exito": res.exito,
            "txid": res.txid or "",
            "bloque": res.bloque or "",
            "t_envio_s": res.t_envio_s or "",
            "t_confirmacion_s": res.t_confirmacion_s or "",
            "fee_lovelace": res.fee_lovelace or "",
            "id_registro": p["id"],
            "hash_sha256": h,
            "timestamp": p["ts"],
            "error": "" if res.exito else res.mensaje,
        }
        filas.append(fila)
        if res.exito:
            print(
                f"    TxID {res.txid[:16]}...  envio={res.t_envio_s}s  "
                f"conf={res.t_confirmacion_s}s  fee={res.fee_lovelace}"
            )
        else:
            print(f"    ERROR: {res.mensaje}")
        if i < n:
            time.sleep(pausa)

    with CSV_SALIDA.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if nueva:
            w.writeheader()
        w.writerows(filas)

    ok = [x for x in filas if x["exito"]]
    if ok:
        confs = [x["t_confirmacion_s"] for x in ok if x["t_confirmacion_s"]]
        print(f"\nSesión {sesion} ({red}): {len(ok)}/{n} éxitos")
        if confs:
            print(
                f"Confirmación: media={statistics.mean(confs):.1f}s  "
                f"mediana={statistics.median(confs):.1f}s  "
                f"min={min(confs):.1f}  max={max(confs):.1f}"
            )
    print(f"Resultados añadidos a {CSV_SALIDA.resolve()}")


if __name__ == "__main__":
    main()
