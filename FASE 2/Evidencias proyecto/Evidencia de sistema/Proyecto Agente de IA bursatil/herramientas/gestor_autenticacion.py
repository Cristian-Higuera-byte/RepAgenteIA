# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara gestor_autenticacion .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""
gestor_autenticacion.py
---------------
Gestión de autenticación de usuarios contra Supabase (tabla `usuarios`): registro, inicio de sesión, cambio de contraseña y de nombre.

Lo usa la pantalla de acceso (registro e inicio de sesión) de la aplicación.
Las credenciales de Supabase se leen del archivo .env (SUPABASE_URL y
SUPABASE_KEY); si faltan, las operaciones devuelven un mensaje de error.

- Las contraseñas NUNCA se guardan en texto plano: se almacena un hash
  PBKDF2-HMAC-SHA256 con salt aleatorio (biblioteca estándar `hashlib`).
- Tabla esperada en Supabase:
    create table usuarios (
        id bigserial primary key,
        nombre text not null,
        email text unique not null,
        password_hash text not null,
        creado_en timestamptz default now()
    );
"""
import os
import hmac
import hashlib
import binascii
import re
import sys
from typing import Any, Optional, cast

from dotenv import load_dotenv

from herramientas import base_datos, contrasenas, verificacion_correo
from herramientas import correo as servicio_correo

load_dotenv()

# Credenciales de Supabase leídas del entorno (.env); vacías si no están definidas
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Cliente único (se crea solo si hay credenciales)
# Instancia compartida del cliente de base de datos (Supabase o PostgreSQL, según BASE_DATOS del .env); el nombre `_supabase` se
# conserva porque otros módulos lo usan. None si no hay credenciales o falla la conexión.
_supabase: Optional[Any] = None
if base_datos.hay_credenciales():
    try:
        _supabase = base_datos.crear_cliente()
    except Exception:
        _supabase = None

# Número de iteraciones de PBKDF2: más iteraciones encarecen los ataques de fuerza bruta
_ITERACIONES = 120_000  # iteraciones PBKDF2


# TITULO CIFRAR CONTRASENA

# ==========================================
# Hashing de contraseñas
# ==========================================
def _cifrar_contrasena(contrasena: str) -> str:
    """
    Genera el hash almacenable de una contraseña con PBKDF2-HMAC-SHA256.

    Crea un salt aleatorio de 16 bytes y devuelve el texto 'salt$hash' (ambos en
    hexadecimal), formato que `_verificar_contrasena` sabe leer.
    """
    # Salt aleatorio por usuario para que contraseñas iguales den hashes distintos.
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), salt, _ITERACIONES)
    return binascii.hexlify(salt).decode() + "$" + binascii.hexlify(dk).decode()


# TITULO VERIFICAR CONTRASENA

def _verificar_contrasena(contrasena: str, almacenado: str) -> bool:
    """
    Comprueba si una contraseña coincide con el valor 'salt$hash' guardado.

    Recalcula el hash con el salt almacenado y lo compara en tiempo constante.
    Devuelve False ante cualquier formato inválido en lugar de lanzar excepción.
    """
    try:
        # Separa el salt y el hash guardados.
        salt_hex, dk_hex = almacenado.split("$")
        salt = binascii.unhexlify(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), salt, _ITERACIONES)
        # Comparación en tiempo constante
        return hmac.compare_digest(binascii.hexlify(dk).decode(), dk_hex)
    except Exception:
        return False


# TITULO VERIFICACION ACTIVA

def verificacion_activa() -> bool:
    """True si el .env activa la confirmación del correo (VERIFICACION_CORREO=true).

    Sin esa variable la plataforma se comporta como antes: el registro inicia sesión de inmediato y no se pide confirmar el correo (así siguen
    funcionando los equipos de desarrollo sin servidor de correo). Con la variable activa y el correo mal configurado no se vuelve al modo anterior:
    la persona no recibe el enlace y no puede entrar, para que un error de configuración no deje cuentas sin verificar.
    """
    return os.environ.get("VERIFICACION_CORREO", "").strip().lower() in ("1", "true", "si", "sí", "activa")


# TITULO ERROR NEUTRO

def _error_neutro(accion: str, error: Exception) -> dict:
    """Respuesta {"ok": False, "mensaje": ...} para un fallo inesperado: la persona ve un texto neutro y el detalle técnico queda solo en el registro del servidor."""
    print(f"[Autenticación] Falló {accion}: {error}", file=sys.stderr, flush=True)
    return {"ok": False, "mensaje": "No pudimos completar la operación en este momento. Inténtalo de nuevo en unos minutos."}


# TITULO VALIDAR CONTRASENA

def validar_contrasena(contrasena: str) -> Optional[str]:
    """Devuelve el aviso a mostrar si la contraseña no cumple la regla única de la plataforma (herramientas/contrasenas.py), o None si es válida."""
    return contrasenas.validar(contrasena)


# TITULO REGISTRAR USUARIO

# ==========================================
# Operaciones de usuario
# ==========================================
def registrar_usuario(nombre: str, correo: str, contrasena: str) -> dict:
    """
    Crea un usuario nuevo. Retorna {"ok": bool, "mensaje": str, "usuario": dict|None}.

    Valida que Supabase esté configurado, que los campos no estén vacíos y que
    la contraseña cumpla la regla de seguridad (8 o más caracteres con mayúscula, minúscula, número y símbolo, y no sea común); verifica que el email (normalizado
    a minúsculas) no exista y luego inserta el registro con la contraseña
    cifrada. El diccionario "usuario" solo incluye id, nombre y email (nunca el
    hash). Efecto secundario: lecturas y una inserción en la tabla `usuarios`.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada (revisa BASE_DATOS y las variables de conexión en .env).", "usuario": None}

    nombre = (nombre or "").strip()
    correo = (correo or "").strip().lower()
    if not nombre or not correo or not contrasena:
        return {"ok": False, "mensaje": "Completa nombre, email y contraseña.", "usuario": None}
    aviso_contrasena = validar_contrasena(contrasena)
    if aviso_contrasena:
        return {"ok": False, "mensaje": aviso_contrasena, "usuario": None}

    try:
        # ¿Ya existe el email?
        existe = _supabase.table("usuarios").select("id").eq("email", correo).execute()
        if existe.data:
            return {"ok": False, "mensaje": "Ya existe una cuenta con ese email.", "usuario": None}

        registro = {
            "nombre": nombre,
            "email": correo,
            "password_hash": _cifrar_contrasena(contrasena),
        }
        con_verificacion = verificacion_activa()
        if con_verificacion:
            registro["correo_verificado"] = False
        resultado = _supabase.table("usuarios").insert(registro).execute()
        if resultado.data:
            usuario = cast(dict, resultado.data[0])
            datos = {"id": usuario.get("id"), "nombre": usuario.get("nombre"), "email": usuario.get("email")}
            if not con_verificacion:
                return {"ok": True, "mensaje": "Cuenta creada correctamente.", "usuario": datos}
            try:
                verificacion_correo.enviar_enlace(_supabase, datos["id"], datos["nombre"], datos["email"], verificacion_correo.VERIFICACION)
                aviso = "Cuenta creada. Revisa tu correo para confirmarla."
            except verificacion_correo.ErrorEnlace:
                aviso = "Cuenta creada, pero no pudimos enviar el correo de confirmación. Pide otro enlace al iniciar sesión."
            return {"ok": True, "mensaje": aviso, "usuario": datos, "requiere_verificacion": True}
        return {"ok": False, "mensaje": "No se pudo crear la cuenta.", "usuario": None}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error al registrar: {e}", "usuario": None}


