# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara contrasenas .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""
contrasenas.py
--------------
Regla única de seguridad de las contraseñas de la plataforma (registro, recuperación y cambio desde el perfil) y datos para el medidor de fuerza
que muestran las pantallas.

Una contraseña es válida si cumple los cinco requisitos (8 o más caracteres, mayúscula, minúscula, número y símbolo) y no es una de las claves más
comunes, incluso disfrazada (por ejemplo «P@ssw0rd!» se reconoce como «password»).
"""
import re
from typing import Optional

# Texto corto que las pantallas muestran como ayuda junto al campo de contraseña.
TEXTO_AYUDA = "Mínimo 8 caracteres, con mayúscula, minúscula, número y símbolo"

# Aviso que se devuelve cuando falta algún requisito.
AVISO_REQUISITOS = "La contraseña debe tener al menos 8 caracteres, con mayúscula, minúscula, número y símbolo."
AVISO_COMUN = "Esa contraseña es demasiado común. Elige otra más difícil de adivinar."

# Requisitos: (descripción que se muestra, comprobación).
REQUISITOS = (
    ("8 o más caracteres", lambda c: len(c) >= 8),
    ("Una letra mayúscula", lambda c: any(letra.isupper() for letra in c)),
    ("Una letra minúscula", lambda c: any(letra.islower() for letra in c)),
    ("Un número", lambda c: any(letra.isdigit() for letra in c)),
    ("Un símbolo (por ejemplo ! ? # $ %)", lambda c: any(not letra.isalnum() and not letra.isspace() for letra in c)),
)

# Claves comunes, solo letras en minúscula: se comparan sin números ni símbolos y deshaciendo los reemplazos típicos (@ por a, 0 por o, etc.).
COMUNES = frozenset("""
password contrasena contrasenia clave claves qwerty qwertyui qwertyuiop asdf asdfg asdfgh asdfghjkl zxcv zxcvb zxcvbn zxcvbnm abc abcd abcde abcdef
abcdefg abcdefgh admin administrador administrator root welcome bienvenido bienvenida letmein iloveyou teamo tequiero hola holamundo holahola chile
chilito santiago colocolo universidad futbol football soccer monkey dragon master login usuario user test testing prueba trading trader bolsa
pinayjara pyj pyjfinance finance capital dinero secret secreto princess sunshine shadow superman batman michael jordan charlie buster hunter
mustang freedom whatever starwars pokemon google facebook instagram changeme default guest pass passw0rd p4ssword unodostres
""".split())

# Reemplazos con los que se disfrazan las claves comunes («p@ssw0rd»).
_DISFRAZ = str.maketrans({"@": "a", "4": "a", "3": "e", "1": "i", "!": "i", "0": "o", "$": "s", "5": "s", "7": "t"})


# TITULO ES COMUN

def es_comun(contrasena: str) -> bool:
    """True si la contraseña es una clave muy común, también cuando está disfrazada con números, símbolos o mayúsculas."""
    minuscula = (contrasena or "").lower()
    nucleo = minuscula.strip("0123456789!?#$%&*._-+= ")
    solo_letras = "".join(letra for letra in nucleo.translate(_DISFRAZ) if letra.isalpha())
    sin_numeros = "".join(letra for letra in minuscula if letra.isalpha())
    return solo_letras in COMUNES or sin_numeros in COMUNES or minuscula in COMUNES or len(set(minuscula)) == 1


# TITULO EVALUAR

def evaluar(contrasena: str) -> list:
    """Devuelve la lista [(descripción, cumple)] de los cinco requisitos, en el orden en que se muestran."""
    contrasena = contrasena or ""
    return [(descripcion, bool(prueba(contrasena))) for descripcion, prueba in REQUISITOS]


# TITULO BARRAS

def barras(contrasena: str) -> int:
    """Cuántas de las 4 barras del medidor de fuerza se llenan (0 a 4); una clave común no pasa de 1."""
    if not contrasena:
        return 0
    cumplidos = sum(1 for _, cumple in evaluar(contrasena) if cumple)
    llenas = {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 4}[cumplidos]
    return min(llenas, 1) if es_comun(contrasena) else llenas


# TITULO VALIDAR

def validar(contrasena: str) -> Optional[str]:
    """Devuelve el aviso para mostrar si la contraseña no es aceptable, o None si lo es."""
    contrasena = contrasena or ""
    if not all(cumple for _, cumple in evaluar(contrasena)):
        return AVISO_REQUISITOS
    if es_comun(contrasena):
        return AVISO_COMUN
    return None


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara contrasenas .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
