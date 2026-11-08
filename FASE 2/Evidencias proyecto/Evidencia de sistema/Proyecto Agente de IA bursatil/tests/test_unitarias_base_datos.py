# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------- INICIO Piña y Jara test_unitarias_base_datos .PY ---------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_unitarias_base_datos.py
----------------------------
Pruebas unitarias del adaptador de PostgreSQL (herramientas/base_datos_postgres.py): construcción del SQL, parámetros,
protecciones y selector de motor. No necesitan una base de datos: solo arman las sentencias.
"""
import pytest

from herramientas import base_datos, base_datos_postgres as bd


@pytest.fixture
def cliente():
    return bd.ClientePostgres({"host": "no-se-conecta"})


def test_select_con_filtro_orden_y_limite(cliente):
    sql, params = cliente.table("usuarios").select("id,nombre").eq("email", "a@b.cl").order("id", desc=True).limit(5).armar_sql()
    assert sql == 'SELECT "id", "nombre" FROM "usuarios" WHERE "email" = %s ORDER BY "id" DESC LIMIT 5'
    assert params == ["a@b.cl"]


def test_insert_devuelve_las_filas(cliente):
    sql, params = cliente.table("watchlist_usuario").insert({"usuario_id": 1, "simbolo": "EURUSD"}).armar_sql()
    assert sql.startswith('INSERT INTO "watchlist_usuario" ("usuario_id", "simbolo") VALUES (%s, %s)')
    assert sql.endswith("RETURNING *")
    assert params == [1, "EURUSD"]


def test_upsert_actualiza_en_conflicto(cliente):
    sql, _ = cliente.table("planes_usuario").upsert({"usuario_id": 1, "plan": "pro"}, on_conflict="usuario_id").armar_sql()
    assert 'ON CONFLICT ("usuario_id") DO UPDATE SET "plan" = EXCLUDED."plan"' in sql


def test_update_y_delete_con_filtro(cliente):
    sql, params = cliente.table("copias").update({"estado": "cerrada"}).eq("id", 3).armar_sql()
    assert sql.startswith('UPDATE "copias" SET "estado" = %s WHERE "id" = %s') and params == ["cerrada", 3]
    sql, params = cliente.table("copias").delete().eq("id", 3).armar_sql()
    assert sql.startswith('DELETE FROM "copias" WHERE "id" = %s') and params == [3]


def test_update_y_delete_sin_filtro_se_rechazan(cliente):
    with pytest.raises(bd.ErrorBaseDatos):
        cliente.table("copias").update({"estado": "x"}).armar_sql()
    with pytest.raises(bd.ErrorBaseDatos):
        cliente.table("copias").delete().armar_sql()


def test_filtro_in_usa_any(cliente):
    sql, params = cliente.table("t").select("*").in_("id", [1, 2, 3]).armar_sql()
    assert 'WHERE "id" = ANY(%s)' in sql and params == [[1, 2, 3]]


def test_los_valores_siempre_van_como_parametros_y_nunca_en_el_sql(cliente):
    malicioso = "x'; DROP TABLE usuarios; --"
    sql, params = cliente.table("usuarios").select("*").eq("email", malicioso).armar_sql()
    assert malicioso not in sql and "DROP" not in sql
    assert params == [malicioso]


@pytest.mark.parametrize("nombre", ["usuarios; DROP TABLE x", 'a"b', "a b", "", "tabla--", "1; select"])
def test_identificadores_peligrosos_se_rechazan(nombre):
    with pytest.raises(bd.ErrorBaseDatos):
        bd._identificador(nombre)


def test_identificador_valido_se_entrecomilla():
    assert bd._identificador("usuarios") == '"usuarios"'


def test_el_selector_elige_supabase_por_defecto(monkeypatch):
    monkeypatch.delenv("BASE_DATOS", raising=False)
    assert base_datos.motor() == "supabase"


@pytest.mark.parametrize("valor, esperado", [("postgres", "postgres"), ("POSTGRES", "postgres"), (" supabase ", "supabase")])
def test_el_selector_acepta_los_motores_validos(monkeypatch, valor, esperado):
    monkeypatch.setenv("BASE_DATOS", valor)
    assert base_datos.motor() == esperado


def test_un_motor_invalido_se_rechaza_con_un_mensaje_claro(monkeypatch):
    monkeypatch.setenv("BASE_DATOS", "mongodb")
    with pytest.raises(bd.ErrorBaseDatos) as error:
        base_datos.motor()
    assert "BASE_DATOS" in str(error.value)
    assert base_datos.hay_credenciales() is False


def test_hay_credenciales_exige_todas_las_variables_del_motor(monkeypatch):
    monkeypatch.setenv("BASE_DATOS", "postgres")
    for var in base_datos.VARIABLES_POSTGRES:
        monkeypatch.setenv(var, "x")
    assert base_datos.hay_credenciales() is True
    monkeypatch.delenv(base_datos.VARIABLES_POSTGRES[0])
    assert base_datos.hay_credenciales() is False


def test_variables_postgres_son_las_documentadas():
    import inspect
    fuente = inspect.getsource(bd.crear_cliente_desde_entorno)
    for var in ("POSTGRES_SERVIDOR", "POSTGRES_PUERTO", "POSTGRES_BASE_DATOS", "POSTGRES_USUARIO", "POSTGRES_CONTRASENA"):
        assert var in fuente


# -------------------------------------------------------------------------------------------------------
# ---------------------------- FIN Piña y Jara test_unitarias_base_datos .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