# TITULO AUTENTICAR USUARIO

def autenticar_usuario(correo: str, contrasena: str) -> dict:
    """
    Valida credenciales. Retorna {"ok": bool, "mensaje": str, "usuario": dict|None}.

    Busca el usuario por email (normalizado a minúsculas) en Supabase y verifica
    la contraseña contra el hash guardado. Usa el mismo mensaje genérico para
    email inexistente y contraseña errónea, para no revelar qué cuentas existen.
    Efecto secundario: consulta de red a la tabla `usuarios`.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada (revisa BASE_DATOS y las variables de conexión en .env).", "usuario": None}

    correo = (correo or "").strip().lower()
    if not correo or not contrasena:
        return {"ok": False, "mensaje": "Ingresa email y contraseña.", "usuario": None}

    try:
        resultado = _supabase.table("usuarios").select("*").eq("email", correo).limit(1).execute()
        if not resultado.data:
            return {"ok": False, "mensaje": "Email o contraseña incorrectos.", "usuario": None}

        usuario = cast(dict, resultado.data[0])
        if _verificar_contrasena(contrasena, usuario.get("password_hash", "")):
            if verificacion_activa() and usuario.get("correo_verificado") is False:
                return {"ok": False, "codigo": "sin_verificar", "mensaje": "Tu correo aún no está verificado.", "usuario": None,
                        "pendiente": {"id": usuario.get("id"), "nombre": usuario.get("nombre"), "email": usuario.get("email")}}
            return {"ok": True, "mensaje": "Sesión iniciada.",
                    "usuario": {"id": usuario.get("id"), "nombre": usuario.get("nombre"), "email": usuario.get("email")}}
        return {"ok": False, "mensaje": "Email o contraseña incorrectos.", "usuario": None}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error al iniciar sesión: {e}", "usuario": None}


# TITULO CAMBIAR CONTRASENA

def cambiar_contrasena(usuario_id, actual: str, nueva: str) -> dict:
    """
    Cambia la contraseña de un usuario. Retorna {"ok": bool, "mensaje": str}.

    Lee el hash guardado del usuario (por id), exige que `actual` coincida con él y guarda el hash de `nueva`
    (PBKDF2 con salt nuevo). La contraseña nueva debe cumplir la regla de herramientas/contrasenas.py (también se avisa antes en el perfil). Efecto secundario: una lectura y una actualización en la tabla `usuarios`.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada (revisa BASE_DATOS y las variables de conexión en .env)."}
    if not actual or not nueva:
        return {"ok": False, "mensaje": "Completa la contraseña actual y la nueva."}
    aviso = validar_contrasena(nueva)
    if aviso:
        return {"ok": False, "mensaje": aviso}
    try:
        fila = _supabase.table("usuarios").select("password_hash").eq("id", usuario_id).limit(1).execute()
        if not fila.data:
            return {"ok": False, "mensaje": "No se encontró tu usuario."}
        if not _verificar_contrasena(actual, cast(dict, fila.data[0]).get("password_hash", "")):
            return {"ok": False, "mensaje": "La contraseña actual no es correcta."}
        _supabase.table("usuarios").update({"password_hash": _cifrar_contrasena(nueva)}).eq("id", usuario_id).execute()
        return {"ok": True, "mensaje": "Contraseña actualizada."}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error al cambiar la contraseña: {e}"}


