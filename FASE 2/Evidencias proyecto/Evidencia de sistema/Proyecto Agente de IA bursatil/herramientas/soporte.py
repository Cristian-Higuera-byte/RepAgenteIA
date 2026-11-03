# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara soporte .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
soporte.py
----------
Reportes de soporte: el usuario escribe un problema en la ventana «Soporte» y llega por correo al buzón de soporte.

El correo sale por el mismo servidor y buzón que usa la plataforma para la verificación de correo (herramientas/correo.py). Va a la dirección de la variable SOPORTE_CORREO del
.env y, si no existe, al propio buzón que envía (CORREO_USUARIO). Lleva en «Responder a» el correo de quien reporta, para contestarle directo. Para no abrir una puerta
a correos masivos, cada usuario puede enviar un reporte por minuto y cinco por día; ese conteo se guarda en memoria del proceso, así que se reinicia con el servidor.
"""
import os
import threading
import time
from datetime import datetime
from typing import Optional

from herramientas import correo

# Temas que ofrece la ventana de soporte.
TEMAS = ("Error en la plataforma", "Mi cuenta o la conexión con Capital.com", "Una orden o una operación", "El agente de IA", "Sugerencia", "Otro")

# Largo mínimo y máximo del mensaje, y límites de envío por usuario.
MINIMO_CARACTERES = 10
MAXIMO_CARACTERES = 2000
SEGUNDOS_ENTRE_REPORTES = 60
MAXIMO_POR_DIA = 5

# Envíos recientes por usuario (id -> horas de envío en segundos), protegidos por un candado.
_ENVIOS: dict = {}
_CANDADO = threading.Lock()


# TITULO LIMPIAR

def _limpiar(texto: str, maximo: int) -> str:
    """Quita los caracteres de control (salvo saltos de línea y tabulaciones) y recorta al máximo; así nada del usuario puede alterar las cabeceras del correo."""
    texto = "".join(letra for letra in str(texto or "") if letra in "\n\t" or ord(letra) >= 32)
    return texto.strip()[:maximo]


# TITULO DESTINATARIO

def destinatario() -> str:
    """Dirección a la que llegan los reportes: SOPORTE_CORREO, o el buzón que envía si no se definió."""
    return (os.environ.get("SOPORTE_CORREO", "").strip() or os.environ.get("CORREO_USUARIO", "").strip())


# TITULO CONTROL DE ENVIOS

def _reservar_envio(clave: str) -> Optional[str]:
    """Anota un envío del usuario `clave` si no pasó los límites; devuelve el motivo del rechazo, o None si puede enviar."""
    ahora = time.time()
    with _CANDADO:
        recientes = [momento for momento in _ENVIOS.get(clave, []) if ahora - momento < 86400]
        if recientes and ahora - recientes[-1] < SEGUNDOS_ENTRE_REPORTES:
            _ENVIOS[clave] = recientes
            return "Espera un minuto antes de enviar otro reporte."
        if len(recientes) >= MAXIMO_POR_DIA:
            _ENVIOS[clave] = recientes
            return "Llegaste al máximo de reportes de hoy. Escríbenos al correo de contacto si es urgente."
        recientes.append(ahora)
        _ENVIOS[clave] = recientes
    return None


def _devolver_envio(clave: str) -> None:
    """Deshace el último envío anotado, para no gastarle un cupo al usuario si el correo no salió."""
    with _CANDADO:
        if _ENVIOS.get(clave):
            _ENVIOS[clave].pop()


# TITULO ENVIAR REPORTE

def enviar_reporte(usuario: dict, tema: str, mensaje: str, seccion: str = "", navegador: str = "") -> dict:
    """Valida y envía un reporte de soporte. Devuelve {"ok": bool, "mensaje": str}; nunca lanza error.

    Recibe el usuario (dict con id, nombre y email), el tema (uno de TEMAS), el mensaje, la sección de la plataforma en que estaba y el resumen de su navegador. Efecto secundario:
    envía un correo al buzón de soporte, con el correo del usuario en «Responder a»."""
    if not usuario or not usuario.get("email"):
        return {"ok": False, "mensaje": "Inicia sesión para enviar un reporte."}
    mensaje = _limpiar(mensaje, MAXIMO_CARACTERES)
    if len(mensaje) < MINIMO_CARACTERES:
        return {"ok": False, "mensaje": f"Cuéntanos un poco más (al menos {MINIMO_CARACTERES} caracteres)."}
    tema = tema if tema in TEMAS else "Otro"
    destino = destinatario()
    if not destino or not correo.configurado():
        return {"ok": False, "mensaje": "El soporte por correo no está disponible por ahora. Escríbenos al correo de contacto."}
    clave = str(usuario.get("id") or usuario.get("email"))
    motivo = _reservar_envio(clave)
    if motivo:
        return {"ok": False, "mensaje": motivo}
    nombre = _limpiar(usuario.get("nombre", ""), 80).replace("\n", " ")
    remitente = _limpiar(usuario.get("email", ""), 120).replace("\n", " ")
    texto = (f"Reporte de soporte de P&J Finance\n\nTema: {tema}\nUsuario: {nombre} <{remitente}> (id {usuario.get('id')})\n"
             f"Sección: {_limpiar(seccion, 40) or 'sin dato'}\nFecha: {datetime.now():%Y-%m-%d %H:%M:%S} (hora del servidor)\n"
             f"Navegador: {_limpiar(navegador, 200).replace(chr(10), ' ') or 'sin dato'}\n\nMensaje:\n{mensaje}\n")
    try:
        correo.enviar(destino, f"[Soporte P&J] {tema}", texto, responder_a=remitente)
    except correo.ErrorCorreo:
        _devolver_envio(clave)
        return {"ok": False, "mensaje": "No pudimos enviar tu reporte en este momento. Inténtalo de nuevo en unos minutos."}
    return {"ok": True, "mensaje": "Reporte enviado. Te responderemos al correo de tu cuenta."}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara soporte .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
