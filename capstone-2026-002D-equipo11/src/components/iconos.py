"""
iconos.py
---------
Íconos de activos con el estilo de las plataformas de trading (tipo XM), en UN
solo lugar para todo el dashboard (Lista de activos, Favoritos, Cartera,
Cotizaciones).

Reglas según el tipo de activo:
  - Divisas (EURUSD, USDJPY…): dos banderas REDONDAS superpuestas
    (moneda base adelante a la izquierda, moneda cotizada atrás a la derecha).
  - Cripto (BTCUSD, ETHUSD…): logo de la cripto + bandera de la moneda cotizada.
  - Índices (US30Cash, JP225Cash…): bandera redonda del país + etiqueta abajo.
  - Materias primas (GOLD, SILVER, OILCash…): ícono propio (SVG) en círculo de color.
  - Acciones (NVDA.OQ…): logo de la empresa sobre un círculo con sus iniciales
    (si el logo no existe, quedan visibles las iniciales).
  - Cualquier otro: iniciales en un círculo de color estable.

Fuentes (uso libre): banderas redondas "circle-flags" (HatScripts, MIT) y logos
de cripto "cryptocurrency-icons" (CC0), ambas por CDN jsDelivr. Los íconos de
materias primas son SVG propios. NO se usan archivos de XM (son su propiedad).

El HTML usa solo estilos en línea e <img> (st.html sanea el SVG en línea, por eso
los SVG propios van como imagen data-URI).
"""
import base64
import html
import re
import time
import urllib.request
import zlib

_FLAG = "https://cdn.jsdelivr.net/gh/HatScripts/circle-flags@gh-pages/flags/{}.svg"
_CRIPTO_URL = "https://cdn.jsdelivr.net/npm/cryptocurrency-icons@0.18.1/svg/color/{}.svg"
_LOGO_ACCION = "https://financialmodelingprep.com/image-stock/{}.png"

# Moneda -> código de bandera (circle-flags)
_MONEDA_PAIS = {
    "USD": "us", "EUR": "european_union", "GBP": "gb", "JPY": "jp", "CHF": "ch",
    "AUD": "au", "NZD": "nz", "CAD": "ca", "CNH": "cn", "CNY": "cn", "HKD": "hk",
    "SGD": "sg", "SEK": "se", "NOK": "no", "DKK": "dk", "PLN": "pl", "MXN": "mx",
    "ZAR": "za", "TRY": "tr", "HUF": "hu", "CZK": "cz", "ILS": "il", "RUB": "ru",
    "BRL": "br", "CLP": "cl", "INR": "in", "KRW": "kr", "THB": "th",
}

# Criptos con logo en cryptocurrency-icons
_CRIPTOS = {
    "BTC": "btc", "ETH": "eth", "LTC": "ltc", "XRP": "xrp", "BCH": "bch",
    "ADA": "ada", "DOT": "dot", "DOGE": "doge", "XLM": "xlm", "EOS": "eos",
    "LINK": "link", "BNB": "bnb", "TRX": "trx", "XMR": "xmr", "ETC": "etc",
    "UNI": "uni", "SOL": "sol", "MATIC": "matic", "AVAX": "avax",
}

# Índice (núcleo del nombre, sin "CASH") -> (bandera, etiqueta)
_INDICES = {
    "US30": ("us", "US30"), "DJ30": ("us", "US30"), "WS30": ("us", "US30"),
    "US100": ("us", "US100"), "NAS100": ("us", "US100"), "USTEC": ("us", "US100"),
    "US500": ("us", "US500"), "SPX500": ("us", "US500"), "SP500": ("us", "US500"),
    "US2000": ("us", "US2000"),
    "JP225": ("jp", "JP225"), "JPN225": ("jp", "JP225"),
    "GER40": ("de", "DE40"), "DE40": ("de", "DE40"), "GER30": ("de", "DE30"),
    "UK100": ("gb", "UK100"), "FRA40": ("fr", "FR40"), "FR40": ("fr", "FR40"),
    "EU50": ("european_union", "EU50"), "STOXX50": ("european_union", "EU50"),
    "AUS200": ("au", "AU200"), "HK50": ("hk", "HK50"), "CHINA50": ("cn", "CN50"),
    "CN50": ("cn", "CN50"), "SPA35": ("es", "ES35"), "IT40": ("it", "IT40"),
    "NETH25": ("nl", "NL25"), "SWI20": ("ch", "CH20"),
    # Índices adicionales de XM
    "CA60": ("ca", "CA60"), "CHINAH": ("hk", "CHH"), "SA40": ("za", "SA40"),
    "SING30": ("sg", "SG30"), "GERMID50": ("de", "MD50"), "GERTECH30": ("de", "TC30"),
    "TAIWAN": ("tw", "TW"), "SPAIN": ("es", "ES35"), "CHN50": ("cn", "A50"),
    "US400": ("us", "US400"), "USFANG": ("us", "FANG"), "USDX": ("us", "DXY"),
    "VIX": ("us", "VIX"),
}

