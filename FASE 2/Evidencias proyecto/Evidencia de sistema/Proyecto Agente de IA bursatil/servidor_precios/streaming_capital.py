# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara streaming_capital .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""
streaming_capital.py  —  Precios en vivo de Capital.com por WebSocket  —  16-10-2026
------------------------------------------------------------------------------------
Mantiene UNA conexión WebSocket a Capital.com POR USUARIO Y CUENTA (demo o real) y guarda el último Bid/Ask de cada
instrumento suscrito en una caché en memoria. `stream_de(clave)` entrega el de cada cuenta; cada uno usa los tokens de
su propia sesión (nunca los de otro) y se detiene con `detener_stream(clave)`. El motor de precios
(servidor_precios/motor/base.py) lee de esa caché en vez de preguntar por REST en
cada ciclo, lo que elimina decenas de llamadas por segundo y hace fluida la app.

Diseño:
  - Corre en un hilo daemon con su propio bucle asyncio (websockets).
  - Reutiliza la sesión REST del usuario (copia del núcleo en herramientas/backends/sesiones_capital.py) para los
    tokens CST / X-SECURITY-TOKEN. El sondeo de cuenta del motor mantiene esa sesión
    viva, así que los tokens no caducan.
  - Reconecta solo ante errores/cierres, re-autenticando y re-suscribiendo.
  - Ping cada 5 min (el límite de Capital es 10) para mantener el stream vivo.
  - Máximo 40 instrumentos (límite de Capital).

