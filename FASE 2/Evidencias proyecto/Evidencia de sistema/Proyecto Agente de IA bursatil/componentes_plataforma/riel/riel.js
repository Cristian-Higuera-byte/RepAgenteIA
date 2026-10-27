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
  // TITULO ESTADO

  /**
   * Lee qué panel está abierto según las clases del elemento html.
   * Devuelve 'dom', 'none' (todo oculto) u 'order' (Operar; es el estado por defecto, sin clase).
   */
  function estado(){
    if (H.classList.contains('pj-panel-dom')) return 'dom';
    if (H.classList.contains('pj-panel-favorito')) return 'fav';
    if (H.classList.contains('pj-panel-activos')) return 'activos';
    if (H.classList.contains('pj-panel-none')) return 'none';
    return 'order';   // sin clase = Operar abierto (default al entrar / F5)
  }
  // TITULO PONER

  /**
   * Fija el estado de los paneles.
   * Recibe s ('dom', 'fav', 'none' u 'order') y activa o quita las clases pj-panel-dom, pj-panel-favorito y pj-panel-none en html; el CSS
   * desliza los paneles en consecuencia.
   */
  function poner(s){
    H.classList.toggle('pj-panel-dom', s === 'dom');
    H.classList.toggle('pj-panel-favorito', s === 'fav');
    H.classList.toggle('pj-panel-activos', s === 'activos');
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
    /* Barra fija Vender/Comprar del celular: abre el panel Operar (la orden se confirma en el ticket, no aquí). */
    if (e.target.closest('.pj-barra-op button')) {
      e.stopPropagation(); e.preventDefault();
      /* Vender abre el ticket con SELL elegido y Comprar con BUY: se pulsa el boton invisible del lado en el ticket (panel_orden/panel.py,
         claves orden_superposicion_sell y _buy), que fija el lado en Python. */
      var lado = e.target.closest('.pj-op-vender') ? 'sell' : 'buy';
      var ov = D.querySelector('.st-key-orden_superposicion_' + lado + ' button');
      /* El panel se abre cuando el ticket ya muestra el lado pedido (si no, se veria saltar de BUY a SELL): se espera hasta 2 s a que el rerun
         del fragmento lo pinte; si el lado ya era el correcto, se abre de inmediato. */
      var ok = function(){ return !!D.querySelector('.orden-mitad.orden-' + lado + '.sel'); };
      if (!ov || ok()) { poner('order'); return; }
      ov.click();
      var intentos = 0;
      var espera = P.setInterval(function(){
        if (ok() || ++intentos > 40) { P.clearInterval(espera); poner('order'); }
      }, 50);
      return;
    }
    /* Celular: tocar el símbolo de la cabecera de precio abre la hoja Lista de activos (o Favoritos si la vista no tiene lista) para cambiar de activo; al elegir un favorito el
       panel se cierra y el clic sigue su curso para que Streamlit cambie el activo. */
    if (P.innerWidth <= 1024 && e.target.closest('.pj-cab-simbolo')) { e.stopPropagation(); e.preventDefault(); poner(estado() === 'none' ? (D.querySelector('.st-key-lista_activos_panel') ? 'activos' : 'fav') : 'none'); return; }
    /* Celular: la hoja abierta se cierra tocando fuera de ella. No depende solo del velo oscuro (clic en html): cualquier clic que no caiga
       dentro de la hoja abierta, ni en la barra de navegacion, la barra Vender/Comprar o el simbolo, la cierra sin llegar a Streamlit. */
    if (P.innerWidth <= 1024 && estado() !== 'none') {
      var abierta = estado() === 'order' ? '.st-key-pj_panel_orden' : estado() === 'dom' ? '.st-key-pj_panel_dom'
        : estado() === 'fav' ? '.st-key-pj_panel_favorito' : '[data-testid="stColumn"]:has(.st-key-lista_activos_panel):not(:has(.st-key-grafico_cerrar_wrap))';
      if (!e.target.closest(abierta + ', .st-key-barra_navegacion_fija, [data-testid=\"stColumn\"]:has(.pj-navegacion), .st-key-pj_barra_operar, .pj-cab-simbolo, .st-key-pj_sbjs, [data-testid="stDialog"], [data-baseweb="popover"]')) {
        e.stopPropagation(); e.preventDefault(); poner('none'); return; }
    }
    /* Cabeceras de las hojas: «Favoritos» (en la lista) y «Lista de activos» (en favoritos) pasan de una hoja a la otra. */
    if (e.target.closest('.pj-ir-fav')) { e.stopPropagation(); e.preventDefault(); poner('fav'); return; }
    if (e.target.closest('.pj-ir-lista')) { e.stopPropagation(); e.preventDefault(); poner('activos'); return; }
    if (P.innerWidth <= 1024 && e.target.closest('[class*="st-key-favsel_"] button, [class*="st-key-wlsel_"] button')) { poner('none'); return; }
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
  /* En celular el panel Operar arranca cerrado (taparía la pantalla): solo la primera vez que carga la página y si no hay otro panel abierto. */
  if (!P.__pjRielMovil && P.innerWidth <= 1024) {
    P.__pjRielMovil = true;
    if (estado() === 'order') poner('none');
  }
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
