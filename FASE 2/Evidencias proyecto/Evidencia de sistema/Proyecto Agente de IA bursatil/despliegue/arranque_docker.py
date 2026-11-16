# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara arranque_docker .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""
arranque_docker.py
------------------
Punto de entrada del contenedor Docker: levanta el servidor de precios y el dashboard de Streamlit en el mismo contenedor y los
vigila. Si uno de los dos procesos se cae, termina el otro y sale con error, de modo que Docker reinicia el contenedor entero
(política `restart: unless-stopped` del docker-compose.yml). Reenvía las señales de parada (docker stop) a ambos procesos.

Se ejecuta con:  python despliegue/arranque_docker.py
Variables opcionales: PUERTO_DASHBOARD (por defecto 8501).
"""
import os
import signal
import subprocess
import sys
import time

# Puerto en el que escucha el dashboard dentro del contenedor.
PUERTO_DASHBOARD = os.environ.get("PUERTO_DASHBOARD", "8501")
# Segundos que se espera a que los procesos cierren solos antes de forzarlos.
ESPERA_CIERRE = 10


# TITULO COMANDOS

def comandos() -> list:
    """Lista de (nombre, comando) de los dos procesos del sistema."""
    return [
        ("servidor de precios", [sys.executable, "servidor_datos.py"]),
        ("dashboard", [sys.executable, "-m", "streamlit", "run", "aplicacion.py", "--server.port", PUERTO_DASHBOARD, "--server.address", "0.0.0.0",
                       "--server.headless", "true"]),
    ]


# TITULO PARAR

def parar(procesos: list) -> None:
    """Pide a los procesos que terminen y, si no lo hacen a tiempo, los fuerza."""
    for _, p in procesos:
        if p.poll() is None:
            p.terminate()
    limite = time.time() + ESPERA_CIERRE
    for _, p in procesos:
        while p.poll() is None and time.time() < limite:
            time.sleep(0.2)
        if p.poll() is None:
            p.kill()


# TITULO PRINCIPAL

def principal() -> int:
    """Arranca los procesos y espera. Devuelve 0 si se pidió detener el contenedor y 1 si algún proceso se cayó."""
    procesos = []
    detener = {"pedido": False}

    def al_recibir_senal(_numero, _marco):
        detener["pedido"] = True
    signal.signal(signal.SIGTERM, al_recibir_senal)
    signal.signal(signal.SIGINT, al_recibir_senal)

    for nombre, comando in comandos():
        print(f"[arranque] iniciando {nombre}: {' '.join(comando)}", flush=True)
        procesos.append((nombre, subprocess.Popen(comando)))
        time.sleep(1)                                          # el servidor de precios debe estar listo antes que el dashboard
    codigo = 0
    while not detener["pedido"]:
        for nombre, p in procesos:
            if p.poll() is not None:
                print(f"[arranque] el proceso «{nombre}» terminó con código {p.returncode}; se detiene el contenedor.", flush=True)
                codigo = 1
                detener["pedido"] = True
                break
        time.sleep(1)
    parar(procesos)
    return codigo


if __name__ == "__main__":
    sys.exit(principal())


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara arranque_docker .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
