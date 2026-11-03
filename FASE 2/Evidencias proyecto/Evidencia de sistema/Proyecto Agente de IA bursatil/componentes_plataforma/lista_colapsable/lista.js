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
   ------------------------------------- INICIO Piña y Jara lista .JS ------------------------------------
   ------------------------------------------------------------------------------------------------------- */

(function(){
  var P = window.parent, D, H;
  try { D = P.document; H = D.documentElement; } catch(e) { return; }
  // Un solo oyente (en fase de captura): el clic en la pestaña alterna la clase
  // en <html> y NO llega a Streamlit, así la lista se oculta/muestra sin recargar.
  if (P.__pjWlFn) D.removeEventListener('click', P.__pjWlFn, true);
  P.__pjWlFn = function(e){
    if (!(e.target && e.target.closest)) return;
    if (!e.target.closest('.st-key-lista_activos_interruptor button')) return;
    e.stopPropagation(); e.preventDefault();
    H.classList.toggle('pj-lista-activos-oculto');
  };
  D.addEventListener('click', P.__pjWlFn, true);
})();


/* -------------------------------------------------------------------------------------------------------
   -------------------------------------- FIN Piña y Jara lista .JS --------------------------------------
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
