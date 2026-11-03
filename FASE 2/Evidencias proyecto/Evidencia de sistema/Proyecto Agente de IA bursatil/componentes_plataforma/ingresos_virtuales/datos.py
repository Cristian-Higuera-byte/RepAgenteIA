# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara datos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Datos del Laboratorio de ingresos: parámetros guardados por usuario, operaciones cerradas de la cuenta y cuáles abrió el agente.

Une tres fuentes: las operaciones cerradas de la cuenta activa (`estadisticas_diario.operaciones`), la lista de operaciones que el
agente de IA abrió (tabla `ordenes` de `data/ordenes.db`, columna `ticket_resultado`, el mismo criterio que usa la vigilancia para
reconocer sus posiciones) y los parámetros de cada modelo de cobro, que se guardan en la carpeta del usuario y la cuenta
(`herramientas/carpeta_usuario.py`) para que cada cuenta tenga los suyos. También lee el consumo de IA del agente
(`herramientas/consumo_ia.py`) para la pestaña de costos y planes.

No cobra ni mueve dinero. Todo lo que se lee es de solo lectura, salvo el archivo de parámetros.
"""
import json
import os
import tempfile
import time

import streamlit as st

from componentes_plataforma import _estaticos
from herramientas.carpeta_usuario import carpeta_usuario, ruta_archivo

# Parámetros por defecto, leídos de parametros.json (junto a este archivo)
PARAMETROS_BASE = _estaticos.datos_json(os.path.join(os.path.dirname(os.path.abspath(__file__)), "parametros.json"))
# Nombre del archivo de parámetros de cada cuenta
_ARCHIVO = "ingresos_virtuales.json"
# Segundos que se reutilizan las operaciones ya leídas en la sesión (leerlas consulta a Capital.com)
_VIDA_OPERACIONES_S = 60
# Clave de session_state donde se guardan las operaciones leídas
_CLAVE_OPERACIONES = "ingresos_virtuales_operaciones"


# TITULO ACOTAR

def _acotar(valor, minimo: float, maximo: float, por_defecto: float) -> float:
    """Convierte `valor` a número dentro de [minimo, maximo]; si no es un número válido (o es una celda vacía) devuelve `por_defecto`."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return por_defecto
    if numero != numero:        # NaN (una celda vacía de las tablas editables): se toma el valor por defecto
        return por_defecto
    return max(minimo, min(maximo, numero))


# TITULO NORMALIZAR PRECIOS IA

def _normalizar_precios_ia(crudos, base: dict) -> dict:
    """Valida la tabla de precios de IA ({modelo: {entrada_acierto, entrada_fallo, salida}}, en dólares por millón de tokens).

    Se queda con los modelos de nombre válido (hasta 12) y deja cada precio entre 0 y 1.000; si la tabla viene vacía o dañada usa la base."""
    if not isinstance(crudos, dict):
        return {k: dict(v) for k, v in base.items()}
    salida = {}
    for nombre, p in list(crudos.items())[:12]:
        if isinstance(nombre, str) and nombre.strip() and isinstance(p, dict):
            salida[nombre.strip()[:60]] = {c: _acotar(p.get(c), 0, 1000, 0.0) for c in ("entrada_acierto", "entrada_fallo", "salida")}
    return salida or {k: dict(v) for k, v in base.items()}


# TITULO NORMALIZAR PLANES

def _normalizar_planes(crudos, base: list) -> list:
    """Valida la lista de planes ({nombre, precio, tope_ia}): hasta 6, con nombre de 1 a 30 letras y montos entre 0 y 10.000 dólares.

    Si la lista viene vacía o dañada usa la base."""
    if not isinstance(crudos, list):
        return [dict(p) for p in base]
    salida = []
    for p in crudos[:6]:
        if isinstance(p, dict) and isinstance(p.get("nombre"), str) and p["nombre"].strip():
            salida.append({"nombre": p["nombre"].strip()[:30], "precio": _acotar(p.get("precio"), 0, 10000, 0.0),
                           "tope_ia": _acotar(p.get("tope_ia"), 0, 10000, 0.0)})
    return salida or [dict(p) for p in base]


