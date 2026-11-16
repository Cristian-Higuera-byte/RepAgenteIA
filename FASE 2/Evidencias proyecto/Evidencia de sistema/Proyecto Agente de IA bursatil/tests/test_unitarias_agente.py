# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------- INICIO Piña y Jara test_unitarias_agente .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_unitarias_agente.py
------------------------
Pruebas unitarias del núcleo del agente: registro de herramientas, tipos de respuesta del modelo, estado del turno,
límites de riesgo y matriz de planes.
"""
import dataclasses
import json
import time

import pytest

from herramientas import permisos_plan
from herramientas_agente.base.registro import Herramienta, RegistroHerramientas
from nucleo_agente.llm.tipos import LlamadaHerramienta, RespuestaLLM
from nucleo_agente.ordenes.limites import LIMITES, LimitesRiesgo
from nucleo_agente.turnos.turno import Turno


def _herramienta(nombre="suma", funcion=None):
    return Herramienta(nombre=nombre, descripcion="Suma dos números", parametros={"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}},
                       funcion=funcion or (lambda a, b: {"resultado": a + b}))


def test_el_registro_ejecuta_una_herramienta_y_devuelve_json():
    registro = RegistroHerramientas()
    registro.registrar(_herramienta())
    salida = registro.ejecutar("suma", {"a": 2, "b": 3})
    assert json.loads(salida)["resultado"] == 5


def test_no_se_pueden_registrar_dos_herramientas_con_el_mismo_nombre():
    registro = RegistroHerramientas()
    registro.registrar(_herramienta())
    with pytest.raises(ValueError):
        registro.registrar(_herramienta())


def test_herramienta_inexistente_devuelve_error_json_sin_lanzar():
    registro = RegistroHerramientas()
    registro.registrar(_herramienta())
    salida = registro.ejecutar("no_existe", {})
    assert isinstance(json.loads(salida), dict)
    assert "suma" in salida                                   # informa al modelo qué herramientas hay


def test_una_herramienta_que_falla_nunca_propaga_la_excepcion():
    registro = RegistroHerramientas()
    registro.registrar(_herramienta("rota", lambda **_: 1 / 0))
    salida = registro.ejecutar("rota", {})
    assert "error" in json.loads(salida)


def test_argumentos_incorrectos_no_rompen_el_registro():
    registro = RegistroHerramientas()
    registro.registrar(_herramienta())
    assert isinstance(json.loads(registro.ejecutar("suma", {"x": 1})), dict)


def test_los_esquemas_tienen_el_formato_de_function_calling():
    registro = RegistroHerramientas()
    registro.registrar(_herramienta())
    esquema = registro.esquemas()[0]
    assert esquema["type"] == "function" and esquema["function"]["name"] == "suma"
    assert registro.nombres() == ["suma"]


def test_la_herramienta_es_inmutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        _herramienta().nombre = "otra"


def test_respuesta_del_modelo_con_llamadas_arma_el_mensaje_assistant():
    r = RespuestaLLM(contenido="", razonamiento=None, llamadas=[LlamadaHerramienta(id="1", nombre="suma", argumentos={"a": 1}, argumentos_raw='{"a": 1}', error=None)],
                     tokens_entrada=10, tokens_salida=5, perfil="analisis")
    m = r.mensaje
    assert m["role"] == "assistant" and m["tool_calls"][0]["function"]["name"] == "suma"


def test_turno_calcula_su_duracion():
    t = Turno(usuario_id="1", prompt="hola")
    t.t_inicio = time.time() - 2
    assert t.duracion >= 2


def test_los_limites_de_riesgo_son_inmutables_y_sus_valores_por_defecto_son_los_documentados():
    with pytest.raises(dataclasses.FrozenInstanceError):
        LIMITES.vigencia_propuesta_min = 999
    assert LIMITES.vigencia_propuesta_min == 10
    assert LIMITES.riesgo_max_por_operacion_pct is None      # sin tope hasta que el usuario lo defina
    assert isinstance(LimitesRiesgo(), LimitesRiesgo)


def test_el_plan_gratis_no_incluye_limites_personalizados_y_el_basico_si():
    assert permisos_plan.permite("limites_agente", "gratis") is False
    assert permisos_plan.permite("limites_agente", "basico") is True
    assert permisos_plan.plan_minimo("limites_agente") == "basico"


# -------------------------------------------------------------------------------------------------------
# ------------------------------ FIN Piña y Jara test_unitarias_agente .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
