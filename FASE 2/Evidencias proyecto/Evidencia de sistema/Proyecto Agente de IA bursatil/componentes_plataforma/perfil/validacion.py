# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara validacion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Validaciones del perfil de usuario: documento (RUT con dígito verificador), teléfono, edad, contraseña y porcentaje completo.

Son funciones puras (sin Streamlit ni red) que devuelven (ok, mensaje) o el valor normalizado, para poder probarlas solas.
"""
import re
from datetime import date
from typing import Any

from componentes_plataforma.perfil.datos import REQUERIDOS, SECCIONES

# Edad mínima para operar y máxima aceptada al leer una fecha de nacimiento.
EDAD_MINIMA = 18
EDAD_MAXIMA = 120


# TITULO LIMPIAR RUT

def limpiar_rut(texto: str) -> str:
    """Deja el RUT solo con dígitos y la K final en mayúscula (sin puntos, guion ni espacios)."""
    return re.sub(r"[^0-9kK]", "", texto or "").upper()


# TITULO DIGITO VERIFICADOR

def digito_verificador(cuerpo: str) -> str:
    """Calcula el dígito verificador (módulo 11) de la parte numérica de un RUT chileno; "K" si corresponde al 10."""
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - suma % 11
    return "0" if resto == 11 else "K" if resto == 10 else str(resto)


# TITULO FORMATEAR RUT

def formatear_rut(texto: str) -> str:
    """Devuelve el RUT con puntos y guion (12.345.678-5); si no tiene al menos 2 caracteres lo devuelve limpio."""
    limpio = limpiar_rut(texto)
    if len(limpio) < 2:
        return limpio
    cuerpo, dv = limpio[:-1], limpio[-1]
    return f"{int(cuerpo):,}".replace(",", ".") + "-" + dv


# TITULO VALIDAR DOCUMENTO

def validar_documento(tipo: str, numero: str) -> tuple[bool, str, str]:
    """Valida el número de documento según su tipo y devuelve (ok, mensaje, número normalizado).

    RUT: 7 u 8 dígitos más dígito verificador correcto. Cédula/DNI: 5 a 15 letras o números. Pasaporte y carnet de
    extranjería: 5 a 20 letras o números. El número normalizado va en mayúsculas y sin espacios (el RUT con puntos y guion)."""
    numero = (numero or "").strip()
    if not numero:
        return False, "Ingresa el número de documento.", ""
    if tipo == "rut":
        limpio = limpiar_rut(numero)
        if not re.fullmatch(r"\d{7,8}[0-9K]", limpio):
            return False, "El RUT debe tener 7 u 8 dígitos y su dígito verificador.", ""
        if digito_verificador(limpio[:-1]) != limpio[-1]:
            return False, "El dígito verificador del RUT no es válido.", ""
        return True, "", formatear_rut(limpio)
    limpio = re.sub(r"[\s.-]", "", numero).upper()
    minimo, maximo = (5, 15) if tipo == "cedula" else (5, 20)
    if not re.fullmatch(rf"[0-9A-Z]{{{minimo},{maximo}}}", limpio):
        return False, f"El documento debe tener entre {minimo} y {maximo} letras o números.", ""
    return True, "", limpio


# TITULO VALIDAR TELEFONO

def validar_telefono(numero: str, opcional: bool = False) -> tuple[bool, str, str]:
    """Valida un teléfono (sin el prefijo del país): de 7 a 12 dígitos tras quitar espacios, guiones y paréntesis.

    Devuelve (ok, mensaje, número normalizado). Con `opcional` un valor vacío es válido."""
    limpio = re.sub(r"[\s().-]", "", numero or "")
    if not limpio:
        return (True, "", "") if opcional else (False, "Ingresa tu número de celular.", "")
    if not re.fullmatch(r"\d{7,12}", limpio):
        return False, "El teléfono debe tener entre 7 y 12 dígitos, solo números.", ""
    return True, "", limpio


# TITULO VALIDAR APODO

def validar_apodo(texto: str) -> tuple[bool, str, str | None]:
    """Valida el apodo (opcional): de 3 a 30 caracteres con letras (con tildes), números, espacios, punto, guion y guion bajo.

    Quita los espacios de los extremos y junta los espacios repetidos. Devuelve (ok, mensaje, apodo normalizado); un apodo vacío es válido y
    se devuelve como None para que la base lo guarde como vacío (así la unicidad no lo cuenta)."""
    limpio = re.sub(r"\s+", " ", texto or "").strip()
    if not limpio:
        return True, "", None
    if not 3 <= len(limpio) <= 30:
        return False, "El apodo debe tener entre 3 y 30 caracteres.", None
    if not re.fullmatch(r"[\w .-]+", limpio):
        return False, "El apodo solo puede llevar letras, números, espacios, punto, guion y guion bajo.", None
    return True, "", limpio


# TITULO EDAD

def edad(nacimiento: date, hoy: date | None = None) -> int:
    """Edad en años cumplidos a la fecha `hoy` (hoy si no se indica)."""
    hoy = hoy or date.today()
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))


# TITULO VALIDAR NACIMIENTO

def validar_nacimiento(nacimiento: date | None) -> tuple[bool, str]:
    """Comprueba que la fecha de nacimiento exista, no sea futura y corresponda a un mayor de 18 años."""
    if nacimiento is None:
        return False, "Indica tu fecha de nacimiento."
    años = edad(nacimiento)
    if años < 0 or años > EDAD_MAXIMA:
        return False, "La fecha de nacimiento no es válida."
    if años < EDAD_MINIMA:
        return False, f"Debes ser mayor de {EDAD_MINIMA} años para operar."
    return True, ""


# TITULO VALIDAR CONTRASENA NUEVA

def validar_contrasena_nueva(actual: str, nueva: str, repetida: str) -> tuple[bool, str]:
    """Valida el cambio de contraseña: no vacía, distinta de la actual, de 8 o más caracteres con letras y números, y repetida igual."""
    if not actual or not nueva or not repetida:
        return False, "Completa los tres campos."
    if nueva == actual:
        return False, "La contraseña nueva debe ser distinta de la actual."
    if len(nueva) < 8 or not re.search(r"[A-Za-z]", nueva) or not re.search(r"\d", nueva):
        return False, "La contraseña nueva debe tener al menos 8 caracteres, con letras y números."
    if nueva != repetida:
        return False, "Las contraseñas nuevas no coinciden."
    return True, ""


# TITULO MASCARA

def mascara(valor: str, visibles: int = 3) -> str:
    """Enmascara un dato sensible dejando visibles solo los últimos `visibles` caracteres (••••••K-5 -> p. ej. ••••••••-5)."""
    valor = str(valor or "")
    if not valor:
        return ""
    return "•" * max(0, len(valor) - visibles) + valor[-visibles:]


# TITULO LLENO

def _lleno(valor: Any) -> bool:
    """¿El valor cuenta como respondido? (no vacío; False o una lista vacía no cuentan)."""
    return valor not in (None, "", [], {})


# TITULO COMPLETITUD

def completitud(perfil: dict[str, Any]) -> tuple[int, list[str]]:
    """Porcentaje (0-100) de campos requeridos del perfil que ya están completos y la lista de los que faltan.

    Recibe el diccionario del perfil guardado; los campos requeridos están en datos.json (`requeridos_completitud`)."""
    faltan = [c for c in REQUERIDOS if not _lleno(perfil.get(c))]
    return round(100 * (len(REQUERIDOS) - len(faltan)) / len(REQUERIDOS)), faltan


# TITULO SECCION COMPLETA

def seccion_completa(id_seccion: str, perfil: dict[str, Any]) -> bool | None:
    """¿Están completos los campos requeridos de una sección? None si la sección no tiene campos requeridos."""
    requeridos = [c["id"] for s in SECCIONES if s["id"] == id_seccion for c in s["campos"] if c["id"] in REQUERIDOS]
    if not requeridos:
        return None
    return all(_lleno(perfil.get(c)) for c in requeridos)


# TITULO ESTADO VERIFICACION

def estado_verificacion(perfil: dict[str, Any]) -> tuple[str, str]:
    """Estado de la verificación de identidad como (clave, texto): "verificado", "pendiente" (perfil completo) o "incompleto"."""
    if perfil.get("verificacion") == "verificado":
        return "verificado", "Identidad verificada"
    if completitud(perfil)[0] == 100:
        return "pendiente", "Verificación pendiente"
    return "incompleto", "Perfil incompleto"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara validacion .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