Solo se usa con PROVEEDOR=capital; el motor no lo arranca con MT5.
"""
from __future__ import annotations

import asyncio
import collections
import json
import threading
import time
from types import SimpleNamespace
from typing import Optional

from herramientas.backends import sesiones_capital

_WS_URL = "wss://api-streaming-capital.backend-capital.com/connect"
_MAX_EPICS = 40
_PING_S = 300            # ping cada 5 min (límite de Capital: 10)
_BACKOFF_S = 3           # espera antes de reconectar


# TITULO STREAM CAPITAL

class _StreamCapital:
    """Conexión WebSocket con Capital.com que recibe las cotizaciones en vivo (bid, ask y cantidades) y las guarda en memoria.

    El motor de precios lee de aquí en vez de consultar REST; el servidor de datos la usa también para el DOM de nivel 1.
    """
    # TITULO INIT

    def __init__(self, clave: tuple = ("legado",)) -> None:
        """Crea los diccionarios de cotizaciones y de cinta, los conjuntos de epics deseados/suscritos y el candado; el hilo se arranca al primer `suscribir`.

        `clave` es la cuenta a la que pertenece este stream: (usuario_id, es_demo), o ("legado",) para la cuenta del .env."""
        self._clave = clave
        self._parar = False
        self._cache: dict = {}          # epic -> {"bid","ask","t"(ms),"bq","aq"}
        self._cinta: dict = {}          # epic -> deque de las últimas cotizaciones (cinta del panel DOM)
        self._deseados: set = set()     # epics que queremos suscribir
        self._suscritos: set = set()    # epics ya suscritos en la conexión actual
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws = None
        self._hilo: Optional[threading.Thread] = None

    # TITULO CUENTA

    def _cuenta(self):
        """Copia del núcleo de Capital de la cuenta de este stream (sesión, tokens y credenciales propios).

        Se pide cada vez para que, si el usuario cambia sus credenciales, el stream use la sesión nueva."""
        return sesiones_capital.modulo_de(self._clave)

    # TITULO DETENER

    def detener(self) -> None:
        """Detiene el stream: cierra la conexión y evita que el hilo vuelva a reconectar."""
        self._parar = True
        if self._ws is not None and self._loop is not None:
            asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)

    # TITULO SUSCRIBIR

    # ---- API pública (la usa el motor, desde su hilo) --------------------
    def suscribir(self, epics) -> None:
        """Pide que estos epics estén suscritos (arranca el hilo WS si hace falta)."""
        nuevos = False
        with self._lock:
            for e in epics:
                if e and e not in self._deseados and len(self._deseados) < _MAX_EPICS:
                    self._deseados.add(e)
                    nuevos = True
        self._asegurar_hilo()
        if nuevos and self._loop is not None:
            asyncio.run_coroutine_threadsafe(self._suscribir_pendientes(), self._loop)

    # TITULO DOM

    def dom(self, epic: str) -> dict:
        """Nivel 1 del libro (mejor bid/ask y la cantidad disponible en cada uno) + cinta de las últimas
        cotizaciones. Capital.com no publica más niveles. Suscribe el epic si aún no lo estaba."""
        self.suscribir([epic])
        d = self._cache.get(epic)
        if not d:
            return {"disponible": False, "motivo": "Sin cotización todavía (esperando el streaming)."}
        return {"disponible": True, "epic": epic, "bid": d["bid"], "ask": d["ask"],
                "bq": d.get("bq", 0.0), "aq": d.get("aq", 0.0), "t": d["t"],
                "cinta": list(self._cinta.get(epic, []))}

    # TITULO TICK

    def tick(self, epic: str):
        """Último tick del epic como objeto estilo MT5 (bid, ask, last, time, time_msc), o None."""
        d = self._cache.get(epic)
        if not d:
            return None
        return SimpleNamespace(
            bid=d["bid"], ask=d["ask"], last=d["bid"] or d["ask"],
            time=int(d["t"] / 1000), time_msc=int(d["t"]),
        )

    # TITULO ASEGURAR HILO

    # ---- hilo + bucle asyncio --------------------------------------------
    def _asegurar_hilo(self) -> None:
        """Arranca el hilo del WebSocket si aún no está corriendo."""
        if self._hilo and self._hilo.is_alive():
            return
        self._parar = False
        self._hilo = threading.Thread(target=self._run, name=f"capital-ws-{'-'.join(map(str, self._clave))}", daemon=True)
        self._hilo.start()

    # TITULO RUN

    def _run(self) -> None:
        """Cuerpo del hilo: crea el bucle asyncio y ejecuta la conexión hasta que termine."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._principal())
        except Exception as e:  # noqa: BLE001
            print(f"[WS Capital] bucle terminó: {e}")

    # TITULO PRINCIPAL

    async def _principal(self) -> None:
        """Bucle de la conexión: se conecta, suscribe los epics pendientes, procesa los mensajes y mantiene el ping; si se corta, espera y reconecta."""
        import websockets  # import tardío: solo si se usa el streaming
        while not self._parar:
            try:
                if not self._cuenta().inicializar_mt5():
                    await asyncio.sleep(5)
                    continue
                # ping_interval=None: Capital usa ping de APLICACIÓN, no el del protocolo WS.
                async with websockets.connect(_WS_URL, ping_interval=None,
                                              open_timeout=15, close_timeout=5) as ws:
                    self._ws = ws
                    with self._lock:
                        self._suscritos.clear()
                    await self._suscribir_pendientes()
                    tarea_ping = asyncio.create_task(self._ping_loop(ws))
                    try:
                        async for mensaje in ws:
                            self._procesar(mensaje)
                    finally:
                        tarea_ping.cancel()
            except Exception as e:  # noqa: BLE001
                print(f"[WS Capital] reconectando tras: {type(e).__name__}: {e}")
            self._ws = None
            if self._parar:
                return
            await asyncio.sleep(_BACKOFF_S)

    # TITULO SUSCRIBIR PENDIENTES

    async def _suscribir_pendientes(self) -> None:
        """Envía a Capital la suscripción de los epics deseados que aún no estén suscritos (hasta el máximo permitido)."""
        if self._ws is None:
            return
        with self._lock:
            faltan = list(self._deseados - self._suscritos)
        if not faltan:
            return
        try:
            await self._ws.send(json.dumps({
                "destination": "marketData.subscribe",
                "correlationId": str(int(time.time())),
                "cst": self._cuenta()._tokens["CST"],
                "securityToken": self._cuenta()._tokens["X-SECURITY-TOKEN"],
                "payload": {"epics": faltan[:_MAX_EPICS]},
            }))
            with self._lock:
                self._suscritos.update(faltan)
        except Exception as e:  # noqa: BLE001
            print(f"[WS Capital] no se pudo suscribir: {e}")

    # TITULO PING LOOP

    async def _ping_loop(self, ws) -> None:
        """Envía un ping cada pocos minutos para que Capital no cierre la conexión por inactividad."""
        while True:
            await asyncio.sleep(_PING_S)
            try:
                await ws.send(json.dumps({
                    "destination": "ping",
                    "correlationId": str(int(time.time())),
                    "cst": self._cuenta()._tokens["CST"],
                    "securityToken": self._cuenta()._tokens["X-SECURITY-TOKEN"],
                }))
            except Exception:
                return

    # TITULO PROCESAR

    def _procesar(self, mensaje) -> None:
        """Interpreta un mensaje del WebSocket: si es una cotización, actualiza el último precio y cantidades del epic y agrega una entrada a su cinta cuando cambia algo."""
        try:
            d = json.loads(mensaje)
        except Exception:
            return
        if d.get("destination") != "quote":
            return
        p = d.get("payload") or {}
        epic = p.get("epic")
        if not epic:
            return
        bid = p.get("bid")
        ofr = p.get("ofr")
        nuevo = {
            "bid": float(bid) if bid is not None else 0.0,
            "ask": float(ofr) if ofr is not None else 0.0,
            "t": int(p.get("timestamp") or time.time() * 1000),
            "bq": float(p.get("bidQty") or 0.0),
            "aq": float(p.get("ofrQty") or 0.0),
        }
        previo = self._cache.get(epic)
        self._cache[epic] = nuevo
        # Cinta: solo cuando cambia el precio o la cantidad (máx. 40 entradas por epic).
        if not previo or (previo["bid"], previo["ask"], previo["bq"], previo["aq"]) != (
                nuevo["bid"], nuevo["ask"], nuevo["bq"], nuevo["aq"]):
            cinta = self._cinta.setdefault(epic, collections.deque(maxlen=40))
            cinta.append({"t": nuevo["t"], "b": nuevo["bid"], "a": nuevo["ask"],
                          "bq": nuevo["bq"], "aq": nuevo["aq"]})


# Streams ya creados, por cuenta (usuario_id, es_demo) o ("legado",)
_STREAMS: dict = {}
_CANDADO_STREAMS = threading.Lock()


# TITULO STREAM DE UNA CUENTA

def stream_de(clave: tuple) -> _StreamCapital:
    """Devuelve el stream de precios de la cuenta `clave`, creándolo la primera vez (no abre conexión hasta el primer `suscribir`)."""
    with _CANDADO_STREAMS:
        stream = _STREAMS.get(clave)
        if stream is None:
            stream = _STREAMS[clave] = _StreamCapital(clave)
        return stream


# TITULO DETENER STREAM

def detener_stream(clave: tuple) -> None:
    """Detiene y olvida el stream de la cuenta `clave` (por ejemplo al quedar sin clientes ni vigilancias)."""
    with _CANDADO_STREAMS:
        stream = _STREAMS.pop(clave, None)
    if stream is not None:
        stream.detener()


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara streaming_capital .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
