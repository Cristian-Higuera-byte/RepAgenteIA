# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara vitrina .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Vitrina de planes: los cuatro planes con su precio y el detalle de lo que incluye cada uno, para las pantallas de inicio de sesión y de registro y para la vista Planes.

NOMBRE DEL ARCHIVO: componentes_plataforma/vitrina_planes/vitrina.py

Todo sale de `configuracion.PLANES_IA` (nombre, precio y preguntas por semana), de `herramientas/plan_funciones.json` (valores de cada función por plan, vía
`permisos_plan.valor`) y de `componentes_plataforma/planes/planes.json` (el lema de cada plan), así que la vitrina nunca se contradice con el cuadro comparativo.
Solo se anuncian funciones que ya existen: las que el catálogo marca como «definido» (todavía sin programar) no aparecen.

Dos usos: (1) la vitrina completa con enlaces (`html_vitrina`), debajo de los formularios de acceso, con botones que llevan a `?acceso=crear&plan=<plan>`; (2) las piezas
sueltas (`html_cabecera` y `html_lista`) con las que la vista Planes arma cada tarjeta alrededor de sus botones reales. Los planes de pago se contratarán con Flow
(muy pronto) y la vitrina lo dice. Los estilos están en `estilos.css` (prefijo `vp-`; las tarjetas de la vista Planes son contenedores con clave `vpc_<plan>`).
"""
from html import escape
from pathlib import Path

import configuracion
from componentes_plataforma import _estaticos
from herramientas import permisos_plan

# Hoja de estilos de la vitrina y textos de cada plan (el lema), de la vista Planes
_CSS = Path(__file__).parent / "estilos.css"
_TEXTOS = _estaticos.datos_json(Path(__file__).resolve().parent.parent / "planes" / "planes.json")
# Plan que se destaca con la cinta «Más elegido»
PLAN_DESTACADO = "pro"
# Lo que incluyen todos los planes (solo funciones ya programadas)
_EN_TODOS = [
    "Cuenta demo de Capital.com para practicar sin arriesgar dinero",
    "Gráficos profesionales con todas las herramientas de dibujo",
    "Órdenes que propone el agente: tú decides si se ejecutan",
    "Operar con stop loss, take profit, órdenes pendientes y calculadora de riesgo",
    "Resumen, cartera y diario de operaciones",
    "Mercados, cotizaciones y buscador de todos los activos",
    "Avisos en tu campana: agente, posiciones cerradas y alertas de precio",
]


# TITULO ESTILOS

def estilos() -> str:
    """Hoja de estilos de la vitrina envuelta en <style>, lista para `st.html`."""
    return _estaticos.estilos(_CSS)


# TITULO NUMERO

def _n(x) -> str:
    """Número con punto de miles (por ejemplo 20.000)."""
    return f"{x:,.0f}".replace(",", ".")


# TITULO PRECIO TEXTO

def precio_texto(precio: float) -> str:
    """Precio en formato español: coma decimal y sin «,00» si es redondo (4,99 · 15)."""
    texto = f"{float(precio):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return texto[:-3] if texto.endswith(",00") else texto


# TITULO VENTAJAS

def _ventajas(clave: str) -> list[tuple[str, str]]:
    """Lo que incluye (o no incluye) el plan `clave`, como pares (texto HTML, clase): «» incluido, «vp-no» no incluido y «vp-plus» ventaja que se resalta.

    Los valores salen de `permisos_plan.valor`. Lo que un plan no tiene se deja tachado en vez de ocultarlo: así se ve qué se gana al subir de plan."""
    def v(funcion):
        """Valor de la función en este plan."""
        return permisos_plan.valor(funcion, clave)
    filas: list[tuple[str, str]] = []
    if "profundo" in (v("perfiles_ia") or []):
        filas.append(("<b>Agente profundo</b>: el modelo más avanzado para estudios complejos", "vp-plus"))
    else:
        filas.append(("Agente rápido y de análisis", ""))
    vigilancias = int(v("vigilancias_activas") or 0)
    if vigilancias:
        filas.append((f"<b>{_n(vigilancias)}</b> vigilancia{'s' if vigilancias != 1 else ''} automática{'s' if vigilancias != 1 else ''} que trabajan por ti", ""))
    else:
        filas.append(("Vigilancias automáticas", "vp-no"))
    filas.append(("Límites de riesgo para el agente", "" if v("limites_agente") else "vp-no"))
    simbolos = int(v("comparar_simbolos") or 1)
    filas.append((f"<b>{_n(v('indicadores_por_grafico'))}</b> indicadores por gráfico · compara <b>{_n(simbolos)}</b> símbolo{'s' if simbolos != 1 else ''}", ""))
    filas.append((f"Backtest de hasta <b>{_n(v('backtest_velas'))}</b> velas", ""))
    filas.append(("Replay: practica vela a vela", "" if v("replay") else "vp-no"))
    filas.append((f"<b>{_n(v('activos_en_lista'))}</b> activos en tu lista", ""))
    filas.append((f"<b>{_n(v('alertas_precio_activas'))}</b> alertas de precio", ""))
    return filas


# TITULO PLAN VALIDO

def plan_valido(clave: str | None) -> str | None:
    """Devuelve `clave` si es un plan que existe (por ejemplo «pro»), o None si viene vacía o no corresponde a ningún plan."""
    return clave if clave in configuracion.PLANES_IA else None


# TITULO CABECERA

def html_cabecera(clave: str, elegido: str | None = None, con_boton: bool = True, precio: float | None = None) -> str:
    """Parte de arriba de la tarjeta de un plan: cinta, sello, nombre, lema, precio, preguntas por semana y, si se pide, el botón-enlace al registro.

    `elegido` es el plan escogido en el registro (sello «Tu elección»). `con_boton` es False en la vista Planes, que pone debajo sus propios botones (el plan
    actual lo marcan allí el borde verde y el botón «Tu plan actual»). `precio` permite pasar el precio de la variante del usuario (por defecto, el primero del plan)."""
    plan = configuracion.PLANES_IA[clave]
    precio = float((plan.get("precios") or [0])[0]) if precio is None else float(precio)
    gratis = precio <= 0
    cinta = "<div class='vp-cinta'>★ MÁS ELEGIDO</div>" if clave == PLAN_DESTACADO else ""
    sello = "<div class='vp-eleccion'>✓ Tu elección</div>" if clave == elegido else ""
    if gratis:
        cifra, nota = "<b>Gratis</b>", "Sin tarjeta · empieza hoy mismo"
        boton = "<a class='vp-boton vp-boton-lleno' href='?acceso=crear' target='_self'>Crear cuenta gratis →</a>"
    else:
        cifra = f"<b>{precio_texto(precio)}</b><span>USD al mes</span>"
        nota = "Pago mensual con Flow · muy pronto"
        relleno = " vp-boton-lleno" if clave == PLAN_DESTACADO else ""
        boton = f"<a class='vp-boton{relleno}' href='?acceso=crear&amp;plan={clave}' target='_self'>Elegir {escape(plan['nombre'])} →</a>"
    return (f"{cinta}{sello}<div class='vp-nombre'>{escape(plan['nombre'])}</div><p class='vp-lema'>{escape(_TEXTOS['titulos'].get(clave, ''))}</p>"
            f"<div class='vp-precio'>{cifra}</div><p class='vp-nota'>{nota}</p>"
            f"<div class='vp-preguntas'><strong>{_n(plan['preguntas_semana'])}</strong><span>preguntas al agente<br>cada semana</span></div>"
            + (boton if con_boton else ""))


# TITULO LISTA

def html_lista(clave: str) -> str:
    """Lista de lo que incluye el plan `clave` (las ventajas con ✓ y lo que no tiene, tachado)."""
    return "<ul class='vp-lista'>" + "".join(f"<li class='{clase}'>{texto}</li>" for texto, clase in _ventajas(clave)) + "</ul>"


# TITULO TARJETA

def _tarjeta(clave: str, elegido: str | None) -> str:
    """Tarjeta completa de un plan para la vitrina de acceso: cabecera con botón-enlace y lista. Lleva la clase del plan, la de destacado y la de elegido."""
    clases = f"vp-tarjeta vp-{clave}" + (" vp-destacada" if clave == PLAN_DESTACADO else "") + (" vp-elegida" if clave == elegido else "")
    return f"<article class='{clases}'>{html_cabecera(clave, elegido)}{html_lista(clave)}</article>"


# TITULO BENEFICIOS

def html_beneficios() -> str:
    """Bloque «Qué te llevas al crear tu cuenta» (tres beneficios reales) que se pone bajo el formulario, con la hoja de estilos. Llena la columna del formulario."""
    items = [("Cuenta demo con dinero virtual", "Practica sin arriesgar tu capital."),
             ("Un agente de IA que analiza el mercado", "Propone operaciones y tú decides cuáles se ejecutan."),
             ("Sin tarjeta para empezar", "El plan Gratis no pide datos de pago.")]
    lista = "".join(f"<li><b>{escape(t)}</b><span>{escape(d)}</span></li>" for t, d in items)
    return estilos() + f"<div class='vp-beneficios'><div class='vp-ben-titulo'>Qué te llevas al crear tu cuenta</div><ul>{lista}</ul></div>"


# TITULO PISTA

def html_pista() -> str:
    """HTML del enlace llamativo que se pone bajo el formulario y baja hasta la vitrina («Mira lo que incluye cada plan»), con la hoja de estilos."""
    return estilos() + "<a class='vp-pista' href='#planes-acceso'>Mira lo que incluye cada plan <b>↓</b></a>"


# TITULO AVISO DEL PLAN ELEGIDO

def html_plan_elegido(clave: str) -> str:
    """HTML del aviso verde que confirma el plan elegido al crear la cuenta, con la hoja de estilos. Explica que se contrata desde Planes cuando el pago con Flow esté disponible."""
    plan = configuracion.PLANES_IA[clave]
    return (estilos() + f"<div class='vp-elegido'><i>✓</i><div>Elegiste el plan <b>{escape(plan['nombre'])}</b>. Crea tu cuenta y actívalo al entrar, "
            f"en la sección Planes (el pago con Flow estará disponible muy pronto).</div></div>")


# TITULO PIE COMUN

def html_comun() -> str:
    """Bloque «Todos los planes incluyen», los avisos de confianza y la nota de precios (para el final de la vitrina y de la vista Planes)."""
    comun = "".join(f"<li>{escape(texto)}</li>" for texto in _EN_TODOS)
    return (f"<div class='vp-comun'><div class='vp-comun-titulo'>Todos los planes incluyen</div><ul>{comun}</ul></div>"
            "<div class='vp-confianza'><span>Sin tarjeta para empezar</span><span>Cambia de plan cuando quieras</span>"
            "<span>Pago en línea con Flow, muy pronto</span></div>"
            "<p class='vp-pie'>Precios en USD por mes. Las preguntas al agente se renuevan cada domingo a las 18:00 (hora de Chile).</p>")


# TITULO REJILLA

def html_rejilla(elegido: str | None = None, cuatro: bool = False, adaptable: bool = False) -> str:
    """Las cuatro tarjetas de los planes en una rejilla: de dos columnas (el panel a la derecha de los formularios de acceso), con `cuatro` de cuatro columnas
    (la sección de planes de la portada, que es ancha) o, con `adaptable`, de dos columnas que pasan a cuatro cuando la pantalla mide 1500 px o más.
    `elegido` es el plan marcado con «Tu elección»."""
    tarjetas = "".join(_tarjeta(clave, plan_valido(elegido)) for clave in configuracion.PLANES_IA)
    return f"<div class='vp-rejilla{' vp-cuatro' if cuatro else ''}{' vp-adaptable' if adaptable else ''}'>{tarjetas}</div>"


# TITULO HTML VITRINA

def html_vitrina(elegido: str | None = None) -> str:
    """HTML completo del panel de planes de las pantallas de acceso: encabezado, las cuatro tarjetas verticales, lo que incluyen todos los planes y los avisos de confianza.

    Va a la derecha del formulario (en pantallas angostas, debajo). Las tarjetas van en dos columnas y, en pantallas de 1500 px o más, las cuatro en una fila.
    `elegido` es el plan que el usuario escogió en el paso anterior (o None): su tarjeta lleva el sello «Tu elección». Incluye la hoja de estilos."""
    return (estilos()
            + "<section class='vp' id='planes-acceso'><div class='vp-cabecera'><span class='vp-etiqueta'>Planes</span>"
              "<div class='vp-titulo'>Elige el plan que <span>impulsa tu trading</span></div>"
              "<p class='vp-sub'>Empieza gratis y mejora cuando quieras. Cada plan te da más preguntas al agente de IA, más vigilancias automáticas y más herramientas "
              "para operar con respaldo.</p></div>"
            + html_rejilla(elegido, adaptable=True) + html_comun() + "</section>")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara vitrina .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
