# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara configuracion .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
configuracion.py
----------------
Configuración central del agente bursátil.

Todo lo que pueda cambiar (modelos, límites, rutas) vive aquí. Las credenciales se leen del
archivo .env (nunca se escriben en el código).

Variables esperadas en el .env:
    DEEPSEEK_API_KEY=sk-...
    DEEPSEEK_BASE_URL=https://api.deepseek.com   (opcional)

Este módulo lo importan nucleo_agente (el agente y su cliente LLM), consola_agente.py y fuentes/mt5_fuentes
(que lo usan además para cargar el .env antes de leer las variables de MetaTrader 5).
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Carpeta raíz del proyecto (la que contiene este archivo); de ella cuelgan .env, data/ y prompts/.
RAIZ = Path(__file__).resolve().parent
# Carga el archivo .env a las variables de entorno; si no existe, no hace nada.
load_dotenv(RAIZ / ".env")

# ──────────────────────────────────────────────────────────────
# DeepSeek
# ──────────────────────────────────────────────────────────────
# Clave de la API de DeepSeek (vacía si no está definida en el .env).
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
# Dirección base de la API; se puede cambiar desde el .env (por ejemplo, para usar un proxy).
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


# TITULO PERFIL MODELO

@dataclass(frozen=True)
class PerfilModelo:
    """
    Una forma de usar un modelo: qué modelo, con o sin razonamiento, y sus parámetros.

    Es inmutable (frozen) para que ningún módulo cambie por accidente un perfil compartido.
    """

    modelo: str
    thinking: bool                 # True = el modelo razona antes de responder
    esfuerzo: str = "high"         # low | high | max (solo aplica si thinking=True)
    temperatura: float = 0.3       # solo aplica si thinking=False
    max_tokens: int = 16384        # en modo thinking incluye los tokens de razonamiento


# Perfiles disponibles para el agente, por nombre; el usuario elige uno en el chat.
PERFILES: dict[str, PerfilModelo] = {
    # Respuestas cortas y consultas simples: más barato y rápido.
    "rapido": PerfilModelo("deepseek-flash", thinking=False, temperatura=0.3),
    # Perfil estándar del agente: razona y usa herramientas.
    "analisis": PerfilModelo("deepseek-flash", thinking=True, esfuerzo="high"),
    # Análisis más exigentes (informes, cruces de varias fuentes).
    "profundo": PerfilModelo("deepseek-v4-pro", thinking=True, esfuerzo="high"),
}
# Nombre del perfil que se usa cuando el usuario no elige otro.
PERFIL_POR_DEFECTO = "analisis"

# ──────────────────────────────────────────────────────────────
# Comportamiento del agente
# ──────────────────────────────────────────────────────────────
MAX_ITERACIONES_HERRAMIENTAS = 8   # tope de ciclos "llamar herramienta → razonar" por consulta
TIEMPO_ESPERA_LLM_SEGUNDOS = 120              # segundos máximos de espera por cada respuesta del modelo
REINTENTOS_LLM = 3                 # reintentos automáticos ante fallos de red o del servicio

