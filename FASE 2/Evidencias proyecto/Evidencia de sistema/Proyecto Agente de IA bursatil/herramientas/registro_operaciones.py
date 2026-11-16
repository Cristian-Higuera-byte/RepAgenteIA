# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara registro_operaciones .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""Registro de las operaciones y del equity de cada usuario en Supabase (base del copy trading).

Qué hace: copia al servidor, para el usuario y la cuenta (demo o real) actuales, lo que el bróker informa: las posiciones abiertas, las operaciones
ya cerradas con su detalle y una foto periódica del balance y del equity. Se guarda en las tablas `operaciones` y `equity_historial` (esquema en
`herramientas/sql/copytrading.sql`). Con eso se calculan después las métricas de una estrategia y se pueden replicar sus operaciones.

Cómo funciona:
  - `sincronizar()` hace una pasada completa y devuelve un resumen. Es idempotente: cada operación del bróker se guarda una sola vez (clave
    usuario + cuenta + id del bróker) y repetir la pasada no duplica nada. Una operación abierta que ya estaba registrada solo actualiza su stop
    loss y take profit; al cerrarse pasa a «cerrada» con precio de cierre, hora y resultado.
  - `sincronizar_en_segundo_plano()` la lanza en un hilo (sin frenar la pantalla) y la limita a una pasada por minuto y usuario; `forzar=True` baja
    la espera a 5 segundos (por ejemplo, justo después de ejecutar una orden). La pantalla de Trading la llama a cada refresco.
  - `anotar_origen()` deja constancia de quién abrió una posición (`manual`, `agente` o `copia`); sin anotación se asume `manual`.
