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
   ----------------------------------- INICIO Piña y Jara cargando .JS -----------------------------------
   ------------------------------------------------------------------------------------------------------- */

/** Funcion autoejecutable que instala, en la pagina padre de Streamlit, el indicador "cargando" de la ficha. */
(function(){
  // P: ventana padre (la app de Streamlit, porque este script corre dentro de un iframe); D: su documento
  var P = window.parent, D;
  // Si el navegador bloquea el acceso al documento padre, no se puede hacer nada
  try { D = P.document; } catch(e) { return; }
  // Inyecta una sola vez la hoja de estilos del indicador (superposicion, anillo giratorio y animacion)
  if (!D.getElementById('pj-mkt-load-css')){
    var st = D.createElement('style'); st.id = 'pj-mkt-load-css';
    st.textContent =
      '#pj-mkt-load{position:fixed;inset:0;z-index:999999;display:flex;align-items:center;justify-content:center;' +
      'background:rgba(5,8,14,.55);backdrop-filter:blur(3px);opacity:0;transition:opacity .18s ease;pointer-events:none;}' +
      '#pj-mkt-load.on{opacity:1;}' +
      '#pj-mkt-load .box{display:flex;flex-direction:column;align-items:center;gap:14px;background:#0d1117;' +
      'border:1px solid #30363d;border-radius:16px;padding:26px 34px;box-shadow:0 18px 50px rgba(0,0,0,.55);}' +
      '#pj-mkt-load .ring{width:46px;height:46px;border-radius:50%;' +
      'background:conic-gradient(from 0deg,rgba(255,75,75,0),#ff4b4b 55%,#ff8f00);' +
      '-webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 5px),#000 calc(100% - 4px));' +
      'mask:radial-gradient(farthest-side,transparent calc(100% - 5px),#000 calc(100% - 4px));' +
      'animation:pjgira .8s linear infinite;}' +
      '#pj-mkt-load .t{color:#e6edf3;font:600 14px "Source Sans Pro",system-ui,sans-serif;}' +
      '#pj-mkt-load .s{color:#8b949e;font:12px "Source Sans Pro",system-ui,sans-serif;margin-top:-8px;}' +
      '@keyframes pjgira{to{transform:rotate(360deg);}}';
    D.head.appendChild(st);
  }
  // tope: temporizador de seguridad que oculta el indicador; obs: observador que detecta la ficha abierta
  var tope = null, obs = null;
  /** Quita el indicador: detiene el observador y el temporizador, lo desvanece y luego lo elimina del DOM. */
  function ocultar(){
    var el = D.getElementById('pj-mkt-load');
    if (obs){ obs.disconnect(); obs = null; }
    if (tope){ clearTimeout(tope); tope = null; }
    if (!el) return;
    el.classList.remove('on');
    setTimeout(function(){ if (el.parentNode) el.parentNode.removeChild(el); }, 200);
  }
  /** Muestra el indicador con el texto "Abriendo (nombre)" y lo oculta cuando aparece la ficha o tras 20 s. */
  function mostrar(nombre){
    // Elimina cualquier indicador previo antes de crear uno nuevo
    ocultar();
    var el = D.createElement('div'); el.id = 'pj-mkt-load';
    el.innerHTML = '<div class="box"><div class="ring"></div><div class="t"></div>' +
                   '<div class="s">Cargando precios, gráfico y estadísticas</div></div>';
    el.querySelector('.t').textContent = nombre ? 'Abriendo ' + nombre + '…' : 'Abriendo ficha…';
    D.body.appendChild(el);
    // La clase "on" se agrega en el siguiente fotograma para que la transicion de opacidad se anime
    requestAnimationFrame(function(){ el.classList.add('on'); });
    // Cuando Streamlit dibuja el contenedor de la ficha (clase st-key-fic_root) el indicador ya no hace falta
    obs = new MutationObserver(function(){ if (D.querySelector('.st-key-fic_root')) ocultar(); });
    obs.observe(D.body, {childList: true, subtree: true});
    tope = setTimeout(ocultar, 20000);            // respaldo: nunca queda pegado
  }
  // Evita acumular escuchas duplicados si el script se ejecuta de nuevo en un rerun
  if (P.__pjMktLoadFn) D.removeEventListener('click', P.__pjMktLoadFn, true);
  /** Escucha de clic global: si el clic fue en un boton "ver" de una fila o tarjeta (st-key-mktclk_), muestra el indicador con el nombre del instrumento. */
  P.__pjMktLoadFn = function(e){
    var b = e.target.closest && e.target.closest('[class*="st-key-mktclk_"] button');
    if (!b) return;
    // Nombre visible del instrumento, tomado de la fila (.mkt-nm b) o de la tarjeta (.mkt-card-nm)
    var cont = b.closest('[class*="st-key-mktrow_"], [class*="st-key-mktcard_"]');
    var nm = cont && cont.querySelector('.mkt-nm b, .mkt-card-nm');
    mostrar(nm ? nm.textContent.trim() : '');
  };
  D.addEventListener('click', P.__pjMktLoadFn, true);   // captura: sin frenar el clic
})();

/* -------------------------------------------------------------------------------------------------------
   ------------------------------------- FIN Piña y Jara cargando .JS ------------------------------------
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