# ──────────────────────────────────────────────────────────────
# Cuota de uso de la IA por plan (ver herramientas/cuota_ia.py)
# ──────────────────────────────────────────────────────────────
# Tokens mensuales de cada plan. Cuentan los tokens de entrada y de salida que informa la API, multiplicados por el peso del modelo
# (más abajo). Una consulta típica gasta del orden de 25.000 tokens (la entrada incluye el prompt, las herramientas y el historial que
# se reenvían en cada llamada): son cifras de partida para ajustar con el consumo real que muestra el Laboratorio.
# `precios` son los precios mensuales (USD) que se muestran en la página de Planes para medir el interés (prueba de demanda): a cada usuario se
# le asigna siempre el mismo, así se comparan las tasas de clic entre precios. Todavía no se cobra nada.
PLANES_IA: dict[str, dict] = {
    "gratis": {"nombre": "Gratis", "tokens_mes": 300_000, "precios": [0]},                         # ≈ 12 consultas: para probar el agente
    "basico": {"nombre": "Básico", "tokens_mes": 3_000_000, "precios": [5, 9, 12]},               # ≈ 120 consultas
    "pro": {"nombre": "Pro", "tokens_mes": 10_000_000, "precios": [12, 19, 29]},                  # ≈ 400 consultas
    "avanzado": {"nombre": "Avanzado", "tokens_mes": 30_000_000, "precios": [29, 49, 69]},        # ≈ 1.200 consultas
}
# Plan de un usuario al que todavía no se le asignó ninguno (modo multiusuario) y plan del modo de un solo usuario (desarrollo: no se te
# limita el agente en tu propio equipo; para probar el límite, cambia el plan en el Laboratorio).
PLAN_POR_DEFECTO = "gratis"
PLAN_MODO_LOCAL = "avanzado"
# Billetera virtual de la plataforma (saldo de prueba sin valor monetario; sirve para pagar planes y queda lista para las cuentas reales).
# moneda: moneda del saldo; bono_inicial: saldo con el que se abre la billetera; recargas: montos que ofrece el botón de recarga;
# recarga_mensual_max: tope de recargas por mes; saldo_maximo: tope del saldo (evita acumular saldo de prueba sin límite).
BILLETERA: dict = {"moneda": "USD", "bono_inicial": 100.0, "recargas": [50, 100, 500, 1000], "recarga_mensual_max": 5000.0, "saldo_maximo": 10000.0}
# Copy trading: requisitos para ser gestor y límites de una estrategia.
# dias_minimos y operaciones_minimas: historial registrado que se pide para publicar; max_estrategias: estrategias vigentes por gestor (las cerradas
# no cuentan); comision_max y comision_defecto: comisión de rendimiento (%) que el gestor cobra a quien copia; inversion_minima: mínimo (USD) para copiar;
# max_copias_por_inversor: copias vigentes por inversor; espera_motor_s: cada cuántos segundos revisa el motor de copia; pendiente_vence_s: segundos tras los
# cuales una copia que quedó a medias (sin confirmar) se da por interrumpida y no se reintenta; liquidacion_dias: cada cuántos días se liquida la comisión de rendimiento.
COPYTRADING: dict = {"dias_minimos": 30, "operaciones_minimas": 20, "max_estrategias": 3, "comision_max": 30.0, "comision_defecto": 20.0, "inversion_minima": 50.0,
                     "categorias": ["Forex", "Índices", "Criptomonedas", "Materias primas", "Metales", "Acciones", "Mixta"],
                     "max_copias_por_inversor": 5, "espera_motor_s": 15, "pendiente_vence_s": 120, "liquidacion_dias": 30}
# Cuánto pesa cada token según el modelo: el modelo «pro» cuesta unas 12 veces más que el «flash», así que gasta 12 veces más cuota.
# Un modelo que no esté en la tabla pesa 1.
PESO_MODELO: dict[str, float] = {"deepseek-flash": 1.0, "deepseek-v4-pro": 12.0}
# Porcentaje de uso desde el cual la barra se pone en ámbar (aviso) y desde el que se pone en rojo.
UMBRAL_AVISO_PCT = 70
UMBRAL_CRITICO_PCT = 90

# ──────────────────────────────────────────────────────────────
# Rutas
# ──────────────────────────────────────────────────────────────
# Carpeta de datos del proyecto (bases de datos locales y archivos JSON).
DIR_DATOS = RAIZ / "data"
# Carpeta con los prompts del agente (prompts/sistema.md).
DIR_PROMPTS = RAIZ / "prompts"


# TITULO VALIDAR CONFIGURACION

def validar_configuracion() -> None:
    """
    Falla temprano y con un mensaje claro si falta algo imprescindible.

    Hoy solo exige la clave de la API de DeepSeek: si no está definida, lanza un RuntimeError que indica
    dónde se busca el archivo .env. La llama el cliente LLM al crearse, antes de hacer la primera petición.
    """
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "Falta DEEPSEEK_API_KEY. Defínela en el archivo .env "
            f"(se busca en: {RAIZ / '.env'})."
        )


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara configuracion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
