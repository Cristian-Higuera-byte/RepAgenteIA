# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------- INICIO Piña y Jara _prueba_base_datos_postgres .PY ------------------------
# -------------------------------------------------------------------------------------------------------

"""
_prueba_base_datos_postgres.py
------------------------------
Pruebas del adaptador `herramientas/base_datos_postgres.py` que NO necesitan una base de datos ni red.

Parte 1: casos concretos. Se arma cada consulta con un cliente falso que anota el SQL en vez de ejecutarlo y se compara con lo esperado.
Parte 2: cobertura real. Se recorre todo el código del proyecto, se encuentran las cadenas `cliente.table(...)...` y `cliente.rpc(...)...`
         y se comprueba que cada método encadenado y cada texto de columnas existan en el adaptador.

Uso (desde la carpeta del proyecto):  env\\Scripts\\python _prueba_base_datos_postgres.py
"""
import ast
import os
import sys
from decimal import Decimal
from datetime import date, datetime, timezone

from herramientas import base_datos_postgres as bd

RAIZ = os.path.dirname(os.path.abspath(__file__))
CARPETAS = ("herramientas", "componentes_plataforma", "nucleo_agente", "aplicacion_principal")
fallos: list = []


# TITULO CLIENTE FALSO

class ClienteFalso(bd.ClientePostgres):
    """Cliente que guarda el SQL que recibe en lugar de ejecutarlo contra una base de datos."""

    def __init__(self):
        """Crea el cliente sin conexión real y con una lista donde se anotan las sentencias."""
        super().__init__({})
        self.sentencias: list = []

    def ejecutar_sentencia(self, sentencia, parametros=None, reintentable=False):
        """Anota la sentencia y sus parámetros, y devuelve una fila de conteo para que count="exact" funcione."""
        self.sentencias.append((sentencia, list(parametros or [])))
        return [{"cantidad": 7}] if "COUNT(*)" in sentencia else []

    def clave_primaria(self, tabla):
        """Devuelve una clave primaria fija de prueba."""
        return ["usuario_id"]


# TITULO COMPROBAR

def comprobar(nombre: str, obtenido, esperado) -> None:
    """Compara lo obtenido con lo esperado; anota el fallo y lo muestra si no coinciden."""
    if obtenido != esperado:
        fallos.append(nombre)
        print(f"  FALLA {nombre}\n    esperado: {esperado}\n    obtenido: {obtenido}")


# TITULO CASOS DE SQL

