# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.

# -------------------------------------------------------------------------------------------------------
# --------------------------- INICIO Piña y Jara test_seguridad_auditoria .PY ---------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_seguridad_auditoria.py
---------------------------
Pruebas de las correcciones de la auditoría de seguridad (V01 a V07) y de los controles de acceso de la versión de noviembre:
política de apertura y parada de emergencia (V02), límites de los formularios (V04), correos temporales y lista blanca, administradores (root),
reCAPTCHA y vencimiento de los enlaces de recuperación. No usan red ni .env: Google, la base de datos y la sesión se reemplazan por dobles.
"""
import pytest

import configuracion
from herramientas import correos_temporales, limites_formularios, paradas_emergencia, politica_apertura, recaptcha, roles


# ── V02: parada de emergencia y política única de apertura ───────────────────────────────────────────────

@pytest.fixture
def paradas(tmp_path, monkeypatch):
    """Archivo de paradas temporal y una sesión simulada (usuario 7 en cuenta demo)."""
    monkeypatch.setattr(paradas_emergencia, "DIR_DATOS", tmp_path)
    monkeypatch.setattr(paradas_emergencia, "RUTA_DB", tmp_path / "paradas.db")
    monkeypatch.setattr(paradas_emergencia, "_PREPARADA", None)
    sesion = {"clave": (7, True)}
    monkeypatch.setattr(paradas_emergencia.sesiones_capital, "clave_actual", lambda: sesion["clave"])
    monkeypatch.setattr(configuracion, "OPERAR_EN_CUENTA_REAL", False)
    return sesion


def test_con_todo_en_orden_se_puede_abrir_en_demo(paradas):
    assert politica_apertura.motivo_de_bloqueo() is None


def test_sin_usuario_identificado_no_se_puede_abrir(paradas):
    paradas["clave"] = ()
    assert "sesión de usuario" in politica_apertura.motivo_de_bloqueo()


def test_la_cuenta_real_esta_apagada_por_defecto(paradas):
    paradas["clave"] = (7, False)
    assert "cuenta real" in politica_apertura.motivo_de_bloqueo()


def test_la_cuenta_real_se_habilita_solo_con_la_variable(paradas, monkeypatch):
    paradas["clave"] = (7, False)
    monkeypatch.setattr(configuracion, "OPERAR_EN_CUENTA_REAL", True)
    assert politica_apertura.motivo_de_bloqueo() is None


def test_la_parada_de_un_usuario_no_afecta_a_otro(paradas):
    paradas_emergencia.fijar_usuario(True)
    assert "emergencia" in politica_apertura.motivo_de_bloqueo()
    paradas["clave"] = (8, True)
    assert politica_apertura.motivo_de_bloqueo() is None


def test_la_parada_es_por_cuenta_demo_o_real(paradas):
    paradas_emergencia.fijar_usuario(True)
    paradas["clave"] = (7, False)
    assert paradas_emergencia.activa_usuario() is False


def test_la_parada_global_bloquea_a_todos_y_se_puede_levantar(paradas):
    paradas_emergencia.fijar_global(True)
    assert "operador" in politica_apertura.motivo_de_bloqueo()
    paradas["clave"] = (99, True)
    assert "operador" in politica_apertura.motivo_de_bloqueo()
    paradas_emergencia.fijar_global(False)
    assert politica_apertura.motivo_de_bloqueo() is None


def test_sin_usuario_no_se_puede_cambiar_la_parada(paradas):
    paradas["clave"] = ()
    with pytest.raises(PermissionError):
        paradas_emergencia.fijar_usuario(True)
    assert paradas_emergencia.activa_usuario() is False


def test_la_parada_sobrevive_al_reinicio_porque_esta_en_disco(paradas, monkeypatch):
    paradas_emergencia.fijar_usuario(True)
    monkeypatch.setattr(paradas_emergencia, "_PREPARADA", None)
    assert paradas_emergencia.activa_usuario() is True


# ── V04: límites de tamaño de los formularios ────────────────────────────────────────────────────────────

def test_un_valor_dentro_del_tope_no_excede():
    assert limites_formularios.excede(("a@b.cl", limites_formularios.CORREO)) is False


def test_un_valor_sobre_el_tope_excede():
    assert limites_formularios.excede(("a" * 41, limites_formularios.CORREO)) is True
    assert limites_formularios.excede(("x" * 129, limites_formularios.API_KEY)) is True


def test_basta_un_campo_excedido_y_se_ignoran_los_que_no_son_texto():
    assert limites_formularios.excede((None, 5), ("ok", 5), (123456789, 3)) is False
    assert limites_formularios.excede(("ok", 5), ("demasiado", 5)) is True


# ── Correos: formato, temporales y lista blanca ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("correo", ["", "sin-arroba", "a@b", "a b@gmail.com"])
def test_un_correo_con_formato_invalido_se_rechaza(correo):
    assert "correo válido" in correos_temporales.validar(correo)


def test_un_correo_temporal_se_rechaza_tambien_en_subdominios():
    assert "temporales" in correos_temporales.validar("x@mailinator.com")
    assert "temporales" in correos_temporales.validar("x@algo.mailinator.com")


@pytest.mark.parametrize("correo", ["a@gmail.com", "a@outlook.com", "a@hotmail.cl", "a@yahoo.com.ar", "a@duocuc.cl", "a@uchile.edu", "a@minsal.gob.cl"])
def test_los_proveedores_conocidos_se_aceptan(correo):
    assert correos_temporales.validar(correo) is None


def test_un_dominio_desconocido_se_rechaza_con_la_lista_blanca(monkeypatch):
    monkeypatch.delenv("CORREOS_SOLO_CONOCIDOS", raising=False)
    assert "proveedor conocido" in correos_temporales.validar("a@empresa-rara-xyz.cl")


def test_la_lista_blanca_se_apaga_con_la_variable(monkeypatch):
    monkeypatch.setenv("CORREOS_SOLO_CONOCIDOS", "false")
    assert correos_temporales.validar("a@empresa-rara-xyz.cl") is None


def test_el_correo_verificado_por_google_no_exige_lista_blanca(monkeypatch):
    monkeypatch.delenv("CORREOS_SOLO_CONOCIDOS", raising=False)
    assert correos_temporales.validar("a@empresa-rara-xyz.cl", verificado_por_google=True) is None
    assert "temporales" in correos_temporales.validar("x@mailinator.com", verificado_por_google=True)


# ── Administradores (root) ───────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def multiusuario(monkeypatch):
    monkeypatch.setattr(roles.sesiones_capital, "MULTIUSUARIO", True)
    monkeypatch.setattr(roles, "_rol_en_base", lambda _id: None)
    monkeypatch.setattr(configuracion, "ROOT_CORREOS", frozenset({"admin@ejemplo.cl"}))


def test_un_correo_de_la_lista_root_es_administrador(multiusuario):
    assert roles.es_root({"id": 1, "email": " ADMIN@ejemplo.cl "}) is True


def test_un_usuario_comun_o_sin_sesion_no_es_administrador(multiusuario):
    assert roles.es_root({"id": 2, "email": "otro@ejemplo.cl"}) is False
    assert roles.es_root(None) is False
    assert roles.es_root("admin@ejemplo.cl") is False


def test_el_rol_root_en_la_base_tambien_vale(multiusuario, monkeypatch):
    monkeypatch.setattr(roles, "_rol_en_base", lambda _id: roles.ROL_ROOT)
    assert roles.es_root({"id": 3, "email": "x@ejemplo.cl"}) is True


# ── reCAPTCHA (Google se reemplaza por respuestas simuladas) ─────────────────────────────────────────────

@pytest.fixture
def captcha(monkeypatch):
    for nombre in ("V3_SITIO", "V3_SECRETA", "V2_SITIO", "V2_SECRETA"):
        monkeypatch.setattr(configuracion, f"RECAPTCHA_{nombre}", "x")
    monkeypatch.setattr(configuracion, "RECAPTCHA_ACTIVO", True)
    monkeypatch.setattr(configuracion, "RECAPTCHA_UMBRAL", 0.5)
    monkeypatch.setattr(configuracion, "RECAPTCHA_MODO", "ambos")
    respuestas = {}
    monkeypatch.setattr(recaptcha, "_consultar", lambda secreta, token, ip=None: respuestas.get(token))
    return respuestas


def test_sin_claves_la_proteccion_esta_apagada_y_acepta_todo(monkeypatch):
    monkeypatch.setattr(configuracion, "RECAPTCHA_ACTIVO", False)
    assert recaptcha.verificar("login").ok is True


def test_modo_ambos_exige_marcar_el_casillero(captcha):
    veredicto = recaptcha.verificar("login", token_v3="t3")
    assert veredicto.ok is False and veredicto.pedir_v2 is True


def test_modo_ambos_acepta_v2_y_v3_buenos(captcha):
    captcha.update({"t2": {"success": True}, "t3": {"success": True, "action": "login", "score": 0.9}})
    veredicto = recaptcha.verificar("login", token_v3="t3", token_v2="t2")
    assert veredicto.ok is True and veredicto.puntaje == 0.9


def test_modo_ambos_rechaza_un_puntaje_bajo(captcha):
    captcha.update({"t2": {"success": True}, "t3": {"success": True, "action": "login", "score": 0.2}})
    assert recaptcha.verificar("login", token_v3="t3", token_v2="t2").ok is False


def test_modo_ambos_rechaza_un_token_de_otra_accion(captcha):
    captcha.update({"t2": {"success": True}, "t3": {"success": True, "action": "registro", "score": 0.9}})
    assert recaptcha.verificar("login", token_v3="t3", token_v2="t2").ok is False


def test_si_google_no_responde_se_rechaza(captcha):
    veredicto = recaptcha.verificar("login", token_v3="t3", token_v2="t2")
    assert veredicto.ok is False and veredicto.mensaje == recaptcha.MENSAJE_SIN_SERVICIO


def test_modo_respaldo_acepta_v3_bueno_sin_casillero(captcha, monkeypatch):
    monkeypatch.setattr(configuracion, "RECAPTCHA_MODO", "respaldo")
    captcha["t3"] = {"success": True, "action": "login", "score": 0.8}
    assert recaptcha.verificar("login", token_v3="t3").ok is True


def test_modo_respaldo_pide_el_casillero_si_el_puntaje_es_bajo(captcha, monkeypatch):
    monkeypatch.setattr(configuracion, "RECAPTCHA_MODO", "respaldo")
    captcha["t3"] = {"success": True, "action": "login", "score": 0.1}
    veredicto = recaptcha.verificar("login", token_v3="t3")
    assert veredicto.ok is False and veredicto.pedir_v2 is True


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara test_seguridad_auditoria .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
