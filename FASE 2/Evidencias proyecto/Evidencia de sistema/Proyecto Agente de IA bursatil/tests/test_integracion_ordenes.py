# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------- INICIO Piña y Jara test_integracion_ordenes .PY ---------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_integracion_ordenes.py
---------------------------
Pruebas de integración del control de órdenes del agente (nucleo_agente/ordenes) sobre una base SQLite temporal:
el agente solo propone, el usuario confirma o rechaza, la propuesta vence, el interruptor de emergencia bloquea las
aperturas y una orden no se envía dos veces aunque se confirme varias veces al mismo tiempo.
"""
import threading
from types import SimpleNamespace

import pytest

from nucleo_agente.ordenes import base_datos, mt5_utiles, propuestas, tablero


@pytest.fixture
def bd_temporal(tmp_path, monkeypatch):
    """Apunta el módulo de órdenes a una base SQLite nueva dentro de una carpeta temporal."""
    monkeypatch.setattr(base_datos, "RUTA_DB", tmp_path / "ordenes.db")
    monkeypatch.setattr(base_datos, "_DB_PREPARADA", None)
    return tmp_path


@pytest.fixture
def envios(monkeypatch):
    """Sustituye el envío al bróker por un doble que cuenta cuántas veces se llamó."""
    llamadas = []

    def enviar(orden):
        llamadas.append(orden["id"])
        return {"ok": True, "estado": "EJECUTADA", "mensaje": "Orden ejecutada (prueba)", "ticket": 12345}
    monkeypatch.setattr(tablero, "_enviar_apertura", enviar)
    monkeypatch.setattr(tablero, "_enviar_cierre", enviar)
    return llamadas


@pytest.fixture
def validacion_ok(monkeypatch):
    """Simula los chequeos globales y la validación de apertura (que dependen del bróker) para probar el flujo."""
    monkeypatch.setattr(propuestas, "_chequeos_globales", lambda para_abrir: (SimpleNamespace(currency="USD"), None))
    monkeypatch.setattr(propuestas, "_resolver_simbolo", lambda s: str(s).upper())
    monkeypatch.setattr(propuestas, "_evaluar_apertura", lambda cuenta, simbolo, lado, sl, tp, riesgo: {
        "ok": True, "datos": {"simbolo": str(simbolo).upper(), "lado": lado, "volumen": 0.1, "precio": 2000.0, "sl": float(sl),
                              "tp": float(tp) if tp else None, "riesgo_dinero": 50.0, "riesgo_pct": float(riesgo), "moneda": "USD"}})


def _proponer(simbolo="XAUUSD", lado="compra"):
    return propuestas.proponer_apertura(simbolo, lado, 1990, 2020, 0.5, "Prueba de integración")


def test_el_agente_solo_propone_y_no_envia_nada_al_broker(bd_temporal, envios, validacion_ok):
    r = _proponer()
    assert r["estado"] == "PROPUESTA_PENDIENTE" and r["id"]
    assert envios == []                                       # nada se envió
    fila = base_datos._consultar("SELECT * FROM ordenes WHERE id = ?", (r["id"],))[0]
    assert fila["estado"] == "PENDIENTE" and fila["origen"] == "agente"
    assert "NO está ejecutada" in r["mensaje"]


def test_una_propuesta_igual_pendiente_no_se_duplica(bd_temporal, envios, validacion_ok):
    a = _proponer()
    b = _proponer()
    assert b.get("id") == a["id"] or b.get("estado") == "PROPUESTA_PENDIENTE"
    assert len(base_datos._consultar("SELECT id FROM ordenes WHERE estado = 'PENDIENTE'")) == 1


def test_una_propuesta_que_incumple_los_limites_se_rechaza_y_queda_auditada(bd_temporal, envios, monkeypatch):
    monkeypatch.setattr(propuestas, "_chequeos_globales", lambda para_abrir: (SimpleNamespace(currency="USD"), None))
    monkeypatch.setattr(propuestas, "_resolver_simbolo", lambda s: str(s).upper())
    monkeypatch.setattr(propuestas, "_evaluar_apertura", lambda *a: {"ok": False, "motivo": "El stop loss es obligatorio y debe ser un precio numérico."})
    r = propuestas.proponer_apertura("XAUUSD", "compra", None, None, 0.5, "sin SL")
    assert r["estado"] == "RECHAZADA" and "stop loss" in r["motivo"]
    fila = base_datos._consultar("SELECT * FROM ordenes")[0]
    assert fila["estado"] == "RECHAZADA_RIESGO" and "stop loss" in fila["detalle"]
    assert envios == []


def test_confirmar_envia_la_orden_una_vez_y_guarda_el_ticket(bd_temporal, envios, validacion_ok):
    id_ = _proponer()["id"]
    r = tablero.confirmar_orden(id_)
    assert r["ok"] is True and r["ticket"] == 12345
    fila = base_datos._consultar("SELECT * FROM ordenes WHERE id = ?", (id_,))[0]
    assert fila["estado"] == "EJECUTADA" and fila["ticket_resultado"] == 12345
    assert envios == [id_]


def test_confirmar_dos_veces_no_reenvia_la_orden(bd_temporal, envios, validacion_ok):
    id_ = _proponer()["id"]
    tablero.confirmar_orden(id_)
    segunda = tablero.confirmar_orden(id_)
    assert segunda["ok"] is False and "EJECUTADA" in segunda["mensaje"]
    assert envios == [id_]


def test_un_doble_clic_simultaneo_envia_la_orden_una_sola_vez(bd_temporal, envios, validacion_ok):
    id_ = _proponer()["id"]
    resultados = []
    hilos = [threading.Thread(target=lambda: resultados.append(tablero.confirmar_orden(id_))) for _ in range(8)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert envios.count(id_) == 1
    assert sum(1 for r in resultados if r["ok"]) == 1


def test_una_propuesta_vencida_no_se_ejecuta_y_queda_expirada(bd_temporal, envios, validacion_ok):
    id_ = _proponer()["id"]
    base_datos._ejecutar("UPDATE ordenes SET expira = ? WHERE id = ?", ("2000-01-01T00:00:00", id_))
    r = tablero.confirmar_orden(id_)
    assert r["ok"] is False and "venció" in r["mensaje"]
    assert base_datos._consultar("SELECT estado FROM ordenes WHERE id = ?", (id_,))[0]["estado"] == "EXPIRADA"
    assert envios == []


def test_el_usuario_puede_rechazar_y_luego_ya_no_se_puede_confirmar(bd_temporal, envios, validacion_ok):
    id_ = _proponer()["id"]
    assert tablero.rechazar_orden(id_) is True
    assert base_datos._consultar("SELECT estado FROM ordenes WHERE id = ?", (id_,))[0]["estado"] == "RECHAZADA_USUARIO"
    assert tablero.confirmar_orden(id_)["ok"] is False
    assert envios == []


def test_confirmar_una_orden_inexistente_no_envia_nada(bd_temporal, envios):
    r = tablero.confirmar_orden("no-existe")
    assert r["ok"] is False and "no existe" in r["mensaje"]
    assert envios == []


def test_el_interruptor_de_emergencia_bloquea_las_nuevas_aperturas(bd_temporal, monkeypatch):
    cuenta = SimpleNamespace(trade_mode=0, balance=10000, currency="USD")
    monkeypatch.setattr(mt5_utiles, "_preparar_mt5", lambda: None)
    monkeypatch.setattr(mt5_utiles, "mt5", SimpleNamespace(account_info=lambda: cuenta, positions_get=lambda: [], ACCOUNT_TRADE_MODE_DEMO=0))
    base_datos.fijar_interruptor_emergencia(True)
    _, motivo = mt5_utiles._chequeos_globales(para_abrir=True)
    assert motivo and "interruptor de emergencia" in motivo
    _, motivo_cierre = mt5_utiles._chequeos_globales(para_abrir=False)
    assert motivo_cierre is None                              # cerrar posiciones sigue permitido
    base_datos.fijar_interruptor_emergencia(False)
    assert mt5_utiles._chequeos_globales(para_abrir=True)[1] is None


def test_todas_las_propuestas_quedan_en_el_historial(bd_temporal, envios, validacion_ok):
    a = _proponer("XAUUSD")["id"]
    b = _proponer("EURUSD", "venta")["id"]
    tablero.confirmar_orden(a)
    tablero.rechazar_orden(b)
    estados = {f["id"]: f["estado"] for f in base_datos._consultar("SELECT id, estado FROM ordenes")}
    assert estados == {a: "EJECUTADA", b: "RECHAZADA_USUARIO"}
    assert len(tablero.listar_historial()) == 2 and tablero.listar_pendientes() == []


# -------------------------------------------------------------------------------------------------------
# ---------------------------- FIN Piña y Jara test_integracion_ordenes .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
