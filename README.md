# LegalCCD

**A hybrid blockchain architecture for privacy-preserving integrity verification of digital chain-of-custody documents.**

LegalCCD anchors the SHA-256 digest of a finalized, electronically signed custody
document, together with metadata containing no directly readable personal or case data,
as native transaction metadata on the Cardano blockchain. The document itself and all
personal data remain off-chain under institutional control. Every anchored record becomes
publicly and independently verifiable through its transaction identifier, without
depending on the institution that produced it.

This repository contains the source code, measurement scripts, and raw experimental
datasets accompanying the article:

> J. Vázquez-Pérez and A. González-Arrieta, "A Hybrid Blockchain Architecture for
> Privacy-Preserving Integrity Verification of Digital Chain-of-Custody Documents:
> Design, Implementation, and Evaluation on Cardano," *IEEE Access* (under review), 2026.

---

## What this prototype does

- Computes the SHA-256 digest (SHA-512 also supported) of a finalized custody document
  **locally**. Because the file is processed as a byte stream, hashing and anchoring are
  **independent of the document format and signature container**.
- Anchors the document digest and non-identifying custody metadata on Cardano as native
  transaction metadata under label `1984`. A SHA-256 digest fits exactly within Cardano's
  64-byte metadata string limit; SHA-512 is automatically split into two 64-byte chunks.
- Waits for on-chain confirmation and records the resulting transaction identifier.
- Verifies any record end-to-end by recomputing the local digest and comparing it against
  the metadata retrieved from the public ledger.

The prototype implements the acquisition, anchoring, and public-verification layer.
Multi-actor custody-transfer workflows belong to the institutional off-chain layer and are
out of scope for this artifact.

> **On the experimental files.** The measurement campaigns (latency, cost, throughput)
> were run over synthetic files representative of custody documents across the expected
> input-size range. Because the mechanism is format-agnostic, the same pipeline applies to
> a real signed custody document; an end-to-end demonstration anchored a real file and
> re-verified it against the ledger.

---

## Reproducing the results without running anything

Every anchoring transaction is recorded on the public Cardano ledger and can be verified
directly in a block explorer for as long as the ledger history remains available.

**Pre-production (preprod) — main measurement campaign (105 transactions):**

- Example (first end-to-end record, smoke test):
  `0d143c673d997f3265fa2a6bfeb1faba32bb0fdc3853cfe31103eb06c2df661c`
- Explorer: https://preprod.cardanoscan.io/transaction/0d143c673d997f3265fa2a6bfeb1faba32bb0fdc3853cfe31103eb06c2df661c
- Full list of identifiers and raw data under `_LOGS/`.

**Mainnet — external-validation campaign (30 transactions + a batch):**

- Example (first mainnet record):
  `191b4ff521d9c52b20158a580f281d123a279efeda966b0eb25e78cd4f51fb47`
- Explorer: https://cardanoscan.io/transaction/191b4ff521d9c52b20158a580f281d123a279efeda966b0eb25e78cd4f51fb47
- Complete list of identifiers, raw per-transaction data, fee/payload curve, and
  verification under `mainnet/` (see `mainnet/README_E8_mainnet_dataset.md`).

Opening any of these transactions shows the anchored metadata (label `1984`) and its
ledger-assigned inclusion time.

---

## Repository layout

