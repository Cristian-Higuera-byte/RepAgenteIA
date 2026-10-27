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
   ------------------------------ INICIO Piña y Jara 00_avisos_de_carga .JS ------------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Avisos si falla el JS o no carga la librería del gráfico
/** Manejador global de errores JS: muestra el mensaje y la línea del error en el elemento #tv-ohlc-vals (la leyenda OHLC) para que el fallo sea visible sin abrir la consola. Recibe el mensaje, el origen y la línea. */
window.onerror = function(msg, src, line){
  var e = document.getElementById('tv-ohlc-vals');
  if (e) e.innerText = 'Error JS: ' + msg + ' (línea ' + line + ')';
};
// Temporizador de 4 s: si pasado ese tiempo la librería lightweight-charts no cargó (CDN bloqueado o sin internet), lo avisa en la leyenda OHLC.
setTimeout(function(){
  var e = document.getElementById('tv-ohlc-vals');
  if (!window.LightweightCharts && e) e.innerText = 'No cargó lightweight-charts (CDN bloqueado o sin internet)';
}, 4000);

/* -------------------------------------------------------------------------------------------------------
   -------------------------------- FIN Piña y Jara 00_avisos_de_carga .JS -------------------------------
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