# TITULO NORMALIZAR PARAMETROS

def normalizar_parametros(crudos: dict) -> dict:
    """Completa con los valores por defecto lo que falte y deja cada parámetro dentro de un rango razonable.

    Evita que un archivo editado a mano o un valor absurdo (porcentajes negativos, cuotas enormes) rompa los cálculos."""
    b = PARAMETROS_BASE
    crudos = crudos if isinstance(crudos, dict) else {}
    umbrales = crudos.get("umbrales") if isinstance(crudos.get("umbrales"), dict) else {}
    activos = crudos.get("activos", b["activos"])
    return {
        "activos": [k for k in (activos if isinstance(activos, list) else b["activos"]) if k in b["activos"]],
        "dias": int(_acotar(crudos.get("dias", b["dias"]), 7, 365, b["dias"])),
        "suscripcion_mensual": _acotar(crudos.get("suscripcion_mensual", b["suscripcion_mensual"]), 0, 10000, b["suscripcion_mensual"]),
        "recargo_fijo": _acotar(crudos.get("recargo_fijo", b["recargo_fijo"]), 0, 1000, b["recargo_fijo"]),
        "recargo_por_lote": _acotar(crudos.get("recargo_por_lote", b["recargo_por_lote"]), 0, 1000, b["recargo_por_lote"]),
        "spread_usd_por_lote": _acotar(crudos.get("spread_usd_por_lote", b["spread_usd_por_lote"]), 0, 1000, b["spread_usd_por_lote"]),
        "referido_participacion": _acotar(crudos.get("referido_participacion", b["referido_participacion"]), 0, 1, b["referido_participacion"]),
        "performance_tasa": _acotar(crudos.get("performance_tasa", b["performance_tasa"]), 0, 1, b["performance_tasa"]),
        "patrimonio_tasa_anual": _acotar(crudos.get("patrimonio_tasa_anual", b["patrimonio_tasa_anual"]), 0, 0.5, b["patrimonio_tasa_anual"]),
        "umbrales": {k: _acotar(umbrales.get(k, v), 0, 1_000_000, v) for k, v in b["umbrales"].items()},
        "costo_fijo_usuario": _acotar(crudos.get("costo_fijo_usuario", b["costo_fijo_usuario"]), 0, 10000, b["costo_fijo_usuario"]),
        "conversion_interes_a_pago": _acotar(crudos.get("conversion_interes_a_pago", b["conversion_interes_a_pago"]), 0, 1, b["conversion_interes_a_pago"]),
        "precios_ia": _normalizar_precios_ia(crudos.get("precios_ia"), b["precios_ia"]),
        "planes": _normalizar_planes(crudos.get("planes"), b["planes"]),
    }


# TITULO LEER PARAMETROS

def leer_parametros() -> dict:
    """Parámetros de la cuenta actual: los guardados (si existen y son válidos) sobre los valores por defecto."""
    try:
        with open(ruta_archivo(_ARCHIVO), "r", encoding="utf-8") as f:
            return normalizar_parametros(json.load(f))
    except (OSError, ValueError):
        return normalizar_parametros({})


# TITULO GUARDAR PARAMETROS

def guardar_parametros(p: dict) -> dict:
    """Guarda los parámetros de la cuenta actual (escritura atómica) y devuelve los que quedaron guardados, ya normalizados."""
    limpio = normalizar_parametros(p)
    os.makedirs(carpeta_usuario(), exist_ok=True)
    temporal = tempfile.NamedTemporaryFile("w", delete=False, dir=carpeta_usuario(), encoding="utf-8")
    try:
        json.dump(limpio, temporal, ensure_ascii=False, indent=2)
        temporal.flush()
        os.fsync(temporal.fileno())
    finally:
        temporal.close()
    os.replace(temporal.name, ruta_archivo(_ARCHIVO))
    return limpio


# TITULO TICKETS DEL AGENTE

