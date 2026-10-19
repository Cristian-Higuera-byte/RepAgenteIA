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

"""Paneles del agente en los costados del dashboard (Fase 1).

NOMBRE DEL PAQUETE: components/agente_paneles

  * renderizar_historial_agente()   -> panel IZQUIERDO (bajo la watchlist): historial
    permanente de cada orden que el agente propuso, ejecutada, rechazada o bloqueada.
  * renderizar_ordenes_propuestas() -> panel DERECHO (sobre el ticket): propuestas
    pendientes con Confirmar / Rechazar, interruptor de emergencia y avisos.

Se llaman desde app.py (vistas Trading y Cartera), así que se dibujan en CADA ejecución de la
app, hagas o no una petición al agente (ya no dependen del chat). app.py llama una sola vez a
inyectar_estilos_agente() para cargar el CSS de ambos paneles.

Vigilancia automática (core/vigilancia.py): el panel derecho muestra además las vigilancias pendientes de
autorizar (con su botón Autorizar) y las activas (con su estado y un botón Detener). Lo que el motor
ejecuta solo queda en el historial marcado como AUTO.

No usan run_every: un temporizador reinicia la ejecución en curso y cortaría la respuesta
del agente mientras escribe. En su lugar, chat/turno_vivo.py hace un st.rerun() al terminar un
turno en el que el agente propuso algo, y Confirmar / Rechazar refrescan toda la app.

Solo este módulo (vía core.ordenes.confirmar_orden) puede hacer que una orden llegue a MT5.

Archivos: historial.py, propuestas.py, vigilancias.py, formato.py, datos.py + estados.json y estilos.css.

Este __init__ es además una fachada: reexporta `renderizar_historial_agente`,
`renderizar_ordenes_propuestas` y `cabecera_agente` desde sus módulos, y define
`inyectar_estilos_agente`, para que app.py importe todo desde un único punto.
"""
import streamlit as st

from components.agente_paneles.estilos import CSS
from components.agente_paneles.formato import cabecera_agente
from components.agente_paneles.historial import renderizar_historial_agente
from components.agente_paneles.propuestas import renderizar_ordenes_propuestas


def inyectar_estilos_agente() -> None:
    """Inyecta en la página el CSS de los dos paneles del agente (historial y propuestas).

    Efecto secundario: escribe un bloque `<style>` en la app mediante `st.html`. Debe
    llamarse UNA sola vez por ejecución (lo hace app.py); no recibe ni devuelve nada.
    """
    st.html(CSS)


# API pública del paquete (lo que app.py puede importar directamente)
__all__ = ["inyectar_estilos_agente", "renderizar_historial_agente", "renderizar_ordenes_propuestas", "cabecera_agente"]


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
