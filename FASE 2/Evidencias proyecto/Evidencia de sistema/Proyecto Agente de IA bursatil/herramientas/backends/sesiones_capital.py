# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara sesiones_capital .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""
sesiones_capital.py
-------------------
Registro de sesiones de Capital.com POR USUARIO Y MODO (demo o real).

`capital_nucleo.py` implementa una sola cuenta con estado de módulo (tokens, cachés, límite de peticiones).
En vez de reescribirlo, aquí se carga una COPIA independiente de ese módulo por cada (usuario, modo): cada copia
tiene sus propias credenciales, su propia sesión, sus cachés y su propio ritmo de peticiones, así que dos usuarios
nunca comparten cuenta, tokens ni lecturas. La fachada `capital.py` enruta cada llamada a la copia del usuario actual.

Cómo se decide el usuario actual (en este orden):
  0. Con `CAPITAL_MULTIUSUARIO` apagado nada de lo siguiente cuenta: siempre se usa la cuenta del .env.
  1. `como_usuario(usuario_id, es_demo)`: contexto explícito, para hilos y procesos de servidor.
  2. El resolvedor registrado con `fijar_resolvedor(fn)`: la aplicación lo usa para leer el usuario y el modo de la
     sesión de Streamlit (funciona también en los fragmentos, que no vuelven a ejecutar el script principal).
  3. Sin usuario: con `CAPITAL_MULTIUSUARIO` apagado usa la cuenta del .env (modo desarrollo de un solo usuario);
     con `CAPITAL_MULTIUSUARIO=true` usa una copia SIN credenciales, que responde "sin conexión". Así un hilo que
     perdió su contexto falla de forma visible en vez de operar con la cuenta de otro.

