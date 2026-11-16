# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara secciones .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Secciones HTML de la portada pública: cada función devuelve el HTML de un bloque (barra, héroe, beneficios, gráficos, agente, mercados, noticias, herramientas, pasos, planes, preguntas, cierre y pie).

El texto sale de contenido.json (se edita sin tocar código), las imágenes reales de la plataforma de la carpeta imagenes/, las cotizaciones y noticias de datos.py y los planes de configuracion.PLANES_IA. Los
enlaces de los botones llevan `?acceso=entrar` o `?acceso=crear`, que `componentes_plataforma/acceso/pantalla.py` interpreta para mostrar el formulario que corresponde. Los íconos son Material Symbols
(la fuente que ya trae Streamlit).
"""
from __future__ import annotations

import base64
import random
import time
from functools import lru_cache
from html import escape
from pathlib import Path

from componentes_plataforma import vitrina_planes
from componentes_plataforma._estaticos import datos_json
from componentes_plataforma.legal import enlaces_html
from componentes_plataforma.portada import datos

# Contenido de la portada (textos, listas y preguntas frecuentes).
C = datos_json(Path(__file__).parent / "contenido.json")
# Carpeta con las capturas reales de la plataforma (para cambiar una imagen basta con reemplazar el archivo, con el mismo nombre).
IMAGENES = Path(__file__).parent / "imagenes"
# Enlaces de acceso: el parámetro de la URL decide qué formulario se muestra.
ENTRAR = "?acceso=entrar"
CREAR = "?acceso=crear"


# TITULO ICONO

def _ico(nombre: str, clase: str = "") -> str:
    """HTML de un ícono Material Symbols por su nombre (por ejemplo «smart_toy»); `clase` suma clases CSS."""
    return f"<span class='pj-p-ico {clase}'>{escape(nombre)}</span>"


# TITULO IMAGEN EN BASE 64

@lru_cache(maxsize=None)
def _uri(nombre: str) -> str:
    """Imagen de la carpeta imagenes/ como data URI (el HTML de Streamlit no sirve archivos locales). Se lee una sola vez por proceso. Devuelve cadena vacía si el archivo no existe."""
    ruta = IMAGENES / f"{nombre}.webp"
    if not ruta.exists():
        return ""
    return "data:image/webp;base64," + base64.b64encode(ruta.read_bytes()).decode()


# TITULO CAPTURA

def _captura(nombre: str, alt: str, clase: str = "") -> str:
    """Captura real de la plataforma dentro de un marco de ventana de navegador. `nombre` es el archivo (sin extensión), `alt` su descripción y `clase` suma clases CSS al marco."""
    return (f"<figure class='pj-p-captura {clase}'><div class='pj-p-captura-barra'><span class='pj-p-pt' style='background:#ff5f57'></span><span class='pj-p-pt' style='background:#febc2e'></span>"
            f"<span class='pj-p-pt' style='background:#28c840'></span></div><img src='{_uri(nombre)}' alt='{escape(alt)}' loading='lazy'></figure>")


# TITULO MINIGRAFICO

def _spark(simbolo: str, sube: bool, serie: list | None = None, ancho: int = 96, alto: int = 32) -> str:
    """Minigráfico de una fila de cotizaciones como imagen data URI. Con `serie` (cierres reales) dibuja esa serie; sin ella, una línea ILUSTRATIVA (semilla fija por símbolo, que termina arriba si el activo sube y abajo si baja), solo para los datos de ejemplo."""
    if serie:
        puntos = list(serie)
    else:
        azar = random.Random(simbolo)
        valor, puntos = 50.0, []
        for i in range(18):
            valor += azar.uniform(-4, 4) + (1.1 if sube else -1.1)
            puntos.append(valor)
    minimo, maximo = min(puntos), max(puntos)
    rango = (maximo - minimo) or 1
    xy = " ".join(f"{i * ancho / (len(puntos) - 1):.1f},{alto - 3 - (v - minimo) / rango * (alto - 6):.1f}" for i, v in enumerate(puntos))
    color = "#2ea043" if sube else "#f85149"
    svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {ancho} {alto}'><polyline points='{xy}' fill='none' stroke='{color}' stroke-width='2' stroke-linejoin='round' stroke-linecap='round'/></svg>"
    return f"<img class='pj-p-spark' alt='' src='data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}'>"


# TITULO NUMERO EN ESPAÑOL

def _num(valor: float, decimales: int) -> str:
    """Número con formato español: punto para los miles y coma para los decimales (por ejemplo 4.023,54)."""
    return f"{valor:,.{decimales}f}".replace(",", "@").replace(".", ",").replace("@", ".")


# TITULO BARRA

def barra() -> str:
    """Barra superior fija: logo, enlaces a las secciones de la página y botones «Iniciar sesión» y «Regístrate»."""
    enlaces = "".join(f"<a href='#{escape(ancla)}'>{escape(texto)}</a>" for texto, ancla in C["nav"])
    return (
        "<header class='pj-p-barra'><div class='pj-p-cont pj-p-barra-fila'>"
        "<a class='pj-p-logo' href='#inicio'><b>P&amp;J</b><span>Finance</span></a>"
        f"<nav class='pj-p-nav'>{enlaces}</nav>"
        f"<div class='pj-p-acciones'><a class='pj-p-btn pj-p-btn-suave' href='{ENTRAR}' target='_self'>Iniciar sesión</a>"
        f"<a class='pj-p-btn pj-p-btn-claro' href='{CREAR}' target='_self'>Regístrate</a></div>"
        "</div></header>"
    )


# TITULO HEROE

def heroe() -> str:
    """Primer bloque: etiqueta, titular, subtítulo, botones de acción, puntos de confianza y la captura real de la plataforma (en celular, la del gráfico, que se lee mejor)."""
    h = C["hero"]
    puntos = "".join(f"<li>{_ico('check_circle')}{escape(p)}</li>" for p in h["puntos"])
    return (
        "<section class='pj-p-heroe' id='inicio'><div class='pj-p-cont'>"
        "<div class='pj-p-heroe-texto'>"
        f"<span class='pj-p-etiqueta'>{escape(h['etiqueta'])}</span>"
        f"<h1>{escape(h['titulo'])}</h1><p class='pj-p-sub'>{escape(h['subtitulo'])}</p>"
        f"<div class='pj-p-botones pj-p-botones-centro'><a class='pj-p-btn pj-p-btn-marca pj-p-btn-grande' href='{CREAR}' target='_self'>{escape(h['cta_principal'])}<span class='pj-p-flecha'>→</span></a>"
        f"<a class='pj-p-btn pj-p-btn-borde pj-p-btn-grande' href='{ENTRAR}' target='_self'>{escape(h['cta_secundario'])}</a></div>"
        f"<ul class='pj-p-puntos pj-p-puntos-centro'>{puntos}</ul></div>"
        f"<div class='pj-p-heroe-vista'>{_captura('plataforma', 'Plataforma: lista de activos, gráfico y chat del agente de IA', 'pj-p-solo-grande')}"
        f"{_captura('grafico', 'Gráfico de EURUSD con indicadores y herramientas de dibujo', 'pj-p-solo-chico')}</div>"
        "</div></section>"
    )


# TITULO PORQUE

def porque() -> str:
    """Tres tarjetas con las razones para elegir la plataforma (al estilo «¿Por qué elegir…?» de los brókeres)."""
    p = C["porque"]
    tarjetas = "".join(f"<article class='pj-p-tarjeta'><div class='pj-p-tarjeta-tit'>{_ico(i)}<h3>{escape(t)}</h3></div><p>{escape(d)}</p></article>" for i, t, d in p["tarjetas"])
    return (f"<section class='pj-p-seccion' id='porque'><div class='pj-p-cont'><h2 class='pj-p-centro'>{escape(p['titulo'])}</h2>"
            f"<p class='pj-p-sub pj-p-centro'>{escape(p['subtitulo'])}</p><div class='pj-p-rejilla3'>{tarjetas}</div></div></section>")


# TITULO GRAFICOS

def graficos() -> str:
    """Bloque de los gráficos: captura real del gráfico a la izquierda y la explicación con cuatro puntos a la derecha."""
    g = C["graficos"]
    puntos = "".join(f"<li>{_ico('bolt')}<div><b>{escape(t)}</b><span>{escape(d)}</span></div></li>" for t, d in g["puntos"])
    return (f"<section class='pj-p-seccion pj-p-fondo' id='graficos'><div class='pj-p-cont pj-p-dos pj-p-dos-inversa'>"
            f"<div class='pj-p-dos-vista'>{_captura('grafico', 'Gráfico de EURUSD con indicadores, herramientas de dibujo, Backtest y Replay')}</div>"
            f"<div class='pj-p-dos-texto'><span class='pj-p-etiqueta'>{escape(g['etiqueta'])}</span><h2>{escape(g['titulo'])}</h2><p class='pj-p-sub'>{escape(g['texto'])}</p>"
            f"<ul class='pj-p-lista'>{puntos}</ul><a class='pj-p-btn pj-p-btn-marca' href='{CREAR}' target='_self'>{escape(C['hero']['cta_principal'])}</a></div></div></section>")


# TITULO AGENTE

def agente() -> str:
    """Bloque del agente de IA: explicación con cuatro puntos a la izquierda y una conversación de ejemplo a la derecha."""
    a = C["agente"]
    puntos = "".join(f"<li>{_ico('bolt')}<div><b>{escape(t)}</b><span>{escape(d)}</span></div></li>" for t, d in a["puntos"])
    chat = (
        "<div class='pj-p-chat' aria-hidden='true'><div class='pj-p-chat-cab'>" + _ico("smart_toy") + "<b>Agente IA Analítico</b><em>Vista ilustrativa</em></div>"
        "<div class='pj-p-burbuja pj-p-usuario'>¿Cómo está el oro hoy? Muéstrame un gráfico.</div>"
        "<div class='pj-p-burbuja pj-p-agente'>El oro cotiza cerca de su máximo semanal, con volumen creciente. Te dejo el gráfico en H4 con soportes y resistencias marcados.</div>"
        "<div class='pj-p-burbuja pj-p-usuario'>Vigila el soporte y avísame si lo rompe.</div>"
        "<div class='pj-p-burbuja pj-p-agente'>Listo. Activé una vigilancia sobre el soporte: te propondré una orden si aparece la señal.</div>"
        "<div class='pj-p-chat-caja'>Escribe tu consulta o pide un gráfico en imagen...<i>" + _ico("arrow_upward") + "</i></div></div>"
    )
    return (f"<section class='pj-p-seccion pj-p-fondo' id='agente'><div class='pj-p-cont pj-p-dos'>"
            f"<div class='pj-p-dos-texto'><span class='pj-p-etiqueta'>{escape(a['etiqueta'])}</span><h2>{escape(a['titulo'])}</h2><p class='pj-p-sub'>{escape(a['texto'])}</p>"
            f"<ul class='pj-p-lista'>{puntos}</ul><a class='pj-p-btn pj-p-btn-marca' href='{CREAR}' target='_self'>{escape(C['hero']['cta_principal'])}</a></div>"
            f"<div class='pj-p-dos-vista'>{chat}</div></div>"
            f"<div class='pj-p-cont pj-p-captura-ancha'>{_captura('agente', 'Panel del agente con perfil, cuota de uso, límites y órdenes propuestas')}<p class='pj-p-nota pj-p-centro'>{escape(a['captura'])}</p></div></section>")


# TITULO ACTIVOS

def activos() -> str:
    """Sección «Mercados»: tabla de activos con precio, variación (verde si sube, rojo si baja) y minigráfico. Los datos salen de `datos.activos()`: en vivo si hay lectura reciente de Capital.com (con la hora de la
    última actualización y minigráficos reales) y, si no, de ejemplo (y lo dice debajo)."""
    a = C["activos"]
    lista = datos.activos()
    en_vivo = not any(x.get("ejemplo") for x in lista)
    filas = ""
    for x in lista:
        sube = x["var"] >= 0
        signo = "+" if sube else ""
        grafico = _spark(x["simbolo"], sube, x.get("serie")) if (x.get("serie") or not en_vivo) else "<span class='pj-p-spark pj-p-spark-vacio'></span>"
        filas += (f"<div class='pj-p-fila'><div class='pj-p-fila-nom'><b>{escape(x['simbolo'])}</b><span>{escape(x['nombre'])}</span></div>{grafico}"
                  f"<div class='pj-p-fila-precio'>{_num(x['precio'], x['decimales'])}</div>"
                  f"<div class='pj-p-fila-var {'pj-p-sube' if sube else 'pj-p-baja'}'>{signo}{_num(x['var'], 2)}%</div></div>")
    if en_vivo:
        hora = time.strftime("%H:%M:%S", time.localtime(max(x["ts"] for x in lista)))
        nota = f"<p class='pj-p-vivo pj-p-centro'><span class='pj-p-punto-vivo'></span>{escape(a['en_vivo'])} · actualizado a las {hora}</p>"
    else:
        nota = f"<p class='pj-p-nota pj-p-centro'>{escape(a['nota_ejemplo'])}</p>"
    return (f"<section class='pj-p-seccion' id='activos'><div class='pj-p-cont pj-p-angosto2'><h2 class='pj-p-centro'>{escape(a['titulo'])}</h2>"
            f"<p class='pj-p-sub pj-p-centro'>{escape(a['subtitulo'])}</p><div class='pj-p-tabla'>{filas}</div>{nota}"
            f"<div class='pj-p-centro pj-p-espacio'><a class='pj-p-btn pj-p-btn-borde pj-p-btn-grande' href='{CREAR}' target='_self'>{escape(a['boton'])}</a></div></div></section>")


# TITULO NOTICIAS

def noticias() -> str:
    """Sección «Noticias»: una nota destacada y hasta cinco más, con medio y hora, que abren el sitio del medio en otra pestaña. Si todavía no hay titulares cargados, muestra un aviso."""
    n = C["noticias"]
    lista = datos.noticias(6)
    if lista:
        def _nota(x: dict, grande: bool = False) -> str:
            resumen = x.get("desc", "")
            resumen = (resumen[:170].rsplit(" ", 1)[0] + "…") if len(resumen) > 170 else resumen
            return (f"<a class='pj-p-nota-card{' pj-p-nota-grande' if grande else ''}' href='{escape(x['link'], quote=True)}' target='_blank' rel='noopener noreferrer nofollow'>"
                    f"<span class='pj-p-nota-meta'><b>{escape(x.get('fuente', ''))}</b><i>{escape(x.get('fecha', ''))}</i></span>"
                    f"<h3>{escape(x['title'])}</h3>{f'<p>{escape(resumen)}</p>' if grande and resumen else ''}</a>")
        cuerpo = f"<div class='pj-p-notas'>{_nota(lista[0], True)}<div class='pj-p-notas-lista'>{''.join(_nota(x) for x in lista[1:])}</div></div>"
        pie = f"<p class='pj-p-nota pj-p-centro'>{escape(n['fuente'])}</p>"
    else:
        cuerpo = f"<div class='pj-p-vacio'>{_ico('newspaper')}<p>{escape(n['espera'])}</p></div>"
        pie = ""
    return (f"<section class='pj-p-seccion pj-p-fondo' id='noticias'><div class='pj-p-cont'><h2 class='pj-p-centro'>{escape(n['titulo'])}</h2>"
            f"<p class='pj-p-sub pj-p-centro'>{escape(n['subtitulo'])}</p>{cuerpo}{pie}"
            f"<div class='pj-p-centro pj-p-espacio'><a class='pj-p-btn pj-p-btn-borde pj-p-btn-grande' href='{CREAR}' target='_self'>{escape(n['boton'])}</a></div></div></section>")


# TITULO HERRAMIENTAS

def herramientas() -> str:
    """Rejilla de seis herramientas de la plataforma (gráficos, mercados, noticias, cartera, diario y copy trading)."""
    h = C["herramientas"]
    items = "".join(f"<article class='pj-p-herr'>{_ico(i, 'pj-p-herr-ico')}<h3>{escape(t)}</h3><p>{escape(d)}</p></article>" for i, t, d in h["items"])
    return (f"<section class='pj-p-seccion' id='herramientas'><div class='pj-p-cont'><h2 class='pj-p-centro'>{escape(h['titulo'])}</h2>"
            f"<p class='pj-p-sub pj-p-centro'>{escape(h['subtitulo'])}</p><div class='pj-p-rejilla3'>{items}</div></div></section>")


# TITULO PASOS

def pasos() -> str:
    """Tres pasos numerados para empezar (crear cuenta, conectar la cuenta demo y operar con el agente)."""
    p = C["pasos"]
    items = "".join(f"<article class='pj-p-paso'><span class='pj-p-num'>{escape(n)}</span><h3>{escape(t)}</h3><p>{escape(d)}</p></article>" for n, t, d in p["items"])
    return (f"<section class='pj-p-seccion pj-p-fondo' id='empezar'><div class='pj-p-cont'><h2 class='pj-p-centro'>{escape(p['titulo'])}</h2>"
            f"<div class='pj-p-rejilla3'>{items}</div><div class='pj-p-centro pj-p-espacio'><a class='pj-p-btn pj-p-btn-marca pj-p-btn-grande' href='{CREAR}' target='_self'>{escape(C['hero']['cta_principal'])}<span class='pj-p-flecha'>→</span></a></div></div></section>")


# TITULO PLANES

def planes() -> str:
    """Sección de planes de la portada: las tarjetas de la vitrina (`componentes_plataforma/vitrina_planes/`) en cuatro columnas, con el detalle de cada plan,
    lo que incluyen todos y los avisos de confianza. El título y el subtítulo salen de contenido.json."""
    p = C["planes"]
    return (vitrina_planes.estilos()
            + f"<section class='pj-p-seccion' id='planes'><div class='pj-p-cont'><h2 class='pj-p-centro'>{escape(p['titulo'])}</h2>"
              f"<p class='pj-p-sub pj-p-centro'>{escape(p['subtitulo'])}</p>"
              f"<div class='vp'>{vitrina_planes.html_rejilla(cuatro=True)}{vitrina_planes.html_comun()}</div></div></section>")


# TITULO PREGUNTAS

def preguntas() -> str:
    """Preguntas frecuentes como bloques desplegables (etiqueta details, sin JavaScript)."""
    f = C["faq"]
    items = "".join(f"<details class='pj-p-pregunta'><summary>{escape(q)}{_ico('expand_more')}</summary><p>{escape(r)}</p></details>" for q, r in f["items"])
    return (f"<section class='pj-p-seccion pj-p-fondo' id='faq'><div class='pj-p-cont pj-p-angosto'><h2 class='pj-p-centro'>{escape(f['titulo'])}</h2>{items}</div></section>")


# TITULO CIERRE

def cierre() -> str:
    """Llamado final a registrarse, con un fondo de degradado de la marca."""
    c = C["cta_final"]
    return (f"<section class='pj-p-cierre'><div class='pj-p-cont pj-p-centro'><h2>{escape(c['titulo'])}</h2><p class='pj-p-sub'>{escape(c['texto'])}</p>"
            f"<div class='pj-p-botones pj-p-botones-centro'><a class='pj-p-btn pj-p-btn-claro pj-p-btn-grande' href='{CREAR}' target='_self'>{escape(c['boton'])}</a>"
            f"<a class='pj-p-btn pj-p-btn-borde pj-p-btn-grande' href='{ENTRAR}' target='_self'>{escape(C['hero']['cta_secundario'])}</a></div></div></section>")


# TITULO PIE

def pie() -> str:
    """Pie de página: aviso de riesgo, enlaces de acceso y créditos de la empresa."""
    return (f"<footer class='pj-p-pie'><div class='pj-p-cont'><p class='pj-p-riesgo'>{escape(C['riesgo'])}</p>"
            f"<p style='margin:-14px 0 22px; font-size:13px; color:#6b7686;'>{enlaces_html()}</p>"
            f"<div class='pj-p-pie-fila'><a class='pj-p-logo' href='#inicio'><b>P&amp;J</b><span>Finance</span></a>"
            f"<span>Sitio creado, programado y diseñado por <a href='https://www.pinayjara.cl' target='_blank' rel='noopener'>Piña y Jara Transportes y Servicios Ltda.</a></span></div></div></footer>")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara secciones .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
