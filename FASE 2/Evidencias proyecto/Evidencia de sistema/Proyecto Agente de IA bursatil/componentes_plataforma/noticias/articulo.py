# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara articulo .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Lectura del texto de un artículo desde su página, para mostrarlo dentro de la plataforma sin iframe ni inicio de sesión.

`texto_articulo(url)` descarga la página desde el servidor y extrae solo el texto del artículo. Usa `trafilatura` si está
instalada (es la que mejor separa el artículo del resto de la página); si no, un extractor sencillo que une los párrafos
largos. Es una función de mejor esfuerzo: muchas páginas bloquean las descargas automáticas o cargan el texto con
JavaScript, y en ese caso devuelve cadena vacía y la ventana de la noticia muestra el resumen con un botón para abrirla en
el sitio. Solo se aceptan direcciones http(s) que apunten a servidores públicos de internet. No depende de Streamlit: el verificador de
`rss.py` la usa desde hilos de fondo para saber qué noticias entregan texto.
"""
import ipaddress
import re
import socket
import threading
import time
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse

_AGENTE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
# Segundos máximos de espera y bytes máximos que se leen de una página.
_ESPERA = 10
_MAX_BYTES = 2_500_000
# Texto mínimo (caracteres) para considerar que se extrajo un artículo y no solo un fragmento de la página.
MINIMO_UTIL = 600
# Texto máximo que se conserva de un artículo.
_MAX_TEXTO = 15000


# TITULO ES PUBLICA

def _es_publica(url: str) -> bool:
    """Indica si la dirección es http(s) y su servidor es público (no localhost ni una red privada).

    Evita que un enlace manipulado en un feed haga que el servidor pida direcciones internas. Devuelve False si el nombre
    no se puede resolver."""
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(p.hostname))
    except Exception:
        return False
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast)


# Etiquetas cuyo contenido nunca es texto del artículo: se ignoran por completo, con todo lo que llevan dentro.
_IGNORAR = {"script", "style", "noscript", "svg", "iframe", "form", "nav", "footer", "header", "aside", "button",
            "select", "template", "head", "figcaption", "picture"}
# Etiquetas de texto que se recogen: párrafos y subtítulos.
_TEXTO = {"p", "h2", "h3", "h4"}
# Señales de código de programación dentro de un texto (publicidad, comentarios, widgets): si aparece alguna, se descarta.
_CODIGO = re.compile(r"(function\s*\(|=>|googletag|jQuery|\bvar\s+\w+\s*=|\bconst\s+\w+\s*=|\bwindow\.\w|\bdocument\.\w|"
                     r"\.push\(|\.display\(|\bnew\s+[A-Z]\w+\(|</?\w+[^>]*>|[{};]\s*[{};]|(\w+\s*:\s*[\"'][^\"']*[\"']\s*,\s*){2,})")
# Párrafos que marcan el final del artículo (comentarios, suscripción, relacionados): desde ahí no se recoge más texto.
_FIN = re.compile(r"^(comentar|comentarios?\b|esta noticia a[uú]n no tiene|sea el primero|deja tu comentario|"
                  r"te puede interesar|noticias relacionadas|art[ií]culos relacionados|lee tambi[eé]n|suscr[ií]bete|"
                  r"related (articles|stories)|read more|sign up)", re.I)


# TITULO PARRAFOS

class _Parrafos(HTMLParser):
    """Recorre una página HTML y junta el texto de sus párrafos y subtítulos.

    Ignora por completo scripts, estilos, menús, pies de página y demás etiquetas de `_IGNORAR` con todo su contenido.
    Anota si cada texto está dentro de una etiqueta `<article>`; `piezas` es la lista `(dentro_de_article, texto)`."""

    # TITULO INIT

    def __init__(self):
        """Prepara el lector con las listas de párrafos y el estado de la etiqueta que se está leyendo."""
        super().__init__(convert_charrefs=True)
        self.piezas: list = []
        self._ignorar = 0
        self._article = 0
        self._actual: list = []
        self._recogiendo = False

    # TITULO HANDLE STARTTAG

    def handle_starttag(self, etiqueta, attrs):
        """Al abrir una etiqueta decide si lo que viene es texto del artículo o contenido que se ignora."""
        if etiqueta in _IGNORAR:
            self._ignorar += 1
        elif etiqueta == "article":
            self._article += 1
        elif etiqueta in _TEXTO and not self._ignorar:
            self._cerrar()
            self._recogiendo = True

    # TITULO HANDLE ENDTAG

    def handle_endtag(self, etiqueta):
        """Al cerrar una etiqueta termina el párrafo en curso o deja de ignorar el contenido."""
        if etiqueta in _IGNORAR:
            self._ignorar = max(0, self._ignorar - 1)
        elif etiqueta == "article":
            self._article = max(0, self._article - 1)
        elif etiqueta in _TEXTO:
            self._cerrar()

    # TITULO HANDLE DATA

    def handle_data(self, data):
        """Agrega al párrafo en curso el texto que hay entre etiquetas, si corresponde al artículo."""
        if self._recogiendo and not self._ignorar:
            self._actual.append(data)

    # TITULO CERRAR

    def _cerrar(self):
        """Termina el texto que se estaba recogiendo y, si no está vacío, lo guarda junto con su pertenencia a `<article>`."""
        if self._recogiendo:
            texto = re.sub(r"\s+", " ", "".join(self._actual)).strip()
            if texto:
                self.piezas.append((self._article > 0, texto))
        self._actual, self._recogiendo = [], False


# Una línea que termina en «; , { } [ ]» o que abre una lista/objeto (`clave: [`) es código: la prosa termina en punto u otro cierre.
_COLA_CODIGO = re.compile(r"([;,{}\[\]]\s*$)|(\b\w+\s*:\s*[\[{])")


# TITULO ES CODIGO

def _es_codigo(texto: str) -> bool:
    """Indica si un texto parece código de programación o publicidad (JavaScript, etiquetas, pares clave: "valor",
    configuraciones de widgets) y no prosa."""
    return (bool(_CODIGO.search(texto)) or bool(_COLA_CODIGO.search(texto))
            or sum(texto.count(c) for c in "{}();=<>") > max(8, len(texto) * 0.08))


# TITULO LIMPIAR LINEAS

def limpiar_lineas(lineas: list) -> list:
    """Filtra las líneas de un artículo: quita las que parecen código, las muy cortas y todo lo que sigue a una señal de
    fin de artículo (comentarios, suscripción, relacionados). Conserva el orden."""
    salida = []
    for t in lineas:
        t = t.strip()
        if _FIN.search(t):
            break
        if len(t) < 40 or _es_codigo(t):
            continue
        salida.append(t)
    return salida


# TITULO EXTRAER

def _extraer(pagina: str) -> str:
    """Extrae el texto del artículo de una página HTML y lo devuelve con un párrafo por línea.

    Si `trafilatura` está instalada la usa primero. Si no (o si no devuelve nada), recorre la página con un analizador HTML
    que ignora scripts, menús y pies de página, prefiere el texto que está dentro de `<article>` y descarta lo que parece
    código o publicidad y lo que viene después de la sección de comentarios. Devuelve cadena vacía si no queda texto."""
    try:
        import trafilatura  # type: ignore[import-untyped]
        t = trafilatura.extract(pagina, include_comments=False, include_tables=False) or ""
        lineas = limpiar_lineas(t.split("\n"))
        if lineas:
            return "\n".join(lineas)
    except Exception:
        pass
    p = _Parrafos()
    try:
        p.feed(pagina)
        p.close()
        p._cerrar()
    except Exception:
        pass
    dentro = [t for en_art, t in p.piezas if en_art]
    return "\n".join(limpiar_lineas(dentro or [t for _, t in p.piezas]))


# Caché propia (no depende de Streamlit para poder usarse desde hilos de fondo): dirección -> (instante, texto).
_TTL_CACHE = 1800
_MAX_CACHE = 400
_CACHE: dict = {}
_CANDADO = threading.Lock()


# TITULO TEXTO ARTICULO

def texto_articulo(url: str) -> str:
    """Texto del artículo de `url`, o cadena vacía si no se pudo leer o es demasiado corto (menos de MINIMO_UTIL).

    Resultado cacheado 30 minutos por dirección (también los fallos, para no repetir descargas inútiles). Descarga la
    página con `urllib` (con el mismo agente de un navegador), rechaza direcciones no públicas y recorta el resultado a un
    máximo razonable. Se puede llamar desde cualquier hilo y nunca lanza excepciones."""
    with _CANDADO:
        guardado = _CACHE.get(url)
    if guardado and time.time() - guardado[0] < _TTL_CACHE:
        return guardado[1]
    texto = _descargar_texto(url)
    with _CANDADO:
        if len(_CACHE) >= _MAX_CACHE:
            _CACHE.pop(next(iter(_CACHE)), None)
        _CACHE[url] = (time.time(), texto)
    return texto


# TITULO DESCARGAR TEXTO

def _descargar_texto(url: str) -> str:
    """Descarga la página de `url` y devuelve su texto de artículo (vacío si falla o es muy corto). Sin caché."""
    try:
        if not _es_publica(url):
            return ""
        req = urllib.request.Request(url, headers={"User-Agent": _AGENTE, "Accept": "text/html,*/*", "Accept-Language": "es,en;q=0.8"})
        with urllib.request.urlopen(req, timeout=_ESPERA) as r:
            pagina = r.read(_MAX_BYTES).decode(r.headers.get_content_charset() or "utf-8", "ignore")
        texto = _extraer(pagina)
        return texto[:_MAX_TEXTO] if len(texto) >= MINIMO_UTIL else ""
    except Exception:
        return ""


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara articulo .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
