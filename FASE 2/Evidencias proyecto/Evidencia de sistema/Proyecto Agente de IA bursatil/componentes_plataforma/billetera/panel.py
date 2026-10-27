# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara panel .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Vista "Billetera": saldo virtual, recarga de saldo de prueba, compra de planes y movimientos.

IMPORTANTE: el saldo es de prueba y no tiene valor monetario; la vista lo dice de entrada. Los botones de depósito y retiro reales quedan
visibles pero desactivados, para cuando existan cuentas reales. El saldo y los movimientos los maneja `herramientas/billetera.py`; los planes se
compran con el mismo callback que usa la vista de Planes (`planes.panel.comprar_con_billetera`), así el plan queda activo con origen «pago».
"""
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

import configuracion
from componentes_plataforma import _estaticos
from componentes_plataforma.planes.panel import comprar_con_billetera, precio_de
from herramientas import billetera, cuota_ia, demanda

# Hoja de estilos de la vista, junto a este archivo
_CSS = Path(__file__).parent / "estilos.css"
# Claves de session_state compartidas con la vista de Planes (aviso de la última compra y su error; se muestran una vez)
_CLAVE_AVISO = "planes_aviso"
_CLAVE_ERROR = "planes_error"
# Aviso o error de la última recarga
_CLAVE_RECARGA = "billetera_recarga"
# Texto visible de cada tipo de movimiento
_TIPOS = {"bono": "Saldo inicial", "recarga_virtual": "Recarga de prueba", "compra_plan": "Compra de plan", "ajuste": "Ajuste",
          "deposito_real": "Depósito", "retiro_real": "Retiro", "resultado_operacion": "Resultado de operación",
          "comision_pagada": "Comisión pagada (copy trading)", "comision_cobrada": "Comisión cobrada (copy trading)"}


# TITULO MONEDA

def _usd(x: float, signo: bool = False) -> str:
    """Monto con dos decimales, coma decimal y punto de miles (por ejemplo «1.250,00 USD»); con `signo` agrega + a los positivos."""
    texto = f"{abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    prefijo = "-" if x < 0 else ("+" if signo and x > 0 else "")
    return f"{prefijo}{texto} {configuracion.BILLETERA['moneda']}"


# TITULO RECARGAR

def _recargar(monto) -> None:
    """Callback del botón «Recargar»: suma `monto` de saldo de prueba y deja el resultado (éxito o error legible) en session_state."""
    try:
        nuevo = billetera.recargar_virtual(float(monto))
        st.session_state[_CLAVE_RECARGA] = ("ok", f"Recargaste {_usd(float(monto))}. Saldo: {_usd(nuevo)}.")
    except (billetera.ErrorBilletera, TypeError, ValueError) as e:
        st.session_state[_CLAVE_RECARGA] = ("error", str(e) or "Elige un monto para recargar.")


# TITULO TABLA MOVIMIENTOS

def _tabla_movimientos(movs: list) -> pd.DataFrame:
    """Tabla de movimientos para mostrar (fecha local, tipo, concepto, monto con signo y saldo que quedó), del más reciente al más antiguo."""
    filas = []
    for m in movs:
        try:
            fecha = datetime.fromisoformat(str(m["creado_en"]).replace("Z", "+00:00")).astimezone().strftime("%d-%m-%Y %H:%M")
        except (KeyError, ValueError):
            fecha = ""
        filas.append({"Fecha": fecha, "Tipo": _TIPOS.get(m.get("tipo"), m.get("tipo", "")), "Concepto": m.get("concepto", ""),
                      "Monto": _usd(float(m.get("monto", 0)), True), "Saldo": _usd(float(m.get("saldo_despues", 0)))})
    return pd.DataFrame(filas, columns=["Fecha", "Tipo", "Concepto", "Monto", "Saldo"])


# TITULO RENDERIZAR PANEL BILLETERA

def renderizar_panel_billetera(main=None) -> None:
    """Dibuja la vista Billetera: aviso de saldo de prueba, saldo y plan actual, recarga, depósito y retiro (desactivados), compra de planes y movimientos.

    `main` no se usa (se conserva por compatibilidad con las demás vistas). No devuelve nada."""
    st.html(_estaticos.estilos(_CSS))
    usuario = st.session_state.get("usuario_informacion") or {}
    uid = usuario.get("id") if isinstance(usuario, dict) else None
    cfg = configuracion.BILLETERA
    actual = cuota_ia.plan_actual()
    saldo = billetera.saldo()
    recargado = billetera.recargado_en_el_mes()
    with st.container(key="billetera_contenedor"):
        st.html("<div class='bil-titulo'>Billetera</div><div class='bil-subtitulo'>Tu saldo dentro de la plataforma: paga planes y, más adelante, opera con cuentas reales.</div>"
                "<div class='bil-aviso'>Billetera de prueba: el saldo es virtual y no tiene valor monetario. No se pueden depositar ni retirar fondos reales todavía.</div>")
        aviso, error = st.session_state.pop(_CLAVE_AVISO, None), st.session_state.pop(_CLAVE_ERROR, None)
        if aviso:
            st.success(aviso)
        if error:
            st.error(error)
        recarga = st.session_state.pop(_CLAVE_RECARGA, None)
        if recarga:
            (st.success if recarga[0] == "ok" else st.error)(recarga[1])
        c1, c2, c3 = st.columns(3, gap="medium")
        c1.html(f"<div class='bil-tarjeta'><div class='bil-etiqueta'>Saldo disponible</div><div class='bil-saldo'>{escape(_usd(saldo))}</div>"
                f"<div class='bil-nota'>Billetera virtual · {escape(cfg['moneda'])}</div></div>")
        c2.html(f"<div class='bil-tarjeta'><div class='bil-etiqueta'>Plan actual</div><div class='bil-valor'>{escape(configuracion.PLANES_IA[actual]['nombre'])}</div>"
                f"<div class='bil-nota'>{escape(cuota_ia.formato(configuracion.PLANES_IA[actual]['tokens_mes']))} tokens de IA al mes</div></div>")
        c3.html(f"<div class='bil-tarjeta'><div class='bil-etiqueta'>Recargado este mes</div><div class='bil-valor'>{escape(_usd(recargado))}</div>"
                f"<div class='bil-nota'>Tope mensual: {escape(_usd(float(cfg['recarga_mensual_max'])))}</div></div>")

        st.html("<div class='bil-seccion'>Agregar o retirar fondos</div>")
        a, b, c = st.columns([3, 1.4, 1.4], gap="medium", vertical_alignment="bottom")
        with a:
            monto = st.segmented_control("Monto de la recarga de prueba", [float(x) for x in cfg["recargas"]], default=float(cfg["recargas"][0]),
                                         format_func=lambda x: f"{x:,.0f} USD".replace(",", "."), key="billetera_monto")
        b.button("Recargar saldo de prueba", key="billetera_recargar", type="primary", icon=":material/add_card:", width="stretch",
                 on_click=_recargar, args=(monto,), disabled=monto is None)
        c.button("Depositar / retirar", key="billetera_real", icon=":material/lock:", width="stretch", disabled=True,
                 help="Disponible cuando la plataforma habilite cuentas reales.")

        st.html("<div class='bil-seccion'>Pagar un plan con tu saldo</div>")
        columnas = st.columns(len(configuracion.PLANES_IA) - 1, gap="medium")
        for col, clave in zip(columnas, [p for p in configuracion.PLANES_IA if p != "gratis"]):
            precio = precio_de(clave, uid)
            variantes = max(len(p.get("precios", [0])) for p in configuracion.PLANES_IA.values())
            with col:
                col.html(f"<div class='bil-plan{' bil-plan-actual' if clave == actual else ''}'><div class='bil-plan-nombre'>{escape(configuracion.PLANES_IA[clave]['nombre'])}</div>"
                         f"<div class='bil-plan-precio'>{precio:,.0f} USD <span>al mes</span></div></div>")
                if clave == actual:
                    st.button("Tu plan actual", key=f"billetera_plan_{clave}", width="stretch", disabled=True)
                else:
                    st.button("Comprar" if saldo >= precio else "Saldo insuficiente", key=f"billetera_plan_{clave}", width="stretch",
                              type="primary" if saldo >= precio else "secondary", disabled=saldo < precio, on_click=comprar_con_billetera,
                              args=(clave, precio, demanda.variante_de(uid, variantes), uid, "billetera"))

        st.html("<div class='bil-seccion'>Movimientos</div>")
        movs = billetera.movimientos(100)
        if movs:
            st.dataframe(_tabla_movimientos(movs), hide_index=True, width="stretch", height=min(420, 38 + 35 * len(movs)))
        else:
            st.info("Todavía no hay movimientos.")



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
