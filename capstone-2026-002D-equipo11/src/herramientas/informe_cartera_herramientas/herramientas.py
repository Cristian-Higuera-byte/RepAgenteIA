# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara herramientas .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Herramientas registradas para el agente de informe de cartera (los esquemas viven en esquemas.json).

Registra ``informe_cartera``, que combina en una sola llamada exposición,
riesgo, volatilidad, correlaciones, noticias, escenarios y alertas de las
posiciones abiertas en MetaTrader 5.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from database.scripts.fuentes import mt5_fuentes as mt5_fuente
from herramientas import analisis_herramientas
from herramientas.base import cargar_json, herramienta
from herramientas.informe_cartera_herramientas.auxiliares import (
    _alertas,
    _correlaciones,
    _escenarios,
    _exposicion,
    _noticias,
    _volatilidad,
)

# Esquemas (descripción y parámetros) de las herramientas de este paquete, leídos de esquemas.json.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


@herramienta(**_ESQ["informe_cartera"])
def informe_cartera() -> dict[str, Any]:
    """Genera el informe integral de la cartera abierta.

    No recibe parámetros. Consulta a MT5 la cuenta y las posiciones; si no hay
    posiciones devuelve solo la cuenta y un mensaje. Si las hay, calcula por
    separado riesgo, exposición, volatilidad, correlaciones, noticias,
    escenarios y alertas; una sección que falle se registra en
    ``secciones_no_disponibles`` (con un mensaje truncado) y el resto sigue siendo válido.
    Devuelve un diccionario con el resumen de cuenta y todas las secciones.
    """
    # Lee la cuenta y las posiciones abiertas desde MT5.
    cuenta = mt5_fuente.cuenta()
    posiciones = mt5_fuente.posiciones().get("posiciones", [])
    equidad = cuenta.get("equidad") or 0.0
    if not posiciones:
        return {
            "fuente": "MetaTrader 5",
            "total_posiciones": 0,
            "cuenta": cuenta,
            "mensaje": "No hay posiciones abiertas: no hay exposición ni riesgo en la cartera.",
        }

    # Registro de secciones que fallaron: nombre -> mensaje de error.
    fallos: dict[str, str] = {}

    def seccion(nombre: str, fn: Any, defecto: Any) -> Any:
        """Ejecuta ``fn`` y devuelve su resultado; si falla, anota el error en ``fallos`` y devuelve ``defecto``."""
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - una sección caída no invalida las demás
            fallos[nombre] = str(e)[:160]
            return defecto

    # Calcula cada sección de forma independiente (el orden importa: escenarios y alertas usan las anteriores).
    riesgo = seccion("riesgo", analisis_herramientas.analizar_riesgo_posicion, {})
    expo = seccion("exposicion", lambda: _exposicion(posiciones, equidad), {})
    vol = seccion("volatilidad", lambda: _volatilidad(sorted({p["simbolo"] for p in posiciones})), {})
    corr = seccion("correlaciones", lambda: _correlaciones(posiciones), {})
    noticias = seccion("noticias", lambda: _noticias(posiciones), {})
    esc = seccion("escenarios", lambda: _escenarios(posiciones, vol, riesgo, equidad), {})
    alertas = seccion("alertas", lambda: _alertas(cuenta, riesgo, expo, corr, noticias), [])
    # Quita el dato interno de la exposición antes de devolverlo al modelo.
    expo.pop("_mayor_divisa", None)

    # Ensambla la respuesta final con solo los campos útiles de cuenta y riesgo.
    return {
        "fuente": "MetaTrader 5 + Investing.com (titulares)",
        "total_posiciones": len(posiciones),
        "cuenta": {k: cuenta.get(k) for k in ("tipo", "moneda", "balance", "equidad", "beneficio_flotante",
                                              "margen_usado", "margen_libre", "nivel_margen_pct")},
        "alertas": alertas,
        "exposicion": expo,
        "riesgo": {k: riesgo.get(k) for k in ("riesgo_total_acumulado_usd", "riesgo_total_equidad_pct",
                                              "posiciones_sin_stop_loss", "aviso", "posiciones")},
        "volatilidad": vol,
        "correlaciones": corr,
        "noticias": noticias,
        "escenarios": esc,
        "secciones_no_disponibles": fallos,
    }


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara herramientas .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
