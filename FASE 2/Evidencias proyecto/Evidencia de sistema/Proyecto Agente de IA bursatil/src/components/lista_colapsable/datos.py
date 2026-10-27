"""Medidas de la lista colapsable (watchlist / historial ocultables con una pestaña).

Los anchos de la barra lateral se importan para posicionar la pestaña pegada al
borde izquierdo del contenido, aunque la barra se expanda/colapse.
"""
from components.barra_lateral.barra import ANCHO_COLAPSADO, ANCHO_EXPANDIDO

TOP = 62             # alto de la barra superior
NAV_COL = ANCHO_COLAPSADO   # barra lateral colapsada (70)
NAV_EXP = ANCHO_EXPANDIDO   # barra lateral expandida (220)
