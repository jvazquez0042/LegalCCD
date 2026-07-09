"""
medir_verificacion_hash.py  (variante de E3)
--------------------------------------------
Idéntico a medir_verificacion.py, pero AÑADE al CSV de salida la columna
'sha256_recuperado' con el hash SHA-256 reconstruido desde los metadatos
de la cadena. Sirve para completar el Anexo C con el hash real de las
transacciones cuyo CSV de origen no lo guardó (p. ej. el piloto v1).

Uso (desde la raíz del proyecto LegalCCD):
    python3 medir_verificacion_hash.py mediciones_cardano.csv

IMPORTANTE: la red activa en config.json debe coincidir con la red donde
se registraron las transacciones del CSV (el piloto fue en preprod).

Salida: verificacion_hash_<nombre_csv_entrada>
"""

import csv
import statistics
import sys
import time
from pathlib import Path

from legalccd.cardano import verificar_txid


def extraer_sha256(metadatos: dict) -> str:
    if not metadatos:
        return ""
    hashes = metadatos.get("hashes", {}) or {}
    valor = hashes.get("SHA-256", "")
    if isinstance(valor, list):
        valor = "".join(valor)
    return str(valor)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python3 medir_verificacion_hash.py <csv_de_mediciones>")
        sys.exit(1)

    entrada = Path(sys.argv[1])
    filas_in = [
        r for r in csv.DictReader(entrada.open(encoding="utf-8"))
        if r.get("txid") and r.get("exito", "True") in ("True", "true", "1")
    ]
    print(f"Verificando {len(filas_in)} transacciones de {entrada.name}\n")

    salida = Path(f"verificacion_hash_{entrada.name}")
    filas_out = []
    for i, r in enumerate(filas_in, 1):
        txid = r["txid"]
        t0 = time.perf_counter()
        res = verificar_txid(txid)
        t = round(time.perf_counter() - t0, 3)

        sha_recuperado = extraer_sha256(res.metadatos) if res.exito else ""
        sha_original = r.get("hash_sha256", "")
        if sha_original:
            integridad = "OK" if sha_recuperado == sha_original else "FALLO"
        else:
            id_rec = str((res.metadatos or {}).get("id", ""))
            integridad = "OK(id)" if id_rec == r.get("id_registro", "") else "FALLO"

        filas_out.append(
            {
                "n": i,
                "txid": txid,
                "exito": res.exito,
                "t_verificacion_s": t,
                "metadatos_ok": bool(res.metadatos),
                "integridad": integridad,
                "bloque": res.bloque or "",
                "id_registro": (res.metadatos or {}).get("id", "") or r.get("id_registro", ""),
                "sha256_recuperado": sha_recuperado,
            }
        )
        print(f"[{i}/{len(filas_in)}] {txid[:16]}...  t={t}s  integridad={integridad}  sha={sha_recuperado[:16]}...")
        time.sleep(0.3)

    with salida.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_out[0].keys()))
        w.writeheader()
        w.writerows(filas_out)

    tiempos = [x["t_verificacion_s"] for x in filas_out if x["exito"]]
    ok_int = sum(1 for x in filas_out if x["integridad"].startswith("OK"))
    con_hash = sum(1 for x in filas_out if x["sha256_recuperado"])
    print(f"\nVerificadas con éxito: {sum(1 for x in filas_out if x['exito'])}/{len(filas_out)}")
    print(f"Integridad correcta:   {ok_int}/{len(filas_out)}")
    print(f"Con hash recuperado:   {con_hash}/{len(filas_out)}")
    if tiempos:
        print(
            f"Latencia verificación: media={statistics.mean(tiempos):.2f}s  "
            f"mediana={statistics.median(tiempos):.2f}s  "
            f"min={min(tiempos):.2f}  max={max(tiempos):.2f}"
        )
    print(f"Resultados en {salida.resolve()}")


if __name__ == "__main__":
    main()
