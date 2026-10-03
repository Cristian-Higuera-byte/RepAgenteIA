"""
auth_manager.py
---------------
Gestión de autenticación de usuarios contra Supabase (tabla `usuarios`).

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

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Cliente único (se crea solo si hay credenciales)
_supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        _supabase = None

_ITERACIONES = 120_000  # iteraciones PBKDF2


# ==========================================
# Hashing de contraseñas
# ==========================================
def _hash_password(password: str) -> str:
    """Genera 'salt$hash' con PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERACIONES)
    return binascii.hexlify(salt).decode() + "$" + binascii.hexlify(dk).decode()


def _verificar_password(password: str, almacenado: str) -> bool:
    """Compara la contraseña con el hash guardado."""
    try:
        salt_hex, dk_hex = almacenado.split("$")
        salt = binascii.unhexlify(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERACIONES)
        # Comparación en tiempo constante
        return hmac.compare_digest(binascii.hexlify(dk).decode(), dk_hex)
    except Exception:
        return False


# ==========================================
# Operaciones de usuario
# ==========================================
def registrar_usuario(nombre: str, email: str, password: str) -> dict:
    """
    Crea un usuario nuevo. Retorna {"ok": bool, "mensaje": str, "usuario": dict|None}.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "Supabase no está configurado (revisa SUPABASE_URL / SUPABASE_KEY en .env).", "usuario": None}

    nombre = (nombre or "").strip()
    email = (email or "").strip().lower()
    if not nombre or not email or not password:
        return {"ok": False, "mensaje": "Completa nombre, email y contraseña.", "usuario": None}
    if len(password) < 6:
        return {"ok": False, "mensaje": "La contraseña debe tener al menos 6 caracteres.", "usuario": None}

    try:
        # ¿Ya existe el email?
        existe = _supabase.table("usuarios").select("id").eq("email", email).execute()
        if existe.data:
            return {"ok": False, "mensaje": "Ya existe una cuenta con ese email.", "usuario": None}

        registro = {
            "nombre": nombre,
            "email": email,
            "password_hash": _hash_password(password),
        }
        resultado = _supabase.table("usuarios").insert(registro).execute()
        if resultado.data:
            usuario = cast(dict, resultado.data[0])
            return {"ok": True, "mensaje": "Cuenta creada correctamente.",
                    "usuario": {"id": usuario.get("id"), "nombre": usuario.get("nombre"), "email": usuario.get("email")}}
        return {"ok": False, "mensaje": "No se pudo crear la cuenta.", "usuario": None}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error al registrar: {e}", "usuario": None}


def autenticar_usuario(email: str, password: str) -> dict:
    """
    Valida credenciales. Retorna {"ok": bool, "mensaje": str, "usuario": dict|None}.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "Supabase no está configurado (revisa SUPABASE_URL / SUPABASE_KEY en .env).", "usuario": None}

    email = (email or "").strip().lower()
    if not email or not password:
        return {"ok": False, "mensaje": "Ingresa email y contraseña.", "usuario": None}

    try:
        resultado = _supabase.table("usuarios").select("*").eq("email", email).limit(1).execute()
        if not resultado.data:
            return {"ok": False, "mensaje": "Email o contraseña incorrectos.", "usuario": None}

        usuario = cast(dict, resultado.data[0])
        if _verificar_password(password, usuario.get("password_hash", "")):
            return {"ok": True, "mensaje": "Sesión iniciada.",
                    "usuario": {"id": usuario.get("id"), "nombre": usuario.get("nombre"), "email": usuario.get("email")}}
        return {"ok": False, "mensaje": "Email o contraseña incorrectos.", "usuario": None}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error al iniciar sesión: {e}", "usuario": None}