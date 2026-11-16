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
   -------------------------- INICIO Piña y Jara 40_one_click_y_confirmacion .JS -------------------------
   ------------------------------------------------------------------------------------------------------- */

      // TITULO OC INPUT

      // ---------- One-Click Trading: estado del interruptor del ticket ----------
      /**
       * Busca el interruptor One-Click Trading del ticket de órdenes en la página de Streamlit.
       * Devuelve el input o null si el ticket no está en pantalla.
       */
      function unClicInput(){ try { return PD.querySelector('.st-key-orden_un_clic input[type="checkbox"]'); } catch(e){ return null; } }
      // TITULO ONE CLICK

      /**
       * Indica si One-Click Trading está activo (true: las acciones se envían sin confirmar).
       */
      function oneClick(){ var i = unClicInput(); return !!(i && i.checked); }
      // TITULO ALTERNAR ONE CLICK

      /**
       * Alterna el interruptor One-Click del ticket (la primera vez Streamlit pide aceptar los términos).
       * Si el ticket no está visible, muestra un aviso de error.
       */
      function alternarOneClick(){
        var i = unClicInput();
        if (i) i.click();   // mismo interruptor del ticket: la 1.ª vez pide aceptar los términos
        else avisar('Abre el ticket de órdenes para cambiar One-Click Trading', true);
      }

      // TITULO ACCION

      /**
       * Ejecuta fn al instante (One-Click activo) o tras confirmar en una tarjeta sobre el gráfico.
       * Recibe titulo y desc (HTML de la descripción), fn (acción a ejecutar) y alCancelar (se llama si el usuario cancela).
       */
      // Ejecuta `fn` al instante (One-Click) o tras confirmar en el gráfico
      function accion(titulo, desc, fn, alCancelar){
        cerrarConfiguracion(true);
        if (oneClick()){ fn(); return; }
        // Tarjeta de confirmación con los botones Cancelar y Confirmar y el enlace para activar One-Click.
        conf = document.createElement('div'); conf.id = 'pj-configuracion';
        conf.innerHTML = '<div class="t"></div><div class="d"></div><div class="bs">' +
          '<button class="no">Cancelar</button><button class="ok">Confirmar</button></div>' +
          '<div class="h"><a class="oc">Activar One-Click Trading</a> para operar sin confirmar.</div>';
        conf.querySelector('.t').textContent = titulo;
        conf.querySelector('.d').innerHTML = desc;
        // Se guarda el callback de cancelación en la propia tarjeta para ejecutarlo al cerrarla.
        conf._cancelar = alCancelar;
        // Evita que el clic sobre la tarjeta llegue al gráfico (arrastre o zoom).
        conf.addEventListener('mousedown', function(e){ e.stopPropagation(); });
        // Botones: Cancelar cierra y revierte; Confirmar cierra y ejecuta; el enlace activa One-Click.
        conf.querySelector('.no').onclick = function(){ cerrarConfiguracion(true); };
        conf.querySelector('.ok').onclick = function(){ cerrarConfiguracion(false); fn(); };
        conf.querySelector('.oc').onclick = function(){ cerrarConfiguracion(true); alternarOneClick(); };
        capa.appendChild(conf);
      }
      // TITULO CERRAR CONF

      /**
       * Cierra la tarjeta de confirmación si está abierta.
       * Recibe cancelar (true: además ejecuta el callback de cancelación guardado para revertir el cambio visual).
       */
      function cerrarConfiguracion(cancelar){
        if (!conf) return;
        if (cancelar && conf._cancelar) conf._cancelar();
        if (conf.parentNode) conf.parentNode.removeChild(conf);
        conf = null;
      }


/* -------------------------------------------------------------------------------------------------------
   --------------------------- FIN Piña y Jara 40_one_click_y_confirmacion .JS ---------------------------
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
