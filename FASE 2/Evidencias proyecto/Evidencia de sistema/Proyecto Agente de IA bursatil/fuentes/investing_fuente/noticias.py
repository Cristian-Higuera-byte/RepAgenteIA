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

"""Extracción de noticias del RSS de Investing.com y búsqueda por palabra clave.

Expone `noticias` (descarga y normaliza un feed RSS por categoría, con caché de
5 minutos) y `buscar_noticias` (filtra ese resultado por una palabra clave).
Los fallos se reportan siempre como ErrorInvesting."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

import requests

from fuentes.investing_fuente.cache import _cacheado
from fuentes.investing_fuente.constantes import AVISO_FUENTE, FEEDS, CABECERAS
from fuentes.investing_fuente.errores import ErrorInvesting
from fuentes.investing_fuente.utiles import _limpiar_html, _sin_nulos


# TITULO NOTICIAS

# ──────────────────────────────────────────────────────────────
# Extracción de Noticias
# ──────────────────────────────────────────────────────────────
def noticias(categoria: str = "general", cantidad: int = 10) -> dict[str, Any]:
    """Obtiene las últimas noticias publicadas en Investing.com para una categoría dada.

    Categorías válidas: 'general', 'mercados', 'forex', 'acciones', 'cripto', 'economia'.

    Recibe la categoría (se normaliza a minúsculas; vacío equivale a 'general') y
    la cantidad deseada (se limita al rango 1-30). Descarga el feed RSS por HTTP,
    extrae título, resumen (recortado a 300 caracteres), fecha y enlace de cada
    ítem y devuelve un diccionario con la fuente, la categoría, el total, la lista
    de noticias, la hora de consulta en UTC y el aviso de la fuente. El resultado
    se cachea 5 minutos por categoría y cantidad. Lanza ErrorInvesting si la
    categoría no existe, si falla la conexión o si el XML es inválido."""
    # Normaliza la categoría y verifica que exista en los feeds configurados.
    cat = (categoria or "general").strip().lower()
    if cat not in FEEDS:
        raise ErrorInvesting(
            f"Categoría inválida: {categoria!r}. Opciones permitidas: {', '.join(FEEDS.keys())}"
        )

    # Acota la cantidad pedida para no inundar el contexto del modelo.
    n = max(1, min(int(cantidad), 30))
    url = FEEDS[cat]

    def _fn() -> dict[str, Any]:
        """Descarga y procesa el feed de la categoría; se ejecuta solo si la caché no tiene un valor vigente.

        Hace la petición HTTP (timeout de 10 s), parsea el XML RSS y construye el
        diccionario de respuesta con las primeras `n` noticias que tengan título.
        Lanza ErrorInvesting ante errores de red o de formato."""
        # Paso 1: petición HTTP al feed; cualquier error de red se traduce a ErrorInvesting.
        try:
            resp = requests.get(url, headers=CABECERAS, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise ErrorInvesting(
                f"No se pudo conectar con Investing.com ({cat}): {e}"
            ) from e

        # Paso 2: interpreta el XML y localiza el nodo <channel> que contiene los ítems.
        try:
            raiz = ET.fromstring(resp.content)
            channel = raiz.find("channel")
            if channel is None:
                raise ErrorInvesting("El feed RSS de Investing.com no devolvió un canal válido.")
        except ET.ParseError as e:
            raise ErrorInvesting(
                f"Error al procesar la respuesta XML de Investing.com: {e}"
            ) from e

        elementos = channel.findall("item")
        resultado = []

        # Paso 3: normaliza solo los primeros n ítems del feed.
        for elemento in elementos[:n]:
            titulo = elemento.findtext("title", default="").strip()
            enlace = elemento.findtext("link", default="").strip()
            fecha_raw = elemento.findtext("pubDate", default="").strip()
            descripcion_raw = elemento.findtext("description", default="")

            # El resumen llega con HTML; se limpia y se recorta para ahorrar tokens.
            resumen = _limpiar_html(descripcion_raw)
            if len(resumen) > 300:
                resumen = resumen[:300] + "..."

            # Se descartan ítems sin título; los campos vacíos se omiten con _sin_nulos.
            if titulo:
                resultado.append(
                    _sin_nulos(
                        {
                            "titulo": titulo,
                            "resumen": resumen or None,
                            "fecha": fecha_raw or None,
                            "enlace": enlace or None,
                        }
                    )
                )

        # Paso 4: arma la respuesta final con metadatos de la consulta.
        return {
            "fuente": "Investing.com",
            "categoria": cat,
            "noticias_totales": len(resultado),
            "noticias": resultado,
            "consultado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "aviso": AVISO_FUENTE,
        }

    # Cache de 5 minutos (300 segundos) para noticias
    return _cacheado(f"investing:{cat}:{n}", 300, _fn)


# TITULO BUSCAR NOTICIAS

def buscar_noticias(
    busqueda: str, categoria: str = "general", cantidad: int = 10
) -> dict[str, Any]:
    """Filtra las noticias recientes de una categoría por una palabra clave (ej. 'FED', 'Oro', 'Inflación').

    Recibe el término a buscar (sin distinguir mayúsculas), la categoría del feed
    y el máximo de coincidencias a devolver. Siempre consulta las 30 noticias más
    recientes de la categoría (aprovechando la caché de `noticias`) y conserva las
    que contienen el término en el título o en el resumen. Devuelve un
    diccionario con el término, el número total de coincidencias y las primeras
    `cantidad` noticias. Lanza ErrorInvesting si el término está vacío o si
    `noticias` falla."""
    # Normaliza el término; una búsqueda vacía no tiene sentido y se rechaza.
    palabra = (busqueda or "").strip().lower()
    if not palabra:
        raise ErrorInvesting("Falta el término de búsqueda.")

    # Se piden siempre 30 para tener el mayor universo posible donde buscar.
    datos_categoria = noticias(categoria=categoria, cantidad=30)
    # Coincidencia por subcadena en título o resumen (el resumen puede no existir).
    filtradas = [
        n for n in datos_categoria["noticias"]
        if palabra in n["titulo"].lower() or palabra in (n.get("resumen") or "").lower()
    ]

    return {
        "fuente": "Investing.com",
        "busqueda": palabra,
        "categoria": categoria,
        "coincidencias": len(filtradas),
        "noticias": filtradas[:cantidad],
        "consultado_utc": datos_categoria["consultado_utc"],
        "aviso": AVISO_FUENTE,
    }


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
