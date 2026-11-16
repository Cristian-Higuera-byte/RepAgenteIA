# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara crear_usuarios_prueba .PY --------------------------
# -------------------------------------------------------------------------------------------------------

"""Crea desde la terminal las cuentas de PRUEBA de la plataforma: una por plan (Gratis, Básico, Profesional y Avanzado), para que el equipo pruebe los límites y funciones de cada uno.

NOMBRE DEL ARCHIVO: crear_usuarios_prueba.py

Uso (en la carpeta del proyecto, con el entorno virtual activado y el .env del servidor):
    python crear_usuarios_prueba.py

Pide UNA contraseña (dos veces, sin que se vea) y la usa para las cuatro cuentas. No se guarda en ningún archivo: solo queda su hash en la tabla `usuarios`. Cada cuenta se crea
con el correo ya verificado, como usuario normal (NO root) y con su plan asignado a mano (origen «admin» en el historial de planes). Si una cuenta ya existe, solo se le fija el plan
y no se cambia su contraseña. Se puede repetir sin problema.

La contraseña debe cumplir la regla de la plataforma (8 o más caracteres con mayúscula, minúscula, número y símbolo, y no ser una clave común). Son cuentas de prueba: conviene
cambiarla o borrar las cuentas cuando terminen las pruebas. Para usar la plataforma cada cuenta debe conectar una API key de Capital.com (demo), igual que cualquier usuario.
"""
import getpass
from datetime import datetime, timezone
from typing import Any

from herramientas import gestor_autenticacion, plan_usuario

# Cuentas de prueba: (correo, nombre, plan)
CUENTAS_PRUEBA = [
    ("gratis@pyjfinance.cl", "Prueba Gratis", "gratis"),
    ("basico@pyjfinance.cl", "Prueba Basico", "basico"),
    ("profesional@pyjfinance.cl", "Prueba Profesional", "pro"),
    ("avanzado@pyjfinance.cl", "Prueba Avanzado", "avanzado"),
]


# TITULO CREAR O ACTUALIZAR

def crear_o_actualizar(cliente: Any, correo: str, nombre: str, plan: str, contrasena: str) -> tuple[bool, str]:
    """Crea la cuenta de prueba (o, si el correo ya existe, solo le fija el plan) y devuelve (éxito, mensaje).

    La contraseña se valida contra la regla de la plataforma antes de crear. El plan se guarda con origen «admin»."""
    correo = correo.strip().lower()
    existente = cliente.table("usuarios").select("id").eq("email", correo).limit(1).execute().data
    if existente:
        usuario_id, creada = existente[0]["id"], False
    else:
        aviso = gestor_autenticacion.validar_contrasena(contrasena)
        if aviso:
            return False, aviso
        registro = {"nombre": nombre, "email": correo, "password_hash": gestor_autenticacion._cifrar_contrasena(contrasena)}
        try:
            try:
                filas = cliente.table("usuarios").insert({**registro, "correo_verificado": True,
                                                          "correo_verificado_en": datetime.now(timezone.utc).isoformat()}).execute().data
            except Exception:  # noqa: BLE001 - sin la columna de verificación de correo
                filas = cliente.table("usuarios").insert(registro).execute().data
        except Exception as e:  # noqa: BLE001
            return False, f"No se pudo crear la cuenta: {e}"
        if not filas:
            return False, "No se pudo crear la cuenta."
        usuario_id, creada = filas[0]["id"], True
    if not plan_usuario.guardar(usuario_id, plan, "admin"):
        return False, f"{correo}: la cuenta existe pero no se pudo fijar el plan (¿existe la tabla planes_usuario y tiene permisos?)."
    return True, f"{correo}: {'creada' if creada else 'ya existía'} con el plan {plan}."


# TITULO PRINCIPAL

def principal() -> None:
    """Pide la contraseña una vez (dos veces para confirmarla) y crea las cuatro cuentas de prueba."""
    cliente = gestor_autenticacion._supabase
    if cliente is None:
        print("La base de datos no está configurada (revisa BASE_DATOS y las variables de conexión en el .env).")
        return
    print("Cuentas de prueba (una por plan):")
    for correo, _nombre, plan in CUENTAS_PRUEBA:
        print(f"  {correo}  ->  plan {plan}")
    contrasena = getpass.getpass("\nContraseña para las cuatro cuentas (no se verá): ")
    if contrasena != getpass.getpass("Repite la contraseña: "):
        print("Las contraseñas no coinciden; no se creó nada.")
        return
    print()
    for correo, nombre, plan in CUENTAS_PRUEBA:
        ok, mensaje = crear_o_actualizar(cliente, correo, nombre, plan, contrasena)
        print(("  OK: " if ok else "  ERROR: ") + mensaje)


if __name__ == "__main__":
    principal()


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara crear_usuarios_prueba .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
