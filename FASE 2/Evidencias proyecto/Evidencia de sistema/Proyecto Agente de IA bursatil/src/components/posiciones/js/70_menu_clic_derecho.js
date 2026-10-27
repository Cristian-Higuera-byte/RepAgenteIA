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
   ----------------------------- INICIO Piña y Jara 70_menu_clic_derecho .JS -----------------------------
   ------------------------------------------------------------------------------------------------------- */

      // ---------- Menú del clic derecho ----------
      /**
       * Cierra el menú contextual abierto (si lo hay) y libera la referencia compartida `menu`.
       */
      function cerrarMenu(){ if (menu && menu.parentNode) menu.parentNode.removeChild(menu); menu = null; }
      // Oyente (en fase de captura) del clic derecho sobre el gráfico: reemplaza el menú del navegador por uno propio
      // que ofrece crear una orden pendiente en el precio del cursor y alternar One-Click Trading.
      /**
       * Maneja el clic derecho: calcula el precio bajo el cursor, decide qué órdenes pendientes son válidas y dibuja el menú.
       * Recibe el evento e (posición del cursor).
       */
      containerEl.addEventListener('contextmenu', function(e){
        e.preventDefault();
        if (!serie) return;
        cerrarMenu();
        // Posición del cursor relativa al contenedor del gráfico y precio correspondiente (redondeado a los decimales del símbolo).
        var r = containerEl.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
        var px = serie.coordinateToPrice(y);
        if (px === null) return;
        px = redondear(px);
        // Volumen del ticket, lista de opciones válidas (ops) y estado de One-Click.
        var vol = volumenTicket(), ops = [], oc = oneClick();
        // Bajo el mercado: Buy Limit o Sell Stop; sobre el mercado: Sell Limit o Buy Stop; dentro del spread: ninguna.
        if (BID && ASK){
          if (px < BID - SM) ops = [['Buy Limit', COMPRA, '▲'], ['Sell Stop', VENTA, '▼']];
          else if (px > ASK + SM) ops = [['Sell Limit', VENTA, '▼'], ['Buy Stop', COMPRA, '▲']];
        }
        // Se arma el HTML del menú: título con el precio, opciones (o aviso) y el interruptor One-Click.
        menu = document.createElement('div'); menu.id = 'pj-menu';
        var h = '<div class="tit">' + REAL + ' · ' + fmt(px, DIGITS) + '</div>';
        if (ops.length){
          ops.forEach(function(o, i){
            h += '<div class="it" data-i="' + i + '"><span class="ic" style="color:' + o[1] + '">' + o[2] + '</span>' +
                 o[0] + ' ' + fmt(vol, 2) + '<span class="px">' + fmt(px, DIGITS) + '</span></div>';
          });
        } else {
          h += '<div class="it dis"><span class="ic">·</span>' + (BID ? 'Precio dentro del spread' : 'Sin precio en vivo') + '</div>';
        }
        h += '<div class="sep"></div><div class="it" data-oc="1"><span class="ic" style="color:#ff8f00">' +
             (oc ? '✓' : '⚡') + '</span>One-Click Trading<span class="px">' + (oc ? 'ON' : 'OFF') + '</span></div>';
        // Posición del menú, limitada para que no se salga del gráfico.
        menu.innerHTML = h;
        menu.style.left = Math.max(0, Math.min(x, containerEl.clientWidth - 250)) + 'px';
        menu.style.top = Math.max(0, Math.min(y, containerEl.clientHeight - 150)) + 'px';
        // El menú no debe iniciar arrastres del gráfico; al pulsar una opción se cierra y se ejecuta su acción.
        menu.addEventListener('mousedown', function(ev){ ev.stopPropagation(); });
        menu.addEventListener('click', function(ev){
          var it = ev.target.closest('.it');
          if (!it || it.classList.contains('dis')) return;
          cerrarMenu();
          if (it.getAttribute('data-oc')){ alternarOneClick(); return; }
          nuevaOrden(ops[+it.getAttribute('data-i')][0], px);
        });
        capa.appendChild(menu);
      }, true);
      // Cualquier clic fuera del menú lo cierra.
      document.addEventListener('mousedown', function(){ cerrarMenu(); });


/* -------------------------------------------------------------------------------------------------------
   ------------------------------- FIN Piña y Jara 70_menu_clic_derecho .JS ------------------------------
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
