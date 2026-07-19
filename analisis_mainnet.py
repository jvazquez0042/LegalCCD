#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analisis_mainnet.py — Reproducible statistical analysis of the LegalCCD Cardano
mainnet external-validation campaign (experiment E8).

Recomputes every mainnet figure reported in the article from the raw CSV files,
with all statistical conventions fixed explicitly:

  * confirmation-latency variable: t_confirmacion_s
  * preprod reference sample (N = 105) = mediciones_cardano_v2.csv (75 session
    records, S1..S3) + mediciones_cardano.csv (30 pilot records)
  * mainnet sample (N = 30)          = mainnet/e8_mainnet_30_combinado.csv
  * difference is defined as   mean(mainnet) - mean(preprod)
  * Mann-Whitney U is computed with the mainnet sample passed FIRST
  * TOST uses Welch (unequal-variance) one-sided t-tests, margin = +/- 10 s,
    fixed a priori; the reported p is max(p_lower, p_upper)
  * bootstrap: percentile method, seed 42, 100000 resamples

Usage:
    python analisis_mainnet.py

Requires: numpy, pandas, scipy.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.abspath(__file__))
LAT = "t_confirmacion_s"
MARGIN = 10.0          # TOST equivalence margin (seconds), fixed a priori
SEED = 42
N_BOOT = 100_000


def load(path):
    full = os.path.join(BASE, path)
    if not os.path.exists(full):
        sys.exit(f"ERROR: file not found: {full}\n"
                 f"Run this script from the repository root.")
    return pd.read_csv(full)


