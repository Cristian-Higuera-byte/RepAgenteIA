# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------- INICIO Piña y Jara test_unitarias_seguridad_y_cifrado .PY ----------------------
# -------------------------------------------------------------------------------------------------------

"""
test_unitarias_seguridad_y_cifrado.py
-------------------------------------
Pruebas unitarias de los mecanismos de seguridad: tokens firmados del servidor de precios, cifrado de credenciales,
hash de contraseñas y hash de tokens de sesión y de enlaces.
"""
import base64
import json
import re

import pytest
from cryptography.fernet import Fernet, InvalidToken

from herramientas import credenciales_bolsa, gestor_autenticacion, sesion_persistente, token_datos, verificacion_correo


# ---- Tokens firmados del servidor de precios -------------------------------------------------------------

def test_token_emitido_se_verifica_y_devuelve_usuario_y_modo():
    token = token_datos.emitir(42, True, 60)
    assert token_datos.verificar(token) == (42, True)


def test_token_de_cuenta_real_conserva_el_modo():
    assert token_datos.verificar(token_datos.emitir(7, False, 60)) == (7, False)


def test_token_alterado_se_rechaza():
    token = token_datos.emitir(42, True, 60)
    alterado = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    assert token_datos.verificar(alterado) is None


def test_token_con_la_carga_cambiada_se_rechaza():
    token = token_datos.emitir(42, True, 60)
    carga, firma = token.split(".")
    relleno = "=" * (-len(carga) % 4)
    datos = json.loads(base64.urlsafe_b64decode(carga + relleno))
    datos_otro = json.dumps({**datos, "u": 99} if "u" in datos else {**datos, "usuario_id": 99}).encode()
    falso = base64.urlsafe_b64encode(datos_otro).decode().rstrip("=") + "." + firma
    assert token_datos.verificar(falso) is None


def test_token_vencido_se_rechaza():
    assert token_datos.verificar(token_datos.emitir(42, True, -5)) is None


@pytest.mark.parametrize("basura", ["", "abc", "a.b", "a.b.c", None, "....", "x" * 500])
def test_tokens_mal_formados_se_rechazan_sin_lanzar_error(basura):
    assert token_datos.verificar(basura) is None


def test_el_token_no_contiene_credenciales_ni_el_secreto():
    token = token_datos.emitir(42, True, 60)
    carga = token.split(".")[0]
    texto = base64.urlsafe_b64decode(carga + "=" * (-len(carga) % 4)).decode()
    assert "s" * 48 not in texto
    assert not re.search(r"password|contrasena|api_key|secret", texto, re.I)


def test_sin_secreto_valido_no_se_emiten_tokens(monkeypatch):
    monkeypatch.setenv("SERVIDOR_SECRETO", "corto")
    assert token_datos.emitir(1, True) == ""
    monkeypatch.setenv("SERVIDOR_SECRETO", "s" * 48)


def test_el_secreto_generado_tiene_al_menos_32_caracteres():
    assert len(token_datos.generar_secreto()) >= 32


# ---- Cifrado de credenciales -----------------------------------------------------------------------------

def test_el_cifrado_es_reversible_y_no_deja_el_texto_en_claro():
    secreto = "MiApiKey-SuperSecreta-123"
    cifrado = credenciales_bolsa._cifrar(secreto)
    assert secreto not in cifrado
    assert credenciales_bolsa._descifrar(cifrado) == secreto


def test_dos_cifrados_del_mismo_texto_son_distintos():
    assert credenciales_bolsa._cifrar("igual") != credenciales_bolsa._cifrar("igual")


def test_con_otra_clave_no_se_puede_descifrar(monkeypatch):
    cifrado = credenciales_bolsa._cifrar("dato")
    monkeypatch.setenv("CREDENCIALES_CLAVES", Fernet.generate_key().decode())
    with pytest.raises(InvalidToken):
        credenciales_bolsa._descifrar(cifrado)


def test_rotacion_de_clave_la_primera_cifra_y_todas_descifran(monkeypatch):
    vieja = Fernet.generate_key().decode()
    monkeypatch.setenv("CREDENCIALES_CLAVES", vieja)
    cifrado_viejo = credenciales_bolsa._cifrar("dato")
    nueva = Fernet.generate_key().decode()
    monkeypatch.setenv("CREDENCIALES_CLAVES", nueva + "," + vieja)
    assert credenciales_bolsa._descifrar(cifrado_viejo) == "dato"
    assert Fernet(nueva.encode()).decrypt(credenciales_bolsa._cifrar("otro").encode()) == b"otro"


def test_las_claves_generadas_son_validas_para_fernet():
    Fernet(credenciales_bolsa.generar_clave().encode())


# ---- Contraseñas y hashes --------------------------------------------------------------------------------

def test_la_contrasena_se_guarda_con_hash_y_sal():
    h1 = gestor_autenticacion._cifrar_contrasena("Panzen2020.")
    h2 = gestor_autenticacion._cifrar_contrasena("Panzen2020.")
    assert "Panzen2020." not in h1
    assert h1 != h2                                           # sal distinta en cada hash
    assert gestor_autenticacion._verificar_contrasena("Panzen2020.", h1) is True
    assert gestor_autenticacion._verificar_contrasena("otra", h1) is False


def test_el_hash_de_contrasenas_usa_muchas_iteraciones():
    assert gestor_autenticacion._ITERACIONES >= 100_000


def test_validar_contrasena_del_gestor_rechaza_claves_debiles():
    assert gestor_autenticacion.validar_contrasena("abc") is not None
    assert gestor_autenticacion.validar_contrasena("Panzen2020.") is None


def test_hash_de_tokens_es_sha256_determinista():
    h = verificacion_correo.hash_de("token-de-prueba")
    assert re.fullmatch(r"[0-9a-f]{64}", h)
    assert h == verificacion_correo.hash_de("token-de-prueba")
    assert sesion_persistente._hash("token-de-prueba") == h


# -------------------------------------------------------------------------------------------------------
# ----------------------- FIN Piña y Jara test_unitarias_seguridad_y_cifrado .PY ------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
