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

Este módulo lo importan core (el agente y su cliente LLM), main.py y database/scripts/fuentes/mt5_fuentes
(que lo usan además para cargar el .env antes de leer las variables de MetaTrader 5).
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Carpeta de código (src/) y raíz del proyecto (capstone-2026-002D-equipo11/); en la raíz vive el .env.
SRC = Path(__file__).resolve().parent
RAIZ = SRC.parent
# Carga el archivo .env a las variables de entorno; si no existe, no hace nada.
load_dotenv(RAIZ / ".env")

# ──────────────────────────────────────────────────────────────
# DeepSeek
# ──────────────────────────────────────────────────────────────
# Clave de la API de DeepSeek (vacía si no está definida en el .env).
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
# Dirección base de la API; se puede cambiar desde el .env (por ejemplo, para usar un proxy).
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


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
TIMEOUT_LLM_SEG = 120              # segundos máximos de espera por cada respuesta del modelo
REINTENTOS_LLM = 3                 # reintentos automáticos ante fallos de red o del servicio

# ──────────────────────────────────────────────────────────────
# Rutas
# ──────────────────────────────────────────────────────────────
# Carpeta de datos del proyecto (bases de datos locales y archivos JSON).
DIR_DATOS = RAIZ / "database" / "data"
# Scripts SQL de la base de órdenes (database/sql).
DIR_SQL = RAIZ / "database" / "sql"
# Carpeta de archivos generados (gráficos, etc.).
DIR_SALIDAS = RAIZ / "outputs"
# Carpeta con los prompts del agente (prompts/sistema.md).
DIR_PROMPTS = SRC / "prompts"


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
