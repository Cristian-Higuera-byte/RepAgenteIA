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
   ---------------------------------- INICIO Piña y Jara transicion .JS ----------------------------------
   ------------------------------------------------------------------------------------------------------- */

/* Cortina de transición: oculta el área de contenido mientras Streamlit dibuja la sección nueva y la muestra ya armada. */
// Función autoejecutable: corre una vez al cargarse el iframe invisible de la transición.
(function(){
  // P = ventana de Streamlit (padre del iframe), D = su documento, H = elemento html donde vive la clase de estado.
  var P = window.parent, D, H;
  // Si el navegador bloquea el acceso al documento padre (otro origen), no hay nada que hacer.
  try { D = P.document; H = D.documentElement; } catch(e) { return; }
  // Botones que cambian de sección: barra lateral y accesos rápidos de Inicio (se pulsan en la vista, no en la barra).
  var BOTONES = '[class*="st-key-navegacion_boton_"] button, [class*="st-key-accsel_"] button';
  // Tiempo máximo con la cortina puesta (ms): si Streamlit no termina, se retira igual para no dejar la pantalla vacía.
  var TOPE = 25000;
  // Pausa (ms) sin ejecución antes de dar la sección por lista; evita descubrirla entre dos pasadas seguidas.
  var REPOSO = 70;
  var reloj = null;
  // TITULO EJECUTANDO

  /**
   * Indica si Streamlit está ejecutando el script (atributo data-test-script-state del contenedor de la aplicación).
   * Devuelve true mientras corre una ejecución (completa o de un fragmento).
   */
  function ejecutando(){
    var a = D.querySelector('[data-testid="stApp"]');
    return !!a && a.getAttribute('data-test-script-state') === 'running';
  }
  // TITULO DESCUBRIR

  /**
   * Retira la cortina: detiene el vigilante y quita la clase pj-navegando tras dos cuadros de animación, para que el
   * navegador ya haya pintado la vista nueva y el fundido empiece sobre contenido completo.
   */
  function descubrir(){
    clearInterval(reloj); reloj = null;
    P.requestAnimationFrame(function(){ P.requestAnimationFrame(function(){ H.classList.remove('pj-navegando'); }); });
  }
  // TITULO CUBRIR

  /**
   * Pone la cortina y vigila la ejecución: espera a ver que el script corre y luego a que se quede quieto un instante.
   * Si pasado 1,5 s nunca corrió (clic sin efecto), cuenta el reposo igualmente; el tope TOPE la retira en cualquier caso.
   */
  function cubrir(){
    var t0 = Date.now(), vistoCorriendo = false, quieto = 0;
    H.classList.add('pj-navegando');
    clearInterval(reloj);
    reloj = setInterval(function(){
      var ahora = Date.now() - t0;
      if (ejecutando()) { vistoCorriendo = true; quieto = 0; }
      else if (vistoCorriendo || ahora > 900) { quieto += 25; }
      if (quieto >= REPOSO || ahora > TOPE) descubrir();
    }, 25);
  }
  // Si el script se carga otra vez (rerun de Streamlit), se retira el oyente anterior para no duplicar clics.
  if (P.__pjTransFn) D.removeEventListener('click', P.__pjTransFn, true);
  /**
   * Oyente de clics en fase de captura, guardado en la ventana padre para poder retirarlo después.
   * Recibe el evento e; si cayó en un botón de navegación que no sea el de la sección ya activa (los activos son de tipo
   * primary), pone la cortina. No detiene el clic: Streamlit lo procesa con normalidad.
   */
  P.__pjTransFn = function(e){
    var b = e.target && e.target.closest && e.target.closest(BOTONES);
    if (!b) return;
    // Pulsar la sección que ya está abierta no cambia nada: no se cubre.
    if (b.getAttribute('data-testid') === 'stBaseButton-primary' && b.closest('[class*="st-key-navegacion_boton_"]')) return;
    cubrir();
  };
  // Captura (true) para enterarse del clic antes que los manejadores de Streamlit.
  D.addEventListener('click', P.__pjTransFn, true);

  // TITULO RESPUESTA INMEDIATA DE LOS BOTONES

  // Botones y interruptores de Streamlit: al pulsarlos reciben al instante la clase pj-esperando (un anillo verde y un leve hundimiento) y la conservan
  // hasta que la ejecución termina, de modo que la pantalla responde en el mismo momento del clic aunque el servidor tarde en contestar.
  var PULSABLES = 'button[data-testid^="stBaseButton"], [data-testid="stCheckbox"] label, [data-testid="stToggle"] label';
  var esperando = null, relojBoton = null;
  // TITULO LIBERAR

  /** Quita la clase de espera del último botón pulsado y detiene su vigilante. */
  function liberar(){
    if (esperando) esperando.classList.remove('pj-esperando');
    esperando = null; clearInterval(relojBoton); relojBoton = null;
  }
  if (P.__pjPulsoFn) D.removeEventListener('click', P.__pjPulsoFn, true);
  /**
   * Oyente de clics (fase de captura): marca el botón pulsado y espera a que la ejecución corra y se quede quieta (o, si nunca corre, 0,7 s; tope 8 s).
   * Ignora los botones deshabilitados y las pestañas. No detiene el clic.
   */
  P.__pjPulsoFn = function(e){
    var b = e.target && e.target.closest && e.target.closest(PULSABLES);
    if (!b || b.disabled || b.getAttribute('aria-disabled') === 'true' || b.closest('[role="tablist"]')) return;
    liberar();
    esperando = b; b.classList.add('pj-esperando');
    var t0 = Date.now(), visto = false, quieto = 0;
    relojBoton = setInterval(function(){
      var ahora = Date.now() - t0;
      if (ejecutando()) { visto = true; quieto = 0; }
      else if (visto || ahora > 700) { quieto += 30; }
      if (quieto >= 90 || ahora > 8000) liberar();
    }, 30);
  };
  D.addEventListener('click', P.__pjPulsoFn, true);
})();

/* -------------------------------------------------------------------------------------------------------
   ----------------------------------- FIN Piña y Jara transicion .JS ------------------------------------
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
