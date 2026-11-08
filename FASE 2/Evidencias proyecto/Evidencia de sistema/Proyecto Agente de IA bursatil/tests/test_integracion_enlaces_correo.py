# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------- INICIO Piña y Jara test_integracion_enlaces_correo .PY ------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_integracion_enlaces_correo.py
----------------------------------
Pruebas de integración de los enlaces de verificación de correo y de recuperación de contraseña
(herramientas/verificacion_correo.py) sobre una base de datos en memoria: un solo uso, vencimiento, límites de envío y tipo.
"""
from datetime import datetime, timedelta, timezone

import pytest

from herramientas import verificacion_correo as vc

BASE = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)


def test_el_token_no_se_guarda_solo_su_hash(cliente_memoria):
    token = vc.crear_enlace(cliente_memoria, 1, vc.VERIFICACION, BASE)
    filas = cliente_memoria.tablas["enlaces_correo"]
    assert len(filas) == 1 and token not in str(filas)
    assert filas[0]["token_hash"] == vc.hash_de(token)


def test_un_enlace_vigente_se_consume_una_sola_vez(cliente_memoria):
    token = vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE)
    assert vc.consumir(cliente_memoria, token, vc.VERIFICACION, BASE + timedelta(minutes=5)) == 7
    assert vc.consumir(cliente_memoria, token, vc.VERIFICACION, BASE + timedelta(minutes=6)) is None


def test_el_enlace_de_verificacion_vence_a_las_24_horas(cliente_memoria):
    token = vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE)
    assert vc.consumir(cliente_memoria, token, vc.VERIFICACION, BASE + timedelta(hours=24, minutes=1)) is None


def test_el_enlace_de_verificacion_sirve_antes_de_vencer(cliente_memoria):
    token = vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE)
    assert vc.consumir(cliente_memoria, token, vc.VERIFICACION, BASE + timedelta(hours=23, minutes=59)) == 7


def test_el_enlace_de_recuperacion_vence_a_los_60_minutos(cliente_memoria):
    t1 = vc.crear_enlace(cliente_memoria, 7, vc.RECUPERACION, BASE)
    assert vc.consumir(cliente_memoria, t1, vc.RECUPERACION, BASE + timedelta(minutes=61)) is None
    t2 = vc.crear_enlace(cliente_memoria, 8, vc.RECUPERACION, BASE)
    assert vc.consumir(cliente_memoria, t2, vc.RECUPERACION, BASE + timedelta(minutes=59)) == 8


def test_un_enlace_no_sirve_para_otro_tipo(cliente_memoria):
    token = vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE)
    assert vc.consumir(cliente_memoria, token, vc.RECUPERACION, BASE) is None


@pytest.mark.parametrize("token", ["", None, "   ", "inventado"])
def test_tokens_vacios_o_falsos_no_consumen_nada(cliente_memoria, token):
    vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE)
    assert vc.consumir(cliente_memoria, token, vc.VERIFICACION, BASE) is None


def test_no_se_puede_pedir_otro_enlace_antes_de_un_minuto(cliente_memoria):
    vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE)
    with pytest.raises(vc.ErrorEnlace):
        vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE + timedelta(seconds=30))
    vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE + timedelta(seconds=61))


def test_maximo_cinco_enlaces_al_dia(cliente_memoria):
    for i in range(vc.MAXIMO_ENVIOS_POR_DIA):
        vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE + timedelta(minutes=2 * i))
    with pytest.raises(vc.ErrorEnlace):
        vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE + timedelta(minutes=30))


def test_los_limites_son_por_usuario(cliente_memoria):
    vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE)
    vc.crear_enlace(cliente_memoria, 8, vc.VERIFICACION, BASE)            # otro usuario: no hay límite compartido


def test_un_enlace_nuevo_invalida_al_anterior(cliente_memoria):
    viejo = vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE)
    nuevo = vc.crear_enlace(cliente_memoria, 7, vc.VERIFICACION, BASE + timedelta(minutes=2))
    assert vc.consumir(cliente_memoria, viejo, vc.VERIFICACION, BASE + timedelta(minutes=3)) is None
    assert vc.consumir(cliente_memoria, nuevo, vc.VERIFICACION, BASE + timedelta(minutes=3)) == 7


def test_la_direccion_del_correo_usa_la_url_publica_configurada():
    enlace = vc.armar_enlace("TOKEN", vc.VERIFICACION)
    assert enlace == "https://plataforma.prueba/?verificar=TOKEN"
    assert vc.armar_enlace("T", vc.RECUPERACION).endswith("?recuperar=T")


def test_sin_url_publica_no_se_arma_el_enlace(monkeypatch):
    monkeypatch.delenv("PLATAFORMA_URL")
    with pytest.raises(vc.ErrorEnlace):
        vc.armar_enlace("T", vc.VERIFICACION)
    monkeypatch.setenv("PLATAFORMA_URL", "https://plataforma.prueba")


def test_si_falla_el_envio_se_borra_el_enlace_y_no_cuenta_contra_el_limite(cliente_memoria, monkeypatch):
    def falla(*_a, **_k):
        raise vc.correo.ErrorCorreo("sin servidor")
    monkeypatch.setattr(vc.correo, "enviar", falla)
    with pytest.raises(vc.ErrorEnlace):
        vc.enviar_enlace(cliente_memoria, 7, "Ana", "ana@correo.cl", vc.VERIFICACION)
    assert cliente_memoria.tablas["enlaces_correo"] == []


def test_si_el_envio_resulta_bien_el_enlace_queda_guardado(cliente_memoria, monkeypatch):
    enviados = []
    monkeypatch.setattr(vc.correo, "enviar", lambda *a, **k: enviados.append(a))
    vc.enviar_enlace(cliente_memoria, 7, "Ana", "ana@correo.cl", vc.VERIFICACION)
    assert len(enviados) == 1 and "https://plataforma.prueba/?verificar=" in enviados[0][2]
    assert len(cliente_memoria.tablas["enlaces_correo"]) == 1


# -------------------------------------------------------------------------------------------------------
# ------------------------- FIN Piña y Jara test_integracion_enlaces_correo .PY -------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
