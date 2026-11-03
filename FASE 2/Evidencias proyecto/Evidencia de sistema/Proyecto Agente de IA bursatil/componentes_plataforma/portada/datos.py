# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara datos .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Datos de las secciones «Mercados» y «Noticias» de la portada pública.

Noticias: reutiliza el lector de RSS de la plataforma (componentes_plataforma/noticias/rss.py), que usa fuentes gratuitas y sin inicio de sesión; la portada nunca espera a la red:
si todavía no hay titulares cargados devuelve una lista vacía y la sección muestra un aviso.

Cotizaciones: EN VIVO con la cuenta de servicio de Capital.com (la del .env del servidor: CAPITAL_API_KEY, CAPITAL_IDENTIFIER, CAPITAL_API_PASSWORD y CAPITAL_DEMO=true; use una cuenta demo
dedicada a la portada). Un solo hilo en segundo plano consulta los precios cada pocos segundos y los deja en una caché; los visitantes solo leen esa caché, así que Capital.com recibe las mismas
peticiones haya 1 o 1.000 visitantes. El hilo se detiene solo si pasan 2 minutos sin visitas. Si no hay credenciales, no hay conexión o la caché está vencida, se muestran cotizaciones de EJEMPLO
(`ejemplo=True`) y la sección lo avisa, así que la portada nunca queda vacía ni se cae.
"""
from __future__ import annotations

import threading
import time

# Cotizaciones de ejemplo (símbolo, nombre, precio, variación en %, decimales). Son ilustrativas: no vienen de ningún mercado.
_EJEMPLO = [
    ("EURUSD", "Euro / Dólar", 1.11362, -0.17, 5),
    ("GBPUSD", "Libra / Dólar", 1.33267, 0.00, 5),
    ("USDJPY", "Dólar / Yen", 157.85, 0.01, 2),
    ("GOLD", "Oro", 4023.54, -0.76, 2),
    ("BTCUSD", "Bitcoin", 80175.25, -1.30, 2),
    ("ETHUSD", "Ethereum", 2322.05, -1.44, 2),
    ("US30", "Dow Jones", 52390.00, -0.28, 2),
    ("ACN", "Accenture", 244.89, 0.51, 2),
]


# Instrumentos de la tabla (símbolo de la plataforma, nombre en español). `resolver_simbolo` del backend los traduce al epic de Capital.com.
_INSTRUMENTOS = [
    ("EURUSD", "Euro / Dólar"), ("GBPUSD", "Libra / Dólar"), ("USDJPY", "Dólar / Yen"), ("GOLD", "Oro"),
    ("BTCUSD", "Bitcoin"), ("ETHUSD", "Ethereum"), ("US30", "Dow Jones"), ("AAPL", "Apple"),
]
# Cada cuántos segundos se consultan los precios, cada cuántos los minigráficos (velas reales), cuánto vive una lectura y cuánto sin visitas antes de detener el hilo.
_CADA_PRECIOS_S = 5.0
_CADA_SERIES_S = 600.0
_VIDA_LECTURA_S = 60.0
_SIN_VISITAS_S = 120.0
# Estado compartido por todos los visitantes: última lectura de precios, series de los minigráficos, hora de la última visita y el hilo.
_estado: dict = {"datos": None, "ts": 0.0, "series": {}, "series_ts": 0.0, "visita": 0.0, "hilo": None}
_candado = threading.Lock()


# TITULO LEER PRECIOS

def _leer_precios(mod) -> list[dict] | None:
    """Pide a Capital.com, en UNA llamada, el precio y la variación del día de todos los instrumentos. `mod` es la copia del backend con la cuenta del servidor.

    Devuelve la lista de cotizaciones (simbolo, nombre, precio, var en %, decimales, ejemplo=False, ts) o None si la respuesta no sirve."""
    epics = {s: mod.resolver_simbolo(s) for s, _ in _INSTRUMENTOS}
    r = mod._pedir("GET", "/markets", parametros={"epics": ",".join(e for e in epics.values() if e)})
    if r is None or r.status_code != 200:
        return None
    detalles = r.json().get("marketDetails", [])
    por_epic = {((m.get("instrument") or {}).get("epic")): m.get("snapshot") or {} for m in detalles}
    ahora = time.time()
    salida = []
    for simbolo, nombre in _INSTRUMENTOS:
        snap = por_epic.get(epics.get(simbolo))
        if not snap or snap.get("bid") is None:
            continue
        precio = float(snap["bid"])
        decimales = int(snap.get("decimalPlacesFactor") or (2 if precio > 100 else 5))
        salida.append({"simbolo": simbolo, "nombre": nombre, "precio": precio, "var": float(snap.get("percentageChange") or 0.0), "decimales": decimales,
                       "ejemplo": False, "ts": ahora})
    return salida or None


# TITULO LEER SERIES

def _leer_series(mod) -> dict:
    """Cierres horarios de las últimas 24 velas de cada instrumento, para los minigráficos (datos reales). Un instrumento que falle se omite."""
    series = {}
    for simbolo, _ in _INSTRUMENTOS:
        try:
            tabla = mod.obtener_datos_historicos(simbolo, mod.TIMEFRAME_H1, 24)
            if tabla is not None and len(tabla) >= 5:
                series[simbolo] = [float(x) for x in tabla["close"].tolist()]
        except Exception:   # noqa: BLE001 - un instrumento sin velas no debe frenar a los demás
            continue
    return series


# TITULO BUCLE

def _bucle() -> None:
    """Hilo de fondo: actualiza la caché de precios cada pocos segundos (y la de minigráficos cada 10 minutos) mientras haya visitas recientes; luego termina."""
    try:
        from herramientas.backends import sesiones_capital
        mod = sesiones_capital.modulo_de(sesiones_capital._CLAVE_LEGADO)   # cuenta de servicio del .env, no la de ningún usuario
        mod.marcar_hilo_fondo()
    except Exception:   # noqa: BLE001 - sin backend o sin credenciales: se queda con los datos de ejemplo
        with _candado:
            _estado["hilo"] = None
        return
    while time.time() - _estado["visita"] < _SIN_VISITAS_S:
        try:
            lectura = _leer_precios(mod)
            if lectura:
                with _candado:
                    _estado["datos"], _estado["ts"] = lectura, time.time()
            if time.time() - _estado["series_ts"] >= _CADA_SERIES_S:
                series = _leer_series(mod)
                with _candado:
                    if series:
                        _estado["series"] = series
                    _estado["series_ts"] = time.time()
        except Exception:   # noqa: BLE001 - un fallo de red no mata el hilo: se reintenta en el próximo ciclo
            pass
        time.sleep(_CADA_PRECIOS_S)
    with _candado:
        _estado["hilo"] = None


# TITULO COTIZACIONES EN VIVO

def _cotizaciones_en_vivo() -> list[dict] | None:
    """Última lectura de precios de Capital.com (con su serie de minigráfico) o None si todavía no hay una lectura reciente.

    Anota la visita y arranca el hilo de fondo si no estaba corriendo; no espera a la red: el primer visitante ve los datos de ejemplo unos segundos y, cuando la lectura llega, la
    sección (que se refresca sola) pasa a mostrar los precios en vivo."""
    with _candado:
        _estado["visita"] = time.time()
        hilo = _estado["hilo"]
        if hilo is None or not hilo.is_alive():
            _estado["hilo"] = threading.Thread(target=_bucle, name="pj-portada-precios", daemon=True)
            _estado["hilo"].start()
        lectura, ts, series = _estado["datos"], _estado["ts"], dict(_estado["series"])
    if not lectura or time.time() - ts > _VIDA_LECTURA_S:
        return None
    return [{**x, "serie": series.get(x["simbolo"])} for x in lectura]


# TITULO EJEMPLO

def _ejemplo() -> list[dict]:
    """Cotizaciones de ejemplo como lista de diccionarios: simbolo, nombre, precio, var (en %), decimales y ejemplo=True."""
    return [{"simbolo": s, "nombre": n, "precio": p, "var": v, "decimales": d, "ejemplo": True, "ts": 0.0} for s, n, p, v, d in _EJEMPLO]


# TITULO ACTIVOS

def activos() -> list[dict]:
    """Cotizaciones para la sección «Mercados»: las en vivo si hay una lectura reciente y, si no, las de ejemplo."""
    try:
        vivas = _cotizaciones_en_vivo()
    except Exception:   # noqa: BLE001 - la portada nunca debe caerse por la fuente de precios
        vivas = None
    return vivas or _ejemplo()


# TITULO NOTICIAS

def noticias(cantidad: int = 6) -> list[dict]:
    """Últimos titulares en español para la portada (si no hay, en cualquier idioma). Devuelve lista vacía si aún no se cargaron.

    Inicia la lectura de las fuentes en segundo plano (una sola vez por proceso) y solo consulta lo que ya está cargado, así que no hace esperar la página. Cada elemento trae `title`, `link`, `fuente`, `fecha` y `desc`."""
    try:
        from componentes_plataforma.noticias import rss
        rss.precargar()
        if not rss.hay_datos():
            return []
        lista = rss.cargar_noticias()
    except Exception:   # noqa: BLE001 - sin red o con una fuente caída, la portada sigue funcionando
        return []
    espanol = [n for n in lista if n.get("idioma") == "ES"]
    return (espanol or lista)[:cantidad]


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
