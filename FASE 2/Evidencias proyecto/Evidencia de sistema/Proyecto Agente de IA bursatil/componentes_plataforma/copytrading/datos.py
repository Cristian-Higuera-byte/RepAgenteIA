# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara datos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Datos SIMULADOS de copy trading: las estrategias están en estrategias.json (editable sin tocar código).

Define también las constantes de la vista: categorías del filtro, pestañas de orden, la
función de ordenación de cada pestaña y los textos/clases CSS del nivel de riesgo.
"""
import threading
import time
from pathlib import Path

from componentes_plataforma import _estaticos
from herramientas import gestor_autenticacion, metricas_estrategia

# Estrategias de ejemplo (diccionarios) leídas de estrategias.json junto a este archivo; se muestran solo si todavía no hay estrategias reales publicadas.
ESTRATEGIAS = _estaticos.datos_json(Path(__file__).parent / "estrategias.json")
# Segundos que se recuerda la lista de estrategias reales antes de volver a consultarla, y su caché: (hora de la consulta, lista)
_VIDA_LISTA_S = 30.0
_CACHE_LISTA: list = [0.0, []]
_CANDADO = threading.Lock()

# Opciones del filtro de categoría; "Cualquiera" no filtra.
CATEGORIAS = ["Cualquiera", "Forex", "Índices", "Criptomonedas", "Materias primas", "Algorítmico"]
# Pestañas de ordenación del listado (cada una tiene su criterio en ORDEN).
PESTANAS = ["Destacadas", "Mejores resultados", "Ratio de victorias alto", "Fondos propios altos",
        "Riesgo bajo", "Drawdown bajo", "Comisiones bajas", "Más populares"]
# Clave de ordenación (para sorted) por pestaña; el signo menos invierte para ordenar de mayor a menor.
ORDEN = {
    "Destacadas": lambda e: -e["rent"],
    "Mejores resultados": lambda e: -e["rent"],
    "Ratio de victorias alto": lambda e: -e["win"],
    "Fondos propios altos": lambda e: -e["fondos"],
    "Riesgo bajo": lambda e: {"bajo": 0, "medio": 1, "alto": 2}[e["riesgo"]],
    "Drawdown bajo": lambda e: e["drawdown"],
    "Comisiones bajas": lambda e: e["comision"],
    "Más populares": lambda e: -e["inversores"],
}
# Clase CSS de la insignia de riesgo (ver estilos.css: rb, rm, ra).
RIESGO_CLS = {"bajo": "rb", "medio": "rm", "alto": "ra"}
# Texto visible de la insignia según el nivel de riesgo.
RIESGO_TEXTO = {"bajo": "Riesgo bajo", "medio": "Riesgo medio", "alto": "Riesgo alto"}


# TITULO ESTRATEGIAS DISPONIBLES

def estrategias() -> tuple:
    """Devuelve (lista de estrategias, es_ejemplo).

    Si hay estrategias reales publicadas en Supabase (`metricas_estrategia.listar_publicadas`), devuelve esas con `es_ejemplo` en False; la consulta se
    recuerda 30 segundos. Si no hay ninguna, o no hay Supabase, devuelve las de ejemplo de estrategias.json con `es_ejemplo` en True."""
    cliente = gestor_autenticacion._supabase
    if cliente is not None:
        with _CANDADO:
            if time.time() - _CACHE_LISTA[0] >= _VIDA_LISTA_S:
                _CACHE_LISTA[0], _CACHE_LISTA[1] = time.time(), metricas_estrategia.listar_publicadas(cliente)
            reales = list(_CACHE_LISTA[1])
        if reales:
            return reales, False
    return ESTRATEGIAS, True


# TITULO POR ID

def por_id(eid):
    """Busca una estrategia por su id entre las que muestra la vista (reales o de ejemplo).

    Recibe `eid` (identificador de la estrategia) y devuelve su diccionario, o None si
    no existe ninguna con ese id.
    """
    return next((e for e in estrategias()[0] if e["id"] == eid), None)


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara datos .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
