# LegalCCD

**A hybrid blockchain-based prototype for the chain of custody of digital evidence.**

LegalCCD anchors cryptographic hashes and non-personal custody metadata of digital
evidence as native transaction metadata on the Cardano blockchain, while all evidence
content and personal data remain off-chain. Every anchored record becomes publicly and
independently verifiable through its transaction identifier, without depending on the
institution that produced it.

This repository contains the source code, measurement scripts, and raw experimental
datasets accompanying the article:

> J. Vázquez-Pérez and A. González-Arrieta, "A Hybrid Blockchain Architecture for a
> GDPR-Aligned Chain of Custody of Digital Evidence: Design, Implementation, and
> Evaluation on Cardano," *IEEE Access* (under review), 2026.

---

## What this prototype does

- Computes forensic hashes (SHA-256 / SHA-512) of a digital item **locally**.
- Anchors the digest and non-personal custody metadata on Cardano as native
  transaction metadata under label `1984`. SHA-256 digests fit exactly within
  Cardano's 64-byte metadata string limit; SHA-512 is automatically split into two
  64-byte chunks.
- Waits for on-chain confirmation and records the resulting transaction identifier.
- Verifies any record end-to-end by recomputing the local hash and comparing it against
  the metadata retrieved from the public ledger.

The prototype implements the acquisition, anchoring, and public verification layer.
Multi-actor custody-transfer workflows belong to the institutional off-chain layer and
are out of scope for this artifact.

---

## Reproducing the results without running anything

Because every anchoring transaction is permanently recorded on the public Cardano
**pre-production** ledger, the core experimental claims can be verified directly in a
block explorer. For example, the first end-to-end record (smoke test) is:

- **TxID:** `0d143c673d997f3265fa2a6bfeb1faba32bb0fdc3853cfe31103eb06c2df661c`
- **Explorer:** https://preprod.cardanoscan.io/transaction/0d143c673d997f3265fa2a6bfeb1faba32bb0fdc3853cfe31103eb06c2df661c

Opening that transaction shows the anchored metadata (label `1984`) and its consensus
timestamp. The complete list of transaction identifiers for the measurement campaign is
available in the raw CSV files under `_LOGS/`.

---

## Repository layout

```
legalccd/            Core package
  app.py             Desktop GUI (CustomTkinter)
  cardano.py         Cardano transaction construction, signing, submission, verification
  hashing.py         SHA-256 / SHA-512 hashing of evidence items
  registro.py        Custody record model and human-readable report generation
  wallet.py          Local wallet management (key generation / loading)
  config.py          Configuration loader (env var or config.json)
main.py              Application entry point (python main.py)
setup_wallet.py      One-time wallet creation and funding address
medir_cardano_v2.py       Anchoring latency / cost campaign (sessions S1..S3)
benchmark_hashing_v2.py   Local hashing throughput benchmark
medir_fee_payload.py      Fee-vs-payload-size series (deterministic cost)
pruebas_funcionales.py    Functional and negative tests, traceable to ISO/IEC 27037
medir_verificacion_hash.py  End-to-end verification with on-chain hash recovery
_LOGS/               Raw console logs and CSV datasets from the campaign
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
- A free [Blockfrost](https://blockfrost.io) project ID for the **Cardano preprod**
  network.

The experimental campaign reported in the article was run on an Apple MacBook Pro
14-inch (2023), Apple M3 Pro, 18 GB unified memory, macOS 26.5. The hashing throughput
figures are hardware-accelerated on ARM and will differ on other CPUs.

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your Blockfrost project ID
cp config.example.json config.json
#   then edit config.json and paste your own preprod project ID,
#   or export it as an environment variable instead:
#   export BLOCKFROST_PROJECT_ID=preprod...

# 3. Create the system wallet and print the address to fund
python setup_wallet.py
#   Fund the printed address with test ADA from the official preprod faucet:
#   https://docs.cardano.org/cardano-testnets/tools/faucet

# 4. Launch the GUI
python main.py
```

> **Note on credentials.** This repository contains no keys or API identifiers. You must
> generate your own wallet (`setup_wallet.py`) and provide your own Blockfrost project
> ID. The `claves/` directory and `config.json` are git-ignored by design and must never
> be committed.

---

## Reproducing the experiments

Each measurement script writes a CSV that mirrors the datasets already provided under
`_LOGS/`. For example:

```bash
python benchmark_hashing_v2.py      # local hashing throughput (Experiment E6)
python medir_fee_payload.py         # fee vs. payload size (Experiment E5)
python medir_cardano_v2.py --sesion S1 --n 25   # anchoring latency/cost (E1/E2)
```

Anchoring scripts require a funded preprod wallet and a valid Blockfrost project ID.
The hashing benchmark runs fully offline.

---

## Security note

This is a research prototype for the **testnet** environment. It is not hardened for
production custody of real evidence, and the wallet keys it manages are testnet keys with
no monetary value. Do not reuse a testnet wallet on mainnet.

---

## License

Released under the [MIT License](LICENSE).
