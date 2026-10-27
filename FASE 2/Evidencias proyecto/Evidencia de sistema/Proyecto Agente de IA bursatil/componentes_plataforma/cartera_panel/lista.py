# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara lista .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
cartera_panel/lista.py
----------------------
Lista de CARTERA (posiciones abiertas) que reemplaza al watchlist en la vista de
Trading cuando el usuario entra a "Cartera". Misma estética que la watchlist; cada fila
es clicable y carga ese símbolo en el gráfico central. Incluye la detección de cierres
(posiciones que desaparecen → tarjeta "cerrada" con su P/G) y, al desplegar una fila, el
detalle inline (detalle.py). Los datos salen en vivo de MT5.

Funciones principales:
  - renderizar_cartera_lista: dibuja el panel completo (encabezado, P/G total, tarjetas
    de cerradas y filas de posiciones abiertas).
  - _detectar_cierres: compara la foto anterior de posiciones con la actual en
    st.session_state para detectar cierres.
  - _renderizar_cerradas: dibuja las tarjetas de posiciones ya cerradas.
Claves de estado de sesión usadas: cartera_anterior, cartera_ganancia_perdida_real, cartera_cerradas, cartera_detalle,
cartera_cerrar, cartera_resultado y cartera_editando.
"""
import html
import re
import time

import streamlit as st

from herramientas.puente_mt5 import obtener_posiciones, obtener_historial
from herramientas import gestor_lista_activos as wl
from herramientas import almacen_cerradas

from componentes_plataforma.iconografia import icono_activo   # íconos estilo XM (comunes a todo el dashboard)

from .comun import neto, formatear_precio, css_lista, css_detalle
from .detalle import detalle_inline

# Altura en píxeles del contenedor con scroll que aloja las tarjetas y las filas de la lista.
ALTURA_LISTA = 700


# TITULO DETECTAR CIERRES

def _detectar_cierres(posicion: list):
    """Compara las posiciones actuales con la foto anterior: las que ya no están
    se cerraron (manual o automáticamente) → se registran como tarjetas cerradas.
    Guarda anti-fallo: si TODO desaparece de golpe (y había más de una), se asume
    un fallo momentáneo de MT5, no cierres reales.

    Recibe `pos`, la lista de posiciones abiertas actuales (diccionarios de MT5). No
    devuelve nada. Efectos secundarios: lee y actualiza st.session_state (cartera_anterior,
    cartera_ganancia_perdida_real, cartera_cerradas, cartera_detalle), consulta el historial de MT5 para confirmar
    cierres automáticos y persiste las tarjetas cerradas con almacen_cerradas.guardar
    (para que sobrevivan a un F5).
    """
    # Foto anterior de posiciones, tickets actuales y P/G exactos registrados por el modal.
    anterior = st.session_state.get("cartera_anterior", {})
    actuales = {p.get("ticket") for p in posicion}
    reales = st.session_state.setdefault("cartera_ganancia_perdida_real", {})   # P/G exacto de cierres manuales
    # Posiciones que estaban en la foto anterior y ya no aparecen.
    desaparecidos = [(ticket, info) for ticket, info in anterior.items() if ticket not in actuales]
    # Se ignora el caso "todo desaparece de golpe" (probable fallo momentáneo de MT5).
    if desaparecidos and not (not posicion and len(anterior) > 1):
        # Historial reciente para obtener el P/G y el precio de cierre reales.
        try:
            historial = obtener_historial(dias=1, limite=80)   # P/G y precio de cierre reales
        except Exception:
            historial = []
        nuevas = []
        # Cada posición desaparecida se convierte en una tarjeta de cerrada.
        for ticket, info in desaparecidos:
            if ticket in reales:                               # cierre manual: P/G exacto
                ganancia_perdida, cierre = reales.pop(ticket), info.get("ac")
            else:                                          # cierre automático: confirmar en historial
                h = next((x for x in historial if x.get("symbol") == info.get("real")
                          and abs(float(x.get("volumen", 0)) - float(info.get("volumen", 0))) < 1e-6), None)
                if h is None:
                    continue                               # no confirmado (posible fallo de MT5): no inventar tarjeta
                ganancia_perdida, cierre = h.get("pg"), h.get("precio_cierre")
            nuevas.append({**info, "ticket": ticket, "pg": ganancia_perdida, "cierre": cierre, "hora": time.strftime("%H:%M")})
        # Guarda las nuevas (las más recientes primero, máximo 8) y limpia el detalle abierto si corresponde.
        if nuevas:
            cerr = {c["ticket"] for c in nuevas}
            st.session_state.cartera_cerradas = (nuevas + st.session_state.get("cartera_cerradas", []))[:8]
            almacen_cerradas.guardar(st.session_state.cartera_cerradas)   # sobrevive al F5
            if st.session_state.get("cartera_detalle") in cerr:
                st.session_state.cartera_detalle = None   # cierra el detalle de la que se cerró
    # Foto actual para la próxima comparación.
    st.session_state.cartera_anterior = {
        p.get("ticket"): {"sym": wl.nombre_visible(p["symbol"]), "real": p["symbol"],
                          "side": p.get("tipo", ""), "volumen": p.get("volumen", 0),
                          "ap": float(p.get("precio_apertura", 0) or 0),
                          "ac": float(p.get("precio_actual", 0) or 0), "pg": neto(p)}
        for p in posicion}


# TITULO RENDERIZAR CERRADAS

def _renderizar_cerradas():
    """Tarjetas de posiciones cerradas (manual o auto), con detalle y 'Aceptar'.

    Lee st.session_state.cartera_cerradas y dibuja una tarjeta por cada una (símbolo, lado,
    P/G, cantidad, precios y hora). El botón "Aceptar" la descarta, actualiza el archivo
    persistente y relanza la app. No devuelve nada.
    """
    # Lista de tarjetas pendientes de aceptar por el usuario.
    cerradas = st.session_state.get("cartera_cerradas", [])
    for c in cerradas:
        # Datos de presentación de la tarjeta: ticket, lado y color según el signo del P/G.
        ticket = c["ticket"]
        lado = "buy" if c.get("side") == "Compra" else "sell"
        lado_etiqueta = "BUY" if lado == "buy" else "SELL"
        ganancia_perdida = float(c.get("pg", 0.0) or 0.0)
        cls_ganancia_perdida = "cartera-sube" if ganancia_perdida >= 0 else "cartera-baja"
        with st.container(key=f"cacerr_{ticket}"):
            # HTML de la tarjeta (estilos .cartera-cerrada y .cc-* en estatico/lista.css).
            st.markdown(
                "<div class='cartera-cerrada'>"
                "<div class='tarjeta-copytrading-superior'>"
                f"<span class='tarjeta-copytrading-icono'>{icono_activo(c.get('real', ''), 30)}</span>"
                f"<span class='tarjeta-copytrading-simbolo'>{html.escape(str(c.get('sym', '')))}"
                f"<span class='tarjeta-copytrading-insignia {lado}'>{lado_etiqueta}</span>"
                "<span class='tarjeta-copytrading-etiqueta'>CERRADA</span></span>"
                f"<span class='tarjeta-copytrading-ganancia-perdida {cls_ganancia_perdida}'>{ganancia_perdida:+,.2f}</span></div>"
                "<div class='tarjeta-copytrading-cuadricula'>"
                f"<span class='it'>Cantidad <b>{c.get('volumen', 0):,.2f}</b></span>"
                f"<span class='it'>Apertura <b>{formatear_precio(c.get('ap'))}</b></span>"
                f"<span class='it'>Cierre <b>{formatear_precio(c.get('cierre', c.get('ac')))}</b></span>"
                f"<span class='it'>Hora <b>{c.get('hora', '')}</b></span>"
                "</div></div>",
                unsafe_allow_html=True,
            )
            # Aceptar: quita la tarjeta del estado y del archivo, y vuelve a ejecutar.
            if st.button("Aceptar", key=f"cacerr_ok_{ticket}", width="stretch"):
                st.session_state.cartera_cerradas = [x for x in cerradas if x["ticket"] != ticket]
                almacen_cerradas.guardar(st.session_state.cartera_cerradas)
                st.rerun()


# TITULO RENDERIZAR CARTERA LISTA

def renderizar_cartera_lista():
    """Panel de posiciones abiertas (reemplaza al watchlist en 'Cartera').

    Obtiene las posiciones de MT5, detecta cierres, y dibuja el encabezado, el P/G total
    (que el feed en vivo actualiza con data-pj-acc), el mensaje de resultado puntual y,
    dentro de un contenedor con scroll, las tarjetas de cerradas y una fila por posición.
    Cada fila tiene un botón invisible superpuesto que despliega el detalle (rerun de
    fragmento) y una X que abre el modal de cierre (rerun de la app). No devuelve nada;
    modifica st.session_state (cartera_editando, cartera_cerradas, cartera_detalle, cartera_cerrar, cartera_resultado).
    """
    # Inyecta los estilos de la lista y del detalle.
    css_lista()
    css_detalle()
    # Posiciones abiertas en vivo desde MT5.
    posicion = obtener_posiciones()
    st.session_state.cartera_editando = False   # lo activan los editores si abren un input
    # Tras un F5 la sesión es nueva: recuperar las tarjetas cerradas del archivo.
    if "cartera_cerradas" not in st.session_state:
        st.session_state.cartera_cerradas = almacen_cerradas.leer()
    _detectar_cierres(posicion)                 # registra tarjetas de posiciones cerradas

    with st.container(key="cartera_panel"):
        # Encabezado del panel: ícono y título.
        st.markdown(
            "<div class='cartera-cabecera'>"
            "<div class='ic'><span class='cartera-icono-material'>account_balance_wallet</span></div>"
            "<div><div class='cartera-titulo'>Cartera</div>"
            "<div class='cartera-subtitulo'>Posiciones abiertas en tiempo real</div></div></div>",
            unsafe_allow_html=True,
        )

        # P/G NETO (profit + swap): así el total coincide con el P/G de la cuenta
        # que se muestra junto al saldo (account_info.profit incluye el swap).
        total = sum(neto(p) for p in posicion) if posicion else 0.0
        cls_t = "cartera-sube" if total >= 0 else "cartera-baja"
        # data-pj-acc="profit": el feed en vivo lo pinta con el MISMO dato que la
        # barra superior → ambos van siempre a la par.
        st.markdown(
            f"<div class='cartera-totales'><div><span class='lbl'>P/G total</span>"
            f"<span class='cnt'>{len(posicion)}</span></div>"
            f"<span class='val {cls_t}' data-pj-acc='profit' data-pj-zero='1' "
            f"data-pj-up='#2ebd85' data-pj-dn='#f6465d'>{total:+,.2f}</span></div>",
            unsafe_allow_html=True,
        )

        # Mensaje de error puntual (p. ej. "no se pudo cerrar").
        r = st.session_state.get("cartera_resultado")
        if r:
            cls_r = "cartera-resultado-aceptar" if r[0] == "ok" else "cartera-resultado-error"
            st.markdown(f"<div class='{cls_r}'>{html.escape(r[1])}</div>", unsafe_allow_html=True)

        # Estado vacío: sin posiciones ni tarjetas pendientes, se muestra un aviso y se termina.
        hay_cerradas = bool(st.session_state.get("cartera_cerradas"))
        if not posicion and not hay_cerradas:
            st.markdown(
                "<div class='cartera-vacio'>Nada que mostrar.<br>"
                "Las operaciones que abras aparecerán aquí.</div>",
                unsafe_allow_html=True,
            )
            return

        abierta = st.session_state.get("cartera_detalle")   # ticket de la fila desplegada
        # Zona con scroll de altura fija que contiene cerradas y abiertas.
        with st.container(height=ALTURA_LISTA, border=False, key="cartera_desplazamiento"):
            # Tarjetas de posiciones cerradas (manual o auto) con "Aceptar", dentro
            # del scroll para que compartan el mismo inset que las abiertas.
            _renderizar_cerradas()
            if not posicion:
                st.markdown("<div class='cartera-vacio' style='padding:24px 10px;'>"
                            "No tienes posiciones abiertas.</div>", unsafe_allow_html=True)
            # Una fila por posición abierta.
            for i, p in enumerate(posicion):
                # Datos de la fila: nombre visible, clave única, lado, P/G y flecha del acordeón.
                simbolo = p["symbol"]
                base = wl.nombre_visible(simbolo)
                slug = re.sub(r"\W", "", simbolo) + f"_{i}"
                ticket = p.get("ticket")
                es_seleccion = (abierta == ticket)
                cls_seleccion = " sel" if es_seleccion else ""
                lado = p.get("tipo", "")
                side = "buy" if lado == "Compra" else "sell"
                lado_etiqueta = "BUY" if lado == "Compra" else "SELL"
                prof = neto(p)
                cls_ganancia_perdida = "cartera-sube" if prof >= 0 else "cartera-baja"
                caret = "▴" if es_seleccion else "▾"

                with st.container(key=f"carow_{slug}"):
                    # Tarjeta HTML de la posición (clases .ca-* de lista.css; data-pj-pos lo repinta el feed en vivo).
                    st.markdown(
                        f"<div class='cartera-fila {side}{cls_seleccion}'>"
                        f"<span class='cartera-icono'>{icono_activo(simbolo, 36)}</span>"
                        f"<div class='cartera-medio'>"
                        f"<div class='cartera-ticket'>{html.escape(base)}"
                        f"<span class='cartera-insignia {side}'>{lado_etiqueta}</span></div>"
                        f"<div class='cartera-meta'>{p.get('volumen',0):,.2f} lotes · "
                        f"{p.get('precio_apertura',0):,.5f}</div></div>"
                        f"<div class='cartera-derecha'>"
                        f"<div class='cartera-ganancia-perdida {cls_ganancia_perdida}' data-pj-pos='{ticket}' "
                        f"data-pj-up='#2ebd85' data-pj-dn='#f6465d'>{prof:+,.2f}</div>"
                        f"<span class='cartera-caret'>{caret}</span></div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    # Clic en la fila -> despliega/pliega el detalle inline (acordeón, como XM).
                    # Rerun de FRAGMENTO (no de app): así el gráfico de col_center NO se
                    # refresca al abrir/cerrar una posición en la lista.
                    if st.button("ver", key=f"casel_{slug}"):
                        st.session_state.cartera_detalle = None if es_seleccion else ticket
                        st.session_state.pop("cartera_resultado", None)
                        st.rerun(scope="fragment")
                    # X -> abre el modal de confirmación de cierre
                    if st.button("✕", key=f"cacls_{slug}", help="Cerrar posición"):
                        st.session_state.cartera_cerrar = {
                            "ticket": ticket, "symbol": base, "profit": prof,
                            "tipo": lado, "volumen": p.get("volumen", 0),
                        }
                        st.session_state.pop("cartera_resultado", None)
                        st.rerun(scope="app")

                # Detalle desplegable justo debajo de la fila (como XM)
                if es_seleccion:
                    detalle_inline(ticket, p)


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara lista .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
