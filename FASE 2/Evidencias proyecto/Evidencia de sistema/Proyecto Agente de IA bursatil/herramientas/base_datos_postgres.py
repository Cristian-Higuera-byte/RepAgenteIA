# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara base_datos_postgres .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""
base_datos_postgres.py
----------------------
Cliente de PostgreSQL con la misma interfaz de consultas que el resto del proyecto usa con Supabase.

Por qué existe: la plataforma habla con la base de datos mediante `cliente.table("tabla").select(...).eq(...).execute()`, una interfaz
del cliente de Supabase que depende de un servicio web (PostgREST) que un PostgreSQL común no trae. Este módulo ofrece esa misma
interfaz pero se conecta directamente a PostgreSQL, de modo que el resto del código no necesita cambiar sus consultas.

Qué soporta (lo único que el proyecto usa):
  - Operaciones: select (con count="exact"), insert, upsert (con on_conflict), update, delete y rpc (funciones de la base de datos).
  - Filtros: eq, neq, gt, gte, lt, lte, is_, in_. Modificadores: order, limit, range. Cierre: execute().
  - La respuesta tiene `.data` (lista de diccionarios) y `.count`, igual que la de Supabase. Los nombres `data`, `count`, `on_conflict`,
    `desc` y `is_` se conservan en inglés a propósito, porque son los que el resto del código ya escribe.

Cómo se parece a Supabase en lo que el código espera:
  - insert, upsert, update y delete devuelven las filas afectadas (RETURNING *), como el cliente de Supabase.
  - Las fechas se entregan como texto ISO, los números decimales como números y los campos JSONB como diccionarios o listas.
  - Los errores conservan el mensaje original de PostgreSQL (por ejemplo «duplicate key value violates unique constraint» o el texto
    de RAISE EXCEPTION «saldo_insuficiente»), porque el código busca esas palabras para decidir qué avisar.
  - update y delete exigen al menos un filtro, como la protección contra borrados totales que trae Supabase.

