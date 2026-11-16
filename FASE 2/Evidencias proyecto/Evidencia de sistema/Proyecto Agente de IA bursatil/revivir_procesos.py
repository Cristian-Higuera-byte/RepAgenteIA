# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara revivir_procesos .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
revivir_procesos.py
-------------------
Vigila los dos procesos de la plataforma en el servidor (el servidor de precios y la aplicación Streamlit) y los vuelve a lanzar si se cayeron.

Para qué sirve: en un hosting compartido los procesos lanzados con nohup pueden terminar (límite de memoria, reinicio del servidor, un error).
Sin este vigilante, la web queda caída hasta que alguien entra a la Terminal. Se ejecuta con una tarea cron cada minuto.

Qué revisa de cada proceso:
  1. Que exista (busca en la lista de procesos del usuario).
  2. Que responda: el servidor de precios en /salud y Streamlit en /_stcore/health. Se prueba hasta 3 veces, con 10 segundos entre intentos.
Qué hace: si no existe, lo lanza; si existe pero no responde (o hay copias duplicadas), lo cierra y lo lanza de nuevo. Un proceso que lleva menos de
2 minutos en marcha se deja tranquilo, porque arrancar demora unos 30 a 40 segundos y no se debe reiniciar en bucle.
Si todo está bien no imprime nada, de modo que el registro del cron solo crece cuando pasa algo.

Uso (con el Python del entorno virtual de la aplicación, desde cualquier carpeta):
  python revivir_procesos.py                  revisa y repara
  python revivir_procesos.py --solo-revisar   informa qué haría, sin tocar nada (para probar antes de activar el cron)

Tarea cron sugerida (cada minuto), con rutas completas porque cron no carga el entorno:
  * * * * * /home/USUARIO/virtualenv/APLICACION/3.11/bin/python /home/USUARIO/public_html/CARPETA/revivir_procesos.py >> /home/USUARIO/revivir_procesos.log 2>&1
