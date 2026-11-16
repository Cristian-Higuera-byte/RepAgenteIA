# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara crear_usuario_root .PY ---------------------------
# -------------------------------------------------------------------------------------------------------

"""Crea usuarios administradores (root) de la plataforma desde la terminal, sin pasar por el registro ni por el correo.

NOMBRE DEL ARCHIVO: crear_usuario_root.py

Uso (en la carpeta del proyecto, con el entorno virtual activado y el .env del servidor):
    python crear_usuario_root.py

Pide, uno por uno, el correo (debe terminar en @pyjfinance.cl), el nombre y la contraseña (escrita dos veces, sin que se vea en pantalla). La contraseña NO se guarda en
ningún archivo ni se muestra: se cifra (PBKDF2) y solo queda el hash en la tabla `usuarios`. El usuario se crea con el correo ya verificado y el rol «root»; si el correo ya
existe, se le da el rol root (y se deja verificado) sin cambiar su contraseña. Se detiene al dejar el correo vacío.

Requiere haber ejecutado antes herramientas/sql/roles.sql (la columna `rol`). Las contraseñas deben cumplir la regla de la plataforma: 8 o más caracteres con mayúscula,
minúscula, número y símbolo, y no ser una clave común. Guárdalas en un gestor de contraseñas, no en el proyecto, el .env ni el repositorio.
"""
import getpass
from datetime import datetime, timezone
from typing import Any

from herramientas import gestor_autenticacion, roles

# Dominio que deben tener los correos de los administradores
DOMINIO = "@pyjfinance.cl"


# TITULO ASCENDER

def _ascender(cliente: Any, usuario_id: Any) -> str | None:
    """Da el rol root al usuario y deja su correo verificado. Devuelve None si salió bien o el motivo del error."""
    ahora = datetime.now(timezone.utc).isoformat()
    try:
        cliente.table("usuarios").update({"rol": "root", "correo_verificado": True, "correo_verificado_en": ahora}).eq("id", usuario_id).execute()
        return None
    except Exception:  # noqa: BLE001 - puede que la verificación de correo no esté instalada: se prueba solo con el rol
        pass
    try:
        cliente.table("usuarios").update({"rol": "root"}).eq("id", usuario_id).execute()
        return None
    except Exception as e:  # noqa: BLE001
        return f"No se pudo dar el rol root (¿ejecutaste herramientas/sql/roles.sql?): {e}"


# TITULO CREAR O ASCENDER

def crear_o_ascender(cliente: Any, nombre: str, correo: str, contrasena: str) -> tuple[bool, str]:
    """Crea el usuario root (o, si el correo ya existe, le da el rol root) y devuelve (éxito, mensaje).

    Valida el dominio del correo y la regla de contraseña antes de tocar la base de datos. `cliente` es el cliente de la base de datos de la plataforma."""
    correo = (correo or "").strip().lower()
    nombre = (nombre or "").strip()
    if not correo.endswith(DOMINIO) or len(correo) <= len(DOMINIO):
        return False, f"El correo debe terminar en {DOMINIO}."
    existente = cliente.table("usuarios").select("id").eq("email", correo).limit(1).execute().data
    if existente:
        error = _ascender(cliente, existente[0]["id"])
        return (error is None), (error or f"{correo} ya existía: ahora es root (su contraseña no cambió).")
    if not nombre:
        return False, "Escribe un nombre."
    aviso = gestor_autenticacion.validar_contrasena(contrasena)
    if aviso:
        return False, aviso
    registro = {"nombre": nombre, "email": correo, "password_hash": gestor_autenticacion._cifrar_contrasena(contrasena), "rol": "root"}
    try:
        try:
            filas = cliente.table("usuarios").insert({**registro, "correo_verificado": True}).execute().data
        except Exception:  # noqa: BLE001 - sin la columna de verificación de correo
            filas = cliente.table("usuarios").insert(registro).execute().data
    except Exception as e:  # noqa: BLE001
        return False, f"No se pudo crear el usuario (¿ejecutaste herramientas/sql/roles.sql?): {e}"
    if not filas:
        return False, "No se pudo crear el usuario."
    roles.olvidar(filas[0].get("id"))
    return True, f"{correo} creado como root, con el correo verificado."


# TITULO PRINCIPAL

def principal() -> None:
    """Bucle interactivo: pide correo, nombre y contraseña (dos veces) y crea cada usuario root hasta que se deje el correo vacío."""
    cliente = gestor_autenticacion._supabase
    if cliente is None:
        print("La base de datos no está configurada (revisa BASE_DATOS y las variables de conexión en el .env).")
        return
    print(f"Crear usuarios root ({DOMINIO}). Deja el correo vacío para terminar.\n")
    while True:
        correo = input("Correo: ").strip().lower()
        if not correo:
            break
        existente = cliente.table("usuarios").select("id").eq("email", correo).limit(1).execute().data if correo.endswith(DOMINIO) else None
        nombre, contrasena = "", ""
        if not existente:
            nombre = input("Nombre completo: ").strip()
            contrasena = getpass.getpass("Contraseña (no se verá): ")
            if contrasena != getpass.getpass("Repite la contraseña: "):
                print("  Las contraseñas no coinciden; no se creó nada.\n")
                continue
        ok, mensaje = crear_o_ascender(cliente, nombre, correo, contrasena)
        print(("  OK: " if ok else "  ERROR: ") + mensaje + "\n")


if __name__ == "__main__":
    principal()


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara crear_usuario_root .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