Las credenciales salen de `credenciales_bolsa` (cifradas en Supabase) y solo viven en memoria dentro de la copia;
nunca se escriben en logs. Se guardan como máximo `CAPITAL_MAX_SESIONES` copias; al pasar el tope se descarta la menos usada.
"""
import contextlib
import contextvars
import hashlib
import importlib.util
import os
import threading
import time
from collections import OrderedDict
from typing import Callable, Optional

from dotenv import load_dotenv

load_dotenv()

# Carpeta raíz del proyecto y ruta del núcleo que se copia por usuario
_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_RUTA_NUCLEO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capital_nucleo.py")
# Carpeta de los archivos de sesión compartidos entre procesos (uno por usuario y modo)
_CARPETA_SESIONES = os.path.join(_RAIZ, "data", "sesiones_capital")

# Direcciones de la API de Capital.com para cada modo
_URL_DEMO = "https://demo-api-capital.backend-capital.com/api/v1"
_URL_REAL = "https://api-capital.backend-capital.com/api/v1"

# Con True cada usuario usa sus propias credenciales; con False toda la plataforma usa la cuenta del .env
MULTIUSUARIO = os.getenv("CAPITAL_MULTIUSUARIO", "").strip().lower() in ("true", "1", "si", "sí")
# Máximo de copias de sesión en memoria
_MAX_SESIONES = max(2, int(os.getenv("CAPITAL_MAX_SESIONES", "200") or 200))
# Segundos que se recuerda que un usuario no tiene credenciales (para no consultar Supabase en cada llamada)
_VIDA_SIN_CREDENCIALES_S = 30.0

# Claves especiales del registro
_CLAVE_LEGADO = ("legado",)
_CLAVE_ANONIMO = ("anonimo",)

_CANDADO = threading.RLock()
# clave -> módulo copiado; el orden de la lista es el de uso reciente (el primero es el menos usado)
_copias: "OrderedDict[tuple, object]" = OrderedDict()
# clave -> epoch hasta el que se da por buena la ausencia de credenciales
_sin_credenciales: dict = {}
# Número de copia, para darle a cada módulo un nombre único
_contador = 0
# Límite de peticiones por segundo que se aplica a cada copia nueva (None = el del núcleo)
_limite_peticiones: Optional[int] = None

# Usuario explícito del hilo actual: (usuario_id, es_demo) o None
_usuario_explicito: contextvars.ContextVar = contextvars.ContextVar("usuario_capital", default=None)
# Función que devuelve (usuario_id, es_demo) del usuario de la sesión actual, o None si no hay
_resolvedor: Optional[Callable[[], Optional[tuple]]] = None


# TITULO FIJAR RESOLVEDOR

def fijar_resolvedor(funcion: Optional[Callable[[], Optional[tuple]]]) -> None:
    """Registra la función que dice quién es el usuario actual: debe devolver (usuario_id, es_demo) o None."""
    global _resolvedor
    _resolvedor = funcion


# TITULO COMO USUARIO

@contextlib.contextmanager
def como_usuario(usuario_id: int, es_demo: bool):
    """Bloque `with` que fija el usuario y el modo para todo lo que se ejecute dentro, en este hilo.

    Es lo que usan los procesos de servidor (motor de órdenes, streaming) que atienden a varios usuarios."""
    marca = _usuario_explicito.set((int(usuario_id), bool(es_demo)))
    try:
        yield
    finally:
        _usuario_explicito.reset(marca)


# TITULO CON CLAVE

@contextlib.contextmanager
def con_clave(clave: tuple):
    """Bloque `with` que fija una clave del registro cualquiera (usuario y modo, o una clave especial) en este hilo.

    Es lo que usa `herramientas/hilos.py` para que un hilo nuevo siga atendiendo al mismo usuario que lo lanzó."""
    marca = _usuario_explicito.set(tuple(clave))
    try:
        yield
    finally:
        _usuario_explicito.reset(marca)


# TITULO CLAVE ACTUAL

def clave_actual() -> tuple:
    """Devuelve la clave del registro del usuario actual: (usuario_id, es_demo), o una clave especial si no hay usuario."""
    if not MULTIUSUARIO:
        return _CLAVE_LEGADO       # modo de un solo usuario: siempre la cuenta del .env, sin importar quién entró
    explicito = _usuario_explicito.get()
    if explicito is not None:
        return explicito
    if _resolvedor is not None:
        try:
            resuelto = _resolvedor()
        except Exception:
            resuelto = None
        if resuelto:
            return (int(resuelto[0]), bool(resuelto[1]))
    return _CLAVE_ANONIMO


# TITULO RUTA DE SESION

def _ruta_sesion(clave: tuple) -> str:
    """Archivo donde la copia comparte su sesión con otros procesos; uno distinto por usuario y modo."""
    huella = hashlib.sha256(repr(clave).encode()).hexdigest()[:16]
    return os.path.join(_CARPETA_SESIONES, f"{huella}.json")


# TITULO FIJAR LIMITE DE PETICIONES

def fijar_limite_peticiones(por_segundo: int) -> None:
    """Cambia el máximo de peticiones por segundo de ESTE proceso para todas las copias, las actuales y las futuras.

    El servidor de datos lo baja a 4 para que, sumado al panel (6), no se supere el tope de 10 por segundo que
    Capital.com aplica a cada cuenta."""
    global _limite_peticiones
    _limite_peticiones = max(1, int(por_segundo))
    with _CANDADO:
        for modulo in _copias.values():
            modulo.fijar_limite_peticiones(_limite_peticiones)


# TITULO CARGAR COPIA

def _cargar_copia(clave: tuple, credenciales: Optional[dict]):
    """Carga una copia nueva e independiente de `capital_nucleo.py` y le pone las credenciales indicadas.

    `credenciales` es {identificador, api_key, api_contrasena, es_demo} o None para una copia SIN cuenta (responde
    "sin conexión"). La clave LEGADO conserva lo que el núcleo leyó del .env. Devuelve el módulo."""
    global _contador
    _contador += 1
    especificacion = importlib.util.spec_from_file_location(f"herramientas.backends.capital_nucleo_{_contador}", _RUTA_NUCLEO)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    if _limite_peticiones is not None:
        modulo.fijar_limite_peticiones(_limite_peticiones)
    if clave == _CLAVE_LEGADO:
        return modulo
    es_demo = bool(credenciales["es_demo"]) if credenciales else True
    modulo._API_KEY = (credenciales or {}).get("api_key", "")
    modulo._IDENTIFIER = (credenciales or {}).get("identificador", "")
    modulo._API_CONTRASENA = (credenciales or {}).get("api_contrasena", "")
    modulo._ES_DEMO = es_demo
    modulo.BASE = _URL_DEMO if es_demo else _URL_REAL
    modulo._ARCHIVO_SESION = _ruta_sesion(clave)
    modulo._ARCHIVO_CANDADO = modulo._ARCHIVO_SESION + ".lock"
    return modulo


# TITULO LEER CREDENCIALES

def _leer_credenciales(clave: tuple) -> Optional[dict]:
    """Lee y descifra las credenciales del usuario y modo de `clave`; None si no hay o no se pudieron leer.

    Nunca escribe secretos en logs: si falla, solo informa el tipo de error."""
    try:
        from herramientas import credenciales_bolsa
        return credenciales_bolsa.obtener_credenciales(clave[0], clave[1])
    except Exception as error:
        print(f"[CAPITAL] No se pudieron leer las credenciales del usuario {clave[0]} ({type(error).__name__}).")
        return None


# TITULO MODULO DE UNA CLAVE

def modulo_de(clave: tuple):
    """Devuelve la copia del núcleo que corresponde a la clave (usuario_id, es_demo), creándola si hace falta.

    Si el usuario no tiene credenciales guardadas para ese modo, devuelve la copia sin cuenta. Es seguro
    llamarla desde varios hilos a la vez. Quien guarde la copia (por ejemplo un stream) debe pedirla de nuevo si
    el usuario cambia sus credenciales."""
    with _CANDADO:
        modulo = _copias.get(clave)
        if modulo is not None:
            _copias.move_to_end(clave)
            return modulo
        if clave not in (_CLAVE_LEGADO, _CLAVE_ANONIMO) and time.time() < _sin_credenciales.get(clave, 0.0):
            return _modulo_sin_cuenta()
        credenciales = None
        if clave not in (_CLAVE_LEGADO, _CLAVE_ANONIMO):
            credenciales = _leer_credenciales(clave)
            if credenciales is None:
                _sin_credenciales[clave] = time.time() + _VIDA_SIN_CREDENCIALES_S
                return _modulo_sin_cuenta()
        modulo = _cargar_copia(clave, credenciales)
        _copias[clave] = modulo
        _descartar_sobrantes()
        return modulo


# TITULO MODULO ACTUAL

def modulo_actual():
    """Devuelve la copia del núcleo que corresponde al usuario actual (ver `clave_actual`)."""
    return modulo_de(clave_actual())


# TITULO MODULO SIN CUENTA

def _modulo_sin_cuenta():
    """Copia sin credenciales, compartida por todos los que no tienen cuenta conectada; responde "sin conexión".

    Se llama con el candado del registro tomado."""
    modulo = _copias.get(_CLAVE_ANONIMO)
    if modulo is None:
        modulo = _cargar_copia(_CLAVE_ANONIMO, None)
        _copias[_CLAVE_ANONIMO] = modulo
    return modulo


# TITULO DESCARTAR SOBRANTES

def _descartar_sobrantes() -> None:
    """Si hay más copias que el máximo permitido, descarta las menos usadas (nunca la del .env ni la sin cuenta)."""
    for clave in list(_copias):
        if len(_copias) <= _MAX_SESIONES:
            return
        if clave not in (_CLAVE_LEGADO, _CLAVE_ANONIMO):
            _copias.pop(clave, None)


# TITULO PROBAR CREDENCIALES

def probar_credenciales(identificador: str, api_key: str, api_contrasena: str, es_demo: bool) -> dict:
    """Comprueba contra Capital.com que las credenciales sirven, SIN guardarlas ni tocar ninguna sesión de usuario.

    Abre una sesión de prueba (POST /session) y la cierra enseguida. Devuelve {"ok": bool, "mensaje": str} con un
    texto apto para mostrar al usuario; nunca incluye ni registra los secretos."""
    import requests
    base = _URL_DEMO if es_demo else _URL_REAL
    try:
        respuesta = requests.post(
            f"{base}/session",
            headers={"X-CAP-API-KEY": api_key, "Content-Type": "application/json"},
            json={"identifier": identificador, "password": api_contrasena, "encryptedPassword": False},
            timeout=15,
        )
    except requests.exceptions.RequestException:
        return {"ok": False, "mensaje": "No se pudo contactar a Capital.com. Revisa tu conexión e inténtalo de nuevo."}
    if respuesta.status_code == 429:
        return {"ok": False, "mensaje": "Capital.com pidió esperar un poco entre intentos. Prueba otra vez en un minuto."}
    if respuesta.status_code != 200:
        modo = "demo" if es_demo else "real"
        return {"ok": False, "mensaje": f"Capital.com rechazó los datos para la cuenta {modo}. Revisa el correo, la API key "
                                        "y la contraseña de la key, y que la key pertenezca a ese tipo de cuenta."}
    try:
        requests.delete(f"{base}/session", headers={"CST": respuesta.headers.get("CST", ""),
                                                    "X-SECURITY-TOKEN": respuesta.headers.get("X-SECURITY-TOKEN", "")},
                        timeout=10)
    except requests.exceptions.RequestException:
        pass
    return {"ok": True, "mensaje": "Conexión verificada."}


# TITULO PROBAR AMBAS CUENTAS

def probar_ambas_cuentas(identificador: str, api_key: str, api_contrasena: str) -> dict:
    """Prueba los mismos datos contra la cuenta demo y contra la real de Capital.com.

    Devuelve {"demo": {"ok", "mensaje"}, "real": {"ok", "mensaje"}}. Capital permite una sesión nueva por segundo,
    así que entre una prueba y la otra hay una pausa. No guarda nada."""
    demo = probar_credenciales(identificador, api_key, api_contrasena, True)
    time.sleep(1.2)
    real = probar_credenciales(identificador, api_key, api_contrasena, False)
    return {"demo": demo, "real": real}


# TITULO OLVIDAR USUARIO

def olvidar_usuario(usuario_id: int) -> None:
    """Descarta las copias del usuario (demo y real), para que la próxima llamada relea sus credenciales.

    Se usa al guardar, cambiar o borrar las credenciales de un usuario o al cerrar su sesión."""
    with _CANDADO:
        for es_demo in (True, False):
            clave = (int(usuario_id), es_demo)
            _copias.pop(clave, None)
            _sin_credenciales.pop(clave, None)


# -------------------------------------------------------------------------------------------------------
# ----------------------------- FIN Piña y Jara sesiones_capital .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
