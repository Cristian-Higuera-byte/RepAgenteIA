# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara test_rendimiento .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_rendimiento.py
-------------------
Pruebas de rendimiento de las operaciones internas del sistema: cada una repite una operación muchas veces y comprueba que
el tiempo total esté bajo un tope. Las mediciones se guardan en tests/_resultados/rendimiento.json como evidencia.
No miden la red, el bróker ni el modelo de lenguaje (eso se prueba en producción con el servidor real).
"""
from datetime import datetime, timedelta, timezone

import pytest

from conftest import registrar_medicion
from herramientas import contrasenas, credenciales_bolsa, token_datos, verificacion_correo as vc
from herramientas import base_datos_postgres as bd
from herramientas_agente.base.registro import Herramienta, RegistroHerramientas
from nucleo_agente.ordenes import base_datos, tablero


def test_validar_contrasenas(cronometro):
    seg = cronometro(lambda i: contrasenas.validar(f"Clave-Fuerte-{i}!x"), 10_000)
    registrar_medicion("validar_contrasena", seg, 10_000)
    assert seg < 3.0


def test_emitir_y_verificar_tokens(cronometro):
    seg = cronometro(lambda i: token_datos.verificar(token_datos.emitir(i, True, 60)), 2_000)
    registrar_medicion("emitir_y_verificar_token", seg, 2_000)
    assert seg < 1.5


def test_cifrar_y_descifrar_credenciales(cronometro):
    seg = cronometro(lambda i: credenciales_bolsa._descifrar(credenciales_bolsa._cifrar(f"api-key-{i}")), 500)
    registrar_medicion("cifrar_y_descifrar_credencial", seg, 500)
    assert seg < 2.0


def test_armar_consultas_sql(cronometro):
    cliente = bd.ClientePostgres({"host": "x"})
    seg = cronometro(lambda i: cliente.table("operaciones").select("*").eq("usuario_id", i).eq("estado", "abierta").order("abierta_en", desc=True).limit(50).armar_sql(), 2_000)
    registrar_medicion("armar_consulta_sql", seg, 2_000)
    assert seg < 1.0


def test_ejecutar_herramientas_del_agente(cronometro):
    registro = RegistroHerramientas()
    registro.registrar(Herramienta("eco", "Devuelve lo recibido", {"type": "object", "properties": {}}, lambda **k: {"recibido": k}))
    seg = cronometro(lambda i: registro.ejecutar("eco", {"valor": i}), 5_000)
    registrar_medicion("ejecutar_herramienta", seg, 5_000)
    assert seg < 1.5


def test_crear_y_consumir_enlaces_de_correo(cliente_memoria, cronometro):
    base = datetime(2026, 11, 8, tzinfo=timezone.utc)

    def uno(i):
        token = vc.crear_enlace(cliente_memoria, i, vc.VERIFICACION, base)
        assert vc.consumir(cliente_memoria, token, vc.VERIFICACION, base + timedelta(minutes=1)) == i
    seg = cronometro(uno, 300)
    registrar_medicion("crear_y_consumir_enlace", seg, 300)
    assert seg < 3.0


def test_registrar_y_listar_ordenes_en_sqlite(tmp_path, monkeypatch, cronometro):
    monkeypatch.setattr(base_datos, "RUTA_DB", tmp_path / "rend.db")
    monkeypatch.setattr(base_datos, "_DB_PREPARADA", None)
    seg = cronometro(lambda i: base_datos._insertar(estado="PENDIENTE", accion="abrir", simbolo="XAUUSD", lado="compra", volumen=0.1, sl=1.0, justificacion="rendimiento"), 300)
    registrar_medicion("insertar_orden_sqlite", seg, 300)
    assert seg < 6.0
    assert len(tablero.listar_pendientes()) == 300


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara test_rendimiento .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