# ---------------------------------------------------------------------------
# SVG propios para materias primas (círculo de color + figura blanca)
# ---------------------------------------------------------------------------
_LINGOTES = (
    "<path d='M9 21h6l1.2 4H7.8z M17 21h6l1.2 4H15.8z M13 16h6l1.2 4H11.8z' "
    "fill='#fff' fill-opacity='.95'/>"
)
_GOTA = "<path d='M16 7c3.6 4.6 6 8 6 11a6 6 0 0 1-12 0c0-3 2.4-6.4 6-11z' fill='#fff'/>"
_LLAMA = (
    "<path d='M16 6c1 4 5 5.5 5 11a5 5 0 0 1-10 0c0-2.6 1.4-4.2 2.6-5.4 "
    ".2 1.8 1 2.8 2 3.2-.6-3.4.4-6 .4-8.8z' fill='#fff'/>"
)

_ESPIGA = (  # granos / agrícolas
    "<path d='M16 25V9' stroke='#fff' stroke-width='1.6' stroke-linecap='round'/>"
    "<path d='M16 12c-3-1-4-3.5-4-3.5s3 .2 4 3.5zm0 0c3-1 4-3.5 4-3.5s-3 .2-4 3.5z"
    "M16 16.5c-3-1-4-3.5-4-3.5s3 .2 4 3.5zm0 0c3-1 4-3.5 4-3.5s-3 .2-4 3.5z"
    "M16 21c-3-1-4-3.5-4-3.5s3 .2 4 3.5zm0 0c3-1 4-3.5 4-3.5s-3 .2-4 3.5z' fill='#fff'/>"
)
_GRANO = (  # café / cacao
    "<ellipse cx='16' cy='16' rx='6' ry='8.5' transform='rotate(30 16 16)' fill='#fff'/>"
    "<path d='M12.6 10.6c3 2.4 3.6 7.6 6.8 10.8' stroke='#6b4428' stroke-width='1.4' fill='none'/>"
)
_CUBO = "<rect x='10' y='10' width='12' height='12' rx='2' fill='#fff'/>"  # azúcar
_GRAFICO = (  # ETFs, índices temáticos, genéricos
    "<polyline points='8,21 13,15 17,18 24,10' fill='none' stroke='#fff' "
    "stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'/>"
    "<path d='M20 10h4v4' fill='none' stroke='#fff' stroke-width='2.2' "
    "stroke-linecap='round' stroke-linejoin='round'/>"
)
_MONEDA_CRIPTO = (  # cripto sin logo conocido
    "<circle cx='16' cy='16' r='8' fill='none' stroke='#fff' stroke-width='2'/>"
    "<path d='M14 12h3a2 2 0 0 1 0 4h-3zm0 4h3.5a2 2 0 0 1 0 4H14zM15 11v10' "
    "fill='none' stroke='#fff' stroke-width='1.6'/>"
)


def _svg_circulo(fondo: str, figura: str) -> str:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
        f"<circle cx='16' cy='16' r='16' fill='{fondo}'/>{figura}</svg>"
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


