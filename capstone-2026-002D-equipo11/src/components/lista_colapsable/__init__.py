"""
components/lista_colapsable
---------------------------------------
Deja la lista (watchlist en Trading, posiciones en Cartera) en su columna de siempre,
con el historial del agente debajo, pero agrega una PESTAÑA para ocultarla/mostrarla.

El toggle NO reejecuta Python: un script intercepta el clic de la pestaña (antes de que
llegue a Streamlit) y alterna la clase `pj-wl-oculto` en <html>; el CSS colapsa a 0 las
columnas marcadas con `marca_columna()` (watchlist e historial) y sus hermanas (gráfico,
chat) se ensanchan solas. Al entrar o tras F5 la lista parte VISIBLE. La pestaña sigue a
la barra lateral cuando se expande/colapsa (clase `pj-sb-exp`).

Uso en vista_operativa: `inyectar_css_lista_colapsable()` (antes del gráfico),
`marca_columna()` dentro de la columna de la lista y de la del historial, y
`renderizar_toggle_lista()` una vez.

Archivos: panel.py (marca + pestaña + script), estilos.py + estilos.css (plantilla con
las medidas), datos.py (toma los anchos de la barra lateral), lista.js (toggle sin rerun).
"""
from components.lista_colapsable.panel import (inyectar_css_lista_colapsable, marca_columna,
                                                           renderizar_toggle_lista)

__all__ = ["inyectar_css_lista_colapsable", "marca_columna", "renderizar_toggle_lista"]
