# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------- INICIO Piña y Jara _prueba_revivir_procesos .PY ---------------------------
# -------------------------------------------------------------------------------------------------------

"""
_prueba_revivir_procesos.py
---------------------------
Pruebas de `revivir_procesos.py` que no necesitan el servidor ni una base de datos.

Parte 1: lectura del tiempo en marcha y de la lista de procesos (con una salida de `ps` de ejemplo, con el formato del servidor).
Parte 2: la decisión de qué hacer con cada proceso (iniciar, reiniciar, esperar o dejarlo).
Parte 3: las comprobaciones de salud contra un servidor HTTP local de mentira, y los reintentos.
Parte 4: lanzar y cerrar un proceso de verdad (un proceso que solo duerme) y comprobar que su salida llega al archivo de registro.
Parte 5: el flujo completo `revisar` con las piezas que tocan el sistema reemplazadas por simuladores.

Uso (desde la carpeta del proyecto):  env\\Scripts\\python _prueba_revivir_procesos.py
"""
import http.server
import json
import os
import sys
import tempfile
import threading
import time

import revivir_procesos as rp

fallos: list = []
hechas = 0

# Salida de `ps -u usuario -o pid=,etime=,args=` con el formato del servidor (dos procesos de la plataforma, otro ajeno y el propio vigilante).
PS_EJEMPLO = """\
 1120859       01:13 /home/u/virtualenv/app/3.11/bin/python3.11_bin servidor_datos.py
 1121082    03:05:44 /home/u/virtualenv/app/3.11/bin/python3.11_bin /home/u/virtualenv/app/3.11/bin/streamlit run aplicacion.py --server.port 28501 --server.address 127.0.0.1
  500 1-02:03:04 /usr/bin/otra_cosa --opcion
  600       00:09 python revivir_procesos.py
linea que no es de ps
"""


# TITULO COMPROBAR

def comprobar(nombre: str, obtenido, esperado) -> None:
    """Compara lo obtenido con lo esperado y cuenta la comprobación; anota el fallo y lo muestra si no coinciden."""
    global hechas
    hechas += 1
    if obtenido != esperado:
        fallos.append(nombre)
        print(f"  FALLA {nombre}\n    esperado: {esperado!r}\n    obtenido: {obtenido!r}")


# TITULO PARTE 1

def probar_lectura() -> int:
    """Parte 1: tiempos de `ps` y búsqueda de procesos en su salida."""
    for texto, segundos in [("07", 7), ("05:30", 330), ("01:02:03", 3723), ("2-01:00:00", 176400), ("1-02:03:04", 93784)]:
        comprobar(f"etime {texto}", rp.segundos_de_etime(texto), segundos)
    precios = rp.buscar_procesos(PS_EJEMPLO, ["servidor_datos.py"], pid_propio=600)
    comprobar("encuentra el servidor de precios", [(p, s) for p, s, _ in precios], [(1120859, 73)])
    aplicacion = rp.buscar_procesos(PS_EJEMPLO, ["streamlit", "aplicacion.py"], pid_propio=600)
    comprobar("encuentra Streamlit con su tiempo", [(p, s) for p, s, _ in aplicacion], [(1121082, 11144)])
    comprobar("no confunde los procesos entre sí", rp.buscar_procesos(PS_EJEMPLO, ["servidor_datos.py", "streamlit"], pid_propio=600), [])
    comprobar("no encuentra lo que no existe", rp.buscar_procesos(PS_EJEMPLO, ["no_existe.py"], pid_propio=600), [])
    comprobar("excluye al propio vigilante", rp.buscar_procesos(PS_EJEMPLO, ["revivir_procesos.py"], pid_propio=600), [])
    comprobar("sin salida de ps no hay procesos", rp.buscar_procesos("", ["servidor_datos.py"], pid_propio=1), [])
    # puerto del servidor de precios
    with tempfile.TemporaryDirectory() as carpeta:
        archivo = os.path.join(carpeta, "constantes.py")
        with open(archivo, "w", encoding="utf-8") as f:
            f.write("# comentario\nOTRA = 1\nPUERTO = 28000\n")
        comprobar("lee el puerto del archivo", rp.leer_puerto_precios(archivo), 28000)
        with open(archivo, "w", encoding="utf-8") as f:
            f.write("sin puerto\n")
        comprobar("sin la línea usa el puerto de fábrica", rp.leer_puerto_precios(archivo), rp.PUERTO_PRECIOS_POR_DEFECTO)
        comprobar("archivo inexistente usa el de fábrica", rp.leer_puerto_precios(os.path.join(carpeta, "no_existe.py")), rp.PUERTO_PRECIOS_POR_DEFECTO)
    comprobar("el puerto real del proyecto es un número", isinstance(rp.leer_puerto_precios(), int), True)
    return 15


