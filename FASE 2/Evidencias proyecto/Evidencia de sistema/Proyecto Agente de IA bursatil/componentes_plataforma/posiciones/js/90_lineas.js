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
   ----------------------------------- INICIO Piña y Jara 90_lineas .JS ----------------------------------
   ------------------------------------------------------------------------------------------------------- */

      // TITULO CREAR LINEA

      // ---------- Líneas ----------
      /**
       * Crea el nodo DOM de una línea (trazo, etiqueta con lotes, P/G y ✕, y recuadro del eje), oculto por defecto.
       * Recibe clase (por ejemplo 'po', 'pm' o 'lv') y devuelve el elemento ya agregado a la capa.
       */
      function crearLinea(clase){
        var el = document.createElement('div'); el.className = 'pl ' + clase;
        el.innerHTML = '<div class="ln"></div><div class="tg"><span class="vo"></span><span class="pg"></span>' +
                       '<span class="x">&#10005;</span></div><div class="ej"></div>';
        el.style.display = 'none';
        capa.appendChild(el);
        return el;
      }

      // TITULO EMPEZAR

      /**
       * Inicia el arrastre de un nivel (precio de entrada, SL o TP) al pulsar el ratón.
       * Recibe id del elemento, f (campo: 'po', 'sl' o 'tp') y el evento e. Solo con el botón izquierdo; el SL de un stop
       * dinámico no se puede arrastrar y muestra un aviso.
       */
      function empezar(id, f, e){
        if (e.button !== 0) return;
        if (f === 'sl' && ITEMS[id] && ITEMS[id].tr){
          e.preventDefault(); e.stopPropagation();
          avisar('El Stop Loss está en automático (stop dinámico). Para cambiarlo, edita la distancia en Cartera.', true);
          return;
        }
        e.preventDefault(); e.stopPropagation();
        cerrarMenu(); cerrarConfiguracion(true);
        // Estado del arrastre: sin precio todavía, posición vertical inicial y bandera de movimiento real.
        drag = {id: id, f: f, px: null, y0: e.clientY, movido: false};
        document.body.style.cursor = 'ns-resize';
      }

      // TITULO CREAR

      /**
       * Crea todos los nodos de un elemento (posición u orden): línea principal, líneas de TP y SL, conector vertical e
       * insignias TP/SL arrastrables, y conecta sus eventos (✕, arrastre, doble clic y clic derecho).
       * Recibe id y devuelve el objeto de nodos {main, tp, sl, con, bds, pend, ...}.
       */
      function crear(id){
        var it = ITEMS[id];
        // n.pend guarda los cambios pendientes de confirmación (po, sl, tp, del).
        var n = {main: crearLinea(it.kind === 'ord' ? 'po' : 'pm'), tp: crearLinea('lv'), sl: crearLinea('lv'), pend: {}};
        n.con = document.createElement('div'); n.con.className = 'cn'; capa.appendChild(n.con);
        // Insignias arrastrables para añadir un TP o un SL que todavía no existen.
        n.bds = document.createElement('div'); n.bds.className = 'bds';
        n.bds.innerHTML = '<span class="bd" title="Arrastrar para añadir Take Profit">TP</span>' +
                          '<span class="bd" title="Arrastrar para añadir Stop Loss">SL</span>';
        capa.appendChild(n.bds);
        n.bdTp = n.bds.children[0]; n.bdSl = n.bds.children[1];
        n.bdTp.style.color = C_TAKE_PROFIT; n.bdTp.style.borderColor = C_TAKE_PROFIT;
        n.bdSl.style.color = C_STOP_LOSS; n.bdSl.style.borderColor = C_STOP_LOSS;
        n.bdTp.addEventListener('mousedown', function(e){ empezar(id, 'tp', e); });
        n.bdSl.addEventListener('mousedown', function(e){ empezar(id, 'sl', e); });
        // ✕ de la línea principal: en posiciones abre el modal de cierre; en órdenes cancela la orden.
        var x = n.main.querySelector('.x');
        x.addEventListener('mousedown', function(e){ e.stopPropagation(); });
        if (it.kind === 'pos'){
          // ✕ de la posición → modal de cierre (botón invisible de Python, gatillos_cierre)
          x.title = 'Cerrar posición';
          x.addEventListener('click', function(e){
            e.stopPropagation();
            try { var b = PD.querySelector('.st-key-grafico_cerrar_' + it.tk + ' button'); if (b) b.click(); } catch(err) {}
          });
        } else {
          x.title = 'Cancelar orden';
          x.addEventListener('click', function(e){ e.stopPropagation(); cancelarOrden(id); });
          var tgo = n.main.querySelector('.tg');
          tgo.title = 'Arrastrar para mover · doble clic o clic derecho para modificar';
          tgo.addEventListener('mousedown', function(e){ if (e.detail < 2) empezar(id, 'po', e); });
          tgo.addEventListener('dblclick', function(e){ e.stopPropagation(); drag = null; document.body.style.cursor = ''; abrirEditor(id); });
          tgo.addEventListener('contextmenu', function(e){ menuOrden(e, id); });
        }
        ['tp', 'sl'].forEach(function(f){
          // Niveles TP y SL existentes: la ✕ los quita y la etiqueta se arrastra para moverlos.
          var lv = n[f], lx = lv.querySelector('.x');
          lx.title = 'Quitar ' + NOMBRE[f];
          lx.addEventListener('mousedown', function(e){ e.stopPropagation(); });
          lx.addEventListener('click', function(e){
            e.stopPropagation();
            // SL en automático (stop dinámico): el motor lo repone enseguida, así que
            // quitarlo desde aquí no sirve (reaparece). Se bloquea como el arrastre.
            if (f === 'sl' && ITEMS[id] && ITEMS[id].tr){
              avisar('El Stop Loss está en automático (stop dinámico). Para quitarlo, desactiva el stop dinámico en Cartera.', true);
              return;
            }
            cambiarNivel(id, f, 0);
          });
          lv.querySelector('.tg').title = 'Arrastrar para mover el ' + NOMBRE[f];
          lv.querySelector('.tg').addEventListener('mousedown', function(e){ empezar(id, f, e); });
        });
        return n;
      }

      // TITULO BORRAR

      /**
       * Elimina del DOM todos los nodos de un elemento y lo quita de `nodos`. Recibe id.
       */
      function borrar(id){
        var n = nodos[id];
        [n.main, n.tp, n.sl, n.con, n.bds].forEach(function(el){ if (el.parentNode) el.parentNode.removeChild(el); });
        delete nodos[id];
      }

      // TITULO UNIR

      /**
       * Reconstruye ITEMS uniendo POS y ORD (con claves 'p'+ticket y 'o'+ticket), crea los nodos de los elementos nuevos y
       * borra los de los que ya no existen.
       */
      // Une posiciones y órdenes en ITEMS y crea/borra sus líneas
      function unir(){
        var nuevo = {};
        for (var a in POSICION){ POSICION[a].kind = 'pos'; POSICION[a].tk = a; nuevo['p' + a] = POSICION[a]; }
        for (var b in ORDEN){ ORDEN[b].kind = 'ord'; ORDEN[b].tk = b; nuevo['o' + b] = ORDEN[b]; }
        ITEMS = nuevo;
        for (var id in nodos){ if (!ITEMS[id]) borrar(id); }
        for (var id2 in ITEMS){ if (!nodos[id2]) nodos[id2] = crear(id2); }
      }

      // TITULO MOVER

      /**
       * Durante un arrastre actualiza el precio propuesto a partir de la posición vertical del ratón (e).
       * Ignora movimientos menores a 4 px para distinguir un clic de un arrastre.
       */
      function mover(e){
        if (!drag || !serie) return;
        if (!drag.movido && Math.abs(e.clientY - drag.y0) < 4) return;   // un clic no es un arrastre
        drag.movido = true;
        var r = containerEl.getBoundingClientRect();
        var px = serie.coordinateToPrice(e.clientY - r.top);
        if (px !== null) drag.px = redondear(px);
      }
      // TITULO SOLTAR

      /**
       * Termina el arrastre. Recibe cancelar (true: descarta el cambio). Si hubo movimiento, el precio cambió y es
       * válido, llama a cambiarNivel(); si no es válido, avisa el motivo.
       */
      function soltar(cancelar){
        if (!drag) return;
        var d = drag; drag = null;
        document.body.style.cursor = '';
        var it = ITEMS[d.id];
        if (cancelar || !it || d.px === null || !d.movido) return;
        var actual = d.f === 'po' ? precioEntrada(it, nodos[d.id]) : (+it[d.f] || 0);
        if (redondear(actual) === d.px) return;                          // mismo precio: nada que enviar
        var motivo = validar(it, d.f, d.px, precioEntrada(it, nodos[d.id]));
        if (motivo){ avisar('No válido: ' + motivo, true); return; }
        cambiarNivel(d.id, d.f, d.px);
      }
      // Seguimiento global del ratón: si se soltó fuera del gráfico se cancela; si no, se actualiza el arrastre.
      document.addEventListener('mousemove', function(e){
        if (!drag) return;
        if (e.buttons === 0){ soltar(true); return; }   // se soltó fuera del gráfico
        mover(e);
      });
      // Soltar el botón confirma el arrastre.
      document.addEventListener('mouseup', function(){ soltar(false); });
      // Escape cancela el arrastre y cierra menú, tarjeta de confirmación y editor.
      document.addEventListener('keydown', function(e){
        if (e.key === 'Escape'){ soltar(true); cerrarMenu(); cerrarConfiguracion(true); cerrarEditor(); }
      });

      // TITULO COLOCAR

      /**
       * Coloca una línea en la altura y (píxeles) y rellena sus textos y colores.
       * Recibe el nodo el, y, ancho w y alto h de la capa, ancho del eje, color col, texto de lotes vo, texto de P/G pg y
       * su color pgCol, precio para el recuadro del eje pxEje, nivel (true para TP/SL: solo contorno) y esOrden.
       * Devuelve true si la línea es visible (dentro del área) y false si queda oculta.
       */
      // Dibuja una línea en la altura del precio dado
      function colocar(el, y, w, h, eje, col, vo, pg, gananciaPerdidaColumna, precioEje, nivel, esOrden){
        if (y === null || y < 0 || y > h - 28){ el.style.display = 'none'; return false; }
        el.style.display = '';
        el.style.top = Math.round(y) + 'px';
        el.style.width = w + 'px';
        var ln = el.querySelector('.ln'), v = el.querySelector('.vo'), g = el.querySelector('.pg'),
            x = el.querySelector('.x'), ej = el.querySelector('.ej'), tg = el.querySelector('.tg');
        // ORDEN PENDIENTE: borde punteado en etiqueta y recuadro (como su línea), relleno intacto.
        var ord = esOrden && !nivel, bs = ord ? 'dashed' : 'solid';
        ln.style.width = (w - eje) + 'px';
        ln.style.borderTopColor = col;
        tg.style.right = (eje + SEPARADOR) + 'px';
        txt(v, vo);
        if (nivel){ v.style.background = '#161b22'; v.style.color = col; v.style.borderColor = col; }
        else { v.style.background = col; v.style.color = '#fff';
               v.style.borderColor = ord ? '#0d1117' : col; }   // punteado oscuro visible sobre el relleno
        v.style.borderStyle = bs;
        txt(g, pg);
        g.style.color = gananciaPerdidaColumna;
        g.style.borderColor = col; g.style.borderStyle = bs;
        x.style.borderColor = col; x.style.borderLeftColor = '#30363d'; x.style.borderStyle = bs;
        // Recuadro del eje: posiciones/órdenes RELLENO; niveles TP/SL solo CONTORNO
        // (como XM: así el TP/SL no se confunde con una posición). Las órdenes pendientes
        // llevan el borde punteado para distinguirse de las posiciones abiertas.
        ej.style.width = eje + 'px';
        if (nivel){ ej.style.background = '#0d1117'; ej.style.color = col;
                    ej.style.boxShadow = 'inset 0 0 0 1.5px ' + col; ej.style.border = 'none'; }
        else { ej.style.background = col; ej.style.color = '#fff'; ej.style.boxShadow = 'none';
               ej.style.border = ord ? '1.5px dashed #0d1117' : 'none'; }
        txt(ej, fmt(precioEje, DIGITS));
        return true;
      }
      // TITULO PG TXT

      /**
       * Formatea una ganancia o pérdida con signo, dos decimales y la moneda (USD).
       */
      function gananciaPerdidaTexto(v){ return (v >= 0 ? '+' : '') + fmt(v, 2) + ' USD'; }

      // Cada frame: alturas (zoom, desplazamiento, autoescala) y arrastres

/* -------------------------------------------------------------------------------------------------------
   ------------------------------------ FIN Piña y Jara 90_lineas .JS ------------------------------------
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
