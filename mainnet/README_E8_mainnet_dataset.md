# LegalCCD — External-validation dataset on the Cardano mainnet

**Author:** Juan Vázquez-Pérez (ORCID 0009-0008-3938-0676), BISITE Research Group, Universidad de Salamanca
**Related software:** LegalCCD (see the main repository record)
**Network:** Cardano mainnet · transaction metadata label **1984**

## Overview

This dataset accompanies the external-validation campaign of LegalCCD on the Cardano **mainnet**, complementing
the pre-production measurements of the main study. It contains the raw per-transaction measurements, the
verification results, and the complete list of public transaction identifiers, so that every reported figure can
be independently reproduced against the public ledger.

All records anchor only a cryptographic digest of a signed custody document together with a randomly generated,
non-semantic record identifier and a UTC timestamp. No personal data, case data, or document content is written
on-chain.

## Campaign summary

| Component | Count | Result |
|---|---|---|
| Anchoring transactions (3 time-of-day sessions × 10) | 30 | 100% confirmed |
| Batch transaction (10 digests in one transaction) | 1 | fee = 203,517 lovelace (1,094 B) |
| Fee/payload series (N = 1, 2, 4, 8, 16, 32) | 6 | linear: bytes = 409 + 72.7·N, R² = 0.9997 |
| Independent verifications (public block explorer) | 2 | metadata recovered and matched |
| Full hash-to-hash demonstration | 1 | on-chain digest matched the source document byte-for-byte |

Fee model (protocol-defined, identical on preprod and mainnet): `fee = 155,381 + 44 · size_in_bytes` lovelace.
Per-record cost: 174,917–178,085 lovelace (≈ EUR 0.026 at 0.146 EUR/ADA, CoinGecko, 9 July 2026); the small
variation reflects the wallet's UTxO composition, not market pricing. Confirmation latency (N = 30): median
26.6 s, mean 32.1 s; no statistically significant difference from the pre-production series (Mann-Whitney
p = 0.75); practical equivalence within a 10 s margin (TOST p = 0.04); no significant time-of-day effect
(Kruskal-Wallis p = 0.13). Third-party verification latency: median 0.28 s.

## Files

| File | Description |
|---|---|
| `e8_mainnet_franja1_tarde.csv` | Anchoring session 1 (afternoon), 10 transactions |
| `e8_mainnet_franja2_noche.csv` | Anchoring session 2 (night), 10 transactions |
| `e8_mainnet_franja3_manana.csv` | Anchoring session 3 (morning), 10 transactions |
| `e8_mainnet_30_combinado.csv` | The 30 anchoring transactions, merged |
| `e8_mainnet_lote.csv` | Batch transaction (N = 10) |
| `e8_mainnet_lote_curva.csv` | Fee/payload series (N = 1, 2, 4, 8, 16, 32) |
| `e8_mainnet_verificacion.csv` | Independent recovery/verification of the 31 anchors + latency |
| `E8_mainnet_TxIDs.txt` | Complete list of public transaction identifiers |

CSV columns for anchoring files: `n, exito, txid, bloque, t_envio_s, t_confirmacion_s, fee_lovelace,
id_registro, timestamp, error` (latencies in seconds, fee in lovelace).

## Reproduction

Each transaction can be inspected on any Cardano explorer, e.g. `https://cardanoscan.io/transaction/<txid>`,
where the metadata under label 1984 exposes the application/version, the record and item identifiers, the UTC
timestamp, and the anchored SHA-256 digest. Recomputing the SHA-256 of the corresponding source document and
comparing it against the on-chain digest reproduces the integrity check.

## License

Data released under CC BY 4.0. Measurement scripts are distributed with the main software repository.
