"""Paquete de herramientas del agente.

Cada módulo nuevo de herramientas (mt5, yfinance, investing, conocimiento...)
se importa aquí para que sus funciones queden registradas al arrancar el agente.
"""

from importlib import import_module
from types import ModuleType

utilidades: ModuleType = import_module(".utilidades", __name__)
yfinance_tools: ModuleType = import_module(".yfinance_tools", __name__)
investing_tools: ModuleType = import_module(".investing_tools", __name__)
mt5_tools: ModuleType = import_module(".mt5_tools", __name__)
conocimiento: ModuleType = import_module(".conocimiento", __name__)

__all__ = [
    "utilidades",
    "yfinance_tools",
    "investing_tools",
    "mt5_tools",
    "conocimiento",
]