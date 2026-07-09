import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({
    "figure.dpi": 300, "savefig.dpi": 300,
    "font.size": 8, "font.family": "serif",
    "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.4,
})
def leer(path, salta_comentario=False):
    with open(path, newline="") as f:
        lineas = f.read().splitlines()
    if salta_comentario and lineas[0].startswith("#"):
        lineas = lineas[1:]
    r = csv.DictReader(lineas)
    return [ {k:(v.strip() if isinstance(v,str) else v) for k,v in row.items()} for row in r ]
bench = leer("benchmark_hashing_v2.csv", salta_comentario=True)
algos = ["SHA-256","SHA-512","SHA-1","MD5"]
tam = sorted({int(r["tam_mb"]) for r in bench})
marcadores = {"SHA-256":"o","SHA-512":"s","SHA-1":"^","MD5":"D"}
grises = {"SHA-256":"0.0","SHA-512":"0.35","SHA-1":"0.55","MD5":"0.7"}
fig, ax = plt.subplots(figsize=(3.4,2.4))
for a in algos:
    ys = []
    for t in tam:
        fila = next(r for r in bench if r["algoritmo"]==a and int(r["tam_mb"])==t)
        ys.append(float(fila["throughput_medio_mb_s"]))
    ax.plot(tam, ys, marker=marcadores[a], color=grises[a], label=a, linewidth=1.0, markersize=3.5)
ax.set_xscale("log")
ax.set_xlabel("File size (MB)")
ax.set_ylabel("Throughput (MB/s)")
ax.legend(fontsize=6, framealpha=0.9)
fig.tight_layout()
fig.savefig("fig_hashing.png", bbox_inches="tight")
plt.close(fig)
pil = leer("mediciones_cardano.csv")
ses = leer("mediciones_cardano_v2.csv")
conf = [float(r["t_confirmacion_s"]) for r in pil] + [float(r["t_confirmacion_s"]) for r in ses]
conf = np.array(conf); n = len(conf); media, mediana = conf.mean(), np.median(conf)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8,2.4))
ax1.plot(range(1,n+1), conf, color="0.3", linewidth=0.6, marker="o", markersize=1.8)
ax1.axhline(media, color="0.0", linestyle="--", linewidth=0.8, label=f"Mean {media:.1f} s")
ax1.axhline(mediana, color="0.0", linestyle=":", linewidth=0.8, label=f"Median {mediana:.1f} s")
ax1.set_xlabel("Transaction #"); ax1.set_ylabel("Confirmation latency (s)")
ax1.legend(fontsize=6, framealpha=0.9); ax1.set_title("(a)", fontsize=8)
xs = np.sort(conf); ys = np.arange(1,n+1)/n
ax2.step(xs, ys, color="0.0", linewidth=1.0, where="post")
ax2.set_xlabel("Confirmation latency (s)"); ax2.set_ylabel("Empirical CDF")
ax2.set_ylim(0,1.02); ax2.set_title("(b)", fontsize=8)
fig.tight_layout(); fig.savefig("fig_latencia.png", bbox_inches="tight"); plt.close(fig)
fp = leer("fee_payload.csv")
from collections import defaultdict
byh = defaultdict(list)
for r in fp: byh[int(r["n_hashes"])].append(int(r["fee_lovelace"]))
hs = sorted(byh); fees = [byh[h][0] for h in hs]
fig, ax = plt.subplots(figsize=(3.4,2.4))
ax.plot(hs, fees, marker="o", color="0.0", linewidth=1.0, markersize=4)
for h,fee in zip(hs,fees):
    ax.annotate(f"{fee:,}", (h,fee), textcoords="offset points", xytext=(0,6), ha="center", fontsize=6)
ax.set_xlabel("Number of anchored digests"); ax.set_ylabel("Fee (lovelace)")
ax.set_xticks(hs)
margen = (max(fees)-min(fees))*0.15
ax.set_ylim(min(fees)-margen, max(fees)+margen*2)
fig.tight_layout(); fig.savefig("fig_fee.png", bbox_inches="tight"); plt.close(fig)
print(f"OK. N={n}, media={media:.2f}, mediana={mediana:.2f}")
print("Generadas: fig_hashing.png, fig_latencia.png, fig_fee.png")