def probar_casos() -> int:
    """Parte 1: arma las consultas más típicas del proyecto y revisa el SQL y los parámetros generados."""
    cliente = ClienteFalso()
    t = cliente.table
    casos = [
        ("select simple", t("usuarios").select("id, nombre").eq("email", "a@b.cl").limit(1).armar_sql(),
         ('SELECT "id", "nombre" FROM "usuarios" WHERE "email" = %s LIMIT 1', ["a@b.cl"])),
        ("select todo, orden", t("estrategias").select("*").order("id", desc=True).armar_sql(),
         ('SELECT * FROM "estrategias" ORDER BY "id" DESC', [])),
        ("eq None es IS NULL", t("copias").select("id").eq("cerrada_en", None).armar_sql(),
         ('SELECT "id" FROM "copias" WHERE "cerrada_en" IS NULL', [])),
        ("is_ null", t("comisiones_rendimiento").select("copia_id").is_("movimiento_billetera_id", "null").armar_sql(),
         ('SELECT "copia_id" FROM "comisiones_rendimiento" WHERE "movimiento_billetera_id" IS NULL', [])),
        ("in_ lista", t("estrategias").select("id").in_("id", [1, 2, 3]).armar_sql(),
         ('SELECT "id" FROM "estrategias" WHERE "id" = ANY(%s)', [[1, 2, 3]])),
        ("in_ vacia", t("estrategias").select("id").in_("id", []).armar_sql(),
         ('SELECT "id" FROM "estrategias" WHERE FALSE', [])),
        ("gte y lt", t("sesiones_persistentes").delete().lt("expira_en", "2026-10-28").armar_sql(),
         ('DELETE FROM "sesiones_persistentes" WHERE "expira_en" < %s RETURNING *', ["2026-10-28"])),
        ("range", t("operaciones").select("*").range(1000, 1999).armar_sql(),
         ('SELECT * FROM "operaciones" LIMIT 1000 OFFSET 1000', [])),
        ("insert dict", t("usuarios").insert({"nombre": "Ana", "email": "a@b.cl"}).armar_sql(),
         ('INSERT INTO "usuarios" ("nombre", "email") VALUES (%s, %s) RETURNING *', ["Ana", "a@b.cl"])),
        ("insert lista con columnas faltantes",
         t("agente_mensajes").insert([{"chat_id": 1, "orden": 1, "turno": 1, "mensaje": {"a": 1}}, {"chat_id": 1, "orden": 2, "turno": 1}]).armar_sql(),
         ('INSERT INTO "agente_mensajes" ("chat_id", "orden", "turno", "mensaje") VALUES (%s, %s, %s, %s), (%s, %s, %s, DEFAULT) RETURNING *',
          [1, 1, 1, {"a": 1}, 1, 2, 1])),
        ("upsert con conflicto", t("credenciales_bolsa").upsert({"usuario_id": 1, "es_demo": True, "version": 1}, on_conflict="usuario_id,es_demo").armar_sql(),
         ('INSERT INTO "credenciales_bolsa" ("usuario_id", "es_demo", "version") VALUES (%s, %s, %s) ON CONFLICT ("usuario_id", "es_demo") '
          'DO UPDATE SET "version" = EXCLUDED."version" RETURNING *', [1, True, 1])),
        ("upsert por clave primaria", t("planes_usuario").upsert({"usuario_id": 1, "plan": "pro"}).armar_sql(),
         ('INSERT INTO "planes_usuario" ("usuario_id", "plan") VALUES (%s, %s) ON CONFLICT ("usuario_id") DO UPDATE SET "plan" = EXCLUDED."plan" RETURNING *',
          [1, "pro"])),
        ("upsert solo claves", t("estrategias_favoritas").upsert({"usuario_id": 1}).armar_sql(),
         ('INSERT INTO "estrategias_favoritas" ("usuario_id") VALUES (%s) ON CONFLICT ("usuario_id") DO NOTHING RETURNING *', [1])),
        ("update", t("agente_chats").update({"titulo": "x"}).eq("id", 5).eq("usuario_id", 1).armar_sql(),
         ('UPDATE "agente_chats" SET "titulo" = %s WHERE "id" = %s AND "usuario_id" = %s RETURNING *', ["x", 5, 1])),
        ("delete", t("agente_memoria_usuario").delete().eq("usuario_id", 1).eq("clave", "k").armar_sql(),
         ('DELETE FROM "agente_memoria_usuario" WHERE "usuario_id" = %s AND "clave" = %s RETURNING *', [1, "k"])),
        ("rpc", cliente.rpc("billetera_mover", {"p_usuario": 1, "p_monto": 10}).armar_sql(),
         ('SELECT * FROM "billetera_mover"("p_usuario" := %s, "p_monto" := %s)', [1, 10])),
    ]
    for nombre, obtenido, esperado in casos:
        comprobar(nombre, obtenido, esperado)

    # execute: select con count y el conteo separado
    respuesta = cliente.table("copias").select("id", count="exact").eq("estado", "activa").limit(1).execute()
    comprobar("count exacto", respuesta.count, 7)
    comprobar("count usa otra sentencia sin limite", cliente.sentencias[-1][0], 'SELECT COUNT(*) AS cantidad FROM "copias" WHERE "estado" = %s')

    # seguridad: nombres raros y operaciones sin filtro
    for nombre, accion in [("tabla con inyeccion", lambda: cliente.table('usuarios"; DROP TABLE x;--')),
                           ("columna con inyeccion", lambda: cliente.table("usuarios").eq("id; --", 1)),
                           ("select con relacion", lambda: cliente.table("usuarios").select("id, perfiles(*)")),
                           ("update sin filtro", lambda: cliente.table("usuarios").update({"nombre": "x"}).armar_sql()),
                           ("delete sin filtro", lambda: cliente.table("usuarios").delete().armar_sql()),
                           ("is_ invalido", lambda: cliente.table("usuarios").is_("id", "otra"))]:
        try:
            accion()
            comprobar(nombre + " debe fallar", "no fallo", "ErrorBaseDatos")
        except bd.ErrorBaseDatos:
            pass

    # conversión de valores como los entrega Supabase
    comprobar("decimal con decimales", bd._convertir_valor(Decimal("12.50")), 12.5)
    comprobar("decimal entero", bd._convertir_valor(Decimal("100")), 100)
    comprobar("fecha con hora", bd._convertir_valor(datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc)), "2026-10-28T12:00:00+00:00")
    comprobar("fecha", bd._convertir_valor(date(2026, 10, 28)), "2026-10-28")
    return len(casos) + 11


