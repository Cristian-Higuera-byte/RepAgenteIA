# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara fundamentales .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Datos fundamentales (Ticker.info) y estados financieros.

Ambas funciones usan la librería yfinance, cachean el resultado (1 h y 6 h) y
lanzan ValueError con un mensaje claro cuando Yahoo no tiene los datos."""
from __future__ import annotations

from typing import Any

import yfinance as yf  # type: ignore[import-untyped]

from fuentes.yfinance_fuente.cache import _cacheado
from fuentes.yfinance_fuente.constantes import _CAMPOS_NUMERO, _CAMPOS_TEXTO, _ESTADOS
from fuentes.yfinance_fuente.utiles import _num, _simbolo, _sin_nulos


# TITULO FUNDAMENTALES

def fundamentales(simbolo: str) -> dict[str, Any]:
    """Devuelve los datos fundamentales de una empresa (valoración, rentabilidad, deuda, etc.).

    Recibe el símbolo de Yahoo (se normaliza a mayúsculas). Lee `Ticker.info`
    por red, copia los campos de texto y numéricos definidos en `datos.json`
    (omite los vacíos), añade una descripción del negocio recortada a 500
    caracteres y una nota sobre las unidades (fracciones vs. porcentajes).
    Resultado cacheado 1 hora. Lanza ValueError si Yahoo no tiene fundamentales
    (normal en forex, índices y cripto)."""
    s = _simbolo(simbolo)

    def _fn() -> dict[str, Any]:
        """Consulta `Ticker.info` y arma el diccionario de fundamentales; solo se ejecuta si la caché no tiene un valor vigente."""
        info = yf.Ticker(s).info or {}
        # Un info con 0 o 1 claves indica que Yahoo no conoce el símbolo o no tiene fundamentales.
        if len(info) <= 1:
            raise ValueError(
                f"Yahoo no tiene datos fundamentales para '{s}'. Es normal en forex, "
                "índices y cripto; para acciones verifica el símbolo."
            )
        datos: dict[str, Any] = {"simbolo": s}
        # Traduce los nombres de Yahoo a las claves de salida configuradas en datos.json.
        for clave, campo in _CAMPOS_TEXTO.items():
            datos[clave] = info.get(campo)
        for clave, campo in _CAMPOS_NUMERO.items():
            datos[clave] = _num(info.get(campo))
        # La descripción se recorta para no gastar contexto del modelo.
        descripcion = info.get("longBusinessSummary")
        if descripcion:
            datos["descripcion"] = descripcion[:500] + ("..." if len(descripcion) > 500 else "")
        datos["nota"] = (
            "Márgenes, ROE, ROA y crecimientos vienen como fracción (0.25 = 25%). "
            "deuda_sobre_capital viene en porcentaje (150 = 150%)."
        )
        return _sin_nulos(datos)

    return _cacheado(f"fundamentales:{s}", 3600, _fn)


# TITULO ESTADOS FINANCIEROS

def estados_financieros(
    simbolo: str, tipo: str = "resultados", frecuencia: str = "anual", periodos: int = 4
) -> dict[str, Any]:
    """Devuelve filas clave de un estado financiero de la empresa para los últimos periodos.

    Recibe el símbolo, el tipo de estado (clave de `_ESTADOS`, p. ej.
    'resultados'), la frecuencia ('anual' o 'trimestral') y el número de periodos
    (se limita a 1-8). Obtiene el DataFrame correspondiente de yfinance, conserva
    las filas clave del tipo (o las primeras 15 si ninguna existe) y devuelve,
    por cada periodo (el más reciente primero), un diccionario fila -> valor
    redondeado a 2 decimales. Resultado cacheado 6 horas. Lanza ValueError si el
    tipo o la frecuencia no son válidos o si Yahoo no tiene el estado."""
    s = _simbolo(simbolo)
    # Valida los parámetros antes de hacer cualquier consulta de red.
    if tipo not in _ESTADOS:
        raise ValueError(f"Tipo inválido: {tipo!r}. Opciones: {', '.join(_ESTADOS)}")
    if frecuencia not in ("anual", "trimestral"):
        raise ValueError("frecuencia debe ser 'anual' o 'trimestral'.")
    n = max(1, min(int(periodos), 8))
    # Cada tipo define el nombre del atributo de yfinance para la versión anual y la trimestral.
    anual, trimestral, filas = _ESTADOS[tipo]
    atributo = anual if frecuencia == "anual" else trimestral

    def _fn() -> dict[str, Any]:
        """Descarga el estado financiero y lo convierte a una lista de periodos; solo se ejecuta si la caché no tiene un valor vigente."""
        tabla_datos = getattr(yf.Ticker(s), atributo)
        if tabla_datos is None or tabla_datos.empty:
            raise ValueError(
                f"Sin estado de {tipo} ({frecuencia}) para '{s}'. Índices, forex y cripto no tienen estados financieros."
            )
        # Se filtran solo las filas clave presentes; si ninguna existe se toman las 15 primeras.
        presentes = [f for f in filas if f in tabla_datos.index]
        tabla_datos = tabla_datos.loc[presentes] if presentes else tabla_datos.head(15)

        salida = []
        for columna in tabla_datos.columns[:n]:  # Yahoo entrega primero el periodo más reciente
            # Cada columna del DataFrame es una fecha de cierre de periodo.
            fila: dict[str, Any] = {
                "periodo": columna.strftime("%Y-%m-%d") if hasattr(columna, "strftime") else str(columna)
            }
            for elemento, valor in tabla_datos[columna].items():
                fila[str(elemento)] = _num(valor, 2)
            salida.append(fila)
        return {
            "simbolo": s,
            "tipo": tipo,
            "frecuencia": frecuencia,
            "periodos": salida,
            "nota": "Cifras en la moneda de reporte de la empresa.",
        }

    return _cacheado(f"estados:{s}:{tipo}:{frecuencia}:{n}", 6 * 3600, _fn)


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara fundamentales .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
