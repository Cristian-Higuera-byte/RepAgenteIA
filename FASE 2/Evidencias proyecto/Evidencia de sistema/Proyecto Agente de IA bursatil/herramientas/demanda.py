# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara demanda .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Registro y análisis de la PRUEBA DE DEMANDA de los planes: cuánta gente mira los planes, cuál elige y a qué precio.

La página de Planes todavía no cobra nada: cada clic en «Quiero este plan» es una señal de interés. Este módulo guarda esas señales y las
resume. Cada evento es una línea de `data/demanda.jsonl` (un solo archivo para toda la plataforma, solo se agrega al final) con la hora, el
usuario, el tipo de evento (`vista_planes`, `clic_plan`, `plan_activado`, `encuesta`, `lista_espera`), el plan, el precio que se le mostró, la variante de
precio y desde dónde llegó (`menu`, `barra_cuota` o `cuota_agotada`).

Para comparar precios, cada usuario recibe SIEMPRE la misma variante (calculada con su identificador), de modo que se puede ver qué precio
genera más clics. El correo solo se guarda si el usuario marca que quiere que le avisen. Las cifras son de intención, no de ventas: un clic
no es un pago.
"""
import hashlib
import json
import os
import threading
import time

from herramientas import carpeta_usuario

# Archivo único con todos los eventos de la prueba (en la carpeta data/ de la raíz del proyecto)
_ARCHIVO = os.path.join(carpeta_usuario._DATOS, "demanda.jsonl")
# Candado de las escrituras dentro del proceso
_CANDADO = threading.Lock()
# Tipos de evento válidos
EVENTOS = ("vista_planes", "clic_plan", "plan_activado", "encuesta", "lista_espera")
# Rangos de precio justo que ofrece la encuesta, en el orden en que se muestran
RANGOS_PRECIO = ["Menos de 5 USD", "5 a 10 USD", "10 a 20 USD", "20 a 40 USD", "Más de 40 USD"]
# Qué es lo que más interesa del plan, para la encuesta
MOTIVOS = ["Más consultas al agente", "Vigilancias automáticas", "Backtest ampliado", "Modelo avanzado", "Soporte prioritario"]


# TITULO VARIANTE DE

def variante_de(usuario_id, cantidad: int) -> int:
    """Variante de precio (0 a cantidad − 1) que le toca al usuario: siempre la misma para el mismo usuario.

    Se calcula con un resumen del identificador, así los usuarios se reparten parejo entre las variantes. Sin identificador (o con una sola
    variante) devuelve 0."""
    if cantidad <= 1 or usuario_id in (None, ""):
        return 0
    return int(hashlib.sha1(str(usuario_id).encode("utf-8")).hexdigest(), 16) % cantidad


# TITULO REGISTRAR

def registrar(evento: str, usuario, plan: str = "", precio: float = 0.0, variante: int = 0, origen: str = "", **extra) -> None:
    """Guarda un evento de la prueba de demanda. `extra` admite datos propios del evento (por ejemplo `correo`, `precio_justo`, `motivo`).

    Ignora los eventos de un tipo desconocido. Nunca lanza excepciones: medir no debe romper la página."""
    if evento not in EVENTOS:
        return
    try:
        linea = {"t": int(time.time()), "evento": evento, "usuario": usuario, "plan": plan, "precio": float(precio), "variante": int(variante),
                 "origen": origen, **extra}
        os.makedirs(os.path.dirname(_ARCHIVO), exist_ok=True)
        with _CANDADO:
            with open(_ARCHIVO, "a", encoding="utf-8") as f:
                f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


# TITULO LEER

def leer(desde: float = 0.0) -> list:
    """Devuelve los eventos con hora igual o posterior a `desde` (marca de tiempo en segundos). Ignora las líneas dañadas."""
    salida = []
    try:
        with open(_ARCHIVO, "r", encoding="utf-8") as f:
            for linea in f:
                try:
                    e = json.loads(linea)
                except ValueError:
                    continue
                if isinstance(e, dict) and float(e.get("t", 0) or 0) >= desde:
                    salida.append(e)
    except OSError:
        return []
    return salida


# TITULO CLAVE USUARIO

def _clave(e: dict) -> str:
    """Identificador de la persona de un evento (los usuarios sin identificador cuentan como uno solo, «anonimo»)."""
    return str(e.get("usuario") if e.get("usuario") not in (None, "") else "anonimo")


# TITULO RESUMIR

def resumir(eventos: list, planes: dict, conversion_a_pago: float = 0.1) -> dict:
    """Resume la prueba de demanda contando PERSONAS distintas (no clics repetidos).

    `planes` es `configuracion.PLANES_IA` y `conversion_a_pago` la fracción de los interesados que se supone que terminaría pagando.
    Devuelve:
      - "visitantes": personas que vieron la página de Planes;
      - "interesados": personas que hicieron clic en algún plan de pago;
      - "lista_espera": personas que pidieron que les avisen;
      - "por_plan": {plan: {"clics", "tasa" (clics sobre visitantes), "espera", "precio_medio" (de los clics)}};
      - "por_variante": {(plan, variante): {"precio", "visitantes", "clics", "tasa"}}, con los visitantes de esa variante;
      - "por_origen": {origen: clics distintos};
      - "precio_justo" y "motivo": {opción: personas} de la encuesta (la última respuesta de cada persona);
      - "ingreso_potencial": suma de (último precio de cada clic) × `conversion_a_pago`, en USD al mes."""
    visitantes = {}                  # persona -> variante con la que entró
    clics: dict = {}                 # (persona, plan) -> evento más reciente
    espera: dict = {}                # (persona, plan) -> evento
    encuestas: dict = {}             # persona -> evento más reciente
    for e in sorted(eventos, key=lambda x: x.get("t", 0)):
        p, tipo = _clave(e), e.get("evento")
        if tipo == "vista_planes":
            visitantes[p] = int(e.get("variante", 0) or 0)
        elif tipo == "clic_plan" and e.get("plan") in planes and e.get("plan") != "gratis":
            clics[(p, e["plan"])] = e
            visitantes.setdefault(p, int(e.get("variante", 0) or 0))
        elif tipo == "lista_espera":
            espera[(p, e.get("plan", ""))] = e
        elif tipo == "encuesta":
            encuestas[p] = e
    n_visitantes = len(visitantes)
    por_plan, por_variante, por_origen = {}, {}, {}
    for clave in planes:
        if clave == "gratis":
            continue
        de_plan = [e for (p, pl), e in clics.items() if pl == clave]
        por_plan[clave] = {"clics": len(de_plan), "tasa": (len(de_plan) / n_visitantes * 100.0) if n_visitantes else 0.0,
                           "espera": sum(1 for (p, pl) in espera if pl == clave),
                           "precio_medio": (sum(float(e.get("precio", 0) or 0) for e in de_plan) / len(de_plan)) if de_plan else 0.0}
        for v, precio in enumerate(planes[clave].get("precios", [])):
            vis = sum(1 for var in visitantes.values() if var == v)
            c = sum(1 for e in de_plan if int(e.get("variante", 0) or 0) == v)
            por_variante[(clave, v)] = {"precio": float(precio), "visitantes": vis, "clics": c, "tasa": (c / vis * 100.0) if vis else 0.0}
    for e in clics.values():
        origen = e.get("origen") or "menu"
        por_origen[origen] = por_origen.get(origen, 0) + 1
    precio_justo, motivo = {}, {}
    for e in encuestas.values():
        if e.get("precio_justo"):
            precio_justo[e["precio_justo"]] = precio_justo.get(e["precio_justo"], 0) + 1
        if e.get("motivo"):
            motivo[e["motivo"]] = motivo.get(e["motivo"], 0) + 1
    interesados = {p for (p, _pl) in clics}
    return {"visitantes": n_visitantes, "interesados": len(interesados), "lista_espera": len({p for (p, _pl) in espera}),
            "por_plan": por_plan, "por_variante": por_variante, "por_origen": dict(sorted(por_origen.items())),
            "precio_justo": precio_justo, "motivo": motivo,
            "ingreso_potencial": sum(float(e.get("precio", 0) or 0) for e in clics.values()) * conversion_a_pago}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara demanda .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
