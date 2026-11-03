# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara base .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Núcleo del motor: suscripciones, lectura de ticks y cuenta, bucle principal y lectura para los clientes.

Define `MotorPrecios` (compuesta con los mixins de stop dinámico y OCO). Hay UN motor por cuenta (usuario y modo
demo o real), creado por `registro.MOTORES`: cada uno tiene su hilo, su stream de precios, su foto de la cuenta y
sus vigilancias (stop dinámico y OCO), y trabaja siempre con la sesión de su usuario. Los hilos HTTP (SSE) solo leen
la última foto de SU motor y esperan novedades en una Condition.
"""
import threading
import time

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]
from herramientas import almacen_capital, almacen_oco, almacen_stop_dinamico
from herramientas.backends import sesiones_capital
from herramientas.puente_mt5 import PROVEEDOR, resolver_simbolo
from herramientas.tickets import ticket as _tk

from ..constantes import (CANDADO_MT5, INTERVALO_CUENTA, INTERVALO_EQUITY, INTERVALO_TICKS,
                          INACTIVIDAD_MOTOR, TTL_REFERENCIA, TTL_SUSCRIPCION)
from .oco import MixinOco
from .stop_dinamico import MixinStopDinamico

# Con Capital, los ticks llegan por WebSocket (push) en vez de sondear REST: el
# motor lee de la caché del stream (instantáneo). Con MT5 no se usa.
_ES_CAPITAL = PROVEEDOR == "capital"
if _ES_CAPITAL:
    from servidor_precios import streaming_capital as _ws


# TITULO MOTOR PRECIOS

class MotorPrecios(MixinStopDinamico, MixinOco):
    """Lee ticks de MT5 en un solo hilo y guarda la última foto de cada símbolo.
    Los clientes SSE esperan en una Condition y reciben SOLO lo que cambió.

    Hereda _paso_trailing/_paso_oco de los mixins. Los diccionarios de estado se describen
    en __init__; las escrituras se hacen bajo self._cond.
    """

    # TITULO INIT

    def __init__(self, clave: tuple = ("legado",), registro=None):
        """Crea el estado vacío del motor: condición de sincronización, cachés y configuración de trailing/OCO.

        `clave` es la cuenta que atiende este motor: (usuario_id, es_demo), o ("legado",) para la cuenta del .env, que
        nunca se apaga. `registro` es el RegistroMotores que lo creó (para retirarse cuando ya no hace falta)."""
        self._clave = clave
        self._registro = registro
        self._detenido = False
        self._ultimo_interes = time.time()   # último instante en que un cliente lo usó
        self._siempre_activo = clave == ("legado",)
        self._stream = _ws.stream_de(clave) if _ES_CAPITAL else None
        # Condition: protege el estado y despierta a los clientes SSE cuando hay cambios
        self._cond = threading.Condition()
        self._seq = 0                 # contador global de cambios
        self._ticks: dict = {}        # pedido -> {"b","a","l","t","ch","pct","seq"}
        self._cuenta: dict = {}       # {"equity","balance","profit","currency","seq"}
        self._subs: dict = {}         # pedido -> último instante en que un cliente lo pidió
        self._reales: dict = {}       # pedido -> nombre real en el terminal
        self._ref: dict = {}          # real -> (cierre_previo, instante)
        self._ultimo_msc: dict = {}   # real -> time_msc del último tick procesado
        self._trailing: dict = {}     # ticket(int) -> {"dist","paso"} (Stop dinámico)
        self._trailing_mtime = -1.0   # mtime de data/trailing.json ya cargado
        self._oco: dict = {}          # par_id -> {"a","b","symbol","ts"} (OCO)
        self._oco_mtime = -1.0        # mtime de data/oco.json ya cargado
        self._oco_armados: set = set()  # par_id cuyas DOS patas ya se vieron vivas (anti-carrera)

    # TITULO SUSCRIBIR

    # --- suscripciones -----------------------------------------------------
    def suscribir(self, simbolos):
        """Registra (o renueva) el interés de un cliente en los símbolos indicados, marcando la hora actual."""
        ahora = time.time()
        with self._cond:
            self._ultimo_interes = ahora
            for s in simbolos:
                self._subs[s] = ahora

    # TITULO ACTIVOS

    def _activos(self):
        """Devuelve los símbolos con suscripción vigente y elimina los que superaron TTL_SUSCRIPCION sin renovarse."""
        limite = time.time() - TTL_SUSCRIPCION
        with self._cond:
            for s in [s for s, t in self._subs.items() if t < limite]:
                self._subs.pop(s, None)
            return list(self._subs.keys())

    # TITULO REAL

    # --- lecturas de MT5 (solo desde el hilo del motor) -------------------
    def _real(self, pedido):
        """Traduce el símbolo pedido por el cliente al nombre real del terminal (con caché).

        La primera vez resuelve el nombre y lo activa en Market Watch con symbol_select.
        """
        real = self._reales.get(pedido)
        if real is None:
            with CANDADO_MT5:
                real = resolver_simbolo(pedido)
                mt5.symbol_select(real, True)
            self._reales[pedido] = real
        return real

    # TITULO CIERRE PREVIO

    def _cierre_previo(self, real):
        """Cierre de la vela diaria ANTERIOR: base de la variación del día.

        Usa caché por símbolo real durante TTL_REFERENCIA segundos. Si solo hay una vela
        diaria, usa su apertura. Devuelve None si MT5 no entrega datos.
        """
        referencia = self._ref.get(real)
        if referencia and time.time() - referencia[1] < TTL_REFERENCIA:
            return referencia[0]
        valor = None
        with CANDADO_MT5:
            rates = mt5.copy_rates_from_pos(real, mt5.TIMEFRAME_D1, 0, 2)
        if rates is not None and len(rates) >= 2:
            valor = float(rates[-2]["close"])
        elif rates is not None and len(rates) == 1:
            valor = float(rates[0]["open"])
        self._ref[real] = (valor, time.time())
        return valor

    # TITULO LEER TICKS

    def _leer_ticks(self):
        """Lee el último tick de cada símbolo activo y devuelve solo los que cambiaron.

        Devuelve {pedido: {b, a, l, t, ch, pct}}: bid, ask, último precio (last o bid),
        hora del tick, variación absoluta y porcentual frente al cierre previo. Omite símbolos
        sin precio o sin tick nuevo (mismo time_msc) y los que fallen. Solo se llama desde el hilo del motor.
        """
        cambios = {}
        activos = self._activos()
        # Con Capital: asegura que los epics activos estén suscritos al WebSocket.
        if _ES_CAPITAL and activos:
            self._stream.suscribir([self._real(p) for p in activos])
        # Recorre los símbolos con suscripción vigente
        for pedido in activos:
            try:
                real = self._real(pedido)
                if _ES_CAPITAL:
                    tick = self._stream.tick(real)      # lectura instantánea de la caché del stream
                else:
                    with CANDADO_MT5:
                        tick = mt5.symbol_info_tick(real)
                if tick is None or not (tick.bid or tick.ask):
                    continue
                if self._ultimo_msc.get(real) == tick.time_msc and pedido in self._ticks:
                    continue          # sin tick nuevo -> nada que enviar
                self._ultimo_msc[real] = tick.time_msc
                precio = tick.last if tick.last > 0 else tick.bid
                previo = self._cierre_previo(real)
                ch = (precio - previo) if previo else 0.0
                porcentaje = (ch / previo * 100) if previo else 0.0
                cambios[pedido] = {
                    "b": tick.bid, "a": tick.ask, "l": precio,
                    "t": int(tick.time), "ch": ch, "pct": porcentaje,
                }
            except Exception:
                continue
        return cambios

    # TITULO LEER CUENTA

    def _leer_cuenta(self):
        """Arma la foto de la cuenta: saldo, equity, margen, P/G, posiciones y órdenes pendientes.

        Devuelve un dict listo para enviar por SSE (claves equity, balance, profit, currency,
        margin..., uso_margen, pos, pc, pi y ord) o None si MT5 no entrega la cuenta.
        Marca con "tr" las posiciones con stop dinámico y con "oco" las órdenes en un par OCO.
        Efecto: lecturas de MT5 bajo candado y de los almacenes en disco.
        """
        with CANDADO_MT5:
            info = mt5.account_info()
            posiciones = mt5.positions_get() or []
            ordenes = mt5.orders_get() or []          # órdenes pendientes
        # Sin cuenta (terminal desconectado): no hay nada que publicar
        if info is None:
            return None
        # Resumen de posiciones abiertas
        # P/G neto por posición (profit + swap) → la suma coincide con info.profit
        posicion = {str(p.ticket): round(p.profit + p.swap, 2) for p in posiciones}
        pc = {str(p.ticket): p.price_current for p in posiciones}   # precio actual (Inicio)
        # detalle por posición para las líneas del gráfico: símbolo, tipo, lotes, apertura,
        # SL/TP, k = valor de 1 unidad de precio por lote (P/G proyectado) y sm = distancia
        # mínima de SL/TP al precio que exige el bróker
        pi = {}
        specs = {}
        def _spec(simbolo):
            """Devuelve (k, sm) del símbolo con caché local: k = valor monetario de 1 unidad de precio
            por lote (tick_value / tick_size) y sm = distancia mínima de stops en precio."""
            if simbolo not in specs:
                with CANDADO_MT5:
                    si = mt5.symbol_info(simbolo)
                marca_tiempo = float(getattr(si, "trade_tick_size", 0) or 0)
                specs[simbolo] = (
                    (float(si.trade_tick_value) / marca_tiempo) if si and marca_tiempo else 0.0,
                    float(getattr(si, "trade_stops_level", 0) or 0) * float(getattr(si, "point", 0) or 0),
                )
            return specs[simbolo]
        # Tickets con stop dinámico y detalle por posición
        tr = almacen_stop_dinamico.leer()      # tickets con stop dinámico activo (etiqueta "auto")
        for p in posiciones:
            k, sm = _spec(p.symbol)
            pi[str(p.ticket)] = {"s": p.symbol, "t": int(p.type), "v": p.volume, "po": p.price_open,
                                 "sl": p.sl, "tp": p.tp, "k": k, "sm": sm,
                                 "tr": 1 if _tk(p.ticket) in tr else 0}
        # Resumen de órdenes pendientes
        # órdenes pendientes (t: 2 Buy Limit, 3 Sell Limit, 4 Buy Stop, 5 Sell Stop)
        oco_tks = almacen_oco.tickets_en_oco()   # tickets vinculados en un par OCO (etiqueta "OCO")
        orden = {}
        for o in ordenes:
            if int(o.type) not in (2, 3, 4, 5):
                continue
            k, sm = _spec(o.symbol)
            orden[str(o.ticket)] = {"s": o.symbol, "t": int(o.type), "v": o.volume_current,
                                    "po": o.price_open, "sl": o.sl, "tp": o.tp, "k": k, "sm": sm,
                                    # caducidad: 0 GTC, 1 DAY, 2 fecha (ex, hora del servidor)
                                    "tt": int(o.type_time), "ex": int(o.time_expiration or 0),
                                    "oco": 1 if _tk(o.ticket) in oco_tks else 0}
        return {"equity": info.equity, "balance": info.balance,
                "profit": info.profit, "currency": info.currency,
                "margin": info.margin, "margin_free": info.margin_free,
                "margin_level": info.margin_level, "credit": info.credit,
                # % del equity usado como margen (barra "margen usado" de Inicio)
                "uso_margen": round(info.margin / info.equity * 100, 2) if info.equity else 0.0,
                "pos": posicion, "pc": pc, "pi": pi, "ord": orden}


    # TITULO PASO EQUITY LOG

    def _paso_equity_log(self):
        """Guarda un snapshot del equity/balance cada INTERVALO_EQUITY segundos.
        El almacen_capital aplica su propio mínimo entre escrituras, así que llamar
        cada ciclo es inofensivo. Alimenta el drawdown de EQUITY real (el que
        incluye el flotante de posiciones abiertas), que MT5 no guarda por sí solo.
        Ver herramientas/almacen_capital.py para la nota de escalado a multiusuario/Supabase."""
        c = self._cuenta
        equity = c.get("equity")
        if equity is None:
            return
        try:
            almacen_capital.registrar(equity, c.get("balance", equity), min_intervalo=INTERVALO_EQUITY)
        except Exception as e:
            print(f"[motor] no se pudo registrar equity: {e}")

    # TITULO CORRER

    # --- bucle principal ---------------------------------------------------
    def correr(self):
        """Bucle infinito del hilo del motor (se ejecuta en un hilo demonio).

        Cada INTERVALO_TICKS lee ticks y, cada INTERVALO_CUENTA, la cuenta; publica los
        cambios con un nuevo número de secuencia y despierta a los clientes. Luego ejecuta
        los pasos de stop dinámico, OCO y registro de equity. Ante un error lo imprime y
        espera 1 s.
        """
        # Todo lo que haga este hilo (lecturas, órdenes, archivos de datos) va con la sesión y las carpetas de SU cuenta
        with sesiones_capital.con_clave(self._clave):
            self._bucle()

    # TITULO DEBE SEGUIR

    def _debe_seguir(self) -> bool:
        """True si el motor sigue haciendo falta: tiene un cliente reciente o vigilancias (stop dinámico u OCO) activas.

        Los motores del .env (modo de un solo usuario) nunca se apagan."""
        if self._siempre_activo or self._trailing or self._oco:
            return True
        return time.time() - self._ultimo_interes < INACTIVIDAD_MOTOR

    # TITULO DETENER

    def detener(self):
        """Pide al hilo del motor que termine y despierta a los clientes que esperan (ya no habrá más novedades)."""
        with self._cond:
            self._detenido = True
            self._cond.notify_all()

    # TITULO BUCLE

    def _bucle(self):
        """Ciclo del motor: ticks, cuenta, stop dinámico, OCO y equity, hasta que se detenga o deje de hacer falta."""
        # Instante de la última lectura de cuenta (limita la frecuencia a INTERVALO_CUENTA)
        ultima_cuenta = 0.0
        # Ciclo del motor
        while not self._detenido:
            inicio = time.time()
            try:
                # 1) Ticks nuevos de los símbolos suscritos
                cambios = self._leer_ticks()
                cuenta = None
                if inicio - ultima_cuenta >= INTERVALO_CUENTA:
                    ultima_cuenta = inicio
                    cuenta = self._leer_cuenta()
                    if cuenta and all(self._cuenta.get(k) == v for k, v in cuenta.items()):
                        cuenta = None   # sin cambios
                # 2) Publica los cambios con una nueva secuencia y avisa a los clientes SSE
                if cambios or cuenta:
                    with self._cond:
                        self._seq += 1
                        for k, v in cambios.items():
                            v["seq"] = self._seq
                            self._ticks[k] = v
                        if cuenta:
                            cuenta["seq"] = self._seq
                            self._cuenta = cuenta
                        self._cond.notify_all()
                # 3) Tareas del cliente que no dependen de si hubo cambios
                self._paso_trailing()          # mueve los stops dinámicos activos
                self._paso_oco()               # cancela la pata sobrante de los OCO ejecutados
                self._paso_equity_log()        # snapshot de equity (drawdown real, Tanda 2)
                if not self._debe_seguir() and self._registro is not None and self._registro.retirar_si_ocioso(self):
                    return
            except Exception as e:
                print(f"[motor] error leyendo MT5: {e}")
                time.sleep(1)
            # Duerme lo que falte para completar el intervalo
            time.sleep(max(0.0, INTERVALO_TICKS - (time.time() - inicio)))

    # TITULO FOTO

    # --- lectura para los clientes ----------------------------------------
    def foto(self, simbolos, desde_seq=0):
        """Ticks (de esos símbolos) y cuenta que cambiaron después de `desde_seq`.

        Devuelve (secuencia_actual, ticks, cuenta); cuenta es None si no cambió. Quita la clave interna "seq".
        """
        with self._cond:
            ticks = {s: {k: v for k, v in self._ticks[s].items() if k != "seq"}
                     for s in simbolos
                     if s in self._ticks and self._ticks[s]["seq"] > desde_seq}
            cuenta = None
            if self._cuenta and self._cuenta.get("seq", 0) > desde_seq:
                cuenta = {k: v for k, v in self._cuenta.items() if k != "seq"}
            return self._seq, ticks, cuenta

    # TITULO ESPERAR

    def esperar(self, seq, tiempo_espera):
        """Bloquea hasta que la secuencia global supere `seq` o pase `timeout` segundos; devuelve la secuencia actual."""
        with self._cond:
            self._cond.wait_for(lambda: self._seq > seq, timeout=tiempo_espera)
            return self._seq




# -------------------------------------------------------------------------------------------------------
# --------------------------------------- FIN Piña y Jara base .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
