# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara icono .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Ícono de un activo según su tipo (ver reglas en el docstring de components/iconografia).

Contiene la lógica de decisión: normaliza el símbolo (`nucleo`) y recorre las reglas por tipo de activo
(materias primas, índices, cripto, divisas, MT5, acciones) hasta construir el HTML con las piezas de
`piezas.py`. Puede consultar MT5 y la red (comprobación de logos) a través de `info_mt5` y `logos`.
"""
import re

from components.iconografia.datos import (CRIPTO_URL, CRIPTOS, FLAG, GENERICO, INDICES, MATERIAS,
                                          MONEDA_PAIS)
from components.iconografia.logos import url_existe, url_logo_accion
from components.iconografia.info_mt5 import info_mt5
from components.iconografia.piezas import caja, iniciales, imagen, indice, logo, par, svg_iniciales


def nucleo(simbolo: str) -> str:
    """Nombre comparable: sin '...', '#', sufijos de bróker/bolsa ni 'Cash'/'micro'.

    Recibe el símbolo tal como lo muestra el bróker y devuelve el núcleo en mayúsculas (por ejemplo
    "US30Cash" -> "US30", "WHEAT-DEC26" -> "WHEAT"). Función pura.
    """
    # Limpia marcas del bróker y descarta el sufijo de bolsa (todo tras el primer punto).
    s = (simbolo or "").strip().replace("...", "").strip("#")
    # Base sin sufijo de bolsa y en mayúsculas para comparar.
    base = s.split(".")[0]
    up = base.upper()
    up = re.sub(r"-[A-Z]{3}\d{2}$", "", up)        # futuros: WHEAT-DEC26 -> WHEAT
    up = re.sub(r"24-7$", "", up)                   # GOLD24-7 -> GOLD
    # Quita "Cash"/"Micro" finales siempre que quede algo de nombre.
    for suf in ("CASH", "MICRO"):
        if up.endswith(suf) and len(up) > len(suf):
            up = up[: -len(suf)]
    return up


def icono_activo(simbolo: str, size: int = 32) -> str:
    """HTML del ícono de un activo (ver reglas en el docstring del paquete).

    Recibe el `simbolo` y el tamaño `size` en píxeles. Evalúa las reglas en orden de prioridad y
    devuelve el HTML del primer tipo que coincide; si ninguno aplica, devuelve las iniciales en un
    círculo de color. Puede consultar MT5 y la red para activos que no se reconocen por nombre.
    """
    # Tamaño entero y nombre normalizado para las comparaciones.
    s = int(size)
    n = nucleo(simbolo)

    # Materias primas (GOLD, XAUUSD, OILCash, NATGAS…)
    for clave, src in MATERIAS.items():
        if n == clave or (len(clave) == 3 and n.startswith(clave) and len(n) == 6):
            return caja(s, imagen(src, s, 0, 0))

    # Índices (US30Cash, JP225Cash…)
    if n in INDICES:
        pais, etiqueta = INDICES[n]
        return indice(pais, etiqueta, s)

    # Cripto (BTCUSD, ETHUSD…): logo + bandera de la moneda cotizada
    for cod, archivo in CRIPTOS.items():
        if n.startswith(cod) and n[len(cod):] in MONEDA_PAIS:
            return par(CRIPTO_URL.format(archivo),
                       FLAG.format(MONEDA_PAIS[n[len(cod):]]), s)

    # Divisas (6 letras = dos monedas conocidas)
    if len(n) == 6 and n[:3] in MONEDA_PAIS and n[3:] in MONEDA_PAIS:
        return par(FLAG.format(MONEDA_PAIS[n[:3]]), FLAG.format(MONEDA_PAIS[n[3:]]), s)

    # Desde aquí se usa la carpeta y la descripción de MT5
    # (los símbolos con punto ya son RIC de acciones y no necesitan consulta).
    if "." in (simbolo or ""):
        carpeta, ric = "Stocks", simbolo
    else:
        carpeta, ric = info_mt5(simbolo)

    # Cripto no listada (APTUSD, ARBUSD, ETHBTC…): logo si la librería lo
    # tiene (si no, iniciales) + bandera/logo de la moneda cotizada
    if carpeta == "Cryptocurrencies":
        for q in ("USD", "EUR", "GBP", "JPY", "BTC"):
            if n.endswith(q) and len(n) > len(q):
                cod = n[: -len(q)]
                src = (url_existe(CRIPTO_URL.format(cod.lower()), "cripto:" + cod)
                       or svg_iniciales(cod))
                otro = (CRIPTO_URL.format("btc") if q == "BTC"
                        else FLAG.format(MONEDA_PAIS[q]))
                return par(src, otro, s)
        return caja(s, imagen(GENERICO["cripto"], s, 0, 0))

    # Índices temáticos (AI_INDX, USD_FX_Index…): gráfico; los de divisas, su bandera
    if carpeta == "Thematic Indices":
        m = re.match(r"^([A-Z]{3})_FX_INDEX$", n)
        if m and m.group(1) in MONEDA_PAIS:
            return indice(MONEDA_PAIS[m.group(1)], "FX", s)
        if "PRECIOUS" in n:
            return caja(s, imagen(MATERIAS["GOLD"], s, 0, 0))
        return caja(s, imagen(GENERICO["tematico"], s, 0, 0))

    # Acciones y ETFs: logo de la empresa/fondo si existe.
    # El código bursátil viene en el nombre (NVDA.OQ en otros brókers) o, en XM,
    # en la DESCRIPCIÓN de MT5: "Adidas AG (ADSGn.DE)", "Telus Corp (TU)".
    if ric:
        url = url_logo_accion(ric)
        if url:
            return caja(s, logo(url, s))
    if carpeta.startswith("ETF"):
        return caja(s, imagen(GENERICO["etf"], s, 0, 0))
    if carpeta == "Derivatives":
        return caja(s, imagen(GENERICO["otro"], s, 0, 0))

    # Resto: iniciales en círculo de color estable
    return caja(s, iniciales(n, s))


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara icono .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
