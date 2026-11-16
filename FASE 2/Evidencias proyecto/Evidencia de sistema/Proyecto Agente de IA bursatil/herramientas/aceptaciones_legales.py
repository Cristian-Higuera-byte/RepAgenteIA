# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara aceptaciones_legales .PY ---------------------------
# -------------------------------------------------------------------------------------------------------

"""
aceptaciones_legales.py
-----------------------
Registro de qué documentos legales (términos de uso, privacidad y cookies, aviso de riesgo) aceptó cada usuario, con su versión y la fecha.

Se guarda en la tabla `aceptaciones_legales` (herramientas/sql/aceptaciones_legales.sql) cuando el usuario marca la casilla al crear su cuenta. Es una constancia: si la
tabla no existe todavía o falla la conexión, no se lanza ningún error y el registro de la cuenta sigue funcionando; la función devuelve False.
"""
from typing import Optional

from herramientas import gestor_autenticacion


# TITULO REGISTRAR

def registrar(usuario_id, documentos, version: str) -> bool:
    """Guarda una fila por cada documento aceptado: `documentos` es la lista de claves (por ejemplo ["terminos", "privacidad", "riesgo"]) y `version` la versión aceptada.

    Devuelve True si se guardaron todas, False si no hay conexión con la base de datos, falta la tabla o falla el guardado."""
    cliente = gestor_autenticacion._supabase
    if cliente is None or usuario_id is None:
        return False
    try:
        for documento in documentos:
            cliente.table("aceptaciones_legales").insert({"usuario_id": usuario_id, "documento": documento, "version": version}).execute()
    except Exception:
        return False
    return True


# TITULO ULTIMA VERSION ACEPTADA

def ultima_version(usuario_id, documento: str) -> Optional[str]:
    """Devuelve la última versión del documento que aceptó el usuario, o None si no la aceptó o no se puede consultar."""
    cliente = gestor_autenticacion._supabase
    if cliente is None or usuario_id is None:
        return None
    try:
        filas = cliente.table("aceptaciones_legales").select("version").eq("usuario_id", usuario_id).eq("documento", documento).order("aceptada_en", desc=True).limit(1).execute()
        return filas.data[0]["version"] if filas.data else None
    except Exception:
        return None


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara aceptaciones_legales .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
