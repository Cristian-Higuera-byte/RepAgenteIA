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

"""Registro de las aceptaciones de los términos de la vigilancia automática (por usuario, con fecha y condiciones).

Guarda y consulta un archivo JSON en disco (`data/vigilancia_aceptaciones.json`, ignorado por git) con una lista de
aceptaciones por usuario. Cada una anota qué vigilancia se autorizó (activo, riesgo, operaciones, duración) y cuándo, para
que quede constancia de lo que el usuario aceptó.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# Versión del texto de terminos.html que se aceptó; súbela cuando cambie el texto legal.
VERSION_TERMINOS = 1

# Ruta del JSON de aceptaciones: carpeta data/ en la raíz del proyecto (dos niveles sobre este paquete)
_RUTA = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "vigilancia_aceptaciones.json")


# TITULO UID

def _uid() -> str:
    """Identificador del usuario actual: su id, si no su correo, y como último recurso "anonimo"."""
    u = st.session_state.get("usuario_informacion") or {}
    return str(u.get("id") or u.get("email") or "anonimo")


# TITULO LEER

def _leer() -> dict[str, list[dict[str, Any]]]:
    """Lee el JSON de aceptaciones; devuelve un diccionario vacío si el archivo no existe o está dañado."""
    try:
        with open(_RUTA, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001 - un archivo ausente o dañado equivale a "sin aceptaciones"
        return {}


# TITULO ACEPTACIONES DE

def aceptaciones_de(uid: str | None = None) -> list[dict[str, Any]]:
    """Lista las aceptaciones registradas de un usuario (las del usuario actual si no se indica), de la más antigua a la más reciente."""
    return list(_leer().get(uid or _uid(), []))


# TITULO REGISTRAR

def registrar(v: dict[str, Any]) -> None:
    """Registra en disco que el usuario actual aceptó los términos para la vigilancia `v` (diccionario del núcleo del agente).

    Agrega una entrada con el correo, la fecha ISO, la versión de los términos y las condiciones autorizadas (id, activo,
    riesgo por operación, máximo de operaciones, intervalo y duración). Crea la carpeta `data/` si no existe y reescribe el
    JSON completo conservando las aceptaciones de los demás usuarios."""
    datos = _leer()
    u = st.session_state.get("usuario_informacion") or {}
    datos.setdefault(_uid(), []).append({
        "email": u.get("email", ""), "fecha": datetime.now().isoformat(timespec="seconds"),
        "version_terminos": VERSION_TERMINOS, "vigilancia_id": v.get("id"), "simbolo": v.get("simbolo"),
        "riesgo_pct": v.get("riesgo_pct"), "max_operaciones": v.get("max_operaciones"),
        "intervalo_min": v.get("intervalo_min"), "duracion_horas": v.get("duracion_horas"),
        "permite_cerrar": bool(v.get("permite_cerrar")),
    })
    os.makedirs(os.path.dirname(_RUTA), exist_ok=True)
    with open(_RUTA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


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
