# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara gestor_alertas .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
gestor_alertas.py
-------------------
Módulo para gestionar y evaluar alertas bursátiles proactivas de forma local.

Las alertas (ticker, condición 'menor'/'mayor' y precio objetivo) se persisten
en un archivo JSON dentro de `data/`. La evaluación consulta el último precio
de cierre en Yahoo Finance (yfinance) y desactiva cada alerta una vez que se
cumple. Expone `crear_alerta`, `listar_alertas` y `evaluar_alertas_activas`.
"""
import json
import os
from datetime import datetime
import yfinance as yf  # type: ignore[import-untyped]

from herramientas import permisos_plan

# Ruta (relativa a la carpeta de ejecución) del JSON donde se guardan las alertas.
ARCHIVO_ALERTAS = "data/alertas_activas.json"


# TITULO CARGAR ALERTAS

def _cargar_alertas() -> list:
    """
    Lee las alertas guardadas en disco.

    Devuelve la lista de diccionarios del JSON; si el archivo no existe o está
    corrupto/ilegible devuelve una lista vacía (nunca lanza excepción).
    """
    if not os.path.exists(ARCHIVO_ALERTAS):
        return []
    try:
        with open(ARCHIVO_ALERTAS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# TITULO GUARDAR ALERTAS

def _guardar_alertas(alertas: list):
    """
    Sobrescribe el archivo JSON de alertas con la lista recibida.

    Escribe en UTF-8 con sangría de 4 espacios. Efecto secundario: escritura en
    disco; falla si la carpeta `data/` no existe.
    """
    os.makedirs(os.path.dirname(ARCHIVO_ALERTAS) or ".", exist_ok=True)
    with open(ARCHIVO_ALERTAS, "w", encoding="utf-8") as f:
        json.dump(alertas, f, indent=4, ensure_ascii=False)


# TITULO CREAR ALERTA

def crear_alerta(ticker: str, condicion: str, valor_objetivo: float) -> str:
    """
    Registra una nueva alerta bursátil.

    Parámetros:
        ticker (str): Símbolo del activo (ej. TSLA, AAPL).
        condicion (str): 'menor' (precio cae por debajo) o 'mayor' (precio supera).
        valor_objetivo (float): Precio límite para disparar la alerta.

    Devuelve un mensaje de confirmación con el id asignado. Efecto secundario:
    escribe el archivo JSON de alertas. El id es el mayor id existente + 1,
    así nunca se repite aunque se hayan borrado alertas.
    """
    # Carga las alertas existentes para calcular el siguiente id.
    alertas = _cargar_alertas()
    # El plan del usuario limita cuántas alertas puede tener activas a la vez (herramientas/permisos_plan.py).
    tope = permisos_plan.limite("alertas_precio_activas")
    activas = sum(1 for a in alertas if a.get("activa", True))
    if tope is not None and activas >= tope:
        return "⚠️ " + permisos_plan.mensaje_bloqueo("alertas_precio_activas") + " Elimina o deja que se dispare alguna alerta antes de crear otra."
    # Arma el registro normalizando ticker (mayúsculas) y condición (minúsculas).
    nueva = {
        "id": max((int(a.get("id", 0)) for a in alertas), default=0) + 1,
        "ticker": ticker.upper(),
        "condicion": condicion.lower(),  # "menor" o "mayor"
        "valor_objetivo": float(valor_objetivo),
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "activa": True
    }
    # Agrega la alerta y persiste la lista completa.
    alertas.append(nueva)
    _guardar_alertas(alertas)
    return f"✅ Alerta creada exitosamente [ID: {nueva['id']}]: Avisar si {ticker.upper()} está {condicion} a {valor_objetivo}."


# TITULO LISTAR ALERTAS

def listar_alertas() -> list:
    """Devuelve la lista completa de alertas registradas (activas e inactivas) leída del JSON."""
    return _cargar_alertas()


# TITULO EVALUAR ALERTAS ACTIVAS

def evaluar_alertas_activas() -> str:
    """
    Revisa todas las alertas activas contra los precios actuales del mercado
    y avisa si alguna condición se ha cumplido.

    Para cada alerta activa consulta en yfinance el último cierre diario y lo
    compara con el objetivo ('menor': precio <= objetivo; 'mayor': precio >=
    objetivo). Las alertas disparadas se marcan como inactivas y todo el estado
    se guarda de nuevo en disco. Devuelve un reporte de texto con una línea por
    alerta evaluada (disparada, pendiente o con error).
    """
    # Carga el estado actual; sin alertas no hay nada que evaluar.
    alertas = _cargar_alertas()
    if not alertas:
        return "No hay alertas activas configuradas en el sistema."
    reporte = "--- EVALUACIÓN DE ALERTAS PROACTIVAS ---\n"
    disparadas = 0
    # Recorre solo las alertas todavía activas.
    for alerta in alertas:
        if not alerta["activa"]:
            continue
        ticker = alerta["ticker"]
        condicion = alerta["condicion"]
        objetivo = alerta["valor_objetivo"]
        try:
            # Obtener precio actual de mercado
            ticket = yf.Ticker(ticker)
            historial = ticket.history(period="1d")
            if historial.empty:
                continue
            precio_actual = float(historial["Close"].iloc[-1])
            # Evalúa la condición contra el precio actual.
            condicion_cumplida = False
            if condicion == "menor" and precio_actual <= objetivo:
                condicion_cumplida = True
            elif condicion == "mayor" and precio_actual >= objetivo:
                condicion_cumplida = True
            # Reporta el resultado; si se cumplió, la alerta se desactiva.
            if condicion_cumplida:
                disparadas += 1
                reporte += f"🚨 ¡ALERTA DISPARADA! El activo {ticker} cotiza a {precio_actual:.2f} (Objetivo: {condicion} a {objetivo}).\n"
                alerta["activa"] = False  # Desactivar tras cumplirse
            else:
                reporte += f"⏳ Alerta ID {alerta['id']} ({ticker}): Precio actual {precio_actual:.2f} (Aún no se cumple {condicion} a {objetivo}).\n"
        except Exception as e:
            reporte += f"❌ Error evaluando alerta para {ticker}: {str(e)}\n"
    # Persiste los cambios de estado (alertas desactivadas).
    _guardar_alertas(alertas)
    if disparadas == 0:
        reporte += "\nNinguna alerta ha alcanzado su valor objetivo en este ciclo."
    return reporte


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara gestor_alertas .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