```
legalccd/            Core package
  app.py             Desktop GUI (CustomTkinter)
  cardano.py         Cardano transaction construction, signing, submission, verification
  hashing.py         SHA-256 / SHA-512 hashing
  registro.py        Custody record model and human-readable report generation
  wallet.py          Local wallet management (key generation / loading)
  config.py          Configuration loader (env var or config.json)
main.py              Application entry point (python main.py)
setup_wallet.py      One-time wallet creation and funding address
medir_cardano_v2.py         Anchoring latency / cost campaign (sessions S1..S3)
benchmark_hashing_v2.py     Local hashing throughput benchmark
medir_fee_payload.py        Fee-vs-payload-size series (deterministic cost)
pruebas_funcionales.py      Functional and negative tests, traceable to ISO/IEC 27037
medir_verificacion_hash.py  End-to-end verification with on-chain hash recovery
_LOGS/               Raw console logs and CSV datasets from the preprod campaign
mainnet/             Cardano mainnet external-validation dataset
  e8_mainnet_30_combinado.csv        30 anchoring transactions (combined)
  e8_mainnet_franja1_tarde.csv       session 1 (afternoon)
  e8_mainnet_franja2_noche.csv       session 2 (night)
  e8_mainnet_franja3_manana.csv      session 3 (morning)
  e8_mainnet_lote.csv                batch transaction (10 digests in one tx)
  e8_mainnet_lote_curva.csv          fee/payload curve (N = 1, 2, 4, 8, 16, 32)
  e8_mainnet_verificacion.csv        per-transaction verification
  E8_mainnet_TxIDs.txt               complete list of mainnet transaction identifiers
  README_E8_mainnet_dataset.md       dataset description and methods
verificacion_hash_mediciones_cardano.csv     End-to-end verification of the 30 pilot records
verificacion_hash_mediciones_cardano_v2.csv  End-to-end verification of the 75 session records
                                             (full SHA-256 re-comparison); 105/105 verified in total
REGISTROS/           Example custody record (first anchored transaction)
```

---

## Requirements

- Python 3.14 (developed and measured on CPython 3.14.6).
- Dependencies in `requirements.txt`:
  - `pycardano >= 0.19` (measured with 0.19.2)
  - `blockfrost-python >= 0.6` (measured with 0.7.0)
  - `customtkinter >= 5.2` (measured with 6.0.0)
  - `cbor2 >= 5.6, < 6`
- A free [Blockfrost](https://blockfrost.io) project ID for the target Cardano network
  (preprod for the main campaign; mainnet for the external-validation campaign).

The experimental campaign reported in the article was run on an Apple MacBook Pro
14-inch (2023), Apple M3 Pro, 18 GB unified memory, macOS 26.5. The hashing throughput
figures are hardware-accelerated on ARM and will differ on other CPUs.

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your Blockfrost project ID for the target network
cp config.example.json config.json
#   then edit config.json and paste your own project ID (preprod or mainnet),
#   or export it as an environment variable instead:
#   export BLOCKFROST_PROJECT_ID=preprod...

# 3. Create the system wallet and print the address to fund
python setup_wallet.py
#   On preprod, fund the printed address with test ADA from the official faucet:
#   https://docs.cardano.org/cardano-testnets/tools/faucet

# 4. Launch the GUI
python main.py
```

> **Note on credentials.** This repository contains no keys or API identifiers. You must
> generate your own wallet (`setup_wallet.py`) and provide your own Blockfrost project ID.
> The `claves/` directory and `config.json` are git-ignored by design and must never be
> committed.

---

## Reproducing the experiments

Each measurement script writes a CSV that mirrors the datasets already provided under
`_LOGS/` (preprod) and `mainnet/` (mainnet). For example:

```bash
python benchmark_hashing_v2.py      # local hashing throughput
python medir_fee_payload.py         # fee vs. payload size
python medir_cardano_v2.py --sesion S1 --n 25   # anchoring latency/cost
```

Anchoring scripts require a funded wallet and a valid Blockfrost project ID for the target
network. The hashing benchmark runs fully offline.

---

## Security note

This is a research prototype. It manages its own wallet keys locally and reads the
Blockfrost project ID from an environment variable or a git-ignored `config.json`;
**no keys or API identifiers are included in this repository**. The main measurement
campaign ran on the Cardano preprod testnet (test ADA, no monetary value); a smaller
external-validation campaign ran on mainnet, where fees carry real cost — handle mainnet
keys accordingly, and never reuse a testnet wallet on mainnet. The prototype is not
hardened for production custody of real evidence.

---

## License

Released under the [MIT License](LICENSE).
