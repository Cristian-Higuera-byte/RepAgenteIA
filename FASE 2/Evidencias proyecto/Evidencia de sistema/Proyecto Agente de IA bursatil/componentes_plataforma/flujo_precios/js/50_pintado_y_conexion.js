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
   ----------------------------- INICIO Piña y Jara 50_pintado_y_conexion .JS ----------------------------
   ------------------------------------------------------------------------------------------------------- */

  // TITULO PINTAR

  /**
   * Repinta el DOM con los últimos ticks conocidos.
   * `solo` (opcional) es un objeto con los símbolos que cambiaron; si es null se repintan todos.
   * Actualiza elementos de precio, mini-gráficos y datos de cuenta.
   */
  function pintar(solo){
    D.querySelectorAll('[data-pj-s]').forEach(function(el){
      var s = el.getAttribute('data-pj-s');
      if (solo && !(s in solo)) return;
      var t = ultimo[s];
      if (t) pintarElemento(el, t);
    });
    D.querySelectorAll('[data-pj-spark]').forEach(function(el){
      var s = el.getAttribute('data-pj-spark');
      if (!solo || (s in solo)) pintarSpark(el, s);
    });
    pintarCuenta();
  }

  // TITULO SIMBOLOS

  /** Devuelve los símbolos distintos marcados con data-pj-s en la página, ordenados y unidos por comas. */
  function simbolos(){
    var set = {};
    D.querySelectorAll('[data-pj-s]').forEach(function(el){ set[el.getAttribute('data-pj-s')] = 1; });
    return Object.keys(set).sort().join(',');
  }

  // TITULO CONECTAR

  /**
   * Abre (o reabre) la conexión SSE a `/stream` para la lista de símbolos `lista`.
   * Cada mensaje trae `t` (ticks por símbolo) y `acc` (cuenta); guarda los datos, repinta y reenvía
   * el mensaje por BroadcastChannel para que el gráfico mueva la vela actual.
   */
  function conectar(lista){
    if (es) es.close();
    actuales = lista;
    // Una sola conexión SSE con todos los símbolos visibles.
    es = new EventSource(API + '/stream?s=' + encodeURIComponent(lista));
    es.onmessage = function(ev){
      var m;
      try { m = JSON.parse(ev.data); } catch(e) { return; }
      // Siembra mini-gráficos nuevos y guarda cada tick recibido.
      sembrarSparks();
      for (var k in m.t){ ultimo[k] = m.t[k]; empujarSpark(k, m.t[k].l); }
      // Datos de cuenta, repintado y reenvío al gráfico.
      if (m.acc) cuenta = m.acc;
      pintar(m.t);
      if (bc) bc.postMessage(m);
    };
  }

  // TITULO REVISAR

  // Revisa si cambió el conjunto de símbolos (cambio de vista/activo) y repinta
  // lo que Streamlit acaba de redibujar con valores viejos.
  /**
   * Sincroniza la suscripción con la página: si cambió el conjunto de símbolos reconecta,
   * y repinta todo con los últimos valores. Se ejecuta con retardo tras cambios en el DOM y al arrancar.
   */
  function revisar(){
    pendiente = false;
    sembrarSparks();                   // la tarjeta redibujada puede traer semilla nueva
    var lista = simbolos();
    if (lista && lista !== actuales) conectar(lista);
    pintar(null);
  }
  // El callback del MutationObserver corre ANTES de que el navegador pinte el
  // cambio: repintar aquí mismo hace que nunca se vea el valor/mini-gráfico viejo
  // que trae el refresco de respaldo de Streamlit (antes se veía ~120 ms → parpadeo).
  // La reconexión por cambio de símbolos sí va con retardo (no es urgente).
  // Observa el DOM de Streamlit: cada redibujado repinta al instante y programa una revisión de símbolos.
  new MutationObserver(function(){
    sembrarSparks();
    pintar(null);
    if (pendiente) return;
    pendiente = true;
    setTimeout(revisar, 120);
  }).observe(D.body, {childList: true, subtree: true});


/* -------------------------------------------------------------------------------------------------------
   ------------------------------ FIN Piña y Jara 50_pintado_y_conexion .JS ------------------------------
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
