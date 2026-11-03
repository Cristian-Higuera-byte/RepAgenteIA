# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara carpeta_usuario .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
carpeta_usuario.py
------------------
Decide DÓNDE se guardan los archivos de datos de cada usuario y cuenta (equity, operaciones cerradas, diario,
pares OCO y stop dinámico).

- Modo de un solo usuario (`CAPITAL_MULTIUSUARIO` apagado): la carpeta de siempre, `data/`. Nada cambia.
- Modo multiusuario: `data/usuarios/<id>/<demo|real>/`. Cada cuenta tiene su propia carpeta porque los tickets, el
  equity y el historial de una cuenta demo no tienen nada que ver con los de la real ni con los de otro usuario.
- Sin usuario (sesión caída o hilo sin contexto): `data/usuarios/_sin_sesion/`, un cajón que nadie usa, para que
  un descuido nunca escriba en la carpeta de otro.

El usuario actual lo decide el mismo mecanismo del backend de Capital (`herramientas/backends/sesiones_capital.py`).
"""
import json
import os

from herramientas.backends import sesiones_capital

# Carpeta `data/` en la raíz del proyecto (un nivel arriba de este archivo)
_DATOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
# Carpeta que agrupa a todos los usuarios en modo multiusuario
_USUARIOS = os.path.join(_DATOS, "usuarios")


# TITULO CARPETA DE UNA CLAVE

def carpeta_de(clave: tuple) -> str:
    """Devuelve la carpeta de datos de la clave (usuario_id, es_demo), o la de los casos especiales (legado, anónimo)."""
    if clave == ("legado",):
        return _DATOS
    if len(clave) == 2:
        return os.path.join(_USUARIOS, str(int(clave[0])), "demo" if clave[1] else "real")
    return os.path.join(_USUARIOS, "_sin_sesion")


# TITULO CARPETA USUARIO

def carpeta_usuario() -> str:
    """Carpeta de datos del usuario y la cuenta actuales (ver el encabezado del archivo)."""
    return carpeta_de(sesiones_capital.clave_actual())


# TITULO RUTA ARCHIVO

def ruta_archivo(nombre: str) -> str:
    """Ruta completa del archivo `nombre` (por ejemplo "oco.json") en la carpeta del usuario y la cuenta actuales."""
    return os.path.join(carpeta_usuario(), nombre)


# TITULO CUENTAS CON ARCHIVO

def cuentas_con_contenido(nombre: str) -> list:
    """Lista las cuentas (usuario_id, es_demo) cuyo archivo JSON `nombre` existe y no está vacío.

    Lo usa el servidor para saber a quién tiene que vigilar aunque no haya abierto la página (stop dinámico y OCO
    deben seguir funcionando con el navegador cerrado). Solo mira la carpeta `data/usuarios`; en modo de un solo
    usuario no hay cuentas que listar."""
    cuentas = []
    if not os.path.isdir(_USUARIOS):
        return cuentas
    for usuario in os.listdir(_USUARIOS):
        if not usuario.isdigit():
            continue
        for modo, es_demo in (("demo", True), ("real", False)):
            ruta = os.path.join(_USUARIOS, usuario, modo, nombre)
            try:
                with open(ruta, "r", encoding="utf-8") as archivo:
                    if json.load(archivo):
                        cuentas.append((int(usuario), es_demo))
            except (OSError, ValueError):
                continue
    return cuentas


# -------------------------------------------------------------------------------------------------------
# ----------------------------- FIN Piña y Jara carpeta_usuario .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
