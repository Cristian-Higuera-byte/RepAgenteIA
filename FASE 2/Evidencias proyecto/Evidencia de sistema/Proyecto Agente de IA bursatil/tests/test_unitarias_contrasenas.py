# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------- INICIO Piña y Jara test_unitarias_contrasenas .PY --------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_unitarias_contrasenas.py
-----------------------------
Pruebas unitarias de la regla de contraseña fuerte (herramientas/contrasenas.py): requisitos, medidor de fuerza y claves comunes.
"""
import pytest

from herramientas import contrasenas


def test_los_cinco_requisitos_se_evaluan_en_orden():
    r = contrasenas.evaluar("Abc123!x")
    assert [c for _, c in r] == [True, True, True, True, True]
    assert len(r) == 5


@pytest.mark.parametrize("clave, indice", [
    ("Ab1!", 0),              # menos de 8 caracteres
    ("abcdefg1!", 1),         # sin mayúscula
    ("ABCDEFG1!", 2),         # sin minúscula
    ("Abcdefgh!", 3),         # sin número
    ("Abcdefg12", 4),         # sin símbolo
])
def test_cada_requisito_incumplido_se_detecta(clave, indice):
    assert contrasenas.evaluar(clave)[indice][1] is False
    assert contrasenas.validar(clave) is not None


@pytest.mark.parametrize("clave", ["Panzen2020.", "Tr4ding#Seguro9", "Mi_Clave-Larga_2026!", "Zx9$kLm2#Qw"])
def test_claves_fuertes_son_aceptadas_y_llenan_las_cuatro_barras(clave):
    assert contrasenas.validar(clave) is None
    assert contrasenas.barras(clave) == 4


@pytest.mark.parametrize("clave", ["Password1!", "P@ssw0rd!", "Qwerty123!", "Admin123$", "Hola1234!"])
def test_claves_comunes_disfrazadas_se_rechazan(clave):
    assert contrasenas.es_comun(clave) is True
    assert contrasenas.validar(clave) == contrasenas.AVISO_COMUN
    assert contrasenas.barras(clave) <= 1


def test_clave_de_un_solo_caracter_repetido_es_comun():
    assert contrasenas.es_comun("aaaaaaaa") is True


@pytest.mark.parametrize("entrada", [None, "", "   "])
def test_entradas_vacias_no_rompen_y_se_rechazan(entrada):
    assert contrasenas.validar(entrada) is not None
    assert contrasenas.barras(entrada) == 0 or contrasenas.barras(entrada) == 1


def test_los_avisos_estan_en_espanol():
    assert "mayúscula" in contrasenas.AVISO_REQUISITOS
    assert "Mínimo 8" in contrasenas.TEXTO_AYUDA


# -------------------------------------------------------------------------------------------------------
# --------------------------- FIN Piña y Jara test_unitarias_contrasenas .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
