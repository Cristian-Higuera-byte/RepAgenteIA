"""
cartera_panel.py
----------------
Lista de CARTERA (posiciones abiertas) que reemplaza al watchlist en la vista
de Trading cuando el usuario entra a "Cartera". Misma estética que la watchlist;
cada fila es clicable y carga ese símbolo en el gráfico central. Los datos salen
en vivo de MT5 (tools.mt5_bridge.obtener_posiciones).
"""
"""
cartera_panel.py
----------------
Lista de CARTERA (posiciones abiertas) que reemplaza al watchlist en la vista
de Trading cuando el usuario entra a "Cartera". Misma estética que la watchlist;
cada fila es clicable y carga ese símbolo en el gráfico central. Los datos salen
en vivo de MT5 (tools.mt5_bridge.obtener_posiciones).
"""
import html
import re

import streamlit as st

from components.live_feed import intervalo as _intervalo
from tools.mt5_bridge import obtener_posiciones, cerrar_posicion
from tools import watchlist_manager as wl

from components.iconos import icono_activo   # íconos estilo XM (comunes a todo el dashboard)

ALTURA_LISTA = 640

_CSS = """
<style>
  div[data-testid="stElementContainer"]:has(.ca-css),
  div[data-testid="element-container"]:has(.ca-css) { display:none; }

  .st-key-ca_panel { background:#0d1117; border:1px solid #1f2937; border-radius:10px; overflow:hidden; }
  .st-key-ca_panel, .st-key-ca_panel [data-testid="stVerticalBlock"],
  .st-key-ca_scroll { gap:0 !important; }
  .st-key-ca_panel div[data-testid="stVerticalBlockBorderWrapper"] { background:transparent !important; border:none !important; }
  .st-key-ca_panel div[data-testid="stMarkdownContainer"] { margin-bottom:0 !important; }

  .ca-head { padding:14px 16px 12px; border-bottom:1px solid #1f2937; background:#0d1117; position:relative; z-index:2; }
  .ca-title { display:flex; align-items:center; gap:8px; font-size:16px; font-weight:700; color:#fff; }
  .ca-sub { font-size:12px; color:#8b949e; margin-top:2px; }

  .ca-totals { display:flex; justify-content:space-between; padding:10px 16px; border-bottom:1px solid #141a22;
      background:#0d1117; position:relative; z-index:2; }
  .ca-totals .lbl { font-size:12px; color:#8b949e; }
  .ca-totals .val { font-size:15px; font-weight:800; font-family:ui-monospace,Consolas,monospace; }

  .st-key-ca_scroll { scrollbar-gutter:stable both-edges; scrollbar-width:thin; scrollbar-color:#2b3550 transparent;
      padding-top:6px; padding-bottom:6px; }
  .st-key-ca_scroll::-webkit-scrollbar { width:6px; }
  .st-key-ca_scroll::-webkit-scrollbar-thumb { background:#2b3550; border-radius:3px; }

  [class*="st-key-carow_"] { position:relative; overflow:hidden; transition:background .15s ease; }
  [class*="st-key-carow_"] div[data-testid="stElementContainer"],
  [class*="st-key-carow_"] div[data-testid="element-container"],
  [class*="st-key-carow_"] div[data-testid="stMarkdownContainer"],
  [class*="st-key-carow_"] div[data-testid="stMarkdown"] { margin:0 !important; }

  .ca-row { display:flex; align-items:center; gap:10px; padding:11px 44px 11px 12px;
      border-bottom:1px solid #1a2130; box-sizing:border-box; line-height:1.25; }
  [class*="st-key-carow_"]:hover .ca-row { background:rgba(255,255,255,0.04); border-radius:8px; border-bottom-color:transparent; }
  .ca-row.sel { background:#1a2236; border-radius:8px; border-bottom-color:transparent; }

  .ca-ico { flex:0 0 auto; display:flex; align-items:center; }
  .ca-mid { flex:1 1 auto; min-width:0; overflow:hidden; }
  .ca-tk { font-size:15px; font-weight:700; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .ca-meta { font-size:12px; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .ca-buy { color:#2ebd85; }
  .ca-sell { color:#f6465d; }
  .ca-right { text-align:right; flex:0 0 auto; white-space:nowrap; }
  .ca-pl { font-size:15px; font-weight:700; font-variant-numeric:tabular-nums; font-family:ui-monospace,Consolas,monospace; }
  .ca-opn { font-size:11px; color:#8b949e; margin-top:2px; font-variant-numeric:tabular-nums; }
  .ca-up { color:#2ebd85; } .ca-down { color:#f6465d; }

  [class*="st-key-casel_"] { position:absolute !important; top:0 !important; right:0 !important; bottom:0 !important;
      left:0 !important; width:100% !important; height:100% !important; margin:0 !important; padding:0 !important; z-index:1; }
  [class*="st-key-casel_"] * { width:100% !important; height:100% !important; min-height:0 !important; margin:0 !important; padding:0 !important; }
  [class*="st-key-casel_"] button { opacity:0; cursor:pointer; }

  /* Botón X para cerrar la posición (por encima del overlay de selección) */
  [class*="st-key-cacls_"] { position:absolute !important; right:8px; top:50%;
      transform:translateY(-50%); width:30px !important; margin:0 !important; z-index:2; }
  [class*="st-key-cacls_"] * { margin:0 !important; }
  [class*="st-key-cacls_"] button { width:30px !important; height:30px !important; min-height:30px !important;
      padding:0 !important; background:transparent !important; border:none !important; box-shadow:none !important;
      color:#8b949e !important; border-radius:8px !important; font-size:15px !important; cursor:pointer; }
  [class*="st-key-cacls_"] button:hover { background:rgba(248,81,73,0.15) !important; color:#f85149 !important; }

  .ca-empty { padding:40px 20px; text-align:center; color:#8b949e; font-size:13px; line-height:1.6; }
  .ca-result-ok { color:#2ebd85; font-size:13px; padding:8px 14px; }
  .ca-result-err { color:#f85149; font-size:13px; padding:8px 14px; }
</style>
"""



