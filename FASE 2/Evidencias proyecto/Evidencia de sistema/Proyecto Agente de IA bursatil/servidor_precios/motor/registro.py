# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------------- INICIO Piña y Jara registro .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""Registro de motores de precios: uno por cuenta (usuario y modo demo o real).

`MOTORES.de(clave)` entrega el motor de una cuenta, creándolo y arrancando su hilo la primera vez. Un motor se
apaga solo cuando pasan `INACTIVIDAD_MOTOR` segundos sin clientes y sin vigilancias activas (stop dinámico u OCO);
las vigilancias deben seguir funcionando con el navegador cerrado, por eso `descubrir()` vuelve a encender el motor
de cualquier cuenta que tenga una configurada (lo llama un hilo del servidor cada pocos segundos).
"""
import threading
import time

from herramientas.carpeta_usuario import cuentas_con_contenido
from herramientas.hilos import lanzar_hilo

from .base import MotorPrecios


# TITULO REGISTRO MOTORES

class RegistroMotores:
    """Guarda los motores vivos, uno por cuenta, y decide cuándo crearlos y cuándo retirarlos."""

    # TITULO INIT

    def __init__(self):
        """Crea el registro vacío con su candado."""
        self._candado = threading.Lock()
        self._motores: dict = {}

    # TITULO DE

    def de(self, clave: tuple) -> MotorPrecios:
        """Devuelve el motor vivo de la cuenta `clave`, creándolo (con su hilo) si no existe o ya se detuvo.

        Marca el motor como usado ahora mismo, así una petición que llega justo cuando iba a apagarse lo mantiene vivo."""
        with self._candado:
            motor = self._motores.get(clave)
            if motor is None or motor._detenido:
                motor = MotorPrecios(clave, registro=self)
                self._motores[clave] = motor
                lanzar_hilo(motor.correr, nombre=f"motor-precios-{'-'.join(map(str, clave))}")
            motor._ultimo_interes = time.time()
            return motor

    # TITULO RETIRAR SI OCIOSO

    def retirar_si_ocioso(self, motor: MotorPrecios) -> bool:
        """Retira el motor del registro y lo detiene si sigue sin hacer falta; devuelve True si lo retiró.

        Vuelve a comprobarlo bajo el candado del registro, para no apagar un motor que un cliente acaba de pedir."""
        with self._candado:
            if motor._debe_seguir() or self._motores.get(motor._clave) is not motor:
                return False
            self._motores.pop(motor._clave, None)
        motor.detener()
        try:
            from servidor_precios import streaming_capital
            streaming_capital.detener_stream(motor._clave)
        except Exception:
            pass
        return True

    # TITULO CLAVES

    def claves(self) -> list:
        """Lista las cuentas que tienen un motor vivo ahora mismo."""
        with self._candado:
            return list(self._motores)

    # TITULO DESCUBRIR

    def descubrir(self) -> list:
        """Enciende el motor de toda cuenta con stop dinámico u OCO configurado y devuelve esas cuentas.

        Mira las carpetas de datos por usuario (`data/usuarios/<id>/<modo>/`): así las vigilancias siguen activas
        aunque el usuario haya cerrado el navegador o el servidor se haya reiniciado."""
        cuentas = set(cuentas_con_contenido("trailing.json")) | set(cuentas_con_contenido("oco.json"))
        for clave in cuentas:
            self.de(clave)
        return sorted(cuentas)


# Registro único del servidor (lo usan ejecucion.py y manejador.py)
MOTORES = RegistroMotores()


# -------------------------------------------------------------------------------------------------------
# ----------------------------------------- FIN Piña y Jara registro .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
