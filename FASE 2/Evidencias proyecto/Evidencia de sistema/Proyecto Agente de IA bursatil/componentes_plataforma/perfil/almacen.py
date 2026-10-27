# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara almacen .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Almacén del perfil de usuario: tabla `perfiles_usuario` de Supabase, o un archivo local si Supabase no está configurado.

La tabla se crea con `esquema.sql` (se ejecuta una vez en el editor SQL de Supabase). Cada usuario tiene UNA fila identificada
por `usuario_id` (el id de la tabla `usuarios`). Solo se leen y escriben los campos de `CAMPOS`: cualquier otra clave se ignora,
para que un formulario nunca pueda tocar columnas ajenas (como `verificacion`). Sin credenciales de Supabase (desarrollo y pruebas)
se usa `data/perfiles_locales.json`, ignorado por git, con la misma interfaz.
"""
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from herramientas import gestor_autenticacion

# Nombre de la tabla en Supabase.
TABLA = "perfiles_usuario"

# Columnas que el usuario puede escribir desde el perfil (la verificación de identidad la fija el equipo, no el formulario).
CAMPOS = (
    "nombres", "apellidos", "apodo", "fecha_nacimiento", "nacionalidad", "genero",
    "tipo_documento", "numero_documento", "pais_documento", "vencimiento_documento",
    "telefono_prefijo", "telefono_movil", "telefono_alterno",
    "pais", "region", "ciudad", "direccion", "codigo_postal",
    "situacion_laboral", "ocupacion", "fuente_fondos", "rango_ingresos", "rango_patrimonio",
    "experiencia", "objetivo", "tolerancia_riesgo", "instrumentos", "es_pep",
    "idioma", "zona_horaria", "moneda_visualizacion", "notificaciones",
)
# Columnas que solo se leen (las controla el sistema).
SOLO_LECTURA = ("verificacion", "creado_en", "actualizado_en")

# Archivo local usado cuando no hay Supabase: carpeta data/ en la raíz del proyecto (dos niveles sobre este paquete).
_RUTA_LOCAL = Path(__file__).resolve().parents[2] / "data" / "perfiles_locales.json"


# TITULO MODO

def modo() -> str:
    """Dónde se guarda el perfil ahora: "supabase" si hay credenciales y cliente, o "local" (archivo) en desarrollo."""
    return "supabase" if gestor_autenticacion._supabase is not None else "local"


# TITULO A JSON

def _serializable(valor: Any) -> Any:
    """Convierte fechas a texto ISO (AAAA-MM-DD) para guardarlas en JSON o en una columna `date`."""
    return valor.isoformat() if isinstance(valor, (date, datetime)) else valor


# TITULO LEER LOCAL

def _leer_local() -> dict[str, dict[str, Any]]:
    """Lee el archivo local de perfiles; diccionario vacío si no existe o está dañado."""
    try:
        return json.loads(_RUTA_LOCAL.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - archivo ausente o dañado equivale a "sin perfiles"
        return {}


# TITULO LEER

def leer(usuario_id: Any) -> dict[str, Any]:
    """Devuelve el perfil guardado del usuario (diccionario vacío si todavía no tiene), solo con columnas conocidas.

    Con Supabase consulta la fila de `perfiles_usuario`; si la consulta falla devuelve un diccionario con la clave
    `_error` y el motivo, para que la pantalla lo muestre sin romperse."""
    if modo() == "local":
        return dict(_leer_local().get(str(usuario_id), {}))
    try:
        r = gestor_autenticacion._supabase.table(TABLA).select("*").eq("usuario_id", int(usuario_id)).limit(1).execute()
    except Exception as e:  # noqa: BLE001 - la pantalla debe seguir funcionando aunque falle la red
        return {"_error": f"No se pudo leer el perfil: {e}"}
    fila = r.data[0] if r.data else {}
    return {k: v for k, v in fila.items() if k in CAMPOS or k in SOLO_LECTURA}


# TITULO GUARDAR

def guardar(usuario_id: Any, campos: dict[str, Any]) -> dict[str, Any]:
    """Guarda (crea o actualiza) los campos del perfil del usuario y devuelve {"ok": bool, "mensaje": str}.

    Solo se escriben las claves de `CAMPOS`; las fechas pasan a texto ISO. Con Supabase usa un `upsert` sobre `usuario_id`
    (una fila por usuario) y marca la fecha de actualización; en modo local mezcla los campos con lo ya guardado."""
    limpio = {k: _serializable(v) for k, v in campos.items() if k in CAMPOS}
    if not limpio:
        return {"ok": False, "mensaje": "No hay datos para guardar."}
    if modo() == "local":
        datos = _leer_local()
        datos.setdefault(str(usuario_id), {}).update(limpio)
        os.makedirs(_RUTA_LOCAL.parent, exist_ok=True)
        _RUTA_LOCAL.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "mensaje": "Datos guardados (modo local: Supabase no está configurado)."}
    try:
        fila = {"usuario_id": int(usuario_id), "actualizado_en": datetime.now().astimezone().isoformat(), **limpio}
        gestor_autenticacion._supabase.table(TABLA).upsert(fila, on_conflict="usuario_id").execute()
    except Exception as e:  # noqa: BLE001 - se informa al usuario con el motivo
        texto = str(e)
        if "duplicate" in texto.lower() or "unique" in texto.lower():
            if "apodo" in texto.lower():
                return {"ok": False, "mensaje": "Ese apodo ya está en uso. Elige otro."}
            return {"ok": False, "mensaje": "Ese documento ya está registrado en otra cuenta."}
        return {"ok": False, "mensaje": f"No se pudieron guardar los datos: {texto}"}
    return {"ok": True, "mensaje": "Datos guardados."}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara almacen .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
