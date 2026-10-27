# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Memoria persistente del agente (Supabase).

Qué guarda y para qué:
  1. Conversaciones (agente_chats + agente_mensajes): cada chat guarda sus mensajes
     completos, incluidas las llamadas a herramientas. Así el usuario puede salir y
     volver, y continuar exactamente donde quedó.
  2. Resumen por conversación (agente_chats.resumen): permite recordar conversaciones
     anteriores aunque el usuario reinicie el chat, sin recargar todos sus mensajes.
  3. Datos del usuario (agente_memoria_usuario): datos duraderos clave -> valor
     (activos que sigue, perfil de riesgo, preferencias...).

Principios de diseño:
  * Best effort: si Supabase falla se lanza ErrorMemoria y el agente sigue funcionando
    sin memoria (es quien decide qué hacer; aquí nunca se cae en silencio).
  * Se carga por TURNOS COMPLETOS: jamás se corta un turno por la mitad. Un mensaje
    'tool' sin su 'tool_calls' hace que DeepSeek responda 400.
  * Cada turno se guarda en UNA sola inserción (todo o nada).
  * Todo está acotado por usuario_id: nunca se mezclan datos de usuarios distintos.

Las tablas se crean con memoria_supabase.sql. Variables del .env: SUPABASE_URL y
SUPABASE_KEY (clave service_role, solo en el servidor).

Archivos: memoria.py (clase Memoria), base.py, conversaciones.py, datos.py, contexto.py, cliente.py, validacion.py,
constantes.py y errores.py.

Este `__init__` es una fachada: reexporta la clase Memoria, ErrorMemoria, las constantes de tablas y límites
y los ayudantes internos (_ahora, _obtener_cliente, _sanear, _turno_valido) para importarlos desde un único lugar.
"""
# Reexportaciones públicas de la capa de memoria.
from nucleo_agente.memoria.cliente import _ahora, _obtener_cliente  # noqa: F401
from nucleo_agente.memoria.constantes import (  # noqa: F401
    MAX_RESUMENES_EN_CONTEXTO, MAX_TURNOS_CARGADOS, TABLA_CHATS, TABLA_DATOS, TABLA_MENSAJES,
)
from nucleo_agente.memoria.errores import ErrorMemoria
from nucleo_agente.memoria.memoria import Memoria
from nucleo_agente.memoria.validacion import _sanear, _turno_valido  # noqa: F401


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
