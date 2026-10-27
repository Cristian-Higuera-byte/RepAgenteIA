# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara permisos_plan .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Qué puede hacer cada usuario según su plan: consulta de límites y funciones, con mensajes listos para mostrar.

La tabla de funciones y valores de cada plan (Gratis, Básico, Pro y Avanzado) vive en `herramientas/plan_funciones.json`: allí está el
catálogo de funciones (nombre, categoría, tipo y si ya se aplica o está por aplicar) y el valor de cada una en cada plan. Los tokens del
agente y los precios salen de `PLANES_IA` en `configuracion.py`. Este módulo solo lee esa tabla y la entrega:

  - `valor(funcion)` / `limite(funcion)` / `permite(funcion)`: lo que permite el plan actual (`limite` devuelve None si no hay tope);
  - `plan_minimo(funcion)`: el primer plan que la incluye (para decir «disponible desde el plan Pro»);
  - `mensaje_bloqueo(funcion)`: el texto que se le muestra al usuario cuando topa con un límite;
  - `exigir(funcion)`: lanza `ErrorPlan` si el plan no la permite;
  - `para_grafico()`: los límites que necesita el gráfico (se le inyectan al abrirlo).

El plan del usuario sale de `herramientas/cuota_ia.py` (`plan_actual`): en multiusuario viene de Supabase y en modo local de un archivo.
"""
import json
import os

import configuracion
from herramientas import cuota_ia

# Ruta de la tabla de funciones por plan y su caché (se relee solo si el archivo cambia)
_RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan_funciones.json")
_CACHE: dict = {"firma": None, "datos": {}}


# TITULO ERROR PLAN

class ErrorPlan(Exception):
    """Se lanza al usar una función que el plan del usuario no incluye o cuyo límite ya se alcanzó. El mensaje ya es legible."""


# TITULO MATRIZ

def matriz() -> dict:
    """Tabla completa de funciones y planes ({"categorias", "funciones", "planes"}), leída del JSON con caché (se relee si el archivo cambia)."""
    firma = os.stat(_RUTA).st_mtime_ns
    if _CACHE["firma"] != firma:
        with open(_RUTA, "r", encoding="utf-8") as f:
            _CACHE.update(firma=firma, datos=json.load(f))
    return _CACHE["datos"]


# TITULO FUNCION

def funcion(clave: str) -> dict | None:
    """Ficha de la función `clave` del catálogo (nombre, categoría, tipo, estado y descripción), o None si no existe."""
    return next((f for f in matriz()["funciones"] if f["clave"] == clave), None)


# TITULO VALOR

def valor(clave: str, plan: str | None = None):
    """Valor de la función `clave` en el `plan` (por defecto el del usuario actual): un número, verdadero/falso, una lista o un texto.

    Los tokens del mes salen de `configuracion.PLANES_IA`. Una función desconocida devuelve None."""
    plan = plan or cuota_ia.plan_actual()
    if clave == "tokens_mes":
        return configuracion.PLANES_IA[plan]["tokens_mes"]
    return matriz()["planes"].get(plan, {}).get(clave)


# TITULO LIMITE

def limite(clave: str, plan: str | None = None):
    """Tope numérico de la función `clave` en el plan, o None si no tiene tope (o la función no es numérica)."""
    v = valor(clave, plan)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


# TITULO PERMITE

def permite(clave: str, plan: str | None = None) -> bool:
    """True si el plan incluye la función: verdadero/falso afirmativo, número mayor que cero, o lista/texto no vacíos."""
    v = valor(clave, plan)
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v > 0
    return bool(v)


# TITULO PLAN MINIMO

def plan_minimo(clave: str) -> str | None:
    """Clave del primer plan (en el orden Gratis → Avanzado) que incluye la función, o None si ninguno."""
    return next((p for p in configuracion.PLANES_IA if permite(clave, p)), None)


# TITULO NOMBRE PLAN

def nombre_plan(plan: str | None) -> str:
    """Nombre visible del plan (por ejemplo «Pro»); cadena vacía si la clave no existe."""
    return configuracion.PLANES_IA.get(plan or "", {}).get("nombre", "")


# TITULO SIGUIENTE PLAN

def siguiente_plan_con_mas(clave: str, plan: str | None = None) -> str | None:
    """Primer plan por encima del actual cuyo valor de `clave` mejora al del actual (más cantidad o la función incluida); None si ya está en el tope."""
    plan = plan or cuota_ia.plan_actual()
    orden = list(configuracion.PLANES_IA)
    actual = valor(clave, plan)
    for p in orden[orden.index(plan) + 1:]:
        v = valor(clave, p)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if v > (actual if isinstance(actual, (int, float)) and not isinstance(actual, bool) else 0):
                return p
        elif v and not actual:
            return p
        elif isinstance(v, list) and isinstance(actual, list) and len(v) > len(actual):
            return p
    return None


# TITULO MENSAJE BLOQUEO

def mensaje_bloqueo(clave: str, plan: str | None = None) -> str:
    """Texto para el usuario cuando topa con un límite o una función que su plan no incluye.

    Dice qué incluye su plan y desde qué plan hay más (o la función), por ejemplo «Tu plan Gratis permite 3 indicadores por gráfico; desde
    el plan Básico puedes usar 5.»"""
    plan = plan or cuota_ia.plan_actual()
    f = funcion(clave) or {"nombre": clave}
    nombre_actual = nombre_plan(plan)
    superior = siguiente_plan_con_mas(clave, plan)
    v, unidad = valor(clave, plan), f.get("unidad", "")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
        base = f"Tu plan {nombre_actual} permite {v:,.0f} {unidad}".replace(",", ".")
        if superior:
            return f"{base}; desde el plan {nombre_plan(superior)} puedes usar {valor(clave, superior):,.0f}.".replace(",", ".")
        return base + "."
    if superior:
        return f"«{f['nombre']}» no está incluido en el plan {nombre_actual}; está disponible desde el plan {nombre_plan(superior)}."
    return f"«{f['nombre']}» no está disponible en tu plan."


# TITULO EXIGIR

def exigir(clave: str) -> None:
    """Lanza `ErrorPlan` con el mensaje de bloqueo si el plan del usuario no incluye la función `clave`; no hace nada si la incluye."""
    if not permite(clave):
        raise ErrorPlan(mensaje_bloqueo(clave))


# TITULO PARA GRAFICO

def para_grafico(plan: str | None = None) -> dict:
    """Límites y funciones que necesita el gráfico del usuario (se inyectan al armar su HTML).

    Devuelve {"plan", "indicadores", "comparar", "backtest_velas", "replay", "mensajes": {...}} con los textos de bloqueo ya escritos, para que el
    gráfico (JavaScript) los muestre sin conocer los planes."""
    plan = plan or cuota_ia.plan_actual()
    return {
        "plan": nombre_plan(plan),
        "indicadores": limite("indicadores_por_grafico", plan), "comparar": limite("comparar_simbolos", plan),
        "backtest_velas": limite("backtest_velas", plan), "replay": permite("replay", plan),
        "mensajes": {"indicadores": mensaje_bloqueo("indicadores_por_grafico", plan), "comparar": mensaje_bloqueo("comparar_simbolos", plan),
                     "backtest_velas": mensaje_bloqueo("backtest_velas", plan), "replay": mensaje_bloqueo("replay", plan)},
    }


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara permisos_plan .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
