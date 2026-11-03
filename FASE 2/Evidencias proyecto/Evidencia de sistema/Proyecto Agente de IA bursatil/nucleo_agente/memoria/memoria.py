# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara memoria .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Memoria persistente del agente: la clase se arma con la base y los mixins de conversaciones, datos y contexto."""
from __future__ import annotations

from nucleo_agente.memoria.base import _BaseMemoria
from nucleo_agente.memoria.contexto import _ContextoMixin
from nucleo_agente.memoria.conversaciones import _ConversacionesMixin
from nucleo_agente.memoria.datos import _DatosMixin


# TITULO MEMORIA

class Memoria(_ConversacionesMixin, _DatosMixin, _ContextoMixin, _BaseMemoria):
    """Memoria persistente de un usuario (Supabase). Ver el docstring del paquete.

    Combina _ConversacionesMixin (chats y turnos), _DatosMixin (datos clave-valor), _ContextoMixin (texto para
    el prompt) y _BaseMemoria (estado y acceso a Supabase).
    """


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara memoria .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
