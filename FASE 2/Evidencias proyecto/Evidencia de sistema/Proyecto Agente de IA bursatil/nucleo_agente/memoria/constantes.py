# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara constantes .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Tablas de Supabase y límites de la memoria."""

# Nombres de las tablas de Supabase (se crean con memoria_supabase.sql).
TABLA_CHATS = "agente_chats"
TABLA_MENSAJES = "agente_mensajes"
TABLA_DATOS = "agente_memoria_usuario"

# Límites de la memoria.
MAX_TURNOS_CARGADOS = 6          # cuántos turnos recientes se reenvían al modelo al retomar un chat
MAX_RESUMENES_EN_CONTEXTO = 3    # cuántos resúmenes de chats anteriores se inyectan en el prompt


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara constantes .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
