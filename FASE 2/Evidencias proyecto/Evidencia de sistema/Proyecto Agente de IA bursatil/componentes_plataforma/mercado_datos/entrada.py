# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara entrada .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Entrada de un símbolo para la watchlist (nombre, categoría, precio y variación).

Consulta MT5 para resolver el nombre real del símbolo en el terminal conectado y componer el diccionario que
consumen la watchlist y las demás vistas.
"""
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from componentes_plataforma.mercado_datos.referencias import variacion
from herramientas import gestor_lista_activos as wl
from herramientas.puente_mt5 import MT5_LOCK, obtener_precio_actual, resolver_simbolo


# TITULO CONSTRUIR ENTRADA

def construir_entrada(simbolo: str) -> dict:
    """Arma la entrada de un símbolo para la watchlist (nombre, categoría, precio)
    usando el nombre EXACTO de MT5 (sin limpiar los '...').

    Recibe el símbolo tal como lo guarda la watchlist. Resuelve su nombre real en el terminal, lo selecciona
    en el Market Watch de MT5 (efecto secundario, bajo `MT5_LOCK`), lee su descripción y ruta para obtener
    nombre visible y categoría, toma el último precio (o el bid si no hay `last`) y calcula la variación del
    día. Devuelve un diccionario con las claves `nombre`, `mercado`, `precio` (float), `var` (texto) y `sube`
    (bool). Si MT5 falla, usa valores por defecto en vez de lanzar excepción.
    """
    # Resolver el nombre real y pedirle a MT5 la información del símbolo (protegido con el candado de MT5)
    try:
        simulado_real = resolver_simbolo(simbolo)  # nombre real en ESTE terminal (con/sin '...')
        with MT5_LOCK:
            mt5.symbol_select(simulado_real, True)
            info = mt5.symbol_info(simulado_real)
    except Exception:
        info = None
    # Nombre amigable: descripción del bróker si existe; si no, el nombre visible del gestor de listas
    nombre = (info.description if info and getattr(info, "description", "") else wl.nombre_visible(simbolo))
    # Categoría deducida de la ruta del símbolo en MT5 (p. ej. Forex, Índices, Acciones)
    mercado = wl.categoria_simbolo(getattr(info, "path", "") if info else "", simbolo)
    # Precio actual: último trade si es positivo; si no, el bid. Cero si no hay tick
    precio = 0.0
    try:
        tick = obtener_precio_actual(simbolo)
        if "error" not in tick:
            precio = tick.get("last", 0) if tick.get("last", 0) > 0 else tick.get("bid", 0)
    except Exception:
        pass
    # Variación del día; 2 decimales para precios altos y 5 para precios bajos (como el forex)
    var = variacion(simbolo, float(precio or 0.0), 2 if precio > 100 else 5)
    # Si no hay referencia de cierre previo se muestra una variación neutra
    return {
        "nombre": nombre,
        "mercado": mercado,
        "precio": float(precio or 0.0),
        "var": var[0] if var else "+0.00 (0.00%)",
        "sube": var[1] if var else True,
    }


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara entrada .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
