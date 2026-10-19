# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara stop_dinamico .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Stop dinámico (trailing stop) del motor.

Mixin que añade a MotorPrecios el seguimiento del SL al precio. La configuración por ticket
viene de herramientas.almacen_stop_dinamico (data/trailing.json) y los cambios se aplican
en MT5 con modificar_sltp.
"""
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]
from tools import almacen_stop_dinamico
from tools.puente_mt5 import modificar_sltp

from ..constantes import CANDADO_MT5


class MixinStopDinamico:
    """Mixin de MotorPrecios con la lógica de stop dinámico.

    Usa el estado definido en MotorPrecios.__init__: _trailing (ticket -> config) y
    _trailing_mtime (fecha del archivo ya cargado).
    """

    # --- Stop dinámico (trailing stop) ------------------------------------
    # El SL sigue al precio a una distancia fija cuando la operación va a favor y
    # NUNCA retrocede. MT5 no tiene una orden trailing en el servidor del bróker:
    # la lógica corre aquí (cliente), por eso solo funciona con este proceso vivo.
    # La config la escribe el panel de Cartera en data/trailing.json (otro proceso).
    def _recargar_trailing(self):
        """Recarga la configuración de trailing desde disco solo si el archivo cambió.

        Efecto: actualiza _trailing y _trailing_mtime.
        """
        m = almacen_stop_dinamico.mtime()
        if m != self._trailing_mtime:
            self._trailing = almacen_stop_dinamico.leer()
            self._trailing_mtime = m

    def _paso_trailing(self):
        """Ejecuta un ciclo del stop dinámico (lo llama el bucle principal del motor).

        Para cada ticket configurado: elimina la config si la posición ya no existe; si no,
        calcula el nuevo SL a distancia `dist` del precio (Bid en compras, Ask en ventas),
        respeta la distancia mínima del bróker y solo lo mueve a favor y más allá del
        paso mínimo, sin retroceder nunca. Efectos: lecturas de MT5, modificar_sltp y
        escritura en el almacén al limpiar tickets cerrados.
        """
        self._recargar_trailing()
        if not self._trailing:
            return
        # Posiciones abiertas indexadas por ticket
        with CANDADO_MT5:
            posiciones = {p.ticket: p for p in (mt5.positions_get() or [])}
        # Copia de las claves porque el diccionario puede cambiar dentro del ciclo
        for ticket in list(self._trailing.keys()):
            cfg = self._trailing[ticket]
            p = posiciones.get(ticket)
            if p is None:                      # posición cerrada -> limpiar la config
                almacen_stop_dinamico.quitar(ticket)
                self._trailing.pop(ticket, None)
                self._trailing_mtime = almacen_stop_dinamico.mtime()
                continue
            # Distancia fija entre precio y SL; sin distancia válida no hay nada que hacer
            dist = float(cfg.get("dist", 0.0))
            if dist <= 0:
                continue
            # Especificaciones del símbolo y último tick
            with CANDADO_MT5:
                si = mt5.symbol_info(p.symbol)
                tick = mt5.symbol_info_tick(p.symbol)
            if si is None or tick is None or not (tick.bid or tick.ask):
                continue
            # Dígitos, tamaño de punto y distancia mínima de stops que exige el bróker
            dig = int(getattr(si, "digits", 5) or 5)
            point = float(getattr(si, "point", 0) or 0)
            sm = float(getattr(si, "trade_stops_level", 0) or 0) * point
            # Paso mínimo para volver a mover el SL (evita reescribirlo en cada
            # micro-tick). Por defecto 5 % de la distancia, con piso de unos points:
            # el SL sigue pegado al precio (gap entre dist y dist×1.05) sin saturar.
            paso = float(cfg.get("paso", 0.0)) or max(point * 3, dist * 0.05)
            # SL vigente (0 = sin SL)
            sl_actual = float(p.sl or 0.0)
            if int(p.type) == 0:               # COMPRA: SL por debajo, sigue al Bid
                precio = tick.bid
                nuevo = round(precio - dist, dig)
                if precio - nuevo < sm:        # respeta la distancia mínima del bróker
                    nuevo = round(precio - sm, dig)
                sube = nuevo > sl_actual + paso if sl_actual > 0 else True
                if sube and 0 < nuevo < precio and (sl_actual <= 0 or nuevo > sl_actual):
                    with CANDADO_MT5:
                        modificar_sltp(int(ticket), sl=nuevo)   # tp=None -> conserva el TP
            else:                              # VENTA: SL por encima, sigue al Ask
                precio = tick.ask
                nuevo = round(precio + dist, dig)
                if nuevo - precio < sm:
                    nuevo = round(precio + sm, dig)
                baja = nuevo < sl_actual - paso if sl_actual > 0 else True
                if baja and nuevo > precio and (sl_actual <= 0 or nuevo < sl_actual):
                    with CANDADO_MT5:
                        modificar_sltp(int(ticket), sl=nuevo)


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara stop_dinamico .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
