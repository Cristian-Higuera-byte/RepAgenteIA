"""
agent.py
---------
Define las 'herramientas' (tools) que el agente de IA podrá invocar
mediante tool calling.
"""
from tools.alertas_manager import crear_alerta, evaluar_alertas_activas
from tools.analysis import (
    calcular_macd,
    calcular_rsi,
    calcular_soportes_resistencias,
    comparar_multi_activos,
    screening_rapido_mercado,
)
from tools.archivos import listar_archivos
from tools.viz_manager import generar_grafico_rendimiento, generar_grafico_barras_comparativo, generar_grafico_predictivo
from tools.data_fetcher import (
    obtener_indicadores_macro,
    obtener_datos_historicos,
    obtener_info_general,
    obtener_noticias_activo,
)
from tools.memoria import limpiar_memoria
from tools.rag_manager import consultar_rag


def resumen_basico(datos):
    """Construye un resumen técnico a partir de datos históricos."""
    cierre = datos["Close"]
    return {
        "precio_actual": float(cierre.iloc[-1]),
        "sma20": float(cierre.tail(20).mean()),
        "sma50": float(cierre.tail(50).mean()),
        "volatilidad": float(cierre.pct_change().std() * (252 ** 0.5)),
    }


def comparar_precio_historico(ticker, fecha):
    datos = obtener_datos_historicos(ticker, periodo="max")
    cierre = datos["Close"]
    historico = cierre.loc[:fecha].iloc[-1]
    return {"ticker": ticker, "fecha": fecha, "precio_historico": float(historico),
            "precio_actual": float(cierre.iloc[-1]),
            "variacion_porcentual": float((cierre.iloc[-1] / historico - 1) * 100)}


def calcular_rendimiento_periodo(ticker, fecha_inicio, fecha_fin):
    datos = obtener_datos_historicos(ticker, periodo="max")["Close"]
    inicio = datos.loc[:fecha_inicio].iloc[-1]
    fin = datos.loc[:fecha_fin].iloc[-1]
    return {"ticker": ticker, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
            "rendimiento_porcentual": float((fin / inicio - 1) * 100)}


def obtener_volatilidad(ticker, periodo="6mo", ventana=20):
    cierre = obtener_datos_historicos(ticker, periodo)["Close"]
    retornos = cierre.pct_change().dropna().tail(ventana)
    return {"ticker": ticker, "periodo": periodo, "ventana": ventana,
            "volatilidad_anualizada": float(retornos.std() * (252 ** 0.5))}

