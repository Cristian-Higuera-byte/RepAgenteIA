# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara gestor_alertas .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""Alertas de precio por usuario.

NOMBRE DEL ARCHIVO: herramientas/gestor_alertas.py

Cada usuario guarda sus alertas (activo, condición «mayor» o «menor» y nivel) en `alertas.json`, dentro de su carpeta de datos
(`data/usuarios/<id>/`), así que no se mezclan con las de otros usuarios y valen para su cuenta demo y su cuenta real. Los precios
salen del conector del bróker (`obtener_precio_actual`). Al cumplirse una alerta se deja un aviso en la campana (categoría
`alertas_precio` de Perfil > Notificaciones) y la alerta se desactiva. Las revisa `herramientas/avisos_usuario.py`.
"""
import json
import os
import tempfile
import threading
from datetime import datetime
from typing import Any

from herramientas import permisos_plan
from herramientas.backends import sesiones_capital
from herramientas.carpeta_usuario import carpeta_usuario
from herramientas.puente_mt5 import obtener_precio_actual
from nucleo_agente import notificaciones

# Nombre del archivo de alertas dentro de la carpeta del usuario.
NOMBRE_ARCHIVO = "alertas.json"
# Condiciones válidas: «mayor» avisa cuando el precio sube hasta el nivel; «menor», cuando baja hasta él.
CONDICIONES = ("mayor", "menor")
# Candado que serializa lecturas y escrituras del archivo dentro del proceso.
_CANDADO = threading.Lock()


# TITULO RUTA

def _ruta() -> str:
    """Ruta del archivo de alertas del usuario actual: su carpeta general (no la de demo o real, para que valgan en las dos cuentas)."""
    carpeta = carpeta_usuario()
    if len(sesiones_capital.clave_actual()) == 2:
        carpeta = os.path.dirname(carpeta)
    return os.path.join(carpeta, NOMBRE_ARCHIVO)


# TITULO CARGAR

def _cargar() -> list[dict[str, Any]]:
    """Lee las alertas del usuario; lista vacía si el archivo no existe o está dañado (nunca lanza excepción)."""
    try:
        with open(_ruta(), "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return datos if isinstance(datos, list) else []
    except Exception:  # noqa: BLE001 - sin archivo legible equivale a «sin alertas»
        return []


# TITULO GUARDAR

def _guardar(alertas: list[dict[str, Any]]) -> None:
    """Escribe la lista completa de alertas de forma atómica (archivo temporal y reemplazo) para no dejar el JSON a medias."""
    ruta = _ruta()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    descriptor, temporal = tempfile.mkstemp(dir=os.path.dirname(ruta), suffix=".tmp")
    with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
        json.dump(alertas, archivo, indent=2, ensure_ascii=False)
    os.replace(temporal, ruta)


# TITULO LISTAR ALERTAS

def listar_alertas(solo_activas: bool = True) -> list[dict[str, Any]]:
    """Alertas del usuario actual, de la más nueva a la más antigua; con `solo_activas` omite las que ya se dispararon."""
    with _CANDADO:
        alertas = _cargar()
    if solo_activas:
        alertas = [a for a in alertas if a.get("activa", True)]
    return list(reversed(alertas))


# TITULO PRECIO ACTUAL

def precio_actual(ticker: str) -> float | None:
    """Último precio del activo según el bróker, o None si no se pudo obtener."""
    try:
        dato = obtener_precio_actual(ticker)
    except Exception:  # noqa: BLE001 - sin precio no se puede evaluar
        return None
    if not isinstance(dato, dict) or dato.get("error"):
        return None
    valor = float(dato.get("last") or dato.get("bid") or 0.0)
    return valor or None


# TITULO CREAR ALERTA

def crear_alerta(ticker: str, condicion: str, valor_objetivo: float) -> tuple[bool, str]:
    """Registra una alerta nueva y devuelve (éxito, mensaje para el usuario).

    `condicion` es «mayor» (avisar cuando suba hasta el nivel), «menor» (cuando baje hasta él) o «auto», que la decide según el precio de
    ese momento: si el nivel está sobre el precio actual avisa al subir y si está bajo, al bajar. Valida el activo (debe tener precio en el
    bróker) y el nivel; rechaza la alerta si el precio ya cumple la condición (se dispararía de inmediato) o si el plan del usuario ya
    alcanzó su tope de alertas activas. Escribe el archivo de alertas."""
    ticker = (ticker or "").strip().upper()
    condicion = (condicion or "").strip().lower()
    if not ticker:
        return False, "Escribe el activo, por ejemplo EURUSD."
    if condicion not in CONDICIONES + ("auto",):
        return False, "Elige si quieres que avise cuando el precio suba o cuando baje."
    try:
        objetivo = float(valor_objetivo)
    except (TypeError, ValueError):
        objetivo = 0.0
    if objetivo <= 0:
        return False, "El nivel debe ser mayor que cero."
    actual = precio_actual(ticker)
    if actual is None:
        return False, f"No se encontró el precio de «{ticker}». Revisa el nombre del activo."
    if condicion == "auto":
        if objetivo == actual:
            return False, f"{ticker} ya cotiza en {actual:g}. Elige un nivel distinto del precio actual."
        condicion = "mayor" if objetivo > actual else "menor"
    if (condicion == "mayor" and actual >= objetivo) or (condicion == "menor" and actual <= objetivo):
        return False, f"{ticker} ya cotiza en {actual:g}: esa alerta se dispararía de inmediato. Elige otro nivel."
    with _CANDADO:
        alertas = _cargar()
        tope = permisos_plan.limite("alertas_precio_activas")
        if tope is not None and sum(1 for a in alertas if a.get("activa", True)) >= tope:
            return False, permisos_plan.mensaje_bloqueo("alertas_precio_activas") + " Quita alguna alerta antes de crear otra."
        alertas.append({
            "id": max((int(a.get("id", 0)) for a in alertas), default=0) + 1,
            "ticker": ticker,
            "condicion": condicion,
            "valor_objetivo": objetivo,
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activa": True,
        })
        _guardar(alertas)
    return True, f"Alerta creada: te avisaré cuando {ticker} {'suba a' if condicion == 'mayor' else 'baje a'} {objetivo:g}."


# TITULO ELIMINAR ALERTA

def eliminar_alerta(alerta_id: int) -> None:
    """Borra del archivo la alerta con ese id (no hace nada si no existe)."""
    with _CANDADO:
        _guardar([a for a in _cargar() if int(a.get("id", 0)) != int(alerta_id)])


# TITULO REVISAR ALERTAS

def revisar_alertas(usuario_id: str) -> int:
    """Compara las alertas activas del usuario con los precios actuales y avisa en la campana las que se cumplieron.

    Devuelve cuántas se dispararon. Una alerta solo se desactiva si el aviso se entregó: si el usuario apagó «Alertas de precio» en
    su perfil queda activa, para avisarle cuando vuelva a encenderlas. Efectos: lee precios del bróker y escribe el archivo."""
    with _CANDADO:
        alertas = _cargar()
        pendientes = [a for a in alertas if a.get("activa", True)]
        if not pendientes:
            return 0
        precios: dict[str, float | None] = {}
        disparadas = 0
        for alerta in pendientes:
            ticker = alerta["ticker"]
            if ticker not in precios:
                precios[ticker] = precio_actual(ticker)
            actual = precios[ticker]
            if actual is None:
                continue
            objetivo, sube = float(alerta["valor_objetivo"]), alerta["condicion"] == "mayor"
            if not ((sube and actual >= objetivo) or (not sube and actual <= objetivo)):
                continue
            aviso = notificaciones.agregar(
                usuario_id, f"Alerta de precio: {ticker}",
                f"{ticker} {'subió a' if sube else 'bajó a'} {actual:g} (tu nivel: {objetivo:g})",
                tipo="alerta", categoria="alertas_precio")
            if aviso["id"] is not None:
                alerta["activa"] = False
                alerta["fecha_disparo"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                disparadas += 1
        if disparadas:
            _guardar(alertas)
    return disparadas


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara gestor_alertas .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
