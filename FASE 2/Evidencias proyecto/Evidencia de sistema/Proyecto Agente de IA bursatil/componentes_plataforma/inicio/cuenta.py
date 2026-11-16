# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara cuenta .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Bloque de cuenta de Inicio: encabezado (saludo, chip de cuenta, Operar), tarjeta principal (equity, P/G,
saldo y márgenes) y "Salud de la cuenta". Los números llevan data-pj-* y los pinta el feed en vivo.

Lee la cuenta de MetaTrader 5 (vía `obtener_info_cuenta`) y escribe HTML con `st.html`; los botones
modifican `st.session_state` (modal de cuentas, ocultar montos, navegación). Está pensado para
ejecutarse dentro de un fragmento de Streamlit declarado en panel.py.
"""
import streamlit as st

# Semáforo de margen, formateo de dinero e íconos Material de la vista Inicio.
from componentes_plataforma.inicio.formato import estado_margen, formatear_dinero, icono_material
# Consulta de los datos de la cuenta conectada en MT5.
from herramientas.puente_mt5 import obtener_info_cuenta


# TITULO DIBUJAR CUENTA

def dibujar_cuenta(nombre: str):
    """Dibuja el encabezado, la tarjeta principal de equity y la tarjeta «Salud de la cuenta».

    Recibe el `nombre` completo del usuario (se usa solo el primer nombre en el saludo). Si MT5 no
    responde muestra una advertencia y termina. Los botones actualizan session_state y relanzan la app
    (chip de cuenta, Operar) o solo el fragmento (ojo de ocultar montos). Los números llevan atributos
    `data-pj-*` para que el feed del navegador los mantenga actualizados.
    """
    # Datos de la cuenta; si MT5 devuelve error no hay nada que mostrar.
    info = obtener_info_cuenta()
    if "error" in info:
        st.warning("No se pudo conectar con el bróker. Revisa la conexión para ver tu cuenta.")
        return
    # Campos de la cuenta con valores por defecto seguros.
    moneda = info.get("currency", "USD")
    inicio_sesion = info.get("login", "—")
    tipo = info.get("tipo", "Demo")
    equity = info.get("equity", 0.0)
    balance = info.get("balance", 0.0)
    profit = info.get("profit", 0.0)
    margin = info.get("margin", 0.0)
    libre = info.get("margin_free", 0.0)
    ml = info.get("margin_level", 0.0)
    lev = info.get("leverage", 0)
    # Porcentaje del equity usado como margen (0 si no hay equity para evitar división por cero).
    uso = (margin / equity * 100) if equity else 0.0
    # Si es True los montos se reemplazan por puntos (botón de ojo).
    oculto = st.session_state.get("inicio_ocultar", False)

    # Encabezado: saludo + chip de cuenta + Operar
    h1, h2, h3 = st.columns([3, 1.6, 0.8], vertical_alignment="bottom")
    with h1:
        st.html(f"<p class='inicio-saludo'>Hola{', ' + nombre.split()[0] if nombre else ''}</p>"
                "<div class='inicio-titulo'>Resumen de tu cuenta</div>")
    with h2:
        if st.button(f"{tipo} · #{inicio_sesion}", key="inicio_seleccion", icon=":material/account_balance_wallet:",
                     width="stretch"):
            st.session_state.inicio_modal_cuentas = True
            st.rerun()
    with h3:
        if st.button("Operar", key="inicio_operar", icon=":material/trending_up:", width="stretch"):
            st.session_state.navegacion_activo = "trading"
            st.rerun()

    def vivo(campo, texto, formato_="usd", extra=""):
        """Devuelve un `<span>` con atributos data-pj-acc/data-pj-fmt para que el feed actualice el valor.

        Recibe el nombre del `campo` de la cuenta, el `texto` inicial, el formato (`fmt_`: usd, pct o
        signed) y atributos HTML `extra`. Si los montos están ocultos devuelve «••••».
        """
        if oculto:
            return "••••"
        return f"<span data-pj-acc='{campo}' data-pj-fmt='{formato_}' {extra}>{texto}</span>"

    # Dos columnas: tarjeta principal (más ancha) y salud de la cuenta.
    c_destacado, c_salud = st.columns([1.75, 1], gap="medium")
    with c_destacado:
        with st.container(key="inicio_destacado"):
            if st.button("", key="inicio_ojo", help="Mostrar montos" if oculto else "Ocultar montos",
                         icon=":material/visibility:" if oculto else ":material/visibility_off:"):
                st.session_state.inicio_ocultar = not oculto
                st.rerun(scope="fragment")
            # Signo del P/G flotante: define clase de color e ícono de tendencia.
            sube = profit >= 0
            # La moneda va FUERA del número en vivo (con el sufijo en un atributo
            # el espacio se perdía y se veía "-4,492.00USD").
            ganancia_perdida_html = ("••••" if oculto else
                       f"<span data-pj-acc='profit' data-pj-fmt='signed'>{profit:+,.2f}</span>"
                       f"<span style='margin-left:4px;'>{moneda}</span>")
            # Tarjeta principal: equity grande, P/G flotante y los tres indicadores (saldo, margen libre y usado).
            st.html(
                "<div class='destacado-superior'><span class='destacado-etiqueta'>Equity</span>"
                f"<span class='destacado-insignia'>{tipo}</span></div>"
                f"<div class='destacado-equity'>{vivo('equity', formatear_dinero(equity))}<small>{moneda}</small></div>"
                f"<div class='destacado-ganancia-perdida {'up' if sube else 'dn'}'>"
                f"{icono_material('trending_up' if sube else 'trending_down', tamano=18)}{ganancia_perdida_html}"
                "<span class='t'>P/G flotante</span></div>"
                "<div class='kpis'>"
                f"<div class='kpi'><div class='k'>Saldo</div><div class='v'>{vivo('balance', formatear_dinero(balance))}</div></div>"
                f"<div class='kpi'><div class='k'>Margen libre</div><div class='v'>{vivo('margin_free', formatear_dinero(libre))}</div></div>"
                f"<div class='kpi'><div class='k'>Margen usado</div><div class='v'>{vivo('margin', formatear_dinero(margin))}</div></div>"
                "</div>"
            )
    with c_salud:
        with st.container(key="inicio_salud"):
            # Semáforo de margen: texto y color según el nivel de margen.
            estado, columna = estado_margen(ml)
            st.html(
                "<div class='salud-titulo'>Salud de la cuenta</div>"
                "<div class='salud-nivel'><span class='k'>Nivel de margen</span>"
                f"<span class='salud-estado' style='color:{columna};background:{columna}1f;'>{estado}</span></div>"
                f"<div class='salud-nivel' style='margin-top:0'><span class='v' style='color:{columna};'>"
                f"<span data-pj-acc='margin_level' data-pj-fmt='pct'>{(f'{ml:,.2f}%' if ml else '—')}</span>"
                "</span></div>"
                "<div class='salud-barra-etiqueta'><span>Margen usado del equity</span>"
                f"<b><span data-pj-acc='uso_margen' data-pj-fmt='pct'>{uso:,.2f}%</span></b></div>"
                f"<div class='salud-barra'><div data-pj-bar='uso_margen' style='width:{min(uso, 100):.1f}%;'></div></div>"
                "<div class='salud-filas'>"
                f"<div class='salud-fila'><span class='k'>Apalancamiento</span><span class='v'>{f'{lev}:1' if lev else '—'}</span></div>"
                f"<div class='salud-fila'><span class='k'>Crédito</span><span class='v'>"
                f"<span data-pj-acc='credit' data-pj-fmt='usd'>{formatear_dinero(info.get('credit', 0.0))}</span></span></div>"
                f"<div class='salud-fila'><span class='k'>Servidor</span><span class='v'>{info.get('servidor', '—')}</span></div>"
                "</div>"
            )


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara cuenta .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
