# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara idempotencia .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Idempotencia de las órdenes del servidor de datos (hallazgo V05 de la auditoría).

Cada petición de trading puede llevar un identificador de solicitud (`id_solicitud`). Si llega dos veces (doble clic, reintento del navegador o
del proxy tras perder la respuesta), el bróker se llama UNA sola vez: la repetición recibe el resultado guardado, o un aviso si la primera
sigue en curso o terminó con un resultado incierto (tiempo agotado o caída). Una solicitud de resultado incierto NO se reenvía sola: la
persona debe comprobar su cuenta, porque reenviar podría duplicar la operación.

Las claves se separan por usuario y cuenta (actor) y por ruta, y se olvidan pasado `VIDA_S`. Sin identificador la petición se atiende como antes."""
import re
import threading
import time

VIDA_S = 900            # cuánto tiempo se recuerda una solicitud (15 min)
MAX_CLAVES = 5000       # tope de solicitudes recordadas
PATRON = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class Idempotencia:
    """Registro en memoria de solicitudes vistas: reservar antes de llamar al bróker y guardar el resultado al terminar."""

    def __init__(self, vida_s: float = VIDA_S, maximo: int = MAX_CLAVES):
        self._vida = vida_s
        self._maximo = maximo
        self._candado = threading.Lock()
        self._datos: dict[tuple, dict] = {}

    def _limpiar(self, ahora: float) -> None:
        vencidas = [k for k, v in self._datos.items() if ahora - v["t"] > self._vida]
        for k in vencidas:
            del self._datos[k]
        if len(self._datos) > self._maximo:
            for k in sorted(self._datos, key=lambda x: self._datos[x]["t"])[: len(self._datos) - self._maximo]:
                del self._datos[k]

    def reservar(self, actor: str, ruta: str, clave: str):
        """Devuelve ("nueva", None) si se debe ejecutar, ("repetida", resultado) si ya terminó, o ("en_curso", None) si sigue en curso o quedó incierta."""
        ahora = time.time()
        llave = (actor, ruta, clave)
        with self._candado:
            self._limpiar(ahora)
            previa = self._datos.get(llave)
            if previa is None:
                self._datos[llave] = {"estado": "en_curso", "resultado": None, "t": ahora}
                return "nueva", None
            if previa["estado"] == "listo":
                return "repetida", previa["resultado"]
            return "en_curso", None

    def guardar(self, actor: str, ruta: str, clave: str, resultado) -> None:
        """Anota el resultado de una solicitud terminada, para devolverlo si se repite."""
        with self._candado:
            self._datos[(actor, ruta, clave)] = {"estado": "listo", "resultado": resultado, "t": time.time()}


IDEMPOTENCIA = Idempotencia()


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara idempotencia .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
