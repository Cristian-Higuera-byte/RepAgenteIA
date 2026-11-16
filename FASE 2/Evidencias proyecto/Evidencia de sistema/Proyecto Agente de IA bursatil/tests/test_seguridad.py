# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara test_seguridad .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_seguridad.py
-----------------
Pruebas de seguridad y de calidad del repositorio: ningún secreto versionado, `.env` ignorado por git, esquemas SQL con
seguridad a nivel de fila, parámetros del acceso de usuarios (sesiones, enlaces, contraseñas) y estándar de código.
"""
import re

import pytest

from herramientas import sesion_persistente, verificacion_correo as vc

EXTENSIONES = {".py", ".md", ".sql", ".json", ".toml", ".txt", ".html", ".css", ".js", ".ejemplo", ".yml", ".yaml"}
IGNORAR = {"__pycache__", "env", "venv", ".venv", ".git", "_resultados", "outputs", "data"}
PATRONES_SECRETOS = {
    "clave de modelo (sk-...)": re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    "clave de AWS": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "token JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\."),
    "llave privada": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "asignación de secreto": re.compile(r"(?i)(?:api[_-]?key|secret|password|contrasena|token)\s*[=:]\s*['\"][A-Za-z0-9_\-/+]{24,}['\"]"),
}


def _archivos(raiz):
    for ruta in raiz.rglob("*"):
        if ruta.is_file() and ruta.suffix in EXTENSIONES and not (set(ruta.relative_to(raiz).parts) & IGNORAR) and "tests" not in ruta.relative_to(raiz).parts[:1]:
            yield ruta


def test_no_hay_secretos_en_los_archivos_del_proyecto(raiz):
    hallazgos = []
    for ruta in _archivos(raiz):
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        for nombre, patron in PATRONES_SECRETOS.items():
            if patron.search(texto):
                hallazgos.append(f"{ruta.relative_to(raiz)}: {nombre}")
    assert hallazgos == []


def test_el_archivo_env_no_esta_en_la_carpeta_del_sistema(raiz):
    assert not (raiz / ".env").exists()


def test_gitignore_excluye_los_archivos_sensibles(raiz):
    texto = (raiz / ".gitignore").read_text(encoding="utf-8")
    lineas = {l.strip() for l in texto.splitlines()}
    for esperado in (".env", "env/", "__pycache__/"):
        assert esperado in lineas, f"falta {esperado} en .gitignore"


def test_los_esquemas_de_supabase_activan_la_seguridad_a_nivel_de_fila(raiz):
    carpeta = raiz / "herramientas" / "sql"
    texto = "\n".join(p.read_text(encoding="utf-8") for p in carpeta.glob("*.sql") if "cpanel" not in p.name)
    tablas = set(re.findall(r"(?i)create\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?(\w+)", texto))
    con_rls = set(re.findall(r"(?i)alter\s+table\s+(?:public\.)?(\w+)\s+enable\s+row\s+level\s+security", texto))
    assert tablas, "no se encontraron tablas"
    assert tablas - con_rls == set(), f"sin seguridad a nivel de fila: {sorted(tablas - con_rls)}"


def test_ningun_mensaje_al_usuario_nombra_al_proveedor_de_base_de_datos(raiz):
    ofensivos = []
    for ruta in (raiz / "herramientas").glob("*.py"):
        for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r'(?:return|raise|error|aviso)\b.*["\'][^"\']*Supabase no est', linea):
                ofensivos.append(f"{ruta.name}:{n}")
    assert ofensivos == []


def test_parametros_de_sesion_persistente():
    assert sesion_persistente.DIAS_DURACION == 30
    assert sesion_persistente.MAX_DISPOSITIVOS == 5


def test_parametros_de_los_enlaces_de_correo():
    assert vc.HORAS_VERIFICACION == 24 and vc.MINUTOS_RECUPERACION == 60
    assert vc.SEGUNDOS_ENTRE_ENVIOS == 60 and vc.MAXIMO_ENVIOS_POR_DIA == 5


def test_los_hash_guardados_nunca_son_el_token():
    token = "token-secreto-de-prueba"
    assert vc.hash_de(token) != token and token not in vc.hash_de(token)


def test_toda_orden_se_guarda_con_su_justificacion_y_origen(raiz):
    esquema = (raiz / "nucleo_agente" / "ordenes" / "sql" / "ordenes.sql").read_text(encoding="utf-8")
    for columna in ("justificacion", "origen", "estado", "detalle"):
        assert columna in esquema


def test_la_vigilancia_automatica_exige_cuenta_demo(raiz):
    codigo = (raiz / "nucleo_agente" / "vigilancia" / "gestion.py").read_text(encoding="utf-8")
    assert "cuenta_demo" in codigo


def test_el_unico_punto_que_envia_ordenes_es_el_tablero(raiz):
    emisores = []
    for ruta in (raiz / "nucleo_agente").rglob("*.py"):
        if "_enviar_apertura(" in ruta.read_text(encoding="utf-8") and ruta.name not in ("tablero.py", "envio.py"):
            emisores.append(ruta.name)
    assert emisores == []


# ---- Calidad del código (estándar de la empresa) --------------------------------------------------------

def test_los_archivos_python_siguen_el_estandar_de_encabezado_y_pie(raiz):
    sin_encabezado, total = [], 0
    for ruta in raiz.rglob("*.py"):
        partes = set(ruta.relative_to(raiz).parts)
        if partes & IGNORAR or ruta.stat().st_size < 200 or ruta.name == "__init__.py":
            continue
        total += 1
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        if "Creado, Programado y Diseñado por Piña y Jara" not in texto[:600] or texto.count("Creado, Programado y Diseñado por Piña y Jara") < 2:
            sin_encabezado.append(str(ruta.relative_to(raiz)))
    assert total > 100
    assert len(sin_encabezado) / total <= 0.05, f"{len(sin_encabezado)} de {total} sin encabezado y pie: {sin_encabezado[:5]}"


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara test_seguridad .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
