# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara entorno .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Carga del .env (configuracion.py o, si no está, python-dotenv) antes de leer cualquier variable de MT5.

Este módulo no define funciones: su importación tiene el efecto de cargar las
variables de entorno (MT5_PATH, MT5_LOGIN, etc.). Se importa primero desde el
`__init__` del paquete para que el resto de módulos ya encuentre el entorno listo."""
# Primero se intenta con configuracion.py, que carga el .env del proyecto al importarse.
try:
    import configuracion  # noqa: F401
except ImportError:
    # Respaldo: usar python-dotenv directamente si está instalado.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        # Sin ninguno de los dos, se continúa con las variables de entorno del sistema.
        pass


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara entorno .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