# TITULO PARTE 2

def probar_decision() -> int:
    """Parte 2: tabla de verdad de `decidir`."""
    sano, enfermo = (lambda: True), (lambda: False)
    llamadas = []

    def espia():
        """Anota que se comprobó la salud (no debería ocurrir si el proceso está arrancando)."""
        llamadas.append(1)
        return True

    comprobar("sin proceso -> iniciar", rp.decidir([], sano), "iniciar")
    comprobar("dos copias -> reiniciar", rp.decidir([(1, 500, "a"), (2, 500, "a")], sano), "reiniciar")
    comprobar("arrancando -> esperar", rp.decidir([(1, 30, "a")], enfermo), "esperar")
    comprobar("arrancando no consulta la salud", (rp.decidir([(1, 30, "a")], espia), llamadas), ("esperar", []))
    comprobar("justo en el límite de gracia se revisa", rp.decidir([(1, rp.SEGUNDOS_GRACIA, "a")], sano), "correcto")
    comprobar("maduro y sano -> correcto", rp.decidir([(1, 500, "a")], sano), "correcto")
    comprobar("maduro y sin responder -> reiniciar", rp.decidir([(1, 500, "a")], enfermo), "reiniciar")
    return 7


# TITULO PARTE 3

def probar_salud() -> int:
    """Parte 3: comprobaciones de salud contra un servidor HTTP local y reintentos."""
    respuestas = {}

    class Manejador(http.server.BaseHTTPRequestHandler):
        """Responde lo que la prueba programó para cada ruta."""

        def do_GET(self):
            """Entrega el código y el cuerpo programados para la ruta pedida."""
            codigo, cuerpo = respuestas.get(self.path, (404, "no hay"))
            self.send_response(codigo)
            self.end_headers()
            self.wfile.write(cuerpo.encode())

        def log_message(self, *argumentos):
            """Silencia el registro del servidor de prueba."""

    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    puerto = servidor.server_address[1]
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        respuestas["/salud"] = (200, json.dumps({"ok": True, "v": 6}))
        comprobar("precios sano", rp.responde_servidor_precios(puerto), True)
        respuestas["/salud"] = (200, json.dumps({"ok": False}))
        comprobar("precios con ok falso", rp.responde_servidor_precios(puerto), False)
        respuestas["/salud"] = (200, "no es json")
        comprobar("precios con cuerpo que no es JSON", rp.responde_servidor_precios(puerto), False)
        respuestas["/salud"] = (500, json.dumps({"ok": True}))
        comprobar("precios con error 500", rp.responde_servidor_precios(puerto), False)
        respuestas["/_stcore/health"] = (200, "ok")
        comprobar("aplicación sana", rp.responde_aplicacion(puerto), True)
        respuestas["/_stcore/health"] = (200, "mal")
        comprobar("aplicación con otro texto", rp.responde_aplicacion(puerto), False)
        respuestas["/_stcore/health"] = (503, "ok")
        comprobar("aplicación con error 503", rp.responde_aplicacion(puerto), False)
    finally:
        servidor.shutdown()
        servidor.server_close()
    inicio = time.time()
    comprobar("puerto cerrado no responde", rp.responde_servidor_precios(puerto), False)
    comprobar("puerto cerrado falla rápido (sin colgarse)", time.time() - inicio < 6, True)

    # reintentos
    cuenta = []
    comprobar("sale bien al primer intento", (rp.responde_con_reintentos(lambda: cuenta.append(1) or True, 3, 0), len(cuenta)), (True, 1))
    cuenta.clear()
    comprobar("sale bien al segundo intento", (rp.responde_con_reintentos(lambda: cuenta.append(1) or len(cuenta) >= 2, 3, 0), len(cuenta)), (True, 2))
    cuenta.clear()
    comprobar("se rinde tras todos los intentos", (rp.responde_con_reintentos(lambda: cuenta.append(1) or False, 3, 0), len(cuenta)), (False, 3))
    return 15


# TITULO PARTE 4

def probar_proceso_real() -> int:
    """Parte 4: lanza un proceso que duerme, comprueba su registro y su cierre."""
    with tempfile.TemporaryDirectory() as carpeta:
        registro = os.path.join(carpeta, "salida.log")
        pid = rp.lanzar_proceso([sys.executable, "-c", "import time; print('hola desde el proceso', flush=True); time.sleep(60)"], carpeta, registro)
        try:
            time.sleep(1.5)
            comprobar("el proceso lanzado está vivo", rp._vivo(pid), True)
            with open(registro, encoding="utf-8") as f:
                comprobar("su salida llega al archivo de registro", "hola desde el proceso" in f.read(), True)
        finally:
            rp.cerrar_procesos([pid], espera=5)
        comprobar("tras cerrarlo ya no está", rp._vivo(pid), False)
        comprobar("cerrar un pid que no existe no falla", rp.cerrar_procesos([pid], espera=1), None)
    return 4


