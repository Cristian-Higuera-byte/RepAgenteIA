# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara rutas .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Rutas candidatas del terminal64.exe de MT5 (MT5_PATH del .env, terminal abierto, carpetas típicas).

Como `initialize()` sin ruta puede colgarse, la conexión necesita rutas
explícitas; este módulo las descubre y las cachea unos minutos."""
from __future__ import annotations

import glob
import os
import subprocess
import time

from fuentes.mt5_fuentes.constantes import _TTL_RUTAS_S


# TITULO TERMINAL EN EJECUCION

def _terminal_en_ejecucion() -> list[str]:
    """Busca los terminal64.exe que estén abiertos ahora mismo en Windows.

    Ejecuta PowerShell (`Get-Process terminal64`, sin ventana, máximo 5 s) y
    devuelve la lista de rutas completas de los ejecutables. Devuelve lista
    vacía ante cualquier error (por ejemplo, en sistemas sin PowerShell)."""
    try:
        salida = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                "Get-Process terminal64 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path",
            ],
            capture_output=True, text=True, timeout=5,
            # CREATE_NO_WINDOW existe solo en Windows; en otros sistemas vale 0 (sin efecto).
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout
        # Se conservan únicamente las líneas que realmente apuntan a terminal64.exe.
        return [l.strip() for l in salida.splitlines() if l.strip().lower().endswith("terminal64.exe")]
    except Exception:
        return []


# Caché de rutas: (instante monotónico, lista de rutas) o None si aún no se calculó.
_rutas_cache: tuple[float, list[str]] | None = None


# TITULO RUTAS CANDIDATAS

def rutas_candidatas(refrescar: bool = False) -> list[str]:
    """Devuelve las rutas posibles del terminal64.exe, en orden de prioridad y sin duplicados.

    Orden: 1) MT5_PATH del .env, 2) terminales abiertos ahora, 3) carpetas
    típicas de instalación (Program Files, Program Files (x86) y
    %APPDATA%\\MetaQuotes\\Terminal). Con `refrescar=True` ignora la caché; de lo
    contrario reutiliza el resultado durante `_TTL_RUTAS_S` segundos. Solo se
    cachea un resultado no vacío. Efectos: lee variables de entorno, el disco y
    puede lanzar un proceso de PowerShell."""
    global _rutas_cache
    ahora = time.monotonic()
    # Devuelve una copia de la caché vigente para que quien llama no pueda alterarla.
    if _rutas_cache is not None and not refrescar and ahora - _rutas_cache[0] < _TTL_RUTAS_S:
        return list(_rutas_cache[1])

    rutas: list[str] = []
    # 1) Ruta configurada explícitamente en el .env (se quitan comillas sobrantes).
    en_env = os.getenv("MT5_PATH", "").strip().strip('"')
    if en_env and os.path.isfile(en_env):
        rutas.append(en_env)
    # 2) Terminales que ya están corriendo.
    rutas += _terminal_en_ejecucion()
    # 3) Instalaciones típicas: cada subcarpeta que contenga un terminal64.exe.
    for base in (
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.path.expandvars(r"%APPDATA%\MetaQuotes\Terminal"),
    ):
        rutas += glob.glob(os.path.join(base, "*", "terminal64.exe"))
    # Elimina duplicados comparando rutas normalizadas (mayúsculas/minúsculas y barras en Windows)
    # y descarta las que no existan como archivo.
    vistas: set[str] = set()
    unicas: list[str] = []
    for r in rutas:
        k = os.path.normcase(os.path.abspath(r))
        if k not in vistas and os.path.isfile(r):
            vistas.add(k)
            unicas.append(r)
    # No se cachea una lista vacía para volver a buscar en la siguiente llamada.
    if unicas:
        _rutas_cache = (ahora, unicas)
    return unicas


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara rutas .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
