# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara test_despliegue .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
test_despliegue.py
------------------
Pruebas de los archivos de despliegue: Dockerfile, docker-compose, `.env.example`, `requirements.txt` instalable, arranque del
contenedor y comprobación de salud. No necesitan Docker: revisan los archivos y la lógica de los scripts de arranque.
"""
import re
import socket

import pytest

from despliegue import arranque_docker, salud

# Variables de uso interno o de diagnóstico que no se documentan para el usuario.
INTERNAS = {"PJ_DIAGNOSTICO", "MT5_BRIDGE_MODULO", "CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"}


def _leer(raiz, nombre):
    return (raiz / nombre).read_text(encoding="utf-8")


def test_existen_los_archivos_de_despliegue(raiz):
    for nombre in ("Dockerfile", "docker-compose.yml", ".dockerignore", ".env.example", "requirements.txt", "despliegue/arranque_docker.py", "despliegue/salud.py"):
        assert (raiz / nombre).is_file(), nombre


def test_el_dockerfile_usa_python_312_expone_los_puertos_y_no_corre_como_administrador(raiz):
    texto = _leer(raiz, "Dockerfile")
    assert re.search(r"(?m)^FROM python:3\.12", texto)
    assert "EXPOSE 8501 8000" in texto and "HEALTHCHECK" in texto
    assert re.search(r"(?m)^USER \w+", texto)


def test_el_compose_publica_los_dos_puertos_y_guarda_los_datos_en_un_volumen(raiz):
    yaml = pytest.importorskip("yaml")
    servicio = yaml.safe_load(_leer(raiz, "docker-compose.yml"))["services"]["plataforma"]
    assert "8501:8501" in servicio["ports"] and "8000:8000" in servicio["ports"]
    assert servicio["env_file"] == ".env" and servicio["restart"] == "unless-stopped"
    assert any(v.endswith(":/app/data") or ":/app/data" in v for v in servicio["volumes"])


def test_la_imagen_no_incluye_secretos(raiz):
    ignorados = {l.strip() for l in _leer(raiz, ".dockerignore").splitlines()}
    assert ".env" in ignorados and "env/" in ignorados


def test_requirements_es_instalable_linea_por_linea(raiz):
    packaging = pytest.importorskip("packaging.requirements")
    lineas = [l.strip() for l in _leer(raiz, "requirements.txt").splitlines() if l.strip() and not l.strip().startswith("#")]
    assert len(lineas) >= 15
    for linea in lineas:
        assert not linea.lower().startswith("pip "), linea                 # el error de la lista anterior
        packaging.Requirement(linea)


def test_requirements_incluye_las_librerias_que_importa_el_codigo(raiz):
    texto = _leer(raiz, "requirements.txt").lower()
    for paquete in ("streamlit", "pandas", "numpy", "requests", "websockets", "yfinance", "python-dotenv", "openai", "supabase", "psycopg2-binary", "cryptography", "matplotlib", "trafilatura"):
        assert paquete in texto, paquete


def test_env_example_documenta_todas_las_variables_que_lee_el_codigo(raiz):
    usadas = set()
    patron = re.compile(r"(?:environ\.get|getenv|environ\[)\(?\s*[\"']([A-Z][A-Z0-9_]{3,})[\"']")
    for ruta in raiz.rglob("*.py"):
        if {"tests", "env", "venv", ".venv", "__pycache__"} & set(ruta.relative_to(raiz).parts):
            continue
        usadas |= set(patron.findall(ruta.read_text(encoding="utf-8", errors="ignore")))
    documentadas = set(re.findall(r"(?m)^#?\s*([A-Z][A-Z0-9_]{3,})=", _leer(raiz, ".env.example")))
    faltan = sorted(usadas - documentadas - INTERNAS)
    assert faltan == [], f"variables sin documentar en .env.example: {faltan}"


def test_env_example_no_trae_claves_reales(raiz):
    texto = _leer(raiz, ".env.example")
    assert not re.search(r"\bsk-[A-Za-z0-9]{20,}", texto)
    assert "reemplazar" in texto


def test_el_arranque_levanta_el_servidor_de_precios_y_el_dashboard():
    cmds = dict(arranque_docker.comandos())
    assert set(cmds) == {"servidor de precios", "dashboard"}
    assert "servidor_datos.py" in cmds["servidor de precios"][-1]
    assert "--server.address" in cmds["dashboard"] and "0.0.0.0" in cmds["dashboard"]


def test_la_comprobacion_de_salud_falla_si_nadie_escucha():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        libre = s.getsockname()[1]
    assert salud.responde(f"http://127.0.0.1:{libre}/salud") is False


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara test_despliegue .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
