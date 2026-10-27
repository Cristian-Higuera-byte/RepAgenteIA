# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara atributos .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Atributos data-pj-* que los componentes ponen en sus etiquetas para que el feed pinte los números."""


def atributos(simbolo: str, campo: str = "px", **extra) -> str:
    """Atributos data-pj-* listos para meter en una etiqueta HTML.

    Recibe el `simbolo` que se pide al servidor, el `campo` a pintar (px, bid, ask, side, var, ch, pct,
    spr; por defecto "px") y atributos extra como argumentos con nombre (cada `k=v` se convierte en
    `data-pj-k="v"`). Devuelve una cadena como `data-pj-s="EURUSD" data-pj-f="px"`. No tiene efectos
    secundarios; el script de js/ lee estos atributos en el navegador.
    """
    # Atributos obligatorios: símbolo y campo.
    partes = [f'data-pj-s="{simbolo}"', f'data-pj-f="{campo}"']
    # Atributos opcionales (decimales, prefijo, colores, etc.) con el prefijo data-pj-.
    for k, v in extra.items():
        partes.append(f'data-pj-{k}="{v}"')
    # Se unen con espacios para insertarlos directamente dentro de la etiqueta.
    return " ".join(partes)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara atributos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
