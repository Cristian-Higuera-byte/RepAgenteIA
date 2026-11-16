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
import math
import os
import hmac
import hashlib
import binascii
import re
import secrets
import sys
from typing import Any, Optional, cast

from dotenv import load_dotenv

from herramientas import base_datos, contrasenas, correos_temporales, limites_formularios, verificacion_correo
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
    if limites_formularios.excede((nombre, limites_formularios.NOMBRE_COMPLETO), (correo, limites_formularios.CORREO), (contrasena, limites_formularios.CONTRASENA)):
        return {"ok": False, "mensaje": "Revisa los datos: alguno es demasiado largo.", "usuario": None}
    aviso_correo = correos_temporales.validar(correo)
    if aviso_correo:
        return {"ok": False, "mensaje": aviso_correo, "usuario": None}
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


# TITULO ACCESO CON GOOGLE

def acceso_con_google(correo: str) -> dict:
    """Resuelve el ingreso de alguien que Google ya identificó (correo verificado por Google).

    Retorna {"ok": True, "usuario": {id, nombre, email}} si el correo ya tiene cuenta (y, como Google lo verificó, la deja con el correo confirmado);
    {"ok": False, "codigo": "nuevo"} si no existe y hay que pedirle los datos para crearla; {"ok": False, "mensaje": ...} si el correo no sirve o falla la base.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada (revisa BASE_DATOS y las variables de conexión en .env)."}
    correo = (correo or "").strip().lower()
    if not correo or limites_formularios.excede((correo, limites_formularios.CORREO)):
        return {"ok": False, "mensaje": "Google no entregó un correo válido."}
    try:
        existe = _supabase.table("usuarios").select("*").eq("email", correo).limit(1).execute()
        if not existe.data:
            aviso_correo = correos_temporales.validar(correo, verificado_por_google=True)
            if aviso_correo:
                return {"ok": False, "mensaje": aviso_correo}
            return {"ok": False, "codigo": "nuevo"}
        usuario = cast(dict, existe.data[0])
        if verificacion_activa() and usuario.get("correo_verificado") is False:
            _supabase.table("usuarios").update({"correo_verificado": True}).eq("id", usuario.get("id")).execute()
        return {"ok": True, "usuario": {"id": usuario.get("id"), "nombre": usuario.get("nombre"), "email": usuario.get("email")}}
    except Exception as e:
        return _error_neutro("el acceso con Google", e)


# TITULO REGISTRAR CON GOOGLE

def registrar_con_google(nombre: str, correo: str) -> dict:
    """Crea la cuenta de alguien que entró con Google. Retorna {"ok": bool, "mensaje": str, "usuario": dict|None}.

    El correo ya viene verificado por Google, así que no se envía enlace de confirmación. La cuenta se crea con una contraseña aleatoria que nadie conoce:
    la persona entra siempre con Google, y si algún día quiere una contraseña propia la elige con «Olvidé mi contraseña».
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada (revisa BASE_DATOS y las variables de conexión en .env).", "usuario": None}
    nombre = (nombre or "").strip()
    correo = (correo or "").strip().lower()
    if not nombre or not correo:
        return {"ok": False, "mensaje": "Faltan datos para crear la cuenta.", "usuario": None}
    if limites_formularios.excede((nombre, limites_formularios.NOMBRE_COMPLETO), (correo, limites_formularios.CORREO)):
        return {"ok": False, "mensaje": "Revisa los datos: alguno es demasiado largo.", "usuario": None}
    aviso_correo = correos_temporales.validar(correo, verificado_por_google=True)
    if aviso_correo:
        return {"ok": False, "mensaje": aviso_correo, "usuario": None}
    try:
        if _supabase.table("usuarios").select("id").eq("email", correo).execute().data:
            return {"ok": False, "mensaje": "Ya existe una cuenta con ese email.", "usuario": None}
        registro = {"nombre": nombre, "email": correo, "password_hash": _cifrar_contrasena(secrets.token_urlsafe(32))}
        if verificacion_activa():
            registro["correo_verificado"] = True
        resultado = _supabase.table("usuarios").insert(registro).execute()
        if resultado.data:
            usuario = cast(dict, resultado.data[0])
            return {"ok": True, "mensaje": "Cuenta creada correctamente.", "usuario": {"id": usuario.get("id"), "nombre": usuario.get("nombre"), "email": usuario.get("email")}}
        return {"ok": False, "mensaje": "No se pudo crear la cuenta.", "usuario": None}
    except Exception as e:
        return {**_error_neutro("el registro con Google", e), "usuario": None}


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
    if limites_formularios.excede((correo, limites_formularios.CORREO), (contrasena, limites_formularios.CONTRASENA)):
        return {"ok": False, "mensaje": "Email o contraseña incorrectos.", "usuario": None}      # mismo texto genérico: no se revela nada y no se gasta tiempo cifrando un texto enorme

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

    Responde igual exista o no una cuenta con ese correo, para no revelar qué cuentas existen: el mensaje, la espera visible («podrás pedir otro en X min») y el máximo diario
    se aplican por CORREO (no por cuenta) en una reserva atómica de la base de datos, así dos solicitudes simultáneas no envían dos correos; el envío sale en un hilo aparte para que
    tampoco el tiempo de respuesta delate la cuenta. Los demás fallos se anotan en el registro del servidor y no se muestran. Efecto secundario: una lectura en `usuarios`, la reserva
    y, si la cuenta existe, un correo.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada."}
    if not servicio_correo.configurado():
        return {"ok": False, "mensaje": "La recuperación de contraseña no está disponible en este momento."}
    correo = (correo or "").strip().lower()
    if not correo or "@" not in correo or limites_formularios.excede((correo, limites_formularios.CORREO)):
        return {"ok": False, "mensaje": "Escribe tu correo electrónico."}
    generico = {"ok": True, "mensaje": f"Si existe una cuenta con ese correo, te enviamos un enlace para restablecer la contraseña. El enlace dura {verificacion_correo.MINUTOS_RECUPERACION} minutos."}
    try:
        filas = _supabase.table("usuarios").select("id,nombre,email").eq("email", correo).limit(1).execute().data
        usuario = cast(dict, filas[0]) if filas else None
        token, solicitud = verificacion_correo.reservar_recuperacion(_supabase, correo, usuario["id"] if usuario else None)
        if usuario:
            verificacion_correo.en_segundo_plano(lambda: verificacion_correo.enviar_recuperacion(_supabase, usuario["id"], usuario.get("nombre") or "", usuario["email"], token, solicitud))
    except verificacion_correo.ErrorEspera as espera:
        # Ya se envió un enlace hace poco: se le dice a la persona cuánto falta para poder pedir otro (así sabe que el correo ya salió y dónde buscarlo).
        minutos = max(1, math.ceil(espera.segundos / 60))
        print(f"[Correo] Recuperación no enviada: ya se envió un enlace; faltan {minutos} min", flush=True)
        return {"ok": True, "espera_minutos": minutos,
                "mensaje": f"Ya enviamos un enlace a este correo hace poco. Revisa tu bandeja de entrada y la carpeta de spam. Podrás pedir otro en {minutos} min."}
    except verificacion_correo.ErrorEnlace as limite:
        if "demasiados" in str(limite):
            print(f"[Correo] Recuperación no enviada: {limite}", flush=True)
            return {"ok": False, "mensaje": "Ya pediste el máximo de enlaces por hoy. Inténtalo de nuevo mañana."}
        print(f"[Correo] Recuperación no enviada: {limite}", flush=True)
    except Exception as e:
        print(f"[Correo] Recuperación no enviada: {e}", flush=True)
    return generico


