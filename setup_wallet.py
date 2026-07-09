"""
setup_wallet.py
---------------
Paso 1 de LegalCCD v0.2: crear la wallet del sistema y mostrar la
dirección que hay que fondear con tADA del faucet de preprod.

Uso:
    python setup_wallet.py           # crea la wallet (si no existe) y muestra la dirección
    python setup_wallet.py --saldo   # consulta el saldo actual (requiere config.json)
"""

import sys

from legalccd.config import cargar_config, ConfigError
from legalccd import wallet


def main() -> None:
    try:
        cfg = cargar_config()
        red = cfg["red"]
    except ConfigError as e:
        # Sin config aún se puede crear la wallet (solo hace falta para el saldo)
        print(f"[Aviso] {e}\n")
        red = "preprod"

    if not wallet.existe_wallet():
        _, addr = wallet.crear_wallet(red)
        print("Wallet creada en ./claves/ (payment.skey + payment.vkey)")
    else:
        addr = wallet.direccion(red)
        print("Wallet ya existente en ./claves/")

    print(f"\nRed: {red}")
    print(f"Dirección del sistema LegalCCD:\n\n  {addr}\n")
    print("Fondéala con tADA (gratis) en el faucet oficial:")
    print("  https://docs.cardano.org/cardano-testnets/tools/faucet")
    print("  (selecciona 'Preprod Testnet', pega la dirección y solicita fondos)\n")

    if "--saldo" in sys.argv:
        from legalccd.cardano import saldo_lovelace
        try:
            saldo = saldo_lovelace()
            print(f"Saldo actual: {saldo} lovelace ({saldo / 1_000_000:.6f} tADA)")
        except Exception as e:  # noqa: BLE001
            print(f"No se pudo consultar el saldo: {e}")


if __name__ == "__main__":
    main()
