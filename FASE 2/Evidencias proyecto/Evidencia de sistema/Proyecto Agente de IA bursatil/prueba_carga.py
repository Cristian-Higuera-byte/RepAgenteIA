"""Prueba de carga simple de la API de precios.

Uso (desde Windows o Kali, con Python 3):
    python prueba_carga.py https://pyj.rmcabogados.cl/salud 50 200
Argumentos: URL, hilos simultáneos, solicitudes totales.
Usa la ruta pública /salud: mide la capacidad de respuesta sin necesitar credenciales.
Guarda el resultado en resultado_carga.txt para adjuntarlo como evidencia.
"""
import statistics, sys, threading, time, urllib.request, urllib.error
from datetime import datetime

url = sys.argv[1] if len(sys.argv) > 1 else "https://pyj.rmcabogados.cl/salud"
hilos = int(sys.argv[2]) if len(sys.argv) > 2 else 50
total = int(sys.argv[3]) if len(sys.argv) > 3 else 200
tiempos, codigos, candado = [], {}, threading.Lock()
pendientes = list(range(total))

def trabajar():
    while True:
        with candado:
            if not pendientes:
                return
            pendientes.pop()
        t0 = time.perf_counter()
        try:
            codigo = urllib.request.urlopen(url, timeout=15).status
        except urllib.error.HTTPError as e:
            codigo = e.code
        except Exception:
            codigo = "error"
        dt = time.perf_counter() - t0
        with candado:
            tiempos.append(dt)
            codigos[codigo] = codigos.get(codigo, 0) + 1

inicio = time.perf_counter()
lista = [threading.Thread(target=trabajar) for _ in range(hilos)]
for h in lista: h.start()
for h in lista: h.join()
duracion = time.perf_counter() - inicio
tiempos.sort()
p95 = tiempos[int(len(tiempos) * 0.95) - 1]
salida = [
    f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}",
    f"URL: {url}", f"Hilos simultáneos: {hilos}", f"Solicitudes: {total}",
    f"Duración total: {duracion:.2f} s", f"Solicitudes por segundo: {total / duracion:.1f}",
    f"Tiempo medio: {statistics.mean(tiempos) * 1000:.0f} ms",
    f"Mediana: {statistics.median(tiempos) * 1000:.0f} ms", f"Percentil 95: {p95 * 1000:.0f} ms",
    f"Máximo: {max(tiempos) * 1000:.0f} ms", f"Códigos de respuesta: {codigos}",
]
print("\n".join(salida))
open("resultado_carga.txt", "w", encoding="utf-8").write("\n".join(salida) + "\n")
