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

// Inicio del script del feed en vivo: abre la función autoejecutable que cierran los fragmentos
// siguientes (hasta 60_arranque.js). Todos comparten las variables declaradas aquí.
(function(){
  // URL del servidor de datos; ensamblador.py sustituye __API__ por la URL como cadena JSON.
  var API = __API__;
  // P = ventana padre (Streamlit); D = su documento, donde viven los elementos data-pj-*.
  var P = window.parent, D;
  try { D = P.document; } catch(e) { return; }   // sin acceso al DOM padre: no hay feed

  // Canal de difusión para reenviar cada tick al gráfico (si el navegador lo soporta).
  var bc = ('BroadcastChannel' in window) ? new BroadcastChannel('pj-ticks') : null;
  // es: conexión EventSource activa; actuales: lista de símbolos suscritos; ultimo: último tick por símbolo;
  // cuenta: último dato de cuenta recibido; pendiente: hay una revisión de símbolos programada.
  var es = null, actuales = '', ultimo = {}, cuenta = null, pendiente = false;
  // spark: serie de precios por símbolo; sparkT: instante del último punto añadido;
  // sembrado: símbolos cuya semilla histórica ya se cargó.
  var spark = {}, sparkT = {}, sembrado = {};
  // Un punto nuevo por cada tick (el motor lee cada 250 ms y solo envía si el
  // precio cambió). 120 puntos ≈ 30 s de ticks en un símbolo muy activo.
  var SPARK_MAX = 120, SPARK_PASO = 250;


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
