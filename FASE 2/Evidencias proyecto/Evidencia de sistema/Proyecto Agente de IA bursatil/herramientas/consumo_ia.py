# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara consumo_ia .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Registro y cálculo del CONSUMO DE IA (tokens y costo) del agente, por usuario y cuenta.

Cada vez que el agente llama al modelo, `nucleo_agente/llm/respuesta.py` avisa aquí con los tokens que gastó la llamada. Se guarda
una línea por llamada en `consumo_ia.jsonl`, dentro de la carpeta de datos del usuario y la cuenta (`herramientas/carpeta_usuario.py`),
con la hora, el perfil y modelo, los tokens de entrada (con cuántos fueron de caché), los de salida, el origen (`chat` o `vigilancia`)
y el identificador del turno de conversación al que pertenece.

El costo se calcula al leer, con una tabla de precios por millón de tokens (la edita el usuario en el Laboratorio), así que cambiar los
precios recalcula todo el historial. Registrar nunca debe romper al agente: cualquier fallo al escribir se ignora.
"""
import contextvars
import json
import os
import threading
import time
import uuid
from contextlib import contextmanager

from herramientas.carpeta_usuario import carpeta_usuario, ruta_archivo

# Nombre del archivo de consumo de cada cuenta
_ARCHIVO = "consumo_ia.jsonl"
# Tamaño a partir del cual se recorta el archivo (conserva las últimas líneas) y cuántas líneas se dejan
_MAX_BYTES = 5_000_000
_LINEAS_AL_RECORTAR = 20000
# Candado que serializa las escrituras dentro del proceso
_CANDADO = threading.Lock()
# Origen de las llamadas del hilo actual ("chat" por defecto; la vigilancia lo cambia) y turno de conversación en curso
_ORIGEN = contextvars.ContextVar("consumo_ia_origen", default="chat")
_TURNO = contextvars.ContextVar("consumo_ia_turno", default="")


# TITULO NUEVO TURNO

def nuevo_turno() -> str:
    """Marca el comienzo de un turno de conversación (un mensaje del usuario y todo lo que el agente hace para responderlo).

    Las llamadas al modelo que ocurran después en este hilo se guardan con ese identificador, para contar turnos y no solo llamadas."""
    turno = uuid.uuid4().hex[:8]
    _TURNO.set(turno)
    return turno


# TITULO ORIGEN

@contextmanager
def origen(nombre: str):
    """Contexto que etiqueta con `nombre` (por ejemplo "vigilancia") las llamadas al modelo hechas dentro, y deja un turno nuevo propio."""
    ficha_origen, ficha_turno = _ORIGEN.set(nombre), _TURNO.set(uuid.uuid4().hex[:8])
    try:
        yield
    finally:
        _ORIGEN.reset(ficha_origen)
        _TURNO.reset(ficha_turno)


# TITULO REGISTRAR

def registrar(perfil: str, modelo: str, usage) -> None:
    """Guarda una línea con el consumo de una llamada al modelo. `usage` es el objeto de uso que entrega la API (puede ser None).

    Toma `prompt_tokens`, `completion_tokens` y `prompt_cache_hit_tokens` (los tokens de entrada que salieron de la caché del proveedor,
    más baratos). Sin datos de uso no guarda nada. También suma los tokens a la cuota mensual del usuario (`herramientas/cuota_ia.py`).
    Nunca lanza excepciones."""
    try:
        entrada = int(getattr(usage, "prompt_tokens", 0) or 0)
        salida = int(getattr(usage, "completion_tokens", 0) or 0)
        if entrada <= 0 and salida <= 0:
            return
        acierto = min(entrada, int(getattr(usage, "prompt_cache_hit_tokens", 0) or 0))
        linea = json.dumps({"t": int(time.time()), "perfil": perfil, "modelo": modelo, "entrada": entrada, "acierto": acierto,
                            "salida": salida, "origen": _ORIGEN.get(), "turno": _TURNO.get()}, ensure_ascii=False)
        with _CANDADO:
            os.makedirs(carpeta_usuario(), exist_ok=True)
            ruta = ruta_archivo(_ARCHIVO)
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(linea + "\n")
            if os.path.getsize(ruta) > _MAX_BYTES:
                _recortar(ruta)
    except Exception:  # noqa: BLE001 - registrar el consumo nunca debe tumbar una respuesta del agente
        pass
    try:
        from herramientas import cuota_ia     # además de anotarla, la llamada gasta cuota del plan del usuario
        cuota_ia.sumar(modelo, int(getattr(usage, "prompt_tokens", 0) or 0) + int(getattr(usage, "completion_tokens", 0) or 0))
    except Exception:  # noqa: BLE001
        pass


# TITULO RECORTAR

def _recortar(ruta: str) -> None:
    """Deja en el archivo solo las últimas `_LINEAS_AL_RECORTAR` líneas (escribe a un temporal y lo renombra)."""
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.readlines()[-_LINEAS_AL_RECORTAR:]
    temporal = ruta + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        f.writelines(lineas)
    os.replace(temporal, ruta)


# TITULO LEER

def leer(desde: float = 0.0) -> list:
    """Devuelve los registros de consumo de la cuenta actual con hora igual o posterior a `desde` (marca de tiempo en segundos).

    Ignora las líneas dañadas. Lista vacía si el archivo no existe."""
    salida = []
    try:
        with open(ruta_archivo(_ARCHIVO), "r", encoding="utf-8") as f:
            for linea in f:
                try:
                    r = json.loads(linea)
                except ValueError:
                    continue
                if isinstance(r, dict) and float(r.get("t", 0) or 0) >= desde:
                    salida.append(r)
    except OSError:
        return []
    return salida


# TITULO COSTO

def costo(registro: dict, precios: dict) -> float:
    """Costo en dólares de una llamada, con los precios por millón de tokens del modelo (`entrada_acierto`, `entrada_fallo`, `salida`).

    Los tokens de entrada que salieron de la caché cuestan `entrada_acierto`; el resto de la entrada, `entrada_fallo`. Si el modelo no
    está en la tabla de precios devuelve 0 (y el panel lo avisa)."""
    p = precios.get(registro.get("modelo", ""))
    if not p:
        return 0.0
    entrada, acierto = int(registro.get("entrada", 0) or 0), int(registro.get("acierto", 0) or 0)
    return (acierto * p["entrada_acierto"] + max(0, entrada - acierto) * p["entrada_fallo"] + int(registro.get("salida", 0) or 0) * p["salida"]) / 1_000_000


# TITULO SUMAR

def _sumar(grupo: list, precios: dict) -> dict:
    """Totales de un grupo de registros: llamadas, turnos distintos, tokens de entrada y salida, y costo en dólares."""
    return {"llamadas": len(grupo), "turnos": len({r.get("turno") or f"s{r.get('t')}" for r in grupo}),
            "entrada": sum(int(r.get("entrada", 0) or 0) for r in grupo), "salida": sum(int(r.get("salida", 0) or 0) for r in grupo),
            "costo": sum(costo(r, precios) for r in grupo)}


# TITULO RESUMIR

def resumir(registros: list, precios: dict, dias: int) -> dict:
    """Resume el consumo: total, por origen, por modelo, por día y proyección mensual.

    `dias` es el largo del periodo analizado (para promediar). Devuelve {"total", "por_origen", "por_modelo", "por_dia" ({"AAAA-MM-DD": costo}),
    "por_dia_origen" ({"AAAA-MM-DD": {origen: costo}}), "sin_precio" (modelos usados que no están en la tabla),
    "mensual_proyectado" (costo del periodo / dias × 30)}."""
    por_origen, por_modelo, por_dia, por_dia_origen = {}, {}, {}, {}
    for r in registros:
        por_origen.setdefault(r.get("origen", "chat"), []).append(r)
        por_modelo.setdefault(r.get("modelo", "?"), []).append(r)
        dia = time.strftime("%Y-%m-%d", time.localtime(int(r.get("t", 0) or 0)))
        por_dia[dia] = por_dia.get(dia, 0.0) + costo(r, precios)
        celda = por_dia_origen.setdefault(dia, {})
        celda[r.get("origen", "chat")] = celda.get(r.get("origen", "chat"), 0.0) + costo(r, precios)
    total = _sumar(registros, precios)
    return {"total": total, "por_origen": {k: _sumar(v, precios) for k, v in sorted(por_origen.items())},
            "por_modelo": {k: _sumar(v, precios) for k, v in sorted(por_modelo.items())}, "por_dia": dict(sorted(por_dia.items())),
            "por_dia_origen": dict(sorted(por_dia_origen.items())),
            "sin_precio": sorted(m for m in por_modelo if m not in precios),
            "mensual_proyectado": total["costo"] / max(1, dias) * 30.0}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara consumo_ia .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
