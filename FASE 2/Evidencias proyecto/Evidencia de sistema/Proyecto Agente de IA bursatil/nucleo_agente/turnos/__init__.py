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

"""Turnos del agente en segundo plano.

NOMBRE DEL PAQUETE: nucleo_agente/turnos

Problema que resuelve: Streamlit vuelve a ejecutar el script entero cada vez que el usuario hace
algo (cambiar de sección, pulsar un botón...). Si el agente corría DENTRO de esa ejecución, cualquier
clic lo cortaba a mitad de la respuesta.

Solución: el turno del agente corre en un hilo propio (daemon). La interfaz solo lo consulta:
  * iniciar()   -> lanza el hilo con la pregunta del usuario (un turno a la vez por usuario).
  * turno_de()  -> estado actual: texto parcial, herramientas usadas, tiempo transcurrido...
  * recoger()   -> la interfaz ya mostró el resultado; el turno deja de estar "pendiente".
Al terminar, el hilo deja un aviso en nucleo_agente/notificaciones.py (la campana de la barra superior).

Detener (cancelar): un hilo no se puede matar a la fuerza a mitad de una llamada, así que cancelar()
solo PIDE la parada; el hilo la atiende en cuanto el agente emite su siguiente evento (al escribir,
casi al instante; si está dentro de una herramienta o esperando al modelo, al terminar esa llamada).
Al detenerlo se cierra el generador del agente, que descarta el turno incompleto de su historial: las
consultas siguientes no arrastran la cancelada.

Este módulo NO usa Streamlit: lo ejecuta un hilo sin contexto de la app. Las herramientas del
agente que hablan con MT5 ya serializan el acceso con MT5_LOCK, igual que antes.

Archivos: turno.py (Turno), registro.py (iniciar/cancelar/recoger), hilo.py, avisos.py, imagenes.py, formato.py.
"""
from nucleo_agente.turnos.avisos import _avisar  # noqa: F401
from nucleo_agente.turnos.formato import formatear_duracion, formatear_reloj
from nucleo_agente.turnos.hilo import _correr  # noqa: F401
from nucleo_agente.turnos.imagenes import _EXT_IMAGEN, _buscar_rutas_imagen, imagenes_de_resultado  # noqa: F401
from nucleo_agente.turnos.registro import (
    _AGENTES, _CANDADO, _TURNOS, agente_de, cancelar, hay_turno_en_curso, iniciar, recoger, registrar_agente, turno_de,
)  # noqa: F401
from nucleo_agente.turnos.turno import VISTA_RECIENTE_S, Turno


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
