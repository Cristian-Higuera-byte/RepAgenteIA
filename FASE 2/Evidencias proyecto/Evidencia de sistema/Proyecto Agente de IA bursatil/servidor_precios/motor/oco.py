# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- INICIO Piña y Jara oco .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""OCO (One-Cancels-the-Other) del motor.

Mixin que añade a MotorPrecios la vigilancia de pares de órdenes pendientes vinculadas.
Lee la configuración de herramientas.almacen_oco (data/oco.json) y cancela en MT5 la
pata sobrante cuando la otra se ejecuta.
"""
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]
from herramientas import almacen_oco
from herramientas.tickets import ticket as _tk
from herramientas.puente_mt5 import eliminar_orden

from ..constantes import CANDADO_MT5


# TITULO MIXIN OCO

class MixinOco:
    """Mixin de MotorPrecios con la lógica OCO.

    Usa los atributos de estado que define MotorPrecios.__init__: _oco (pares vigentes),
    _oco_mtime (fecha del archivo ya cargado) y _oco_armados (pares con ambas patas vistas).
    """

    # TITULO RECARGAR OCO

    # --- OCO (One-Cancels-the-Other) --------------------------------------
    # Dos órdenes pendientes vinculadas: cuando UNA se ejecuta (pasa a posición),
    # se cancela la otra. MT5 no tiene OCO nativo: la lógica vive aquí (cliente),
    # por eso solo funciona con este proceso vivo. La config la escribe el ticket
    # de órdenes en data/oco.json (otro proceso).
    def _recargar_oco(self):
        """Recarga los pares OCO desde disco solo si el archivo cambió (compara mtime).

        Efecto: actualiza _oco y _oco_mtime y descarta de _oco_armados los pares que ya no existen.
        """
        # Compara la fecha de modificación para evitar leer el JSON en cada ciclo
        m = almacen_oco.mtime()
        if m != self._oco_mtime:
            # Archivo nuevo o modificado: vuelve a leerlo
            self._oco = almacen_oco.leer()
            self._oco_mtime = m
            # olvida pares "armados" que ya no existen
            self._oco_armados &= set(self._oco.keys())

    # TITULO PASO OCO

    def _paso_oco(self):
        """Ejecuta un ciclo de vigilancia OCO (lo llama el bucle principal del motor).

        Consulta órdenes y posiciones en MT5 y, por cada par: lo marca como armado cuando
        ambas patas están vivas; si una sale del libro porque se ejecutó (es posición),
        elimina la otra pata; si fue cancelada a mano, solo rompe el vínculo.
        Efectos: llamadas a MT5 (orders_get, positions_get, eliminar_orden) y escritura
        en el almacén OCO al cerrar pares.
        """
        # Sincroniza la configuración antes de evaluar
        self._recargar_oco()
        if not self._oco:
            return
        # Foto del estado de MT5 bajo candado
        with CANDADO_MT5:
            ordenes = mt5.orders_get() or []
            posiciones = mt5.positions_get() or []
        # tickets de órdenes pendientes vivas ahora mismo
        vivos = {_tk(o.ticket) for o in ordenes if int(o.type) in (2, 3, 4, 5)}
        # tickets que ya son posición (una pendiente al ejecutarse conserva su ticket
        # como identifier de la posición): sirve para distinguir "ejecutada" de "cancelada"
        en_posicion = set()
        for p in posiciones:
            en_posicion.add(_tk(p.ticket))
            en_posicion.add(_tk(getattr(p, "identifier", p.ticket)))
        # Evalúa cada par (copia de las claves: _cerrar_oco modifica el dict)
        for par_id in list(self._oco.keys()):
            configuracion = self._oco[par_id]
            a, b = _tk(configuracion["a"]), _tk(configuracion["b"])
            a_vivo, b_vivo = a in vivos, b in vivos
            if a_vivo and b_vivo:
                self._oco_armados.add(par_id)        # ambas patas confirmadas
                continue
            if not (a_vivo or b_vivo):               # ninguna sigue pendiente: nada que hacer
                self._cerrar_oco(par_id)
                continue
            if par_id not in self._oco_armados:
                # Aún no se vieron las DOS vivas: puede ser la ventana entre colocar la
                # 1.ª y la 2.ª pata. Se espera a confirmarlas antes de actuar (anti-carrera).
                continue
            # Exactamente una pata sigue viva y el par estaba armado -> la otra salió del libro
            vivo = a if a_vivo else b
            ido = b if a_vivo else a
            if ido in en_posicion:                   # la otra SE EJECUTÓ -> cancela la sobrante (OCO)
                with CANDADO_MT5:
                    eliminar_orden(vivo)
            # si no está en posición, fue cancelada a mano: solo se rompe el vínculo
            self._cerrar_oco(par_id)

    # TITULO CERRAR OCO

    def _cerrar_oco(self, par_id):
        """Da por terminado un par OCO: lo quita del almacén en disco y del estado en memoria.

        Recibe el identificador del par. Actualiza _oco_mtime para no recargar el archivo que
        acaba de modificar este mismo proceso.
        """
        almacen_oco.quitar_par(par_id)
        self._oco.pop(par_id, None)
        self._oco_mtime = almacen_oco.mtime()
        self._oco_armados.discard(par_id)


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- FIN Piña y Jara oco .PY ---------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
