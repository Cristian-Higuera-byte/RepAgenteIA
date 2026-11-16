# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------- INICIO Piña y Jara test_seguridad_v01_v03_v06_v07 .PY -------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_seguridad_v01_v03_v06_v07.py
---------------------------------
Pruebas de aceptación de la auditoría de seguridad para los hallazgos V01 (propuestas aisladas por usuario y cuenta), V03 (la API de precios exige
credencial incluso en modo legado), V06 (la sesión ya no viaja en la dirección y las revocaciones sobreviven a un fallo del almacenamiento) y V07
(el token de datos se revoca al cerrar sesión o cambiar la contraseña). No usan red: el bróker, la base y el servidor se reemplazan por dobles.
V05 (idempotencia ante reintentos y reinicios) sigue abierto y no se prueba aquí.
"""
import threading
import time
from types import SimpleNamespace

import pytest

from herramientas import almacen_sesiones, token_datos
from herramientas.backends import sesiones_capital
from nucleo_agente.ordenes import base_datos, propuestas, tablero
from servidor_precios import manejador as modulo_manejador
from servidor_precios.manejador import Manejador


# ── Fixtures ──────────────────────────────────────────────────────────────────────────

@pytest.fixture
def bd_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(base_datos, "RUTA_DB", tmp_path / "ordenes.db")
    monkeypatch.setattr(base_datos, "_DB_PREPARADA", None)


@pytest.fixture
def envios(monkeypatch):
    llamadas = []

    def enviar(orden):
        llamadas.append(orden["id"])
        return {"ok": True, "estado": "EJECUTADA", "mensaje": "Orden ejecutada (prueba)", "ticket": 1}
    monkeypatch.setattr(tablero, "_enviar_apertura", enviar)
    monkeypatch.setattr(tablero, "_enviar_cierre", enviar)
    return llamadas


@pytest.fixture
def validacion_ok(monkeypatch):
    monkeypatch.setattr(propuestas, "_chequeos_globales", lambda para_abrir: (SimpleNamespace(currency="USD"), None))
    monkeypatch.setattr(propuestas, "_resolver_simbolo", lambda s: str(s).upper())
    monkeypatch.setattr(propuestas, "_evaluar_apertura", lambda cuenta, simbolo, lado, sl, tp, riesgo: {
        "ok": True, "datos": {"simbolo": str(simbolo).upper(), "lado": lado, "volumen": 0.1, "precio": 2000.0, "sl": float(sl),
                              "tp": float(tp) if tp else None, "riesgo_dinero": 50.0, "riesgo_pct": float(riesgo), "moneda": "USD"}})


@pytest.fixture
def multiusuario(monkeypatch):
    monkeypatch.setattr(sesiones_capital, "MULTIUSUARIO", True)


def _proponer():
    return propuestas.proponer_apertura("XAUUSD", "compra", 1990, 2020, 0.5, "Prueba de aceptación")


@pytest.fixture
def secreto(monkeypatch):
    monkeypatch.setenv("SERVIDOR_SECRETO", "s" * 40)
    token_datos._memoria.clear()
    yield
    token_datos._memoria.clear()


@pytest.fixture
def base_revocaciones(secreto, cliente_memoria, monkeypatch):
    monkeypatch.setattr(token_datos, "_cliente", lambda: cliente_memoria)
    return cliente_memoria


class _Peticion:
    """Doble mínimo de la petición HTTP: ejecuta `Manejador._identificar` real sin abrir ningún socket."""
    _identificar = Manejador._identificar

    def __init__(self, ruta):
        self.path = ruta
        self.respuestas = []

    def _rechazar(self, codigo, mensaje):
        self.respuestas.append((codigo, mensaje))


# ── V01: aislamiento de propuestas por usuario y cuenta ───────────────────────────────

def test_v01_un_usuario_no_ve_las_propuestas_de_otro(bd_temporal, envios, validacion_ok, multiusuario):
    with sesiones_capital.como_usuario(1, True):
        id_a = _proponer()["id"]
        assert [o["id"] for o in tablero.listar_pendientes()] == [id_a]
    with sesiones_capital.como_usuario(2, True):
        assert tablero.listar_pendientes() == []
        assert tablero.listar_historial() == []


def test_v01_un_usuario_no_puede_rechazar_la_propuesta_de_otro(bd_temporal, envios, validacion_ok, multiusuario):
    with sesiones_capital.como_usuario(1, True):
        id_a = _proponer()["id"]
    with sesiones_capital.como_usuario(2, True):
        assert tablero.rechazar_orden(id_a) is False
    with sesiones_capital.como_usuario(1, True):
        assert [o["id"] for o in tablero.listar_pendientes()] == [id_a]   # sigue intacta


def test_v01_un_usuario_no_puede_confirmar_la_propuesta_de_otro_ni_toca_el_broker(bd_temporal, envios, validacion_ok, multiusuario):
    with sesiones_capital.como_usuario(1, True):
        id_a = _proponer()["id"]
    with sesiones_capital.como_usuario(2, True):
        resultado = tablero.confirmar_orden(id_a)
    assert resultado["ok"] is False and "no existe" in resultado["mensaje"]
    assert envios == []
    with sesiones_capital.como_usuario(1, True):
        assert [o["id"] for o in tablero.listar_pendientes()] == [id_a]   # ninguna mutación


def test_v01_una_propuesta_demo_no_se_confirma_desde_la_cuenta_real(bd_temporal, envios, validacion_ok, multiusuario):
    with sesiones_capital.como_usuario(1, True):
        id_demo = _proponer()["id"]
    with sesiones_capital.como_usuario(1, False):
        assert tablero.listar_pendientes() == []
        resultado = tablero.confirmar_orden(id_demo)
    assert resultado["ok"] is False
    assert envios == []


def test_v01_el_dueno_si_puede_confirmar_su_propuesta(bd_temporal, envios, validacion_ok, multiusuario):
    with sesiones_capital.como_usuario(1, True):
        id_a = _proponer()["id"]
        assert tablero.confirmar_orden(id_a)["ok"] is True
    assert envios == [id_a]


def test_v01_dos_confirmaciones_simultaneas_del_dueno_envian_una_sola_orden(bd_temporal, envios, validacion_ok, multiusuario):
    with sesiones_capital.como_usuario(1, True):
        id_a = _proponer()["id"]
    resultados = []

    def confirmar():
        with sesiones_capital.como_usuario(1, True):
            resultados.append(tablero.confirmar_orden(id_a))
    hilos = [threading.Thread(target=confirmar) for _ in range(6)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert envios.count(id_a) == 1
    assert sum(1 for r in resultados if r["ok"]) == 1


def test_v01_sin_usuario_no_se_pueden_crear_propuestas(bd_temporal, validacion_ok, multiusuario):
    with pytest.raises(base_datos.SinSesionError):
        _proponer()


# ── V03: la API exige credencial también en modo legado ───────────────────────────────

def test_v03_en_multiusuario_sin_token_responde_401(secreto, multiusuario):
    peticion = _Peticion("/ticks?s=XAUUSD")
    assert peticion._identificar() is None
    assert peticion.respuestas[0][0] == 401


def test_v03_en_multiusuario_un_token_falsificado_responde_401(secreto, multiusuario):
    valido = token_datos.emitir(1, True)
    carga, firma = valido.split(".")
    for falso in (f"{carga}.{'0' * len(firma)}", "basura", f"{carga}x.{firma}"):
        peticion = _Peticion(f"/t/{falso}/ticks")
        assert peticion._identificar() is None
        assert peticion.respuestas[0][0] == 401


def test_v03_en_modo_legado_una_mutacion_sin_token_responde_401(secreto, monkeypatch):
    monkeypatch.setattr(sesiones_capital, "MULTIUSUARIO", False)
    peticion = _Peticion("/orden")
    assert peticion._identificar(mutacion=True) is None
    assert peticion.respuestas[0][0] == 401


def test_v03_en_modo_legado_una_mutacion_con_token_falsificado_responde_401(secreto, monkeypatch):
    monkeypatch.setattr(sesiones_capital, "MULTIUSUARIO", False)
    peticion = _Peticion("/t/falso.falso/orden")
    assert peticion._identificar(mutacion=True) is None
    assert peticion.respuestas[0][0] == 401


def test_v03_con_token_valido_pasa_y_la_ruta_queda_sin_el_token(base_revocaciones, multiusuario):
    token = token_datos.emitir(5, False)
    peticion = _Peticion(f"/t/{token}/ticks?s=XAUUSD")
    assert peticion._identificar() == (5, False)
    assert peticion.path == "/ticks?s=XAUUSD"       # el token no queda en la ruta que se registra
    assert peticion.respuestas == []


def test_v03_la_ruta_de_salud_es_publica(multiusuario):
    peticion = _Peticion("/salud")
    assert peticion._identificar() == ("anonimo",)
    assert peticion.respuestas == []


def test_v03_un_origen_ajeno_no_esta_autorizado():
    manejador = SimpleNamespace(headers={"Origin": "https://sitio-malicioso.example"})
    assert Manejador._origen_local(manejador) is False
    manejador.headers = {}
    assert Manejador._origen_local(manejador) is False


# ── V06: la sesión no viaja en la dirección y la revocación es verificable ───────────

def test_v06_la_sesion_ya_no_usa_el_parametro_s_de_la_direccion():
    ruta = modulo_manejador.__file__.replace("servidor_precios/manejador.py", "componentes_plataforma/acceso/sesion.py")
    codigo = open(ruta, encoding="utf-8").read()
    assert 'del st.query_params["s"]' in codigo               # un ?s= antiguo se descarta
    assert "st.query_params[\"s\"] =" not in codigo           # y nunca se vuelve a escribir


def test_v06_cerrar_en_todos_borra_las_sesiones_del_usuario_y_anota_el_instante():
    almacen_sesiones._sesiones.clear()
    a = almacen_sesiones.crear({"id": 9, "nombre": "A", "email": "a@x"})
    b = almacen_sesiones.crear({"id": 9, "nombre": "A", "email": "a@x"})
    otro = almacen_sesiones.crear({"id": 10, "nombre": "B", "email": "b@x"})
    antes = time.time()
    almacen_sesiones.revocar_usuario(9)
    assert almacen_sesiones.obtener(a) is None and almacen_sesiones.obtener(b) is None
    assert almacen_sesiones.obtener(otro) is not None
    assert almacen_sesiones.revocada_desde(9) >= antes
    almacen_sesiones._sesiones.clear()


def test_v06_cerrar_una_sesion_no_invalida_la_de_otro_dispositivo(base_revocaciones):
    h1, h2 = token_datos.huella_sesion("cookie-1"), token_datos.huella_sesion("cookie-2")
    t1 = token_datos.leer(token_datos.emitir(3, True, sesion=h1))
    t2 = token_datos.leer(token_datos.emitir(3, True, sesion=h2))
    assert token_datos.revocar_sesion(3, h1) is True
    assert token_datos.esta_revocado(t1) is True
    assert token_datos.esta_revocado(t2) is False


def test_v06_si_el_almacenamiento_falla_al_revocar_no_se_declara_exito(secreto, monkeypatch):
    class Roto:
        def table(self, nombre):
            raise RuntimeError("base caída")
    monkeypatch.setattr(token_datos, "_cliente", lambda: Roto())
    assert token_datos.revocar_usuario(3) is False
    assert token_datos.revocar_sesion(3, "abc") is False


def test_v06_sin_base_configurada_la_revocacion_informa_fallo(secreto, monkeypatch):
    monkeypatch.setattr(token_datos, "_cliente", lambda: None)
    assert token_datos.revocar_usuario(3) is False


# ── V07: el token de datos se revoca y los flujos se cortan ───────────────────────────

def test_v07_cerrar_todas_las_sesiones_invalida_los_tokens_anteriores(base_revocaciones):
    antes = token_datos.leer(token_datos.emitir(4, True))
    time.sleep(0.01)
    assert token_datos.revocar_usuario(4) is True
    assert token_datos.esta_revocado(antes) is True
    time.sleep(0.01)
    despues = token_datos.leer(token_datos.emitir(4, True))
    assert token_datos.esta_revocado(despues) is False        # un inicio de sesión nuevo sí vale


def test_v07_con_la_sesion_revocada_la_peticion_siguiente_se_rechaza(base_revocaciones, multiusuario):
    token = token_datos.emitir(4, True)
    assert _Peticion(f"/t/{token}/ticks")._identificar() == (4, True)
    time.sleep(0.01)
    token_datos.revocar_usuario(4)
    peticion = _Peticion(f"/t/{token}/ticks")
    assert peticion._identificar() is None
    assert peticion.respuestas == [(401, "sesión cerrada")]


def test_v07_si_no_se_puede_comprobar_la_revocacion_una_orden_se_rechaza_con_503(secreto, multiusuario, monkeypatch):
    class Roto:
        def table(self, nombre):
            raise RuntimeError("base caída")
    monkeypatch.setattr(token_datos, "_cliente", lambda: Roto())
    token = token_datos.emitir(4, True)
    orden = _Peticion(f"/t/{token}/orden")
    assert orden._identificar(mutacion=True) is None
    assert orden.respuestas[0][0] == 503


def test_v07_el_stream_se_revisa_con_una_frecuencia_definida():
    assert 0 < modulo_manejador.REVISION_STREAM_S <= 10      # el flujo abierto se corta en pocos segundos
    assert token_datos.MEMORIA_REVOCACION_S <= 10


def test_v07_un_token_vencido_o_sin_secreto_no_se_acepta(monkeypatch):
    monkeypatch.setenv("SERVIDOR_SECRETO", "s" * 40)
    vencido = token_datos.emitir(1, True, vida_s=-10)
    assert token_datos.leer(vencido) is None
    monkeypatch.setenv("SERVIDOR_SECRETO", "corto")
    assert token_datos.emitir(1, True) == ""


def test_v07_el_token_no_aparece_en_la_ruta_que_se_registra(base_revocaciones, multiusuario):
    token = token_datos.emitir(8, True)
    peticion = _Peticion(f"/t/{token}/stream?s=XAUUSD")
    peticion._identificar()
    assert token not in peticion.path


# -------------------------------------------------------------------------------------------------------
# ------------------------- FIN Piña y Jara test_seguridad_v01_v03_v06_v07 .PY --------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.

