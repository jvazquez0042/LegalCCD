"""
generar_entorno.py
------------------
Genera entorno.txt con la descripción reproducible del entorno
experimental (Anexo D de la tesis y sección de evaluación del artículo).
Ejecutar una vez en la máquina donde se realicen las mediciones:
    python generar_entorno.py
"""
import platform
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

LIBRERIAS = ["customtkinter", "pycardano", "blockfrost-python", "matplotlib"]

lineas = [
    "ENTORNO EXPERIMENTAL — LegalCCD v0.2",
    f"Generado: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
    "",
    f"Sistema operativo : {platform.platform()}",
    f"Procesador        : {platform.processor() or platform.machine()}",
    f"Arquitectura      : {platform.architecture()[0]}",
    f"Python            : {platform.python_version()} ({sys.executable})",
    "",
    "Librerías:",
]
for lib in LIBRERIAS:
    try:
        lineas.append(f"  {lib:<20} {metadata.version(lib)}")
    except metadata.PackageNotFoundError:
        lineas.append(f"  {lib:<20} (no instalada)")

try:  # RAM total en Windows
    import ctypes
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    st = MEMORYSTATUSEX(); st.dwLength = ctypes.sizeof(st)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
    lineas.insert(6, f"RAM total         : {st.ullTotalPhys / 1024**3:.1f} GB")
except Exception:
    pass

Path("entorno.txt").write_text("\n".join(lineas), encoding="utf-8")
print("\n".join(lineas))
print("\nGuardado en entorno.txt")
