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
   ------------------------------------ INICIO Piña y Jara avisos .JS ------------------------------------
   ------------------------------------------------------------------------------------------------------- */

// Aviso flotante (toast) del resultado de la orden, inyectado en el documento PADRE.
// avisos.py reemplaza los marcadores __FONDO__ / __ICONO__ / __NONCE__ / __MSG__ y lo
// envuelve en <script>. El __NONCE__ evita que se repita en cada refresco del fragmento.
/** Funcion autoejecutable: crea el aviso en la pagina padre, lo anima y lo cierra solo a los 6 segundos o con la X. */
(function(){
  // P: ventana padre (la app de Streamlit, pues el script corre en un iframe); D: su documento. Si el navegador lo bloquea, se aborta
  var P = window.parent, D; try { D = P.document; } catch(e) { return; }
  if (P.__pjToastNonce === __NONCE__) return;   // ya mostrado para este resultado
  // Se recuerda el nonce en la ventana padre para no repetir el aviso en los refrescos del fragmento
  P.__pjToastNonce = __NONCE__;
  // Si queda un aviso anterior en pantalla, se elimina antes de crear el nuevo
  var vj = D.getElementById('pj-toast'); if (vj) vj.remove();
  // Recuadro fijo abajo a la derecha; empieza transparente y desplazado para animar su aparicion
  var el = D.createElement('div'); el.id = 'pj-toast';
  el.style.cssText = 'position:fixed;right:22px;bottom:56px;z-index:100010;max-width:380px;'+
    'display:flex;align-items:flex-start;gap:10px;padding:13px 14px;border-radius:12px;'+
    'background:__FONDO__;color:#fff;font:600 13.5px system-ui,sans-serif;'+
    'box-shadow:0 10px 30px rgba(0,0,0,.45);opacity:0;transform:translateY(8px);'+
    'transition:opacity .2s ease,transform .2s ease;';
  // Contenido: icono, mensaje y boton de cierre (X)
  el.innerHTML = '<span style="font-size:18px;line-height:1.2">__ICONO__</span>'+
    '<span style="flex:1;line-height:1.4">'+__MSG__+'</span>'+
    '<span id="pj-texto" style="cursor:pointer;opacity:.85;font-size:15px;padding:0 2px">&#10005;</span>';
  D.body.appendChild(el);
  // Al siguiente fotograma se muestra con opacidad plena y en su posicion final (dispara la transicion)
  P.requestAnimationFrame(function(){ el.style.opacity='1'; el.style.transform='translateY(0)'; });
  // tmr: temporizador del cierre automatico
  var tmr;
  // TITULO CERRAR

  /** Cierra el aviso: lo desvanece, lo elimina del DOM tras 220 ms y cancela el temporizador. */
  function cerrar(){
    if (!el) return;
    el.style.opacity='0'; el.style.transform='translateY(8px)';
    P.setTimeout(function(){ if (el && el.parentNode) el.parentNode.removeChild(el); }, 220);
    el = null; P.clearTimeout(tmr);
  }
  // La X cierra de inmediato; si no, se cierra solo a los 6 segundos
  el.querySelector('#pj-texto').onclick = cerrar;
  tmr = P.setTimeout(cerrar, 6000);
})();

/* -------------------------------------------------------------------------------------------------------
   -------------------------------------- FIN Piña y Jara avisos .JS -------------------------------------
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