Variables del .env: POSTGRES_SERVIDOR, POSTGRES_PUERTO, POSTGRES_BASE_DATOS, POSTGRES_USUARIO y POSTGRES_CONTRASENA.
El controlador `psycopg2` se importa solo al conectar, de modo que este módulo se puede cargar y probar sin tener una base de datos.
"""
import os
import re
import threading
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

# Un nombre de tabla, columna o función válido: letras, números y guion bajo, sin empezar por número. Evita inyectar SQL en los nombres.
_IDENTIFICADOR = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Conexiones simultáneas máximas hacia la base de datos (el hosting comparte la memoria con el resto de la plataforma).
MAXIMO_CONEXIONES = 5

# Tiempo máximo, en milisegundos, que puede tardar una sentencia antes de que PostgreSQL la cancele.
TIEMPO_MAXIMO_SENTENCIA_MS = 30000


# TITULO ERROR

class ErrorBaseDatos(Exception):
    """Error propio del adaptador: una consulta mal armada o una configuración incompleta (no un error de PostgreSQL)."""


# TITULO RESPUESTA

class RespuestaConsulta:
    """Resultado de una consulta con la misma forma que el de Supabase: `data` (lista de diccionarios) y `count` (total o None)."""

    def __init__(self, datos: list, cantidad: Optional[int] = None):
        """Guarda las filas devueltas y, si se pidió contar, el total de filas que cumplían el filtro."""
        self.data = datos
        self.count = cantidad


# TITULO NOMBRES

def _identificador(nombre: str) -> str:
    """Valida un nombre de tabla, columna o función y lo devuelve entre comillas dobles; lanza ErrorBaseDatos si no es un nombre válido."""
    if not isinstance(nombre, str) or not _IDENTIFICADOR.match(nombre):
        raise ErrorBaseDatos(f"Nombre no válido para la base de datos: {nombre!r}")
    return f'"{nombre}"'


# TITULO COLUMNAS

def _columnas_sql(columnas: str) -> str:
    """Convierte el texto de columnas de un select («*» o «a, b, c») en SQL; lanza ErrorBaseDatos si usa una sintaxis no soportada."""
    texto = (columnas or "*").strip()
    if texto == "*":
        return "*"
    return ", ".join(_identificador(parte.strip()) for parte in texto.split(","))


# TITULO CONVERTIR VALOR

def _convertir_valor(valor: Any) -> Any:
    """Convierte un valor leído de PostgreSQL a la forma que entrega Supabase: fechas en texto ISO y decimales como número."""
    if isinstance(valor, Decimal):
        return int(valor) if valor.as_tuple().exponent >= 0 else float(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


# TITULO VALOR JSON

class ValorJson:
    """Marca un valor (diccionario o lista) que se guarda en una columna JSON.

    Solo los datos de insert, upsert y update se marcan así. Las listas de los filtros (`in_`) NO se marcan, porque PostgreSQL debe
    recibirlas como arreglo y no como JSON.
    """

    def __init__(self, contenido: Any):
        """Guarda el diccionario o la lista que se enviará como JSON."""
        self.contenido = contenido

    def __eq__(self, otro: Any) -> bool:
        """Compara por contenido, con otro ValorJson o con el diccionario o lista original (útil en las pruebas)."""
        return self.contenido == (otro.contenido if isinstance(otro, ValorJson) else otro)

    __hash__ = None


# TITULO MARCAR JSON

def _marcar_json(valor: Any) -> Any:
    """Marca como JSON los diccionarios y las listas que se van a guardar; deja el resto de los valores igual."""
    return ValorJson(valor) if isinstance(valor, (dict, list)) else valor


# TITULO PREPARAR PARAMETRO

def _preparar_parametro(valor: Any) -> Any:
    """Convierte un valor marcado como ValorJson al tipo JSON de psycopg2; deja el resto (incluidas las listas de filtros) igual."""
    if isinstance(valor, ValorJson):
        from psycopg2.extras import Json
        return Json(valor.contenido)
    return valor


# TITULO CLIENTE

class ClientePostgres:
    """Cliente con la interfaz de Supabase (`table`, `rpc`) sobre un grupo de conexiones directas a PostgreSQL."""

    def __init__(self, parametros_conexion: dict, maximo_conexiones: int = MAXIMO_CONEXIONES):
        """Guarda los datos de conexión; el grupo de conexiones se abre recién en la primera consulta."""
        self._parametros_conexion = dict(parametros_conexion)
        self._maximo_conexiones = maximo_conexiones
        self._grupo = None
        self._candado = threading.Lock()
        self._claves_primarias: dict[str, list[str]] = {}

    # TITULO GRUPO

    def _obtener_grupo(self):
        """Abre (una sola vez) el grupo de conexiones y lo devuelve; las conexiones usan hora UTC y un tiempo máximo por sentencia."""
        with self._candado:
            if self._grupo is None:
                from psycopg2.pool import ThreadedConnectionPool
                self._grupo = ThreadedConnectionPool(
                    1, self._maximo_conexiones,
                    options=f"-c timezone=UTC -c statement_timeout={TIEMPO_MAXIMO_SENTENCIA_MS}",
                    **self._parametros_conexion)
            return self._grupo

    # TITULO EJECUTAR

    def ejecutar_sentencia(self, sentencia: str, parametros: Optional[list] = None, reintentable: bool = False) -> list:
        """Ejecuta una sentencia SQL y devuelve sus filas como lista de diccionarios (vacía si no devuelve filas).

        Si la conexión estaba cerrada se toma otra; si se corta durante una lectura (`reintentable`) se reintenta una vez. Las escrituras
        no se reintentan, para no repetir un insert o un movimiento de dinero que sí alcanzó a ejecutarse.
        """
        from psycopg2 import InterfaceError, OperationalError
        from psycopg2.extras import RealDictCursor

        grupo = self._obtener_grupo()
        valores = [_preparar_parametro(valor) for valor in (parametros or [])]
        for intento in (1, 2):
            conexion = grupo.getconn()
            descartar = bool(conexion.closed)
            try:
                if descartar:
                    raise OperationalError("la conexión estaba cerrada")
                conexion.autocommit = True
                with conexion.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sentencia, valores or None)
                    filas = cursor.fetchall() if cursor.description else []
                return [{columna: _convertir_valor(valor) for columna, valor in fila.items()} for fila in filas]
            except (OperationalError, InterfaceError):
                descartar = True
                if intento == 2 or not (reintentable or conexion.closed):
                    raise
            finally:
                grupo.putconn(conexion, close=descartar)
        return []

    # TITULO CLAVE PRIMARIA

    def clave_primaria(self, tabla: str) -> list:
        """Devuelve las columnas de la clave primaria de la tabla (se consulta una sola vez y se recuerda)."""
        if tabla not in self._claves_primarias:
            _identificador(tabla)
            filas = self.ejecutar_sentencia(
                "SELECT a.attname AS columna FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid "
                "AND a.attnum = ANY(i.indkey) WHERE i.indrelid = %s::regclass AND i.indisprimary ORDER BY a.attnum",
                [tabla], reintentable=True)
            self._claves_primarias[tabla] = [fila["columna"] for fila in filas]
        return self._claves_primarias[tabla]

    # TITULO TABLA

    def table(self, nombre: str) -> "ConstructorConsulta":
        """Empieza una consulta sobre la tabla indicada (igual que `cliente.table(...)` de Supabase)."""
        return ConstructorConsulta(self, nombre)

    # TITULO RPC

    def rpc(self, nombre: str, parametros: Optional[dict] = None) -> "ConstructorFuncion":
        """Prepara la llamada a una función de la base de datos con parámetros con nombre (igual que `cliente.rpc(...)`)."""
        return ConstructorFuncion(self, nombre, parametros or {})


# TITULO CONSTRUCTOR DE CONSULTAS

class ConstructorConsulta:
    """Arma una consulta paso a paso (select, insert, upsert, update o delete, con sus filtros) y la ejecuta con `execute()`."""

    def __init__(self, cliente: ClientePostgres, tabla: str):
        """Empieza una consulta vacía sobre la tabla; la operación se define con select, insert, upsert, update o delete."""
        self._cliente = cliente
        self._nombre_tabla = tabla
        self._tabla = _identificador(tabla)
        self._operacion: Optional[str] = None
        self._columnas = "*"
        self._contar = False
        self._datos: Any = None
        self._conflicto: Optional[str] = None
        self._condiciones: list = []
        self._orden: list = []
        self._limite: Optional[int] = None
        self._desplazamiento: Optional[int] = None

    # TITULO OPERACIONES

    def select(self, columnas: str = "*", count: Optional[str] = None, **_ignorados) -> "ConstructorConsulta":
        """Lee filas; con count="exact" la respuesta trae también el total de filas que cumplen el filtro (sin contar el límite)."""
        self._operacion = "select"
        self._columnas = _columnas_sql(columnas)
        self._contar = count is not None
        return self

    def insert(self, datos: Any, **_ignorados) -> "ConstructorConsulta":
        """Inserta una fila (diccionario) o varias (lista de diccionarios) y devuelve las filas creadas."""
        self._operacion = "insert"
        self._datos = datos
        return self

    def upsert(self, datos: Any, on_conflict: Optional[str] = None, **_ignorados) -> "ConstructorConsulta":
        """Inserta o actualiza si la fila ya existe; `on_conflict` son las columnas únicas separadas por coma (por defecto, la clave primaria)."""
        self._operacion = "upsert"
        self._datos = datos
        self._conflicto = on_conflict
        return self

    def update(self, cambios: dict, **_ignorados) -> "ConstructorConsulta":
        """Cambia las columnas indicadas en las filas que cumplan los filtros y devuelve las filas modificadas."""
        self._operacion = "update"
        self._datos = cambios
        return self

    def delete(self, **_ignorados) -> "ConstructorConsulta":
        """Borra las filas que cumplan los filtros y devuelve las filas borradas."""
        self._operacion = "delete"
        return self

    # TITULO FILTROS

    def _agregar_condicion(self, texto: str, parametros: Optional[list] = None) -> "ConstructorConsulta":
        """Agrega una condición SQL (con sus parámetros) al filtro de la consulta; todas se combinan con AND."""
        self._condiciones.append((texto, parametros or []))
        return self

    def eq(self, columna: str, valor: Any) -> "ConstructorConsulta":
        """Filtra las filas donde la columna es igual al valor (si el valor es None, donde es nula)."""
        nombre = _identificador(columna)
        if valor is None:
            return self._agregar_condicion(f"{nombre} IS NULL")
        return self._agregar_condicion(f"{nombre} = %s", [valor])

    def neq(self, columna: str, valor: Any) -> "ConstructorConsulta":
        """Filtra las filas donde la columna es distinta del valor (si el valor es None, donde no es nula)."""
        nombre = _identificador(columna)
        if valor is None:
            return self._agregar_condicion(f"{nombre} IS NOT NULL")
        return self._agregar_condicion(f"{nombre} <> %s", [valor])

    def gt(self, columna: str, valor: Any) -> "ConstructorConsulta":
        """Filtra las filas donde la columna es mayor que el valor."""
        return self._agregar_condicion(f"{_identificador(columna)} > %s", [valor])

    def gte(self, columna: str, valor: Any) -> "ConstructorConsulta":
        """Filtra las filas donde la columna es mayor o igual que el valor."""
        return self._agregar_condicion(f"{_identificador(columna)} >= %s", [valor])

    def lt(self, columna: str, valor: Any) -> "ConstructorConsulta":
        """Filtra las filas donde la columna es menor que el valor."""
        return self._agregar_condicion(f"{_identificador(columna)} < %s", [valor])

    def lte(self, columna: str, valor: Any) -> "ConstructorConsulta":
        """Filtra las filas donde la columna es menor o igual que el valor."""
        return self._agregar_condicion(f"{_identificador(columna)} <= %s", [valor])

    def is_(self, columna: str, valor: Any) -> "ConstructorConsulta":
        """Filtra las filas donde la columna es nula, verdadera o falsa (el valor acepta None, True, False o los textos "null", "true", "false")."""
        nombre = _identificador(columna)
        texto = str(valor).lower() if valor is not None else "null"
        if texto not in ("null", "true", "false"):
            raise ErrorBaseDatos(f"is_ solo acepta null, true o false, no {valor!r}")
        return self._agregar_condicion(f"{nombre} IS {texto.upper()}")

    def in_(self, columna: str, valores: Any) -> "ConstructorConsulta":
        """Filtra las filas donde la columna es igual a alguno de los valores de la lista (lista vacía: no coincide ninguna)."""
        nombre = _identificador(columna)
        lista = list(valores)
        if not lista:
            return self._agregar_condicion("FALSE")
        return self._agregar_condicion(f"{nombre} = ANY(%s)", [lista])

    # TITULO MODIFICADORES

    def order(self, columna: str, desc: bool = False, **_ignorados) -> "ConstructorConsulta":
        """Ordena el resultado por la columna, de forma ascendente o, con desc=True, descendente."""
        self._orden.append(f"{_identificador(columna)} {'DESC' if desc else 'ASC'}")
        return self

    def limit(self, cantidad: int) -> "ConstructorConsulta":
        """Limita el resultado a esa cantidad de filas."""
        self._limite = int(cantidad)
        return self

    def range(self, desde: int, hasta: int) -> "ConstructorConsulta":
        """Devuelve las filas desde la posición `desde` hasta la `hasta`, ambas incluidas (la primera fila es la 0)."""
        self._desplazamiento = int(desde)
        self._limite = int(hasta) - int(desde) + 1
        return self

    # TITULO ARMAR SQL

    def _donde(self) -> tuple:
        """Devuelve la cláusula WHERE y sus parámetros a partir de los filtros acumulados (texto vacío si no hay filtros)."""
        if not self._condiciones:
            return "", []
        texto = " WHERE " + " AND ".join(condicion for condicion, _ in self._condiciones)
        return texto, [valor for _, parametros in self._condiciones for valor in parametros]

    def _filas_a_insertar(self) -> tuple:
        """Devuelve (columnas, filas) normalizadas para insert y upsert: todas las filas con las mismas columnas, en el mismo orden."""
        filas = self._datos if isinstance(self._datos, list) else [self._datos]
        if not filas or not all(isinstance(fila, dict) for fila in filas):
            raise ErrorBaseDatos("insert y upsert esperan un diccionario o una lista de diccionarios")
        columnas: list = []
        for fila in filas:
            for columna in fila:
                if columna not in columnas:
                    columnas.append(columna)
        return columnas, filas

    def _sql_insertar(self) -> tuple:
        """Arma el INSERT (o el INSERT con ON CONFLICT si es upsert) y devuelve la sentencia SQL con sus parámetros."""
        columnas, filas = self._filas_a_insertar()
        if not columnas:
            return f"INSERT INTO {self._tabla} DEFAULT VALUES RETURNING *", []
        nombres = [_identificador(columna) for columna in columnas]
        parametros: list = []
        grupos = []
        for fila in filas:
            marcas = []
            for columna in columnas:
                if columna in fila:
                    marcas.append("%s")
                    parametros.append(_marcar_json(fila[columna]))
                else:
                    marcas.append("DEFAULT")
            grupos.append("(" + ", ".join(marcas) + ")")
        sentencia = f"INSERT INTO {self._tabla} ({', '.join(nombres)}) VALUES {', '.join(grupos)}"
        if self._operacion == "upsert":
            conflicto = [parte.strip() for parte in self._conflicto.split(",")] if self._conflicto else self._cliente.clave_primaria(self._nombre_tabla)
            if not conflicto:
                raise ErrorBaseDatos(f"upsert sobre {self._nombre_tabla} necesita on_conflict: la tabla no tiene clave primaria")
            destino = ", ".join(_identificador(columna) for columna in conflicto)
            cambiables = [columna for columna in columnas if columna not in conflicto]
            if cambiables:
                asignaciones = ", ".join(f"{_identificador(columna)} = EXCLUDED.{_identificador(columna)}" for columna in cambiables)
                sentencia += f" ON CONFLICT ({destino}) DO UPDATE SET {asignaciones}"
            else:
                sentencia += f" ON CONFLICT ({destino}) DO NOTHING"
        return sentencia + " RETURNING *", parametros

    def _sql_actualizar(self) -> tuple:
        """Arma el UPDATE con los cambios y los filtros; exige al menos un filtro para no modificar toda la tabla por error."""
        if not isinstance(self._datos, dict) or not self._datos:
            raise ErrorBaseDatos("update espera un diccionario con al menos un cambio")
        if not self._condiciones:
            raise ErrorBaseDatos("update necesita al menos un filtro")
        asignaciones = ", ".join(f"{_identificador(columna)} = %s" for columna in self._datos)
        donde, parametros = self._donde()
        return f"UPDATE {self._tabla} SET {asignaciones}{donde} RETURNING *", [_marcar_json(valor) for valor in self._datos.values()] + parametros

    def _sql_borrar(self) -> tuple:
        """Arma el DELETE con los filtros; exige al menos un filtro para no borrar toda la tabla por error."""
        if not self._condiciones:
            raise ErrorBaseDatos("delete necesita al menos un filtro")
        donde, parametros = self._donde()
        return f"DELETE FROM {self._tabla}{donde} RETURNING *", parametros

    def _sql_leer(self) -> tuple:
        """Arma el SELECT con sus filtros, orden, límite y desplazamiento."""
        donde, parametros = self._donde()
        sentencia = f"SELECT {self._columnas} FROM {self._tabla}{donde}"
        if self._orden:
            sentencia += " ORDER BY " + ", ".join(self._orden)
        if self._limite is not None:
            sentencia += f" LIMIT {self._limite}"
        if self._desplazamiento:
            sentencia += f" OFFSET {self._desplazamiento}"
        return sentencia, parametros

    def armar_sql(self) -> tuple:
        """Devuelve (sentencia, parámetros) de la operación elegida, sin ejecutarla (sirve para revisar y probar la consulta)."""
        if self._operacion in (None, "select"):
            return self._sql_leer()
        if self._operacion in ("insert", "upsert"):
            return self._sql_insertar()
        if self._operacion == "update":
            return self._sql_actualizar()
        return self._sql_borrar()

    # TITULO EJECUTAR

    def execute(self) -> RespuestaConsulta:
        """Ejecuta la consulta y devuelve una RespuestaConsulta con `data` y, si se pidió contar, `count`."""
        sentencia, parametros = self.armar_sql()
        es_lectura = self._operacion in (None, "select")
        filas = self._cliente.ejecutar_sentencia(sentencia, parametros, reintentable=es_lectura)
        total = None
        if es_lectura and self._contar:
            donde, parametros_conteo = self._donde()
            conteo = self._cliente.ejecutar_sentencia(f"SELECT COUNT(*) AS cantidad FROM {self._tabla}{donde}", parametros_conteo, reintentable=True)
            total = int(conteo[0]["cantidad"])
        return RespuestaConsulta(filas, total)


# TITULO CONSTRUCTOR DE FUNCIONES

class ConstructorFuncion:
    """Prepara la llamada a una función de la base de datos (por ejemplo billetera_mover) y la ejecuta con `execute()`."""

    def __init__(self, cliente: ClientePostgres, nombre: str, parametros: dict):
        """Guarda la función y sus parámetros con nombre; los nombres se validan para no inyectar SQL."""
        self._cliente = cliente
        self._funcion = _identificador(nombre)
        self._parametros = parametros

    # TITULO EJECUTAR

    def armar_sql(self) -> tuple:
        """Devuelve (sentencia, parámetros) de la llamada, con la forma SELECT * FROM funcion(nombre := valor, ...)."""
        nombres = [f"{_identificador(nombre)} := %s" for nombre in self._parametros]
        return f"SELECT * FROM {self._funcion}({', '.join(nombres)})", list(self._parametros.values())

    def execute(self) -> RespuestaConsulta:
        """Ejecuta la función y devuelve sus filas en `data`; no se reintenta, porque puede mover dinero o modificar datos."""
        sentencia, parametros = self.armar_sql()
        return RespuestaConsulta(self._cliente.ejecutar_sentencia(sentencia, parametros, reintentable=False))


# TITULO CREAR CLIENTE

def crear_cliente_desde_entorno() -> ClientePostgres:
    """Crea el cliente leyendo POSTGRES_SERVIDOR, POSTGRES_PUERTO, POSTGRES_BASE_DATOS, POSTGRES_USUARIO y POSTGRES_CONTRASENA del entorno.

    Lanza ErrorBaseDatos si falta alguna de las cinco. No abre ninguna conexión: eso ocurre recién en la primera consulta.
    """
    variables = {"host": "POSTGRES_SERVIDOR", "port": "POSTGRES_PUERTO", "dbname": "POSTGRES_BASE_DATOS",
                 "user": "POSTGRES_USUARIO", "password": "POSTGRES_CONTRASENA"}
    valores = {clave: os.environ.get(nombre, "") for clave, nombre in variables.items()}
    faltantes = [variables[clave] for clave, valor in valores.items() if not valor]
    if faltantes:
        raise ErrorBaseDatos("Faltan variables en el .env: " + ", ".join(faltantes))
    return ClientePostgres(valores)


# -------------------------------------------------------------------------------------------------------
# ------------------------------ FIN Piña y Jara base_datos_postgres .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
