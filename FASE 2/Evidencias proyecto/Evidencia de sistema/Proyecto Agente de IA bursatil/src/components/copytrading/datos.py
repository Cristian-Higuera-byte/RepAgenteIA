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
from pathlib import Path

from components import _estaticos

# Lista de estrategias (diccionarios) leída de estrategias.json junto a este archivo.
ESTRATEGIAS = _estaticos.datos_json(Path(__file__).parent / "estrategias.json")

# Opciones del filtro de categoría; "Cualquiera" no filtra.
CATEGORIAS = ["Cualquiera", "Forex", "Índices", "Criptomonedas", "Materias primas", "Algorítmico"]
# Pestañas de ordenación del listado (cada una tiene su criterio en ORDEN).
TABS = ["Destacadas", "Mejores resultados", "Ratio de victorias alto", "Fondos propios altos",
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
RIESGO_TXT = {"bajo": "Riesgo bajo", "medio": "Riesgo medio", "alto": "Riesgo alto"}


def por_id(eid):
    """Busca una estrategia por su id.

    Recibe `eid` (identificador de la estrategia) y devuelve su diccionario, o None si
    no existe ninguna con ese id.
    """
    return next((e for e in ESTRATEGIAS if e["id"] == eid), None)


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
