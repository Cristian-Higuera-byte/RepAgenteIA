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
   ------------------------------ INICIO Piña y Jara 95_ubicar_etiquetas .JS -----------------------------
   ------------------------------------------------------------------------------------------------------- */

      /**
       * Bucle de dibujo (una vez por fotograma con requestAnimationFrame): ajusta la capa al tamaño del gráfico, convierte
       * cada precio en altura con la escala de la serie, coloca líneas, etiquetas, insignias y conectores, refresca el
       * editor abierto y apila los recuadros del eje evitando que se pisen con el precio en vivo.
       * No recibe parámetros; modifica el DOM.
       */
      function ubicar(){
        requestAnimationFrame(ubicar);
        if (!serie) return;
        // Tamaño actual del gráfico y sincronización de la capa con su posición.
        var w = containerEl.clientWidth, h = containerEl.clientHeight;
        actualizarMercado();
        capa.style.left = containerEl.offsetLeft + 'px'; capa.style.top = containerEl.offsetTop + 'px';
        capa.style.width = w + 'px'; capa.style.height = h + 'px';
        // Ancho del eje de precios (72 px si la escala no lo informa).
        var eje = 72;
        try { eje = chart.priceScale('right').width() || 72; } catch(e) {}
        // Altura del precio en vivo y lista de recuadros del eje visibles para apilar más abajo.
        var yLive = (BID && serie) ? serie.priceToCoordinate(BID) : null;   // y del recuadro blanco del precio en vivo
        var cajas = [];   // recuadros del eje visibles (para apilarlos sin pisar el blanco)
        // Con el editor abierto se actualizan sus Bid/Ask; si su orden desapareció se cierra.
        if (ed){
          txt(ed.querySelector('.b'), BID ? fmt(BID, DIGITS) : '—');
          txt(ed.querySelector('.a'), ASK ? fmt(ASK, DIGITS) : '—');
          if (!ITEMS[edPrev ? edPrev.id : ''] && edPrev) cerrarEditor();   // la orden se ejecutó o se canceló
        }
        for (var id in nodos){
          var it = ITEMS[id], n = nodos[id];
          if (!it) continue;
          // Por cada elemento: color según el lado, estado de arrastre y precio de entrada efectivo (arrastrado, en edición o real).
          var lado = esCompra(it) ? COMPRA : VENTA;
          var arrPo = drag && drag.id === id && drag.f === 'po';
          var prev = edPrev && edPrev.id === id ? edPrev : null;
          var entrada = arrPo ? drag.px : (prev ? prev.po : precioEntrada(it, n));
          // Línea principal: posiciones con lotes con signo y P/G en vivo; órdenes con tipo, volumen y precio.
          var y0 = serie.priceToCoordinate(entrada), visible;
          if (it.kind === 'pos'){
            visible = colocar(n.main, y0, w, h, eje, lado, (esCompra(it) ? '+' : '-') + fmt(it.v, 2),
                              pgTxt(it.p || 0), (it.p || 0) >= 0 ? COMPRA : VENTA, it.po, false, false);
            n.main.querySelector('.tg').title = TIPO[it.t] + ' ' + fmt(it.v, 2) + ' lote(s) a ' + fmt(it.po, DIGITS);
          } else {
            visible = colocar(n.main, y0, w, h, eje,
                              lado, TIPO[it.t].toUpperCase() + ' ' + fmt(it.v, 2) + (it.oco ? ' · OCO' : ''),
                              'at ' + fmt(entrada, DIGITS), '#c9d1d9', entrada, false, true);
          }
          // Clases de estado: pendiente de confirmación e inválida (precio de entrada mal ubicado).
          var malPo = arrPo && validar(it, 'po', entrada, entrada);
          n.main.className = 'pl ' + (it.kind === 'ord' ? 'po' : 'pm') +
            ((n.pend.po !== undefined || n.pend.del) ? ' pend' : '') + (malPo ? ' mal' : '');
          if (visible) cajas.push({ej: n.main.querySelector('.ej'), y: y0});
          // ys: alturas de las líneas del elemento (para el conector); hay: niveles TP y SL existentes.
          var ys = visible ? [y0] : [], hay = {};
          ['tp', 'sl'].forEach(function(f){
            // Líneas de nivel TP y SL: precio arrastrado, en edición, pendiente o real; se ocultan si no existen.
            var arrastra = drag && drag.id === id && drag.f === f;
            var px = arrastra ? drag.px : (prev ? prev[f] : (f in n.pend ? n.pend[f] : it[f]));
            var el = n[f];
            if (!px){ el.style.display = 'none'; return; }
            hay[f] = true;
            var col = f === 'tp' ? C_TP : C_SL, g = pgEn(it, entrada, px);
            var y = serie.priceToCoordinate(px);
            var etq = f.toUpperCase() + (f === 'sl' && it.tr ? ' auto' : '') + ' ' + fmt(it.v, 2);
            if (f === 'sl') el.querySelector('.x').title = it.tr
              ? 'Gestionado por el stop dinámico (quítalo en Cartera)' : 'Quitar Stop Loss';
            if (colocar(el, y, w, h, eje, col, etq, pgTxt(g),
                        g >= 0 ? COMPRA : VENTA, px, true, false)){ ys.push(y); cajas.push({ej: el.querySelector('.ej'), y: y}); }
            el.className = 'pl lv' + ((f in n.pend) ? ' pend' : '') +
                           (arrastra && validar(it, f, px, entrada) ? ' mal' : '');
          });
          // Insignias TP / SL (solo para los niveles que faltan)
          n.bdTp.style.display = hay.tp ? 'none' : '';
          n.bdSl.style.display = hay.sl ? 'none' : '';
          if (visible && (!hay.tp || !hay.sl) && !n.pend.del){
            n.bds.style.display = '';
            n.bds.style.top = (Math.round(y0) - 11) + 'px';
            n.bds.style.right = (eje + SEP + n.main.querySelector('.tg').offsetWidth + 6) + 'px';
          } else {
            n.bds.style.display = 'none';
          }
          // Conector vertical entre la línea principal y sus niveles (como XM)
          if (ys.length > 1){
            var a = Math.max(0, Math.min.apply(null, ys)), b = Math.min(h, Math.max.apply(null, ys));
            n.con.style.display = '';
            n.con.style.left = (w - eje - 14) + 'px';
            n.con.style.top = a + 'px'; n.con.style.height = (b - a) + 'px';
            n.con.style.borderLeftColor = lado; n.con.style.background = lado;
          } else {
            n.con.style.display = 'none';
          }
        }

        // ---- Apilado del eje (como XM): el recuadro BLANCO del precio en vivo MANDA
        // (se queda en su sitio) y EMPUJA los nuestros, que quedan PEGADOS (sin hueco).
        // Solo se mueve el chip del eje (.ej); la línea y la etiqueta grande siguen en su
        // precio real. Si no hay precio en vivo, cada recuadro queda en su sitio. ----
        // Constante de apilado y estado del precio en vivo (visible solo si cae dentro del área).
        var ALTO = 20;   // = alto del recuadro -> quedan pegados, sin espacio (todos iguales)
        var liveVivo = (yLive !== null && yLive >= 0 && yLive <= h - 10);
        if (liveVivo){
          liveEl.style.display = ''; liveEl.style.width = eje + 'px'; txt(liveEl, fmt(BID, DIGITS));
        } else {
          liveEl.style.display = 'none';
        }
        // Lista ordenada por altura; el recuadro blanco actúa de ancla y los demás se empujan hacia arriba o abajo.
        var lista = cajas.slice();
        if (liveVivo) lista.push({ej: liveEl, y: yLive, ancla: true, abs: true});   // el blanco es el ancla
        lista.sort(function(p, q){ return p.y - q.y; });
        var ia = -1;
        for (var i = 0; i < lista.length; i++){ if (lista[i].ancla){ ia = i; break; } }
        if (ia < 0){
          lista.forEach(function(c){ c.aj = c.y; });              // sin precio en vivo: sin empujar
        } else {
          lista[ia].aj = lista[ia].y;
          for (var i = ia - 1; i >= 0; i--){ lista[i].aj = Math.min(lista[i].y, lista[i + 1].aj - ALTO); }
          for (var i = ia + 1; i < lista.length; i++){ lista[i].aj = Math.max(lista[i].y, lista[i - 1].aj + ALTO); }
        }
        lista.forEach(function(c){
          if (!c.ej) return;
          // Se aplica el desplazamiento vertical calculado a cada recuadro del eje.
          c.ej.style.top = Math.round(c.abs ? c.aj - 10 : -10 + (c.aj - c.y)) + 'px';
        });
      }


/* -------------------------------------------------------------------------------------------------------
   ------------------------------- FIN Piña y Jara 95_ubicar_etiquetas .JS -------------------------------
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