# TITULO VERIFICAR CORREO

def verificar_correo(token: str) -> dict:
    """
    Confirma el correo de una cuenta con el enlace que le llegó. Retorna {"ok": bool, "mensaje": str}.

    El enlace se consume (solo sirve una vez y vence a las 24 horas) y la cuenta pasa a «correo verificado». Efecto secundario: una actualización
    en `enlaces_correo` y otra en `usuarios`.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada."}
    try:
        usuario_id = verificacion_correo.consumir(_supabase, token, verificacion_correo.VERIFICACION)
        if usuario_id is None:
            return {"ok": False, "mensaje": "El enlace no es válido o ya venció. Inicia sesión para pedir uno nuevo."}
        _supabase.table("usuarios").update({"correo_verificado": True, "correo_verificado_en": verificacion_correo.ahora_utc().isoformat()}).eq("id", usuario_id).execute()
        return {"ok": True, "mensaje": "Correo confirmado. Ya puedes iniciar sesión."}
    except Exception as e:
        return _error_neutro("la confirmación del correo", e)


# TITULO REENVIAR VERIFICACION

def reenviar_verificacion(usuario_id, nombre: str, destinatario: str) -> dict:
    """
    Envía un enlace de confirmación nuevo a una cuenta que la propia plataforma ya identificó. Retorna {"ok": bool, "mensaje": str}.

    Se usa solo con los datos que guardó el servidor (la cuenta recién creada, o la que acaba de escribir bien su contraseña), nunca con una dirección que
    alguien escriba en un formulario: así nadie puede usar este botón para enviar correos a terceros ni para saber qué cuentas existen.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada."}
    try:
        verificacion_correo.enviar_enlace(_supabase, usuario_id, nombre, destinatario, verificacion_correo.VERIFICACION)
        return {"ok": True, "mensaje": "Te enviamos un nuevo enlace. Revisa tu correo."}
    except verificacion_correo.ErrorEnlace as error:
        return {"ok": False, "mensaje": str(error)}
    except Exception as e:
        return _error_neutro("el reenvío del enlace", e)