_MATERIAS = {
    "GOLD": _svg_circulo("#f2b630", _LINGOTES), "XAU": _svg_circulo("#f2b630", _LINGOTES),
    "SILVER": _svg_circulo("#aab2bd", _LINGOTES), "XAG": _svg_circulo("#aab2bd", _LINGOTES),
    "PLATINUM": _svg_circulo("#7f8c9a", _LINGOTES), "XPT": _svg_circulo("#7f8c9a", _LINGOTES),
    "PALLADIUM": _svg_circulo("#9aa5b1", _LINGOTES), "XPD": _svg_circulo("#9aa5b1", _LINGOTES),
    "COPPER": _svg_circulo("#c26a3d", _LINGOTES), "XCU": _svg_circulo("#c26a3d", _LINGOTES),
    "OIL": _svg_circulo("#4a4f57", _GOTA), "USOIL": _svg_circulo("#4a4f57", _GOTA),
    "WTI": _svg_circulo("#4a4f57", _GOTA), "XTI": _svg_circulo("#4a4f57", _GOTA),
    "BRENT": _svg_circulo("#2f3540", _GOTA), "UKOIL": _svg_circulo("#2f3540", _GOTA),
    "XBR": _svg_circulo("#2f3540", _GOTA), "UKO": _svg_circulo("#2f3540", _GOTA),
    "NATGAS": _svg_circulo("#2f6fde", _LLAMA), "NGAS": _svg_circulo("#2f6fde", _LLAMA),
    "XNG": _svg_circulo("#2f6fde", _LLAMA), "GAS": _svg_circulo("#2f6fde", _LLAMA),
    # Futuros de XM (núcleo sin vencimiento: "WHEAT-DEC26" -> "WHEAT")
    "GAU": _svg_circulo("#f2b630", _LINGOTES),               # oro en gramos (GAUUSD)
    "PALL": _svg_circulo("#9aa5b1", _LINGOTES), "PLAT": _svg_circulo("#7f8c9a", _LINGOTES),
    "HGCOP": _svg_circulo("#c26a3d", _LINGOTES),
    "OILMN": _svg_circulo("#4a4f57", _GOTA), "GSOIL": _svg_circulo("#5b616b", _GOTA),
    "WHEAT": _svg_circulo("#c9a227", _ESPIGA), "CORN": _svg_circulo("#e0b100", _ESPIGA),
    "SBEAN": _svg_circulo("#7a9a3a", _ESPIGA), "COTTO": _svg_circulo("#8fa3b8", _ESPIGA),
    "COFFE": _svg_circulo("#6b4428", _GRANO), "COCOA": _svg_circulo("#7b4a2e", _GRANO),
    "SUGAR": _svg_circulo("#d9a5b3", _CUBO),
}
_GENERICO = {
    "etf": _svg_circulo("#2563eb", _GRAFICO),
    "tematico": _svg_circulo("#7c3aed", _GRAFICO),
    "otro": _svg_circulo("#475569", _GRAFICO),
    "cripto": _svg_circulo("#f7931a", _MONEDA_CRIPTO),
}

_PALETA = ["#3b82f6", "#ec4899", "#f97316", "#8b5cf6", "#14b8a6",
           "#ef4444", "#22c55e", "#eab308", "#06b6d4", "#64748b"]


# ---------------------------------------------------------------------------
# Piezas HTML
# ---------------------------------------------------------------------------
def _caja(s: int, interior: str, ancho: int | None = None) -> str:
    w = ancho or s
    return (
        f"<span style='position:relative; display:inline-block; flex:0 0 {w}px; "
        f"width:{w}px; height:{s}px; vertical-align:middle;'>{interior}</span>"
    )


def _img(src: str, d: int, left: float, top: float, z: int = 1, borde: bool = False,
         fondo: str = "transparent") -> str:
    aro = "box-shadow:0 0 0 1.5px #0d1117;" if borde else ""
    return (
        f"<img src='{src}' alt='' style='position:absolute; left:{left:.1f}px; top:{top:.1f}px; "
        f"width:{d}px; height:{d}px; border-radius:50%; z-index:{z}; background:{fondo}; "
        f"object-fit:cover; {aro}'>"
    )


def _iniciales(texto: str, s: int, z: int = 0) -> str:
    t = re.sub(r"[^A-Za-z0-9]", "", texto)[:2].upper() or "?"
    color = _PALETA[zlib.crc32(texto.encode()) % len(_PALETA)]
    return (
        f"<span style='position:absolute; inset:0; border-radius:50%; background:{color}; "
        f"color:#fff; font-weight:800; font-size:{max(9, int(s * 0.38))}px; z-index:{z}; "
        f"display:flex; align-items:center; justify-content:center; "
        f"font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'>{html.escape(t)}</span>"
    )


