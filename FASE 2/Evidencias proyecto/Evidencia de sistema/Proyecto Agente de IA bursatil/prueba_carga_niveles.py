"""Prueba de carga por niveles de la API de precios.

Uso:  python prueba_carga_niveles.py https://pyj.rmcabogados.cl/salud
Prueba 5, 10, 20 y 50 conexiones simultáneas (40 solicitudes por nivel), distingue el tipo de error
y guarda el resultado en resultado_carga_niveles.txt para adjuntarlo como evidencia.
"""
import socket, statistics, sys, threading, time, urllib.error, urllib.request
from datetime import datetime

url = sys.argv[1] if len(sys.argv) > 1 else "https://pyj.rmcabogados.cl/salud"
NIVELES, POR_NIVEL, ESPERA = (5, 10, 20, 50), 40, 15

def una_solicitud():
    t0 = time.perf_counter()
    try:
        codigo = str(urllib.request.urlopen(url, timeout=ESPERA).status)
    except urllib.error.HTTPError as e:
        codigo = f"HTTP {e.code}"
    except (socket.timeout, TimeoutError):
        codigo = "timeout"
    except urllib.error.URLError as e:
        codigo = "timeout" if "timed out" in str(e.reason) else f"conexión: {type(e.reason).__name__}"
    except Exception as e:
        codigo = f"otro: {type(e).__name__}"
    return codigo, time.perf_counter() - t0

def nivel(hilos):
    pendientes, resultados, candado = list(range(POR_NIVEL)), [], threading.Lock()
    def trabajar():
        while True:
            with candado:
                if not pendientes: return
                pendientes.pop()
            r = una_solicitud()
            with candado: resultados.append(r)
    t0 = time.perf_counter()
    hs = [threading.Thread(target=trabajar) for _ in range(hilos)]
    [h.start() for h in hs]; [h.join() for h in hs]
    dur = time.perf_counter() - t0
    codigos = {}
    for c, _ in resultados: codigos[c] = codigos.get(c, 0) + 1
    ok = sorted(t for c, t in resultados if c == "200")
    linea = (f"{hilos:>3} hilos | OK {codigos.get('200', 0)}/{POR_NIVEL} | "
             f"mediana OK {statistics.median(ok) * 1000 if ok else 0:.0f} ms | "
             f"{POR_NIVEL / dur:.1f} sol/s | {dur:.1f} s | {codigos}")
    print(linea, flush=True)
    return linea

salida = [f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}", f"URL: {url}", f"Solicitudes por nivel: {POR_NIVEL}; espera máxima: {ESPERA} s"]
for n in NIVELES:
    salida.append(nivel(n)); time.sleep(3)
open("resultado_carga_niveles.txt", "w", encoding="utf-8").write("\n".join(salida) + "\n")
