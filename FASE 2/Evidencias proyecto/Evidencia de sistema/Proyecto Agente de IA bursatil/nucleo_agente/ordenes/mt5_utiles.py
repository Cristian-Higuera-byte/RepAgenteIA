# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara mt5_utiles .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Utilidades de MetaTrader 5: símbolos, reloj del servidor, pérdida del día, riesgo expuesto y chequeos globales.

También reexporta MT5_LOCK, inicializar_mt5 y resolver_simbolo del puente común (herramientas/puente_mt5.py)
para que el resto del paquete y la vigilancia usen el mismo candado y la misma conexión que el resto de la app."""
import functools
import time
from datetime import datetime, timedelta
from typing import Any

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from nucleo_agente.ordenes.base_datos import _ahora, _consultar, interruptor_emergencia_activo
from nucleo_agente.ordenes.limites import LIMITES, limites_actuales
from herramientas.puente_mt5 import MT5_LOCK, NOMBRE_BROKER, PROVEEDOR, inicializar_mt5, resolver_simbolo

# Candado que serializa las decisiones de riesgo y los envíos de órdenes. Con MetaTrader 5 es MT5_LOCK; con Capital.com ese candado no
# bloquea (su API REST admite varias consultas a la vez), así que se usa el de órdenes del backend, que sí es real: dos
# confirmaciones simultáneas (el usuario y una vigilancia) no pueden pasar a la vez los límites de riesgo.
if PROVEEDOR == "capital":
    from herramientas.backends.capital import _ORDEN_CANDADO as _CANDADO_DECISIONES
else:
    _CANDADO_DECISIONES = MT5_LOCK


# TITULO NORMALIZAR

def _normalizar(simbolo: str) -> str:
    """Limpia un símbolo escrito por el usuario o el modelo: quita puntos suspensivos, espacios y pasa a mayúsculas."""
    return (simbolo or "").replace("...", "").replace("…", "").strip().upper()


# TITULO RESOLVER SIMBOLO

def _resolver_simbolo(simbolo: str) -> str:
    """Nombre del símbolo tal como lo llama el bróker (exacto -> núcleo -> alias). Si no se puede
    traducir, devuelve el nombre limpio y la validación posterior dirá que no existe."""
    limpio = (simbolo or "").replace("...", "").replace("…", "").strip()
    try:
        real = resolver_simbolo(limpio)
    except Exception:  # noqa: BLE001 - un fallo del resolvedor no debe impedir validar
        real = limpio
    return real or limpio


# TITULO SIMBOLOS PARA RELOJ

def _simbolos_para_reloj() -> list[str]:
    """Símbolos de los que leer un tick para conocer la hora del servidor: los de la Observación de
    mercado (visibles), o unos comunes si no hay ninguno."""
    try:
        visibles = [s.name for s in (mt5.symbols_get() or []) if getattr(s, "visible", False)]
    except Exception:  # noqa: BLE001
        visibles = []
    return visibles[:30] or ["EURUSD", "GOLD", "XAUUSD", "BTCUSD"]


# TITULO DESVIACION

def _desviacion(info: Any) -> int:
    """Deslizamiento máximo en PUNTOS: el mínimo configurado, o el doble del spread si es mayor.
    Un valor fijo no sirve para todos los activos (en cripto, índices o acciones 20 puntos son centavos)."""
    return max(LIMITES.desviacion_puntos, int(getattr(info, "spread", 0) or 0) * 2)


# TITULO CON CANDADO

def _con_candado(funcion):
    """Decorador que serializa las decisiones de riesgo y los envíos de órdenes (MT5_LOCK con MetaTrader 5; el candado de órdenes de Capital.com).

    La API de MetaTrader 5 no es segura entre hilos y servidor_datos.py / los fragmentos en
    vivo leen MT5 en paralelo. Como es un RLock, anidar llamadas con este decorador es seguro.
    """
    @functools.wraps(funcion)
    def envuelta(*args: Any, **kwargs: Any) -> Any:
        """Ejecuta la función original dentro del candado de decisiones y devuelve su resultado sin modificarlo."""
        with _CANDADO_DECISIONES:
            return funcion(*args, **kwargs)
    return envuelta


# TITULO PREPARAR MT5

def _preparar_mt5() -> str | None:
    """None si MT5 está listo; si no, el mensaje de error."""
    with MT5_LOCK:
        # inicializar_mt5 usa la ruta del terminal configurada (MT5_PATH) y no reintenta en bucle.
        if mt5.terminal_info() is None and not inicializar_mt5():
            return f"No se pudo conectar con {NOMBRE_BROKER}: {mt5.last_error()}"
    return None


# TITULO INICIO DIA SERVIDOR

def _inicio_dia_servidor() -> int | None:
    """Epoch (en hora del SERVIDOR del broker) de las 00:00 de hoy, o None si no se puede saber.

    MT5 guarda las horas de las operaciones en hora del servidor, que no es la hora local: usar la
    medianoche local desfasa el "día" varias horas. Se toma la hora del último tick como reloj del
    servidor; si es viejo (fin de semana, mercado cerrado) no sirve y se usa el método local.
    """
    for simbolo in _simbolos_para_reloj():
        tick = mt5.symbol_info_tick(simbolo)
        if tick is not None and tick.time and abs(time.time() - tick.time) < 86400:
            return int(tick.time - tick.time % 86400)
    return None


# TITULO PERDIDA DEL DIA

def _perdida_del_dia(cuenta: Any) -> float:
    """Pérdida del día (número positivo): operaciones cerradas hoy + resultado flotante."""
    ahora = datetime.now()
    # Se intenta alinear el "día" con la hora del servidor; si no se puede, se usa la medianoche local.
    inicio_servidor = _inicio_dia_servidor()
    if inicio_servidor is None:
        desde = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        desde = ahora - timedelta(days=3)  # ventana amplia; luego se filtra por la hora del servidor
    # Historial de operaciones desde el inicio de la ventana hasta mañana (para no perder las de hoy).
    deals = mt5.history_deals_get(desde, ahora + timedelta(days=1)) or []
    # Resultado realizado: solo compras/ventas (no depósitos), con comisión y swap, filtrando por hora del servidor.
    realizado = sum(
        d.profit + d.commission + d.swap
        for d in deals
        if d.type in (mt5.DEAL_TYPE_BUY, mt5.DEAL_TYPE_SELL)
        and (inicio_servidor is None or d.time >= inicio_servidor)
    )
    # Pérdida = lo realizado más lo flotante, en positivo; las ganancias dan 0.
    return max(0.0, -(realizado + cuenta.profit))


# TITULO RIESGO EXPUESTO

def _riesgo_expuesto(cuenta: Any, incluir_pendientes: bool) -> float:
    """Dinero que se perdería si saltaran TODOS los stop loss: posiciones abiertas (+ propuestas pendientes)."""
    total = 0.0
    # Por cada posición abierta: pérdida si el precio llega al stop loss.
    for p in mt5.positions_get() or []:
        if p.sl:
            resultado = mt5.order_calc_profit(p.type, p.symbol, p.volume, p.price_open, p.sl)
            total += max(0.0, -resultado) if resultado is not None else 0.0
        elif limites_actuales().riesgo_max_por_operacion_pct is not None:  # sin stop loss el riesgo es desconocido: se asume el máximo por operación que definió el usuario
            total += cuenta.equity * limites_actuales().riesgo_max_por_operacion_pct / 100
    # Opcionalmente suma el riesgo de propuestas de apertura aún vigentes que el usuario no ha resuelto.
    if incluir_pendientes:
        filas = _consultar(
            "SELECT COALESCE(SUM(riesgo_dinero), 0) AS total FROM ordenes "
            "WHERE estado = 'PENDIENTE' AND accion = 'abrir' AND expira > ?",
            (_ahora(),),
        )
        total += float(filas[0]["total"] or 0)
    return total


# TITULO EXPOSICION NOCIONAL

def _exposicion_nocional() -> float:
    """Valor total (en la moneda de la cuenta, aproximado) de las posiciones abiertas: volumen × precio actual × tamaño del contrato. Sirve para medir el apalancamiento.

    Una posición cuyos datos no se pueden leer no suma (se ignora, no se rechaza)."""
    total = 0.0
    for p in mt5.positions_get() or []:
        info = mt5.symbol_info(p.symbol)
        contrato = float(getattr(info, "trade_contract_size", 1.0) or 1.0) if info is not None else 1.0
        total += abs(float(p.volume) * float(getattr(p, "price_current", 0.0) or p.price_open) * contrato)
    return total


# TITULO MODO LLENADO

def _modo_llenado(info: Any) -> int:
    """Elige el modo de llenado de órdenes que admite el símbolo.

    Recibe symbol_info y mira los bits de `filling_mode`: 2 = IOC, 1 = FOK; si ninguno, devuelve RETURN."""
    modo = info.filling_mode
    # El bit 2 indica que el bróker acepta IOC (ejecutar lo posible y cancelar el resto).
    if modo & 2:
        return mt5.ORDER_FILLING_IOC
    # El bit 1 indica FOK (ejecutar todo o nada).
    if modo & 1:
        return mt5.ORDER_FILLING_FOK
    return mt5.ORDER_FILLING_RETURN


# TITULO CHEQUEOS GLOBALES

def _chequeos_globales(para_abrir: bool) -> tuple[Any, str | None]:
    """(cuenta, motivo_de_rechazo). Cerrar posiciones solo exige MT5 listo y cuenta demo."""
    # Paso 1: MT5 debe estar conectado.
    error = _preparar_mt5()
    if error:
        return None, error
    cuenta = mt5.account_info()
    if cuenta is None:
        return None, f"No se pudo leer la cuenta de {NOMBRE_BROKER}."
    # Paso 2: bloqueo si la cuenta no es demo.
    if LIMITES.solo_demo and cuenta.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        return cuenta, "BLOQUEADO: la cuenta conectada NO es demo y la Fase 1 solo opera en cuenta demo."
    # Paso 3: restricciones que solo aplican a abrir posiciones.
    if para_abrir:
        if interruptor_emergencia_activo():
            return cuenta, "Las nuevas aperturas están bloqueadas (interruptor de emergencia activado por el usuario)."
        # Pérdida diaria acumulada frente al tope que definió el usuario (si lo hay; % del balance).
        limites = limites_actuales()
        if limites.perdida_max_diaria_pct is not None:
            perdida = _perdida_del_dia(cuenta)
            tope = cuenta.balance * limites.perdida_max_diaria_pct / 100
            if perdida >= tope:
                return cuenta, (
                    f"Se alcanzó la pérdida máxima diaria que definiste ({perdida:.2f} de {tope:.2f} "
                    f"{cuenta.currency}). No se abren más operaciones hoy."
                )
        # Tope de posiciones simultáneas (solo si el usuario lo definió; por defecto no hay tope).
        abiertas = len(mt5.positions_get() or [])
        if limites.max_posiciones_abiertas is not None and abiertas >= limites.max_posiciones_abiertas:
            return cuenta, f"Ya hay {abiertas} posiciones abiertas (máximo que definiste: {limites.max_posiciones_abiertas})."
    return cuenta, None


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara mt5_utiles .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
