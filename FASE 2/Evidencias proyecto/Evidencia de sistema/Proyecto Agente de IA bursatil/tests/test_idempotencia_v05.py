# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara test_idempotencia_v05 .PY --------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_idempotencia_v05.py
------------------------
Pruebas de aceptación del hallazgo V05 de la auditoría (idempotencia y envíos duplicados): doble clic, respuesta perdida tras aceptar la orden,
tiempo agotado en la confirmación, caída entre el envío y el guardado, y repetición de una solicitud del servidor de datos. En todos los casos
la orden llega al bróker una sola vez. No usan red: el bróker y la base se reemplazan por dobles.
"""
import io
import json
import threading
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from nucleo_agente.ordenes import base_datos, propuestas, tablero
from servidor_precios import limites
from servidor_precios import manejador as modulo_manejador
from servidor_precios.idempotencia import Idempotencia
from servidor_precios.manejador import Manejador


@pytest.fixture
def bd_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(base_datos, "RUTA_DB", tmp_path / "ordenes.db")
    monkeypatch.setattr(base_datos, "_DB_PREPARADA", None)


@pytest.fixture
def validacion_ok(monkeypatch):
    monkeypatch.setattr(propuestas, "_chequeos_globales", lambda para_abrir: (SimpleNamespace(currency="USD"), None))
    monkeypatch.setattr(propuestas, "_resolver_simbolo", lambda s: str(s).upper())
    monkeypatch.setattr(propuestas, "_evaluar_apertura", lambda cuenta, simbolo, lado, sl, tp, riesgo: {
        "ok": True, "datos": {"simbolo": str(simbolo).upper(), "lado": lado, "volumen": 0.1, "precio": 2000.0, "sl": float(sl),
                              "tp": float(tp) if tp else None, "riesgo_dinero": 50.0, "riesgo_pct": float(riesgo), "moneda": "USD"}})


def _proponer():
    return propuestas.proponer_apertura("XAUUSD", "compra", 1990, 2020, 0.5, "Prueba V05")["id"]


def _estado(id_):
    return base_datos._consultar("SELECT estado, detalle FROM ordenes WHERE id = ?", (id_,))[0]


# ── Órdenes del agente: una confirmación, un envío ───────────────────────────────────

def test_v05_tiempo_agotado_en_el_envio_no_permite_reenviar(bd_temporal, validacion_ok, monkeypatch):
    llamadas = []

    def enviar_con_timeout(orden):
        llamadas.append(orden["id"])
        raise TimeoutError("el bróker no respondió")
    monkeypatch.setattr(tablero, "_enviar_apertura", enviar_con_timeout)
    id_ = _proponer()
    primera = tablero.confirmar_orden(id_)
    assert primera["ok"] is False and "revisa" in primera["mensaje"].lower()
    assert _estado(id_)["estado"] == "ERROR"
    segunda = tablero.confirmar_orden(id_)
    assert segunda["ok"] is False
    assert llamadas == [id_]                      # un solo envío aunque el usuario reintente


def test_v05_respuesta_perdida_tras_aceptar_la_orden_no_duplica(bd_temporal, validacion_ok, monkeypatch):
    llamadas = []
    monkeypatch.setattr(tablero, "_enviar_apertura", lambda o: llamadas.append(o["id"]) or {"ok": True, "estado": "EJECUTADA", "mensaje": "Ejecutado", "ticket": 7})
    monkeypatch.setattr(tablero.time, "sleep", lambda s: None)
    original = tablero._ejecutar

    def base_caida(sql, params=()):
        if sql.startswith("UPDATE ordenes SET estado = ?, detalle"):
            raise RuntimeError("la base no respondió")
        return original(sql, params)
    monkeypatch.setattr(tablero, "_ejecutar", base_caida)
    id_ = _proponer()
    resultado = tablero.confirmar_orden(id_)                       # no lanza el error del guardado
    assert resultado["ok"] is True and "No se pudo guardar" in resultado["mensaje"]
    assert tablero.confirmar_orden(id_)["ok"] is False             # sigue EJECUTANDO: no se reenvía
    assert llamadas == [id_]


def test_v05_un_fallo_pasajero_al_guardar_se_reintenta_y_queda_ejecutada(bd_temporal, validacion_ok, monkeypatch):
    monkeypatch.setattr(tablero, "_enviar_apertura", lambda o: {"ok": True, "estado": "EJECUTADA", "mensaje": "Ejecutado", "ticket": 9})
    monkeypatch.setattr(tablero.time, "sleep", lambda s: None)
    original = tablero._ejecutar
    fallos = {"n": 0}

    def una_caida(sql, params=()):
        if sql.startswith("UPDATE ordenes SET estado = ?, detalle") and fallos["n"] < 1:
            fallos["n"] += 1
            raise RuntimeError("bloqueo pasajero")
        return original(sql, params)
    monkeypatch.setattr(tablero, "_ejecutar", una_caida)
    id_ = _proponer()
    assert tablero.confirmar_orden(id_)["ok"] is True
    assert _estado(id_)["estado"] == "EJECUTADA"


def test_v05_reinicio_entre_el_envio_y_el_guardado_no_reenvia(bd_temporal, validacion_ok, monkeypatch):
    llamadas = []
    monkeypatch.setattr(tablero, "_enviar_apertura", lambda o: llamadas.append(o["id"]) or {"ok": True, "estado": "EJECUTADA", "mensaje": "x", "ticket": 1})
    id_ = _proponer()
    vencida = (datetime.now() - timedelta(minutes=5)).isoformat(timespec="seconds")
    # Estado que deja una caída justo después de enviar: la orden quedó EJECUTANDO y su vigencia ya pasó.
    base_datos._ejecutar("UPDATE ordenes SET estado = 'EJECUTANDO', expira = ? WHERE id = ?", (vencida, id_))
    tablero.expirar_vencidas()                                      # lo que hace la plataforma al arrancar de nuevo
    assert _estado(id_)["estado"] == "ERROR" and "revisa" in _estado(id_)["detalle"].lower()
    assert tablero.confirmar_orden(id_)["ok"] is False
    assert llamadas == []                                           # ningún reenvío automático


def test_v05_doble_clic_sigue_enviando_una_sola_vez(bd_temporal, validacion_ok, monkeypatch):
    llamadas = []
    monkeypatch.setattr(tablero, "_enviar_apertura", lambda o: llamadas.append(o["id"]) or {"ok": True, "estado": "EJECUTADA", "mensaje": "x", "ticket": 1})
    id_ = _proponer()
    hilos = [threading.Thread(target=tablero.confirmar_orden, args=(id_,)) for _ in range(8)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert llamadas == [id_]


# ── Servidor de datos: la misma solicitud no llega dos veces al bróker ───────────────

def test_v05_registro_de_idempotencia_devuelve_el_resultado_guardado():
    registro = Idempotencia()
    assert registro.reservar("u1", "mercado", "abc12345") == ("nueva", None)
    registro.guardar("u1", "mercado", "abc12345", {"ticket": 5})
    assert registro.reservar("u1", "mercado", "abc12345") == ("repetida", {"ticket": 5})


def test_v05_una_solicitud_en_curso_o_incierta_no_se_reenvia():
    registro = Idempotencia()
    registro.reservar("u1", "mercado", "abc12345")
    assert registro.reservar("u1", "mercado", "abc12345") == ("en_curso", None)


def test_v05_la_clave_es_por_usuario_y_por_ruta():
    registro = Idempotencia()
    registro.reservar("u1", "mercado", "abc12345")
    assert registro.reservar("u2", "mercado", "abc12345")[0] == "nueva"
    assert registro.reservar("u1", "orden", "abc12345")[0] == "nueva"


def test_v05_las_solicitudes_se_olvidan_pasado_el_plazo():
    registro = Idempotencia(vida_s=0)
    registro.reservar("u1", "mercado", "abc12345")
    assert registro.reservar("u1", "mercado", "abc12345")[0] == "nueva"


def test_v05_el_identificador_de_solicitud_se_valida():
    ok = limites.validar_orden("mercado", {"symbol": "EURUSD", "lado": "BUY", "volumen": 0.1, "id_solicitud": "q1abc-DEF_9"})
    assert ok["id_solicitud"] == "q1abc-DEF_9"
    for malo in ("corto", "con espacio y símbolos!", "x" * 80, 12345):
        with pytest.raises(limites.ErrorSolicitud):
            limites.validar_orden("mercado", {"symbol": "EURUSD", "lado": "BUY", "volumen": 0.1, "id_solicitud": malo})
    sin_id = limites.validar_orden("mercado", {"symbol": "EURUSD", "lado": "BUY", "volumen": 0.1})
    assert "id_solicitud" not in sin_id


class _Peticion:
    """Doble de la petición HTTP para ejecutar `Manejador._atender_post` real sin socket."""
    _atender_post = Manejador._atender_post

    def __init__(self, cuerpo):
        datos = json.dumps(cuerpo).encode()
        self.path = "/mercado"
        self.headers = {"Origin": "http://localhost", "Content-Length": str(len(datos))}
        self.rfile = io.BytesIO(datos)
        self.salidas = []
        self.close_connection = False

    def _origen_local(self):
        return True

    def _responder(self, cuerpo):
        self.salidas.append((200, cuerpo))

    def _rechazar(self, codigo, mensaje):
        self.salidas.append((codigo, mensaje))

    def _error_interno(self, *args, **kw):
        self.salidas.append((500, "error interno"))


@pytest.fixture
def servidor(monkeypatch):
    from servidor_precios.idempotencia import IDEMPOTENCIA
    IDEMPOTENCIA._datos.clear()
    monkeypatch.setattr(limites, "auditar", lambda *a, **k: None)
    llamadas = []
    monkeypatch.setattr(modulo_manejador, "ejecutar_orden_mercado", lambda s, l, v: llamadas.append((s, l, v)) or {"ticket": 55, "ok": True})
    return llamadas


CUERPO = {"symbol": "EURUSD", "lado": "BUY", "volumen": 0.1, "id_solicitud": "solicitud-0001"}


def test_v05_la_misma_solicitud_enviada_dos_veces_llega_una_vez_al_broker(servidor):
    primera, segunda = _Peticion(CUERPO), _Peticion(CUERPO)
    primera._atender_post(("u1", "demo"))
    segunda._atender_post(("u1", "demo"))
    assert len(servidor) == 1
    assert primera.salidas == segunda.salidas == [(200, {"ticket": 55, "ok": True})]


def test_v05_tras_un_fallo_incierto_el_reintento_se_rechaza_con_409_sin_llamar_al_broker(servidor, monkeypatch):
    def cae(s, l, v):
        servidor.append((s, l, v))
        raise RuntimeError("se cortó la conexión")
    monkeypatch.setattr(modulo_manejador, "ejecutar_orden_mercado", cae)
    primera, reintento = _Peticion(CUERPO), _Peticion(CUERPO)
    primera._atender_post(("u1", "demo"))
    reintento._atender_post(("u1", "demo"))
    assert primera.salidas[0][0] == 500
    assert reintento.salidas[0][0] == 409
    assert len(servidor) == 1


def test_v05_solicitudes_distintas_o_de_otro_usuario_si_se_envian(servidor):
    _Peticion(CUERPO)._atender_post(("u1", "demo"))
    _Peticion({**CUERPO, "id_solicitud": "solicitud-0002"})._atender_post(("u1", "demo"))
    _Peticion(CUERPO)._atender_post(("u2", "demo"))
    assert len(servidor) == 3


def test_v05_sin_identificador_la_peticion_se_atiende_como_antes(servidor):
    sin_id = {"symbol": "EURUSD", "lado": "BUY", "volumen": 0.1}
    _Peticion(sin_id)._atender_post(("u1", "demo"))
    _Peticion(sin_id)._atender_post(("u1", "demo"))
    assert len(servidor) == 2

# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara test_idempotencia_v05 .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.

