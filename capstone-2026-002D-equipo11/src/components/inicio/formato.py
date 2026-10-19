# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara formato .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Pequeños formateadores de la vista Inicio: dinero, íconos Material y semáforo de nivel de margen.

Son funciones puras (sin efectos secundarios) usadas por cuenta.py, posiciones.py, historial.py y panel.py.
"""


def formatear_dinero(v, dec=2):
    """Formatea `v` como dinero en dólares con separador de miles y `dec` decimales (por defecto 2).

    Devuelve «—» si el valor no es convertible a número.
    """
    # Conversión protegida: valores nulos o no numéricos se muestran como guion.
    try:
        return f"${float(v):,.{dec}f}"
    except Exception:
        return "—"


def icono_material(nombre: str, color: str = "", size: int = 0) -> str:
    """HTML de un ícono de la fuente Material Symbols (clase `mi`) con nombre de glifo `nombre`.

    `color` (CSS) y `size` (px) son opcionales y se aplican como estilo en línea cuando se indican.
    """
    # Estilo en línea solo con las propiedades pedidas.
    estilo = (f"color:{color};" if color else "") + (f"font-size:{size}px;" if size else "")
    return f"<span class='mi' style='{estilo}'>{nombre}</span>"


def estado_margen(ml: float) -> tuple:
    """(texto, color) del semáforo del nivel de margen.

    Recibe el nivel de margen `ml` en porcentaje: 0 o vacío significa sin posiciones (gris), 300 o más
    saludable (verde), 150 o más atención (ámbar) y por debajo riesgo (rojo).
    """
    # Sin posiciones abiertas el nivel de margen es 0.
    if not ml:
        return "Sin posiciones", "#8b949e"
    if ml >= 300:
        return "Saludable", "#3fb950"
    if ml >= 150:
        return "Atención", "#d29922"
    return "Riesgo", "#f85149"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara formato .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
