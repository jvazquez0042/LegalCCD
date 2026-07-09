# LegalCCD v0.2 — Guía paso a paso

Objetivo: dejar el sistema registrando en la testnet **preprod** de Cardano
y obtener los datos experimentales para el artículo (IEEE Access) y la tesis.

Tiempo estimado total: 30-40 minutos (la mayor parte, esperas de la red).

---

## Paso 0. Instalar dependencias

Abre una terminal (CMD o PowerShell) en la carpeta `LegalCCD` y ejecuta:

    pip install -r requirements.txt

## Paso 1. Crear cuenta gratuita en Blockfrost (5 min)

1. Entra en https://blockfrost.io y regístrate (gratis).
2. Pulsa **Add project**.
3. Nombre: `LegalCCD` (o el que quieras). **Network: Cardano preprod** (importante).
4. Copia el **project_id** (empieza por `preprod...`).

## Paso 2. Crear config.json

En la carpeta `LegalCCD` crea un archivo `config.json` con este contenido
(pegando tu project_id):

    {
        "blockfrost_project_id": "preprodXXXXXXXXXXXXXXXXXXXX",
        "red": "preprod"
    }

## Paso 3. Crear la wallet del sistema

    python setup_wallet.py

Esto genera las claves en `./claves/` y te muestra una dirección que
empieza por `addr_test1...`. Cópiala.

## Paso 4. Fondear la dirección con tADA (gratis)

1. Entra en https://docs.cardano.org/cardano-testnets/tools/faucet
2. Selecciona **Preprod Testnet**.
3. Pega la dirección y solicita fondos (te enviarán ~10.000 tADA de prueba;
   no tienen valor real).
4. Espera 1-2 minutos y comprueba el saldo:

    python setup_wallet.py --saldo

## Paso 5. Primer registro real (prueba de humo)

    python -c "from legalccd.registro import Registro; from legalccd.cardano import registrar_en_cardano; r = Registro(id_vestigio='VD-PRUEBA-001', hashes={'SHA-256': 'a'*64}); print(registrar_en_cardano(r.payload_blockchain()))"

Si todo va bien verás un TxID. Puedes verlo públicamente en:
`https://preprod.cardanoscan.io/transaction/<TxID>`
(guarda ese enlace: los TxID reales irán citados en el artículo).

## Paso 6. Experimento de red para el artículo (~30 min desatendido)

    python medir_cardano.py 30 45

Envía 30 transacciones con pausa de 45 s y genera `mediciones_cardano.csv`
con latencias de envío, latencias de confirmación, fees y TxIDs.
**Ese CSV me lo pasas** y con él construyo las tablas y figuras de la
sección de evaluación.

## Paso 7. Benchmark local de hashing (~10 min)

    python benchmark_hashing.py

Genera `benchmark_hashing.csv` con el throughput de SHA-256/512, SHA-1 y
MD5 para archivos de 1 MB a 1 GB. **También me lo pasas.**
Anota además el modelo de CPU y la RAM de tu equipo (aparecerá en el
artículo como plataforma experimental; en Windows: `msinfo32`).

## Paso 8. Verificación (opcional pero recomendable)

Con cualquier TxID del CSV:

    python -c "from legalccd.cardano import verificar_txid; print(verificar_txid('PEGA_AQUI_UN_TXID'))"

Debe devolver el bloque y los metadatos recuperados de la red, idénticos
a los enviados. Esta verificación independiente también se menciona en
el artículo (cualquier tercero puede reproducirla sin permiso de nadie,
que es exactamente el argumento de auditabilidad pública).

---

## Problemas frecuentes

- **"Falta el project_id"**: revisa que `config.json` está en la carpeta
  `LegalCCD` (la misma donde está `main.py`).
- **"BadInputsUTxO" o error de UTxO**: has lanzado dos transacciones muy
  seguidas; espera 1 minuto y reintenta (por eso `medir_cardano.py` mete
  pausas).
- **Saldo 0 tras el faucet**: el faucet tarda a veces 2-3 minutos; también
  comprueba que pediste fondos en **Preprod** y no en Preview.
- **Errores de instalación de pycardano en Windows**: asegúrate de tener
  Python 3.10+ de 64 bits (`python --version`).

## Seguridad

`claves/payment.skey` es la clave privada del sistema. En preprod no hay
dinero real, pero trátala como secreta (no la subas a GitHub ni la
compartas): quien la tenga puede firmar registros como si fuera el sistema.
