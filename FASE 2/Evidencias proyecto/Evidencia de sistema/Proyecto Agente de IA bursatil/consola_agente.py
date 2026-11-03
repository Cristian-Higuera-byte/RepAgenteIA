# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara consola_agente .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
consola_agente.py
-----------------
Chat por terminal para probar el agente sin abrir el dashboard.

Ejecutar:  python consola_agente.py

Además de servir de consola, el dashboard (aplicacion.py) importa este módulo como "lógica principal
del backend" y lo reparte a las vistas que lo necesitan.
"""
import configuracion
from nucleo_agente.agente import Agente  # type: ignore[import-untyped]
from nucleo_agente.llm import ErrorLLM  # type: ignore[import-untyped]

# Texto de ayuda que se muestra al iniciar la consola: lista los comandos disponibles.
AYUDA = "Comandos: /reset (nueva conversación), /perfil <nombre>, /pensar (ver/ocultar razonamiento), /salir"


# TITULO PRINCIPAL

def principal() -> None:
    """
    Ejecuta el chat por terminal hasta que el usuario escribe /salir (o cierra la entrada con Ctrl+C / Ctrl+D).

    Crea el agente del usuario local; si falta la configuración (por ejemplo, la clave de DeepSeek)
    muestra el error y termina. Luego repite: lee una línea, atiende los comandos (/reset, /pensar,
    /perfil, /salir) o, si es un mensaje normal, se lo envía al agente y va imprimiendo su respuesta
    en vivo: texto, razonamiento (solo si está activado), herramientas usadas y un resumen final con
    los tokens consumidos y el perfil. Los errores del modelo se muestran sin cerrar la consola.
    """
    # Crea el agente; si falta la clave de la API u otra configuración, informa y termina.
    try:
        agente = Agente(usuario_id="local")
    except RuntimeError as e:
        print(e)
        return

    # Indica si se imprime el razonamiento interno del modelo (se alterna con /pensar).
    mostrar_razonamiento = False
    print("Agente bursátil listo.")
    print("Memoria:", f"activa (chat {str(agente.memoria.chat_id)[:8]})" if agente.memoria else "DESACTIVADA")
    print(AYUDA)

    # Bucle principal: una iteración por cada línea que escribe el usuario.
    while True:
        try:
            entrada = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Ctrl+D / Ctrl+C: salida limpia.
            print()
            break
        if not entrada:
            continue

        # --- Comandos de la consola ---
        if entrada == "/salir":
            break
        if entrada == "/reset":
            agente.reiniciar()
            print("Conversación reiniciada.")
            continue
        if entrada == "/pensar":
            mostrar_razonamiento = not mostrar_razonamiento
            print(f"Razonamiento visible: {mostrar_razonamiento}")
            continue
        if entrada.startswith("/perfil"):
            partes = entrada.split()
            if len(partes) == 2 and partes[1] in configuracion.PERFILES:
                agente.perfil = partes[1]
                print(f"Perfil activo: {partes[1]}")
            else:
                print("Perfiles disponibles:", ", ".join(configuracion.PERFILES))
            continue

        # --- Mensaje normal: se envía al agente y se imprime su respuesta a medida que llega ---
        print("\nAgente: ", end="", flush=True)
        try:
            for evento in agente.responder_stream(entrada):
                if evento.tipo == "texto":
                    print(evento.texto, end="", flush=True)
                elif evento.tipo == "razonamiento" and mostrar_razonamiento:
                    print(evento.texto, end="", flush=True)
                elif evento.tipo == "herramienta":
                    print(f"\n  [herramienta] {evento.texto}({evento.datos})", flush=True)
                elif evento.tipo == "fin":
                    d = evento.datos
                    print(f"\n  [{d['tokens_entrada']} entrada / {d['tokens_salida']} salida | perfil: {d['perfil']}]")
        except ErrorLLM as e:
            print(f"\n[Error] {e}")


# Solo arranca el chat cuando el archivo se ejecuta directamente (python consola_agente.py),
# no cuando el dashboard lo importa.
if __name__ == "__main__":
    principal()


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara consola_agente .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
