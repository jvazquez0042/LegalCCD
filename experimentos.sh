#!/bin/bash
# =====================================================================
# experimentos.sh — Lanzador de la campaña experimental LegalCCD v0.2
# Uso:  bash experimentos.sh   (desde la raíz de ~/LegalCCD)
# Cada experimento guarda su salida de consola automáticamente en
# _LOGS/AAAA-MM-DD_consola/  mediante tee (evidencia para la tesis).
# =====================================================================

set -u
cd "$(dirname "$0")"

FECHA=$(date +%Y-%m-%d)
LOGDIR="_LOGS/${FECHA}_consola"
mkdir -p "$LOGDIR"

ejecutar () {
    local nombre="$1"; shift
    local logfile="${LOGDIR}/${nombre}_$(date +%H%M%S).txt"
    echo ""
    echo ">>> Ejecutando: $*"
    echo ">>> Salida registrada en: $logfile"
    echo ""
    "$@" 2>&1 | tee "$logfile"
    echo ""
    echo ">>> Fin de $nombre. Log guardado en $logfile"
    echo ""
}

while true; do
    echo "====================================================="
    echo "   CAMPAÑA EXPERIMENTAL LegalCCD v0.2 — ${FECHA}"
    echo "====================================================="
    echo "  0) Generar entorno.txt (Anexo D)"
    echo "  1) Experimento 6 — Benchmark de hashing (10-15 min)"
    echo "  2) Experimento 4 — Pruebas funcionales (pide TxID)"
    echo "  3) Experimento 1 — Sesión S1 preprod (25 tx, ~25 min)"
    echo "  4) Experimento 1 — Sesión S2 preprod (25 tx, ~25 min)"
    echo "  5) Experimento 1 — Sesión S3 preprod (25 tx, ~25 min)"
    echo "  6) Experimento 5 — Curva fee/payload (~10 min)"
    echo "  7) Experimento 3 — Verificación extremo a extremo"
    echo "  8) Experimento 2 — Sesión P1 preview (30 tx, ~30 min)"
    echo "     (requiere config.json apuntando a preview)"
    echo "  9) Consultar saldo de la wallet"
    echo "  q) Salir"
    echo "-----------------------------------------------------"
    read -r -p "Elige opción: " op

    case "$op" in
        0) ejecutar "entorno" python3 generar_entorno.py ;;
        1) ejecutar "benchmark_hashing" python3 benchmark_hashing_v2.py ;;
        2) read -r -p "TxID real de preprod: " txid
           ejecutar "pruebas_funcionales" python3 pruebas_funcionales.py --red "$txid" ;;
        3) ejecutar "S1" python3 medir_cardano_v2.py 25 30 --sesion S1 ;;
        4) ejecutar "S2" python3 medir_cardano_v2.py 25 30 --sesion S2 ;;
        5) ejecutar "S3" python3 medir_cardano_v2.py 25 30 --sesion S3 ;;
        6) ejecutar "fee_payload" python3 medir_fee_payload.py ;;
        7) ejecutar "verificacion" python3 medir_verificacion.py mediciones_cardano_v2.csv ;;
        8) ejecutar "P1_preview" python3 medir_cardano_v2.py 30 30 --sesion P1 ;;
        9) ejecutar "saldo" python3 setup_wallet.py --saldo ;;
        q|Q) echo "Hasta luego."; exit 0 ;;
        *) echo "Opción no válida." ;;
    esac
done
