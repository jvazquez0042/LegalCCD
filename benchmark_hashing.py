"""
benchmark_hashing.py
--------------------
Mide el rendimiento del componente de adquisición (hashing local) para
la sección de evaluación del artículo: throughput (MB/s) por algoritmo
y tamaño de archivo.

Genera archivos sintéticos de distintos tamaños, calcula cada hash
`repeticiones` veces y guarda las medias en benchmark_hashing.csv.

Uso:
    python benchmark_hashing.py                # tamaños por defecto, 5 repeticiones
    python benchmark_hashing.py --rapido       # prueba rápida (tamaños pequeños)
"""

import csv
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

from legalccd.hashing import calcular_hash_archivo

TAMANIOS_MB = [1, 10, 100, 500, 1024]      # 1 MB .. 1 GB
TAMANIOS_MB_RAPIDO = [1, 10, 50]
ALGORITMOS = ["SHA-256", "SHA-512", "SHA-1", "MD5"]
REPETICIONES = 5
CSV_SALIDA = Path("benchmark_hashing.csv")


def crear_archivo(tam_mb: int, carpeta: Path) -> Path:
    ruta = carpeta / f"sintetico_{tam_mb}MB.bin"
    bloque = os.urandom(1024 * 1024)
    with ruta.open("wb") as f:
        for _ in range(tam_mb):
            f.write(bloque)
    return ruta


def main() -> None:
    rapido = "--rapido" in sys.argv
    tamanios = TAMANIOS_MB_RAPIDO if rapido else TAMANIOS_MB

    filas = []
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        for tam in tamanios:
            print(f"Generando archivo sintético de {tam} MB ...")
            ruta = crear_archivo(tam, carpeta)
            for alg in ALGORITMOS:
                tiempos = []
                for _ in range(REPETICIONES):
                    t0 = time.perf_counter()
                    res = calcular_hash_archivo(ruta, [alg])
                    tiempos.append(time.perf_counter() - t0)
                    if res.get("error"):
                        raise RuntimeError(res["error"])
                media = statistics.mean(tiempos)
                mbps = tam / media
                filas.append(
                    {
                        "algoritmo": alg,
                        "tam_mb": tam,
                        "t_medio_s": round(media, 4),
                        "desv_s": round(statistics.stdev(tiempos), 4)
                        if len(tiempos) > 1 else 0,
                        "throughput_mb_s": round(mbps, 1),
                        "repeticiones": REPETICIONES,
                    }
                )
                print(f"  {alg:8s} {tam:5d} MB  "
                      f"t={media:.3f}s  {mbps:.1f} MB/s")
            ruta.unlink()

    with CSV_SALIDA.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"\nResultados guardados en {CSV_SALIDA.resolve()}")


if __name__ == "__main__":
    main()
