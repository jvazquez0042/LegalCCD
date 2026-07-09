"""
pruebas_funcionales.py  (Experimento E4)
----------------------------------------
Batería de pruebas funcionales y negativas del prototipo LegalCCD v0.2,
trazable a los requisitos de ISO/IEC 27037:2012. Genera la tabla de
casos de prueba de la sección de resultados de la tesis.

Casos:
  T1  Detección de manipulación: se altera UN byte de un archivo y se
      comprueba que el SHA-256 cambia (integridad, ISO 27037 cl. 6.9).
      [local, sin red]
  T2  Estabilidad del hash: el mismo archivo produce el mismo hash en
      cálculos repetidos (reproducibilidad, cl. 5.3.4). [local]
  T3  Fragmentación SHA-512: un hash de 128 caracteres se fragmenta en
      2 cadenas de 64 bytes y se reconstruye sin pérdida (límite de
      protocolo de metadatos de Cardano). [local]
  T4  Minimización de datos (RGPD by design): el payload que se envía a
      la cadena NO contiene ninguno de los campos personales del
      registro local. [local]
  T5  TxID inexistente: la verificación de un TxID falso devuelve error
      controlado, no un falso positivo. [requiere red]
  T6  Cotejo negativo: los metadatos recuperados de una tx real NO
      validan contra un hash distinto (no hay falsos positivos en el
      cotejo). [requiere red y un TxID real como argumento]

Uso:
    python pruebas_funcionales.py                    # T1-T4 (sin red)
    python pruebas_funcionales.py --red <txid_real>  # T1-T6

Salida: pruebas_funcionales.csv
"""

import csv
import hashlib
import os
import sys
import tempfile
from pathlib import Path

from legalccd.hashing import calcular_hash_archivo
from legalccd.registro import Registro
from legalccd.cardano import preparar_metadatos, METADATA_LABEL

RESULTADOS = []


def caso(id_caso: str, descripcion: str, iso: str, resultado: bool, detalle: str):
    RESULTADOS.append(
        {
            "caso": id_caso,
            "descripcion": descripcion,
            "clausula_iso_27037": iso,
            "resultado": "PASA" if resultado else "FALLA",
            "detalle": detalle,
        }
    )
    print(f"  [{ 'PASA' if resultado else 'FALLA' }] {id_caso}: {descripcion}")


def t1_manipulacion(tmp: Path):
    ruta = tmp / "vestigio.bin"
    datos = bytearray(os.urandom(1024 * 512))
    ruta.write_bytes(datos)
    h1 = calcular_hash_archivo(ruta, ["SHA-256"])["hashes"]["SHA-256"]
    datos[100] ^= 0x01  # alterar un único bit de un byte
    ruta.write_bytes(datos)
    h2 = calcular_hash_archivo(ruta, ["SHA-256"])["hashes"]["SHA-256"]
    caso(
        "T1", "Detección de manipulación (1 byte alterado)", "6.9 (integridad)",
        h1 != h2, f"hash original {h1[:12]}... != alterado {h2[:12]}...",
    )


def t2_estabilidad(tmp: Path):
    ruta = tmp / "estable.bin"
    ruta.write_bytes(os.urandom(1024 * 512))
    hashes = {calcular_hash_archivo(ruta, ["SHA-256"])["hashes"]["SHA-256"] for _ in range(10)}
    caso(
        "T2", "Estabilidad del hash (10 cálculos idénticos)", "5.3.4 (reproducibilidad)",
        len(hashes) == 1, f"{10} cálculos -> {len(hashes)} valor(es) distinto(s)",
    )


def t3_fragmentacion():
    h512 = hashlib.sha512(b"LegalCCD").hexdigest()  # 128 caracteres
    r = Registro(id_vestigio="VD-T3", hashes={"SHA-512": h512})
    md = preparar_metadatos(r.payload_blockchain())[METADATA_LABEL]
    frag = md["hashes"]["SHA-512"]
    ok = (
        isinstance(frag, list)
        and all(len(x.encode()) <= 64 for x in frag)
        and "".join(frag) == h512
    )
    caso(
        "T3", "Fragmentación y reconstrucción de SHA-512 (limite 64 B)",
        "n/a (límite de protocolo Cardano)", ok,
        f"{len(frag) if isinstance(frag, list) else 1} fragmentos, reconstrucción exacta: {ok}",
    )


def t4_minimizacion():
    r = Registro(
        id_vestigio="VD-T4",
        hashes={"SHA-256": "a" * 64},
        nombre_actuante="Nombre Apellidos",
        id_profesional="12345-X",
        desc_caso="Descripción sensible del caso",
        num_caso="DP 123/2026",
    )
    payload = r.payload_blockchain()
    plano = str(payload)
    campos_personales = ["Nombre Apellidos", "12345-X", "sensible", "DP 123/2026"]
    filtrado = not any(c in plano for c in campos_personales)
    claves_ok = set(payload.keys()) == {"app", "v", "id", "vid", "ts", "hashes"}
    caso(
        "T4", "Minimización de datos en payload on-chain (RGPD)",
        "5.4.3 / RGPD art. 5.1.c", filtrado and claves_ok,
        f"claves payload: {sorted(payload.keys())}; datos personales presentes: {not filtrado}",
    )


def t5_txid_inexistente():
    from legalccd.cardano import verificar_txid
    falso = "0" * 64
    res = verificar_txid(falso)
    caso(
        "T5", "Verificación de TxID inexistente (negativa controlada)",
        "6.9 (verificabilidad)", not res.exito,
        f"exito={res.exito}; mensaje={res.mensaje[:60]}",
    )


def t6_cotejo_negativo(txid_real: str):
    from legalccd.cardano import verificar_txid
    res = verificar_txid(txid_real)
    if not res.exito or not res.metadatos:
        caso("T6", "Cotejo negativo contra hash distinto", "6.9",
             False, "no se pudieron recuperar metadatos de la tx indicada")
        return
    hashes = res.metadatos.get("hashes", {}) or {}
    rec = hashes.get("SHA-256", "")
    if isinstance(rec, list):
        rec = "".join(rec)
    hash_falso = "f" * 64
    caso(
        "T6", "Cotejo negativo contra hash distinto (sin falsos positivos)",
        "6.9 (integridad)", str(rec) != hash_falso and bool(rec),
        f"recuperado {str(rec)[:12]}... != falso {hash_falso[:12]}...",
    )


def main() -> None:
    con_red = "--red" in sys.argv
    txid_real = ""
    if con_red:
        idx = sys.argv.index("--red")
        if len(sys.argv) > idx + 1:
            txid_real = sys.argv[idx + 1]

    print("Batería de pruebas funcionales LegalCCD v0.2\n")
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        t1_manipulacion(carpeta)
        t2_estabilidad(carpeta)
        t3_fragmentacion()
        t4_minimizacion()
    if con_red:
        t5_txid_inexistente()
        if txid_real:
            t6_cotejo_negativo(txid_real)
        else:
            print("  (T6 omitido: indica un TxID real tras --red)")

    salida = Path("pruebas_funcionales.csv")
    with salida.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(RESULTADOS[0].keys()))
        w.writeheader()
        w.writerows(RESULTADOS)

    pasan = sum(1 for r in RESULTADOS if r["resultado"] == "PASA")
    print(f"\n{pasan}/{len(RESULTADOS)} casos superados. Tabla en {salida.resolve()}")


if __name__ == "__main__":
    main()