# TITULO PARTE 5

def probar_flujo() -> int:
    """Parte 5: `revisar` completo con ps, lanzamiento, cierre y salud reemplazados por simuladores."""
    originales = {n: getattr(rp, n) for n in ("ejecutar_ps", "lanzar_proceso", "cerrar_procesos", "responde_con_reintentos", "anotar", "tomar_candado")}
    mensajes, lanzados, cerrados = [], [], []
    estado = {"ps": "", "sano": True, "fallar_al_lanzar": False}

    def lanzar(comando, carpeta, registro):
        """Simula lanzar: anota el comando y el nombre del registro."""
        if estado["fallar_al_lanzar"]:
            raise OSError("sin memoria")
        lanzados.append((comando[-1] if "servidor_datos.py" in comando else "streamlit", os.path.basename(registro)))
        return 4242

    rp.ejecutar_ps = lambda: estado["ps"]
    rp.lanzar_proceso = lanzar
    rp.cerrar_procesos = lambda pids, espera=0: cerrados.append(sorted(pids))
    rp.responde_con_reintentos = lambda comprobar_: estado["sano"]
    rp.anotar = mensajes.append
    rp.tomar_candado = lambda: open(os.devnull)

    def correr(solo_revisar=False):
        """Ejecuta `revisar` limpiando antes lo anotado."""
        mensajes.clear(); lanzados.clear(); cerrados.clear()
        return rp.revisar(solo_revisar)

    try:
        estado.update(ps="", sano=True)
        comprobar("nada en marcha: salida 0", correr(), 0)
        comprobar("nada en marcha: lanza los dos", lanzados, [("servidor_datos.py", "datos.log"), ("streamlit", "app.log")])
        comprobar("nada en marcha: no cierra nada", cerrados, [])

        estado.update(ps=PS_EJEMPLO.replace("01:13", "05:13"), sano=True)
        correr()
        comprobar("todo sano y maduro: no hace nada", (lanzados, cerrados, mensajes), ([], [], []))

        correr(solo_revisar=True)
        comprobar("solo revisar: informa y no toca", (lanzados, cerrados, len(mensajes)), ([], [], 2))

        estado.update(ps=PS_EJEMPLO.replace("01:13", "05:13"), sano=False)
        correr()
        comprobar("sin responder: cierra y vuelve a lanzar los dos", (sorted(cerrados), [n for n, _ in lanzados]), ([[1120859], [1121082]], ["servidor_datos.py", "streamlit"]))

        estado.update(ps=PS_EJEMPLO, sano=False)  # el servidor lleva 1:13 (arrancando) y Streamlit 3 horas
        correr()
        comprobar("arrancando se respeta; el maduro sin responder se reinicia", ([n for n, _ in lanzados], cerrados), (["streamlit"], [[1121082]]))

        duplicado = PS_EJEMPLO.replace("01:13", "05:13") + " 777    09:00 /x/python3.11_bin /x/bin/streamlit run aplicacion.py\n"
        estado.update(ps=duplicado, sano=True)
        correr()
        comprobar("streamlit duplicado: cierra las dos copias y lanza una", (cerrados, [n for n, _ in lanzados]), ([[777, 1121082]], ["streamlit"]))

        estado.update(ps="", sano=True, fallar_al_lanzar=True)
        comprobar("si no se puede lanzar: salida 1", correr(), 1)
        comprobar("si no se puede lanzar: lo anota y sigue", any("NO se pudo lanzar" in m for m in mensajes), True)
    finally:
        for nombre, funcion in originales.items():
            setattr(rp, nombre, funcion)
    return 14


# TITULO PRINCIPAL

def principal() -> int:
    """Ejecuta las cinco partes y devuelve 0 si todo pasó o 1 si hubo fallos."""
    total = 0
    for numero, (titulo, funcion) in enumerate([("lectura de procesos y tiempos", probar_lectura), ("decisión", probar_decision),
                                                ("salud y reintentos", probar_salud), ("proceso real: lanzar y cerrar", probar_proceso_real),
                                                ("flujo completo", probar_flujo)], 1):
        print(f"Parte {numero}: {titulo}")
        antes = hechas
        funcion()
        print(f"  {hechas - antes} comprobaciones")
    total = hechas
    if fallos:
        print(f"\nFALLARON {len(fallos)} de {total}")
        return 1
    print(f"\nTODO OK ({total} comprobaciones)")
    return 0


if __name__ == "__main__":
    sys.exit(principal())


# -------------------------------------------------------------------------------------------------------
# ---------------------------- FIN Piña y Jara _prueba_revivir_procesos .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
