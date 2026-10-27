"""
streaming_capital.py  —  Precios en vivo de Capital.com por WebSocket  —  16-10-2026
------------------------------------------------------------------------------------
Mantiene UNA conexión WebSocket a Capital.com y guarda el último Bid/Ask de cada
instrumento suscrito en una caché en memoria. El motor de precios
(servidor_precios/motor/base.py) lee de esa caché en vez de preguntar por REST en
cada ciclo, lo que elimina decenas de llamadas por segundo y hace fluida la app.

Diseño:
  - Corre en un hilo daemon con su propio bucle asyncio (websockets).
  - Reutiliza la sesión REST del backend (herramientas/backends/capital.py) para los
    tokens CST / X-SECURITY-TOKEN. El sondeo de cuenta del motor mantiene esa sesión
    viva, así que los tokens no caducan.
  - Reconecta solo ante errores/cierres, re-autenticando y re-suscribiendo.
  - Ping cada 5 min (el límite de Capital es 10) para mantener el stream vivo.
  - Máximo 40 instrumentos (límite de Capital).

Solo se usa con PROVEEDOR=capital; el motor no lo arranca con MT5.
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
from types import SimpleNamespace
from typing import Optional

from tools.backends import capital as cap

_WS_URL = "wss://api-streaming-capital.backend-capital.com/connect"
_MAX_EPICS = 40
_PING_S = 300            # ping cada 5 min (límite de Capital: 10)
_BACKOFF_S = 3           # espera antes de reconectar


class _StreamCapital:
    def __init__(self) -> None:
        self._cache: dict = {}          # epic -> {"bid","ask","t"(ms)}
        self._deseados: set = set()     # epics que queremos suscribir
        self._suscritos: set = set()    # epics ya suscritos en la conexión actual
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws = None
        self._hilo: Optional[threading.Thread] = None

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

    def tick(self, epic: str):
        """Último tick del epic como objeto estilo MT5 (bid, ask, last, time, time_msc), o None."""
        d = self._cache.get(epic)
        if not d:
            return None
        return SimpleNamespace(
            bid=d["bid"], ask=d["ask"], last=d["bid"] or d["ask"],
            time=int(d["t"] / 1000), time_msc=int(d["t"]),
        )

    # ---- hilo + bucle asyncio --------------------------------------------
    def _asegurar_hilo(self) -> None:
        if self._hilo and self._hilo.is_alive():
            return
        self._hilo = threading.Thread(target=self._run, name="capital-ws", daemon=True)
        self._hilo.start()

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._principal())
        except Exception as e:  # noqa: BLE001
            print(f"[WS Capital] bucle terminó: {e}")

    async def _principal(self) -> None:
        import websockets  # import tardío: solo si se usa el streaming
        while True:
            try:
                if not cap.inicializar_mt5():
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
                        async for msg in ws:
                            self._procesar(msg)
                    finally:
                        tarea_ping.cancel()
            except Exception as e:  # noqa: BLE001
                print(f"[WS Capital] reconectando tras: {type(e).__name__}: {e}")
            self._ws = None
            await asyncio.sleep(_BACKOFF_S)

    async def _suscribir_pendientes(self) -> None:
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
                "cst": cap._tokens["CST"],
                "securityToken": cap._tokens["X-SECURITY-TOKEN"],
                "payload": {"epics": faltan[:_MAX_EPICS]},
            }))
            with self._lock:
                self._suscritos.update(faltan)
        except Exception as e:  # noqa: BLE001
            print(f"[WS Capital] no se pudo suscribir: {e}")

    async def _ping_loop(self, ws) -> None:
        while True:
            await asyncio.sleep(_PING_S)
            try:
                await ws.send(json.dumps({
                    "destination": "ping",
                    "correlationId": str(int(time.time())),
                    "cst": cap._tokens["CST"],
                    "securityToken": cap._tokens["X-SECURITY-TOKEN"],
                }))
            except Exception:
                return

    def _procesar(self, msg) -> None:
        try:
            d = json.loads(msg)
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
        self._cache[epic] = {
            "bid": float(bid) if bid is not None else 0.0,
            "ask": float(ofr) if ofr is not None else 0.0,
            "t": int(p.get("timestamp") or time.time() * 1000),
        }


STREAM = _StreamCapital()
