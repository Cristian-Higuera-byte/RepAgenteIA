# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara historial .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Panel IZQUIERDO: historial permanente de cada orden que el agente propuso, ejecutó o se bloqueó.

Lee el historial desde core.ordenes y lo dibuja como una lista con scroll bajo la
watchlist. Es solo lectura: no confirma ni rechaza nada (eso ocurre en propuestas.py).
"""
from typing import Any

import streamlit as st

from components.agente_paneles.datos import ESTADOS
from components.agente_paneles.formato import cabecera_agente, clase_lado, detalle, escapar_html, hora, marca_auto, titulo, vacio
from core import ordenes


def fila_historial(o: dict[str, Any]) -> str:
    """Construye el HTML de una fila del historial para la orden `o`.

    Muestra hora (con marca AUTO si fue automática), insignia con el estado en su color,
    título y detalle. La clase de lado (buy/sell/cerrar) pinta la franja lateral.
    """
    # Texto y color de la insignia según el estado; gris si el estado no se conoce
    estado = str(o.get("estado") or "")
    etiqueta, color = ESTADOS.get(estado, (estado or "Desconocido", "#8b949e"))
    return (
        f"<div class='ag-row {clase_lado(o)}'>"
        f"<div class='ag-top'><span class='ag-t'>{hora(o.get('creada'))}{marca_auto(o)}</span>"
        f"<span class='ag-badge' style='color:{color};border-color:{color}55;background:{color}18'>"
        f"{escapar_html(etiqueta)}</span></div>"
        f"<div class='ag-main'>{titulo(o)}</div>{detalle(o)}</div>"
    )


def renderizar_historial_agente(limite: int = 30, altura: int = 300) -> None:
    """Dibuja el panel izquierdo con el historial de órdenes del agente.

    Recibe `limite` (máximo de órdenes a leer) y `altura` (px del contenedor con scroll).
    Antes de leer marca como vencidas las propuestas expiradas (escribe en el almacén de
    órdenes). Si la lectura falla, muestra una advertencia y no dibuja el panel.
    """
    try:
        ordenes.expirar_vencidas()  # marca como vencidas las propuestas que ya expiraron
        historial = ordenes.listar_historial(limite)
    except Exception as e:  # noqa: BLE001
        st.warning(f"No se pudo leer el historial del agente: {e}")
        return

    # Panel con clave fija: estilos.css lo apunta con el prefijo agh_
    with st.container(key="agh_panel"):
        st.html(cabecera_agente("history", "Historial del agente", "Cada orden que propone, ejecuta o se bloquea."))
        # Zona con scroll vertical de altura fija
        with st.container(height=altura, border=False, key="agh_scroll"):
            if not historial:
                st.html(vacio("history", "Aún no hay órdenes registradas."))
            else:
                st.html("".join(fila_historial(o) for o in historial))


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara historial .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
