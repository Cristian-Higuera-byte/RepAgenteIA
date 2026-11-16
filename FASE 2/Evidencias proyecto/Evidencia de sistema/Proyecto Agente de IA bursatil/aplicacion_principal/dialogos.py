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


# TITULO RENDERIZAR DIALOGOS

def renderizar_dialogos() -> None:
    """
    Dibuja, uno tras otro, los cuatro diálogos que pueden abrirse sobre la página.

    Cada diálogo se abre solo cuando su bandera está activa en la sesión: el buscador de símbolos,
    la confirmación de cierre de una posición (Cartera) y los términos y condiciones de One-Click
    Trading (la primera vez que se activa) y los de la autorización de una vigilancia automática del agente. Los componentes se importan en el momento de usarse.
    """
    # Diálogo del buscador (se abre con la bandera `mostrar_buscador`). Se dibuja aquí, en el
    # script principal, para que no choque con los fragmentos en vivo.
    from componentes_plataforma.buscador import renderizar_buscador
    renderizar_buscador()

    # Ventana de confirmación de cierre de posición (Cartera). Igual que el buscador, se dibuja
    # fuera de los fragmentos en vivo.
    from componentes_plataforma.cartera_panel import renderizar_modal_cerrar
    renderizar_modal_cerrar()

    # Términos y condiciones de One-Click Trading (la primera vez que se activa).
    from componentes_plataforma.operacion_un_clic import renderizar_modal_terminos
    renderizar_modal_terminos()

    # Términos y condiciones de la vigilancia automática del agente (al pulsar «Autorizar vigilancia»).
    from componentes_plataforma.vigilancia_terminos import renderizar_modal_terminos_vigilancia
    renderizar_modal_terminos_vigilancia()


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
