"""
benchmark_hashing_v2.py  (Experimento E6)
-----------------------------------------
Versión metodológicamente reforzada del benchmark de hashing para la
sección de resultados de la tesis y del artículo IEEE Access.

Mejoras respecto a benchmark_hashing.py (v1):
  1. CALENTAMIENTO: antes de medir, cada archivo se lee una vez completa
     para poblar la caché de disco del SO. Elimina el efecto de arranque
     en frío que distorsionaba la primera medición (p. ej. SHA-256 a
     1 MB con desviación mayor que la media en la v1).
  2. 30 REPETICIONES por combinación algoritmo x tamaño (antes 5),
     suficiente para intervalos de confianza estables.
  3. ESTADÍSTICOS ROBUSTOS: media, mediana, desviación típica, IC 95 %
     de la media (t de Student) y throughput calculado sobre la mediana.
  4. TRAZABILIDAD: registra fecha, versión de Python y plataforma en
     una fila de comentario del CSV (reproducibilidad, ISO/IEC 27041).

Uso (desde la raíz del proyecto LegalCCD):
    python benchmark_hashing_v2.py                 # completo (~10-15 min)
    python benchmark_hashing_v2.py --rapido        # prueba rápida

Salida: benchmark_hashing_v2.csv
"""

import csv
import math
import os
import platform
import statistics
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from legalccd.hashing import calcular_hash_archivo

TAMANIOS_MB = [1, 10, 100, 500, 1024]
TAMANIOS_MB_RAPIDO = [1, 10]
ALGORITMOS = ["SHA-256", "SHA-512", "SHA-1", "MD5"]
REPETICIONES = 30
CSV_SALIDA = Path("benchmark_hashing_v2.csv")

# Valor crítico t de Student (dos colas, alfa=0.05) para gl = n-1.
# Para n=30 (gl=29): 2.045. Se tabulan valores por si cambia REPETICIONES.
T_CRITICO = {4: 2.776, 9: 2.262, 14: 2.145, 19: 2.093, 29: 2.045, 49: 2.010}


def t_critico(gl: int) -> float:
    """Devuelve el valor t más próximo tabulado (conservador)."""
    claves = sorted(T_CRITICO)
    for k in claves:
        if gl <= k:
            return T_CRITICO[k]
    return 1.96  # aproximación normal para muestras grandes


def crear_archivo(tam_mb: int, carpeta: Path) -> Path:
    ruta = carpeta / f"sintetico_{tam_mb}MB.bin"
    bloque = os.urandom(1024 * 1024)
    with ruta.open("wb") as f:
        for _ in range(tam_mb):
            f.write(bloque)
    return ruta


def calentar(ruta: Path) -> None:
    """Lee el archivo completo una vez para poblar la caché del SO."""
    with ruta.open("rb") as f:
        while f.read(8 * 1024 * 1024):
            pass


def main() -> None:
    rapido = "--rapido" in sys.argv
    tamanios = TAMANIOS_MB_RAPIDO if rapido else TAMANIOS_MB
    reps = 5 if rapido else REPETICIONES

    filas = []
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        for tam in tamanios:
            print(f"Generando archivo sintético de {tam} MB ...")
            ruta = crear_archivo(tam, carpeta)
            calentar(ruta)
            for alg in ALGORITMOS:
                # descarte adicional: una ejecución no medida por algoritmo
                calcular_hash_archivo(ruta, [alg])
                tiempos = []
                for _ in range(reps):
                    t0 = time.perf_counter()
                    res = calcular_hash_archivo(ruta, [alg])
                    tiempos.append(time.perf_counter() - t0)
                    if res.get("error"):
                        raise RuntimeError(res["error"])
                media = statistics.mean(tiempos)
                mediana = statistics.median(tiempos)
                desv = statistics.stdev(tiempos) if len(tiempos) > 1 else 0.0
                semi_ic = t_critico(len(tiempos) - 1) * desv / math.sqrt(len(tiempos))
                fila = {
                    "algoritmo": alg,
                    "tam_mb": tam,
                    "repeticiones": len(tiempos),
                    "t_medio_s": round(media, 5),
                    "t_mediana_s": round(mediana, 5),
                    "desv_s": round(desv, 5),
                    "ic95_semiamplitud_s": round(semi_ic, 5),
                    "throughput_mediana_mb_s": round(tam / mediana, 1),
                    "throughput_medio_mb_s": round(tam / media, 1),
                }
                filas.append(fila)
                print(
                    f"  {alg:8s} {tam:5d} MB  mediana={mediana:.4f}s "
                    f"(IC95 ±{semi_ic:.4f})  "
                    f"throughput={fila['throughput_mediana_mb_s']} MB/s"
                )

    with CSV_SALIDA.open("w", newline="", encoding="utf-8") as f:
        f.write(
            f"# benchmark_hashing_v2 | {datetime.now(timezone.utc).isoformat(timespec='seconds')}"
            f" | Python {platform.python_version()} | {platform.platform()}\n"
        )
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    print(f"\nResultados guardados en {CSV_SALIDA.resolve()}")
    print("Envía este CSV para generar las tablas y figuras de la tesis.")


if __name__ == "__main__":
    main()
