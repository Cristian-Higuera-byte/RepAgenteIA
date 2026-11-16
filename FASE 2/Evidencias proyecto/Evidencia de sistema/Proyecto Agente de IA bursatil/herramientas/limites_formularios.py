# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara limites_formularios .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

"""Largos máximos de los campos de texto de los formularios (inicio de sesión, registro, recuperar contraseña, conectar la API).

Un campo sin tope deja escribir o pegar texto infinito: infla lo que viaja al servidor, lo que se guarda y el trabajo de cifrar contraseñas. Estos topes se aplican en dos
lugares: en el campo (`max_chars` de Streamlit, que corta lo que se escribe) y en el servidor (`excede`), porque el tope del campo se puede saltar enviando los datos a mano.
"""

# Correo: el estándar permite hasta 254, pero ningún correo real se acerca; 40 caracteres alcanzan para cualquier correo habitual y no dejan pegar textos enormes.
CORREO = 40
# Contraseña de la cuenta de la plataforma: 40 caracteres alcanzan de sobra para una contraseña o una frase, y no dejan cargar textos enormes al cifrarla.
CONTRASENA = 40
# Nombres y cada apellido; el nombre completo guardado en la cuenta es nombres + paterno + materno separados por espacios.
NOMBRES = 40
APELLIDO = 40
NOMBRE_COMPLETO = NOMBRES + APELLIDO + APELLIDO + 2
# Clave (API key) que entrega Capital.com y la contraseña que la persona definió al crearla en Capital.com (no es la de la plataforma; ese largo lo decide Capital.com).
API_KEY = 128
API_CONTRASENA = 128


# TITULO EXCEDE

def excede(*pares) -> bool:
    """True si algún valor supera su tope. Recibe pares `(valor, máximo)`; los valores vacíos o que no son texto se ignoran.

    Ejemplo: `excede((correo, CORREO), (contrasena, CONTRASENA))`."""
    for valor, maximo in pares:
        if isinstance(valor, str) and len(valor) > maximo:
            return True
    return False


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara limites_formularios .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
