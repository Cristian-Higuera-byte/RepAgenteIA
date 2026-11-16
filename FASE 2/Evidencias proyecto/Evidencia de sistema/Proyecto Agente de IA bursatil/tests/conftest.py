# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara conftest .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
conftest.py
-----------
Configuración común de las pruebas: prepara la ruta del proyecto y el entorno, y ofrece un cliente de base de datos
en memoria que imita la parte de la interfaz de consultas que usa el proyecto, para probar sin una base real.

Ejecutar desde la carpeta del sistema:  python -m pytest tests -q
"""
import json
import os
import pathlib
import sys
import time

import pytest

RAIZ = pathlib.Path(os.environ.get("PROYECTO_RAIZ", pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(RAIZ))
os.environ["PROVEEDOR"] = "capital"                       # evita cargar MetaTrader5 (solo existe en Windows)
os.environ["SERVIDOR_SECRETO"] = "s" * 48                  # secreto de pruebas (no es el de producción)
from cryptography.fernet import Fernet  # noqa: E402
os.environ["CREDENCIALES_CLAVES"] = Fernet.generate_key().decode()
os.environ["PLATAFORMA_URL"] = "https://plataforma.prueba"

RESULTADOS = pathlib.Path(__file__).resolve().parent / "_resultados"


@pytest.fixture(scope="session")
def raiz():
    """Carpeta raíz del sistema."""
    return RAIZ


def registrar_medicion(nombre, segundos, operaciones):
    """Guarda en tests/_resultados/rendimiento.json cuánto tardó una operación repetida (evidencia de las pruebas de rendimiento)."""
    RESULTADOS.mkdir(exist_ok=True)
    ruta = RESULTADOS / "rendimiento.json"
    datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    datos[nombre] = {"operaciones": operaciones, "segundos": round(segundos, 4), "microsegundos_por_operacion": round(segundos / operaciones * 1e6, 1)}
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


class _Respuesta:
    def __init__(self, data):
        self.data = data
        self.count = len(data)


class _Consulta:
    """Subconjunto de la interfaz table().select/insert/update/delete().eq/gt/gte/is_/order().execute() sobre listas en memoria."""

    def __init__(self, filas):
        self._filas = filas
        self._op = "select"
        self._carga = None
        self._filtros = []
        self._orden = None

    def select(self, *_a, **_k):
        self._op = "select"
        return self

    def insert(self, datos, **_k):
        self._op, self._carga = "insert", datos
        return self

    def update(self, cambios, **_k):
        self._op, self._carga = "update", cambios
        return self

    def delete(self, **_k):
        self._op = "delete"
        return self

    def eq(self, col, valor):
        self._filtros.append(lambda f: f.get(col) == valor)
        return self

    def gt(self, col, valor):
        self._filtros.append(lambda f: f.get(col) is not None and f.get(col) > valor)
        return self

    def gte(self, col, valor):
        self._filtros.append(lambda f: f.get(col) is not None and f.get(col) >= valor)
        return self

    def is_(self, col, valor):
        esperado = None if valor in ("null", None) else valor
        self._filtros.append(lambda f: f.get(col) == esperado)
        return self

    def order(self, col, desc=False, **_k):
        self._orden = (col, desc)
        return self

    def limit(self, _n):
        return self

    def execute(self):
        coincide = [f for f in self._filas if all(c(f) for c in self._filtros)]
        if self._op == "insert":
            nueva = dict(self._carga)
            nueva.setdefault("id", len(self._filas) + 1)
            self._filas.append(nueva)
            return _Respuesta([dict(nueva)])
        if self._op == "update":
            for f in coincide:
                f.update(self._carga)
            return _Respuesta([dict(f) for f in coincide])
        if self._op == "delete":
            for f in coincide:
                self._filas.remove(f)
            return _Respuesta([dict(f) for f in coincide])
        if self._orden:
            coincide = sorted(coincide, key=lambda f: f.get(self._orden[0]) or "", reverse=self._orden[1])
        return _Respuesta([dict(f) for f in coincide])


class ClienteMemoria:
    """Cliente de base de datos en memoria con la misma interfaz que Supabase para las consultas del proyecto."""

    def __init__(self):
        self.tablas = {}

    def table(self, nombre):
        return _Consulta(self.tablas.setdefault(nombre, []))


@pytest.fixture
def cliente_memoria():
    return ClienteMemoria()


@pytest.fixture
def cronometro():
    """Devuelve una función que ejecuta una operación N veces y mide el tiempo total."""
    def medir(funcion, repeticiones):
        t0 = time.perf_counter()
        for i in range(repeticiones):
            funcion(i)
        return time.perf_counter() - t0
    return medir


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara conftest .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
