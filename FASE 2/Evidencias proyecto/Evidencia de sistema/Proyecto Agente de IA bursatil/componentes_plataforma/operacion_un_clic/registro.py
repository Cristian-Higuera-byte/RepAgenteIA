# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara registro .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Registro de la aceptación de los términos de One-Click Trading (por usuario, con fecha).

Guarda y consulta un archivo JSON en disco (`data/one_click_aceptaciones.json`) con una entrada por usuario.
"""
import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

# MODO DEMO: la renuncia se muestra CADA VEZ que se activa One-Click Trading (para
# presentaciones). La aceptación se sigue registrando en _RUTA con su fecha.
# Para el uso normal (pedirla solo la primera vez), poner False.
PEDIR_SIEMPRE = True

# Ruta del JSON de aceptaciones: carpeta data/ en la raíz del proyecto (dos niveles sobre este paquete)
_RUTA = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "one_click_aceptaciones.json")


# TITULO UID

def _uid() -> str:
    """Identificador del usuario actual: su id, si no su correo, y como último recurso "anonimo"."""
    u = st.session_state.get("usuario_informacion") or {}
    return str(u.get("id") or u.get("email") or "anonimo")


# TITULO LEER

def _leer() -> dict:
    """Lee el JSON de aceptaciones; devuelve un diccionario vacío si el archivo no existe o está dañado."""
    try:
        with open(_RUTA, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# TITULO ACEPTADO

def aceptado() -> bool:
    """¿El usuario actual ya aceptó los términos de One-Click Trading?

    Con `PEDIR_SIEMPRE` activo devuelve siempre False. Si no, consulta primero la caché de sesión
    (`terminos_un_clic_aceptado`) y luego el archivo en disco, guardando el resultado positivo en la sesión."""
    if PEDIR_SIEMPRE:
        return False
    if st.session_state.get("terminos_un_clic_aceptado"):
        return True
    correcto = _uid() in _leer()
    if correcto:
        st.session_state.terminos_un_clic_aceptado = True
    return correcto


# TITULO REGISTRAR

def registrar():
    """Registra la aceptación del usuario actual en disco (correo, fecha ISO y versión de los términos).

    Crea la carpeta `data/` si no existe, reescribe el JSON completo y marca `terminos_un_clic_aceptado` en la sesión."""
    # Se lee lo existente para no perder las aceptaciones de otros usuarios
    datos = _leer()
    u = st.session_state.get("usuario_informacion") or {}
    datos[_uid()] = {"email": u.get("email", ""), "fecha": datetime.now().isoformat(timespec="seconds"),
                     "version_terminos": 1}
    os.makedirs(os.path.dirname(_RUTA), exist_ok=True)
    with open(_RUTA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    st.session_state.terminos_un_clic_aceptado = True


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara registro .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