def _par(src_a: str, src_b: str, s: int) -> str:
    """Dos círculos superpuestos: A adelante-izquierda, B atrás-derecha."""
    d = round(s * 0.66)
    top = (s - d) / 2
    return _caja(s, _img(src_b, d, s - d, top, z=1) + _img(src_a, d, 0, top, z=2, borde=True))


def _indice(pais: str, etiqueta: str, s: int) -> str:
    d = round(s * 0.84)
    fs = max(6, round(s * 0.2))
    badge = (
        f"<span style='position:absolute; left:50%; bottom:-1px; transform:translateX(-50%); "
        f"z-index:3; background:#11151c; color:#e6edf3; font-size:{fs}px; font-weight:700; "
        f"line-height:1; padding:1px 3px; border-radius:3px; white-space:nowrap; "
        f"font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'>{etiqueta}</span>"
    )
    return _caja(s, _img(_FLAG.format(pais), d, (s - d) / 2, 0, z=1) + badge)


def _nucleo(simbolo: str) -> str:
    """Nombre comparable: sin '...', '#', sufijos de bróker/bolsa ni 'Cash'/'micro'."""
    s = (simbolo or "").strip().replace("...", "").strip("#")
    base = s.split(".")[0]
    up = base.upper()
    up = re.sub(r"-[A-Z]{3}\d{2}$", "", up)        # futuros: WHEAT-DEC26 -> WHEAT
    up = re.sub(r"24-7$", "", up)                   # GOLD24-7 -> GOLD
    for suf in ("CASH", "MICRO"):
        if up.endswith(suf) and len(up) > len(suf):
            up = up[: -len(suf)]
    return up


# Sufijo de bolsa de XM/Reuters (RIC) -> sufijo de la fuente de logos.
# Bolsas de EE. UU. (OQ = Nasdaq, N = NYSE…) no llevan sufijo.
_BOLSA_SUFIJO = {
    "OQ": "", "O": "", "N": "", "A": "", "K": "", "P": "",
    "DE": ".DE", "F": ".F", "PA": ".PA", "L": ".L", "AS": ".AS", "MI": ".MI",
    "MC": ".MC", "SW": ".SW", "S": ".SW", "HK": ".HK", "T": ".T", "TO": ".TO",
    "ST": ".ST", "CO": ".CO", "HE": ".HE", "OL": ".OL", "BR": ".BR", "VI": ".VI",
    "LS": ".LS", "I": ".IR",
}
_BOLSAS_CLASE = {"ST", "CO", "HE", "OL"}   # nórdicas: clase de acción en minúscula