def _neto(p: dict) -> float:
    """P/G neto de una posición (profit + swap), como lo suma MT5 en la cuenta."""
    return float(p.get("profit", 0.0) or 0.0) + float(p.get("swap", 0.0) or 0.0)

def renderizar_cartera_lista():
    """Panel de posiciones abiertas (reemplaza al watchlist en 'Cartera')."""
    st.markdown(_CSS, unsafe_allow_html=True)
    pos = obtener_posiciones()

    with st.container(key="ca_panel"):
        st.markdown(
            "<div class='ca-head'><div class='ca-title'><span>🧰</span>"
            "<span>CARTERA</span></div>"
            "<div class='ca-sub'>Posiciones abiertas en tiempo real</div></div>",
            unsafe_allow_html=True,
        )

        # P/G NETO (profit + swap): así el total coincide con el P/G de la cuenta
        # que se muestra junto al saldo (account_info.profit incluye el swap).
        total = sum(_neto(p) for p in pos) if pos else 0.0
        cls_t = "ca-up" if total >= 0 else "ca-down"
        # data-pj-acc="profit": el feed en vivo lo pinta con el MISMO dato que la
        # barra superior → ambos van siempre a la par.
        st.markdown(
            f"<div class='ca-totals'><span class='lbl'>P/G total ({len(pos)})</span>"
            f"<span class='val {cls_t}' data-pj-acc='profit' data-pj-zero='1' "
            f"data-pj-up='#2ebd85' data-pj-dn='#f6465d'>{total:+,.2f}</span></div>",
            unsafe_allow_html=True,
        )

        # Resultado del último cierre (persiste hasta el próximo cierre)
        r = st.session_state.get("ca_result")
        if r:
            cls_r = "ca-result-ok" if r[0] == "ok" else "ca-result-err"
            st.markdown(f"<div class='{cls_r}'>{html.escape(r[1])}</div>", unsafe_allow_html=True)

        if not pos:
            st.markdown(
                "<div class='ca-empty'>Nada que mostrar.<br>"
                "Las operaciones que abras aparecerán aquí.</div>",
                unsafe_allow_html=True,
            )
            return

        sel = st.session_state.get("activo_seleccionado")
        with st.container(height=ALTURA_LISTA, border=False, key="ca_scroll"):
            for i, p in enumerate(pos):
                sym = p["symbol"]
                base = wl.nombre_visible(sym)
                slug = re.sub(r"\W", "", sym) + f"_{i}"
                es_sel = (sel == sym)
                cls_sel = " sel" if es_sel else ""
                lado = p.get("tipo", "")
                cls_lado = "ca-buy" if lado == "Compra" else "ca-sell"
                prof = _neto(p)
                cls_pl = "ca-up" if prof >= 0 else "ca-down"

                with st.container(key=f"carow_{slug}"):
                    st.markdown(
                        f"<div class='ca-row{cls_sel}'>"
                        f"<span class='ca-ico'>{icono_activo(sym, 34)}</span>"
                        f"<div class='ca-mid'><div class='ca-tk'>{html.escape(base)}</div>"
                        f"<div class='ca-meta {cls_lado}'>{html.escape(lado)} · {p.get('volumen',0):,.2f} lotes</div></div>"
                        f"<div class='ca-right'><div class='ca-pl {cls_pl}' data-pj-pos='{p.get('ticket')}' "
                        f"data-pj-up='#2ebd85' data-pj-dn='#f6465d'>{prof:+,.2f}</div>"
                        f"<div class='ca-opn'>{p.get('precio_apertura',0):,.5f}</div></div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    # Clic en la fila -> carga el símbolo en el gráfico
                    if st.button("ver", key=f"casel_{slug}"):
                        st.session_state.activo_seleccionado = sym
                        st.rerun(scope="app")
                    # X -> abre el modal de confirmación de cierre
                    if st.button("✕", key=f"cacls_{slug}", help="Cerrar posición"):
                        st.session_state.ca_cerrar = {
                            "ticket": p.get("ticket"), "symbol": base, "profit": prof,
                            "tipo": lado, "volumen": p.get("volumen", 0),
                        }
                        st.session_state.pop("ca_result", None)
                        st.rerun(scope="app")


# --- Modal de confirmación de cierre (se renderiza FUERA del fragmento, en
#     app.py, como el buscador, para no chocar con el auto-refresco) ---
def _al_descartar():
    """Clic fuera del modal / Esc: se descarta la intención de cierre (si no,
    el modal reaparecería en la siguiente reejecución)."""
    st.session_state.ca_cerrar = None


def texto_cerrar(prof: float) -> str:
    """Texto del botón estilo XM: 'Cerrar con pérdida de -$220.00' /
    'Cerrar con ganancia de $280.00'. (live_feed.py usa el mismo formato.)"""
    verbo = "ganancia" if prof >= 0 else "pérdida"
    signo = "-" if prof < 0 else ""
    return f"Cerrar con {verbo} de {signo}${abs(prof):,.2f}"


# Estilo copiado del modal de XM: tarjeta azul oscuro redondeada, sin "X",
# botón grande con el monto (naranja P&J en vez del azul de XM) y "Cancelar" con borde. Todo acotado con :has()
# a ESTE modal (el contenedor del botón se llama ca_btncerrar_<ticket>).
_SEL = "[data-testid='stDialog']:has([class*='st-key-ca_btncerrar_'])"
_CSS_MODAL = f"""
<style>
  /* Centrado: el fondo del diálogo (Streamlit 1.64) es un flex con
     align-items:flex-start; el diálogo es un section, no un div. */
  {_SEL} {{ align-items:center !important; background:rgba(5,8,15,.55) !important; }}
  /* Colores de la paleta del dashboard (paneles #0d1117, bordes #30363d) */
  {_SEL} > div {{
    background:#0d1117 !important; border:1px solid #30363d !important;
    border-radius:16px !important;
    width:460px !important; max-width:calc(100% - 32px) !important;
    box-shadow:0 18px 50px rgba(0,0,0,.55) !important;
  }}
  {_SEL} button[aria-label='Close'] {{ display:none !important; }}
  {_SEL} h2, {_SEL} [slot='title'] {{
    color:#ffffff !important; font-size:25px !important; font-weight:700 !important;
    padding:30px 30px 10px !important;
  }}
  {_SEL} [data-testid='stVerticalBlock'] {{ gap:14px !important; }}
  {_SEL} .st-key-ca_cerrar_ok button,
  {_SEL} .st-key-ca_cerrar_cancel button {{
    height:70px !important; border-radius:12px !important; width:100% !important;
  }}
  /* Botón principal con el naranja del logo P&J (mismo degradado que nav_bar.py) */
  {_SEL} .st-key-ca_cerrar_ok button {{
    background:linear-gradient(135deg,#ff4b4b 0%,#ff8f00 100%) !important;
    border:none !important; color:#ffffff !important;
  }}
  {_SEL} .st-key-ca_cerrar_ok button:hover {{ filter:brightness(1.1) !important; }}
  {_SEL} .st-key-ca_cerrar_cancel button {{
    background:#161b22 !important; border:1px solid #30363d !important; color:#ffffff !important;
  }}
  {_SEL} .st-key-ca_cerrar_cancel button:hover {{ border-color:#58a6ff !important; background:#21262d !important; }}
  {_SEL} .st-key-ca_cerrar_ok button p,
  {_SEL} .st-key-ca_cerrar_cancel button p {{
    font-size:20px !important; font-weight:700 !important; color:#ffffff !important;
  }}
</style>
"""


@st.dialog("¿Quiere cerrar su posición?", on_dismiss=_al_descartar)
def _dialogo_cerrar():
    c = st.session_state.get("ca_cerrar") or {}
    ticket = c.get("ticket")
    # P/G FRESCO de MT5 al abrir (el de la fila podía tener hasta 5 s de atraso:
    # la fila la pinta el feed en vivo, pero el dato guardado era del último refresco).
    prof = c.get("profit", 0.0)
    try:
        fresca = next((p for p in obtener_posiciones() if p.get("ticket") == ticket), None)
        if fresca:
            prof = _neto(fresca)
    except Exception:
        pass
    st.markdown(_CSS_MODAL, unsafe_allow_html=True)
    etiqueta = texto_cerrar(prof)
    # El contenedor lleva el ticket en su clave: live_feed.py actualiza el texto
    # del botón en vivo con el P/G neto de esa posición (mismo dato que la fila).
    with st.container(key=f"ca_btncerrar_{ticket}"):
        cerrar = st.button(etiqueta, type="primary", width="stretch", key="ca_cerrar_ok")
    if cerrar:
        res = cerrar_posicion(c.get("ticket"))
        if "error" in res:
            st.session_state.ca_result = ("error", f"No se pudo cerrar: {res['error']}")
        else:
            st.session_state.ca_result = (
                "ok", f"Posición de {c.get('symbol','')} cerrada ({res.get('profit', prof):+,.2f} USD)")
        st.session_state.ca_cerrar = None
        st.rerun()
    if st.button("Cancelar", width="stretch", key="ca_cerrar_cancel"):
        st.session_state.ca_cerrar = None
        st.rerun()


def render_modal_cerrar():
    """Llamar desde app.py (fuera de los fragmentos en vivo)."""
    if st.session_state.get("ca_cerrar"):
        _dialogo_cerrar()