HERRAMIENTAS = [
    {
        "type": "function",
        "function": {
            "name": "obtener_resumen_activo",
            "description": "Obtiene un resumen técnico rápido (precio actual, SMA20, SMA50 y volatilidad) de un activo bursátil.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil, ej. AAPL, TSLA, SQM.SN"},
                    "periodo": {"type": "string", "description": "Rango de datos: 1mo, 3mo, 6mo, 1y", "default": "6mo"}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_info_empresa",
            "description": "Obtiene información fundamental de la empresa (sector, industria, PER, capitalización de mercado, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil, ej. MSFT, GOOGL"}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comparar_precio_historico",
            "description": "Compara el precio actual de un activo con su precio en una fecha pasada específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil"},
                    "fecha": {"type": "string", "description": "Fecha en formato YYYY-MM-DD"},
                },
                "required": ["ticker", "fecha"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_rendimiento_periodo",
            "description": "Calcula el rendimiento porcentual de un activo entre dos fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil"},
                    "fecha_inicio": {"type": "string", "description": "Fecha de inicio YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha de fin YYYY-MM-DD"},
                },
                "required": ["ticker", "fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_volatilidad",
            "description": "Calcula la volatilidad histórica anualizada de un activo bursátil en un período y ventana específicos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil, ej. AAPL, NVDA, SQM.SN"},
                    "periodo": {"type": "string", "description": "Rango de datos a consultar: 1mo, 3mo, 6mo, 1y, 5y", "default": "6mo"},
                    "ventana": {"type": "integer", "description": "Número de días recientes a usar en el cálculo (por defecto 20)", "default": 20},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_archivos",
            "description": "Lista los archivos y carpetas de un directorio dado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directorio": {"type": "string", "description": "Ruta del directorio. Por defecto, el actual."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "limpiar_memoria",
            "description": "Limpia y borra todo el historial local de consultas guardadas.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_rsi",
            "description": "Calcula el Índice de Fuerza Relativa (RSI) actual de un activo para evaluar sobrecompra o sobreventa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil, ej. AAPL, TSLA"},
                    "periodo": {"type": "string", "description": "Rango de datos a consultar: 1mo, 3mo, 6mo, 1y", "default": "6mo"}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_macd",
            "description": "Calcula el indicador MACD y su línea de señal para identificar cambios de tendencia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil, ej. MSFT, NVDA"},
                    "periodo": {"type": "string", "description": "Rango de datos a consultar: 6mo, 1y", "default": "6mo"}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_soportes_resistencias",
            "description": "Identifica niveles clave de soporte y resistencia recientes basados en máximos y mínimos locales.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil, ej. AAPL, SQM.SN"},
                    "ventana": {"type": "integer", "description": "Días a evaluar para soporte y resistencia (por defecto 20)", "default": 20}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_rag",
            "description": "Busca información en la base de conocimiento interna y documentos corporativos de la empresa mediante recuperación semántica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pregunta": {"type": "string", "description": "Consulta o tema específico a buscar en los documentos internos."}
                },
                "required": ["pregunta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_noticias_activo",
            "description": "Obtiene las noticias y titulares bursátiles recientes de un activo para evaluar eventos corporativos o macroeconómicos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil del activo, ej. AAPL, NVDA, TSLA"},
                    "limite": {"type": "integer", "description": "Número máximo de noticias a recuperar (por defecto 5)", "default": 5}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_indicadores_macro",
            "description": "Consulta indicadores macroeconómicos globales clave (tasas de interés de referencia con bonos, oro e inflación, y energía/petróleo).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_alerta",
            "description": "Configura una regla de monitoreo proactivo para avisar si un activo cruza un precio objetivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil, ej. TSLA, AAPL"},
                    "condicion": {"type": "string", "description": "Condición de disparo: 'menor' o 'mayor'"},
                    "valor_objetivo": {"type": "number", "description": "Precio límite numérico de la alerta"}
                },
                "required": ["ticker", "condicion", "valor_objetivo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluar_alertas_activas",
            "description": "Revisa el estado actual del mercado frente a todas las alertas configuradas para ver si alguna se ha cumplido.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comparar_multi_activos",
            "description": "Compara simultáneamente el rendimiento porcentual y precios de una lista de activos en un período específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de símbolos bursátiles a comparar, ej. ['TSLA', 'AAPL', 'MSFT']"
                    },
                    "periodo": {"type": "string", "description": "Período de comparación (ej. '1mo', '3mo', '1y')", "default": "1mo"}
                },
                "required": ["tickers"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "screening_rapido_mercado",
            "description": "Ejecuta un screening o barrido automatizado sobre una lista de activos para evaluar tendencias mensuales.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de tickers para el screening."
                    }
                },
                "required": ["tickers"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generar_grafico_rendimiento",
            "description": "Genera un gráfico visual de la evolución del precio de un activo bursátil y lo guarda como imagen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil, ej. TSLA, AAPL, MSFT"},
                    "periodo": {"type": "string", "description": "Período del gráfico: '1mo', '3mo', '6mo', '1y'", "default": "6mo"}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generar_grafico_barras_comparativo",
            "description": "Genera un gráfico visual de barras comparando el rendimiento porcentual de múltiples activos en un período de tiempo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de símbolos bursátiles a comparar, ej. ['TSLA', 'AAPL', 'MSFT', 'NVDA']"
                    },
                    "periodo": {"type": "string", "description": "Período de comparación: '1mo', '3mo', '6mo', '1y'", "default": "1mo"}
                },
                "required": ["tickers"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generar_grafico_predictivo",
            "description": "Genera una estimación y gráfico predictivo de precios futuros basado en modelos de tendencia histórica para un activo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo bursátil, ej. TSLA, AAPL, MSFT"},
                    "periodo": {"type": "string", "description": "Período histórico base de análisis: '3mo', '6mo', '1y'", "default": "6mo"},
                    "dias_futuros": {"type": "integer", "description": "Cantidad de días a proyectar en el futuro (ej. 30)", "default": 30}
                },
                "required": ["ticker"],
            },
        },
    },
]

NOMBRES_VALIDOS = {
    "obtener_resumen_activo",
    "obtener_info_empresa",
    "comparar_precio_historico",
    "calcular_rendimiento_periodo",
    "obtener_volatilidad",
    "listar_archivos",
    "lista_archivos",
    "limpiar_memoria",
    "calcular_rsi",
    "calcular_macd",
    "calcular_soportes_resistencias",
    "consultar_rag",
    "obtener_noticias_activo",
    "obtener_indicadores_macro",
    "crear_alerta",
    "evaluar_alertas_activas",
    "evalua_alertas_activas",
    "comparar_multi_activos",
    "compara_multi_activos",
    "screening_rapido_mercado",
    "commentary",
    "generar_grafico_rendimiento",
    "generar_grafico_barras_comparativo",
    "graficar_rendimiento",
    "graficar_barras_comparativo",
    "graficar_barras",
    "arguments",
    "generar_grafico_predictivo",
    "graficar_predictivo",
    "genera_grafico_prediccion",
}

