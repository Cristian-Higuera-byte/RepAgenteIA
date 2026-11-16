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
    // TITULO FORMATO PANEL

    /**
     * Devuelve el priceFormat de un panel de oscilador según la definición df: el formato automático si dec es auto,
     * o precisión fija de df.dec decimales (2 por defecto).
     */
    function formatoPanel(tablaDatos){
      if (tablaDatos.dec === 'auto') return PF_AUTO;
      var n = (typeof tablaDatos.dec === 'number') ? tablaDatos.dec : 2;
      return { type: 'price', precision: n, minMove: Math.pow(10, -n) };
    }
    // TITULO FORMATO INST

    // Formato final de un indicador: el elegido en sus ajustes (Precisión) o el suyo por defecto
    /**
     * Devuelve el priceFormat final de una instancia: la precisión elegida por el usuario en sus ajustes (inst.pr) o,
     * si no hay, la del indicador (en panel) o la del símbolo (sobre el precio).
     */
    function formatoInst(tablaDatos, inst, enPanel){
      if (inst.pr !== null && inst.pr !== undefined) return { type: 'price', precision: inst.pr, minMove: Math.pow(10, -inst.pr) };
      return enPanel ? formatoPanel(tablaDatos) : PF;
    }
    // TITULO TEXTO VALOR

    /**
     * Da formato de texto al valor v de un indicador para la línea de estado, respetando la precisión elegida, los
     * decimales del panel o los dígitos del símbolo.
     */
    function textoValor(tablaDatos, inst, v){
      if (inst.pr !== null && inst.pr !== undefined) return v.toFixed(inst.pr);
      if (tablaDatos.destino !== 'panel') return v.toFixed(DIGITS);
      if (tablaDatos.dec === 'auto') return PF_AUTO.formatter(v);
      return v.toFixed(typeof tablaDatos.dec === 'number' ? tablaDatos.dec : 2);
    }

    // renders: uid de instancia -> { series, panel, capas } con lo que cada indicador tiene dibujado
    var renders = {};   // uid -> { series: [], panel: bool }

    // TITULO CREAR PANE

    // ---------- Paneles de osciladores ----------
    /**
     * Crea (o reutiliza) el panel de oscilador de la instancia inst: contenedor con título, valores, botones de
     * ajustes y quitar, y un gráfico LightweightCharts propio sincronizado con el principal. Registra el panel en
     * PANES y devuelve su registro.
     */
    function crearPanel(inst){
      var id = inst.uid;
      if (PANELES[id]) return PANELES[id];
      var cont = document.getElementById('osc-paneles');
      var tb = document.getElementById('tradingview-barra-herramientas-izquierda');
      cont.style.marginLeft = (tb ? tb.offsetWidth : 0) + 'px';   // alinea las barras con las del gráfico principal
      cont.style.display = 'flex';
      var el = document.createElement('div'); el.className = 'osc-panel';
      var cuerpo = document.createElement('div'); cuerpo.className = 'osc-cuerpo';
      var tit = document.createElement('div'); tit.className = 'osc-titulo';
      var txt = document.createElement('span'); txt.className = 'osc-nombre'; txt.textContent = tituloInstancia(inst);
      tit.appendChild(txt);
      var vals = document.createElement('span'); vals.className = 'indicador-valores'; tit.appendChild(vals);
      var configuracion = document.createElement('button'); configuracion.className = 'osc-x'; configuracion.title = 'Ajustes del indicador'; configuracion.textContent = String.fromCharCode(9881);
      configuracion.addEventListener('click', function(){ abrirAjustesIndicador(id); });
      var x = document.createElement('button'); x.className = 'osc-x osc-quitar'; x.title = 'Quitar indicador'; x.textContent = String.fromCharCode(215);
      x.addEventListener('click', function(){ quitarIndicador(id); });
      tit.appendChild(configuracion); tit.appendChild(x);
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
      el.addEventListener('dblclick', function(ev){ if (ev.target.tagName !== 'BUTTON') abrirAjustesIndicador(id); });
      PANELES[id] = { el: el, chart: ch, s: {}, txt: txt, vals: vals };
      reajustarPaneles();
      var r = chart.timeScale().getVisibleLogicalRange();
      if (r) ch.timeScale().setVisibleLogicalRange(r);
      return PANELES[id];
    }

    // TITULO QUITAR PANE

    /**
     * Destruye el panel de oscilador con identificador id (gráfico y elemento DOM), lo borra de PANES, reparte la
     * altura y oculta el contenedor si ya no queda ninguno.
     */
    function quitarPanel(id){
      var p = PANELES[id];
      if (!p) return;
      p.chart.remove(); p.el.parentNode.removeChild(p.el);
      delete PANELES[id];
      reajustarPaneles();
      if (!Object.keys(PANELES).length) document.getElementById('osc-paneles').style.display = 'none';
    }

    // TITULO REAJUSTAR PANES

    // Altura de cada panel: 110 px si hay uno; con varios se reparten ~220 px (mínimo 70) y el contenedor hace scroll
    /**
     * Recalcula la altura de cada panel abierto: 110 px si hay uno y, con varios, se reparten unos 220 px con un
     * mínimo de 70 px.
     */
    function reajustarPaneles(){
      var ids = Object.keys(PANELES), h = ids.length ? Math.max(70, Math.floor(Math.min(110, 220 / ids.length))) : 0;
      ids.forEach(function(id){ PANELES[id].el.style.height = h + 'px'; });
    }

    // TITULO SINCRONIZAR PANES

    /**
     * Aplica el rango lógico visible del gráfico principal a todos los paneles de osciladores para que sus barras
     * queden alineadas. Recibe el rango y no hace nada si es nulo.
     */
    function sincronizarPaneles(range){
      if (!range) return;
      Object.keys(PANELES).forEach(function(id){ PANELES[id].chart.timeScale().setVisibleLogicalRange(range); });
    }

    // TITULO PUNTOS DE CAPA

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
        if (esNumero(v)) {
          var pt = { time: t, value: v };
          if (capa.cols && capa.cols[s]) pt.color = capa.cols[s];
          out.push(pt);
        } else if (k < n) {
          out.push({ time: t });
        }
      }
      return out;
    }

    // TITULO OPCIONES ESTILO CAPA

    // ---------- Construcción y borrado de lo dibujado ----------
    // Opciones de estilo de una capa (color, grosor, tipo de línea, visibilidad, etiqueta en la escala, formato)
    /**
     * Construye las opciones de estilo de la capa i de una instancia: color, visibilidad, formato de precio y, si es
     * línea, grosor, tipo de trazo y etiqueta en la escala de precios.
     */
    function opcionesEstiloCapa(tablaDatos, inst, i, enPanel){
      var tipo = tablaDatos.capas[i][2] || 'linea';
      var etiqueta = inst.et && (tablaDatos.capas.length === 1 || tablaDatos.etiq === true) && i === 0;
      var o = { color: colorCapa(inst, i), visible: capaVisible(inst, i), priceFormat: formatoInst(tablaDatos, inst, enPanel) };
      if (tipo === 'linea') { o.lineWidth = anchoCapa(inst, i); o.lineStyle = estiloLineaCapa(inst, i); o.lastValueVisible = etiqueta; }
      return o;
    }
    // TITULO CREAR SERIE CAPA

    /**
     * Crea en el gráfico ch la serie de la capa i (histograma, puntos o línea según su tipo) con su estilo y, en
     * paneles con rango fijo, fija la escala automática de la serie. Devuelve la serie.
     */
    function crearSerieCapa(ch, tablaDatos, inst, i, enPanel){
      var tipo = tablaDatos.capas[i][2] || 'linea', op = opcionesEstiloCapa(tablaDatos, inst, i, enPanel), s;
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
      if (enPanel && tablaDatos.rango) {
        var mn = tablaDatos.rango[0], mx = tablaDatos.rango[1];
        s.applyOptions({ autoscaleInfoProvider: function(){ return { priceRange: { minValue: mn, maxValue: mx } }; } });
      }
      return s;
    }

    // TITULO APLICAR ESTILO IND

    // Aplica el estilo actual de `inst` a lo que ya está dibujado (sin reconstruirlo)
    /** Aplica el estilo actual de la instancia inst a las series ya dibujadas, sin reconstruirlas. */
    function aplicarEstiloIndicador(inst){
      var r = renders[inst.uid], tablaDatos = DEFS[inst.id];
      if (!r) return;
      r.series.forEach(function(s, i){ s.applyOptions(opcionesEstiloCapa(tablaDatos, inst, i, r.panel)); });
    }

    // TITULO CONSTRUIR RENDER

    /**
     * Crea las series de un indicador (en su panel o sobre el gráfico principal), añade las líneas guía de nivel en
     * paneles y devuelve el registro { series, panel, capas } que se guarda en renders.
     */
    function construirDibujar(inst, capas){
      var tablaDatos = DEFS[inst.id], enPanel = tablaDatos.destino === 'panel', series = [], ch;
      if (enPanel) ch = crearPanel(inst).chart; else ch = chart;
      for (var i = 0; i < tablaDatos.capas.length; i++){
        var s = crearSerieCapa(ch, tablaDatos, inst, i, enPanel);
        if (!enPanel && capas[i] && capas[i].pasos) s.applyOptions({ lineType: LightweightCharts.LineType.WithSteps });
        series.push(s);
      }
      if (enPanel && tablaDatos.niveles && series.length) {
        // las líneas guía cuelgan de la primera serie del panel
        var base = series[0];
        tablaDatos.niveles.forEach(function(n){
          base.createPriceLine({ price: n, color: '#8b949e', lineWidth: 1, lineStyle: 2, axisLabelVisible: n !== 0, title: '' });
        });
      }
      return { series: series, panel: enPanel, capas: capas };
    }

    // TITULO QUITAR RENDER

    /**
     * Elimina lo dibujado por el indicador de identificador uid (panel completo o series del gráfico principal) y lo
     * borra de renders.
     */
    function quitarDibujar(uid){
      var r = renders[uid];
      if (!r) return;
      if (r.panel) quitarPanel(uid);
      else r.series.forEach(function(s){ try { chart.removeSeries(s); } catch (e) {} });
      delete renders[uid];
    }

    // ---------- Valores en la línea de estado (último dato, o el de la vela bajo el cursor) ----------
    // idxCursor: índice de la vela bajo el cursor (null = usar la última vela)
    var indiceCursor = null;
    // TITULO PINTAR VALORES IND

    /**
     * Escribe en la línea de estado de cada indicador el valor de sus capas en la vela bajo el cursor (o en la última
     * si no hay cursor), con el color de cada capa.
     */
    function pintarValoresIndicador(){
      var n = datosActuales.length;
      if (!n) return;
      var idx = indiceCursor === null ? n - 1 : Math.max(0, Math.min(n - 1, indiceCursor));
      indicadorActivos.forEach(function(inst){
        var r = renders[inst.uid], tablaDatos = DEFS[inst.id], cont = refsValores[inst.uid];
        if (!cont) return;
        if (!r || !inst.sl) { cont.textContent = ''; return; }
        var partes = [];
        r.capas.forEach(function(c, i){
          if (!capaVisible(inst, i)) return;
          var s = idx - (c.desp || 0), v = (s >= 0 && s < n) ? c.vals[s] : null;
          if (!esNumero(v)) return;
          var col = (c.cols && c.cols[s]) ? c.cols[s] : colorCapa(inst, i);
          partes.push('<span style="color:' + col.replace(/[^#a-zA-Z0-9(),.%]/g, '') + '">' + textoValor(tablaDatos, inst, v) + '</span>');
        });
        cont.innerHTML = partes.join(' ');
      });
    }
    // refsValores: uid -> elemento HTML donde se escriben los valores (leyenda o título del panel)
    var refsValores = {};   // uid -> elemento donde se escriben los valores (leyenda o título del panel)
    // Al mover el cursor se guarda la vela señalada y se repintan los valores de los indicadores
    chart.subscribeCrosshairMove(function(parametro){
      var nuevo = (parametro && parametro.point && parametro.logical !== undefined) ? Math.round(parametro.logical) : null;
      if (nuevo === indiceCursor) return;
      indiceCursor = nuevo;
      pintarValoresIndicador();
    });

    // ---------- Leyenda de los indicadores sobre el gráfico ----------
    // firmaLeyendaInd: resumen del estado de la leyenda para evitar reconstruirla si nada cambió
    var firmaLeyendaIndicador = '';
    // TITULO REFRESCAR LEYENDA IND

    /**
     * Reconstruye la leyenda de indicadores sobre el gráfico (nombre, valores y botones mostrar/ocultar, ajustes y
     * quitar) solo si cambió su firma; actualiza también los títulos de los paneles.
     */
    function refrescarLeyendaIndicador(){
      var cont = document.getElementById('tradingview-indicador-leyenda');
      if (!cont) return;
      var firma = modoComparar + temporalidadActual + '|' + indicadorActivos.map(function(i){
        return i.uid + tituloInstancia(i) + (i.oculto ? 'o' : '') + (visibleEnTemporalidad(i) ? '' : 'x') + (i.c ? i.c.join('') : '') + (i.sl ? 's' : '');
      }).join(',');
      if (firma === firmaLeyendaIndicador) return;
      firmaLeyendaIndicador = firma;
      cont.innerHTML = '';
      refsValores = {};
      indicadorActivos.forEach(function(inst){
        var tablaDatos = DEFS[inst.id];
        if (!tablaDatos) return;
        if (tablaDatos.destino === 'panel') { if (PANELES[inst.uid]) { PANELES[inst.uid].txt.textContent = tituloInstancia(inst); refsValores[inst.uid] = PANELES[inst.uid].vals; } return; }
        var apagado = inst.oculto || modoComparar || !visibleEnTemporalidad(inst);
        var it = document.createElement('div'); it.className = 'indicador-elemento' + (apagado ? ' apagado' : '');
        var pto = document.createElement('span'); pto.className = 'indicador-punto'; pto.style.background = colorCapa(inst, 0);
        var nom = document.createElement('span'); nom.className = 'indicador-nombre'; nom.textContent = tituloInstancia(inst);
        it.appendChild(pto); it.appendChild(nom);
        var vals = document.createElement('span'); vals.className = 'indicador-valores'; it.appendChild(vals);
        refsValores[inst.uid] = vals;
        it.addEventListener('dblclick', function(ev){ ev.stopPropagation(); abrirAjustesIndicador(inst.uid); });
        /**
         * Auxiliar de refrescarLeyendaInd: crea un botón con texto txt, título titulo y clase opcional cls que
         * ejecuta fn al pulsarse (sin propagar el clic) y lo añade a la fila de la leyenda.
         */
        function boton(txt, titulo, fn, cls){
          var b = document.createElement('button'); b.className = 'indicador-boton' + (cls ? ' ' + cls : ''); b.textContent = txt; b.title = titulo;
          b.addEventListener('click', function(ev){ ev.stopPropagation(); fn(); });
          it.appendChild(b);
        }
        boton(inst.oculto ? String.fromCharCode(9675) : String.fromCharCode(9679), inst.oculto ? 'Mostrar' : 'Ocultar', function(){ inst.oculto = !inst.oculto; cambioIndicadores(); });
        boton(String.fromCharCode(9881), 'Ajustes (o doble clic)', function(){ abrirAjustesIndicador(inst.uid); });
        boton(String.fromCharCode(10005), 'Quitar', function(){ quitarIndicador(inst.uid); }, 'indicador-quitar');
        cont.appendChild(it);
      });
      pintarValoresIndicador();
    }

    // TITULO CAMBIO INDICADORES

    // ---------- Altas, bajas y cambios ----------
    /**
     * Guarda la configuración recordada y recalcula/redibuja todos los indicadores activos. Se llama tras cualquier
     * alta, baja o cambio.
     */
    function cambioIndicadores(){
      guardarConfiguracion();
      actualizarIndicadoresActivos();
    }
    // TITULO ANADIR INDICADOR

    /**
     * Añade una instancia nueva del indicador id (con periodo y color distintos si ya existía otra), guarda y
     * redibuja. Devuelve la instancia o null si el id no existe.
     */
    function anadirIndicador(id){
      var tablaDatos = DEFS[id];
      if (!tablaDatos) return null;
      // El plan limita cuántos indicadores puede haber a la vez en el gráfico
      if (PLAN.indicadores != null && indicadorActivos.length >= PLAN.indicadores) { avisoPlan(PLAN.mensajes.indicadores); return null; }
      var inst = nuevaInstancia(id, null);
      var previos = indicadorActivos.filter(function(i){ return i.id === id; });
      if (tablaDatos.sug && previos.length) {   // la 2.ª SMA nace con otro periodo para que no se superponga con la 1.ª
        var usados = previos.map(function(i){ return i.p.periodo; });
        for (var k = 0; k < tablaDatos.sug.length; k++) if (usados.indexOf(tablaDatos.sug[k]) < 0) { inst.p.periodo = tablaDatos.sug[k]; break; }
      }
      if (tablaDatos.capas.length === 1 && previos.length) {
        var col = PALETA_INDICADOR[previos.length % PALETA_INDICADOR.length];
        if (col !== tablaDatos.capas[0][1]) inst.c = [col];
      }
      indicadorActivos.push(inst);
      cambioIndicadores();
      return inst;
    }
    // TITULO QUITAR INDICADOR

    /**
     * Elimina la instancia uid de los indicadores activos, quita su dibujo, cierra su ventana de ajustes si estaba
     * abierta y guarda los cambios.
     */
    function quitarIndicador(uid){
      indicadorActivos = indicadorActivos.filter(function(i){ return i.uid !== uid; });
      quitarDibujar(uid);
      if (typeof cerrarAjustesSiEs === 'function') cerrarAjustesSiEs(uid);
      cambioIndicadores();
    }
    // TITULO RECONSTRUIR INDICADOR

    // Cambió un parámetro, color, grosor, visibilidad…: se recalcula y se aplica el estilo sin rehacer los paneles
    /**
     * Tras cambiar un parámetro, color, grosor o visibilidad de inst, aplica el estilo a lo dibujado y recalcula
     * todo.
     */
    function reconstruirIndicador(inst){
      aplicarEstiloIndicador(inst);
      cambioIndicadores();
    }

    // TITULO ACTUALIZAR INDICADORES ACTIVOS

    // ---------- Actualización ----------
    /**
     * Recalcula todos los indicadores activos con las velas actuales: crea o quita sus dibujos según visibilidad,
     * temporalidad y modo comparar, vuelca los datos en las series y refresca leyenda y valores.
     */
    function actualizarIndicadoresActivos(){
      var vivos = {};
      indicadorActivos.forEach(function(inst){
        var tablaDatos = DEFS[inst.id];
        if (!tablaDatos) return;
        vivos[inst.uid] = true;
        var visible = !inst.oculto && visibleEnTemporalidad(inst) && !(tablaDatos.destino === 'precio' && modoComparar) && datosActuales.length > 0;
        if (!visible) { quitarDibujar(inst.uid); return; }
        var capas;
        try { capas = tablaDatos.calc(datosActuales, inst.p); }
        catch (e) { console.error('Indicador ' + inst.id + ':', e); quitarDibujar(inst.uid); return; }
        var r = renders[inst.uid];
        if (r && r.series.length !== capas.length) { quitarDibujar(inst.uid); r = null; }
        if (!r) r = renders[inst.uid] = construirDibujar(inst, capas);
        r.capas = capas;
        capas.forEach(function(c, i){ r.series[i].setData(puntosDeCapa(c, datosActuales)); });
      });
      Object.keys(renders).forEach(function(uid){ if (!vivos[uid]) quitarDibujar(uid); });
      refrescarLeyendaIndicador();
      pintarValoresIndicador();
    }

    // En tiempo real (cada tick) no se recalcula todo cada vez: como mucho una vez cada 0,6 s
    // ultCalcInd: instante del último recálculo; timerInd: temporizador pendiente de la limitación por tick
    var ultimoCalcIndicador = 0, temporizadorIndicador = null;
    // TITULO ACTUALIZAR INDICADORES TICK

    /**
     * Versión con limitación para tiempo real: recalcula los indicadores como máximo una vez cada 0,6 s, programando
     * un temporizador si llega otro tick antes.
     */
    function actualizarIndicadoresTick(){
      if (!indicadorActivos.length) return;
      var ahora = Date.now();
      if (ahora - ultimoCalcIndicador >= 600) { ultimoCalcIndicador = ahora; actualizarIndicadoresActivos(); return; }
      if (!temporizadorIndicador) temporizadorIndicador = setTimeout(function(){ temporizadorIndicador = null; ultimoCalcIndicador = Date.now(); actualizarIndicadoresActivos(); }, 600);
    }

    // TITULO INDICADOR BAJO PUNTO

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
      indicadorActivos.forEach(function(inst){
        var r = renders[inst.uid], tablaDatos = DEFS[inst.id];
        if (!r || tablaDatos.destino !== 'precio') return;
        r.capas.forEach(function(c, i){
          if (!capaVisible(inst, i)) return;
          for (var dk = -1; dk <= 1; dk++){
            var s = k + dk - (c.desp || 0), v = (s >= 0 && s < c.vals.length) ? c.vals[s] : null;
            if (!esNumero(v)) continue;
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
    document.getElementById('grafico-contenedor').addEventListener('dblclick', function(ev){
      var caja = document.getElementById('c').getBoundingClientRect();
      var uid = indicadorBajoPunto(ev.clientX - caja.left, ev.clientY - caja.top);
      if (uid) { ev.stopPropagation(); ev.preventDefault(); abrirAjustesIndicador(uid); }
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