Solo usa la biblioteca estándar de Python; el puerto del servidor de precios se lee de servidor_precios/constantes.py (una sola fuente).
"""
import argparse
import getpass
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime
from typing import Callable, Optional

# Carpeta del proyecto (donde viven aplicacion.py y servidor_datos.py): la de este archivo.
RAIZ = os.path.dirname(os.path.abspath(__file__))

# Puerto interno de Streamlit; debe coincidir con el que usa el .htaccess del servidor.
PUERTO_APLICACION = 28501

# Puerto del servidor de precios si no se puede leer de servidor_precios/constantes.py.
PUERTO_PRECIOS_POR_DEFECTO = 8000

# Un proceso con menos segundos en marcha que esto no se revisa (todavía está arrancando).
SEGUNDOS_GRACIA = 120

# Cuántas veces se pregunta si responde y cuánto se espera entre intentos antes de darlo por caído.
INTENTOS_SALUD = 3
SEGUNDOS_ENTRE_INTENTOS = 10

# Segundos que se espera a que un proceso cierre por las buenas antes de forzarlo.
SEGUNDOS_ESPERA_CIERRE = 10


# TITULO REGISTRO

def anotar(mensaje: str) -> None:
    """Imprime una línea con la fecha y la hora; el cron la guarda en su registro."""
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {mensaje}", flush=True)


# TITULO PUERTO DEL SERVIDOR DE PRECIOS

def leer_puerto_precios(ruta: Optional[str] = None) -> int:
    """Lee el puerto del servidor de precios de servidor_precios/constantes.py (línea `PUERTO = n`); si no se puede, usa el de fábrica."""
    ruta = ruta or os.path.join(RAIZ, "servidor_precios", "constantes.py")
    try:
        with open(ruta, encoding="utf-8") as archivo:
            coincidencia = re.search(r"^PUERTO\s*=\s*(\d+)", archivo.read(), re.MULTILINE)
        return int(coincidencia.group(1)) if coincidencia else PUERTO_PRECIOS_POR_DEFECTO
    except OSError:
        return PUERTO_PRECIOS_POR_DEFECTO


# TITULO TIEMPO EN MARCHA

def segundos_de_etime(texto: str) -> int:
    """Convierte el tiempo en marcha que informa `ps` ([[dd-]hh:]mm:ss) en segundos."""
    dias = 0
    if "-" in texto:
        parte_dias, texto = texto.split("-", 1)
        dias = int(parte_dias)
    numeros = [int(parte) for parte in texto.split(":")]
    while len(numeros) < 3:
        numeros.insert(0, 0)
    horas, minutos, segundos = numeros
    return ((dias * 24 + horas) * 60 + minutos) * 60 + segundos


# TITULO LISTAR PROCESOS

def ejecutar_ps() -> str:
    """Devuelve la salida de `ps` con pid, tiempo en marcha y línea de comando de los procesos del usuario actual."""
    resultado = subprocess.run(["ps", "-u", getpass.getuser(), "-o", "pid=,etime=,args="], capture_output=True, text=True, timeout=20)
    return resultado.stdout


def buscar_procesos(salida_ps: str, marcas: list, pid_propio: Optional[int] = None) -> list:
    """Devuelve [(pid, segundos en marcha, línea de comando)] de los procesos cuya línea contiene TODAS las marcas; excluye el propio vigilante."""
    pid_propio = os.getpid() if pid_propio is None else pid_propio
    encontrados = []
    for linea in salida_ps.splitlines():
        partes = re.match(r"^\s*(\d+)\s+([\d:-]+)\s+(.*)$", linea)
        if not partes:
            continue
        pid, tiempo, comando = int(partes.group(1)), partes.group(2), partes.group(3)
        if pid != pid_propio and all(marca in comando for marca in marcas):
            encontrados.append((pid, segundos_de_etime(tiempo), comando))
    return encontrados


# TITULO COMPROBAR SALUD

def consultar(url: str, tiempo_maximo: int = 5) -> tuple:
    """Hace un GET y devuelve (código, cuerpo); (None, "") si no responde, se agota el tiempo o hay un error de conexión."""
    try:
        with urllib.request.urlopen(url, timeout=tiempo_maximo) as respuesta:
            return respuesta.status, respuesta.read(2000).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 - cualquier fallo significa «no responde»
        return None, ""


def responde_servidor_precios(puerto: int) -> bool:
    """True si el servidor de precios contesta {"ok": true} en /salud."""
    codigo, cuerpo = consultar(f"http://127.0.0.1:{puerto}/salud")
    try:
        return codigo == 200 and json.loads(cuerpo).get("ok") is True
    except ValueError:
        return False


def responde_aplicacion(puerto: int) -> bool:
    """True si Streamlit contesta «ok» en /_stcore/health."""
    codigo, cuerpo = consultar(f"http://127.0.0.1:{puerto}/_stcore/health")
    return codigo == 200 and cuerpo.strip().lower() == "ok"


def responde_con_reintentos(comprobar: Callable[[], bool], intentos: int = INTENTOS_SALUD, espera: float = SEGUNDOS_ENTRE_INTENTOS) -> bool:
    """Ejecuta la comprobación hasta `intentos` veces, esperando entre una y otra; True en cuanto una sale bien."""
    for numero in range(intentos):
        if comprobar():
            return True
        if numero < intentos - 1:
            time.sleep(espera)
    return False


# TITULO DECIDIR

def decidir(encontrados: list, responde: Callable[[], bool], gracia: int = SEGUNDOS_GRACIA) -> str:
    """Decide qué hacer con un proceso: "iniciar" (no existe), "reiniciar" (duplicado o no responde), "esperar" (arrancando) o "correcto"."""
    if not encontrados:
        return "iniciar"
    if len(encontrados) > 1:
        return "reiniciar"
    if min(segundos for _, segundos, _ in encontrados) < gracia:
        return "esperar"
    return "correcto" if responde() else "reiniciar"


# TITULO CERRAR E INICIAR

def cerrar_procesos(pids: list, espera: float = SEGUNDOS_ESPERA_CIERRE) -> None:
    """Pide a los procesos que terminen y, si siguen vivos pasada la espera, los fuerza."""
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            continue
    limite = time.time() + espera
    while time.time() < limite and any(_vivo(pid) for pid in pids):
        time.sleep(0.5)
    for pid in pids:
        if _vivo(pid):
            try:
                os.kill(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
            except OSError:
                pass


def _vivo(pid: int) -> bool:
    """True si el proceso sigue existiendo (y no es un zombi pendiente de recoger).

    En Windows (solo se usa para probar en un equipo de desarrollo) se consulta con `tasklist`, porque allí `os.kill(pid, 0)` termina el proceso
    en lugar de solo comprobar si existe.
    """
    if os.name != "posix":
        salida = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True).stdout or b""
        return str(pid).encode() in salida
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as archivo:
            return archivo.read().rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return True


def lanzar_proceso(comando: list, carpeta: str, archivo_registro: str) -> int:
    """Lanza el comando en segundo plano, desligado del cron (sigue vivo al terminar este script) y con su salida en el archivo de registro."""
    registro = open(archivo_registro, "ab")
    opciones = {"start_new_session": True} if os.name == "posix" else {}
    proceso = subprocess.Popen(comando, cwd=carpeta, stdin=subprocess.DEVNULL, stdout=registro, stderr=subprocess.STDOUT, **opciones)
    registro.close()
    return proceso.pid


# TITULO PROCESOS DE LA PLATAFORMA

def definir_procesos(puerto_precios: int) -> list:
    """Devuelve la descripción de los dos procesos: nombre, marcas para encontrarlos, comando, registro y comprobación de salud."""
    return [
        {"nombre": "servidor de precios", "marcas": ["servidor_datos.py"], "registro": "datos.log",
         "comando": [sys.executable, "servidor_datos.py"],
         "responde": lambda: responde_servidor_precios(puerto_precios)},
        {"nombre": "aplicación (Streamlit)", "marcas": ["streamlit", "aplicacion.py"], "registro": "app.log",
         "comando": [sys.executable, "-m", "streamlit", "run", "aplicacion.py", "--server.port", str(PUERTO_APLICACION), "--server.address", "127.0.0.1",
                     "--server.headless", "true", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false"],
         "responde": lambda: responde_aplicacion(PUERTO_APLICACION)},
    ]


# TITULO CANDADO

def tomar_candado():
    """Toma un candado para que dos revisiones no corran a la vez (con cron cada minuto podrían solaparse). Devuelve el archivo, None si ya hay otra en curso."""
    try:
        import fcntl
    except ImportError:  # sin fcntl (por ejemplo en Windows, solo para pruebas) no hay candado
        return open(os.devnull)
    archivo = open(os.path.join(tempfile.gettempdir(), f"pyj_revivir_{getpass.getuser()}.lock"), "w")
    try:
        fcntl.flock(archivo, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        archivo.close()
        return None
    return archivo


# TITULO PRINCIPAL

def revisar(solo_revisar: bool) -> int:
    """Revisa cada proceso y repara lo que haga falta; con `solo_revisar` solo informa. Devuelve 0 si todo quedó en orden o 1 si hubo un fallo."""
    candado = tomar_candado()
    if candado is None:
        return 0
    puerto_precios = leer_puerto_precios()
    resultado = 0
    for proceso in definir_procesos(puerto_precios):
        encontrados = buscar_procesos(ejecutar_ps(), proceso["marcas"])
        accion = decidir(encontrados, lambda: responde_con_reintentos(proceso["responde"]))
        if solo_revisar:
            anotar(f"[solo revisar] {proceso['nombre']}: {accion} ({len(encontrados)} proceso(s))")
            continue
        if accion in ("correcto", "esperar"):
            continue
        motivo = {"iniciar": "no estaba en marcha", "reiniciar": "no respondía o estaba duplicado"}[accion]
        anotar(f"{proceso['nombre']}: {motivo}; se vuelve a lanzar")
        try:
            if encontrados:
                cerrar_procesos([pid for pid, _, _ in encontrados])
            pid = lanzar_proceso(proceso["comando"], RAIZ, os.path.join(os.path.expanduser("~"), proceso["registro"]))
            anotar(f"{proceso['nombre']}: lanzado con el pid {pid}")
        except Exception as error:  # noqa: BLE001 - el vigilante no debe caerse por un fallo
            anotar(f"{proceso['nombre']}: NO se pudo lanzar: {error}")
            resultado = 1
    candado.close()
    return resultado


def principal() -> int:
    """Lee las opciones de la línea de comandos y ejecuta la revisión."""
    analizador = argparse.ArgumentParser(description="Revive el servidor de precios y la aplicación si se cayeron.")
    analizador.add_argument("--solo-revisar", action="store_true", help="informa qué haría, sin cerrar ni lanzar nada")
    return revisar(analizador.parse_args().solo_revisar)


if __name__ == "__main__":
    sys.exit(principal())


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara revivir_procesos .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