# Excepciones RIC -> ticker que ninguna regla puede deducir (sobre todo París:
# AXA = AXAF.PA en Reuters y CS.PA en bolsa). Hallazgo: probar variantes
# automáticas del RIC daba logos EQUIVOCADOS (AIRF.PA Air France -> AIR.PA
# Airbus; CAGR.PA Crédit Agricole -> CA.PA Carrefour), por eso van a mano.
_RIC_A_TICKER = {
    "AXAF.PA": "CS.PA", "BNPP.PA": "BNP.PA", "DANO.PA": "BN.PA", "LVMH.PA": "MC.PA",
    "OREP.PA": "OR.PA", "AIRP.PA": "AI.PA", "AIRF.PA": "AF.PA", "CARR.PA": "CA.PA",
    "CAGR.PA": "ACA.PA", "SGOB.PA": "SGO.PA", "ENGIE.PA": "ENGI.PA", "ORAN.PA": "ORA.PA",
    "PUBP.PA": "PUB.PA", "CAPP.PA": "CAP.PA", "ACCP.PA": "AC.PA", "ATOS.PA": "ATO.PA",
    "BOLL.PA": "BOL.PA", "HRMS.PA": "RMS.PA", "PRTP.PA": "KER.PA", "PERP.PA": "RI.PA",
    "LEGD.PA": "LR.PA", "DAST.PA": "DSY.PA", "MICP.PA": "ML.PA", "BOUY.PA": "EN.PA",
    "DIOR.PA": "CDI.PA", "ESLX.PA": "EL.PA", "ALSO.PA": "ALO.PA", "FOUG.PA": "FGR.PA",
    "JCDX.PA": "DEC.PA", "SASY.PA": "SAN.PA", "TTEF.PA": "TTE.PA", "SCHN.PA": "SU.PA",
    "RENA.PA": "RNO.PA", "SOGN.PA": "GLE.PA", "VIE.PA": "VIE.PA", "EUFI.PA": "ERF.PA",
    "LAGA.PA": "MMB.PA", "TEPRF.PA": "TEP.PA", "GETP.PA": "GET.PA", "EDEN.PA": "EDEN.PA",
    "SGEF.PA": "DG.PA", "TCFP.PA": "HO.PA", "VLOF.PA": "FR.PA", "UBIP.PA": "UBI.PA",
    "SOIT.PA": "SOI.PA", "EXHO.PA": "SW.PA", "SCOR.PA": "SCR.PA", "RCOP.PA": "RCO.PA",
    "ISOS.PA": "IPS.PA", "IMTP.PA": "NK.PA", "EURA.PA": "RF.PA", "CVO.PA": "COV.PA",
    "BIOX.PA": "BIM.PA", "BICP.PA": "BB.PA", "LTEN.PA": "ATE.PA", "RUBF.PA": "RUI.PA",
    "SESFd.PA": "SESG.PA", "MWDP.PA": "MF.PA", "GFCP.PA": "GFC.PA", "NEXS.PA": "NEX.PA",
    "LOIM.PA": "LI.PA", "CASP.PA": "CO.PA",
    # Xetra (DAX/MDAX): Reuters != ticker
    "BASFn.DE": "BAS.DE", "BAYGn.DE": "BAYN.DE", "EONGn.DE": "EOAN.DE", "MBGn.DE": "MBG.DE",
    "HNKG_p.DE": "HEN3.DE", "MRCG.DE": "MRK.DE", "DTEGn.DE": "DTE.DE", "SIEGn.DE": "SIE.DE",
    "ALVG.DE": "ALV.DE", "MUVGn.DE": "MUV2.DE", "DBKGn.DE": "DBK.DE", "CBKG.DE": "CBK.DE",
    "RWEG.DE": "RWE.DE", "SAPG.DE": "SAP.DE", "BMWG.DE": "BMW.DE", "IFXGn.DE": "IFX.DE",
    "DPWGn.DE": "DHL.DE", "DHLn.DE": "DHL.DE", "LHAG.DE": "LHA.DE", "HNRGn.DE": "HNR1.DE",
    "FREG.DE": "FRE.DE", "FMEG.DE": "FME.DE", "BEIG.DE": "BEI.DE", "CONG.DE": "CON.DE",
    "HEIG.DE": "HEI.DE", "PSHG_p.DE": "PAH3.DE", "ZALG.DE": "ZAL.DE", "DB1Gn.DE": "DB1.DE",
    "SY1G.DE": "SY1.DE", "PUMG.DE": "PUM.DE", "AIXGn.DE": "AIXA.DE", "NDXG.DE": "NDX1.DE",
    "FNTGn.DE": "FNTN.DE", "NAFG.DE": "NDA.DE", "LEGn.DE": "LEG.DE",
    "ERST.VI": "EBS.VI", "UNIQ.VI": "UQA.VI", "WBSV.VI": "WIE.VI", "TELA.VI": "TKA.VI",
    "CPIE.VI": "IIA.VI",
    "AGES.BR": "AGS.BR", "IETB.BR": "DIE.BR",
}
_BOLSAS_MENOS_UNA = {"VI", "HE"}   # Viena/Helsinki: el RIC agrega 1 letra (OMVV -> OMV)


def _ticker_logo(simbolo: str) -> str:
    """Código Reuters de XM -> ticker de la fuente de logos.
    NVDA.OQ -> NVDA · TU -> TU · ADSGn.DE -> ADS.DE · VOWG_p.DE -> VOW3.DE ·
    UHR.S -> UHR.SW · PEABb.ST -> PEAB-B.ST."""
    base, _, bolsa = (simbolo or "").partition(".")
    bolsa = bolsa.upper()
    pref = bool(re.search(r"_p$", base))                 # acción preferente
    base = re.sub(r"_[a-z]+$", "", base)
    if bolsa in ("DE", "F"):
        # Xetra: el RIC agrega 'G' (+ minúsculas): ADSGn -> ADS, VOWG -> VOW
        base = re.sub(r"[a-z]+$", "", base)
        if base.endswith("G") and len(base) > 2:
            base = base[:-1]
        if pref and not base[-1:].isdigit():
            base += "3"                                  # preferentes: VOW3, JUN3
    elif bolsa in _BOLSAS_CLASE and re.search(r"[a-z]$", base):
        base = base[:-1] + "-" + base[-1].upper()        # PEABb -> PEAB-B
    else:
        base = re.sub(r"[a-z]+$", "", base)
    return base + _BOLSA_SUFIJO.get(bolsa, "." + bolsa if bolsa else "")