# TITULO SOLICITAR RECUPERACION

def solicitar_recuperacion(correo: str) -> dict:
    """
    Envía el enlace para restablecer la contraseña. Retorna {"ok": bool, "mensaje": str}.

    Responde siempre el mismo mensaje exista o no una cuenta con ese correo, para no revelar qué cuentas existen. Los fallos (por ejemplo, pedirlo muy
    seguido) se anotan en el registro del servidor y no se muestran. Efecto secundario: una lectura en `usuarios` y, si existe, un correo.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada."}
    if not servicio_correo.configurado():
        return {"ok": False, "mensaje": "La recuperación de contraseña no está disponible en este momento."}
    correo = (correo or "").strip().lower()
    if not correo or "@" not in correo:
        return {"ok": False, "mensaje": "Escribe tu correo electrónico."}
    generico = {"ok": True, "mensaje": "Si existe una cuenta con ese correo, te enviamos un enlace para restablecer la contraseña."}
    try:
        filas = _supabase.table("usuarios").select("id,nombre,email").eq("email", correo).limit(1).execute().data
        if filas:
            usuario = cast(dict, filas[0])
            verificacion_correo.enviar_enlace(_supabase, usuario["id"], usuario.get("nombre") or "", usuario["email"], verificacion_correo.RECUPERACION)
    except Exception as e:
        print(f"[Correo] Recuperación no enviada: {e}", flush=True)
    return generico


# TITULO RESTABLECER CONTRASENA

def restablecer_contrasena(token: str, nueva: str) -> dict:
    """
    Cambia la contraseña con el enlace de recuperación. Retorna {"ok": bool, "mensaje": str}.

    Valida la contraseña nueva ANTES de usar el enlace, así una contraseña débil no lo gasta. Al terminar, la cuenta queda con el correo verificado (quien
    recibió el enlace demostró que controla ese correo) y se cierran todas sus sesiones guardadas. Efecto secundario: actualizaciones en
    `enlaces_correo`, `usuarios` y `sesiones_persistentes`.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada."}
    aviso = validar_contrasena(nueva)
    if aviso:
        return {"ok": False, "mensaje": aviso}
    try:
        usuario_id = verificacion_correo.consumir(_supabase, token, verificacion_correo.RECUPERACION)
        if usuario_id is None:
            return {"ok": False, "mensaje": "El enlace no es válido o ya venció. Pide uno nuevo."}
        cambios = {"password_hash": _cifrar_contrasena(nueva)}
        if verificacion_activa():
            cambios.update({"correo_verificado": True, "correo_verificado_en": verificacion_correo.ahora_utc().isoformat()})
        _supabase.table("usuarios").update(cambios).eq("id", usuario_id).execute()
        from herramientas import sesion_persistente
        sesion_persistente.revocar_todas(usuario_id)
        return {"ok": True, "mensaje": "Contraseña actualizada. Ya puedes iniciar sesión."}
    except Exception as e:
        return _error_neutro("el restablecimiento de la contraseña", e)


# TITULO ACTUALIZAR NOMBRE

def actualizar_nombre(usuario_id, nombre: str) -> dict:
    """
    Actualiza el nombre que se muestra del usuario (columna `nombre` de `usuarios`). Retorna {"ok": bool, "mensaje": str}.

    Lo usa el perfil al guardar nombres y apellidos, para que la barra superior y el saludo muestren el nombre completo.
    """
    nombre = (nombre or "").strip()
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada."}
    if not nombre:
        return {"ok": False, "mensaje": "El nombre no puede estar vacío."}
    try:
        _supabase.table("usuarios").update({"nombre": nombre}).eq("id", usuario_id).execute()
        return {"ok": True, "mensaje": "Nombre actualizado."}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error al actualizar el nombre: {e}"}


# -------------------------------------------------------------------------------------------------------
# ------------------------------- FIN Piña y Jara gestor_autenticacion .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
