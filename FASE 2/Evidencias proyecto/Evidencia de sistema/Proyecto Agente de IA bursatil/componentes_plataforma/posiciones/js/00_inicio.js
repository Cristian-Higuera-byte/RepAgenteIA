/*
Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
Dirección: José Joaquín Prieto #5373 -
San Miguel - Santiago - Chile
contacto.pinayjara@gmail.com
https://www.pinayjara.cl
Creado, Programado y Diseñado por Piña y Jara
Transportes y Servicios Ltda.
*/


/* -------------------------------------------------------------------------------------------------------
   ----------------------------------- INICIO Piña y Jara 00_inicio .JS ----------------------------------
   ------------------------------------------------------------------------------------------------------- */

    // ===== Trading desde el gráfico (componentes_plataforma/posiciones/) =====
    // Función autoejecutable que se cierra en el último fragmento (99_en_vivo.js); todos los fragmentos comparten su ámbito.
    // Los marcadores de datos de abajo los sustituye js_grafico.py antes de entregar el script al navegador.
    (function(){
      // REAL = símbolo real del bróker; INI = estado inicial (posiciones, órdenes, Bid/Ask, volumen mínimo...).
      var REAL = __POS_REAL__, INICIO = __POS_INI__;
      // POS y ORD: posiciones abiertas y órdenes pendientes por ticket, en el formato compacto del feed.
      var POSICION = INICIO.pos || {}, ORDEN = INICIO.ord || {};
      // BID/ASK: último precio conocido (0 hasta que llegue un tick); VMIN: volumen mínimo; SM: distancia mínima de stops;
      // K: valor monetario de una unidad de precio por lote (para proyectar P/G).
      var BID = INICIO.ba[0], ASK = INICIO.ba[1], VMIN = INICIO.vmin || 0.01, SM = INICIO.sm || 0, K = INICIO.k || 0;
      // OFF: desfase del reloj del servidor del bróker respecto a la hora real; EM: modos de caducidad permitidos.
      var OFF = INICIO.off || 0, EM = INICIO.em || 0;   // desfase hora servidor (s) y modos de caducidad
      // Colores: compra (verde), venta (rojo), take profit (verde) y stop loss (naranja).
      var COMPRA = '#3fb950', VENTA = '#f85149', C_TAKE_PROFIT = '#3fb950', C_STOP_LOSS = '#ff8f00';
      // SEP: separación horizontal entre las etiquetas y el eje de precios.
      var SEPARADOR = 56;   // px entre las etiquetas y el eje de precios (como XM)
      // NOMBRE: texto mostrado para cada nivel (tp, sl).
      var NOMBRE = {tp: 'Take Profit', sl: 'Stop Loss'};
      // TIPO: nombre en inglés de cada tipo de operación de MT5 (0 y 1 posiciones; 2 a 5 órdenes pendientes).
      var TIPO = {0: 'Buy', 1: 'Sell', 2: 'Buy Limit', 3: 'Sell Limit', 4: 'Buy Stop', 5: 'Sell Stop'};
      // PD: documento de la página de Streamlit (padre del iframe del gráfico), para leer el ticket de órdenes.
      var PD = window.parent.document;


/* -------------------------------------------------------------------------------------------------------
   ------------------------------------ FIN Piña y Jara 00_inicio .JS ------------------------------------
   ------------------------------------------------------------------------------------------------------- */

/*
Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
Dirección: José Joaquín Prieto #5373 -
San Miguel - Santiago - Chile
contacto.pinayjara@gmail.com
https://www.pinayjara.cl
Creado, Programado y Diseñado por Piña y Jara
Transportes y Servicios Ltda.
*/
