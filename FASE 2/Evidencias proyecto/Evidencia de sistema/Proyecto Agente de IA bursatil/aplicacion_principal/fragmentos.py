# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara fragmentos .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Fragmentos en vivo: partes de la página que se refrescan solas sin reejecutar todo el script.

Con `servidor_datos.py` corriendo, los precios, variaciones y el saldo llegan al navegador por el
feed SSE (`componentes_plataforma/flujo_precios/`); entonces estos fragmentos solo hacen un
refresco LENTO de respaldo (sparkline, nombres, resincronización), lo que evita reejecuciones
innecesarias y los choques de deltas ("Cannot set a node at a delta path"). Sin el servidor
vuelven al refresco de 2 segundos de siempre.

Los fragmentos se crean en CADA ejecución del script (no al importar el módulo) porque
`intervalo(...)` depende de si el servidor está vivo en ese momento.
"""
from types import SimpleNamespace

import streamlit as st

from componentes_plataforma.mercado_datos import actualizar_precios_mt5
from componentes_plataforma.favoritos import renderizar_barra_favoritos
from componentes_plataforma.flujo_precios import intervalo
from componentes_plataforma.lista_activos import renderizar_watchlist


# TITULO CREAR FRAGMENTOS

def crear_fragmentos() -> SimpleNamespace:
    """
    Crea los tres fragmentos en vivo de la página y los devuelve agrupados.

    Devuelve un objeto con tres funciones listas para llamar: `favoritos` (barra de favoritos con
    precios actualizados), `watchlist` (lista de activos de la vista Trading) y `cartera` (lista
    de posiciones abiertas de la vista Cartera). Se llama una vez por ejecución de la página.
    """
    # Cada cuánto se refrescan favoritos y watchlist; con el feed activo no hay recarga periódica
    # (así se evita el parpadeo).
    INTERVALO_PRECIOS = intervalo("2s")

    @st.fragment(run_every=INTERVALO_PRECIOS)
    def favoritos_en_vivo():
        """Actualiza los precios desde MT5 y vuelve a dibujar la barra de favoritos."""
        actualizar_precios_mt5()
        renderizar_barra_favoritos(vertical=True)   # dentro del panel «Favoritos» del rail derecho (apilados)

    @st.fragment(run_every=INTERVALO_PRECIOS)
    def watchlist_en_vivo():
        """Dibuja la lista de activos; los precios ya los refresca `favoritos_en_vivo`."""
        renderizar_watchlist()

    def cartera_en_vivo():
        """
        Dibuja la lista de posiciones abiertas (reemplaza al watchlist en la vista Cartera).

        La ganancia/pérdida total y por posición llegan por el feed en vivo; el refresco del
        fragmento solo agrega o quita filas. El auto-refresco se PAUSA únicamente mientras el
        usuario edita un nivel (clave `cartera_editando`): así, al escribir el TP, el SL o la distancia,
        la reejecución no le quita el foco al campo. Con el detalle abierto pero sin editar, la
        lista sigue refrescando para detectar cierres que ocurran solos.
        """
        from componentes_plataforma.cartera_panel import renderizar_cartera_lista
        cada = None if st.session_state.get("cartera_editando") else intervalo("2s", "5s")
        st.fragment(run_every=cada)(renderizar_cartera_lista)()

    return SimpleNamespace(favoritos=favoritos_en_vivo, watchlist=watchlist_en_vivo, cartera=cartera_en_vivo)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara fragmentos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
