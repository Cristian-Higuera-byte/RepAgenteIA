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

"""Paquete del gráfico principal del dashboard (panel central).

No contiene lógica propia: solo agrupa los módulos de abajo para que se importen como
`componentes_plataforma.grafico.<modulo>`.

Organización:
  panel.py            orquesta: cabecera de precio + gráfico + botones de cierre
  cabecera_precio.py  barra de precio en vivo (se refresca sola)
  simbolo.py          decimales y tamaño del pip de un símbolo (MT5)
  ensamblador.py      arma el HTML del gráfico juntando los fragmentos de estatico/
  estatico/           el gráfico en sí (HTML + CSS + JS), partido por temas:
      esqueleto.html  orden en que se pegan los fragmentos (líneas `@@ruta`)
      css/ html/ js/  fragmentos; los números del nombre marcan el orden
El trading desde el gráfico (líneas de posición, SL/TP, órdenes) sigue en
componentes_plataforma/posiciones/ y se inserta donde el esqueleto dice __POSICIONES_JS__.
"""


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