def tickets_del_agente() -> dict:
    """Devuelve {ticket: origen} de las posiciones que el agente abrió y se ejecutaron.

    El origen es "agente" (propuesta que el usuario confirmó) o "automatica" (vigilancia autorizada). Lee `data/ordenes.db` sin
    modificarla; si la base no existe o falla, devuelve un diccionario vacío (todas las operaciones se tratan como manuales)."""
    try:
        from nucleo_agente.ordenes.base_datos import _consultar
        filas = _consultar("SELECT ticket_resultado, origen FROM ordenes WHERE accion = 'abrir' AND estado = 'EJECUTADA' "
                           "AND ticket_resultado IS NOT NULL AND ticket_resultado != ''")
    except Exception:  # noqa: BLE001 - sin base de órdenes no hay operaciones del agente que reconocer
        return {}
    return {str(f["ticket_resultado"]): (f["origen"] or "agente") for f in filas}


# TITULO RESUMEN PROPUESTAS

def resumen_propuestas() -> dict:
    """Cuenta las propuestas del agente por estado (EJECUTADA, RECHAZADA_USUARIO, RECHAZADA_RIESGO, EXPIRADA, ERROR, PENDIENTE…).

    Devuelve {estado: cantidad}; vacío si no hay base de órdenes. Sirve para ver cuántas propuestas acepta el usuario."""
    try:
        from nucleo_agente.ordenes.base_datos import _consultar
        filas = _consultar("SELECT estado, COUNT(*) AS n FROM ordenes WHERE accion = 'abrir' GROUP BY estado")
    except Exception:  # noqa: BLE001
        return {}
    return {f["estado"]: int(f["n"]) for f in filas}


# TITULO CARGAR OPERACIONES

def cargar_operaciones(dias: int, forzar: bool = False) -> list:
    """Operaciones cerradas de la cuenta activa en los últimos `dias` días (hasta 500), con caché de 60 s en la sesión.

    La caché vive en `st.session_state` (no en memoria del proceso) para que nunca se mezclen las operaciones de dos usuarios.
    `forzar` ignora la caché. Devuelve lista vacía si Capital.com no responde."""
    guardado = st.session_state.get(_CLAVE_OPERACIONES)
    if guardado and not forzar and guardado[1] == dias and time.time() - guardado[0] < _VIDA_OPERACIONES_S:
        return guardado[2]
    try:
        from herramientas import estadisticas_diario
        ops = estadisticas_diario.operaciones(dias, 500)
    except Exception:  # noqa: BLE001 - sin conexión se muestra el aviso de "sin operaciones"
        ops = []
    st.session_state[_CLAVE_OPERACIONES] = (time.time(), dias, ops)
    return ops


# TITULO CAPITAL REFERENCIA

def capital_de_referencia() -> tuple:
    """Devuelve (capital, es_demo): el saldo en efectivo de la cuenta activa (10.000 si no se puede leer) y si la cuenta es demo.

    Es la base sobre la que se calcula el retorno y la comisión sobre patrimonio."""
    try:
        from herramientas.puente_mt5 import obtener_info_cuenta
        info = obtener_info_cuenta()
        capital = float(info.get("balance") or info.get("equity") or 0.0)
        return (capital if capital > 0 else 10000.0), str(info.get("tipo", "Demo")).lower() != "real"
    except Exception:  # noqa: BLE001
        return 10000.0, True


# TITULO DIVIDIR POR ORIGEN

def dividir_por_origen(ops: list, tickets: dict) -> dict:
    """Separa las operaciones en {"agente": [...], "automatica": [...], "manual": [...]} según quién las abrió.

    Una operación es del agente si su identificador (`pos_id`) está entre los tickets que el agente abrió."""
    grupos = {"agente": [], "automatica": [], "manual": []}
    for o in ops:
        origen = tickets.get(str(o.get("pos_id", "")))
        grupos["manual" if origen is None else ("automatica" if origen == "automatica" else "agente")].append(o)
    return grupos


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara datos .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
