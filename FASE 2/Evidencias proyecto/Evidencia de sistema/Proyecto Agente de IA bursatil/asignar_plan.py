# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara asignar_plan .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""Asigna a mano el plan de una cuenta desde la terminal (para pruebas y soporte), con o sin vencimiento.

NOMBRE DEL ARCHIVO: asignar_plan.py

Uso (en la carpeta del proyecto, con el entorno virtual activado y el .env del servidor):
    python asignar_plan.py correo plan [dias]

    correo   el correo de la cuenta (debe existir)
    plan     gratis, basico, pro (o profesional) o avanzado
    dias     opcional: cuántos días vale el plan de pago desde hoy (por ejemplo 30). Sin dias, el plan no vence. El plan Gratis nunca vence.

Ejemplos:
    python asignar_plan.py avanzado@pyjfinance.cl avanzado
    python asignar_plan.py basico@pyjfinance.cl basico 30
    python asignar_plan.py gratis@pyjfinance.cl gratis

El cambio queda en el historial de planes con origen «admin» y rige en menos de un minuto (o al reiniciar Streamlit). Para que el vencimiento funcione hay que haber ejecutado antes
herramientas/sql/planes_vencimiento.sql; sin esa columna el plan se asigna igual, pero sin fecha.
"""
import sys
from datetime import datetime
from typing import Any

import configuracion
from herramientas import gestor_autenticacion, plan_usuario

# Nombres alternativos que se aceptan para cada plan
_ALIAS = {"profesional": "pro", "gratuito": "gratis", "básico": "basico"}


# TITULO ASIGNAR

def asignar(cliente: Any, correo: str, plan: str, dias: int | None = None) -> tuple[bool, str]:
    """Fija el plan de la cuenta `correo` y devuelve (éxito, mensaje). `dias` es la duración del plan de pago desde hoy (None = no vence)."""
    plan = _ALIAS.get(plan.strip().lower(), plan.strip().lower())
    if plan not in configuracion.PLANES_IA:
        return False, f"El plan «{plan}» no existe. Usa: {', '.join(configuracion.PLANES_IA)}."
    if dias is not None and dias <= 0:
        return False, "Los días deben ser un número mayor que cero."
    correo = correo.strip().lower()
    filas = cliente.table("usuarios").select("id").eq("email", correo).limit(1).execute().data
    if not filas:
        return False, f"No existe ninguna cuenta con el correo {correo}."
    usuario_id = filas[0]["id"]
    anterior = plan_usuario.plan_de(usuario_id)
    if not plan_usuario.guardar(usuario_id, plan, "admin", anterior=anterior, dias=dias):
        return False, "No se pudo guardar el plan (¿existe la tabla planes_usuario y tiene permisos?)."
    nombre = configuracion.PLANES_IA[plan]["nombre"]
    vence = plan_usuario.vence_de(usuario_id)
    if vence:
        return True, f"{correo}: ahora en el plan {nombre}, vigente hasta el {datetime.fromtimestamp(vence).strftime('%d-%m-%Y')}."
    if dias and plan != "gratis":
        return True, f"{correo}: ahora en el plan {nombre}, pero SIN fecha de vencimiento: ejecuta herramientas/sql/planes_vencimiento.sql y repite el comando."
    return True, f"{correo}: ahora en el plan {nombre}."


# TITULO PRINCIPAL

def principal(argumentos: list[str]) -> int:
    """Lee los argumentos de la línea de comandos, asigna el plan e imprime el resultado. Devuelve 0 si salió bien y 1 si no."""
    if len(argumentos) not in (2, 3):
        print(__doc__)
        return 1
    try:
        dias = int(argumentos[2]) if len(argumentos) == 3 else None
    except ValueError:
        print("Los días deben ser un número, por ejemplo 30.")
        return 1
    cliente = gestor_autenticacion._supabase
    if cliente is None:
        print("La base de datos no está configurada (revisa BASE_DATOS y las variables de conexión en el .env).")
        return 1
    ok, mensaje = asignar(cliente, argumentos[0], argumentos[1], dias)
    print(("OK: " if ok else "ERROR: ") + mensaje)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara asignar_plan .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
