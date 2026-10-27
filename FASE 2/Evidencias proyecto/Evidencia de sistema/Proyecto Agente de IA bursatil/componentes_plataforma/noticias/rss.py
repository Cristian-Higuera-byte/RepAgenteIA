# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- INICIO Piña y Jara rss .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Lectura de las fuentes de noticias (RSS) con revisión periódica barata: título, enlace, imagen, fecha, fuente y texto.

Cada fuente tiene su propio estado en memoria, compartido por todas las sesiones: la última respuesta, el `ETag` y el
`Last-Modified`. Al revisarla se envían esas marcas y, si nada cambió, el servidor responde 304 sin cuerpo, así que
revisar cada `INTERVALO_CONDICIONAL` segundos casi no cuesta. Las fuentes que no soportan peticiones condicionales se
revisan cada `INTERVALO_NORMAL` segundos. Las fuentes se consultan en paralelo y una que falla no afecta a las demás
(se conservan sus últimas noticias). Hace peticiones HTTP directas con `urllib` y analiza el XML con `ElementTree`.
"""
import hashlib
import html
import re
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from componentes_plataforma.noticias.articulo import limpiar_lineas, texto_articulo
from componentes_plataforma.noticias.datos import (FUENTES, FUENTES_MAS, INTERVALO_CONDICIONAL, INTERVALO_NORMAL,
                                                   MAX_POR_FUENTE, MAX_VERIFICAR, PLACEHOLDER)

_AGENTE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
# Segundos máximos de espera por una fuente (la petición HTTP) y, antes de dibujar, por las fuentes que se refrescan a la vez:
# con noticias ya cargadas casi no se espera (se dibuja lo que hay y el refresco sigue en segundo plano); la primera vez, sin
# nada que mostrar, se espera lo justo para que salgan las fuentes más rápidas y el resto aparece en la siguiente revisión.
_ESPERA_FUENTE = 8
_ESPERA_FRIA = 2.5
_ESPERA_CALIENTE = 0.8
# Hilos que revisan las fuentes, compartidos por todas las sesiones.
_REFRESCADOR = ThreadPoolExecutor(max_workers=8)
# Estado por dirección: {"items", "etag", "modificado", "ultima" (instante de la última revisión), "fallos"}.
_ESTADO: dict = {}
_CANDADO = threading.Lock()
# Resultado de la comprobación de cada noticia que necesita leer su página: enlace -> True (entrega texto) o False (no).
_LECTURA: dict = {}
_EN_CURSO: set = set()
_VERIFICADOR = ThreadPoolExecutor(max_workers=4)
# Segundos que se espera, como máximo, a que terminen las comprobaciones pendientes antes de dibujar (las que no alcancen se
# resuelven en segundo plano y esas noticias aparecen en la siguiente revisión).
_ESPERA_VERIFICACION = 1.0
# Marca de que ya se lanzó la precarga de las fuentes (una vez por proceso).
_PRECARGADO = threading.Event()


# TITULO ETIQUETA

def _etiqueta(el) -> str:
    """Nombre de una etiqueta XML sin su espacio de nombres (`{...}content` pasa a `content`); vacío si no es etiqueta."""
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


# TITULO HIJO

def _hijo(el, nombre: str):
    """Primer hijo directo cuyo nombre (sin espacio de nombres) coincide, o None."""
    for h in el:
        if _etiqueta(h) == nombre:
            return h
    return None


# TITULO LIMPIAR

def _limpiar(texto: str) -> str:
    """Quita las etiquetas HTML de un texto, decodifica las entidades (&amp;, etc.) y recorta los espacios.
    Acepta None o vacío y devuelve cadena vacía."""
    return html.unescape(re.sub(r"<[^>]+>", "", texto or "")).strip()


# TITULO A PARRAFOS

def _a_parrafos(fragmento_html: str) -> str:
    """Convierte el HTML de un artículo (`content:encoded`) en texto plano con un párrafo por línea.

    Los cierres de párrafo, saltos de línea y encabezados pasan a saltos de línea; el resto de etiquetas se elimina y las
    entidades se decodifican. Devuelve cadena vacía si no queda nada."""
    t = re.sub(r"(?is)<(script|style|noscript|iframe)\b.*?</\1>", "", fragmento_html or "")
    t = re.sub(r"(?i)</(p|div|h[1-6]|li|blockquote)>|<br\s*/?>", "\n", t)
    lineas = [html.unescape(re.sub(r"<[^>]+>", "", ln)).strip() for ln in t.split("\n")]
    return "\n".join(ln for ln in lineas if ln)


# TITULO FECHA A MARCA TIEMPO

def _fecha_a_marca_tiempo(pubdate: str) -> float:
    """Convierte la fecha de publicación de un item RSS en una marca de tiempo unix.

    Intenta primero el formato RFC 822 de RSS y luego el formato ISO `AAAA-MM-DD HH:MM:SS` (interpretado en
    UTC). Devuelve 0.0 si la fecha está vacía o no se reconoce."""
    pubdate = (pubdate or "").strip()
    if not pubdate:
        return 0.0
    try:
        return parsedate_to_datetime(pubdate).timestamp()
    except Exception:
        pass
    texto = pubdate[:19].replace("T", " ")
    try:
        return datetime.strptime(texto, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return 0.0


# TITULO FECHA LOCAL

def _fecha_local(marca_tiempo: float, raw: str) -> str:
    """Formatea la marca de tiempo como `dd-mm-aaaa hh:mm` en hora local; si no hay `ts` o falla, devuelve el
    texto original `raw`."""
    try:
        return datetime.fromtimestamp(marca_tiempo).strftime("%d-%m-%Y %H:%M") if marca_tiempo else raw
    except Exception:
        return raw


# TITULO IMAGEN

def _imagen(it, crudo: str) -> str:
    """Dirección de la imagen de una noticia: `enclosure`, `media:content`, `media:thumbnail` o la primera `<img>` del
    contenido. Devuelve cadena vacía si no hay ninguna."""
    for h in it.iter():
        if _etiqueta(h) in ("enclosure", "content", "thumbnail"):
            url = (h.get("url") or "").strip()
            tipo = h.get("type") or ""
            if url.startswith("http") and (not tipo or tipo.startswith("image") or _etiqueta(h) == "thumbnail"
                                           or h.get("medium") == "image"):
                return url
    m = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", html.unescape(crudo))
    return m.group(1) if m and m.group(1).startswith("http") else ""


# TITULO PARSEAR

def _parsear(cuerpo: bytes, fuente: dict) -> list:
    """Convierte el XML de un RSS en la lista de noticias de la fuente (las más nuevas primero, hasta MAX_POR_FUENTE).

    Cada noticia es un diccionario con `id`, `title`, `link`, `desc` (resumen), `texto` (artículo completo si el RSS lo
    incluye en `content:encoded`, si no vacío), `img`, `_ts` (marca de tiempo para ordenar), `fecha` (texto), `fuente`,
    `idioma`, `extraer` (si conviene intentar leer el artículo) y `lectura` (si se puede leer dentro de la plataforma). Devuelve lista vacía si el XML no es válido."""
    try:
        raiz = ET.fromstring(cuerpo)
    except Exception:
        return []
    salida = []
    for it in raiz.findall(".//item"):
        h_t, h_l = _hijo(it, "title"), _hijo(it, "link")
        titulo = _limpiar(h_t.text if h_t is not None else "")
        enlace = ((h_l.text if h_l is not None else "") or "").strip()
        if not titulo or not enlace:
            continue
        h_d, h_c, h_f = _hijo(it, "description"), _hijo(it, "encoded"), _hijo(it, "pubDate")
        crudo = ET.tostring(it, encoding="unicode")
        marca_tiempo = _fecha_a_marca_tiempo((h_f.text if h_f is not None else "") or "")
        texto = "\n".join(limpiar_lineas(_a_parrafos(h_c.text).split("\n"))) if h_c is not None and h_c.text else ""
        salida.append({
            "id": hashlib.sha1(enlace.encode("utf-8")).hexdigest()[:12],
            "title": titulo,
            "link": enlace,
            "desc": _limpiar(h_d.text if h_d is not None else "") or texto[:300],
            "texto": texto if len(texto) > 600 else "",
            "img": _imagen(it, crudo) or PLACEHOLDER,
            "_ts": marca_tiempo,
            "fecha": _fecha_local(marca_tiempo, ((h_f.text if h_f is not None else "") or "")[:16]),
            "fuente": fuente["nombre"],
            "idioma": fuente["idioma"],
            "extraer": bool(fuente.get("extraer")),
            "lectura": bool(fuente.get("lectura")),
        })
    salida.sort(key=lambda n: n["_ts"], reverse=True)
    return salida[:MAX_POR_FUENTE]


# TITULO REFRESCAR

def _refrescar(fuente: dict) -> None:
    """Revisa una fuente si ya pasó su intervalo y actualiza su estado.

    Marca la revisión antes de pedir (así dos sesiones a la vez no repiten la petición) y envía `If-None-Match` /
    `If-Modified-Since` cuando la fuente los soporta. Con 304 conserva las noticias; con 200 las reemplaza; ante
    cualquier error conserva las anteriores y cuenta el fallo. No devuelve nada."""
    url = fuente["url"]
    intervalo = INTERVALO_CONDICIONAL if fuente.get("condicional") else INTERVALO_NORMAL
    with _CANDADO:
        est = _ESTADO.setdefault(url, {"items": [], "etag": "", "modificado": "", "ultima": 0.0, "fallos": 0})
        if time.time() - est["ultima"] < intervalo:
            return
        est["ultima"] = time.time()
        etag, modificado = est["etag"], est["modificado"]
    cabeceras = {"User-Agent": _AGENTE, "Accept": "application/rss+xml, application/xml, text/xml, */*"}
    if etag:
        cabeceras["If-None-Match"] = etag
    if modificado:
        cabeceras["If-Modified-Since"] = modificado
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=cabeceras), timeout=_ESPERA_FUENTE) as r:
            cuerpo = r.read(3_000_000)
            nuevas = _parsear(cuerpo, fuente)
            with _CANDADO:
                if nuevas:
                    est["items"] = nuevas
                est["etag"] = r.headers.get("ETag", "")
                est["modificado"] = r.headers.get("Last-Modified", "")
                est["fallos"] = 0
    except urllib.error.HTTPError as e:
        with _CANDADO:
            est["fallos"] = 0 if e.code == 304 else est["fallos"] + 1
    except Exception:
        with _CANDADO:
            est["fallos"] += 1


# TITULO VERIFICAR

def _verificar(link: str) -> None:
    """Comprueba si la página de una noticia entrega texto de artículo y guarda el resultado en `_LECTURA`.

    Se ejecuta en un hilo de fondo; el texto queda en la caché de `articulo`, así que al abrir la noticia es instantáneo."""
    try:
        correcto = bool(texto_articulo(link))
    except Exception:
        correcto = False
    with _CANDADO:
        if len(_LECTURA) >= 2000:
            _LECTURA.pop(next(iter(_LECTURA)), None)
        _LECTURA[link] = correcto
        _EN_CURSO.discard(link)


# TITULO PEDIR VERIFICACIONES

def _pedir_verificaciones(listas: list) -> list:
    """Lanza en segundo plano la comprobación de las noticias recientes que aún no se han comprobado.

    Solo cuenta las noticias de fuentes con `lectura` y `extraer` cuyo RSS no trae el texto, las `MAX_VERIFICAR` más nuevas
    de cada fuente. Devuelve la lista de tareas lanzadas (para poder esperarlas un momento)."""
    tareas = []
    for lista in listas:
        nuevas = 0
        for n in lista:
            if not (n["lectura"] and n["extraer"] and not n["texto"]):
                continue
            nuevas += 1
            if nuevas > MAX_VERIFICAR:
                break
            with _CANDADO:
                if n["link"] in _LECTURA or n["link"] in _EN_CURSO:
                    continue
                _EN_CURSO.add(n["link"])
            tareas.append(_VERIFICADOR.submit(_verificar, n["link"]))
    return tareas


# TITULO CLASIFICAR

def _clasificar(n: dict):
    """Devuelve la noticia con su campo `lectura` definitivo, o None si todavía no se sabe.

    Entrega texto (`lectura` verdadero) si su fuente lo permite y el RSS trae el texto o la página se pudo leer. Si la
    fuente no permite lectura, o la página no entregó texto, queda en falso (irá al panel lateral). Si la comprobación
    aún no terminó devuelve None: la noticia no se muestra en ningún lado hasta saberlo."""
    if not n["lectura"] or n["texto"]:
        return n
    if not n["extraer"]:
        return dict(n, lectura=False)
    with _CANDADO:
        correcto = _LECTURA.get(n["link"])
    return None if correcto is None else dict(n, lectura=correcto)


# TITULO JUNTAR

def _juntar(fuentes: list) -> list:
    """Noticias de varias fuentes, sin enlaces ni títulos repetidos y de la más nueva a la más vieja.

    Revisa en paralelo las fuentes que lo necesitan, sin hacer esperar la página: con noticias ya cargadas espera como máximo
    `_ESPERA_CALIENTE` segundos y la primera vez (sin nada que mostrar) `_ESPERA_FRIA`; las fuentes que no alcancen siguen en
    segundo plano y se verán en la próxima lectura. Comprueba en segundo plano qué noticias entregan texto (espera como máximo
    `_ESPERA_VERIFICACION` segundos) y reúne lo que hay en el estado de cada fuente. Cada noticia sale con `lectura` verdadero
    solo si de verdad se puede leer aquí."""
    pendientes = [f for f in fuentes if time.time() - _ESTADO.get(f["url"], {}).get("ultima", 0.0)
                  >= (INTERVALO_CONDICIONAL if f.get("condicional") else INTERVALO_NORMAL)]
    if pendientes:
        con_datos = any(_ESTADO.get(f["url"], {}).get("items") for f in fuentes)
        wait([_REFRESCADOR.submit(_refrescar, f) for f in pendientes], timeout=_ESPERA_CALIENTE if con_datos else _ESPERA_FRIA)
    with _CANDADO:
        listas = [list(_ESTADO.get(f["url"], {}).get("items", [])) for f in fuentes]
    tareas = _pedir_verificaciones(listas)
    if tareas:
        wait(tareas, timeout=_ESPERA_VERIFICACION)
    vistos_enlace: set = set()
    vistos_titulo: set = set()
    todas = []
    for lista in listas:
        for n in lista:
            n = _clasificar(n)
            if n is None:
                continue
            clave = re.sub(r"\W+", "", n["title"].lower())
            if n["link"] in vistos_enlace or clave in vistos_titulo:
                continue
            vistos_enlace.add(n["link"])
            vistos_titulo.add(clave)
            todas.append(n)
    todas.sort(key=lambda n: n["_ts"], reverse=True)
    return todas


# TITULO HAY DATOS

def hay_datos() -> bool:
    """¿Ya hay noticias cargadas de alguna fuente principal? Sirve para decidir si la página muestra un aviso de carga."""
    with _CANDADO:
        return any(_ESTADO.get(f["url"], {}).get("items") for f in FUENTES)


# TITULO PRECARGAR

def precargar() -> None:
    """Empieza a leer todas las fuentes en segundo plano, una sola vez por proceso (las siguientes llamadas no hacen nada).

    Se llama al iniciar la sesión del usuario: cuando abre la sección Noticias, las fuentes ya están leídas y las noticias que
    necesitan comprobar su texto ya se están comprobando, así que la página se dibuja al instante. No espera ni devuelve nada."""
    if _PRECARGADO.is_set():
        return
    _PRECARGADO.set()

    def _tarea() -> None:
        """Lee las fuentes y, cuando llegan, lanza la comprobación del texto de sus noticias."""
        fuentes = FUENTES + FUENTES_MAS
        wait([_REFRESCADOR.submit(_refrescar, f) for f in fuentes], timeout=_ESPERA_FUENTE + 2)
        with _CANDADO:
            listas = [list(_ESTADO.get(f["url"], {}).get("items", [])) for f in fuentes]
        _pedir_verificaciones(listas)
    threading.Thread(target=_tarea, name="pj-noticias-precarga", daemon=True).start()


# TITULO CARGAR NOTICIAS

def cargar_noticias() -> list:
    """Noticias de las fuentes principales (`FUENTES`). Alimentan la noticia principal y el carrusel."""
    return _juntar(FUENTES)


# TITULO CARGAR MAS NOTICIAS

def cargar_mas_noticias() -> list:
    """Noticias de las fuentes de "Más noticias" (`FUENTES_MAS`)."""
    return _juntar(FUENTES_MAS)

# -------------------------------------------------------------------------------------------------------
# --------------------------------------- FIN Piña y Jara rss .PY ---------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
