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
# PREGUNTAS SEMANALES al agente de cada plan: la cuota se reinicia cada semana (ver REINICIO_SEMANAL). Cuenta cada pregunta del usuario que el agente alcanza a
# responder, sin importar su largo ni el perfil usado; los análisis de las vigilancias automáticas no cuentan (su límite es el de vigilancias_activas del plan).
# Los valores los definió el equipo de la empresa (Patricio): 6, 12, 18 y 24 preguntas por semana.
# `precios` son los precios mensuales (USD) de la página de Planes y de la portada. Con un solo precio por plan ya no hay prueba de precios A/B
# (si se agregan más precios a un plan, a cada usuario se le asigna siempre el mismo y se comparan los clics, como antes).
PLANES_IA: dict[str, dict] = {
    "gratis": {"nombre": "Gratis", "preguntas_semana": 6, "precios": [0]},
    "basico": {"nombre": "Básico", "preguntas_semana": 12, "precios": [4.99]},
    "pro": {"nombre": "Profesional", "preguntas_semana": 18, "precios": [14.99]},
    "avanzado": {"nombre": "Avanzado", "preguntas_semana": 24, "precios": [29.99]},
}
# Cuándo se reinicia la cuota de preguntas: cada semana, el día `dia` (0 = lunes … 6 = domingo) a la hora indicada, en la zona horaria `zona` (con
# cambio de horario incluido). El domingo por la tarde queda justo antes de la apertura semanal del mercado de divisas. Si la zona no está disponible
# (en Windows hace falta el paquete tzdata), se usa la hora local del servidor.
REINICIO_SEMANAL = {"zona": "America/Santiago", "dia": 6, "hora": 18, "minuto": 0}
# Plan de un usuario al que todavía no se le asignó ninguno (modo multiusuario) y plan del modo de un solo usuario (desarrollo: no se te
# limita el agente en tu propio equipo; para probar el límite, cambia el plan en el Laboratorio).
PLAN_POR_DEFECTO = "gratis"
PLAN_MODO_LOCAL = "avanzado"
# Cambio de plan SIN pago. False (lanzamiento): solo el plan Gratis se activa solo; los planes de pago esperan la pasarela de pago (Flow) y, mientras tanto, el botón
# «Contratar» solo deja registrado el interés del usuario. True (PLANES_LIBRES=true en el .env): cualquiera puede pasar a cualquier plan sin pagar, para probar cuotas
# y funciones en desarrollo (con el saldo virtual de la Billetera y el selector de plan del Laboratorio).
PLANES_LIBRES: bool = os.getenv("PLANES_LIBRES", "").strip().lower() in ("1", "true", "si", "sí", "yes")
# Correos de los administradores (root), separados por comas, en la variable ROOT_CORREOS del .env. Los root ven las secciones internas (hoy, el Laboratorio). El rol también
# puede darse en la base de datos (columna `rol` de `usuarios`, herramientas/sql/roles.sql); ver herramientas/roles.py.
ROOT_CORREOS: frozenset = frozenset(c.strip().lower() for c in os.getenv("ROOT_CORREOS", "").split(",") if c.strip())
# reCAPTCHA de Google en los formularios públicos y sensibles (herramientas/recaptcha.py). v3 puntúa en silencio cada envío y v2 (el casillero «No soy un robot») se pide solo si el
# puntaje es bajo. Las claves se crean en google.com/recaptcha/admin (una para v3 y otra para v2 casillero, con los dominios de la plataforma) y se ponen en el .env: la clave del
# sitio es pública y la secreta no debe salir del servidor. Con las cuatro puestas la protección se exige; sin ellas queda apagada (desarrollo).
RECAPTCHA_V3_SITIO: str = os.getenv("RECAPTCHA_V3_SITIO", "").strip()
RECAPTCHA_V3_SECRETA: str = os.getenv("RECAPTCHA_V3_SECRETA", "").strip()
RECAPTCHA_V2_SITIO: str = os.getenv("RECAPTCHA_V2_SITIO", "").strip()
RECAPTCHA_V2_SECRETA: str = os.getenv("RECAPTCHA_V2_SECRETA", "").strip()
# Puntaje mínimo de v3 (0 a 1) para aceptar un envío sin pedir el casillero de v2. Google recomienda 0.5 como punto de partida.
RECAPTCHA_UMBRAL: float = float(os.getenv("RECAPTCHA_UMBRAL", "0.5") or 0.5)
RECAPTCHA_ACTIVO: bool = all((RECAPTCHA_V3_SITIO, RECAPTCHA_V3_SECRETA, RECAPTCHA_V2_SITIO, RECAPTCHA_V2_SECRETA))
# Cómo se combinan v3 y v2. «ambos» (por defecto): cada formulario muestra siempre el casillero «No soy un robot» (v2) y además se exige un puntaje bueno de v3 (invisible); hacen
# falta las dos comprobaciones. «respaldo»: v3 decide en silencio y el casillero de v2 solo aparece si el puntaje es bajo. Se cambia con RECAPTCHA_MODO en el .env.
RECAPTCHA_MODO: str = os.getenv("RECAPTCHA_MODO", "ambos").strip().lower() or "ambos"
# Billetera virtual de la plataforma (saldo de prueba sin valor monetario; sirve para pagar planes y queda lista para las cuentas reales).
# moneda: moneda del saldo; bono_inicial: saldo con el que se abre la billetera; recargas: montos que ofrece el botón de recarga;
# recarga_mensual_max: tope de recargas por mes; saldo_maximo: tope del saldo (evita acumular saldo de prueba sin límite).
BILLETERA: dict = {"moneda": "USD", "bono_inicial": 0.0, "recargas": [50, 100, 500, 1000], "recarga_mensual_max": 5000.0, "saldo_maximo": 10000.0}
# Cuenta real: DESHABILITADA por defecto. Mientras sea False no se puede abrir NINGUNA operación en la cuenta real de Capital.com, por ningún camino (gráfico, ticket, agente, copy trading):
# la política de apertura (herramientas/politica_apertura.py) lo rechaza y el agente y el copy trading solo operan en cuenta demo. Se habilita a propósito con OPERAR_EN_CUENTA_REAL=true en el
# .env del servidor, cuando las protecciones de la auditoría de seguridad estén probadas y la revisión legal lo permita. Cerrar posiciones y cancelar órdenes siguen disponibles.
OPERAR_EN_CUENTA_REAL: bool = os.getenv("OPERAR_EN_CUENTA_REAL", "false").strip().lower() in ("1", "true", "si", "sí")
# Copy trading: requisitos para ser gestor y límites de una estrategia.
# dias_minimos y operaciones_minimas: historial registrado que se pide para publicar; max_estrategias: estrategias vigentes por gestor (las cerradas
# no cuentan); comision_max y comision_defecto: comisión de rendimiento (%) que el gestor cobra a quien copia; inversion_minima: mínimo (USD) para copiar;
# max_copias_por_inversor: copias vigentes por inversor; espera_motor_s: cada cuántos segundos revisa el motor de copia; pendiente_vence_s: segundos tras los
# cuales una copia que quedó a medias (sin confirmar) se da por interrumpida y no se reintenta; liquidacion_dias: cada cuántos días se liquida la comisión de rendimiento.
COPYTRADING: dict = {"dias_minimos": 30, "operaciones_minimas": 20, "max_estrategias": 3, "comision_max": 30.0, "comision_defecto": 20.0, "inversion_minima": 50.0,
                     "categorias": ["Forex", "Índices", "Criptomonedas", "Materias primas", "Metales", "Acciones", "Mixta"],
                     "max_copias_por_inversor": 5, "espera_motor_s": 15, "pendiente_vence_s": 120, "liquidacion_dias": 30}
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