# TITULO COBERTURA

def raiz_de_cadena(nodo):
    """Sigue una cadena de llamadas hacia atrás y devuelve (nombre de la raíz table/rpc o None, métodos encadenados)."""
    metodos = []
    while isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
        if nodo.func.attr in ("table", "rpc"):
            return nodo.func.attr, metodos
        metodos.append((nodo.func.attr, nodo))
        nodo = nodo.func.value
    return None, metodos


def probar_cobertura() -> int:
    """Parte 2: recorre el código real y verifica que cada método y cada texto de columnas usados existan en el adaptador."""
    disponibles = {nombre for nombre in dir(bd.ConstructorConsulta) if not nombre.startswith("_")} | \
                  {nombre for nombre in dir(bd.ConstructorFuncion) if not nombre.startswith("_")}
    cadenas = 0
    usados: dict = {}
    for carpeta in CARPETAS:
        for ruta, _, archivos in os.walk(os.path.join(RAIZ, carpeta)):
            for archivo in archivos:
                if not archivo.endswith(".py"):
                    continue
                camino = os.path.join(ruta, archivo)
                arbol = ast.parse(open(camino, encoding="utf-8").read(), filename=camino)
                for nodo in ast.walk(arbol):
                    if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute) and nodo.func.attr == "execute":
                        raiz, metodos = raiz_de_cadena(nodo)
                        if raiz is None:
                            continue
                        cadenas += 1
                        for nombre, llamada in metodos:
                            usados.setdefault(nombre, []).append(os.path.relpath(camino, RAIZ))
                            if nombre == "select" and llamada.args and isinstance(llamada.args[0], ast.Constant):
                                try:
                                    bd._columnas_sql(llamada.args[0].value)
                                except bd.ErrorBaseDatos:
                                    comprobar(f"select no soportado en {os.path.relpath(camino, RAIZ)}", llamada.args[0].value, "texto soportado")
                            for palabra in llamada.keywords:
                                if palabra.arg in ("count", "head", "returning", "ignore_duplicates", "default_to_null") and nombre != "select":
                                    comprobar(f"argumento {palabra.arg} en {nombre} ({os.path.relpath(camino, RAIZ)})", palabra.arg, "no usado")
    print(f"  cadenas table/rpc encontradas en el código: {cadenas}")
    print("  métodos usados:", ", ".join(f"{n}({len(v)})" for n, v in sorted(usados.items())))
    for nombre, lugares in sorted(usados.items()):
        if nombre not in disponibles and nombre != "execute":
            comprobar(f"método '{nombre}' falta en el adaptador (usado en {sorted(set(lugares))[:3]})", nombre, "implementado")
    return cadenas


# TITULO EJECUTOR CON PSYCOPG2 FALSO