# TITULO RESTABLECER CONTRASENA

def restablecer_contrasena(token: str, nueva: str) -> dict:
    """
    Cambia la contraseña con el enlace de recuperación. Retorna {"ok": bool, "mensaje": str}.

    Valida la contraseña nueva ANTES de usar el enlace, así una contraseña débil no lo gasta. El enlace se usa y la contraseña se guarda en UNA sola transacción de la base de datos
    (`restablecer_contrasena_atomico`): si el guardado falla, el enlace sigue sirviendo y la contraseña anterior no cambia. Al terminar, la cuenta queda con el correo verificado (quien
    recibió el enlace demostró que controla ese correo) y se cierran todas sus sesiones guardadas. Efecto secundario: actualizaciones en `enlaces_correo`, `usuarios` y `sesiones_persistentes`.
    """
    if _supabase is None:
        return {"ok": False, "mensaje": "La base de datos no está configurada."}
    if limites_formularios.excede((nueva, limites_formularios.CONTRASENA)):
        return {"ok": False, "mensaje": f"La contraseña no puede tener más de {limites_formularios.CONTRASENA} caracteres."}
    aviso = validar_contrasena(nueva)
    if aviso:
        return {"ok": False, "mensaje": aviso}
    try:
        # Antes de gastar el enlace se comprueba que la contraseña nueva no sea igual a la actual: así quien se equivoca puede elegir otra con el mismo enlace.
        vigente = verificacion_correo.consultar(_supabase, token, verificacion_correo.RECUPERACION)
        if vigente is None:
            return {"ok": False, "mensaje": "El enlace no es válido o ya venció. Pide uno nuevo."}
        actual = _supabase.table("usuarios").select("password_hash").eq("id", vigente[0]).limit(1).execute().data
        if actual and _verificar_contrasena(nueva, actual[0].get("password_hash", "")):
            return {"ok": False, "mensaje": "La contraseña nueva no puede ser igual a la actual. Elige otra."}
        usuario_id = verificacion_correo.restablecer_atomico(_supabase, token, _cifrar_contrasena(nueva), verificacion_activa())
        if usuario_id is None:
            return {"ok": False, "mensaje": "El enlace no es válido o ya venció. Pide uno nuevo."}
        from herramientas import sesion_persistente, token_datos
        sesion_persistente.revocar_todas(usuario_id)
        token_datos.revocar_usuario(usuario_id)      # el token del servidor de datos y sus conexiones en vivo también dejan de servir
        return {"ok": True, "mensaje": "Contraseña actualizada. Ya puedes iniciar sesión."}
    except Exception as e:
        return _error_neutro("el restablecimiento de la contraseña", e)


# TITULO SEGUNDOS RESTANTES RECUPERACION

def segundos_restantes_recuperacion(token: str) -> Optional[int]:
    """Segundos que le quedan al enlace de recuperación `token` (0 o más), o None si no es válido, ya se usó o ya venció. No gasta el enlace.

    Lo usa la pantalla de la contraseña nueva para mostrar la cuenta regresiva y no dejar escribir una contraseña si el enlace ya no sirve."""
    if _supabase is None:
        return None
    try:
        vigente = verificacion_correo.consultar(_supabase, token, verificacion_correo.RECUPERACION)
    except Exception:  # noqa: BLE001 - un fallo de la base no debe romper la pantalla
        return None
    if vigente is None:
        return None
    return max(0, int((vigente[1] - verificacion_correo.ahora_utc()).total_seconds()))


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
