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
   ---------------------------------- INICIO Piña y Jara flotante .JS ------------------------------------
   ------------------------------------------------------------------------------------------------------- */

/* Script del chat flotante: abre y cierra el panel del chat sin reejecutar Python y mantiene la zona de mensajes al final. */
// Función autoejecutable: se ejecuta una vez al cargarse el iframe invisible del chat flotante.
(function(){
  // P = ventana de Streamlit (padre del iframe), D = su documento, H = elemento html donde vive la clase de estado.
  var P = window.parent, D, H;
  // Si el navegador bloquea el acceso al documento padre (otro origen), no hay nada que hacer.
  try { D = P.document; H = D.documentElement; } catch(e) { return; }
  // TITULO ZONA DE MENSAJES

  /** Zona con scroll de los mensajes del chat flotante, o null si todavía no existe. */
  function zona(){ return D.querySelector('.st-key-agente_chat_desplazamiento_flot'); }
  // TITULO BAJAR

  /** Lleva la zona de mensajes al último mensaje. Se llama al abrir el panel y mientras llegan mensajes nuevos. */
  function bajar(){ var z = zona(); if (z) z.scrollTop = z.scrollHeight; }
  // TITULO ABIERTO

  /** Dice si el chat flotante se ve: abierto como ventana (pj-chat-abierto) o acoplado al rail derecho (pj-panel-agente). */
  function visible(){ return H.classList.contains('pj-chat-abierto') || H.classList.contains('pj-panel-agente'); }
  // TITULO PONER

  /**
   * Abre o cierra el chat como ventana flotante.
   * Recibe v (true abre, false cierra). Al abrir lleva los mensajes al final; con el cursor (no en pantallas táctiles) deja la caja de texto lista para escribir.
   */
  function poner(v){
    H.classList.toggle('pj-chat-abierto', v);
    if (!v) return;
    P.__pjChatCerca = true;
    [60, 250, 700].forEach(function(ms){ P.setTimeout(bajar, ms); });
    if (!(P.matchMedia && P.matchMedia('(pointer: coarse)').matches)) {
      P.setTimeout(function(){ var t = D.querySelector('.st-key-pj_chat_flotante textarea'); if (t) t.focus(); }, 320);
    }
  }
  // Si el script se carga otra vez (rerun de Streamlit), se retiran los oyentes y el temporizador anteriores para no duplicarlos.
  if (P.__pjChatClic) D.removeEventListener('click', P.__pjChatClic, true);
  if (P.__pjChatTecla) D.removeEventListener('keydown', P.__pjChatTecla, true);
  if (P.__pjChatScroll) D.removeEventListener('scroll', P.__pjChatScroll, true);
  if (P.__pjChatReloj) P.clearInterval(P.__pjChatReloj);
  /**
   * Oyente de clics en fase de captura (antes que Streamlit, así no hay rerun): la burbuja abre o cierra el chat y la X lo cierra.
   * Recibe el evento e; cualquier otro clic sigue su curso.
   */
  P.__pjChatClic = function(e){
    if (!(e.target && e.target.closest)) return;
    var b = e.target.closest('.st-key-chat_burbuja_abrir button');
    var x = e.target.closest('.st-key-chat_cerrar button');
    if (!b && !x) return;
    e.stopPropagation(); e.preventDefault();
    poner(b ? !H.classList.contains('pj-chat-abierto') : false);
  };
  D.addEventListener('click', P.__pjChatClic, true);
  /* Escape cierra la ventana (salvo que haya un diálogo de Streamlit abierto, que usa esa tecla). */
  P.__pjChatTecla = function(e){
    if (e.key === 'Escape' && H.classList.contains('pj-chat-abierto') && !D.querySelector('[data-testid="stDialog"]')) poner(false);
  };
  D.addEventListener('keydown', P.__pjChatTecla, true);
  /* Recuerda si el usuario dejó los mensajes al final; si subió a leer algo anterior no se le arrastra hacia abajo cuando llega texto nuevo. */
  P.__pjChatCerca = true;
  P.__pjChatScroll = function(e){
    var z = zona();
    if (z && e.target === z) P.__pjChatCerca = z.scrollHeight - z.scrollTop - z.clientHeight < 80;
  };
  D.addEventListener('scroll', P.__pjChatScroll, true);
  /* Mientras el chat se ve, los mensajes nuevos (la respuesta en vivo cada segundo) mantienen la zona al final si ya estaba al final. */
  P.__pjChatReloj = P.setInterval(function(){ if (visible() && P.__pjChatCerca) bajar(); }, 400);
})();
/* -------------------------------------------------------------------------------------------------------
   ------------------------------------- FIN Piña y Jara flotante .JS ------------------------------------
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
