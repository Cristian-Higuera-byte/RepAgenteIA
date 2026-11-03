# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara utilidades .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Utilidades de la vigilancia: acceso a la base (vía nucleo_agente.ordenes), actualizar, notificar y finalizar.

Reutilizan la base SQLite del paquete ordenes para que ambas tablas compartan conexión y migraciones."""
from __future__ import annotations

import traceback
from datetime import datetime
from typing import Any

from nucleo_agente import notificaciones, ordenes


# TITULO ISO

def _iso(dt: datetime) -> str:
    """Convierte una fecha a texto ISO sin fracciones, el formato que se guarda y compara en SQLite."""
    return dt.isoformat(timespec="seconds")


# TITULO A NUMERO

def _a_numero(valor: Any) -> float | None:
    """Convierte a float un valor que el modelo pudo enviar como texto ('1,25'); devuelve None si no es un número
    (los booleanos, vacíos y None también dan None)."""
    if isinstance(valor, bool) or valor is None or valor == "":
        return None
    try:
        return float(str(valor).replace(",", ".")) if isinstance(valor, str) else float(valor)
    except (TypeError, ValueError):
        return None


# TITULO CONSULTAR

def _consultar(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Atajo a ordenes._consultar: ejecuta un SELECT y devuelve las filas como diccionarios."""
    return ordenes._consultar(sql, params)


# TITULO ACTUALIZAR

def _actualizar(vid: str, **campos: Any) -> None:
    """Actualiza columnas de una vigilancia por id con los campos recibidos por nombre (no hace nada si no hay).
    Los nombres de columna son fijos del código; los valores van como parámetros."""
    if not campos:
        return
    # Se arma "col = ?, col2 = ?" y los valores viajan como parámetros.
    asignaciones = ", ".join(f"{c} = ?" for c in campos)
    ordenes._ejecutar(f"UPDATE vigilancias SET {asignaciones} WHERE id = ?", (*campos.values(), vid))


# TITULO OBTENER

def obtener(vid: str) -> dict[str, Any] | None:
    """Devuelve la fila de la vigilancia con ese id como diccionario, o None si no existe."""
    filas = _consultar("SELECT * FROM vigilancias WHERE id = ?", (vid,))
    return filas[0] if filas else None


# TITULO NOTIFICAR

def _notificar(v: dict[str, Any], titulo: str, texto: str, tipo: str = "auto") -> None:
    """Agrega una notificación (campana) al usuario dueño de la vigilancia, referida a su id.

    Cualquier fallo se imprime y se ignora para que avisar nunca detenga al motor."""
    try:
        notificaciones.agregar(v["usuario_id"], titulo, texto, tipo=tipo, ref=v["id"])
    except Exception:  # noqa: BLE001 - un fallo al avisar nunca debe tumbar el motor
        traceback.print_exc()


# TITULO LADO TEXTO

def _lado_texto(lado: str) -> str:
    """Devuelve "Compra" o "Venta" con mayúscula inicial para los títulos de notificación."""
    return "Compra" if str(lado).lower() == "compra" else "Venta"


# TITULO FINALIZAR

def _finalizar(v: dict[str, Any], estado: str, titulo: str, texto: str, tipo: str = "auto") -> None:
    """Cierra una vigilancia: guarda el estado final y el detalle (máx. 300 caracteres) y notifica al usuario."""
    _actualizar(v["id"], estado=estado, detalle=texto[:300])
    _notificar(v, titulo, texto, tipo=tipo)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara utilidades .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
