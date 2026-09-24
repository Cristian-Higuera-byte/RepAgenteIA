"""
alertas_manager.py
-------------------
Módulo para gestionar y evaluar alertas bursátiles proactivas de forma local.
"""

import json
import os
from datetime import datetime

import yfinance as yf  # type: ignore[import-untyped]

ARCHIVO_ALERTAS = "data/alertas_activas.json"

def _cargar_alertas() -> list:
    if not os.path.exists(ARCHIVO_ALERTAS):
        return []
    try:
        with open(ARCHIVO_ALERTAS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _guardar_alertas(alertas: list):
    with open(ARCHIVO_ALERTAS, "w", encoding="utf-8") as f:
        json.dump(alertas, f, indent=4, ensure_ascii=False)

def crear_alerta(ticker: str, condicion: str, valor_objetivo: float) -> str:
    """
    Registra una nueva alerta bursátil.
    
    Parámetros:
        ticker (str): Símbolo del activo (ej. TSLA, AAPL).
        condicion (str): 'menor' (precio cae por debajo) o 'mayor' (precio supera).
        valor_objetivo (float): Precio límite para disparar la alerta.
    """
    alertas = _cargar_alertas()
    
    nueva = {
        "id": len(alertas) + 1,
        "ticker": ticker.upper(),
        "condicion": condicion.lower(), # "menor" o "mayor"
        "valor_objetivo": float(valor_objetivo),
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "activa": True
    }
    
    alertas.append(nueva)
    _guardar_alertas(alertas)
    return f"✅ Alerta creada exitosamente [ID: {nueva['id']}]: Avisar si {ticker.upper()} está {condicion} a {valor_objetivo}."

def listar_alertas() -> list:
    """Retorna todas las alertas registradas."""
    return _cargar_alertas()

def evaluar_alertas_activas() -> str:
    """
    Revisa todas las alertas activas contra los precios actuales del mercado
    y avisa si alguna condición se ha cumplido.
    """
    alertas = _cargar_alertas()
    if not alertas:
        return "No hay alertas activas configuradas en el sistema."
        
    reporte = "--- EVALUACIÓN DE ALERTAS PROACTIVAS ---\n"
    disparadas = 0
    
    for alerta in alertas:
        if not alerta["activa"]:
            continue
            
        ticker = alerta["ticker"]
        condicion = alerta["condicion"]
        objetivo = alerta["valor_objetivo"]
        
        try:
            # Obtener precio actual de mercado
            tk = yf.Ticker(ticker)
            hist = tk.history(period="1d")
            if hist.empty:
                continue
            precio_actual = float(hist["Close"].iloc[-1])
            
            condicion_cumplida = False
            if condicion == "menor" and precio_actual <= objetivo:
                condicion_cumplida = True
            elif condicion == "mayor" and precio_actual >= objetivo:
                condicion_cumplida = True
                
            if condicion_cumplida:
                disparadas += 1
                reporte += f"🚨 ¡ALERTA DISPARADA! El activo {ticker} cotiza a {precio_actual:.2f} (Objetivo: {condicion} a {objetivo}).\n"
                alerta["activa"] = False # Desactivar tras cumplirse
            else:
                reporte += f"⏳ Alerta ID {alerta['id']} ({ticker}): Precio actual {precio_actual:.2f} (Aún no se cumple {condicion} a {objetivo}).\n"
        except Exception as e:
            reporte += f"❌ Error evaluando alerta para {ticker}: {str(e)}\n"
            
    _guardar_alertas(alertas)
    if disparadas == 0:
        reporte += "\nNinguna alerta ha alcanzado su valor objetivo en este ciclo."
    return reporte