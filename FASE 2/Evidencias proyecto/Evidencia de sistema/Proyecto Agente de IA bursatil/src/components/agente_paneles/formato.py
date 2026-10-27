# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara formato .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Utilidades de formato de los paneles del agente.

Funciones puras que convierten datos de órdenes y vigilancias (diccionarios del núcleo del
agente) en fragmentos HTML o texto para los paneles. Todo texto que viene del agente o de
MT5 se escapa con `escapar_html` para evitar inyección de HTML. Las clases CSS que
generan (ag-row, ag-head, ag-kv, ...) están definidas en estilos.css.
"""
import html
from datetime import datetime
from typing import Any


def escapar_html(valor: Any) -> str:
    """Convierte cualquier valor a texto seguro para incrustar en HTML.

    Recibe `valor` (None se trata como cadena vacía) y devuelve la cadena con `& < > " '`
    escapados.
    """
    return html.escape("" if valor is None else str(valor), quote=True)


def numero(valor: Any) -> str:
    """Formatea un precio o nivel con hasta 5 decimales sin ceros sobrantes.

    Devuelve "—" si el valor es None, 0 o vacío (sin dato). Si no se puede convertir a
    número devuelve el valor escapado tal cual.
    """
    # Sin dato: guion largo como marcador visual
    if valor in (None, 0, ""):
        return "—"
    try:
        return f"{float(valor):.5f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return escapar_html(valor)


def hora(iso: Any) -> str:
    """Formatea una marca de tiempo ISO como hora corta.

    Devuelve "HH:MM" si la fecha es de hoy y "dd/mm HH:MM" en otro caso. Si el valor no es
    una fecha ISO válida lo devuelve escapado sin transformar.
    """
    try:
        dt = datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        return escapar_html(iso)
    return dt.strftime("%H:%M") if dt.date() == datetime.now().date() else dt.strftime("%d/%m %H:%M")


def titulo(o: dict[str, Any]) -> str:
    """Construye el título HTML de una orden (lado, volumen y símbolo).

    Para órdenes de cierre devuelve "CERRAR #ticket · SIMBOLO"; para aperturas, una insignia
    coloreada con la clase `buy` o `sell` (según compra/venta), el volumen y el símbolo.
    Recibe `o`, el diccionario de la orden, y devuelve un fragmento HTML ya escapado.
    """
    simbolo = escapar_html(o.get("simbolo") or "—")
    # Cierre de posición: se muestra el ticket objetivo si existe
    if o.get("accion") == "cerrar":
        ticket = f"#{escapar_html(o['ticket_objetivo'])}" if o.get("ticket_objetivo") else "posición"
        return f"CERRAR {ticket} · {simbolo}"
    # Apertura: la clase CSS colorea el lado (compra = buy, venta = sell)
    lado = str(o.get("lado") or "").lower()
    clase = "buy" if lado == "compra" else "sell" if lado == "venta" else ""
    try:
        vol = f" {float(o['volumen']):g}" if o.get("volumen") else ""
    except (TypeError, ValueError):
        vol = ""
    return f"<span class='{clase}'>{escapar_html(lado.upper() or '—')}</span>{vol} · {simbolo}"


def detalle(o: dict[str, Any]) -> str:
    """Devuelve el texto de detalle de una orden como bloque HTML (o "" si no hay texto).

    En estados finales (ejecutada, rechazada por riesgo, error) prioriza el `detalle` del
    resultado; en los demás, la `justificacion` del agente. El texto se recorta a 110
    caracteres y el completo queda en el atributo title (tooltip).
    """
    # Elige qué texto mostrar según el estado de la orden
    if o.get("estado") in ("EJECUTADA", "RECHAZADA_RIESGO", "ERROR"):
        txt = o.get("detalle") or o.get("justificacion")
    else:
        txt = o.get("justificacion") or o.get("detalle")
    # Limpia y recorta para que la fila del historial no crezca demasiado
    txt = (txt or "").strip()
    corto = txt if len(txt) <= 110 else txt[:107] + "…"
    return f"<div class='ag-det' title='{escapar_html(txt)}'>{escapar_html(corto)}</div>" if txt else ""


def clase_lado(o: dict[str, Any]) -> str:
    """'buy' | 'sell' | 'cerrar': define el color de la franja lateral de la fila."""
    if o.get("accion") == "cerrar":
        return "cerrar"
    lado = str(o.get("lado") or "").lower()
    return "buy" if lado == "compra" else "sell" if lado == "venta" else "cerrar"


def cabecera_agente(icono: str, titulo: str, subtitulo: str) -> str:
    """Cabecera de panel (icono Material + título + subtítulo), igual que 'Lista de activos'."""
    return (
        f"<div class='ag-head'><div class='ic'><span class='ag-mi'>{escapar_html(icono)}</span></div>"
        f"<div><div class='ag-title'>{escapar_html(titulo)}</div><div class='ag-sub'>{escapar_html(subtitulo)}</div></div></div>"
    )


def vacio(icono: str, texto: str) -> str:
    """Devuelve el HTML del mensaje de panel vacío (icono Material + texto, clase `ag-empty`)."""
    return f"<div class='ag-empty'><span class='ag-mi'>{escapar_html(icono)}</span>{escapar_html(texto)}</div>"


def marca_auto(o: dict[str, Any]) -> str:
    """Etiqueta AUTO si la orden la ejecutó una vigilancia automática (sin confirmación manual)."""
    return "<span class='ag-auto'>AUTO</span>" if o.get("origen") == "automatica" else ""


def par_clave_valor(etiqueta: str, valor: str, clase: str = "") -> str:
    """Devuelve una celda etiqueta/valor (`ag-kv`) para las cuadrículas de datos.

    `valor` se inserta sin escapar (el llamador ya lo escapó o es HTML propio); `clase`
    opcional (`pos`/`neg`) colorea el valor.
    """
    return f"<div class='ag-kv'><span>{escapar_html(etiqueta)}</span><b class='{clase}'>{valor}</b></div>"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara formato .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
