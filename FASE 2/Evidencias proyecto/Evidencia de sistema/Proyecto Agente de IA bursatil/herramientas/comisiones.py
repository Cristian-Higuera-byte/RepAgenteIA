# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara comisiones .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Comisión de rendimiento del copy trading: cuánto debe pagar el seguidor al gestor y el cobro con la billetera virtual.

Reglas:
  - La comisión es un porcentaje (el de la estrategia, entre 0 y 30 %) de la GANANCIA NUEVA de la copia: la suma de los resultados de sus operaciones, por encima de su
    marca de agua. La marca de agua (`copias.marca_agua`) es la mayor ganancia sobre la que ya se cobró; así nunca se cobra dos veces la misma ganancia, ni hay comisión
    mientras la copia no recupere sus pérdidas.
  - Se liquida cada `liquidacion_dias` días (30) desde el alta o desde la liquidación anterior, y una vez más al detener la copia (cuando ya no tiene posiciones abiertas
    o pasaron 10 minutos).
  - El pago pasa dinero de la billetera virtual del seguidor a la del gestor en una sola operación (`billetera.transferir`, con una clave por liquidación: repetir no duplica).
    Si el seguidor no tiene saldo, la comisión queda pendiente, la copia se pausa (motivo `comision_pendiente`) y el motor reintenta en cada pasada; al cobrarse se reanuda sola.
  - Cada liquidación queda en `comisiones_rendimiento` (ganancia, marca de agua antes y después, porcentaje, comisión y el movimiento de billetera con el que se pagó).
Limitación: las posiciones que el seguidor deja abiertas al detener la copia no entran en la comisión final; lo que cierren después ya no se liquida.
"""
from datetime import datetime, timedelta, timezone

import configuracion
from herramientas import billetera

_TABLA = "comisiones_rendimiento"
# Minutos que se espera a que se cierren las posiciones de una copia detenida antes de liquidar su comisión final
_ESPERA_FINAL_MIN = 10


# TITULO AHORA

def _ahora() -> datetime:
    """Fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


# TITULO A FECHA

def _fecha(valor) -> datetime | None:
    """Convierte un texto ISO de Supabase en datetime con zona horaria; None si no se puede."""
    try:
        f = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
        return f if f.tzinfo else f.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


# TITULO A NUMERO

