# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
componentes_plataforma/iconografia
----------------------
Íconos de activos con el estilo de las plataformas de trading (tipo XM), en UN
solo lugar para todo el dashboard (Lista de activos, Favoritos, Cartera,
Cotizaciones).

Reglas según el tipo de activo:
  - Divisas (EURUSD, USDJPY…): dos banderas REDONDAS superpuestas
    (moneda base adelante a la izquierda, moneda cotizada atrás a la derecha).
  - Cripto (BTCUSD, ETHUSD…): logo de la cripto + bandera de la moneda cotizada.
  - Índices (US30Cash, JP225Cash…): bandera redonda del país + etiqueta abajo.
  - Materias primas (GOLD, SILVER, OILCash…): ícono propio (SVG) en círculo de color.
  - Acciones (NVDA.OQ…): logo de la empresa sobre un círculo con sus iniciales
    (si el logo no existe, quedan visibles las iniciales).
  - Cualquier otro: iniciales en un círculo de color estable.

Fuentes (uso libre): banderas redondas "circle-flags" (HatScripts, MIT) y logos
de cripto "cryptocurrency-icons" (CC0), ambas por CDN jsDelivr. Los íconos de
materias primas son SVG propios. NO se usan archivos de XM (son su propiedad).

El HTML usa solo estilos en línea e <img> (st.html sanea el SVG en línea, por eso
los SVG propios van como imagen data-URI).

Estructura del paquete (este `__init__` es una fachada que solo reexporta `icono_activo`, para que el
resto del dashboard importe desde `componentes_plataforma.iconografia`; el módulo
`componentes_plataforma/iconografia/` lo reexpone a su vez con el nombre histórico):
  icono.py     lógica de decisión por tipo de activo (`icono_activo`, `nucleo`)
  piezas.py    fragmentos HTML (cajas, imágenes circulares, pares de banderas, índices, iniciales, logos)
  datos.py     tablas leídas de `datos/*.json` y generador de SVG data-URI
  logos.py     conversión RIC -> ticker de logo y comprobación con caché de que la imagen existe
  info_mt5.py  carpeta y código bursátil de un símbolo según MetaTrader 5
"""
# Función principal: devuelve el HTML del ícono de un activo.
from componentes_plataforma.iconografia.icono import icono_activo

# API pública del paquete.
__all__ = ["icono_activo"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
