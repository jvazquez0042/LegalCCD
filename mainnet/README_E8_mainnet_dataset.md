LegalCCD — External-validation dataset on the Cardano mainnet

Author: Juan Vázquez-Pérez (ORCID 0009-0008-3938-0676), BISITE Research Group, Universidad de Salamanca
Related software: LegalCCD (see the main repository record)
Network: Cardano mainnet · transaction metadata label 1984

Overview

This dataset accompanies the external-validation campaign of LegalCCD on the Cardano mainnet, complementing
the pre-production measurements of the main study. It contains the raw per-transaction measurements, the
verification results, and the complete list of public transaction identifiers, so that every reported figure can
be independently reproduced against the public ledger.

Each experimental record anchors a SHA-256 digest generated through the same file-format-independent LegalCCD
hashing and anchoring path designed for finalized, electronically signed custody documents; the campaign inputs
were synthetic files representative of custody documents across the expected size range, not real case material.
Each on-chain payload carries the digest together with a randomly generated, non-semantic record identifier and a
UTC timestamp. No directly readable personal data, case numbers, or document content is written on-chain. The
document-level digest is nevertheless treated conservatively as potentially linkable data, since a party holding a
candidate document could recompute it and test for equality.

Campaign summary

ComponentCountResultAnchoring transactions (3 time-of-day sessions x 10)30100% confirmedBatch transaction (10 digests in one transaction)1fee = 203,517 lovelace (1,094 B)Fee/payload series (N = 1, 2, 4, 8, 16, 32)6linear: bytes = 409 + 72.7*N, R2 = 0.9997Anchors recovered from the public ledger31see "Verification" below

For the evaluated transaction path, all mainnet observations satisfied the protocol fee equation
fee = 155,381 + 44 * size_in_bytes lovelace exactly (zero residual on the fee/payload series).
Per-record cost: 174,917-178,085 lovelace (approx. EUR 0.026 at 0.146 EUR/ADA, CoinGecko, 9 July 2026); the small
variation reflects the wallet's UTxO composition, not market pricing. Confirmation latency (N = 30): median
26.6 s, mean 32.1 s; no statistically significant difference from the pre-production series (Mann-Whitney
p = 0.75); limited evidence of practical equivalence within a 10 s margin (TOST p = 0.04); no significant
time-of-day effect (Kruskal-Wallis p = 0.13). Third-party verification latency: median 0.28 s.

Verification

e8_mainnet_verificacion.csv documents the recovery of 31 anchors from the public ledger: the 30 individual
transactions were each recovered and their record identifiers matched the local values; the N = 10 batch was
recovered separately and, by design, does not expose a single record identifier for comparison (recovery only).

A full hash-to-hash demonstration was additionally performed on a real file
(TxID ae68b478060344b4da1e005329a2e8f26c28ac86b251b5abb87fdd43a8bcac65, publicly inspectable): the on-chain
digest matched the local SHA-256 of the source document. The source file itself is retained off-chain and is not
redistributed here; the byte-for-byte comparison therefore requires that file, while the on-chain digest and
metadata remain publicly verifiable.

Files

FileDescriptione8_mainnet_franja1_tarde.csvAnchoring session 1 (afternoon), 10 transactionse8_mainnet_franja2_noche.csvAnchoring session 2 (night), 10 transactionse8_mainnet_franja3_manana.csvAnchoring session 3 (morning), 10 transactionse8_mainnet_30_combinado.csvThe 30 anchoring transactions, mergede8_mainnet_lote.csvBatch transaction (N = 10)e8_mainnet_lote_curva.csvFee/payload series (N = 1, 2, 4, 8, 16, 32)e8_mainnet_verificacion.csvLedger recovery/verification of the 31 anchors + latencyE8_mainnet_TxIDs.txtComplete list of public transaction identifiers

CSV columns for anchoring files: n, exito, txid, bloque, t_envio_s, t_confirmacion_s, fee_lovelace, id_registro, timestamp, error, franja. Latencies are in seconds; t_envio_s is the time from submission to
Blockfrost acceptance and t_confirmacion_s the time from submission to the transaction's first on-chain
confirmation. fee is in lovelace (1 ADA = 1,000,000 lovelace). Timestamps are in UTC; the session labels
tarde/noche/manana denote afternoon/night/morning local execution windows.

Reproduction

Each transaction can be inspected on any Cardano explorer, e.g. https://cardanoscan.io/transaction/<txid>,
where the metadata under label 1984 exposes the application/version, the record and item identifiers, the UTC
timestamp, and the anchored SHA-256 digest. Recomputing the SHA-256 of the corresponding source document and
comparing it against the on-chain digest reproduces the integrity check.

Provenance


Dataset version: 1.0 (mainnet external-validation campaign, E8)
Software: LegalCCD, release v0.4 of the main repository
Environment: Python 3.14.6, PyCardano 0.19.2, blockfrost-python 0.7.0; macOS (Apple M3 Pro)
Network: Cardano mainnet; anchoring via a wallet dedicated exclusively to this experiment


License


Data (this dataset): released under CC BY 4.0.
Measurement scripts / software: distributed with the main repository under the MIT License.
