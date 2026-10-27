# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __main__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Prueba rápida de conexión:  python -m nucleo_agente.llm   (desde la carpeta del proyecto).

Envía un mensaje mínimo al perfil "rapido" por streaming, imprime la respuesta en vivo y, al final, los
tokens de entrada y salida. Hace una llamada real a la API de DeepSeek (requiere DEEPSEEK_API_KEY).
"""
from nucleo_agente.llm import ClienteLLM

# Cliente con el perfil rápido y una petición de una sola línea.
llm = ClienteLLM("rapido")
# El texto se imprime a medida que llega; el evento "final" trae el conteo de tokens.
for ev in llm.chat_stream([{"role": "user", "content": "Responde solo: conexión OK"}]):
    if ev.tipo == "texto":
        print(ev.texto, end="", flush=True)
    elif ev.tipo == "final" and (respuesta := ev.respuesta) is not None:
        print(f"\n[{respuesta.tokens_entrada} tokens entrada / {respuesta.tokens_salida} salida]")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __main__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