_LOGO_OK: dict = {}        # símbolo -> url (acierto: se guarda para siempre)
_LOGO_FALLO: dict = {}     # símbolo -> instante del último fallo (se reintenta)
_REINTENTO_LOGO = 120      # s


def _url_existe(url: str, clave: str) -> str:
    """Devuelve `url` si responde como imagen, "" si no (misma caché que logos)."""
    if clave in _LOGO_OK:
        return _LOGO_OK[clave]
    if time.time() - _LOGO_FALLO.get(clave, 0) < _REINTENTO_LOGO:
        return ""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            if r.status == 200 and "image" in r.headers.get("Content-Type", ""):
                _LOGO_OK[clave] = url
                return url
    except Exception:
        pass
    _LOGO_FALLO[clave] = time.time()
    return ""


def _url_logo_accion(simbolo: str) -> str:
    """URL del logo de una acción/ETF ("" si la fuente no lo tiene). Un <img>
    sin logo se vería como imagen rota, por eso se verifica antes.
    Candidatos en orden: excepción conocida (_RIC_A_TICKER) o conversión del
    RIC; en Viena/Helsinki además el RIC sin la letra extra (OMVV.VI -> OMV.VI).
    Caché en _url_existe: aciertos permanentes, fallos reintentados cada 2 min
    (hallazgo: antes un fallo por demora en el arranque quedaba para siempre)."""
    ticker = _RIC_A_TICKER.get(simbolo) or _ticker_logo(simbolo)
    candidatos = [ticker]
    base, _, bolsa = ticker.partition(".")
    if bolsa in _BOLSAS_MENOS_UNA and simbolo not in _RIC_A_TICKER and len(base) > 2:
        candidatos.append(base[:-1] + "." + bolsa)
    for t in candidatos:
        url = _url_existe(_LOGO_ACCION.format(t), "logo:" + t)
        if url:
            return url
    return ""


def _logo(url: str, s: int) -> str:
    """Logo COMPLETO dentro de un círculo blanco (object-fit: contain + margen).
    Hallazgo: con 'cover' los logos apaisados (Adidas 128×86) se recortaban al
    centro y el círculo quedaba en blanco."""
    m = max(2, round(s * 0.14))
    return (
        f"<span style='position:absolute; inset:0; border-radius:50%; background:#ffffff; "
        f"overflow:hidden; display:flex; align-items:center; justify-content:center;'>"
        f"<img src='{url}' alt='' style='width:{s - 2 * m}px; height:{s - 2 * m}px; "
        f"object-fit:contain;'></span>"
    )


_INFO_CACHE: dict = {}


def _info_mt5(simbolo: str) -> tuple:
    """(carpeta, ric) del símbolo según MT5. carpeta = primer nivel de `path`
    ("Stocks", "ETF Derivatives", "Cryptocurrencies"…); ric = código entre
    paréntesis al final de la descripción ("Adidas AG (ADSGn.DE)" -> "ADSGn.DE",
    "Telus Corp (TU)" -> "TU"). ("", "") si no hay MT5.
    Hallazgo: XM nombra las acciones por la empresa ("Adidas", "Nvidia"), sin
    sufijo de bolsa; el código bursátil solo está en la descripción."""
    if simbolo in _INFO_CACHE:
        return _INFO_CACHE[simbolo]
    res = ("", "")
    try:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        from tools.mt5_bridge import MT5_LOCK, resolver_simbolo
        with MT5_LOCK:
            info = mt5.symbol_info(resolver_simbolo(simbolo))
        if info is not None:
            carpeta = (info.path or "").split(chr(92))[0]
            m = re.search(r"\(([A-Za-z0-9_]+(?:\.[A-Za-z]{1,3})?)\)\s*$", info.description or "")
            res = (carpeta, m.group(1) if m else "")
            _INFO_CACHE[simbolo] = res     # solo se guarda si MT5 respondió
    except Exception:
        pass
    return res


