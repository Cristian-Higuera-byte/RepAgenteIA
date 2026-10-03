"""
simbolos.py
-----------
Catálogo de símbolos de MT5 (XM) y su equivalencia con Yahoo Finance.
Lógica PURA: no importa MetaTrader5 ni yfinance. El catálogo se construye con
filas (dicts) que entrega fuentes.py, así que es fácil de probar.

Reglas de diseño (basadas en el diagnóstico real de tu servidor XM):
  * La ruta de cada símbolo ('Stocks\\EU\\Italy\\A2A') define su categoría.
  * Las acciones traen el código RIC en la descripción: 'A2A SpA (A2.MI)'.
  * El RIC NO siempre coincide con el ticker de Yahoo (A2.MI vs A2A.MI,
    ADSGn.DE vs ADS.DE). Ante la duda NO se adivina: se devuelve ticker=None y
    el candidato aparte. Un ticker equivocado podría traer OTRA empresa.
  * Correcciones manuales: MAPA_MANUAL (abajo) o data/simbolos_override.json.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Iterable, Optional

OVERRIDE_PATH = os.path.join("data", "simbolos_override.json")   # {"A2A": "A2A.MI"}
MODO_TRADING_COMPLETO = 4                                         # SYMBOL_TRADE_MODE_FULL

# Equivalencias verificadas contra el diagnóstico de tu servidor.
MAPA_MANUAL: dict[str, str] = {
    "GOLD": "GC=F", "OILCash": "CL=F", "BRENTCash": "BZ=F", "NGASCash": "NG=F",
    "AUS200Cash": "^AXJO", "A2A": "A2A.MI",
}
_NOTA_FUTURO = "Yahoo entrega el futuro continuo; MT5 el CFD cash/spot: pueden diferir por vencimiento."
NOTAS_MANUAL: dict[str, str] = {
    "GOLD": "Yahoo GC=F es el futuro del oro, no el spot: puede diferir de MT5 en unos dólares.",
    "OILCash": _NOTA_FUTURO, "BRENTCash": _NOTA_FUTURO, "NGASCash": _NOTA_FUTURO,
}

# Sufijo RIC (Reuters) -> sufijo Yahoo.  '' = EE. UU. (sin sufijo en Yahoo).
_RIC_A_YAHOO: dict[str, str] = {
    "N": "", "O": "", "OQ": "", "A": "", "K": "",
    "L": ".L", "PA": ".PA", "DE": ".DE", "MI": ".MI", "MC": ".MC", "AS": ".AS",
    "BR": ".BR", "LS": ".LS", "ST": ".ST", "CO": ".CO", "HE": ".HE", "OL": ".OL",
    "VI": ".VI", "TO": ".TO", "S": ".SW",
}

# Español -> inglés para buscar en descripciones (que vienen en inglés).
_ALIAS = {"oro": "gold", "plata": "silver", "petroleo": "oil", "crudo": "oil",
          "dolar": "dollar", "libra": "pound", "franco": "franc", "indice": "index"}

_RE_RIC = re.compile(r"\(([A-Za-z0-9._&\-]+)\)\s*$")


# ----------------------------------------------------------------- Utilidades
def _norm(texto: str) -> str:
    s = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


def cargar_overrides(ruta: str = OVERRIDE_PATH) -> dict[str, str]:
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return {str(k): str(v) for k, v in datos.items()} if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def extraer_ric(descripcion: str) -> Optional[str]:
    m = _RE_RIC.search((descripcion or "").strip())
    return m.group(1) if m else None


def clasificar(ruta: str) -> dict:
    """Categoría, clase de activo (para anualizar volatilidad) y región según la ruta MT5."""
    partes = [p for p in (ruta or "").split("\\") if p]
    top = partes[0] if partes else ""
    medio = partes[1:-1]
    region = "/".join(medio) if top in ("Stocks", "Turbo Stocks") else None
    if top == "Stocks":
        cat, clase = "acciones", "accion"
    elif top == "Turbo Stocks":
        cat, clase = "turbo", "accion"
    elif top == "ETF Derivatives":
        cat, clase = "etf", "accion"
    elif top == "Cryptocurrencies":
        cat, clase = "cripto", "cripto"
    elif top == "Forex":
        cat, clase = "forex", "forex"
    elif top == "Thematic Indices":
        cat, clase = "indices_tematicos", "indice"
    elif top == "Derivatives":
        texto = " ".join(medio).lower()
        if "metal" in texto:
            cat, clase = "metales", "commodity"
        elif "energ" in texto:
            cat, clase = "energia", "commodity"
        elif "indic" in texto:
            cat, clase = "indices", "indice"
        else:
            cat, clase = "derivados_otros", "commodity"
    else:
        cat, clase = "otro", "otro"
    return {"categoria": cat, "clase": clase, "region": region, "grupo_mt5": top}


def _t(ticker, confianza, motivo, nota=None, candidato=None) -> dict:
    return {"ticker": ticker, "confianza": confianza, "motivo": motivo,
            "nota": nota, "candidato": candidato}


def ticker_yahoo(nombre: str, descripcion: str, ruta: str,
                 overrides: Optional[dict[str, str]] = None) -> dict:
    """Equivalente en Yahoo de un símbolo MT5.

    confianza: 'manual' | 'alta' | 'media' | 'ninguna'. Con 'ninguna', ticker=None.
    """
    ov = overrides or {}
    if nombre in ov:
        return _t(ov[nombre], "manual", "override del usuario")
    if nombre in MAPA_MANUAL:
        return _t(MAPA_MANUAL[nombre], "manual", "mapa verificado", NOTAS_MANUAL.get(nombre))

    cat = clasificar(ruta)["categoria"]
    if cat == "forex":
        if re.fullmatch(r"[A-Z]{6}", nombre):
            return _t(f"{nombre}=X", "alta", "par de divisas")
        return _t(None, "ninguna", "nombre de forex no estándar")
    if cat == "cripto":
        if re.fullmatch(r"[A-Z0-9]{2,10}USD", nombre):
            return _t(f"{nombre[:-3]}-USD", "media",
                      "par cripto/USD (algunas monedas usan otro ticker en Yahoo)")
        return _t(None, "ninguna", "cripto sin par USD estándar")
    if cat in ("acciones", "turbo", "etf"):
        ric = extraer_ric(descripcion)
        if not ric:
            return _t(None, "ninguna", "sin código RIC en la descripción")
        nota = ("Variante 'Turbo' de XM: condiciones propias, no asumas que replica "
                "el CFD estándar.") if cat == "turbo" else None
        if cat == "etf":
            if re.fullmatch(r"[A-Z]{1,5}", ric):
                return _t(ric, "alta", "ETF de EE. UU.")
            return _t(None, "ninguna", f"ETF con código no estándar '{ric}'")
        root, punto, suf = ric.rpartition(".")
        if not punto:
            root, suf = ric, ""
        if punto and suf not in _RIC_A_YAHOO:
            return _t(None, "ninguna", f"sufijo RIC '.{suf}' sin equivalencia conocida", nota)
        ysuf = _RIC_A_YAHOO.get(suf, "")
        if not re.fullmatch(r"[A-Z0-9]{1,6}", root):
            return _t(None, "ninguna",
                      f"código '{ric}' ambiguo (minúsculas o símbolos: clase de acción "
                      "o código distinto en Yahoo)", nota, candidato=root.upper() + ysuf)
        if ysuf == ".L":
            nota = ((nota + " ") if nota else "") + \
                "Yahoo cotiza Londres en peniques (GBX); MT5 puede usar libras."
        confianza = "alta" if (ysuf == "" and punto) else "media"
        return _t(root + ysuf, confianza, f"RIC {ric} -> Yahoo", nota)
    return _t(None, "ninguna", "sin equivalencia verificada; agrégala en data/simbolos_override.json")


# ----------------------------------------------------------------- Catálogo
_RANGO_CONF = {"manual": 0, "alta": 1, "media": 2, "ninguna": 9}


class Catalogo:
    """Catálogo en memoria de los símbolos del servidor MT5."""

    def __init__(self, filas: Iterable[dict], overrides: Optional[dict[str, str]] = None):
        ov = cargar_overrides() if overrides is None else overrides
        self._reg: dict[str, dict] = {}
        for f in filas:
            nombre = f["nombre"]
            desc = f.get("descripcion", "") or ""
            ruta = f.get("ruta", "") or ""
            cls = clasificar(ruta)
            y = ticker_yahoo(nombre, desc, ruta, ov)
            reg = {**f, **cls, "ric": extraer_ric(desc),
                   "yahoo": y["ticker"], "yahoo_confianza": y["confianza"],
                   "yahoo_nota": y["nota"], "yahoo_motivo": y["motivo"],
                   "yahoo_candidato": y["candidato"],
                   "operable": f.get("modo_trading") == MODO_TRADING_COMPLETO,
                   "_nom": _norm(nombre), "_txt": _norm(f"{nombre} {desc}")}
            self._reg[nombre] = reg
        self._ci = {n.lower(): n for n in self._reg}
        self._por_yahoo: dict[str, str] = {}
        mejor: dict[str, tuple] = {}
        for nombre, r in self._reg.items():
            if not r["yahoo"]:
                continue
            clave = r["yahoo"].upper()
            puntaje = (r["categoria"] == "turbo", _RANGO_CONF[r["yahoo_confianza"]], nombre)
            if clave not in mejor or puntaje < mejor[clave]:
                mejor[clave] = puntaje
                self._por_yahoo[clave] = nombre

    def __len__(self) -> int:
        return len(self._reg)

    def obtener(self, nombre: str) -> Optional[dict]:
        real = self._ci.get((nombre or "").strip().lower())
        return self._reg.get(real) if real else None

    def por_yahoo(self, ticker: str) -> Optional[str]:
        return self._por_yahoo.get((ticker or "").strip().upper())

    @staticmethod
    def publico(reg: dict) -> dict:
        return {k: v for k, v in reg.items() if not k.startswith("_")}

    def resumen(self) -> dict:
        cats: dict[str, int] = {}
        conf: dict[str, int] = {}
        for r in self._reg.values():
            cats[r["categoria"]] = cats.get(r["categoria"], 0) + 1
            conf[r["yahoo_confianza"]] = conf.get(r["yahoo_confianza"], 0) + 1
        return {"total": len(self._reg), "por_categoria": cats, "equivalencia_yahoo": conf}

    # ---- búsqueda
    def _variantes(self, texto: str) -> list[str]:
        q = _norm(texto)
        var = [q]
        trad = " ".join(_ALIAS.get(t, t) for t in q.split())
        if trad != q:
            var.append(trad)
        return var

    @staticmethod
    def _puntuar(q: str, reg: dict) -> int:
        nom, txt = reg["_nom"], reg["_txt"]
        if not q:
            return 0
        if q == nom:
            s = 100
        else:
            pats = [re.compile(r"\b" + re.escape(t)) for t in q.split()]
            if nom.startswith(q):
                s = 85
            elif all(p.search(nom) for p in pats):
                s = 70
            elif all(p.search(txt) for p in pats):
                s = 55
            else:
                return 0
        return s - (15 if reg["categoria"] == "turbo" else 0)

    def buscar(self, consulta: str, categoria: Optional[str] = None, clase: Optional[str] = None,
               solo_operables: bool = False, limite: int = 10) -> list[dict]:
        variantes = self._variantes(consulta)
        res = []
        for r in self._reg.values():
            if categoria and r["categoria"] != categoria:
                continue
            if clase and r["clase"] != clase:
                continue
            if solo_operables and not r["operable"]:
                continue
            s = max(self._puntuar(v, r) for v in variantes)
            if s > 0:
                res.append((s, r))
        res.sort(key=lambda x: (-x[0], len(x[1]["nombre"]), x[1]["nombre"]))
        return [{"nombre": r["nombre"], "descripcion": r["descripcion"], "categoria": r["categoria"],
                 "clase": r["clase"], "digitos": r["digitos"], "operable": r["operable"],
                 "yahoo": r["yahoo"], "puntaje": s} for s, r in res[:max(1, limite)]]

    def resolver(self, texto: str) -> tuple[Optional[str], str, list[dict]]:
        """(nombre_mt5 | None, motivo, sugerencias). No adivina si hay ambigüedad."""
        texto = (texto or "").strip()
        if not texto:
            return None, "entrada vacía", []
        r = self.obtener(texto)
        if r:
            return r["nombre"], "nombre exacto en MT5", []
        n = self.por_yahoo(texto)
        if n:
            return n, f"equivalente MT5 del ticker Yahoo {texto.upper()}", []
        sug = self.buscar(texto, limite=5)
        if sug:
            top = sug[0]["puntaje"]
            segundo = sug[1]["puntaje"] if len(sug) > 1 else 0
            if top >= 85 or (top >= 55 and top - segundo >= 10):
                return sug[0]["nombre"], "mejor coincidencia por nombre/descripción", sug
        return None, "sin coincidencia única", sug