Solo trabaja en modo multiusuario y con Supabase configurado; en cualquier otro caso no hace nada. Nunca lanza excepciones: ante un fallo devuelve
el motivo en el resumen y lo intenta de nuevo en la pasada siguiente.
Límites conocidos: el equity al abrir de una posición es el del primer momento en que la plataforma la vio; los depósitos y retiros todavía no se
descuentan (`flujo_neto` queda en 0); las operaciones cerradas que Capital.com no detalla se reintentan en las pasadas siguientes.
"""
import json
import os
import threading
import time
from datetime import datetime, timezone

from herramientas import gestor_autenticacion
from herramientas.backends import sesiones_capital
from herramientas.carpeta_usuario import carpeta_de
from herramientas.hilos import lanzar_hilo
from herramientas.puente_mt5 import PROVEEDOR, detalle_cierre, obtener_historial, obtener_info_cuenta, obtener_posiciones

# Nombres de las tablas de Supabase
_TABLA = "operaciones"
_TABLA_EQUITY = "equity_historial"
# Segundos mínimos entre dos pasadas del mismo usuario (normal y con `forzar`)
_ESPERA_S = 60.0
_ESPERA_FORZADA_S = 5.0
# Cada cuántos segundos se guarda una foto del equity aunque no haya cierres
_FOTO_CADA_S = 900.0
# Días de historial que se leen la primera vez y en las pasadas siguientes, y máximo de cierres que se detallan por pasada
_DIAS_PRIMERA_VEZ = 60
_DIAS_NORMAL = 7
_MAX_CIERRES_POR_PASADA = 30
# Cuántos identificadores se consultan por pedido a Supabase
_LOTE = 100
# Estado por usuario y cuenta: {"ultimo": hora de la última pasada, "foto": hora de la última foto, "corre": hay una pasada en curso}
_ESTADO: dict = {}
_CANDADO = threading.Lock()
# Último mensaje de error mostrado (para no repetirlo en cada pasada)
_ultimo_error = [""]
# Orígenes anotados de las posiciones: {(usuario, cuenta): {ticket: origen}}
_ORIGENES: dict = {}
_ORIGENES_VALIDOS = ("manual", "agente", "copia")
# Traducción de los tipos de instrumento de Capital.com
_TIPOS_ACTIVO = {"INDICES": "Índices", "CURRENCIES": "Forex", "SHARES": "Acciones", "CRYPTOCURRENCIES": "Criptomonedas",
                 "COMMODITIES": "Materias primas", "BONDS": "Bonos", "OPT_RATES": "Tasas", "ETFS": "ETF"}


# TITULO CONTEXTO

def _contexto():
    """Devuelve (cliente de Supabase, id de usuario, tipo de cuenta "demo"/"real") del usuario actual, o None si no se puede registrar
    (modo de un solo usuario, sin sesión o sin Supabase)."""
    clave = sesiones_capital.clave_actual()
    cliente = gestor_autenticacion._supabase
    if not sesiones_capital.MULTIUSUARIO or len(clave) != 2 or cliente is None:
        return None
    return cliente, int(clave[0]), "demo" if clave[1] else "real"


# TITULO FECHA ISO

def _iso(epoch) -> str | None:
    """Fecha y hora UTC en texto ISO a partir de un epoch en segundos (None si no hay)."""
    try:
        return datetime.fromtimestamp(float(epoch), timezone.utc).isoformat() if epoch else None
    except (TypeError, ValueError, OverflowError, OSError):
        return None


# TITULO ARCHIVO DE ORIGENES

def _ruta_origenes() -> str:
    """Archivo donde se guarda el origen anotado de las posiciones del usuario y la cuenta actuales."""
    return os.path.join(carpeta_de(sesiones_capital.clave_actual()), "origenes_operaciones.json")


# TITULO ANOTAR ORIGEN

def anotar_origen(ticket, origen: str) -> None:
    """Anota quién abrió la posición `ticket` (id del bróker): "manual", "agente" o "copia". Se guarda en memoria y en un archivo del usuario, para
    que la próxima pasada de `sincronizar` lo use aunque la plataforma se reinicie. Un origen inválido o un ticket vacío se ignoran."""
    if origen not in _ORIGENES_VALIDOS or not ticket:
        return
    clave = sesiones_capital.clave_actual()
    with _CANDADO:
        mapa = _ORIGENES.setdefault(clave, _leer_origenes())
        mapa[str(ticket)] = origen
        try:
            ruta = _ruta_origenes()
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta + ".tmp", "w", encoding="utf-8") as f:
                json.dump(mapa, f)
            os.replace(ruta + ".tmp", ruta)
        except OSError:
            pass


# TITULO LEER ORIGENES

def _leer_origenes() -> dict:
    """Orígenes anotados guardados en el archivo del usuario ({} si no hay o está dañado)."""
    try:
        with open(_ruta_origenes(), "r", encoding="utf-8") as f:
            datos = json.load(f)
        return {str(k): v for k, v in datos.items() if v in _ORIGENES_VALIDOS} if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


# TITULO ORIGEN DE

def origen_de(ticket) -> str:
    """Origen anotado de la posición `ticket` ("manual" si nadie lo anotó)."""
    clave = sesiones_capital.clave_actual()
    with _CANDADO:
        mapa = _ORIGENES.get(clave)
        if mapa is None:
            mapa = _ORIGENES[clave] = _leer_origenes()
        return mapa.get(str(ticket), "manual")


# TITULO DATOS DEL INSTRUMENTO

def _datos_instrumento(epic: str) -> tuple:
    """Devuelve (tipo de activo en español, apalancamiento) del instrumento `epic`; (None, None) si el bróker no lo informa.

    Solo con Capital.com: el tipo sale del tipo de instrumento y el apalancamiento del margen requerido (100 ÷ porcentaje de margen)."""
    if PROVEEDOR != "capital" or not epic:
        return None, None
    try:
        from herramientas.backends.capital_nucleo import obtener_mercado
        instrumento = (obtener_mercado(epic) or {}).get("instrument", {}) or {}
        tipo = _TIPOS_ACTIVO.get(str(instrumento.get("type", "")).upper()) or (str(instrumento.get("type", "")).title() or None)
        margen = float(instrumento.get("marginFactor") or 0)
        return tipo, (int(round(100.0 / margen)) if margen > 0 else None)
    except Exception:  # noqa: BLE001 - un dato de apoyo no debe frenar el registro
        return None, None


# TITULO EXISTENTES

def _existentes(cliente, usuario: int, cuenta: str, ids: list) -> dict:
    """Consulta a Supabase qué operaciones de `ids` (ids del bróker) ya están registradas. Devuelve {id_broker: fila con estado, stop_loss y take_profit}."""
    salida: dict = {}
    for i in range(0, len(ids), _LOTE):
        filas = (cliente.table(_TABLA).select("id_broker,estado,stop_loss,take_profit").eq("usuario_id", usuario).eq("cuenta_tipo", cuenta)
                 .in_("id_broker", [str(x) for x in ids[i:i + _LOTE]]).execute().data or [])
        salida.update({f["id_broker"]: f for f in filas})
    return salida


# TITULO FILA ABIERTA

def _fila_abierta(p: dict, usuario: int, cuenta: str, equity: float | None) -> dict | None:
    """Fila de `operaciones` para una posición abierta del bróker (None si le faltan datos básicos)."""
    volumen = float(p.get("volumen") or 0)
    if volumen <= 0 or not p.get("ticket") or not p.get("symbol"):
        return None
    tipo_activo, apalancamiento = _datos_instrumento(p["symbol"])
    return {"usuario_id": usuario, "cuenta_tipo": cuenta, "id_broker": str(p["ticket"]), "simbolo": p["symbol"], "tipo_activo": tipo_activo,
            "lado": "compra" if p.get("tipo") == "Compra" else "venta", "volumen": volumen, "precio_apertura": float(p.get("precio_apertura") or 0),
            "abierta_en": _iso(p.get("tiempo")) or _iso(time.time()), "stop_loss": float(p.get("sl") or 0) or None,
            "take_profit": float(p.get("tp") or 0) or None, "equity_apertura": equity, "apalancamiento": apalancamiento,
            "estado": "abierta", "origen": origen_de(p["ticket"])}


# TITULO SINCRONIZAR POSICIONES

def _sincronizar_posiciones(cliente, usuario: int, cuenta: str, equity: float | None, resumen: dict) -> None:
    """Registra las posiciones abiertas nuevas y actualiza el stop loss y el take profit de las que ya estaban. Suma al `resumen` las nuevas."""
    posiciones = [p for p in (obtener_posiciones() or []) if p.get("ticket")]
    if not posiciones:
        return
    registradas = _existentes(cliente, usuario, cuenta, [p["ticket"] for p in posiciones])
    nuevas = []
    for p in posiciones:
        previa = registradas.get(str(p["ticket"]))
        if previa is None:
            fila = _fila_abierta(p, usuario, cuenta, equity)
            if fila:
                nuevas.append(fila)
        elif previa.get("estado") == "abierta":
            sl, tp = float(p.get("sl") or 0) or None, float(p.get("tp") or 0) or None
            if (sl or 0) != float(previa.get("stop_loss") or 0) or (tp or 0) != float(previa.get("take_profit") or 0):
                cliente.table(_TABLA).update({"stop_loss": sl, "take_profit": tp, "actualizado_en": _iso(time.time())}) \
                    .eq("usuario_id", usuario).eq("cuenta_tipo", cuenta).eq("id_broker", str(p["ticket"])).execute()
    if nuevas:
        cliente.table(_TABLA).insert(nuevas).execute()
        resumen["nuevas"] += len(nuevas)


# TITULO SINCRONIZAR CIERRES

def _sincronizar_cierres(cliente, usuario: int, cuenta: str, resumen: dict) -> None:
    """Registra como cerradas las operaciones que el bróker ya cerró: actualiza las que estaban abiertas en la base y agrega las que no se vieron
    abiertas. Detalla como máximo `_MAX_CIERRES_POR_PASADA` por pasada; el resto queda para la siguiente. Suma al `resumen` las cerradas."""
    primera_vez = not (cliente.table(_TABLA).select("id").eq("usuario_id", usuario).eq("cuenta_tipo", cuenta).limit(1).execute().data or [])
    historial = [h for h in (obtener_historial(dias=_DIAS_PRIMERA_VEZ if primera_vez else _DIAS_NORMAL, limite=200) or []) if h.get("deal_id")]
    if not historial:
        return
    registradas = _existentes(cliente, usuario, cuenta, [h["deal_id"] for h in historial])
    pendientes = [h for h in historial if registradas.get(str(h["deal_id"]), {}).get("estado") != "cerrada"][:_MAX_CIERRES_POR_PASADA]
    for h in pendientes:
        d = detalle_cierre(h["deal_id"], h.get("fecha", 0)) or {}
        volumen, entrada, salida = float(d.get("volumen") or 0), float(d.get("entrada") or 0), float(d.get("salida") or 0)
        if volumen <= 0 or not entrada or not salida or d.get("tipo") not in ("Compra", "Venta"):
            continue                                   # Capital todavía no detalla esta operación: se reintenta en la próxima pasada
        cierre = _iso(h.get("fecha"))
        datos_cierre = {"estado": "cerrada", "precio_cierre": salida, "cerrada_en": cierre, "resultado": round(float(h.get("pg") or 0), 2),
                        "actualizado_en": _iso(time.time())}
        if str(h["deal_id"]) in registradas:
            cliente.table(_TABLA).update(datos_cierre).eq("usuario_id", usuario).eq("cuenta_tipo", cuenta).eq("id_broker", str(h["deal_id"])).execute()
        else:
            tipo_activo, apalancamiento = _datos_instrumento(d.get("epic", ""))
            cliente.table(_TABLA).insert({
                "usuario_id": usuario, "cuenta_tipo": cuenta, "id_broker": str(h["deal_id"]), "simbolo": d.get("epic") or h.get("symbol", ""),
                "tipo_activo": tipo_activo, "lado": "compra" if d["tipo"] == "Compra" else "venta", "volumen": volumen, "precio_apertura": entrada,
                "abierta_en": _iso(d.get("hora_in")) or cierre, "apalancamiento": apalancamiento, "origen": origen_de(h["deal_id"]), **datos_cierre}).execute()
        resumen["cerradas"] += 1


# TITULO FOTO DE EQUITY

def _foto_equity(cliente, usuario: int, cuenta: str, info: dict, clave: tuple, resumen: dict, hubo_cierres: bool) -> None:
    """Guarda una foto del balance y el equity si pasó el tiempo definido (`_FOTO_CADA_S`) o si hubo cierres en esta pasada."""
    ahora = time.time()
    estado = _ESTADO.setdefault(clave, {})
    if not hubo_cierres and ahora - estado.get("foto", 0.0) < _FOTO_CADA_S:
        return
    cliente.table(_TABLA_EQUITY).insert({"usuario_id": usuario, "cuenta_tipo": cuenta, "balance": round(float(info.get("balance") or 0), 2),
                                         "equity": round(float(info.get("equity") or 0), 2), "flujo_neto": 0}).execute()
    estado["foto"] = ahora
    resumen["foto"] = True


# TITULO SINCRONIZAR

def sincronizar() -> dict:
    """Hace una pasada completa de registro para el usuario y la cuenta actuales y devuelve un resumen.

    Devuelve {"nuevas": operaciones abiertas registradas, "cerradas": operaciones cerradas registradas o actualizadas, "foto": si guardó una
    foto del equity, "omitida": motivo si no hizo nada (sin Supabase, modo de un solo usuario o ya hay una pasada en curso), "error": texto si
    falló}. No lanza excepciones."""
    resumen = {"nuevas": 0, "cerradas": 0, "foto": False}
    contexto = _contexto()
    if contexto is None:
        resumen["omitida"] = "sin Supabase o sin modo multiusuario"
        return resumen
    cliente, usuario, cuenta = contexto
    clave = (usuario, cuenta)
    with _CANDADO:
        estado = _ESTADO.setdefault(clave, {})
        if estado.get("corre"):
            resumen["omitida"] = "ya hay una pasada en curso"
            return resumen
        estado["corre"] = True
        estado["ultimo"] = time.time()
    try:
        info = obtener_info_cuenta() or {}
        if "error" in info:
            resumen["omitida"] = "sin conexión con el bróker"
            return resumen
        _sincronizar_posiciones(cliente, usuario, cuenta, round(float(info.get("equity") or 0), 2) or None, resumen)
        _sincronizar_cierres(cliente, usuario, cuenta, resumen)
        _foto_equity(cliente, usuario, cuenta, info, clave, resumen, resumen["cerradas"] > 0)
        _ultimo_error[0] = ""
        if resumen["nuevas"] or resumen["cerradas"]:
            try:
                from herramientas import copiador
                copiador.despertar()          # el motor de copy trading replica enseguida lo que acaba de registrarse
            except Exception:  # noqa: BLE001
                pass
    except Exception as e:  # noqa: BLE001 - el registro nunca debe romper la plataforma
        resumen["error"] = str(e)[:200]
        if resumen["error"] != _ultimo_error[0]:
            _ultimo_error[0] = resumen["error"]
            print(f"[REGISTRO] No se pudo registrar las operaciones: {resumen['error']}")
    finally:
        with _CANDADO:
            _ESTADO[clave]["corre"] = False
    return resumen


# TITULO SINCRONIZAR EN SEGUNDO PLANO

def sincronizar_en_segundo_plano(forzar: bool = False) -> bool:
    """Lanza `sincronizar` en un hilo si ya pasó la espera desde la última pasada del usuario (60 s; 5 s con `forzar`). Devuelve True si lanzó el
    hilo. Es barata de llamar en cada refresco de la pantalla: casi siempre solo comprueba la hora."""
    contexto = _contexto()
    if contexto is None:
        return False
    clave = (contexto[1], contexto[2])
    with _CANDADO:
        estado = _ESTADO.setdefault(clave, {})
        if estado.get("corre") or time.time() - estado.get("ultimo", 0.0) < (_ESPERA_FORZADA_S if forzar else _ESPERA_S):
            return False
        estado["ultimo"] = time.time()
    lanzar_hilo(sincronizar, nombre="registro-operaciones")
    return True



# -------------------------------------------------------------------------------------------------------
# ------------------------------ FIN Piña y Jara registro_operaciones .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
