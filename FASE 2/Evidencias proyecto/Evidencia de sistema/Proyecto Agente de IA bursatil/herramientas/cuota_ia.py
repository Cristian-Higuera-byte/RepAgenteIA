# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara cuota_ia .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Cuota mensual de uso de la IA por usuario y plan: cuántos tokens lleva gastados, cuántos le quedan y si puede seguir usando el agente.

Cada llamada al modelo suma sus tokens (entrada + salida, multiplicados por el peso del modelo) al uso del mes. El límite sale del plan del
usuario (`configuracion.PLANES_IA`). Al agotarlo, el agente deja de responder hasta que se renueve la cuota el primer día del mes siguiente
o el usuario cambie de plan. La cuota es de la PERSONA, no de la cuenta: demo y real comparten el mismo contador (se guarda en la carpeta del
usuario, un nivel sobre la de cada cuenta), así que cambiar de cuenta no reinicia el gasto.

El uso se anota en un archivo por mes (`cuota_ia_AAAA-MM.jsonl`), una línea por llamada y solo agregando al final: así dos procesos que escriben a
la vez (la página y el motor de vigilancias) no se pisan. El plan se guarda en `cuota_plan.json`. El límite es «blando»: la comprobación se
hace al empezar cada consulta, de modo que una consulta que empieza justo antes del tope puede pasarse un poco.
"""
import json
import os
import threading
import time
from datetime import datetime

import configuracion
from herramientas import plan_usuario
from herramientas.carpeta_usuario import carpeta_de
from herramientas.backends import sesiones_capital

# Nombre del archivo donde se guarda el plan del usuario
_ARCHIVO_PLAN = "cuota_plan.json"
# Candado de las escrituras dentro del proceso
_CANDADO = threading.Lock()
# Suma ya calculada de cada archivo de uso: ruta -> (tamaño, fecha de modificación, total). Se recalcula solo si el archivo cambió.
_SUMAS: dict = {}
# Nombres de los meses para el aviso de renovación
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# TITULO ERROR CUOTA

class ErrorCuota(Exception):
    """Se lanza al intentar usar el agente con la cuota del mes agotada. El mensaje ya es legible para el usuario."""


# TITULO CARPETA CUOTA

def _carpeta_cuota() -> str:
    """Carpeta donde se guarda la cuota del usuario actual: la del usuario (un nivel sobre la de su cuenta demo o real)."""
    clave = sesiones_capital.clave_actual()
    carpeta = carpeta_de(clave)
    return os.path.dirname(carpeta) if len(clave) == 2 else carpeta


# TITULO MES ACTUAL

def _mes_actual() -> str:
    """Mes en curso como "AAAA-MM" (hora local)."""
    return datetime.now().strftime("%Y-%m")


# TITULO RUTA USO

def _ruta_uso(mes: str) -> str:
    """Ruta del archivo de uso del usuario actual para el mes `mes` ("AAAA-MM")."""
    return os.path.join(_carpeta_cuota(), f"cuota_ia_{mes}.jsonl")


# TITULO PLAN ACTUAL

def plan_actual() -> str:
    """Clave del plan del usuario actual (por ejemplo "pro"). Si no tiene uno guardado o es inválido, el plan por defecto
    (el del modo local si la plataforma corre para un solo usuario).

    En multiusuario el plan se lee de Supabase (`herramientas/plan_usuario.py`, con caché de unos segundos); en modo local, de un archivo."""
    clave = sesiones_capital.clave_actual()
    if sesiones_capital.MULTIUSUARIO and len(clave) == 2:
        plan = plan_usuario.plan_de(clave[0])
        return plan if plan in configuracion.PLANES_IA else configuracion.PLAN_POR_DEFECTO
    try:
        with open(os.path.join(_carpeta_cuota(), _ARCHIVO_PLAN), "r", encoding="utf-8") as f:
            plan = json.load(f).get("plan")
        if plan in configuracion.PLANES_IA:
            return plan
    except (OSError, ValueError, AttributeError):
        pass
    return configuracion.PLAN_POR_DEFECTO if sesiones_capital.MULTIUSUARIO else configuracion.PLAN_MODO_LOCAL


# TITULO FIJAR PLAN

def fijar_plan(plan: str, origen: str = "prueba") -> bool:
    """Asigna `plan` al usuario actual. Devuelve False, sin cambiar nada, si el plan no existe (o, en multiusuario, si no se pudo guardar).

    En multiusuario se guarda en Supabase junto con su historial; en modo local, en un archivo (escritura atómica). `origen` anota de dónde viene
    el cambio ("prueba" mientras no se cobra, "pago" o "admin"). Lo usan la vista de Planes y el Laboratorio; cuando haya cobro, el plan vendrá de
    la suscripción del usuario."""
    if plan not in configuracion.PLANES_IA:
        return False
    clave = sesiones_capital.clave_actual()
    if sesiones_capital.MULTIUSUARIO and len(clave) == 2:
        return plan_usuario.guardar(clave[0], plan, origen, anterior=plan_actual())
    carpeta = _carpeta_cuota()
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, _ARCHIVO_PLAN)
    with _CANDADO:
        with open(ruta + ".tmp", "w", encoding="utf-8") as f:
            json.dump({"plan": plan}, f)
        os.replace(ruta + ".tmp", ruta)
    return True


# TITULO PESO

def peso(modelo: str) -> float:
    """Cuánta cuota gasta cada token del `modelo` (1 si no está en `configuracion.PESO_MODELO`)."""
    return float(configuracion.PESO_MODELO.get(modelo, 1.0))


# TITULO SUMAR

def sumar(modelo: str, tokens: int) -> None:
    """Suma al uso del mes los `tokens` gastados por una llamada al `modelo` (ya multiplicados por el peso del modelo).

    Agrega una línea al archivo del mes. Nunca lanza excepciones: anotar el uso no debe tumbar una respuesta."""
    try:
        if tokens <= 0:
            return
        carpeta = _carpeta_cuota()
        os.makedirs(carpeta, exist_ok=True)
        linea = json.dumps({"t": int(time.time()), "modelo": modelo, "tok": round(tokens * peso(modelo), 2)}) + "\n"
        with _CANDADO:
            with open(_ruta_uso(_mes_actual()), "a", encoding="utf-8") as f:
                f.write(linea)
    except Exception:  # noqa: BLE001
        pass


# TITULO USADO

def usado(mes: str | None = None) -> float:
    """Tokens (ponderados) gastados por el usuario actual en el mes `mes` ("AAAA-MM"; por defecto el actual).

    Suma el archivo de uso del mes; guarda el resultado y solo vuelve a leerlo si el archivo cambió de tamaño o de fecha."""
    ruta = _ruta_uso(mes or _mes_actual())
    try:
        info = os.stat(ruta)
    except OSError:
        return 0.0
    clave = (info.st_size, info.st_mtime_ns)
    guardado = _SUMAS.get(ruta)
    if guardado and guardado[0] == clave:
        return guardado[1]
    total = 0.0
    with open(ruta, "r", encoding="utf-8") as f:
        for linea in f:
            try:
                total += float(json.loads(linea).get("tok", 0) or 0)
            except (ValueError, AttributeError):
                continue
    _SUMAS[ruta] = (clave, total)
    return total


# TITULO RENUEVA

def _renueva() -> str:
    """Texto con el día en que se renueva la cuota: el primero del mes siguiente (por ejemplo "1 de noviembre")."""
    hoy = datetime.now()
    mes_siguiente = 1 if hoy.month == 12 else hoy.month + 1
    return f"1 de {_MESES[mes_siguiente - 1]}"


# TITULO ESTADO

def estado() -> dict:
    """Estado de la cuota del usuario actual.

    Devuelve {"plan", "nombre", "limite", "usado", "restante", "porcentaje" (0 a 100, sin pasar de 100), "agotada", "nivel" ("ok",
    "aviso" o "critico" según los umbrales de la configuración), "renueva"}. Los tokens vienen redondeados a enteros."""
    plan = plan_actual()
    limite = int(configuracion.PLANES_IA[plan]["tokens_mes"])
    gastado = usado()
    porcentaje = min(100.0, gastado / limite * 100.0) if limite > 0 else 100.0
    agotada = gastado >= limite
    nivel = ("critico" if porcentaje >= configuracion.UMBRAL_CRITICO_PCT else "aviso" if porcentaje >= configuracion.UMBRAL_AVISO_PCT else "ok")
    return {"plan": plan, "nombre": configuracion.PLANES_IA[plan]["nombre"], "limite": limite, "usado": int(round(gastado)),
            "restante": max(0, int(round(limite - gastado))), "porcentaje": porcentaje, "agotada": agotada, "nivel": nivel, "renueva": _renueva()}


# TITULO FORMATO

def formato(n: float) -> str:
    """Formatea una cantidad de tokens con puntos de miles (por ejemplo 45.200)."""
    return f"{int(round(n)):,}".replace(",", ".")


# TITULO TEXTO USO

def texto_uso() -> str:
    """Texto corto del uso del mes para el pie de cada respuesta: «Uso del mes: 45.200 / 300.000 tokens (15 %) · plan Gratis»."""
    e = estado()
    return f"Uso del mes: {formato(e['usado'])} / {formato(e['limite'])} tokens ({e['porcentaje']:.0f} %) · plan {e['nombre']}"


# TITULO EXIGIR

def exigir() -> None:
    """Lanza `ErrorCuota` si el usuario ya gastó toda la cuota del mes; no hace nada si aún le queda.

    Se llama al empezar cada consulta al agente. El mensaje explica el límite, cuándo se renueva y que puede cambiar de plan."""
    e = estado()
    if e["agotada"]:
        raise ErrorCuota(f"Alcanzaste el límite de tokens de tu plan {e['nombre']} este mes ({formato(e['limite'])}). La cuota se renueva el "
                         f"{e['renueva']}; mientras tanto puedes pasar a un plan superior para seguir usando el agente.")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara cuota_ia .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
