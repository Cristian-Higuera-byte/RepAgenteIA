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

"""Herramientas registradas para el agente de riesgo macro (los esquemas viven en esquemas.json).

Registra ``evaluar_riesgo_noticias_proximas``, una señal basada en titulares
recientes de Investing.com (no un calendario económico).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from database.scripts.fuentes import investing_fuente
from herramientas.base import cargar_json, herramienta
from herramientas.macro_eventos_herramientas.auxiliares import CATEGORIAS, _DIVISAS, _EVENTOS

# Esquemas (descripción y parámetros) de la herramienta, leídos de esquemas.json.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


@herramienta(**_ESQ["evaluar_riesgo_noticias_proximas"])
def evaluar_riesgo_noticias_proximas(
    divisa: str = "ALL",
    cantidad_titulares: int = 20,
) -> dict[str, Any]:
    """Evalúa si hay titulares recientes sobre eventos macro de alto impacto.

    Recibe una divisa (p. ej. "USD"; "ALL" para no filtrar) y cuántos titulares
    pedir por categoría. Consulta las categorías de Investing.com, elimina
    duplicados y conserva los titulares que mencionan un evento de alto impacto
    (y, si se pidió, la divisa). Devuelve el nivel de cautela (PRECAUCIÓN o SIN
    SEÑALES EN TITULARES), hasta 8 titulares y la limitación de la fuente; si
    todas las consultas fallan, devuelve ``disponible: False`` con un mensaje.
    Hace llamadas de red; no inventa eventos.
    """
    # Normaliza la divisa y busca sus palabras clave (None si es "ALL" o desconocida).
    divisa_clean = (divisa or "ALL").strip().upper()
    claves_divisa = _DIVISAS.get(divisa_clean)

    # Descarga los titulares de cada categoría contando las consultas fallidas.
    titulares: list[dict[str, Any]] = []
    fallos = 0
    for categoria in CATEGORIAS:
        try:
            res = investing_fuente.noticias(categoria=categoria, cantidad=cantidad_titulares)
        except Exception:  # noqa: BLE001 - se informa abajo; no se inventa nada
            fallos += 1
            continue
        titulares.extend(res.get("noticias", []))

    # Si todas las categorías fallaron, no hay base para evaluar.
    if fallos == len(CATEGORIAS):
        return {
            "fuente": "Investing.com (titulares)",
            "disponible": False,
            "mensaje": (
                "No se pudieron obtener noticias de Investing.com, así que no se puede evaluar el riesgo "
                "macro. No hay datos de calendario económico."
            ),
        }

    # Filtra titulares únicos que mencionen un evento de alto impacto y, si aplica, la divisa.
    vistos: set[str] = set()
    relevantes: list[dict[str, Any]] = []
    for n in titulares:
        titulo = n.get("titulo", "")
        if not titulo or titulo in vistos:
            continue
        vistos.add(titulo)
        texto = f"{titulo} {n.get('resumen') or ''}".lower()
        if not any(p in texto for p in _EVENTOS):
            continue
        if claves_divisa and not any(p in texto for p in claves_divisa):
            continue
        relevantes.append({k: n.get(k) for k in ("titulo", "fecha", "enlace")})

    # Define el nivel de cautela y el texto de lectura según haya o no titulares relevantes.
    if relevantes:
        nivel = "PRECAUCIÓN"
        lectura = (
            f"{len(relevantes)} titular(es) reciente(s) hablan de eventos macro de alto impacto. Conviene "
            "revisar la hora exacta del evento en un calendario económico antes de abrir operaciones o ajustar stops."
        )
    else:
        nivel = "SIN SEÑALES EN TITULARES"
        lectura = (
            "No se detectaron titulares sobre eventos de alto impacto, pero esto NO garantiza que no haya "
            "eventos próximos: no hay un calendario económico conectado."
        )

    return {
        "fuente": "Investing.com (titulares recientes; no es un calendario económico)",
        "disponible": True,
        "divisa_evaluada": divisa_clean,
        "titulares_revisados": len(vistos),
        "nivel_cautela_macro": nivel,
        "titulares_alto_impacto": relevantes[:8],
        "lectura": lectura,
        "limitacion": "Sin horas exactas ni cifras previstas/anteriores de los eventos.",
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