def main():
    # ---- Load samples ---------------------------------------------------
    mainnet = load(os.path.join("mainnet", "e8_mainnet_30_combinado.csv"))
    pre_v2 = load("mediciones_cardano_v2.csv")   # 75 session records
    pre_v1 = load("mediciones_cardano.csv")      # 30 pilot records

    m = mainnet[LAT].astype(float).to_numpy()
    p = np.concatenate([pre_v2[LAT].astype(float).to_numpy(),
                        pre_v1[LAT].astype(float).to_numpy()])

    print("=" * 68)
    print("LegalCCD — mainnet external-validation campaign (E8)")
    print("=" * 68)
    print(f"mainnet sample size : {m.size}")
    print(f"preprod sample size : {p.size}")
    if m.size != 30 or p.size != 105:
        print("WARNING: expected 30 mainnet and 105 preprod observations.")

    # ---- Descriptives (mainnet) ----------------------------------------
    print("\n[1] Mainnet confirmation latency (s)")
    print(f"    median = {np.median(m):.3f}   mean = {np.mean(m):.4f}   "
          f"min = {m.min():.3f}   max = {m.max():.3f}")

    fee = mainnet["fee_lovelace"].astype(int)
    print(f"    per-record fee range: {fee.min()}-{fee.max()} lovelace")

    # ---- Mann-Whitney U (mainnet passed first) -------------------------
    U, p_mw = stats.mannwhitneyu(m, p, alternative="two-sided")
    print("\n[2] Mann-Whitney U (mainnet vs preprod, mainnet first)")
    print(f"    U = {U:.0f}   p = {p_mw:.4f}")

    # ---- Welch TOST, margin +/- 10 s -----------------------------------
    diff = m.mean() - p.mean()
    se = np.sqrt(m.var(ddof=1) / m.size + p.var(ddof=1) / p.size)
    # Welch-Satterthwaite degrees of freedom
    df = (m.var(ddof=1) / m.size + p.var(ddof=1) / p.size) ** 2 / (
        (m.var(ddof=1) / m.size) ** 2 / (m.size - 1)
        + (p.var(ddof=1) / p.size) ** 2 / (p.size - 1))
    t_lower = (diff - (-MARGIN)) / se            # H1: diff > -margin (upper tail)
    p_lower = stats.t.sf(t_lower, df)
    t_upper = (diff - MARGIN) / se               # H1: diff <  margin (lower tail)
    p_upper = stats.t.cdf(t_upper, df)
    p_tost = max(p_lower, p_upper)
    print(f"\n[3] Welch TOST, equivalence margin +/- {MARGIN:.0f} s")
    print(f"    mean difference (mainnet - preprod) = {diff:.4f} s")
    print(f"    p_lower = {p_lower:.5f}   p_upper = {p_upper:.5f}   "
          f"p_TOST = {p_tost:.5f}")

    # ---- Bootstrap CIs (percentile, seed 42) ---------------------------
    rng = np.random.default_rng(SEED)
    mean_diffs = np.empty(N_BOOT)
    med_diffs = np.empty(N_BOOT)
    for i in range(N_BOOT):
        bm = rng.choice(m, m.size, replace=True)
        bp = rng.choice(p, p.size, replace=True)
        mean_diffs[i] = bm.mean() - bp.mean()
        med_diffs[i] = np.median(bm) - np.median(bp)
    ci_mean = np.percentile(mean_diffs, [2.5, 97.5])
    ci_med = np.percentile(med_diffs, [2.5, 97.5])
    print(f"\n[4] Bootstrap 95% CI (percentile, seed {SEED}, {N_BOOT} resamples)")
    print(f"    mean difference   : [{ci_mean[0]:.3f}, {ci_mean[1]:.3f}] s")
    print(f"    median difference : [{ci_med[0]:.3f}, {ci_med[1]:.3f}] s")
    print("    (values match the article to the reported precision; exact last")
    print("     decimals depend on the RNG implementation.)")

    # ---- Kruskal-Wallis by time-of-day session -------------------------
    groups = [g[LAT].astype(float).to_numpy()
              for _, g in mainnet.groupby("franja")]
    H, p_kw = stats.kruskal(*groups)
    print(f"\n[5] Kruskal-Wallis by time-of-day session ({len(groups)} groups)")
    print(f"    H = {H:.4f}   p = {p_kw:.5f}")

    # ---- Fee/payload linear regression + exact fee identity ------------
    curva = load(os.path.join("mainnet", "e8_mainnet_lote_curva.csv"))
    N = curva["n_evidencias"].astype(float).to_numpy()
    B = curva["bytes_serializados"].astype(float).to_numpy()
    slope, intercept, r, _, _ = stats.linregress(N, B)
    print("\n[6] Fee/payload series (N = 1,2,4,8,16,32)")
    print(f"    bytes = {intercept:.3f} + {slope:.4f} * N   R^2 = {r**2:.7f}")

    lote = load(os.path.join("mainnet", "e8_mainnet_lote.csv"))
    allrows = pd.concat([curva, lote], ignore_index=True)
    pred = 155381 + 44 * allrows["bytes_serializados"].astype(int)
    resid = (allrows["fee_lovelace"].astype(int) - pred).abs().max()
    print(f"    fee = 155381 + 44 * bytes  ->  max residual = {resid} lovelace "
          f"({'exact' if resid == 0 else 'NOT exact'})")

    # ---- Verification summary ------------------------------------------
    ver = load(os.path.join("mainnet", "e8_mainnet_verificacion.csv"))
    recovered = ver["recuperado"].astype(str).str.lower().eq("true").sum()
    id_match = ver["id_coincide"].astype(str).str.lower().eq("true").sum()
    print("\n[7] Ledger recovery / verification")
    print(f"    anchors recovered : {recovered}/{len(ver)}")
    print(f"    record-id matches : {id_match} "
          f"(the N=10 batch exposes no single record id, by design)")
    if "t_verificacion_s" in ver:
        tv = ver["t_verificacion_s"].astype(float)
        print(f"    verification latency: median = {tv.median():.3f} s   "
              f"mean = {tv.mean():.4f} s")

    print("\n" + "=" * 68)
    print("Done.")
    print("=" * 68)


if __name__ == "__main__":
    main()
