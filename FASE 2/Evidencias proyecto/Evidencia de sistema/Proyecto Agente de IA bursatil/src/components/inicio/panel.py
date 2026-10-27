# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara panel .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Panel de Inicio: arma la vista con sus bloques (cuenta, accesos rápidos, posiciones, historial,
promociones y modal de cuentas). Los fragmentos `run_every` se declaran aquí porque su intervalo depende de
si el feed en vivo está activo en ese momento.

Es el punto de entrada de la vista Inicio: lo importan `__init__.py` y `inicio_panel.py`.
"""
import streamlit as st

# Bloques de la vista y sus datos, estilos y formateadores.
from components.inicio.cuenta import dibujar_cuenta
from components.inicio.datos import ACCIONES, PROMOS
from components.inicio.estilos import CSS
from components.inicio.formato import icono_material
from components.inicio.historial import dibujar_historial
from components.inicio.modal_cuentas import modal_cuentas
from components.inicio.posiciones import dibujar_posiciones
# Intervalo de refresco de los fragmentos según haya o no feed en vivo.
from components.flujo_precios import intervalo as _intervalo
# Conexión a MetaTrader 5.
from tools.puente_mt5 import inicializar_mt5


def _ir_o_avisar(destino, titulo: str) -> None:
    """Acción de un acceso rápido (`on_click`): cambia a la vista `destino` o avisa si todavía no existe.

    Se ejecuta antes de que Streamlit vuelva a correr el script, así la vista nueva se dibuja en una sola pasada (sin
    `st.rerun()`). Recibe el destino (clave de `nav_activo` o vacío) y el título del acceso; no devuelve nada."""
    if destino:
        st.session_state.nav_activo = destino
    else:
        st.toast(f"{titulo}: disponible próximamente.")


def renderizar_panel_inicio(main=None):
    """Dibuja la vista Inicio completa: cuenta, accesos rápidos, posiciones, historial y promociones.

    El parámetro `main` no se usa; se conserva por compatibilidad con la firma de los demás paneles.
    Inicializa MT5, inyecta los estilos, declara los fragmentos en vivo y, al final, abre el modal de
    cuentas si `ini_modal_cuentas` está activo. Modifica `st.session_state` (ini_ocultar, nav_activo).
    """
    # Asegura la conexión con MT5 y carga los estilos de la vista.
    inicializar_mt5()
    st.html(CSS)

    # Estado inicial del botón de ocultar montos.
    if "ini_ocultar" not in st.session_state:
        st.session_state.ini_ocultar = False
    # Nombre del usuario para el saludo (vacío si no hay sesión).
    usuario = st.session_state.get("usuario_info") or {}
    nombre = (usuario.get("nombre") if isinstance(usuario, dict) else "") or ""

    # Cuenta (en vivo vía feed; sin recarga periódica si hay feed)
    @st.fragment(run_every=_intervalo("2s"))
    def _cuenta_vivo():
        """Fragmento de la tarjeta de cuenta; su refresco periódico depende del feed en vivo."""
        dibujar_cuenta(nombre)

    # Posiciones abiertas (precio y P/G en vivo por el feed)
    @st.fragment(run_every=_intervalo("2s", "5s"))
    def _posiciones_vivo():
        """Fragmento de posiciones abiertas; el precio y el P/G los actualiza el feed."""
        dibujar_posiciones()

    # Historial de operaciones cerradas. Se refresca cada pocos segundos para que una
    # operación recién cerrada aparezca sola (entran filas nuevas al cerrar posiciones).
    @st.fragment(run_every=_intervalo("8s", "12s"))
    def _historial():
        """Fragmento del historial; se refresca solo para mostrar operaciones recién cerradas."""
        dibujar_historial()

    # Contenido centrado con ancho máximo
    with st.container(key="ini_wrap"):
        _cuenta_vivo()

        st.html("<div class='ini-sec'><h3>Accesos rápidos</h3></div>")
        # Una tarjeta por acceso rápido; cada una lleva un botón invisible que navega al destino.
        acc_cols = st.columns(len(ACCIONES), gap="medium")
        for i, (ic, color, titulo, sub, dest) in enumerate(ACCIONES):
            with acc_cols[i]:
                with st.container(key=f"accrow_{i}"):
                    st.html(
                        f"<div class='acc-card'><div class='acc-ic' style='background:{color}1f;'>"
                        f"{icono_material(ic, color)}</div><div class='acc-tx'><div class='acc-t'>{titulo}</div>"
                        f"<div class='acc-s'>{sub}</div></div>{icono_material('chevron_right')}</div>"
                    )
                    st.button(titulo, key=f"accsel_{i}", on_click=_ir_o_avisar, args=(dest, titulo))

        _posiciones_vivo()

        _historial()

        st.html("<div class='ini-sec'><h3>Promociones</h3></div>")
        # Cuadrícula de promociones a partir de datos.json.
        st.html("<div class='promo-grid'>" + "".join(
            f"<div class='promo-card {c}'>{icono_material(ic, color)}<h4>{t}</h4><p>{d}</p></div>"
            for c, ic, color, t, d in PROMOS) + "</div>")

    # Modal selección de cuenta (fuera de los fragmentos en vivo)
    if st.session_state.get("ini_modal_cuentas"):
        modal_cuentas()


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara panel .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