def _n(valor, defecto: float = 0.0) -> float:
    """Convierte a número (Supabase puede entregar los numéricos como texto); `defecto` si está vacío o es inválido."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


# TITULO CALCULAR

def calcular(ganancia: float, marca_agua: float, porcentaje: float) -> tuple:
    """Devuelve (ganancia nueva, comisión): la parte de `ganancia` que supera la `marca_agua` y el `porcentaje` % de ella redondeado a centavos. (0, 0) si no la supera."""
    base = max(0.0, ganancia - marca_agua)
    return round(base, 2), round(base * porcentaje / 100.0, 2)


# TITULO GANANCIA DE LA COPIA

def ganancia_de(cliente, copia_id) -> float:
    """Ganancia acumulada de la copia: suma de los resultados de sus operaciones que ya tienen resultado (cerradas)."""
    filas = cliente.table("operaciones").select("resultado").eq("copia_id", copia_id).execute().data or []
    return round(sum(_n(f["resultado"]) for f in filas if f.get("resultado") is not None), 2)


# TITULO PENDIENTE

def pendiente(cliente, copia_id) -> float:
    """Total de comisiones de la copia que todavía no se cobraron."""
    filas = cliente.table(_TABLA).select("comision,movimiento_billetera_id").eq("copia_id", copia_id).execute().data or []
    return round(sum(_n(f["comision"]) for f in filas if f.get("movimiento_billetera_id") is None and _n(f["comision"]) > 0), 2)


# TITULO PAGAR

def _pagar(cliente, copia: dict, estrategia: dict, fila: dict) -> bool:
    """Intenta cobrar la comisión de la liquidación `fila` pasando el dinero de la billetera del seguidor a la del gestor. Devuelve True si quedó cobrada."""
    try:
        movimiento = billetera.transferir(copia["inversor_id"], estrategia["gestor_id"], _n(fila["comision"]), f"Comisión de rendimiento · {estrategia['nombre']}",
                                          f"Comisión de rendimiento · {estrategia['nombre']}", referencia=str(copia["id"]), clave_unica=f"comision-{fila['id']}")
    except billetera.ErrorBilletera:
        return False
    cliente.table(_TABLA).update({"movimiento_billetera_id": movimiento}).eq("id", fila["id"]).execute()
    cliente.table("copias").update({"marca_agua": max(_n(copia.get("marca_agua")), _n(fila["marca_agua_despues"]))}).eq("id", copia["id"]).execute()
    copia["marca_agua"] = max(_n(copia.get("marca_agua")), _n(fila["marca_agua_despues"]))
    return True


# TITULO COBRAR PENDIENTES

def cobrar_pendientes(cliente, copia: dict, estrategia: dict) -> float:
    """Intenta cobrar las comisiones pendientes de la copia. Si ya no queda nada pendiente y la copia estaba pausada por eso, la reanuda. Devuelve lo que sigue pendiente."""
    filas = cliente.table(_TABLA).select("*").eq("copia_id", copia["id"]).order("id").execute().data or []
    for f in filas:
        if f.get("movimiento_billetera_id") is None and _n(f["comision"]) > 0:
            _pagar(cliente, copia, estrategia, f)
    queda = pendiente(cliente, copia["id"])
    if queda <= 0 and copia.get("estado") == "pausada" and copia.get("motivo_cierre") == "comision_pendiente":
        cliente.table("copias").update({"estado": "activa", "motivo_cierre": None}).eq("id", copia["id"]).execute()
        copia.update({"estado": "activa", "motivo_cierre": None})
    return queda


# TITULO ULTIMO PERIODO

def _ultimo_corte(cliente, copia: dict) -> datetime:
    """Fecha desde la que corre el periodo actual: la de la última liquidación o, si no hay, la del alta de la copia."""
    fila = (cliente.table(_TABLA).select("periodo_hasta").eq("copia_id", copia["id"]).order("periodo_hasta", desc=True).limit(1).execute().data or [None])[0]
    return (_fecha(fila["periodo_hasta"]) if fila else None) or _fecha(copia.get("creada_en")) or _ahora()


# TITULO DEBE LIQUIDAR

def _toca_liquidar(cliente, copia: dict, ahora: datetime) -> bool:
    """True si a la copia le toca una liquidación: la mensual (cada `liquidacion_dias` días) o la final de una copia detenida."""
    if copia["estado"] == "cerrada":
        if copia.get("comision_final_en"):
            return False
        cerrada = _fecha(copia.get("cerrada_en")) or ahora
        abiertas = cliente.table("operaciones").select("id").eq("copia_id", copia["id"]).eq("estado", "abierta").limit(1).execute().data or []
        return not abiertas or ahora >= cerrada + timedelta(minutes=_ESPERA_FINAL_MIN)
    return ahora - _ultimo_corte(cliente, copia) >= timedelta(days=configuracion.COPYTRADING["liquidacion_dias"])


# TITULO REVISAR

def revisar(cliente, copia: dict, estrategia: dict, ahora: datetime | None = None) -> dict:
    """Revisa la comisión de una copia: cobra lo pendiente y, si toca, hace la liquidación (mensual o final) y la cobra.

    Devuelve {"liquidada": bool, "comision": lo liquidado ahora, "pendiente": lo que queda por cobrar}. Si la comisión no se pudo cobrar y la copia estaba activa,
    la pausa con el motivo `comision_pendiente`."""
    ahora = ahora or _ahora()
    resumen = {"liquidada": False, "comision": 0.0, "pendiente": cobrar_pendientes(cliente, copia, estrategia)}
    if not _toca_liquidar(cliente, copia, ahora):
        return resumen
    ganancia, marca = ganancia_de(cliente, copia["id"]), _n(copia.get("marca_agua"))
    _, comision = calcular(ganancia, marca, _n(estrategia.get("comision_pct")))
    nueva_marca = max(ganancia, marca)
    fila = {"copia_id": copia["id"], "periodo_desde": _ultimo_corte(cliente, copia).isoformat(), "periodo_hasta": ahora.isoformat(), "ganancia_acumulada": ganancia, "marca_agua_antes": marca,
            "marca_agua_despues": nueva_marca, "comision_pct": _n(estrategia.get("comision_pct")), "comision": comision}
    try:
        fila = (cliente.table(_TABLA).insert(fila).execute().data or [fila])[0]
    except Exception:  # noqa: BLE001 - ya existía esa liquidación
        return resumen
    resumen.update({"liquidada": True, "comision": comision})
    if comision <= 0:
        cliente.table("copias").update({"marca_agua": nueva_marca}).eq("id", copia["id"]).execute()
        copia["marca_agua"] = nueva_marca
    elif not _pagar(cliente, copia, estrategia, fila):
        resumen["pendiente"] = pendiente(cliente, copia["id"])
        if copia["estado"] == "activa":
            cliente.table("copias").update({"estado": "pausada", "motivo_cierre": "comision_pendiente"}).eq("id", copia["id"]).execute()
            copia.update({"estado": "pausada", "motivo_cierre": "comision_pendiente"})
    if copia["estado"] == "cerrada":
        cliente.table("copias").update({"comision_final_en": ahora.isoformat()}).eq("id", copia["id"]).execute()
        copia["comision_final_en"] = ahora.isoformat()
    resumen["pendiente"] = pendiente(cliente, copia["id"])
    return resumen



# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara comisiones .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
