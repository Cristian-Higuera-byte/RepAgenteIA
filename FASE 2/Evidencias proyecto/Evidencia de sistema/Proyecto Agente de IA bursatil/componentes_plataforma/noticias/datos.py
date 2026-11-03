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

"""Fuentes RSS y parámetros del panel de noticias (viven en fuentes.json).

Separa la configuración (fuentes y tamaños de paginación) del código que lee los feeds, de modo que se pueda
cambiar sin tocar la lógica. Cada fuente es un diccionario con `nombre`, `idioma` (ES o EN), `url`, `condicional`
(si el servidor acepta peticiones condicionales ETag / Last-Modified, lo que permite revisarla cada pocos segundos casi
sin costo), `extraer` (si conviene intentar leer el texto del artículo cuando el RSS solo trae un resumen) y `lectura`
(si sus artículos pueden leerse dentro de la plataforma). Una noticia llega a la sección principal solo si su fuente tiene
`lectura` y además se comprobó que entrega texto (viene en el RSS o se pudo extraer de su página); todas las demás van al
panel lateral «Otras fuentes», que solo muestra imagen, titular y un enlace al sitio.
"""
from pathlib import Path

from componentes_plataforma._estaticos import datos_json

# Contenido completo de fuentes.json
_D = datos_json(Path(__file__).parent / "fuentes.json")

# Fuentes que alimentan la noticia principal y el carrusel
FUENTES = list(_D["fuentes"])
FUENTES_MAS = list(_D["fuentes_mas"])      # fuentes adicionales para el apartado "Más noticias"
# Imagen de respaldo para las noticias que no traen foto
PLACEHOLDER = _D["placeholder"]
# Noticias por página del carrusel (también las columnas que se dibujan)
POR_PAGINA = _D["por_pagina"]
# Máximo de noticias del carrusel (sin contar la principal)
MAX_CARRUSEL = _D["max_carrusel"]
# Cada cuántos segundos se revisa una fuente que acepta peticiones condicionales, y cada cuántos una que no
INTERVALO_CONDICIONAL = _D["intervalo_condicional"]
INTERVALO_NORMAL = _D["intervalo_normal"]
# Máximo de noticias que se toman de cada fuente (para que una sola no llene la lista)
MAX_POR_FUENTE = _D["max_por_fuente"]
# De las fuentes que necesitan leer la página del artículo: cuántas noticias recientes se comprueban en cada una (solo
# llegan a la sección principal las que de verdad entregan texto) y cuántas noticias de cada fuente muestra el panel lateral.
MAX_VERIFICAR = _D["max_verificar_por_fuente"]
MAX_EXTERNAS = _D["max_externas_por_fuente"]

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
