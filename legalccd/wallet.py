"""
legalccd.wallet
---------------
Gestión de claves de firma y dirección de LegalCCD.

Las claves se generan una sola vez y se guardan en ./claves/
(payment.skey / payment.vkey). La dirección derivada es la que
hay que fondear con tADA del faucet de preprod:
https://docs.cardano.org/cardano-testnets/tools/faucet

SEGURIDAD: payment.skey es la clave privada. En testnet no hay
valor económico real, pero el archivo debe tratarse como secreto
para que nadie pueda registrar transacciones suplantando al sistema.
"""

from pathlib import Path

from pycardano import (
    Address,
    Network,
    PaymentSigningKey,
    PaymentVerificationKey,
)

from legalccd.config import DIR_CLAVES

RUTA_SKEY = DIR_CLAVES / "payment.skey"
RUTA_VKEY = DIR_CLAVES / "payment.vkey"


def existe_wallet() -> bool:
    return RUTA_SKEY.exists() and RUTA_VKEY.exists()


def crear_wallet(red: str = "preprod") -> tuple[PaymentSigningKey, Address]:
    """Genera un par de claves nuevo y lo persiste en ./claves/."""
    DIR_CLAVES.mkdir(exist_ok=True)
    if existe_wallet():
        raise FileExistsError(
            f"Ya existe una wallet en {DIR_CLAVES}. "
            "Bórrala manualmente si de verdad quieres regenerarla "
            "(perderías el acceso a los fondos de la dirección anterior)."
        )
    skey = PaymentSigningKey.generate()
    vkey = PaymentVerificationKey.from_signing_key(skey)
    skey.save(str(RUTA_SKEY))
    vkey.save(str(RUTA_VKEY))
    return skey, direccion(red)


def cargar_wallet() -> PaymentSigningKey:
    if not existe_wallet():
        raise FileNotFoundError(
            "No hay wallet. Ejecuta primero:  python setup_wallet.py"
        )
    return PaymentSigningKey.load(str(RUTA_SKEY))


def direccion(red: str = "preprod") -> Address:
    """Dirección de pago derivada de la clave de verificación."""
    vkey = PaymentVerificationKey.load(str(RUTA_VKEY))
    network = Network.MAINNET if red == "mainnet" else Network.TESTNET
    return Address(payment_part=vkey.hash(), network=network)
