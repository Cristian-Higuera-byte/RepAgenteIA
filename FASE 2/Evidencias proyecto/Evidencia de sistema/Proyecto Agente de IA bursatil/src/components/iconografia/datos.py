# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara datos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Datos de los íconos (monedas, criptos, índices, bolsas, materias primas…). Viven en `datos/*.json`;
aquí se leen una vez y quedan listos con el mismo formato que usaba el código.

Se ejecuta al importar: lee los JSON (con la caché de `_estaticos.datos_json`) y construye las constantes
del módulo. También expone `svg_circulo`, que fabrica los íconos SVG propios como imágenes data-URI.
"""
import base64
from pathlib import Path

# Lector de JSON con caché de la carpeta de estáticos.
from components._estaticos import datos_json

# Carpeta con los archivos JSON de datos.
_DIR = Path(__file__).parent / "datos"


def _json(nombre: str):
    """Lee y devuelve el contenido del archivo JSON `nombre` ubicado en la carpeta `datos/` del paquete."""
    return datos_json(_DIR / nombre)


def svg_circulo(fondo: str, figura: str) -> str:
    """Círculo de color con una figura blanca, como imagen data-URI.

    Recibe el color de `fondo` y el fragmento SVG de la `figura` (en un lienzo de 32x32). Devuelve una
    cadena `data:image/svg+xml;base64,...` apta para el atributo `src` de un `<img>`; se usa porque
    `st.html` sanea los SVG en línea.
    """
    # Documento SVG completo: círculo de fondo + figura.
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
        f"<circle cx='16' cy='16' r='16' fill='{fondo}'/>{figura}</svg>"
    )
    # Se codifica en base64 para incrustarlo como data-URI.
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


# Plantillas de URL de las fuentes externas (banderas, logos de cripto y de acciones).
_URLS = _json("urls.json")
FLAG = _URLS["bandera"]                    # banderas redondas (circle-flags)
CRIPTO_URL = _URLS["cripto"]               # logos de cripto (cryptocurrency-icons)
LOGO_ACCION = _URLS["logo_accion"]         # logos de acciones/ETF

MONEDA_PAIS = _json("moneda_pais.json")    # moneda -> código de bandera
CRIPTOS = _json("criptos.json")            # cripto -> archivo del logo
INDICES = {k: tuple(v) for k, v in _json("indices.json").items()}   # núcleo -> (bandera, etiqueta)
PALETA = _json("paleta.json")              # colores estables para las iniciales
RIC_A_TICKER = _json("ric_a_ticker.json")  # excepciones RIC de Reuters -> ticker del logo

# Reglas por bolsa para convertir códigos Reuters en tickers de logos.
_BOLSAS = _json("bolsas.json")
BOLSA_SUFIJO = _BOLSAS["sufijo"]                      # bolsa Reuters -> sufijo de la fuente de logos
BOLSAS_CLASE = set(_BOLSAS["clase_minuscula"])        # nórdicas: clase de acción en minúscula
BOLSAS_MENOS_UNA = set(_BOLSAS["menos_una_letra"])    # Viena/Helsinki: el RIC agrega 1 letra

# Figuras SVG reutilizables y los íconos finales de materias primas y genéricos (data-URI por clave).
_FIGURAS = _json("figuras.json")
MATERIAS = {k: svg_circulo(c, _FIGURAS[f]) for k, (c, f) in _json("materias.json").items()}
GENERICO = {k: svg_circulo(c, _FIGURAS[f]) for k, (c, f) in _json("genericos.json").items()}


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara datos .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
