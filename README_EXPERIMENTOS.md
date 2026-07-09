# Plan experimental LegalCCD v0.2 — Guía de ejecución

Objetivo: completar la evidencia empírica de la tesis (nuevo apartado de
resultados del Cap. IX) y del artículo IEEE Access. Copia estos 5 scripts
en la raíz de `C:\LegalCCD` (junto a `main.py`) y ejecútalos desde ahí.

## Orden y calendario recomendado (3-4 días)

| Día | Experimento | Comando | Duración aprox. |
|-----|-------------|---------|-----------------|
| 1 (mañana) | E6 hashing | `python benchmark_hashing_v2.py` | 10-15 min |
| 1 (mañana) | E4 funcionales | `python pruebas_funcionales.py --red <un_txid_real>` | 2 min |
| 1 (mañana) | E1 sesión S1 | `python medir_cardano_v2.py 25 30 --sesion S1` | ~25 min |
| 1 (tarde)  | E1 sesión S2 | `python medir_cardano_v2.py 25 30 --sesion S2` | ~25 min |
| 2 o fin de semana | E1 sesión S3 | `python medir_cardano_v2.py 25 30 --sesion S3` | ~25 min |
| 2 | E5 fee/payload | `python medir_fee_payload.py` | ~10 min |
| 3 | E2 Preview | ver abajo | ~35 min |
| 3 | E3 verificación | `python medir_verificacion.py mediciones_cardano_v2.csv` | ~5 min |

Notas:
- E1: las 3 sesiones en franjas distintas (mañana / tarde / fin de semana)
  son deliberadas: capturan variabilidad temporal de la red. Con las 30 tx
  que ya tienes, N total ≥ 105 en preprod.
- Fondos: E1+E5 consumen ~15 tADA de fees. Comprueba el saldo; si falta,
  faucet de preprod: https://docs.cardano.org/cardano-testnets/tools/faucet

## E2 — Réplica en Preview (reproducibilidad inter-red)

1. En https://blockfrost.io crea un proyecto nuevo para **Cardano preview**.
2. En `config.json` cambia:
   ```json
   { "blockfrost_project_id": "preview...", "red": "preview" }
   ```
3. Pide fondos al faucet seleccionando **Preview Testnet** (misma URL).
   La dirección de tu wallet en preview la muestra `setup_wallet.py`
   (misma clave, red distinta).
4. Ejecuta: `python medir_cardano_v2.py 30 30 --sesion P1`
5. Ejecuta E3 también en preview ANTES de devolver config.json a preprod:
   `python medir_verificacion.py mediciones_cardano_v2.csv`
   (solo verificará las tx de la red activa; las de preprod las verificas
   con config.json en preprod).
6. Devuelve `config.json` a preprod.

## Qué enviarme al terminar

1. `benchmark_hashing_v2.csv`
2. `mediciones_cardano_v2.csv`  (acumulado de S1, S2, S3 y P1)
3. `verificacion_mediciones_cardano_v2.csv` (y el de preprod si lo separas)
4. `pruebas_funcionales.csv`
5. `fee_payload.csv`
6. Si algo falla: copia del mensaje de error de consola.

Con esos CSV genero: tablas y figuras definitivas, análisis estadístico
(medianas, IC 95 %, comparativa preprod/preview) y la redacción completa
del apartado de resultados de la tesis + la sección experimental del
artículo IEEE Access.

## Qué NO hacemos y por qué (para la memoria de la tesis)

- **Test de carga/estrés**: las testnets son infraestructura compartida y
  el plan gratuito de Blockfrost impone límites de peticiones; saturarlas
  sería metodológicamente cuestionable y contrario a las condiciones de
  uso. La escalabilidad se discute con los benchmarks de la literatura ya
  citados en el Cap. IX (DLPS, Baliga et al.). Se declara como limitación
  de alcance — es lo honesto y lo defendible.
