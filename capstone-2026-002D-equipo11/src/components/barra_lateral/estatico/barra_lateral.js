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
   --------------------------------- INICIO Piña y Jara barra_lateral .JS --------------------------------
   ------------------------------------------------------------------------------------------------------- */

// Expandir / colapsar la barra lateral SIN reejecutar Python (animado).
// Lo carga barra.py con components.html(..., height=0). El clic del ☰ (que vive en la
// barra superior, .st-key-top_toggle) se intercepta en fase de CAPTURA en el documento
// padre y se hace stopPropagation para que NO dispare un rerun de Streamlit; solo se
// alterna la clase pj-sb-exp en <html> y el CSS anima anchos y márgenes.
// Al cargar la página (o iniciar sesión) la barra parte SIEMPRE retraída.
/**
 * Función autoejecutable que instala el comportamiento del botón de menú (hamburguesa):
 * alterna la barra lateral entre colapsada y expandida sin reejecutar Python.
 * No recibe parámetros ni devuelve nada; sus efectos son sobre el documento padre de Streamlit.
 */
(function(){
  // P: ventana padre (la app de Streamlit; este script corre en un iframe de altura 0).
  // D: documento padre. H: su elemento html, donde vive la clase pj-sb-exp.
  var P = window.parent, D, H;
  // Si el iframe no puede acceder al padre (restricción de origen), no hace nada
  try { D = P.document; H = D.documentElement; } catch(e) { return; }
  /**
   * Activa o desactiva el estado expandido de la barra lateral.
   * @param {boolean} exp - true para expandir (añade pj-sb-exp a html), false para colapsar.
   */
  function aplicar(exp){ H.classList.toggle('pj-sb-exp', exp); }
  // La bandera vive en la ventana: si Streamlit recrea este iframe al navegar
  // entre vistas, NO se vuelve a cerrar; se mantiene como el usuario la dejó.
  if (!P.__pjSbIniciada){
    P.__pjSbIniciada = true;
    // Desactiva las transiciones un instante para que el primer cierre no se vea animado
    H.classList.add('pj-sb-sinanim');
    aplicar(false);
    P.setTimeout(function(){ H.classList.remove('pj-sb-sinanim'); }, 80);
  }

  // Un solo oyente en el documento padre (se reemplaza si el iframe se recrea).
  // Fase de CAPTURA en document: corre antes que React; stopPropagation evita
  // que el clic dispare un rerun de Streamlit.
  // Retira el oyente anterior (si lo hay) antes de registrar el nuevo
  if (P.__pjSbFn) D.removeEventListener('click', P.__pjSbFn, true);
  /**
   * Oyente de clic en fase de captura: si el clic cae en el botón del menú de la barra
   * superior (.st-key-top_toggle), lo consume y alterna la barra lateral.
   * @param {MouseEvent} e - Evento de clic recibido en el documento padre.
   */
  P.__pjSbFn = function(e){
    // Busca el botón del menú entre el objetivo del clic y sus ancestros
    var b = e.target && e.target.closest && e.target.closest('.st-key-top_toggle button');
    if (!b) return;
    // Evita que Streamlit procese el clic como un rerun
    e.stopPropagation(); e.preventDefault();
    aplicar(!H.classList.contains('pj-sb-exp'));
  };
  // El tercer argumento true registra el oyente en fase de captura
  D.addEventListener('click', P.__pjSbFn, true);
})();

/* -------------------------------------------------------------------------------------------------------
   ---------------------------------- FIN Piña y Jara barra_lateral .JS ----------------------------------
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
