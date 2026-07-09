"""
medir_cardano.py
----------------
Experimento para la sección de evaluación del artículo (y de la tesis):
envía N registros de cadena de custodia a la testnet preprod de Cardano
y mide, por transacción:

  - t_envio_s          : latencia de construcción+firma+submit
  - t_confirmacion_s   : latencia hasta inclusión en bloque
  - fee_lovelace       : comisión pagada
  - txid, bloque       : trazabilidad pública (verificable en
                         https://preprod.cardanoscan.io/transaction/<txid>)

Resultados: mediciones_cardano.csv + resumen estadístico por pantalla.

Uso:
    python medir_cardano.py            # 10 transacciones (por defecto)
    python medir_cardano.py 30         # 30 transacciones
    python medir_cardano.py 30 60      # 30 transacciones, pausa 60 s entre ellas

Nota metodológica: cada transacción consume ~0.17-0.20 tADA de fee y
bloquea 1 tADA que vuelve como cambio. Con 100 tADA del faucet hay
margen de sobra para 30-50 mediciones. La pausa entre transacciones
evita encadenar UTxOs sin confirmar.
"""

import csv
import hashlib
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from legalccd.cardano import registrar_en_cardano
from legalccd.registro import Registro

CSV_SALIDA = Path("mediciones_cardano.csv")


def payload_sintetico(i: int) -> dict:
    """
    Genera un registro sintético realista: el 'vestigio' es un contenido
    único por iteración, del que se calcula el SHA-256 igual que haría
    la aplicación con un archivo real.
    """
    contenido = f"LegalCCD-experimento-{i}-{time.time_ns()}".encode()
    h = hashlib.sha256(contenido).hexdigest()
    r = Registro(
        id_vestigio=f"VD-EXP-{i:03d}",
        hashes={"SHA-256": h},
    )
    p = r.payload_blockchain()
    p["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return p


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    pausa = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    print(f"Experimento: {n} transacciones en preprod, pausa {pausa}s\n")
    filas = []
    for i in range(1, n + 1):
        p = payload_sintetico(i)
        print(f"[{i}/{n}] enviando registro {p['id']} ...", flush=True)
        res = registrar_en_cardano(p, esperar_confirmacion=True)
        if not res.exito:
            print(f"    ERROR: {res.mensaje}")
            filas.append({"n": i, "exito": False, "error": res.mensaje})
        else:
            print(
                f"    TxID {res.txid[:16]}...  "
                f"envio={res.t_envio_s}s  conf={res.t_confirmacion_s}s  "
                f"fee={res.fee_lovelace} lovelace  bloque={res.bloque}"
            )
            filas.append(
                {
                    "n": i,
                    "exito": True,
                    "txid": res.txid,
                    "bloque": res.bloque,
                    "t_envio_s": res.t_envio_s,
                    "t_confirmacion_s": res.t_confirmacion_s,
                    "fee_lovelace": res.fee_lovelace,
                    "id_registro": p["id"],
                    "timestamp": p["ts"],
                }
            )
        if i < n:
            time.sleep(pausa)

    campos = [
        "n", "exito", "txid", "bloque", "t_envio_s",
        "t_confirmacion_s", "fee_lovelace", "id_registro",
        "timestamp", "error",
    ]
    with CSV_SALIDA.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print(f"\nResultados guardados en {CSV_SALIDA.resolve()}")

    ok = [f for f in filas if f.get("exito")]
    if ok:
        for metrica, clave in [
            ("Latencia de envío (s)", "t_envio_s"),
            ("Latencia de confirmación (s)", "t_confirmacion_s"),
            ("Fee (lovelace)", "fee_lovelace"),
        ]:
            vals = [f[clave] for f in ok if f.get(clave) is not None]
            if vals:
                print(
                    f"{metrica:32s} n={len(vals)}  "
                    f"media={statistics.mean(vals):.2f}  "
                    f"mediana={statistics.median(vals):.2f}  "
                    f"min={min(vals):.2f}  max={max(vals):.2f}  "
                    f"desv={statistics.stdev(vals):.2f}" if len(vals) > 1 else
                    f"{metrica}: {vals[0]}"
                )
        print(f"\nTasa de éxito: {len(ok)}/{n} ({100*len(ok)/n:.1f}%)")


if __name__ == "__main__":
    main()
