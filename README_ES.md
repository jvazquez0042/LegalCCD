# LegalCCD — Sistema de Cadena de Custodia de Vestigios Digitales

**Versión:** 0.2 — Integración completa con Cardano (registro y verificación desde la GUI)  
**Plataforma:** macOS / Windows / Linux (Python 3.14)  
**Marco normativo:** ISO/IEC 27037:2012

---

## Instalación rápida

### 1. Requisitos previos
- Python 3.10 o superior (https://python.org/downloads)
- Marcar "Add Python to PATH" durante la instalación

### 2. Instalar dependencias

```bash
pip install customtkinter
```

### 3. Ejecutar la aplicación

```bash
python main.py
```

---

## Estructura del proyecto

```
LegalCCD/
├── main.py                  # Punto de entrada
├── requirements.txt
├── legalccd/
│   ├── __init__.py
│   ├── app.py               # Interfaz gráfica (CustomTkinter)
│   ├── hashing.py           # Cálculo de hashes (hashlib)
│   ├── registro.py          # Modelo de datos y exportación .txt
│   ├── cardano.py           # Integración Cardano (PyCardano + Blockfrost)
│   ├── wallet.py            # Claves Ed25519 del sistema
│   └── config.py            # Configuración de red (preprod/preview)
└── README.md
```

---

## Empaquetar como .exe (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name LegalCCD main.py
```

El ejecutable se generará en `dist/LegalCCD.exe`.

Para incluir el icono:
```bash
pyinstaller --onefile --windowed --name LegalCCD --icon=icono.ico main.py
```

---

## Funcionamiento

### Modos de entrada
| Modo | Descripción |
|------|-------------|
| Subir archivo | Calcula el hash del archivo seleccionado. El archivo nunca sale del dispositivo. |
| Texto libre | Calcula el hash del texto introducido (UTF-8). |
| Introducir hash | Registra un hash ya calculado externamente. |

### Algoritmos disponibles
| Algoritmo | Por defecto | Recomendado para custodia |
|-----------|-------------|--------------------------|
| SHA-256   | ✅ Sí       | ✅ Sí                     |
| SHA-512   | No          | ✅ Sí                     |
| MD5       | No          | ⚠ No (colisiones conocidas) |
| SHA-1     | No          | ⚠ No (colisiones conocidas) |

### Separación de datos (privacidad y RGPD)

**Reporte local (.txt):** contiene todos los campos del formulario,
incluyendo datos del caso, descripción del vestigio, nombre del
actuante, y otros datos adicionales.

**Registro en blockchain (v0.2):** contendrá exclusivamente:
- ID de registro (generado automáticamente)
- ID de vestigio
- Hashes criptográficos
- Timestamp UTC

Ningún dato personal ni contenido del vestigio se enviará a la red.

---

## Hoja de ruta

| Versión | Estado | Contenido |
|---------|--------|-----------|
| v0.1 | ✅ Actual | Hashing local, formulario, exportación .txt |
| v0.2 | Planificado | Integración Cardano preprod (PyCardano + Blockfrost) |
| v0.3 | Planificado | Verificación de TxID, consulta de registros en red |

---

## Referencia técnica

- **Hashing:** `hashlib` (biblioteca estándar de Python)
- **Interfaz:** `customtkinter` 5.x
- **Integración blockchain (v0.2):** `pycardano` + Blockfrost API
- **Red objetivo:** Cardano preprod testnet
- **Metadatos:** Transacción nativa con label 1984 (sin contratos Plutus)
- **Marco normativo:** ISO/IEC 27037:2012 — Identificación, recopilación,
  adquisición y preservación de evidencia digital

---

## Novedades v0.2 (completa)

- Botón **Registrar en Cardano** en la pestaña Resumen: ancla el payload como metadato nativo (etiqueta 1984) y muestra TxID, bloque, fee y URL de verificación pública.
- Pestaña **Verificar TxID**: consulta independiente de la red, muestra los metadatos inmutables y coteja los hashes con el registro actual.
- **Autoguardado** de reportes en `REGISTROS/` con fecha y hora en el nombre (`LegalCCD_AAAAMMDD_HHMMSS_<id>_<caso>.txt`), al confirmar en Cardano y al guardar en historial.
- Requisitos de red: `pip install pycardano blockfrost-python` + `config.json` con el project_id de Blockfrost + wallet creada con `python setup_wallet.py`.