def _svg_iniciales(texto: str) -> str:
    """Círculo con iniciales como imagen (para combinarlo en _par)."""
    t = html.escape(re.sub(r"[^A-Za-z0-9]", "", texto)[:3].upper() or "?")
    color = _PALETA[zlib.crc32(texto.encode()) % len(_PALETA)]
    fs = 11 if len(t) <= 2 else 9
    figura = (f"<text x='16' y='16' text-anchor='middle' dominant-baseline='central' "
              f"font-family='Arial,sans-serif' font-weight='700' font-size='{fs}' fill='#fff'>{t}</text>")
    return _svg_circulo(color, figura)


def icono_activo(simbolo: str, size: int = 32) -> str:
    """HTML del ícono de un activo (ver reglas en el docstring del módulo)."""
    s = int(size)
    n = _nucleo(simbolo)

    # Materias primas (GOLD, XAUUSD, OILCash, NATGAS…)
    for clave, src in _MATERIAS.items():
        if n == clave or (len(clave) == 3 and n.startswith(clave) and len(n) == 6):
            return _caja(s, _img(src, s, 0, 0))

    # Índices (US30Cash, JP225Cash…)
    if n in _INDICES:
        pais, etiqueta = _INDICES[n]
        return _indice(pais, etiqueta, s)

    # Cripto (BTCUSD, ETHUSD…): logo + bandera de la moneda cotizada
    for cod, archivo in _CRIPTOS.items():
        if n.startswith(cod) and n[len(cod):] in _MONEDA_PAIS:
            return _par(_CRIPTO_URL.format(archivo),
                        _FLAG.format(_MONEDA_PAIS[n[len(cod):]]), s)

    # Divisas (6 letras = dos monedas conocidas)
    if len(n) == 6 and n[:3] in _MONEDA_PAIS and n[3:] in _MONEDA_PAIS:
        return _par(_FLAG.format(_MONEDA_PAIS[n[:3]]), _FLAG.format(_MONEDA_PAIS[n[3:]]), s)

    # Desde aquí se usa la carpeta y la descripción de MT5
    if "." in (simbolo or ""):
        carpeta, ric = "Stocks", simbolo
    else:
        carpeta, ric = _info_mt5(simbolo)

    # Cripto no listada (APTUSD, ARBUSD, ETHBTC…): logo si la librería lo
    # tiene (si no, iniciales) + bandera/logo de la moneda cotizada
    if carpeta == "Cryptocurrencies":
        for q in ("USD", "EUR", "GBP", "JPY", "BTC"):
            if n.endswith(q) and len(n) > len(q):
                cod = n[: -len(q)]
                src = (_url_existe(_CRIPTO_URL.format(cod.lower()), "cripto:" + cod)
                       or _svg_iniciales(cod))
                otro = (_CRIPTO_URL.format("btc") if q == "BTC"
                        else _FLAG.format(_MONEDA_PAIS[q]))
                return _par(src, otro, s)
        return _caja(s, _img(_GENERICO["cripto"], s, 0, 0))

    # Índices temáticos (AI_INDX, USD_FX_Index…): gráfico; los de divisas, su bandera
    if carpeta == "Thematic Indices":
        m = re.match(r"^([A-Z]{3})_FX_INDEX$", n)
        if m and m.group(1) in _MONEDA_PAIS:
            return _indice(_MONEDA_PAIS[m.group(1)], "FX", s)
        if "PRECIOUS" in n:
            return _caja(s, _img(_MATERIAS["GOLD"], s, 0, 0))
        return _caja(s, _img(_GENERICO["tematico"], s, 0, 0))

    # Acciones y ETFs: logo de la empresa/fondo si existe.
    # El código bursátil viene en el nombre (NVDA.OQ en otros brókers) o, en XM,
    # en la DESCRIPCIÓN de MT5: "Adidas AG (ADSGn.DE)", "Telus Corp (TU)".
    if ric:
        url = _url_logo_accion(ric)
        if url:
            return _caja(s, _logo(url, s))
    if carpeta.startswith("ETF"):
        return _caja(s, _img(_GENERICO["etf"], s, 0, 0))
    if carpeta == "Derivatives":
        return _caja(s, _img(_GENERICO["otro"], s, 0, 0))

    # Resto: iniciales en círculo de color estable
    return _caja(s, _iniciales(n, s))