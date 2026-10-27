# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara dialogos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Diálogos de la página que deben dibujarse en el script principal.

Se dibujan al final de la página, fuera de los fragmentos en vivo, para que no choquen con sus
reejecuciones automáticas.
"""


def renderizar_dialogos() -> None:
    """
    Dibuja, uno tras otro, los tres diálogos que pueden abrirse sobre la página.

    Cada diálogo se abre solo cuando su bandera está activa en la sesión: el buscador de símbolos,
    la confirmación de cierre de una posición (Cartera) y los términos y condiciones de One-Click
    Trading (la primera vez que se activa). Los componentes se importan en el momento de usarse.
    """
    # Diálogo del buscador (se abre con la bandera `mostrar_buscador`). Se dibuja aquí, en el
    # script principal, para que no choque con los fragmentos en vivo.
    from components.buscador import renderizar_buscador
    renderizar_buscador()

    # Ventana de confirmación de cierre de posición (Cartera). Igual que el buscador, se dibuja
    # fuera de los fragmentos en vivo.
    from components.cartera_panel import renderizar_modal_cerrar
    renderizar_modal_cerrar()

    # Términos y condiciones de One-Click Trading (la primera vez que se activa).
    from components.un_clic import renderizar_modal_terminos
    renderizar_modal_terminos()


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara dialogos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
