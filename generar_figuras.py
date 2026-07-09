"""
generar_figuras.py
------------------
Genera las figuras del apartado de resultados (Cap. IX) a partir de los
CSV de los experimentos. Diseñadas para impresión: 300 dpi, escala de
grises compatible, rotulación en español.

Figuras:
  F1  throughput_hashing.png      throughput por algoritmo y tamaño (E6/v1)
  F2  latencia_confirmacion.png   distribución de latencias de confirmación (E1)
  F3  latencia_sesiones.png       boxplot de latencias por sesión/red (E1/E2, si hay columna 'sesion')
  F4  fees.png                    fee por transacción (y por configuración si existe fee_payload.csv)

Uso:
    python generar_figuras.py <benchmark.csv> <mediciones.csv> [fee_payload.csv]
Acepta tanto los CSV v1 como los v2 (detecta columnas).
"""

import csv
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.dpi": 300,
})

SALIDA = Path("figuras")
SALIDA.mkdir(exist_ok=True)

MARCADORES = {"SHA-256": "o", "SHA-512": "s", "SHA-1": "^", "MD5": "d"}
LINEAS = {"SHA-256": "-", "SHA-512": "--", "SHA-1": "-.", "MD5": ":"}


def leer_csv(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8") as f:
        lineas = [l for l in f if not l.startswith("#")]
    return list(csv.DictReader(lineas))


def f1_throughput(bench: list[dict]) -> None:
    col_thr = ("throughput_mediana_mb_s"
               if "throughput_mediana_mb_s" in bench[0] else "throughput_mb_s")
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    for alg in MARCADORES:
        filas = sorted(
            (r for r in bench if r["algoritmo"] == alg),
            key=lambda r: int(r["tam_mb"]),
        )
        if not filas:
            continue
        x = [int(r["tam_mb"]) for r in filas]
        y = [float(r[col_thr]) for r in filas]
        ax.plot(x, y, marker=MARCADORES[alg], linestyle=LINEAS[alg],
                color="black", markerfacecolor="white", label=alg)
    ax.set_xscale("log")
    ax.set_xlabel("Tamaño del archivo (MB, escala log.)")
    ax.set_ylabel("Throughput (MB/s)")
    ax.legend(frameon=False, ncols=2)
    fig.tight_layout()
    fig.savefig(SALIDA / "F1_throughput_hashing.png")
    plt.close(fig)
    print("F1_throughput_hashing.png")


def f2_latencias(med: list[dict]) -> None:
    confs = [float(r["t_confirmacion_s"]) for r in med
             if r.get("exito") in ("True", "true", "1") and r.get("t_confirmacion_s")]
    if not confs:
        return
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    ax.hist(confs, bins=12, color="0.75", edgecolor="black")
    mediana = statistics.median(confs)
    ax.axvline(mediana, color="black", linestyle="--",
               label=f"Mediana = {mediana:.1f} s")
    ax.set_xlabel("Latencia de confirmación (s)")
    ax.set_ylabel("Nº de transacciones")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(SALIDA / "F2_latencia_confirmacion.png")
    plt.close(fig)
    print(f"F2_latencia_confirmacion.png  (n={len(confs)}, mediana={mediana:.1f}s)")


def f3_sesiones(med: list[dict]) -> None:
    if "sesion" not in med[0]:
        return
    grupos, etiquetas = [], []
    claves = sorted({(r["sesion"], r.get("red", "")) for r in med})
    for ses, red in claves:
        vals = [float(r["t_confirmacion_s"]) for r in med
                if r["sesion"] == ses and r.get("red", "") == red
                and r.get("exito") in ("True", "true", "1") and r.get("t_confirmacion_s")]
        if vals:
            grupos.append(vals)
            etiquetas.append(f"{ses}\n({red})")
    if not grupos:
        return
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    bp = ax.boxplot(grupos, labels=etiquetas, patch_artist=True)
    for caja in bp["boxes"]:
        caja.set_facecolor("0.85")
    ax.set_ylabel("Latencia de confirmación (s)")
    ax.set_xlabel("Sesión (red)")
    fig.tight_layout()
    fig.savefig(SALIDA / "F3_latencia_sesiones.png")
    plt.close(fig)
    print("F3_latencia_sesiones.png")


def f4_fees(med: list[dict], fee_payload: list[dict] | None) -> None:
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    if fee_payload:
        confs = sorted({r["config"] for r in fee_payload})
        medias = []
        for c in confs:
            fees = [int(r["fee_lovelace"]) for r in fee_payload
                    if r["config"] == c and r.get("exito") in ("True", "true", "1")]
            medias.append(statistics.mean(fees) / 1e6 if fees else 0)
        ax.bar(confs, medias, color="0.8", edgecolor="black")
        ax.set_xlabel("Configuración de payload (nº de hashes)")
        ax.set_ylabel("Fee medio (ADA)")
    else:
        fees = [int(r["fee_lovelace"]) / 1e6 for r in med
                if r.get("exito") in ("True", "true", "1") and r.get("fee_lovelace")]
        ax.plot(range(1, len(fees) + 1), fees, marker="o", markersize=3,
                color="black", linestyle="none")
        ax.set_xlabel("Transacción (orden de envío)")
        ax.set_ylabel("Fee (ADA)")
        ax.set_ylim(0, max(fees) * 1.3)
    fig.tight_layout()
    fig.savefig(SALIDA / "F4_fees.png")
    plt.close(fig)
    print("F4_fees.png")


def main() -> None:
    if len(sys.argv) < 3:
        print("Uso: python generar_figuras.py <benchmark.csv> <mediciones.csv> [fee_payload.csv]")
        sys.exit(1)
    bench = leer_csv(Path(sys.argv[1]))
    med = leer_csv(Path(sys.argv[2]))
    fee = leer_csv(Path(sys.argv[3])) if len(sys.argv) > 3 else None
    f1_throughput(bench)
    f2_latencias(med)
    f3_sesiones(med)
    f4_fees(med, fee)
    print(f"\nFiguras en {SALIDA.resolve()}")


if __name__ == "__main__":
    main()
