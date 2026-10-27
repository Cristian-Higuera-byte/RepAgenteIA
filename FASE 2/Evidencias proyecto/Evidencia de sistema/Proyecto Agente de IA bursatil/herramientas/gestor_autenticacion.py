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
from typing import Optional, cast

from dotenv import load_dotenv
from supabase import Client, create_client  # type: ignore[import-not-found]

load_dotenv()

# Credenciales de Supabase leídas del entorno (.env); vacías si no están definidas
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Cliente único (se crea solo si hay credenciales)
# Instancia compartida del cliente Supabase; None si no hay credenciales o falla la conexión.
_supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
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


# TITULO REGISTRAR USUARIO

# ==========================================
# Operaciones de usuario
# ==========================================
def registrar_usuario(nombre: str, correo: str, contrasena: str) -> dict:
    """
    Crea un usuario nuevo. Retorna {"ok": bool, "mensaje": str, "usuario": dict|None}.

    Valida que Supabase esté configurado, que los campos no estén vacíos y que
    la contraseña tenga al menos 6 caracteres; verifica que el email (normalizado
    a minúsculas) no exista y luego inserta el registro con la contraseña
    cifrada. El diccionario "usuario" solo incluye id, nombre y email (nunca el
    hash). Efecto secundario: lecturas y una inserción en la tabla `usuarios`.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "Supabase no está configurado (revisa SUPABASE_URL / SUPABASE_KEY en .env).", "usuario": None}

    nombre = (nombre or "").strip()
    correo = (correo or "").strip().lower()
    if not nombre or not correo or not contrasena:
        return {"ok": False, "mensaje": "Completa nombre, email y contraseña.", "usuario": None}
    if len(contrasena) < 6:
        return {"ok": False, "mensaje": "La contraseña debe tener al menos 6 caracteres.", "usuario": None}

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
        resultado = _supabase.table("usuarios").insert(registro).execute()
        if resultado.data:
            usuario = cast(dict, resultado.data[0])
            return {"ok": True, "mensaje": "Cuenta creada correctamente.",
                    "usuario": {"id": usuario.get("id"), "nombre": usuario.get("nombre"), "email": usuario.get("email")}}
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
        return {"ok": False, "mensaje": "Supabase no está configurado (revisa SUPABASE_URL / SUPABASE_KEY en .env).", "usuario": None}

    correo = (correo or "").strip().lower()
    if not correo or not contrasena:
        return {"ok": False, "mensaje": "Ingresa email y contraseña.", "usuario": None}

    try:
        resultado = _supabase.table("usuarios").select("*").eq("email", correo).limit(1).execute()
        if not resultado.data:
            return {"ok": False, "mensaje": "Email o contraseña incorrectos.", "usuario": None}

        usuario = cast(dict, resultado.data[0])
        if _verificar_contrasena(contrasena, usuario.get("password_hash", "")):
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
    (PBKDF2 con salt nuevo). La contraseña nueva se valida en el perfil (largo, letras y números); aquí solo se exige
    que no esté vacía. Efecto secundario: una lectura y una actualización en la tabla `usuarios`.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "Supabase no está configurado (revisa SUPABASE_URL / SUPABASE_KEY en .env)."}
    if not actual or not nueva:
        return {"ok": False, "mensaje": "Completa la contraseña actual y la nueva."}
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


# TITULO ACTUALIZAR NOMBRE

def actualizar_nombre(usuario_id, nombre: str) -> dict:
    """
    Actualiza el nombre que se muestra del usuario (columna `nombre` de `usuarios`). Retorna {"ok": bool, "mensaje": str}.

    Lo usa el perfil al guardar nombres y apellidos, para que la barra superior y el saludo muestren el nombre completo.
    """
    nombre = (nombre or "").strip()
    if _supabase is None:
        return {"ok": False, "mensaje": "Supabase no está configurado."}
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