def probar_ejecutor() -> int:
    """Parte 3: recorre el ejecutor real con un `psycopg2` simulado (sin base de datos) y revisa conexiones, reintentos y valores."""
    import types

    class ErrorOperacional(Exception):
        """Simula psycopg2.OperationalError."""

    class ErrorInterfaz(Exception):
        """Simula psycopg2.InterfaceError."""

    class JsonFalso:
        """Simula psycopg2.extras.Json."""

        def __init__(self, contenido):
            """Guarda el contenido recibido."""
            self.contenido = contenido

    class CursorFalso:
        """Simula un cursor: anota lo ejecutado y devuelve filas preparadas."""

        def __init__(self, conexion):
            """Se asocia a la conexión que lo creó."""
            self.conexion = conexion
            self.description = None
            self._filas: list = []

        def __enter__(self):
            """Permite usarlo con `with`."""
            return self

        def __exit__(self, *argumentos):
            """Cierra el `with` sin suprimir errores."""
            return False

        def execute(self, sentencia, valores):
            """Anota la ejecución o lanza el error programado para esa conexión."""
            if self.conexion.error:
                raise self.conexion.error
            ambiente.ejecutadas.append((sentencia, valores))
            self.description = ["columna"]
            self._filas = [{"saldo": Decimal("12.50"), "creada": datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc), "datos": {"a": 1}}]

        def fetchall(self):
            """Devuelve las filas preparadas."""
            return self._filas

    class ConexionFalsa:
        """Simula una conexión del grupo; puede tener un error programado."""

        def __init__(self, error=None):
            """Crea la conexión abierta, con el error que lanzará al ejecutar (si se indicó)."""
            self.closed = 0
            self.autocommit = False
            self.error = error

        def cursor(self, cursor_factory=None):
            """Devuelve un cursor falso."""
            return CursorFalso(self)

    class GrupoFalso:
        """Simula ThreadedConnectionPool: entrega las conexiones programadas y anota cómo se devuelven."""

        def __init__(self, minimo, maximo, **parametros):
            """Anota con qué parámetros se creó el grupo."""
            ambiente.parametros_grupo = parametros
            self.maximo = maximo

        def getconn(self):
            """Entrega la siguiente conexión programada (o una sana si ya no quedan)."""
            return ambiente.conexiones.pop(0) if ambiente.conexiones else ConexionFalsa()

        def putconn(self, conexion, close=False):
            """Anota si la conexión se devolvió para reutilizar o se descartó."""
            ambiente.devueltas.append(close)

    ambiente = types.SimpleNamespace(ejecutadas=[], devueltas=[], conexiones=[], parametros_grupo={})
    modulos = {"psycopg2": types.ModuleType("psycopg2"), "psycopg2.extras": types.ModuleType("psycopg2.extras"),
               "psycopg2.pool": types.ModuleType("psycopg2.pool")}
    modulos["psycopg2"].OperationalError = ErrorOperacional
    modulos["psycopg2"].InterfaceError = ErrorInterfaz
    modulos["psycopg2.extras"].RealDictCursor = object
    modulos["psycopg2.extras"].Json = JsonFalso
    modulos["psycopg2.pool"].ThreadedConnectionPool = GrupoFalso
    anteriores = {nombre: sys.modules.get(nombre) for nombre in modulos}
    sys.modules.update(modulos)
    try:
        cliente = bd.ClientePostgres({"host": "localhost", "dbname": "base", "user": "u", "password": "p"})

        # lectura normal: valores como Supabase y conexión devuelta para reutilizar
        filas = cliente.table("usuarios").select("saldo").in_("id", [1, 2]).execute().data
        comprobar("ejecutor convierte decimal", filas[0]["saldo"], 12.5)
        comprobar("ejecutor convierte fecha", filas[0]["creada"], "2026-10-28T12:00:00+00:00")
        comprobar("ejecutor entrega jsonb como diccionario", filas[0]["datos"], {"a": 1})
        comprobar("lista del filtro in_ NO se envuelve como JSON", ambiente.ejecutadas[-1][1], [[1, 2]])
        comprobar("conexión devuelta sin descartar", ambiente.devueltas[-1], False)
        comprobar("grupo con zona UTC y tiempo máximo", "timezone=UTC" in ambiente.parametros_grupo["options"] and "statement_timeout" in ambiente.parametros_grupo["options"], True)
        comprobar("grupo recibe los datos de conexión", ambiente.parametros_grupo["host"], "localhost")

        # el diccionario de un insert sí va como JSON
        cliente.table("agente_mensajes").insert({"chat_id": 1, "mensaje": {"role": "user"}}).execute()
        parametros = ambiente.ejecutadas[-1][1]
        comprobar("diccionario del insert se envía como JSON", isinstance(parametros[1], JsonFalso) and parametros[1].contenido == {"role": "user"}, True)

        # lectura con conexión cortada: se reintenta una vez y funciona
        ambiente.ejecutadas.clear()
        ambiente.devueltas.clear()
        ambiente.conexiones[:] = [ConexionFalsa(error=ErrorOperacional("se cortó"))]
        cliente.table("usuarios").select("id").execute()
        comprobar("lectura se reintenta tras cortarse", (len(ambiente.ejecutadas), ambiente.devueltas), (1, [True, False]))

        # escritura con conexión cortada: NO se reintenta y se descarta la conexión
        ambiente.ejecutadas.clear()
        ambiente.devueltas.clear()
        ambiente.conexiones[:] = [ConexionFalsa(error=ErrorOperacional("se cortó"))]
        try:
            cliente.table("usuarios").insert({"nombre": "x"}).execute()
            comprobar("escritura cortada debe fallar", "no fallo", "ErrorOperacional")
        except ErrorOperacional:
            pass
        comprobar("escritura no se reintenta", (len(ambiente.ejecutadas), ambiente.devueltas), (0, [True]))

        # rpc no se reintenta
        ambiente.devueltas.clear()
        ambiente.conexiones[:] = [ConexionFalsa(error=ErrorOperacional("se cortó"))]
        try:
            cliente.rpc("billetera_mover", {"p_usuario": 1}).execute()
            comprobar("rpc cortado debe fallar", "no fallo", "ErrorOperacional")
        except ErrorOperacional:
            pass
        comprobar("rpc no se reintenta", ambiente.devueltas, [True])

        # un error de la base (por ejemplo, restricción única) conserva su texto y la conexión se reutiliza
        ambiente.devueltas.clear()
        ambiente.conexiones[:] = [ConexionFalsa(error=Exception("duplicate key value violates unique constraint"))]
        try:
            cliente.table("usuarios").insert({"email": "a"}).execute()
        except Exception as error:  # noqa: BLE001 - se revisa el texto, no el tipo
            comprobar("el texto del error se conserva", "duplicate" in str(error).lower(), True)
        comprobar("tras un error de datos la conexión se reutiliza", ambiente.devueltas, [False])
    finally:
        for nombre, anterior in anteriores.items():
            if anterior is None:
                sys.modules.pop(nombre, None)
            else:
                sys.modules[nombre] = anterior
    return 14


# TITULO PRINCIPAL

def principal() -> int:
    """Ejecuta las tres partes y devuelve 0 si todo pasó o 1 si hubo fallos."""
    print("Parte 1: casos de SQL")
    cantidad = probar_casos()
    print(f"  {cantidad} comprobaciones")
    print("Parte 2: cobertura del código real")
    probar_cobertura()
    print("Parte 3: ejecutor con psycopg2 simulado")
    print(f"  {probar_ejecutor()} comprobaciones")
    if fallos:
        print(f"\nFALLARON {len(fallos)} comprobaciones")
        return 1
    print("\nTODO OK")
    return 0


if __name__ == "__main__":
    sys.exit(principal())


# -------------------------------------------------------------------------------------------------------
# ---------------------------- FIN Piña y Jara _prueba_base_datos_postgres .PY --------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
