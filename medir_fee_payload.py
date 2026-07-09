"""
medir_fee_payload.py  (Experimento E5)
--------------------------------------
Mide la relación entre el tamaño del payload de metadatos y la comisión
(fee) pagada. Sustenta la sección de viabilidad económica de la tesis:
el fee en Cardano es determinista (a + b·tamaño_tx), de modo que el
coste por registro es predecible — a diferencia de los modelos de
subasta de gas (Ethereum).

Envía 3 transacciones por configuración (9 en total, ~1,6 tADA):
  C1: 1 hash  (SHA-256)                         payload mínimo
  C2: 2 hashes (SHA-256 + SHA-512 fragmentado)  payload medio
  C3: 4 hashes (SHA-256, SHA-512, SHA-1, MD5)   payload máximo de la app

Uso (desde la raíz del proyecto LegalCCD, red preprod):
    python medir_fee_payload.py

Salida: fee_payload.csv
"""

import csv
import hashlib
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from legalccd.cardano import registrar_en_cardano
from legalccd.registro import Registro

CSV_SALIDA = Path("fee_payload.csv")
PAUSA_S = 30
REPS = 3


def hashes_para(config: str, semilla: bytes) -> dict:
    h = {
        "SHA-256": hashlib.sha256(semilla).hexdigest(),
        "SHA-512": hashlib.sha512(semilla).hexdigest(),
        "SHA-1": hashlib.sha1(semilla).hexdigest(),
        "MD5": hashlib.md5(semilla).hexdigest(),
    }
    if config == "C1":
        return {"SHA-256": h["SHA-256"]}
    if config == "C2":
        return {"SHA-256": h["SHA-256"], "SHA-512": h["SHA-512"]}
    return h  # C3


def main() -> None:
    filas = []
    for config in ("C1", "C2", "C3"):
        for rep in range(1, REPS + 1):
            semilla = f"fee-exp-{config}-{rep}-{time.time_ns()}".encode()
            r = Registro(
                id_vestigio=f"VD-FEE-{config}-{rep}",
                hashes=hashes_para(config, semilla),
            )
            p = r.payload_blockchain()
            p["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            n_hashes = len(p["hashes"])
            print(f"[{config} rep {rep}] {n_hashes} hash(es) ... ", end="", flush=True)
            res = registrar_en_cardano(p, esperar_confirmacion=True)
            filas.append(
                {
                    "config": config,
                    "n_hashes": n_hashes,
                    "rep": rep,
                    "exito": res.exito,
                    "txid": res.txid or "",
                    "fee_lovelace": res.fee_lovelace or "",
                    "t_confirmacion_s": res.t_confirmacion_s or "",
                    "error": "" if res.exito else res.mensaje,
                }
            )
            print(f"fee={res.fee_lovelace} lovelace" if res.exito else f"ERROR {res.mensaje}")
            time.sleep(PAUSA_S)

    with CSV_SALIDA.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    print("\nResumen fee por configuración:")
    for config in ("C1", "C2", "C3"):
        fees = [x["fee_lovelace"] for x in filas if x["config"] == config and x["exito"]]
        if fees:
            print(
                f"  {config}: media={statistics.mean(fees):.0f} lovelace "
                f"({statistics.mean(fees)/1e6:.4f} ADA)  n={len(fees)}"
            )
    print(f"Resultados en {CSV_SALIDA.resolve()}")


if __name__ == "__main__":
    main()
