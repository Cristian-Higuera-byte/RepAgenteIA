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
   ------------------------------------- INICIO Piña y Jara riel .JS -------------------------------------
   ------------------------------------------------------------------------------------------------------- */

/* Script del rail derecho: alterna los paneles Operar y DOM sin reejecutar Python. */
// Función autoejecutable: se ejecuta una vez al cargarse el iframe invisible del rail.
(function(){
  // P = ventana de Streamlit (padre del iframe), D = su documento, H = elemento html donde viven las clases de estado.
  var P = window.parent, D, H;
  // Si el navegador bloquea el acceso al documento padre (otro origen), no hay nada que hacer.
  try { D = P.document; H = D.documentElement; } catch(e) { return; }
  /**
   * Lee qué panel está abierto según las clases del elemento html.
   * Devuelve 'dom', 'none' (todo oculto) u 'order' (Operar; es el estado por defecto, sin clase).
   */
  function estado(){
    if (H.classList.contains('pj-panel-dom')) return 'dom';
    if (H.classList.contains('pj-panel-fav')) return 'fav';
    if (H.classList.contains('pj-panel-none')) return 'none';
    return 'order';   // sin clase = Operar abierto (default al entrar / F5)
  }
  /**
   * Fija el estado de los paneles.
   * Recibe s ('dom', 'fav', 'none' u 'order') y activa o quita las clases pj-panel-dom, pj-panel-fav y pj-panel-none en html; el CSS
   * desliza los paneles en consecuencia.
   */
  function poner(s){
    H.classList.toggle('pj-panel-dom', s === 'dom');
    H.classList.toggle('pj-panel-fav', s === 'fav');
    H.classList.toggle('pj-panel-none', s === 'none');
  }
  // Si el script se carga otra vez (rerun de Streamlit), se retira el oyente anterior para no duplicar clics.
  if (P.__pjRailFn) D.removeEventListener('click', P.__pjRailFn, true);
  /**
   * Oyente de clics en fase de captura, guardado en la ventana padre para poder retirarlo después.
   * Recibe el evento e; si el clic cayó en el botón Operar, DOM o Favoritos del rail, lo intercepta (antes de que llegue a
   * Streamlit, así no hay rerun) y alterna el panel: pulsar el botón del panel abierto lo oculta todo.
   */
  P.__pjRailFn = function(e){
    if (!(e.target && e.target.closest)) return;
    // Botones del rail identificados por la clave que les da Streamlit (clases st-key-rail_order y st-key-rail_dom).
    var bo = e.target.closest('.st-key-rail_order button');
    var bd = e.target.closest('.st-key-rail_dom button');
    var bf = e.target.closest('.st-key-rail_fav button');
    // Cualquier otro clic sigue su curso normal.
    if (!bo && !bd && !bf) return;
    e.stopPropagation(); e.preventDefault();
    var c = estado();
    if (bo) poner(c === 'order' ? 'none' : 'order');
    else if (bd) poner(c === 'dom' ? 'none' : 'dom');
    else    poner(c === 'fav' ? 'none' : 'fav');
  };
  // Captura (true) para adelantarse a los manejadores de Streamlit.
  D.addEventListener('click', P.__pjRailFn, true);
})();
/* -------------------------------------------------------------------------------------------------------
   --------------------------------------- FIN Piña y Jara riel .JS --------------------------------------
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
