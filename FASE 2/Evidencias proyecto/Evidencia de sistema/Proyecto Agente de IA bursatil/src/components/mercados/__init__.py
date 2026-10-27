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
components/mercados
-------------------
Paquete de la página "Mercados" (barra lateral), con diseño de plataforma de bróker. Expone solo
`renderizar_panel_mercados`, que arma la página completa; el resto de módulos son piezas internas.

- Resumen del mercado: 5 referencias (S&P 500, Nasdaq, Oro, EUR/USD, Bitcoin)
  con precio y variación del día en vivo + tendencia de las últimas 24 h.
- Pestañas por categoría (con cantidad), buscador y orden.
- Tabla: instrumento, precio, cambio, cambio %, rango del día (barra),
  tendencia de 5 días (mini-gráfico) y estado del mercado (abierto/cerrado).
- Cada fila / tarjeta es CLICABLE -> ficha del instrumento (modal): precio en
  vivo, caja Vender/Comprar con spread, gráfico interactivo (Lightweight Charts)
  con periodos 1S/1M/3M/6M/1A, rendimiento, estadísticas clave y
  especificaciones del contrato.

Precios, cambios y Bid/Ask se pintan en vivo con el feed SSE (flujo_vivo.py);
sin servidor de datos, los fragmentos se refrescan cada pocos segundos.
La variación es la DEL DÍA (contra el cierre diario anterior), la misma base
que usan Favoritos, la lista de activos y el feed.

Los nombres cambian entre brókers (XM: US30Cash, GOLD, SpainCash, futuros
"COCOA-DEC26", acciones por nombre de empresa "Apple"...). `resolver()` (broker.py) prueba
los candidatos del catálogo, luego el sufijo Cash, el futuro vigente y, para
acciones, el ticker que MT5 trae en la descripción ("Apple Inc (AAPL.OQ)").

Archivos: panel.py (arma la página), secciones.py (pulso + tabla), ficha.py (modal), grafico.py,
piezas.py (HTML), broker.py (datos MT5), constantes.py + datos.json (catálogo), estilos.css y estatico/.
"""
# Fachada: reexporta la única función pública del paquete para que se importe como `mercados.renderizar_panel_mercados`
from components.mercados.panel import renderizar_panel_mercados

# Nombres públicos del paquete
__all__ = ["renderizar_panel_mercados"]


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
