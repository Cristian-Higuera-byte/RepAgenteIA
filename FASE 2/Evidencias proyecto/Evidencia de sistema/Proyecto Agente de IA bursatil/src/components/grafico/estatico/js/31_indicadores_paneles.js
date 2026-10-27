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
   ---------------------------- INICIO Piña y Jara 31_indicadores_paneles .JS ----------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Indicadores: motor (series sobre el precio, paneles de osciladores, leyenda y actualización)
    // Formato de precio automático: decide los decimales según la magnitud del valor, para indicadores sin escala fija
    var PF_AUTO = {   // decimales según la magnitud del valor: sirve para indicadores sin escala fija (MACD, OBV, ATR…)
      type: 'custom', minMove: 1e-8,
      formatter: function(v){
        var a = Math.abs(v);
        if (a === 0) return '0';
        if (a >= 1000) return v.toFixed(0);
        if (a >= 10) return v.toFixed(2);
        if (a >= 1) return v.toFixed(3);
        return v.toFixed(Math.min(8, 1 + Math.ceil(-Math.log10(a))));
      }
    };
    /**
     * Devuelve el priceFormat de un panel de oscilador según la definición df: el formato automático si dec es auto,
     * o precisión fija de df.dec decimales (2 por defecto).
     */
    function formatoPanel(df){
      if (df.dec === 'auto') return PF_AUTO;
      var n = (typeof df.dec === 'number') ? df.dec : 2;
      return { type: 'price', precision: n, minMove: Math.pow(10, -n) };
    }
    // Formato final de un indicador: el elegido en sus ajustes (Precisión) o el suyo por defecto
    /**
     * Devuelve el priceFormat final de una instancia: la precisión elegida por el usuario en sus ajustes (inst.pr) o,
     * si no hay, la del indicador (en panel) o la del símbolo (sobre el precio).
     */
    function formatoInst(df, inst, enPanel){
      if (inst.pr !== null && inst.pr !== undefined) return { type: 'price', precision: inst.pr, minMove: Math.pow(10, -inst.pr) };
      return enPanel ? formatoPanel(df) : PF;
    }
    /**
     * Da formato de texto al valor v de un indicador para la línea de estado, respetando la precisión elegida, los
     * decimales del panel o los dígitos del símbolo.
     */
    function textoValor(df, inst, v){
      if (inst.pr !== null && inst.pr !== undefined) return v.toFixed(inst.pr);
      if (df.destino !== 'panel') return v.toFixed(DIGITS);
      if (df.dec === 'auto') return PF_AUTO.formatter(v);
      return v.toFixed(typeof df.dec === 'number' ? df.dec : 2);
    }

    // renders: uid de instancia -> { series, panel, capas } con lo que cada indicador tiene dibujado
    var renders = {};   // uid -> { series: [], panel: bool }

    // ---------- Paneles de osciladores ----------
    /**
     * Crea (o reutiliza) el panel de oscilador de la instancia inst: contenedor con título, valores, botones de
     * ajustes y quitar, y un gráfico LightweightCharts propio sincronizado con el principal. Registra el panel en
     * PANES y devuelve su registro.
     */
    function crearPane(inst){
      var id = inst.uid;
      if (PANES[id]) return PANES[id];
      var cont = document.getElementById('osc-panes');
      var tb = document.getElementById('tv-toolbar-left');
      cont.style.marginLeft = (tb ? tb.offsetWidth : 0) + 'px';   // alinea las barras con las del gráfico principal
      cont.style.display = 'flex';
      var el = document.createElement('div'); el.className = 'osc-pane';
      var cuerpo = document.createElement('div'); cuerpo.className = 'osc-cuerpo';
      var tit = document.createElement('div'); tit.className = 'osc-titulo';
      var txt = document.createElement('span'); txt.className = 'osc-nombre'; txt.textContent = tituloInstancia(inst);
      tit.appendChild(txt);
      var vals = document.createElement('span'); vals.className = 'ind-valores'; tit.appendChild(vals);
      var cfg = document.createElement('button'); cfg.className = 'osc-x'; cfg.title = 'Ajustes del indicador'; cfg.textContent = String.fromCharCode(9881);
      cfg.addEventListener('click', function(){ abrirAjustesInd(id); });
      var x = document.createElement('button'); x.className = 'osc-x osc-quitar'; x.title = 'Quitar indicador'; x.textContent = String.fromCharCode(215);
      x.addEventListener('click', function(){ quitarIndicador(id); });
      tit.appendChild(cfg); tit.appendChild(x);
      el.appendChild(cuerpo); el.appendChild(tit); cont.appendChild(el);
      var ch = LightweightCharts.createChart(cuerpo, {
        autoSize: true,
        layout: { background: { color: '#0d1117' }, textColor: '#d1d4dc', fontSize: 11 },
        grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } },
        timeScale: { visible: false },
        rightPriceScale: { borderColor: '#30363d', minimumWidth: 72, scaleMargins: { top: 0.15, bottom: 0.1 } },
        handleScroll: false,
        handleScale: false
      });
      el.addEventListener('dblclick', function(ev){ if (ev.target.tagName !== 'BUTTON') abrirAjustesInd(id); });
      PANES[id] = { el: el, chart: ch, s: {}, txt: txt, vals: vals };
      reajustarPanes();
      var r = chart.timeScale().getVisibleLogicalRange();
      if (r) ch.timeScale().setVisibleLogicalRange(r);
      return PANES[id];
    }

    /**
     * Destruye el panel de oscilador con identificador id (gráfico y elemento DOM), lo borra de PANES, reparte la
     * altura y oculta el contenedor si ya no queda ninguno.
     */
    function quitarPane(id){
      var p = PANES[id];
      if (!p) return;
      p.chart.remove(); p.el.parentNode.removeChild(p.el);
      delete PANES[id];
      reajustarPanes();
      if (!Object.keys(PANES).length) document.getElementById('osc-panes').style.display = 'none';
    }

    // Altura de cada panel: 110 px si hay uno; con varios se reparten ~220 px (mínimo 70) y el contenedor hace scroll
    /**
     * Recalcula la altura de cada panel abierto: 110 px si hay uno y, con varios, se reparten unos 220 px con un
     * mínimo de 70 px.
     */
    function reajustarPanes(){
      var ids = Object.keys(PANES), h = ids.length ? Math.max(70, Math.floor(Math.min(110, 220 / ids.length))) : 0;
      ids.forEach(function(id){ PANES[id].el.style.height = h + 'px'; });
    }

    /**
     * Aplica el rango lógico visible del gráfico principal a todos los paneles de osciladores para que sus barras
     * queden alineadas. Recibe el rango y no hace nada si es nulo.
     */
    function sincronizarPanes(range){
      if (!range) return;
      Object.keys(PANES).forEach(function(id){ PANES[id].chart.timeScale().setVisibleLogicalRange(range); });
    }

    // ---------- Datos de cada capa ----------
    // Una vela = un punto; donde el indicador aún no tiene valor va un punto vacío ({time}) para que los
    // paneles queden alineados con el gráfico principal. `desp` desplaza la línea (positivo = hacia el futuro).
    /**
     * Convierte una capa calculada (vals, cols, desp) en los puntos de la serie: un punto por vela, con punto vacío
     * donde no hay valor para mantener la alineación. El desplazamiento (desp) mueve la línea hacia el futuro
     * extrapolando el tiempo.
     */
    function puntosDeCapa(capa, datos){
      var n = datos.length, d = capa.desp || 0, out = [];
      var dt = n > 1 ? (datos[n-1].time - datos[n-2].time) : 3600, total = n + Math.max(0, d);
      for (var k = 0; k < total; k++){
        var t = k < n ? datos[k].time : datos[n-1].time + (k - n + 1) * dt;
        var s = k - d, v = (s >= 0 && s < n) ? capa.vals[s] : null;
        if (esNum(v)) {
          var pt = { time: t, value: v };
          if (capa.cols && capa.cols[s]) pt.color = capa.cols[s];
          out.push(pt);
        } else if (k < n) {
          out.push({ time: t });
        }
      }
      return out;
    }

    // ---------- Construcción y borrado de lo dibujado ----------
    // Opciones de estilo de una capa (color, grosor, tipo de línea, visibilidad, etiqueta en la escala, formato)
    /**
     * Construye las opciones de estilo de la capa i de una instancia: color, visibilidad, formato de precio y, si es
     * línea, grosor, tipo de trazo y etiqueta en la escala de precios.
     */
    function opcionesEstiloCapa(df, inst, i, enPanel){
      var tipo = df.capas[i][2] || 'linea';
      var etiqueta = inst.et && (df.capas.length === 1 || df.etiq === true) && i === 0;
      var o = { color: colorCapa(inst, i), visible: capaVisible(inst, i), priceFormat: formatoInst(df, inst, enPanel) };
      if (tipo === 'linea') { o.lineWidth = anchoCapa(inst, i); o.lineStyle = estiloLineaCapa(inst, i); o.lastValueVisible = etiqueta; }
      return o;
    }
    /**
     * Crea en el gráfico ch la serie de la capa i (histograma, puntos o línea según su tipo) con su estilo y, en
     * paneles con rango fijo, fija la escala automática de la serie. Devuelve la serie.
     */
    function crearSerieCapa(ch, df, inst, i, enPanel){
      var tipo = df.capas[i][2] || 'linea', op = opcionesEstiloCapa(df, inst, i, enPanel), s;
      if (tipo === 'hist') {
        op.priceLineVisible = false; op.lastValueVisible = false;
        s = ch.addHistogramSeries(op);
      } else if (tipo === 'puntos') {
        op.lineVisible = false; op.pointMarkersVisible = true; op.pointMarkersRadius = enPanel ? 3 : 2;
        op.priceLineVisible = false; op.lastValueVisible = false; op.crosshairMarkerVisible = false;
        s = ch.addLineSeries(op);
      } else {
        op.priceLineVisible = false; op.crosshairMarkerVisible = false;
        s = ch.addLineSeries(op);
      }
      if (enPanel && df.rango) {
        var mn = df.rango[0], mx = df.rango[1];
        s.applyOptions({ autoscaleInfoProvider: function(){ return { priceRange: { minValue: mn, maxValue: mx } }; } });
      }
      return s;
    }

    // Aplica el estilo actual de `inst` a lo que ya está dibujado (sin reconstruirlo)
    /** Aplica el estilo actual de la instancia inst a las series ya dibujadas, sin reconstruirlas. */
    function aplicarEstiloInd(inst){
      var r = renders[inst.uid], df = DEFS[inst.id];
      if (!r) return;
      r.series.forEach(function(s, i){ s.applyOptions(opcionesEstiloCapa(df, inst, i, r.panel)); });
    }

    /**
     * Crea las series de un indicador (en su panel o sobre el gráfico principal), añade las líneas guía de nivel en
     * paneles y devuelve el registro { series, panel, capas } que se guarda en renders.
     */
    function construirRender(inst, capas){
      var df = DEFS[inst.id], enPanel = df.destino === 'panel', series = [], ch;
      if (enPanel) ch = crearPane(inst).chart; else ch = chart;
      for (var i = 0; i < df.capas.length; i++){
        var s = crearSerieCapa(ch, df, inst, i, enPanel);
        if (!enPanel && capas[i] && capas[i].pasos) s.applyOptions({ lineType: LightweightCharts.LineType.WithSteps });
        series.push(s);
      }
      if (enPanel && df.niveles && series.length) {
        // las líneas guía cuelgan de la primera serie del panel
        var base = series[0];
        df.niveles.forEach(function(n){
          base.createPriceLine({ price: n, color: '#8b949e', lineWidth: 1, lineStyle: 2, axisLabelVisible: n !== 0, title: '' });
        });
      }
      return { series: series, panel: enPanel, capas: capas };
    }

    /**
     * Elimina lo dibujado por el indicador de identificador uid (panel completo o series del gráfico principal) y lo
     * borra de renders.
     */
    function quitarRender(uid){
      var r = renders[uid];
      if (!r) return;
      if (r.panel) quitarPane(uid);
      else r.series.forEach(function(s){ try { chart.removeSeries(s); } catch (e) {} });
      delete renders[uid];
    }

    // ---------- Valores en la línea de estado (último dato, o el de la vela bajo el cursor) ----------
    // idxCursor: índice de la vela bajo el cursor (null = usar la última vela)
    var idxCursor = null;
    /**
     * Escribe en la línea de estado de cada indicador el valor de sus capas en la vela bajo el cursor (o en la última
     * si no hay cursor), con el color de cada capa.
     */
    function pintarValoresInd(){
      var n = datosActuales.length;
      if (!n) return;
      var idx = idxCursor === null ? n - 1 : Math.max(0, Math.min(n - 1, idxCursor));
      indActivos.forEach(function(inst){
        var r = renders[inst.uid], df = DEFS[inst.id], cont = refsValores[inst.uid];
        if (!cont) return;
        if (!r || !inst.sl) { cont.textContent = ''; return; }
        var partes = [];
        r.capas.forEach(function(c, i){
          if (!capaVisible(inst, i)) return;
          var s = idx - (c.desp || 0), v = (s >= 0 && s < n) ? c.vals[s] : null;
          if (!esNum(v)) return;
          var col = (c.cols && c.cols[s]) ? c.cols[s] : colorCapa(inst, i);
          partes.push('<span style="color:' + col.replace(/[^#a-zA-Z0-9(),.%]/g, '') + '">' + textoValor(df, inst, v) + '</span>');
        });
        cont.innerHTML = partes.join(' ');
      });
    }
    // refsValores: uid -> elemento HTML donde se escriben los valores (leyenda o título del panel)
    var refsValores = {};   // uid -> elemento donde se escriben los valores (leyenda o título del panel)
    // Al mover el cursor se guarda la vela señalada y se repintan los valores de los indicadores
    chart.subscribeCrosshairMove(function(param){
      var nuevo = (param && param.point && param.logical !== undefined) ? Math.round(param.logical) : null;
      if (nuevo === idxCursor) return;
      idxCursor = nuevo;
      pintarValoresInd();
    });

    // ---------- Leyenda de los indicadores sobre el gráfico ----------
    // firmaLeyendaInd: resumen del estado de la leyenda para evitar reconstruirla si nada cambió
    var firmaLeyendaInd = '';
    /**
     * Reconstruye la leyenda de indicadores sobre el gráfico (nombre, valores y botones mostrar/ocultar, ajustes y
     * quitar) solo si cambió su firma; actualiza también los títulos de los paneles.
     */
    function refrescarLeyendaInd(){
      var cont = document.getElementById('tv-ind-legend');
      if (!cont) return;
      var firma = modoComparar + tfActual + '|' + indActivos.map(function(i){
        return i.uid + tituloInstancia(i) + (i.oculto ? 'o' : '') + (visibleEnTF(i) ? '' : 'x') + (i.c ? i.c.join('') : '') + (i.sl ? 's' : '');
      }).join(',');
      if (firma === firmaLeyendaInd) return;
      firmaLeyendaInd = firma;
      cont.innerHTML = '';
      refsValores = {};
      indActivos.forEach(function(inst){
        var df = DEFS[inst.id];
        if (!df) return;
        if (df.destino === 'panel') { if (PANES[inst.uid]) { PANES[inst.uid].txt.textContent = tituloInstancia(inst); refsValores[inst.uid] = PANES[inst.uid].vals; } return; }
        var apagado = inst.oculto || modoComparar || !visibleEnTF(inst);
        var it = document.createElement('div'); it.className = 'ind-item' + (apagado ? ' apagado' : '');
        var pto = document.createElement('span'); pto.className = 'ind-pto'; pto.style.background = colorCapa(inst, 0);
        var nom = document.createElement('span'); nom.className = 'ind-nom'; nom.textContent = tituloInstancia(inst);
        it.appendChild(pto); it.appendChild(nom);
        var vals = document.createElement('span'); vals.className = 'ind-valores'; it.appendChild(vals);
        refsValores[inst.uid] = vals;
        it.addEventListener('dblclick', function(ev){ ev.stopPropagation(); abrirAjustesInd(inst.uid); });
        /**
         * Auxiliar de refrescarLeyendaInd: crea un botón con texto txt, título titulo y clase opcional cls que
         * ejecuta fn al pulsarse (sin propagar el clic) y lo añade a la fila de la leyenda.
         */
        function boton(txt, titulo, fn, cls){
          var b = document.createElement('button'); b.className = 'ind-btn' + (cls ? ' ' + cls : ''); b.textContent = txt; b.title = titulo;
          b.addEventListener('click', function(ev){ ev.stopPropagation(); fn(); });
          it.appendChild(b);
        }
        boton(inst.oculto ? String.fromCharCode(9675) : String.fromCharCode(9679), inst.oculto ? 'Mostrar' : 'Ocultar', function(){ inst.oculto = !inst.oculto; cambioIndicadores(); });
        boton(String.fromCharCode(9881), 'Ajustes (o doble clic)', function(){ abrirAjustesInd(inst.uid); });
        boton(String.fromCharCode(10005), 'Quitar', function(){ quitarIndicador(inst.uid); }, 'ind-quitar');
        cont.appendChild(it);
      });
      pintarValoresInd();
    }

    // ---------- Altas, bajas y cambios ----------
    /**
     * Guarda la configuración recordada y recalcula/redibuja todos los indicadores activos. Se llama tras cualquier
     * alta, baja o cambio.
     */
    function cambioIndicadores(){
      guardarConfig();
      actualizarIndicadoresActivos();
    }
    /**
     * Añade una instancia nueva del indicador id (con periodo y color distintos si ya existía otra), guarda y
     * redibuja. Devuelve la instancia o null si el id no existe.
     */
    function anadirIndicador(id){
      var df = DEFS[id];
      if (!df) return null;
      var inst = nuevaInstancia(id, null);
      var previos = indActivos.filter(function(i){ return i.id === id; });
      if (df.sug && previos.length) {   // la 2.ª SMA nace con otro periodo para que no se superponga con la 1.ª
        var usados = previos.map(function(i){ return i.p.periodo; });
        for (var k = 0; k < df.sug.length; k++) if (usados.indexOf(df.sug[k]) < 0) { inst.p.periodo = df.sug[k]; break; }
      }
      if (df.capas.length === 1 && previos.length) {
        var col = PALETA_IND[previos.length % PALETA_IND.length];
        if (col !== df.capas[0][1]) inst.c = [col];
      }
      indActivos.push(inst);
      cambioIndicadores();
      return inst;
    }
    /**
     * Elimina la instancia uid de los indicadores activos, quita su dibujo, cierra su ventana de ajustes si estaba
     * abierta y guarda los cambios.
     */
    function quitarIndicador(uid){
      indActivos = indActivos.filter(function(i){ return i.uid !== uid; });
      quitarRender(uid);
      if (typeof cerrarAjustesSiEs === 'function') cerrarAjustesSiEs(uid);
      cambioIndicadores();
    }
    // Cambió un parámetro, color, grosor, visibilidad…: se recalcula y se aplica el estilo sin rehacer los paneles
    /**
     * Tras cambiar un parámetro, color, grosor o visibilidad de inst, aplica el estilo a lo dibujado y recalcula
     * todo.
     */
    function reconstruirIndicador(inst){
      aplicarEstiloInd(inst);
      cambioIndicadores();
    }

    // ---------- Actualización ----------
    /**
     * Recalcula todos los indicadores activos con las velas actuales: crea o quita sus dibujos según visibilidad,
     * temporalidad y modo comparar, vuelca los datos en las series y refresca leyenda y valores.
     */
    function actualizarIndicadoresActivos(){
      var vivos = {};
      indActivos.forEach(function(inst){
        var df = DEFS[inst.id];
        if (!df) return;
        vivos[inst.uid] = true;
        var visible = !inst.oculto && visibleEnTF(inst) && !(df.destino === 'precio' && modoComparar) && datosActuales.length > 0;
        if (!visible) { quitarRender(inst.uid); return; }
        var capas;
        try { capas = df.calc(datosActuales, inst.p); }
        catch (e) { console.error('Indicador ' + inst.id + ':', e); quitarRender(inst.uid); return; }
        var r = renders[inst.uid];
        if (r && r.series.length !== capas.length) { quitarRender(inst.uid); r = null; }
        if (!r) r = renders[inst.uid] = construirRender(inst, capas);
        r.capas = capas;
        capas.forEach(function(c, i){ r.series[i].setData(puntosDeCapa(c, datosActuales)); });
      });
      Object.keys(renders).forEach(function(uid){ if (!vivos[uid]) quitarRender(uid); });
      refrescarLeyendaInd();
      pintarValoresInd();
    }

    // En tiempo real (cada tick) no se recalcula todo cada vez: como mucho una vez cada 0,6 s
    // ultCalcInd: instante del último recálculo; timerInd: temporizador pendiente de la limitación por tick
    var ultCalcInd = 0, timerInd = null;
    /**
     * Versión con limitación para tiempo real: recalcula los indicadores como máximo una vez cada 0,6 s, programando
     * un temporizador si llega otro tick antes.
     */
    function actualizarIndicadoresTick(){
      if (!indActivos.length) return;
      var ahora = Date.now();
      if (ahora - ultCalcInd >= 600) { ultCalcInd = ahora; actualizarIndicadoresActivos(); return; }
      if (!timerInd) timerInd = setTimeout(function(){ timerInd = null; ultCalcInd = Date.now(); actualizarIndicadoresActivos(); }, 600);
    }

    // ---------- Doble clic sobre una línea de indicador (sobre el precio) abre sus ajustes ----------
    /**
     * Busca el indicador sobre el precio cuya línea pasa más cerca (tolerancia de unos 9 px) del punto (x, y) del
     * gráfico. Devuelve el uid del indicador o null.
     */
    function indicadorBajoPunto(x, y){
      var mejor = null, dMejor = 9;   // tolerancia en píxeles
      var k = chart.timeScale().coordinateToLogical(x);
      if (k === null || k === undefined) return null;
      k = Math.round(k);
      indActivos.forEach(function(inst){
        var r = renders[inst.uid], df = DEFS[inst.id];
        if (!r || df.destino !== 'precio') return;
        r.capas.forEach(function(c, i){
          if (!capaVisible(inst, i)) return;
          for (var dk = -1; dk <= 1; dk++){
            var s = k + dk - (c.desp || 0), v = (s >= 0 && s < c.vals.length) ? c.vals[s] : null;
            if (!esNum(v)) continue;
            var py = r.series[i].priceToCoordinate(v);
            if (py === null || py === undefined) continue;
            var dist = Math.abs(py - y) + (dk === 0 ? 0 : 2);
            if (dist < dMejor) { dMejor = dist; mejor = inst.uid; }
          }
        });
      });
      return mejor;
    }
    // Doble clic sobre una línea de indicador: abre sus ajustes (fase de captura para adelantarse a otros manejadores)
    document.getElementById('chart-wrapper').addEventListener('dblclick', function(ev){
      var caja = document.getElementById('c').getBoundingClientRect();
      var uid = indicadorBajoPunto(ev.clientX - caja.left, ev.clientY - caja.top);
      if (uid) { ev.stopPropagation(); ev.preventDefault(); abrirAjustesInd(uid); }
    }, true);

/* -------------------------------------------------------------------------------------------------------
   ------------------------------ FIN Piña y Jara 31_indicadores_paneles .JS -----------------------------
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
