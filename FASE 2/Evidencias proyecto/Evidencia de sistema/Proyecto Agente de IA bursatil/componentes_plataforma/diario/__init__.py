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
componentes_plataforma/diario
------------------
Vista "Diario" (Trading Journal, sección E): registro automático de operaciones
cerradas desde MT5 + métricas (win rate, profit factor, R/R, expectancy, drawdown)
+ ficha por operación con mini-gráfico auto-generado y notas editables (estrategia,
emoción, razón) y R/R planificado/realizado.

Archivos: panel.py (arma la vista), tabla.py, ficha.py, mini_grafico.py, formato.py,
datos.json (estrategias y emociones) y estilos.css.

Estética alineada con el historial de la vista Inicio (tabla `pos`, íconos de
activo, pills BUY/SELL, verde/rojo con la paleta P&J). Datos de estadisticas_diario /
almacen_diario.

Este archivo es la fachada del paquete: reexporta renderizar_panel_journal (definida en
panel.py) para que el resto de la plataforma muestre el Diario con una sola importación.
"""
# Reexporta la función pública de la vista.
from componentes_plataforma.diario.panel import renderizar_panel_journal

# Nombres públicos del paquete.
__all__ = ["renderizar_panel_journal"]


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