def ejecutar_herramienta(nombre_funcion: str, argumentos: dict):
    if nombre_funcion == "obtener_resumen_activo":
        datos = obtener_datos_historicos(argumentos["ticker"], argumentos.get("periodo", "6mo"))
        return resumen_basico(datos)
    elif nombre_funcion == "obtener_info_empresa":
        return obtener_info_general(argumentos["ticker"])
    elif nombre_funcion == "comparar_precio_historico":
        return comparar_precio_historico(argumentos["ticker"], argumentos["fecha"])
    elif nombre_funcion == "calcular_rendimiento_periodo":
        return calcular_rendimiento_periodo(
            argumentos["ticker"], argumentos["fecha_inicio"], argumentos["fecha_fin"]
        )
    elif nombre_funcion == "obtener_volatilidad":
        return obtener_volatilidad(
            argumentos["ticker"],
            argumentos.get("periodo", "6mo"),
            argumentos.get("ventana", 20),
        )
    elif nombre_funcion == "listar_archivos":
        return listar_archivos(argumentos.get("directorio", "."))
    elif nombre_funcion == "limpiar_memoria":
        return limpiar_memoria()
    elif nombre_funcion == "calcular_rsi":
        datos = obtener_datos_historicos(argumentos["ticker"], argumentos.get("periodo", "6mo"))
        return {"ticker": argumentos["ticker"], "rsi": calcular_rsi(datos)}
    elif nombre_funcion == "calcular_macd":
        datos = obtener_datos_historicos(argumentos["ticker"], argumentos.get("periodo", "6mo"))
        resultado_macd = calcular_macd(datos)
        return {"ticker": argumentos["ticker"], **resultado_macd}
    elif nombre_funcion == "calcular_soportes_resistencias":
        datos = obtener_datos_historicos(argumentos["ticker"], periodo="3mo")
        return {"ticker": argumentos["ticker"], **calcular_soportes_resistencias(datos, argumentos.get("ventana", 20))}
    elif nombre_funcion == "consultar_rag":
        return {"contexto_documental": consultar_rag(argumentos["pregunta"])}
    elif nombre_funcion == "obtener_noticias_activo":
        noticias = obtener_noticias_activo(argumentos["ticker"], argumentos.get("limite", 5))
        return {"ticker": argumentos["ticker"], "noticias": noticias}
    elif nombre_funcion == "obtener_indicadores_macro":
        return {"indicadores_macro": obtener_indicadores_macro()}
    elif nombre_funcion == "crear_alerta":
        return {"resultado": crear_alerta(argumentos["ticker"], argumentos["condicion"], argumentos["valor_objetivo"])}
    elif nombre_funcion in ["evaluar_alertas_activas", "evalua_alertas_activas"]:
        return {"resultado": evaluar_alertas_activas()}
    elif nombre_funcion == "comparar_multi_activos":
        return {"resultado": comparar_multi_activos(argumentos["tickers"], argumentos.get("periodo", "1mo"))}
    elif nombre_funcion == "screening_rapido_mercado":
        return {"resultado": screening_rapido_mercado(argumentos["tickers"])}
    elif nombre_funcion == "commentary":
        # El LLm quiso hacer un comentario/resumen del activo solicitado
        ticker = argumentos.get("ticker", "AAPL")
        return {"resumen_activo": obtener_info_general(ticker)}
    elif nombre_funcion == "generar_grafico_rendimiento":
        return {"resultado": generar_grafico_rendimiento(argumentos["ticker"], argumentos.get("periodo", "6mo"))}
    elif nombre_funcion == "generar_grafico_barras_comparativo":
        return {"resultado": generar_grafico_barras_comparativo(argumentos["tickers"], argumentos.get("periodo", "1mo"))}
    elif nombre_funcion == "generar_grafico_predictivo":
        return {"resultado": generar_grafico_predictivo(argumentos["ticker"], argumentos.get("periodo", "6mo"), argumentos.get("dias_futuros", 30))}
    else:
        raise ValueError(
            f"Herramienta '{nombre_funcion}' no reconocida. "
            f"Herramientas disponibles: {', '.join(sorted(NOMBRES_VALIDOS))}"
        )