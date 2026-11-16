# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara noticias .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Noticias de un símbolo y consenso de analistas.

Ambas funciones consultan yfinance, cachean el resultado (5 min y 1 h) y son
tolerantes a los cambios de formato de Yahoo."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yfinance as yf  # type: ignore[import-untyped]

from fuentes.yfinance_fuente.cache import _cacheado
from fuentes.yfinance_fuente.utiles import _entero, _num, _simbolo, _sin_nulos


# TITULO NORMALIZAR NOTICIA

# ──────────────────────────────────────────────────────────────
# Noticias
# ──────────────────────────────────────────────────────────────
def _normalizar_noticia(elemento: dict[str, Any] | None) -> dict[str, Any] | None:
    """Yahoo ha cambiado el formato de las noticias; aquí se soportan el nuevo y el antiguo.

    Recibe un ítem crudo de noticia. Devuelve un diccionario con título,
    resumen (recortado a 300 caracteres), fuente, fecha y url (se omiten los
    campos ausentes), o None si el ítem no es un diccionario o no tiene título.
    En el formato nuevo los datos están dentro de la clave 'content'; en el
    antiguo, en el nivel superior."""
    if not isinstance(elemento, dict):
        return None

    # Formato nuevo: los datos viven en item['content']; formato antiguo: en el propio item.
    c = elemento.get("content") if isinstance(elemento.get("content"), dict) else elemento
    if not isinstance(c, dict):
        return None

    titulo = c.get("title")
    if not titulo:
        return None

    # Nombre del medio: 'provider.displayName' (nuevo) o 'publisher' (antiguo).
    proveedor = c.get("provider")
    fuente = proveedor.get("displayName") if isinstance(proveedor, dict) else c.get("publisher")

    # Fecha: texto ISO (nuevo) o timestamp en segundos (antiguo), convertido a ISO en UTC.
    fecha = c.get("pubDate") or c.get("displayTime")
    provider_publish_tiempo = c.get("providerPublishTime")
    if not fecha and isinstance(provider_publish_tiempo, (int, float)):
        fecha = datetime.fromtimestamp(provider_publish_tiempo, tz=timezone.utc).isoformat(timespec="seconds")

    # Enlace: primero los objetos de URL del formato nuevo, luego el campo 'link' del antiguo.
    url = None
    for clave in ("canonicalUrl", "clickThroughUrl"):
        v = c.get(clave)
        if isinstance(v, dict) and v.get("url"):
            url = v["url"]
            break
    url = url or c.get("link")

    # El resumen se recorta para ahorrar contexto del modelo.
    resumen = c.get("summary") or c.get("description")
    if isinstance(resumen, str) and len(resumen) > 300:
        resumen = resumen[:300] + "..."

    return _sin_nulos({"titulo": titulo, "resumen": resumen, "fuente": fuente, "fecha": fecha, "url": url})


# TITULO NOTICIAS

def noticias(simbolo: str, cantidad: int = 8) -> list[dict[str, Any]]:
    """Devuelve las últimas noticias de Yahoo Finance asociadas a un símbolo.

    Recibe el símbolo y la cantidad (se limita a 1-20). Usa `get_news` de
    yfinance (o el atributo `news` en versiones antiguas), normaliza cada ítem
    con `_normalizar_noticia` y descarta los inválidos. Devuelve una lista de
    diccionarios. Resultado cacheado 5 minutos."""
    s = _simbolo(simbolo)
    n = max(1, min(int(cantidad), 20))

    def _fn() -> list[dict[str, Any]]:
        """Descarga y normaliza las noticias; solo se ejecuta si la caché no tiene un valor vigente."""
        ticker = yf.Ticker(s)
        try:
            crudo = ticker.get_news(count=n)
        except (AttributeError, TypeError):  # versiones antiguas de yfinance
            crudo = ticker.news
        # Generador perezoso: normaliza y luego filtra los ítems que quedaron en None.
        normalizadas = (_normalizar_noticia(i) for i in (crudo or []))
        return [x for x in normalizadas if x][:n]

    return _cacheado(f"noticias:{s}:{n}", 300, _fn)


# TITULO CONSENSO ANALISTAS

# ──────────────────────────────────────────────────────────────
# Consenso de analistas
# ──────────────────────────────────────────────────────────────
def consenso_analistas(simbolo: str) -> dict[str, Any]:
    """Devuelve el consenso de analistas: precios objetivo y conteo de recomendaciones.

    Recibe el símbolo. Lee `analyst_price_targets` y `recommendations_summary`
    de yfinance (cada bloque se intenta de forma independiente y los errores se
    ignoran). Devuelve precios objetivo, las dos filas más recientes de
    recomendaciones y una nota sobre los periodos. Resultado cacheado 1 hora.
    Lanza ValueError si no hay ningún dato (solo existen para acciones y algunos ETF)."""
    s = _simbolo(simbolo)

    def _fn() -> dict[str, Any]:
        """Consulta los dos bloques de datos de analistas; solo se ejecuta si la caché no tiene un valor vigente."""
        ticker = yf.Ticker(s)
        resultado: dict[str, Any] = {"simbolo": s}

        # Bloque 1: precios objetivo (actual, mínimo, máximo, media...). Si falla, se omite.
        try:
            objetivos = ticker.analyst_price_targets
            if objetivos:
                resultado["precio_objetivo"] = {k: _num(v) for k, v in objetivos.items()}
        except Exception:  # noqa: BLE001
            pass

        # Bloque 2: conteo de recomendaciones por periodo; solo los dos más recientes.
        try:
            tabla_datos = ticker.recommendations_summary
            if tabla_datos is not None and not tabla_datos.empty:
                resultado["recomendaciones"] = [
                    {k: (v if isinstance(v, str) else _entero(v)) for k, v in fila.items()}
                    for fila in tabla_datos.head(2).to_dict("records")
                ]
        except Exception:  # noqa: BLE001
            pass

        # Si solo existe la clave 'simbolo', ningún bloque devolvió datos.
        if len(resultado) == 1:
            raise ValueError(f"Sin datos de analistas para '{s}' (solo existen para acciones y algunos ETF).")
        resultado["nota"] = "recomendaciones: conteo de analistas por periodo ('0m' = mes actual, '-1m' = mes anterior)."
        return resultado

    return _cacheado(f"analistas:{s}", 3600, _fn)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara noticias .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
