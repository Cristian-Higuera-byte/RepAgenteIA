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
componentes_plataforma/posiciones
---------------------
Trading desde el gráfico (como MT5 / XM). Términos de trading en INGLÉS.

- POSICIONES abiertas del símbolo: línea en el precio de apertura con etiqueta
  [lotes con signo | P/G en vivo | ✕]; la ✕ abre el modal de cierre de Cartera.
- ÓRDENES PENDIENTES (Buy/Sell Limit/Stop): línea punteada con etiqueta
  [BUY LIMIT 0.01 | at 1.11982 | ✕]. Se ARRASTRA para cambiar el precio de entrada
  (el número del eje se ajusta mientras se mueve); la ✕ cancela la orden.
- TAKE PROFIT / STOP LOSS de posiciones y órdenes: insignias "TP"/"SL" que se
  arrastran para crear el nivel (con el P/G proyectado a ese precio); los niveles
  existentes son líneas propias que se mueven o se quitan con su ✕.
- MENÚ DEL CLIC DERECHO: en el precio del cursor ofrece Buy Limit / Sell Stop
  (bajo el mercado) o Sell Limit / Buy Stop (sobre el mercado) con el volumen del
  ticket, y el interruptor One-Click Trading.
- ONE-CLICK TRADING (interruptor del ticket, `orden_un_clic`; componentes_plataforma/operacion_un_clic/):
  activo → todo se envía al instante; apagado → cada acción pide confirmar en el
  propio gráfico.

Antes de enviar se valida el lado correcto y la distancia mínima del bróker.
Los envíos van a servidor_datos.py (POST /sltp, /orden, /orden/modificar,
/orden/eliminar; solo desde páginas de localhost), sin rerun de Streamlit.

Piezas:
- `js_posiciones(simbolo)`: JS que grafico/panel.py inserta DENTRO de `iniciar()`
  del gráfico (usa `chart`, `serie`, `containerEl`, `API`, `DIGITS`, `SIMBOLO`).
  Datos iniciales desde Python; luego en vivo con el mensaje de cuenta del feed
  (`acc.pi` posiciones, `acc.ord` órdenes, `acc.pos` P/G, `acc.pc` precio actual)
  y los ticks (Bid/Ask) que llegan por BroadcastChannel('pj-ticks').
- `gatillos_cierre()`: botones invisibles `grafico_cerrar_<ticket>` que pulsa la ✕ de una
  posición → abre el modal de cierre en Python.

Este paquete es el que expone la fachada `componentes_plataforma/posiciones/`; sus dos nombres públicos
(`js_posiciones` y `gatillos_cierre`) los consume `grafico/panel.py`.

Archivos: js_grafico.py (ensambla js/*.js), datos_iniciales.py (estado inicial desde MT5), gatillos.py y js/
(un fragmento por responsabilidad: estilos, utilidades, one-click, envío de órdenes, menú, editor, líneas, en vivo).
"""
# Botones invisibles que abren el modal de cierre desde la ✕ del gráfico.
from componentes_plataforma.posiciones.gatillos import gatillos_cierre
# Ensamblador del JavaScript de trading que se inserta dentro del gráfico.
from componentes_plataforma.posiciones.js_grafico import js_posiciones

# API pública del paquete.
__all__ = ["js_posiciones", "gatillos_cierre"]


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
