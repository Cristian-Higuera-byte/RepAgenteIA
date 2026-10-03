(function(){
  var CONFIG = window.TRADING_CHART_CONFIG || {};
  var API = CONFIG.apiUrl || __API_URL_JS__;
  var SIMBOLO = CONFIG.symbol || __SIMBOLO_JS__;
  var DIGITS = Number.isFinite(CONFIG.digits)
    ? CONFIG.digits
    : __DIGITS__;
  var PIP = Number.isFinite(CONFIG.pipSize)
    ? CONFIG.pipSize
    : __PIP__;
  var TICK_SIZE = Number.isFinite(CONFIG.tickSize)
    ? CONFIG.tickSize
    : Math.pow(10, -DIGITS);

  var PF = { type: 'price', precision: DIGITS, minMove: TICK_SIZE };

  var tfActual = "H1";
  var nBarrasActual = 1500;
  var tipoActual = "candlestick";
  var datosActuales = [];

  var cargaId = 0;
  var cargando = false;
  var pollEnCurso = false;

  var indicadores = { sma20: false, sma50: false, ema20: false, bollinger: false, rsi: false };
  var seriesInd = { sma20: null, sma50: null, ema20: null, bolsuper: null, bolmedia: null, bolinf: null };

  var chartRsi = null;
  var serieRsi = null;

  function iniciar(){
    if(!window.LightweightCharts){ setTimeout(iniciar, 60); return; }

    var containerEl = document.getElementById('c');
    var chart = LightweightCharts.createChart(containerEl, {
      autoSize: true,
      layout: { background: { color: '#0d1117' }, textColor: '#d1d4dc', fontSize: 12 },
      grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } },
      timeScale: { borderColor: '#30363d', timeVisible: true, secondsVisible: false },
      rightPriceScale: { borderColor: '#30363d', minimumWidth: 72 },
      crosshair: { mode: 0 }
    });

    var serie = null;
    var serieVolumen = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'vol',
      color: 'rgba(63,185,80,0.5)'
    });
    chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });

    function crearSerie(tipo){
      if (serie) { chart.removeSeries(serie); }
      if (tipo === "candlestick") {
        serie = chart.addCandlestickSeries({ priceFormat: PF, upColor:'#3fb950', downColor:'#f85149', borderUpColor:'#3fb950', borderDownColor:'#f85149', wickUpColor:'#3fb950', wickDownColor:'#f85149' });
      } else if (tipo === "hollow") {
        serie = chart.addCandlestickSeries({ priceFormat: PF, upColor:'transparent', downColor:'#f85149', borderUpColor:'#3fb950', borderDownColor:'#f85149', wickUpColor:'#3fb950', wickDownColor:'#f85149' });
      } else if (tipo === "bars") {
        serie = chart.addBarSeries({ priceFormat: PF, upColor: '#3fb950', downColor: '#f85149' });
      } else if (tipo === "line") {
        serie = chart.addLineSeries({ priceFormat: PF, color: '#3fb950', lineWidth: 2 });
      } else if (tipo === "area") {
        serie = chart.addAreaSeries({ priceFormat: PF, lineColor:'#3fb950', lineWidth:2, topColor:'rgba(63,185,80,0.4)', bottomColor:'rgba(63,185,80,0.0)' });
      } else if (tipo === "heikin") {
        serie = chart.addCandlestickSeries({ priceFormat: PF, upColor:'#3fb950', downColor:'#f85149', borderUpColor:'#3fb950', borderDownColor:'#f85149', wickUpColor:'#3fb950', wickDownColor:'#f85149' });
      }
      if (serie) {
        serie.priceScale().applyOptions({ scaleMargins: { top: 0.08, bottom: 0.22 } });
      }
    }

    crearSerie(tipoActual);

    // ==========================================================================
    // SISTEMA DE DIBUJO PROFESIONAL CON MENÚ FLOTANTE DE LÍNEAS
    // ==========================================================================
    var canvas = document.getElementById('drawing-canvas');
    var ctx = canvas.getContext('2d');
    var wrapEl = document.getElementById('chart-wrapper');
    var activeTool = 'cross';
    var bloqueado = false;
    var imanActivo = true;

    var seleccionadoId = null;
    var hoverId = null;
    var dibujoEnCurso = null;
    var esperandoSegundoClick = false;
    var inicioClick = null;
    var arrastre = null;

    var NIVELES_FIB = [
      { val: 0.0,   color: '#f85149' }, { val: 0.236, color: '#ff9800' },
      { val: 0.382, color: '#f5c518' }, { val: 0.5,   color: '#3fb950' },
      { val: 0.618, color: '#58a6ff' }, { val: 0.786, color: '#a78bfa' },
      { val: 1.0,   color: '#f85149' }
    ];

    var estiloCursor = document.createElement('style');
    estiloCursor.textContent =
      '#chart-wrapper.cur-mover, #chart-wrapper.cur-mover * { cursor: move !important; }' +
      '#chart-wrapper.cur-punto, #chart-wrapper.cur-punto * { cursor: pointer !important; }' +
      '#chart-wrapper.cur-dibujar, #chart-wrapper.cur-dibujar * { cursor: crosshair !important; }';
    document.head.appendChild(estiloCursor);
    function setCursor(cls){
      wrapEl.classList.remove('cur-mover', 'cur-punto', 'cur-dibujar');
      if (cls) wrapEl.classList.add(cls);
    }

    var storageKey = 'dibujos_' + SIMBOLO;
    var elementosDibujados = [];
    try {
      var guardados = localStorage.getItem(storageKey);
      if (guardados) { elementosDibujados = JSON.parse(guardados); }
    } catch(e) { elementosDibujados = []; }

    var historial = [JSON.stringify(elementosDibujados)];
    var posHist = 0;

    function guardarDibujosLocal() {
      try { localStorage.setItem(storageKey, JSON.stringify(elementosDibujados)); } catch(e) {}
    }
    function confirmarCambio(){
      historial = historial.slice(0, posHist + 1);
      historial.push(JSON.stringify(elementosDibujados));
      if (historial.length > 60) historial.shift();
      posHist = historial.length - 1;
      guardarDibujosLocal();
      redibujarTodo();
    }
    function restaurarHistorial(){
      elementosDibujados = JSON.parse(historial[posHist]);
      seleccionadoId = null; hoverId = null;
      guardarDibujosLocal();
      redibujarTodo();
    }
    function deshacer(){ if (posHist > 0) { posHist--; restaurarHistorial(); } }
    function rehacer(){ if (posHist < historial.length - 1) { posHist++; restaurarHistorial(); } }

    var cssW = 0, cssH = 0;
    var sucio = true;

    function redibujarTodo(){ sucio = true; }

    function resizeCanvas() {
      var dpr = window.devicePixelRatio || 1;
      cssW = wrapEl.clientWidth;
      cssH = wrapEl.clientHeight;
      canvas.width = Math.max(1, Math.round(cssW * dpr));
      canvas.height = Math.max(1, Math.round(cssH * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      redibujarTodo();
    }

    if (window.ResizeObserver) {
      new ResizeObserver(resizeCanvas).observe(wrapEl);
    } else {
      window.addEventListener('resize', resizeCanvas);
    }
    resizeCanvas();

    function areaTrazado(){
      var anchoEje = 60, altoEje = 28;
      try { anchoEje = chart.priceScale('right').width(); } catch (e) {}
      try { altoEje = chart.timeScale().height(); } catch (e) {}
      return { w: Math.max(0, cssW - anchoEje), h: Math.max(0, cssH - altoEje) };
    }

    chart.timeScale().subscribeVisibleLogicalRangeChange(function(range){
      redibujarTodo();
      if (chartRsi && range) chartRsi.timeScale().setVisibleLogicalRange(range);
    });

    function ok(){
      for (var i = 0; i < arguments.length; i++){
        var v = arguments[i];
        if (v === null || v === undefined || typeof v !== 'number' || !isFinite(v)) return false;
      }
      return true;
    }

    var cacheSeg = { n: -1, t: -1, v: 60 };
    function segBarra(){
      var n = datosActuales.length;
      if (n < 2) return 60;
      var tUlt = datosActuales[n - 1].time;
      if (cacheSeg.n === n && cacheSeg.t === tUlt) return cacheSeg.v;
      var difs = [];
      for (var i = Math.max(1, n - 60); i < n; i++){
        var d = datosActuales[i].time - datosActuales[i - 1].time;
        if (d > 0) difs.push(d);
      }
      difs.sort(function(a, b){ return a - b; });
      cacheSeg = { n: n, t: tUlt, v: difs.length ? difs[Math.floor(difs.length / 2)] : 60 };
      return cacheSeg.v;
    }

    function tiempoALogico(t){
      var n = datosActuales.length;
      if (!n || typeof t !== 'number' || !isFinite(t)) return null;
      var seg = segBarra();
      var primero = datosActuales[0].time, ultimo = datosActuales[n - 1].time;
      if (t <= primero) return (t - primero) / seg;
      if (t >= ultimo) return (n - 1) + (t - ultimo) / seg;
      var lo = 0, hi = n - 1;
      while (hi - lo > 1){
        var mid = (lo + hi) >> 1;
        if (datosActuales[mid].time <= t) lo = mid; else hi = mid;
      }
      var t0 = datosActuales[lo].time, t1 = datosActuales[hi].time;
      return lo + (t - t0) / (t1 - t0);
    }

    function logicoATiempo(l){
      var n = datosActuales.length;
      if (!n || typeof l !== 'number' || !isFinite(l)) return null;
      var seg = segBarra();
      if (l <= 0) return datosActuales[0].time + l * seg;
      if (l >= n - 1) return datosActuales[n - 1].time + (l - (n - 1)) * seg;
      var i = Math.floor(l);
      var t0 = datosActuales[i].time, t1 = datosActuales[i + 1].time;
      return t0 + (l - i) * (t1 - t0);
    }

    function xDeTiempo(t){
      var l = tiempoALogico(t);
      if (l === null) return null;
      return chart.timeScale().logicalToCoordinate(l);
    }
    function yDePrecio(p){
      if (!serie || typeof p !== 'number') return null;
      return serie.priceToCoordinate(p);
    }

    function magnetEfectivo(e){ return imanActivo !== !!(e && e.ctrlKey); }

    function puntoDesdeMouse(x, y, conIman){
      if (!serie || !datosActuales.length) return null;
      var l = chart.timeScale().coordinateToLogical(x);
      var p = serie.coordinateToPrice(y);
      if (l === null || p === null) return null;
      if (conIman){
        var i = Math.round(l);
        if (i >= 0 && i < datosActuales.length){
          var v = datosActuales[i];
          var mejor = null, mejorD = 14;
          [v.open, v.high, v.low, v.close].forEach(function(cand){
            var cy = serie.priceToCoordinate(cand);
            if (cy !== null){
              var d = Math.abs(cy - y);
              if (d < mejorD){ mejorD = d; mejor = cand; }
            }
          });
          l = i;
          if (mejor !== null) p = mejor;
        }
      }
      var t = logicoATiempo(l);
      if (t === null) return null;
      return { l: l, time: t, price: p };
    }

    // --------------------------------------------------------------------------
    // Motor geométrico de herramientas de dibujo
    // --------------------------------------------------------------------------
    function puntoVisual(el, n){
      var t = el['time' + n], p = el['price' + n];
      return { x: xDeTiempo(t), y: yDePrecio(p) };
    }

    function geom(el){
      if (el.tipo === 'hline') return { y: yDePrecio(el.price) };
      if (el.tipo === 'vline') return { x: xDeTiempo(el.time) };
      if (el.tipo === 'text') return { x: xDeTiempo(el.time), y: yDePrecio(el.price) };
      if (el.tipo === 'crossline') return { x: xDeTiempo(el.time), y: yDePrecio(el.price) };
      var g = {};
      for (var n = 1; n <= 3; n++) {
        if (el['time' + n] === undefined) break;
        var q = puntoVisual(el, n);
        g['x' + n] = q.x; g['y' + n] = q.y;
      }
      if (!ok(g.x1, g.y1, g.x2, g.y2)) return null;
      return g;
    }

    function distSeg(px, py, x1, y1, x2, y2){
      var dx = x2 - x1, dy = y2 - y1;
      var l2 = dx * dx + dy * dy;
      var t = l2 ? ((px - x1) * dx + (py - y1) * dy) / l2 : 0;
      t = Math.max(0, Math.min(1, t));
      return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
    }

    function distanciaLineaInfinita(px, py, x1, y1, x2, y2){
      var dx = x2 - x1, dy = y2 - y1;
      var den = Math.hypot(dx, dy) || 1;
      return Math.abs(dy * px - dx * py + x2 * y1 - y2 * x1) / den;
    }

    function offsetCanal(g){
      if (!ok(g.x3, g.y3)) return { dx: 0, dy: g.y2 - g.y1 };
      var dx = g.x2 - g.x1, dy = g.y2 - g.y1;
      var len = Math.hypot(dx, dy) || 1;
      var nx = -dy / len, ny = dx / len;
      var signed = ((g.x3 - g.x1) * nx) + ((g.y3 - g.y1) * ny);
      return { dx: nx * signed, dy: ny * signed };
    }

    function hitTest(el, x, y, seleccionado){
      var g = geom(el);
      if (!g) return null;
      if (el.tipo === 'hline') return Math.abs(y - g.y) <= 6 ? 'body' : null;
      if (el.tipo === 'vline') return Math.abs(x - g.x) <= 6 ? 'body' : null;
      if (el.tipo === 'crossline') return (Math.abs(x - g.x) <= 6 || Math.abs(y - g.y) <= 6) ? 'body' : null;
      if (el.tipo === 'text'){
        ctx.font = '13px sans-serif';
        var w = ctx.measureText(el.texto || 'Texto').width;
        return (x >= g.x - 4 && x <= g.x + w + 4 && y >= g.y - 16 && y <= g.y + 6) ? 'body' : null;
      }
      if (seleccionado){
        if (Math.hypot(x - g.x1, y - g.y1) <= 10) return 'p1';
        if (Math.hypot(x - g.x2, y - g.y2) <= 10) return 'p2';
        if (ok(g.x3, g.y3) && Math.hypot(x - g.x3, y - g.y3) <= 10) return 'p3';
      }
      if (['trend','ray','extended','angle','arrow'].indexOf(el.tipo) >= 0){
        return distSeg(x, y, g.x1, g.y1, g.x2, g.y2) <= 7 ? 'body' : null;
      }
      if (el.tipo === 'hray'){
        if (x < g.x1 - 6) return null;
        return Math.abs(y - g.y1) <= 7 ? 'body' : null;
      }
      if (el.tipo === 'channel'){
        var off = offsetCanal(g);
        var d1 = distSeg(x, y, g.x1, g.y1, g.x2, g.y2);
        var d2 = distSeg(x, y, g.x1 + off.dx, g.y1 + off.dy, g.x2 + off.dx, g.y2 + off.dy);
        return Math.min(d1, d2) <= 7 ? 'body' : null;
      }
      if (el.tipo === 'fib_channel'){
        var oc = offsetCanal(g);
        for (var fc = 0; fc < FIB_CHANNEL_LEVELS.length; fc++){
          var lv = FIB_CHANNEL_LEVELS[fc].val;
          var lx1 = g.x1 + oc.dx * lv, ly1 = g.y1 + oc.dy * lv;
          var lx2 = g.x2 + oc.dx * lv, ly2 = g.y2 + oc.dy * lv;
          if (distSeg(x, y, lx1, ly1, lx2, ly2) <= 6) return 'body';
        }
        return null;
      }
      var xa = Math.min(g.x1, g.x2), xb = Math.max(g.x1, g.x2);
      var ya = Math.min(g.y1, g.y2), yb = Math.max(g.y1, g.y2);
      if (el.tipo === 'measure' || el.tipo === 'rectangle' || el.tipo === 'ellipse' || el.tipo === 'triangle'){
        return (x >= xa - 7 && x <= xb + 7 && y >= ya - 7 && y <= yb + 7) ? 'body' : null;
      }
      if (el.tipo === 'fib' || el.tipo === 'fib_extension'){
        if (x < xa - 8 || x > xb + 8) return null;
        var niveles = el.tipo === 'fib' ? NIVELES_FIB : NIVELES_FIB_EXT;
        for (var i = 0; i < niveles.length; i++){
          var yn = el.tipo === 'fib'
            ? g.y1 + (g.y2 - g.y1) * niveles[i].val
            : (ok(g.y3) ? g.y3 + (g.y2 - g.y1) * niveles[i].val : g.y1 + (g.y2 - g.y1) * niveles[i].val);
          if (Math.abs(y - yn) <= 6) return 'body';
        }
        return null;
      }
      return null;
    }

    function elementoBajo(x, y){
      if (seleccionadoId !== null && elementosDibujados[seleccionadoId]){
        var h = hitTest(elementosDibujados[seleccionadoId], x, y, true);
        if (h) return { idx: seleccionadoId, parte: h };
      }
      for (var i = elementosDibujados.length - 1; i >= 0; i--){
        var h2 = hitTest(elementosDibujados[i], x, y, false);
        if (h2) return { idx: i, parte: h2 };
      }
      return null;
    }

    function dibujarHandle(c, x, y, col){
      if (!ok(x,y)) return;
      c.save(); c.fillStyle = '#ffffff'; c.strokeStyle = col; c.lineWidth = 2;
      c.beginPath(); c.arc(x, y, 5, 0, 2 * Math.PI); c.fill(); c.stroke(); c.restore();
    }

    function dibujarLinea(c, x1, y1, x2, y2, col, width, dash){
      c.strokeStyle = col; c.lineWidth = width || 2; c.lineCap = 'round';
      if (dash) c.setLineDash(dash);
      c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke();
      if (dash) c.setLineDash([]);
    }

    function dibujarElemento(c, el, sel, hov){
      var g = geom(el); if (!g) return;
      c.save();
      var hoverExtra = (hov && !sel) ? 1 : 0;

      if (el.tipo === 'trend'){
        var col = el.color || '#2962ff'; dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,col,(el.ancho||2)+hoverExtra);
        if (sel){ dibujarHandle(c,g.x1,g.y1,col); dibujarHandle(c,g.x2,g.y2,col); }

      } else if (el.tipo === 'ray'){
        var colR = el.color || '#2962ff'; var dx = g.x2-g.x1, dy = g.y2-g.y1;
        var extX = cssW + 500; var extY = g.y1 + (dx !== 0 ? dy/dx*(extX-g.x1) : 0);
        dibujarLinea(c,g.x1,g.y1,extX,extY,colR,(el.ancho||2)+hoverExtra);
        if(sel){dibujarHandle(c,g.x1,g.y1,colR);dibujarHandle(c,g.x2,g.y2,colR);}

      } else if (el.tipo === 'extended'){
        var colE = el.color || '#2962ff'; var ddx=g.x2-g.x1, ddy=g.y2-g.y1;
        if (Math.abs(ddx) < 0.001){ dibujarLinea(c,g.x1,0,g.x1,cssH,colE,(el.ancho||2)+hoverExtra); }
        else { var slope=ddy/ddx; dibujarLinea(c,0,g.y1-slope*g.x1,cssW,g.y1+slope*(cssW-g.x1),colE,(el.ancho||2)+hoverExtra); }
        if(sel){dibujarHandle(c,g.x1,g.y1,colE);dibujarHandle(c,g.x2,g.y2,colE);}

      } else if (el.tipo === 'angle'){
        var colA=el.color||'#a78bfa'; dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,colA,(el.ancho||2)+hoverExtra);
        var base=Math.atan2(0,1), ang=Math.atan2(-(g.y2-g.y1),g.x2-g.x1)*180/Math.PI;
        c.font='11px sans-serif'; c.fillStyle=colA; c.fillText((ang>=0?'+':'')+ang.toFixed(1)+'°',g.x2+7,g.y2-7);
        if(sel){dibujarHandle(c,g.x1,g.y1,colA);dibujarHandle(c,g.x2,g.y2,colA);}

      } else if (el.tipo === 'hline'){
        var colH=el.color||'#f5c518'; dibujarLinea(c,0,g.y,cssW,g.y,colH,(el.ancho||1.5)+hoverExtra,[6,4]);
        if(sel){c.fillStyle=colH;c.fillRect(0,g.y-4,6,8);}

      } else if (el.tipo === 'hray'){
        var colHR=el.color||'#f5c518'; dibujarLinea(c,g.x1,g.y1,cssW,g.y1,colHR,(el.ancho||1.5)+hoverExtra);
        if(sel)dibujarHandle(c,g.x1,g.y1,colHR);

      } else if (el.tipo === 'vline'){
        var colV=el.color||'#58a6ff'; dibujarLinea(c,g.x,0,g.x,cssH,colV,1.5,[4,4]);
        if(sel){c.fillStyle=colV;c.fillRect(g.x-4,0,8,6);}

      } else if (el.tipo === 'crossline'){
        var colX=el.color||'#8b949e'; dibujarLinea(c,g.x,0,g.x,cssH,colX,1,[4,4]); dibujarLinea(c,0,g.y,cssW,g.y,colX,1,[4,4]);
        if(sel)dibujarHandle(c,g.x,g.y,colX);

      } else if (el.tipo === 'channel'){
        var colC=el.color||'#2962ff', oc=offsetCanal(g);
        c.globalAlpha=.08;c.fillStyle=colC;c.beginPath();c.moveTo(g.x1,g.y1);c.lineTo(g.x2,g.y2);c.lineTo(g.x2+oc.dx,g.y2+oc.dy);c.lineTo(g.x1+oc.dx,g.y1+oc.dy);c.closePath();c.fill();c.globalAlpha=1;
        dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,colC,2+hoverExtra);dibujarLinea(c,g.x1+oc.dx,g.y1+oc.dy,g.x2+oc.dx,g.y2+oc.dy,colC,2+hoverExtra);
        if(sel){dibujarHandle(c,g.x1,g.y1,colC);dibujarHandle(c,g.x2,g.y2,colC);dibujarHandle(c,g.x3,g.y3,colC);}

      } else if (el.tipo === 'fib'){
        var xa=Math.min(g.x1,g.x2), xb=Math.max(g.x1,g.x2), dY=g.y2-g.y1, dP=el.price2-el.price1;
        var nv=NIVELES_FIB.map(function(n){return {n:n,y:g.y1+dY*n.val,precio:el.price1+dP*n.val};});
        c.globalAlpha=.07; for(var fi=0;fi<nv.length-1;fi++){c.fillStyle=nv[fi+1].n.color;c.fillRect(xa,Math.min(nv[fi].y,nv[fi+1].y),xb-xa,Math.abs(nv[fi+1].y-nv[fi].y));} c.globalAlpha=1;
        c.font='11px sans-serif'; nv.forEach(function(q){c.strokeStyle=q.n.color;c.fillStyle=q.n.color;c.beginPath();c.moveTo(xa,q.y);c.lineTo(xb,q.y);c.stroke();c.fillText(String(+q.n.val.toFixed(3))+' ('+q.precio.toFixed(DIGITS)+')',xa+5,q.y-3);});
        dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,'rgba(139,148,158,.8)',1,[4,4]);
        if(sel){dibujarHandle(c,g.x1,g.y1,'#a78bfa');dibujarHandle(c,g.x2,g.y2,'#a78bfa');}

      } else if (el.tipo === 'fib_extension'){
        var exa=Math.min(g.x1,g.x2,g.x3), exb=Math.max(g.x1,g.x2,g.x3), baseDy=g.y2-g.y1;
        c.font='11px sans-serif';
        NIVELES_FIB_EXT.forEach(function(n){
          var yy=g.y3+baseDy*n.val;
          c.strokeStyle=n.color;c.fillStyle=n.color;c.beginPath();c.moveTo(exa,yy);c.lineTo(cssW,yy);c.stroke();
          var precio=el.price3+(el.price2-el.price1)*n.val;
          c.fillText(String(n.val)+' ('+precio.toFixed(DIGITS)+')',Math.max(4,exa+5),yy-3);
        });
        dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,'rgba(139,148,158,.8)',1,[4,4]);
        dibujarLinea(c,g.x2,g.y2,g.x3,g.y3,'rgba(139,148,158,.8)',1,[4,4]);
        if(sel){dibujarHandle(c,g.x1,g.y1,'#a78bfa');dibujarHandle(c,g.x2,g.y2,'#a78bfa');dibujarHandle(c,g.x3,g.y3,'#a78bfa');}

      } else if (el.tipo === 'fib_channel'){
        var ocf=offsetCanal(g); c.font='11px sans-serif';
        FIB_CHANNEL_LEVELS.forEach(function(n){
          var f=n.val, x1=g.x1+ocf.dx*f, y1=g.y1+ocf.dy*f, x2=g.x2+ocf.dx*f, y2=g.y2+ocf.dy*f;
          dibujarLinea(c,x1,y1,x2,y2,n.color,1.2);
          c.fillStyle=n.color;c.fillText(String(n.val),Math.min(x1,x2)+5,Math.min(y1,y2)-4);
        });
        dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,'rgba(139,148,158,.9)',2,[4,4]);
        dibujarLinea(c,g.x1+ocf.dx,g.y1+ocf.dy,g.x2+ocf.dx,g.y2+ocf.dy,'rgba(139,148,158,.7)',1,[4,4]);
        if(sel){dibujarHandle(c,g.x1,g.y1,'#a78bfa');dibujarHandle(c,g.x2,g.y2,'#a78bfa');dibujarHandle(c,g.x3,g.y3,'#a78bfa');}

      } else if (el.tipo === 'rectangle'){
        var colG=el.color||'#58a6ff'; var rw=g.x2-g.x1,rh=g.y2-g.y1;
        c.globalAlpha=.08;c.fillStyle=colG;c.fillRect(Math.min(g.x1,g.x2),Math.min(g.y1,g.y2),Math.abs(rw),Math.abs(rh));c.globalAlpha=1;
        c.strokeStyle=colG;c.lineWidth=2+hoverExtra;c.strokeRect(Math.min(g.x1,g.x2),Math.min(g.y1,g.y2),Math.abs(rw),Math.abs(rh));
        if(sel){dibujarHandle(c,g.x1,g.y1,colG);dibujarHandle(c,g.x2,g.y2,colG);}

      } else if (el.tipo === 'ellipse'){
        var colEl=el.color||'#58a6ff'; var cx=(g.x1+g.x2)/2,cy=(g.y1+g.y2)/2,rx=Math.abs(g.x2-g.x1)/2,ry=Math.abs(g.y2-g.y1)/2;
        c.globalAlpha=.08;c.fillStyle=colEl;c.beginPath();c.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);c.fill();c.globalAlpha=1;c.strokeStyle=colEl;c.lineWidth=2+hoverExtra;c.beginPath();c.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);c.stroke();
        if(sel){dibujarHandle(c,g.x1,g.y1,colEl);dibujarHandle(c,g.x2,g.y2,colEl);}

      } else if (el.tipo === 'triangle'){
        var colT=el.color||'#58a6ff'; var tx1=g.x1,ty1=g.y1,tx2=g.x2,ty2=g.y2,tx3=g.x1,ty3=g.y2;
        c.globalAlpha=.08;c.fillStyle=colT;c.beginPath();c.moveTo(tx1,ty1);c.lineTo(tx2,ty2);c.lineTo(tx3,ty3);c.closePath();c.fill();c.globalAlpha=1;c.strokeStyle=colT;c.lineWidth=2+hoverExtra;c.beginPath();c.moveTo(tx1,ty1);c.lineTo(tx2,ty2);c.lineTo(tx3,ty3);c.closePath();c.stroke();
        if(sel){dibujarHandle(c,g.x1,g.y1,colT);dibujarHandle(c,g.x2,g.y2,colT);}

      } else if (el.tipo === 'arrow'){
        var colAr=el.color||'#3fb950';dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,colAr,2+hoverExtra);var a=Math.atan2(g.y2-g.y1,g.x2-g.x1),hs=10;
        c.fillStyle=colAr;c.beginPath();c.moveTo(g.x2,g.y2);c.lineTo(g.x2-hs*Math.cos(a-Math.PI/6),g.y2-hs*Math.sin(a-Math.PI/6));c.lineTo(g.x2-hs*Math.cos(a+Math.PI/6),g.y2-hs*Math.sin(a+Math.PI/6));c.closePath();c.fill();
        if(sel){dibujarHandle(c,g.x1,g.y1,colAr);dibujarHandle(c,g.x2,g.y2,colAr);}

      } else if (el.tipo === 'text'){
        c.font='13px sans-serif';c.fillStyle=el.color||'#ffffff';c.fillText(el.texto||'Texto',g.x,g.y);
        if(sel||hov){var tw=c.measureText(el.texto||'Texto').width;c.strokeStyle='rgba(88,166,255,.8)';c.lineWidth=1;c.setLineDash([3,3]);c.strokeRect(g.x-4,g.y-16,tw+8,22);c.setLineDash([]);}

      } else if (el.tipo === 'measure'){
        var sube=el.price2>=el.price1,colM=sube?'#2962ff':'#f23645',mw=g.x2-g.x1,mh=g.y2-g.y1;
        c.globalAlpha=.15;c.fillStyle=colM;c.fillRect(g.x1,g.y1,mw,mh);c.globalAlpha=1;c.strokeStyle=colM;c.lineWidth=1;c.strokeRect(g.x1,g.y1,mw,mh);
        var l1=tiempoALogico(el.time1),l2=tiempoALogico(el.time2),barras=(l1===null||l2===null)?0:Math.abs(Math.round(l2-l1));
        var dif=el.price2-el.price1,pct=el.price1?(dif/el.price1)*100:0,textoDif=PIP>0?(dif/PIP).toFixed(1)+' pips':dif.toFixed(DIGITS);
        var txt=(dif>=0?'+':'')+textoDif+' ('+(pct>=0?'+':'')+pct.toFixed(2)+'%) · '+barras+' barras';c.font='12px sans-serif';var pw=c.measureText(txt).width+16,px0=(g.x1+g.x2)/2-pw/2,py0=sube?Math.min(g.y1,g.y2)-28:Math.max(g.y1,g.y2)+8;
        c.fillStyle=colM;c.fillRect(px0,py0,pw,20);c.fillStyle='#fff';c.textBaseline='middle';c.fillText(txt,px0+8,py0+10);
        if(sel){dibujarHandle(c,g.x1,g.y1,colM);dibujarHandle(c,g.x2,g.y2,colM);}
      }
      c.restore();
    }

    function fmtTiempo(t){
      var d=new Date(t*1000); function p(n){return (n<10?'0':'')+n;}
      return p(d.getUTCDate())+'/'+p(d.getUTCMonth()+1)+' '+p(d.getUTCHours())+':'+p(d.getUTCMinutes());
    }

    function badgePrecio(c,y,precio,fondo,texto,ap){
      if(!ok(y)||y<0||y>ap.h)return;var w=cssW-ap.w;c.save();c.fillStyle=fondo;c.fillRect(ap.w,y-10,w,20);c.fillStyle=texto;c.font='11px sans-serif';c.textBaseline='middle';c.textAlign='left';c.fillText(precio.toFixed(DIGITS),ap.w+6,y);c.restore();
    }
    function badgeTiempo(c,x,t,fondo,ap){
      var h=cssH-ap.h;if(!ok(x)||x<0||x>ap.w||h<10)return;var w=92,bx=Math.max(0,Math.min(ap.w-w,x-w/2));c.save();c.fillStyle=fondo;c.fillRect(bx,ap.h,w,h);c.fillStyle='#fff';c.font='11px sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillText(fmtTiempo(t),bx+w/2,ap.h+h/2);c.restore();
    }
    function etiquetasEje(c,el,ap){
      if(el.tipo==='hline'){badgePrecio(c,yDePrecio(el.price),el.price,el.color||'#f5c518','#fff',ap);return;}
      if(el.tipo==='vline'){badgeTiempo(c,xDeTiempo(el.time),el.time,el.color||'#58a6ff',ap);return;}
      if(el.tipo==='hray'){badgePrecio(c,yDePrecio(el.price1),el.price1,el.color||'#f5c518','#fff',ap);return;}
      if(el.tipo==='crossline'){badgePrecio(c,yDePrecio(el.price),el.price,el.color||'#8b949e','#fff',ap);badgeTiempo(c,xDeTiempo(el.time),el.time,el.color||'#8b949e',ap);return;}
      if(el.tipo==='text')return;
      var col=el.tipo.indexOf('fib')===0?'#7c5cd6':(el.tipo==='measure'?(el.price2>=el.price1?'#2962ff':'#f23645'):(el.color||'#2962ff'));
      if(el.price1!==undefined)badgePrecio(c,yDePrecio(el.price1),el.price1,col,'#fff',ap);
      if(el.price2!==undefined)badgePrecio(c,yDePrecio(el.price2),el.price2,col,'#fff',ap);
      if(el.time1!==undefined)badgeTiempo(c,xDeTiempo(el.time1),el.time1,col,ap);
      if(el.time2!==undefined)badgeTiempo(c,xDeTiempo(el.time2),el.time2,col,ap);
    }

    function pintar(){
      ctx.clearRect(0, 0, cssW, cssH);
      if (!serie || !datosActuales.length) return;
      var ap = areaTrazado();
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, 0, ap.w, ap.h);
      ctx.clip();
      elementosDibujados.forEach(function(el, idx){
        dibujarElemento(ctx, el, idx === seleccionadoId, idx === hoverId);
      });
      if (dibujoEnCurso) dibujarElemento(ctx, dibujoEnCurso, true, false);
      ctx.restore();

      elementosDibujados.forEach(function(el, idx){
        if (idx === seleccionadoId || el.tipo === 'hline' || el.tipo === 'vline') etiquetasEje(ctx, el, ap);
      });
      if (dibujoEnCurso) etiquetasEje(ctx, dibujoEnCurso, ap);
    }

    var ultimaFirma = '';
    function firmaVista(){
      if (!datosActuales.length || !serie) return '';
      var ref = datosActuales[datosActuales.length - 1].close;
      var ts = chart.timeScale();
      return [
        serie.priceToCoordinate(ref),
        serie.priceToCoordinate(ref * 1.01),
        ts.logicalToCoordinate(0),
        ts.logicalToCoordinate(100)
      ].join('|');
    }

    function bucleRedibujo(){
      if (elementosDibujados.length > 0 || dibujoEnCurso) {
        var f = firmaVista();
        if (sucio || f !== ultimaFirma) { ultimaFirma = f; sucio = false; pintar(); }
      } else if (sucio) {
        sucio = false;
        pintar();
      }
      requestAnimationFrame(bucleRedibujo);
    }
    requestAnimationFrame(bucleRedibujo);

    function bloquearGrafico(b){
      try { chart.applyOptions({ handleScroll: !b, handleScale: !b }); } catch (e) {}
    }

    function cancelarDibujoEnCurso(){
      dibujoEnCurso = null; esperandoSegundoClick = false; inicioClick = null;
      redibujarTodo();
    }

    // --------------------------------------------------------------------------
    // Menús flotantes y configuración de herramientas
    // --------------------------------------------------------------------------
    var gruposFlyout = [
      { boton:document.getElementById('tool-trend'), menu:document.getElementById('lines-flyout') },
      { boton:document.getElementById('tool-fib'), menu:document.getElementById('fib-flyout') },
      { boton:document.getElementById('tool-geometry'), menu:document.getElementById('geometry-flyout') },
      { boton:document.getElementById('tool-text'), menu:document.getElementById('annotations-flyout') },
      { boton:document.getElementById('tool-measure'), menu:document.getElementById('measure-flyout') }
    ];
    function cerrarFlyouts(excepto){ gruposFlyout.forEach(function(g){if(g.menu&&g.menu!==excepto)g.menu.classList.remove('show');}); }
    gruposFlyout.forEach(function(g){
      if(!g.boton||!g.menu)return;
      g.boton.addEventListener('click',function(e){e.stopPropagation();var abierto=g.menu.classList.contains('show');cerrarFlyouts(g.menu);g.menu.classList.toggle('show',!abierto);});
      g.menu.querySelectorAll('.tvtool-flyout-item').forEach(function(item){
        item.addEventListener('click',function(e){e.stopPropagation();var tool=item.getAttribute('data-tool');g.menu.classList.remove('show');activarHerramienta(tool);var svg=item.querySelector('svg');if(svg)g.boton.innerHTML=svg.outerHTML+'<span class="tvtool-arrow">▼</span>';});
      });
    });
    window.addEventListener('click',function(){cerrarFlyouts(null);});

    var NIVELES_FIB_EXT=[
      {val:-0.272,color:'#8b949e'},{val:0,color:'#f85149'},{val:0.382,color:'#f5c518'},
      {val:0.618,color:'#58a6ff'},{val:1,color:'#3fb950'},{val:1.272,color:'#ff9800'},
      {val:1.618,color:'#a78bfa'},{val:2.618,color:'#f85149'}
    ];
    var FIB_CHANNEL_LEVELS=[
      {val:-1,color:'#8b949e'},{val:0,color:'#f85149'},{val:0.382,color:'#f5c518'},
      {val:0.618,color:'#58a6ff'},{val:1,color:'#3fb950'},{val:1.618,color:'#a78bfa'},{val:2.618,color:'#f85149'}
    ];

    var TOOL_POINTS={
      trend:2,ray:2,extended:2,angle:2,hline:1,hray:1,vline:1,crossline:1,channel:3,
      fib:2,fib_extension:3,fib_channel:3,rectangle:2,ellipse:2,triangle:2,arrow:2,
      text:1,measure:2
    };
    function puntosHerramienta(tool){return TOOL_POINTS[tool]||2;}
    var mantenerHerramienta=false;

    function activarHerramienta(toolName){
      if(dibujoEnCurso&&toolName!==activeTool)cancelarDibujoEnCurso();
      activeTool=toolName;
      document.querySelectorAll('.tvtool').forEach(function(b){
        var t=b.getAttribute('data-tool');
        if(t!=='clear'&&t!=='lock'&&t!=='magnet'&&t!=='keep')b.classList.toggle('active',t===toolName);
      });
      setCursor(toolName==='cross'?'':'cur-dibujar');
    }

    document.querySelectorAll('.tvtool').forEach(function(btn){
      btn.addEventListener('click',function(){
        var tool=btn.getAttribute('data-tool');
        if(tool==='clear'){
          if(elementosDibujados.length&&confirm('¿Deseas limpiar todos los dibujos de este gráfico?')){elementosDibujados=[];seleccionadoId=null;hoverId=null;confirmarCambio();}
          return;
        }
        if(tool==='lock'){
          bloqueado=!bloqueado;btn.style.color=bloqueado?'#3fb950':'#8b949e';btn.title=bloqueado?'Desbloquear dibujos':'Bloquear dibujos';
          if(bloqueado){seleccionadoId=null;hoverId=null;activarHerramienta('cross');redibujarTodo();} return;
        }
        if(tool==='magnet'){
          imanActivo=!imanActivo;btn.classList.toggle('active',imanActivo);btn.title='Magnetismo: '+(imanActivo?'activado':'desactivado');return;
        }
        if(tool==='keep'){
          mantenerHerramienta=!mantenerHerramienta;btn.classList.toggle('active',mantenerHerramienta);btn.title=mantenerHerramienta?'Mantener herramienta activa: sí':'Mantener herramienta activa: no';return;
        }
        // Los botones con flyout no deben activar directamente la herramienta contenedora.
        if(['tool-trend','tool-fib','tool-geometry','tool-text','tool-measure'].indexOf(btn.id)>=0)return;
        activarHerramienta(tool);
      });
    });

    function posMouse(e){var r=wrapEl.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};}

    function crearDibujoInicial(tool,pt){
      var d={tipo:tool,time1:pt.time,price1:pt.price,time2:pt.time,price2:pt.price};
      if(puntosHerramienta(tool)>=3){d.time3=pt.time;d.price3=pt.price;}
      return d;
    }

    function actualizarDibujoEnCurso(pos,e){
      if(!dibujoEnCurso)return;
      var pt=puntoDesdeMouse(pos.x,pos.y,magnetEfectivo(e));if(!pt)return;
      var n=dibujoEnCurso._puntoActual||2;
      dibujoEnCurso['time'+n]=pt.time;dibujoEnCurso['price'+n]=pt.price;redibujarTodo();
    }

    function finalizarDibujo(valido){
      if(!dibujoEnCurso)return;
      var d=dibujoEnCurso;delete d._puntoActual;
      dibujoEnCurso=null;esperandoSegundoClick=false;inicioClick=null;
      var g=geom(d),largo=(g&&ok(g.x1,g.y1,g.x2,g.y2))?Math.hypot(g.x2-g.x1,g.y2-g.y1):0;
      var suficiente=largo>3&&(puntosHerramienta(d.tipo)<3||ok(g.x3,g.y3));
      if(valido&&suficiente){elementosDibujados.push(d);seleccionadoId=elementosDibujados.length-1;confirmarCambio();}
      else redibujarTodo();
      if(mantenerHerramienta){activarHerramienta(d.tipo);}else activarHerramienta('cross');
    }

    function anclasOriginales(el){
      if(el.tipo==='hline')return{price:el.price};
      if(el.tipo==='vline')return{l:tiempoALogico(el.time)};
      if(el.tipo==='crossline')return{l:tiempoALogico(el.time),price:el.price};
      if(el.tipo==='text')return{l:tiempoALogico(el.time),price:el.price};
      return{l1:tiempoALogico(el.time1),price1:el.price1,l2:tiempoALogico(el.time2),price2:el.price2,l3:el.time3!==undefined?tiempoALogico(el.time3):null,price3:el.price3};
    }

    function aplicarArrastre(pos,e){
      var el=elementosDibujados[arrastre.idx];if(!el)return;var o=arrastre.orig;
      if(arrastre.modo==='move'){
        var l=chart.timeScale().coordinateToLogical(pos.x),p=serie.coordinateToPrice(pos.y);if(l===null||p===null)return;
        var dl=l-arrastre.l0,dp=p-arrastre.p0;
        if(el.tipo==='hline')el.price=o.price+dp;
        else if(el.tipo==='vline')el.time=logicoATiempo(o.l+dl);
        else if(el.tipo==='crossline'){el.time=logicoATiempo(o.l+dl);el.price=o.price+dp;}
        else if(el.tipo==='text'){el.time=logicoATiempo(o.l+dl);el.price=o.price+dp;}
        else {el.time1=logicoATiempo(o.l1+dl);el.price1=o.price1+dp;el.time2=logicoATiempo(o.l2+dl);el.price2=o.price2+dp;if(o.l3!==null){el.time3=logicoATiempo(o.l3+dl);el.price3=o.price3+dp;}}
      }else{
        var pt=puntoDesdeMouse(pos.x,pos.y,magnetEfectivo(e));if(!pt)return;
        var n=arrastre.modo==='p1'?1:(arrastre.modo==='p2'?2:3);
        el['time'+n]=pt.time;el['price'+n]=pt.price;
        if(n===1&&el.tipo==='hline')el.price=pt.price;
        if(n===1&&el.tipo==='vline')el.time=pt.time;
        if(n===1&&el.tipo==='crossline'){el.time=pt.time;el.price=pt.price;}
      }
      redibujarTodo();
    }

    wrapEl.addEventListener('mousedown',function(e){
      if(e.button!==0||bloqueado||!serie)return;
      var pos=posMouse(e),ap=areaTrazado();if(pos.x>ap.w||pos.y>ap.h)return;

      if(dibujoEnCurso&&esperandoSegundoClick){
        e.preventDefault();e.stopPropagation();bloquearGrafico(true);
        actualizarDibujoEnCurso(pos,e);
        var nActual=dibujoEnCurso._puntoActual||2;
        var total=puntosHerramienta(dibujoEnCurso.tipo);
        if(nActual>=total){finalizarDibujo(true);return;}
        dibujoEnCurso._puntoActual=nActual+1;
        esperandoSegundoClick=false;
        inicioClick={x:pos.x,y:pos.y};
        return;
      }

      if(activeTool!=='cross'){
        e.preventDefault();e.stopPropagation();var pt=puntoDesdeMouse(pos.x,pos.y,magnetEfectivo(e));if(!pt)return;
        if(activeTool==='hline'){elementosDibujados.push({tipo:'hline',price:pt.price});seleccionadoId=elementosDibujados.length-1;confirmarCambio();if(!mantenerHerramienta)activarHerramienta('cross');}
        else if(activeTool==='hray'){elementosDibujados.push({tipo:'hray',time1:pt.time,price1:pt.price,time2:pt.time,price2:pt.price});seleccionadoId=elementosDibujados.length-1;confirmarCambio();if(!mantenerHerramienta)activarHerramienta('cross');}
        else if(activeTool==='vline'){elementosDibujados.push({tipo:'vline',time:pt.time});seleccionadoId=elementosDibujados.length-1;confirmarCambio();if(!mantenerHerramienta)activarHerramienta('cross');}
        else if(activeTool==='crossline'){elementosDibujados.push({tipo:'crossline',time:pt.time,price:pt.price});seleccionadoId=elementosDibujados.length-1;confirmarCambio();if(!mantenerHerramienta)activarHerramienta('cross');}
        else if(activeTool==='text'){
          var textoPrompt=prompt('Introduce el texto analítico:','Soporte Clave');if(textoPrompt){elementosDibujados.push({tipo:'text',time:pt.time,price:pt.price,texto:textoPrompt});seleccionadoId=elementosDibujados.length-1;confirmarCambio();}
          if(!mantenerHerramienta)activarHerramienta('cross');
        }else{
          bloquearGrafico(true);dibujoEnCurso=crearDibujoInicial(activeTool,pt);dibujoEnCurso._puntoActual=2;inicioClick={x:pos.x,y:pos.y};esperandoSegundoClick=false;seleccionadoId=null;redibujarTodo();
        }
        return;
      }

      var hit=elementoBajo(pos.x,pos.y);
      if(hit){e.preventDefault();e.stopPropagation();bloquearGrafico(true);seleccionadoId=hit.idx;arrastre={modo:hit.parte==='body'?'move':hit.parte,idx:hit.idx,l0:chart.timeScale().coordinateToLogical(pos.x),p0:serie.coordinateToPrice(pos.y),orig:anclasOriginales(elementosDibujados[hit.idx]),movido:false,x0:pos.x,y0:pos.y};redibujarTodo();return;}
      if(seleccionadoId!==null){seleccionadoId=null;redibujarTodo();}
    },true);

    if(window._tvGlobalMousemove){window.removeEventListener('mousemove',window._tvGlobalMousemove);window.removeEventListener('mouseup',window._tvGlobalMouseup);document.removeEventListener('keydown',window._tvGlobalKeydown);}

    window._tvGlobalMousemove=function(e){
      var pos=posMouse(e);
      if(arrastre){if(!arrastre.movido&&Math.hypot(pos.x-arrastre.x0,pos.y-arrastre.y0)<3)return;arrastre.movido=true;aplicarArrastre(pos,e);return;}
      if(dibujoEnCurso){actualizarDibujoEnCurso(pos,e);return;}
      var nuevoHover=null,cls='',dentro=pos.x>=0&&pos.y>=0&&pos.x<=cssW&&pos.y<=cssH;
      if(dentro&&!bloqueado&&activeTool==='cross'){var ap=areaTrazado();if(pos.x<=ap.w&&pos.y<=ap.h){var h=elementoBajo(pos.x,pos.y);if(h){nuevoHover=h.idx;cls=h.parte==='body'?'cur-mover':'cur-punto';}}}
      if(nuevoHover!==hoverId){hoverId=nuevoHover;redibujarTodo();}setCursor(activeTool!=='cross'?'cur-dibujar':cls);
    };
    window.addEventListener('mousemove',window._tvGlobalMousemove);

    window._tvGlobalMouseup=function(e){
      if(arrastre){var huboCambio=arrastre.movido;arrastre=null;if(huboCambio)confirmarCambio();}
      else if(dibujoEnCurso&&!esperandoSegundoClick){
        var pos=posMouse(e),dist=inicioClick?Math.hypot(pos.x-inicioClick.x,pos.y-inicioClick.y):0;
        if(dist>6){
          actualizarDibujoEnCurso(pos,e);
          var nActual=dibujoEnCurso._puntoActual||2,total=puntosHerramienta(dibujoEnCurso.tipo);
          if(total===2 || nActual>=total){finalizarDibujo(true);}
          else{dibujoEnCurso._puntoActual=nActual+1;esperandoSegundoClick=true;inicioClick={x:pos.x,y:pos.y};}
        } else {esperandoSegundoClick=true;}
      }
      bloquearGrafico(false);
    };
    window.addEventListener('mouseup',window._tvGlobalMouseup);

    window.addEventListener('blur',function(){if(arrastre){var huboCambio=arrastre.movido;arrastre=null;if(huboCambio)confirmarCambio();}bloquearGrafico(false);});

    window._tvGlobalKeydown=function(e){
      var tag=(e.target&&e.target.tagName)||'';if(tag==='INPUT'||tag==='TEXTAREA')return;var k=e.key;
      if(k==='Escape'){if(dibujoEnCurso)cancelarDibujoEnCurso();activarHerramienta('cross');if(seleccionadoId!==null){seleccionadoId=null;redibujarTodo();}return;}
      if((k==='Delete'||k==='Backspace')&&seleccionadoId!==null&&!bloqueado){e.preventDefault();elementosDibujados.splice(seleccionadoId,1);seleccionadoId=null;hoverId=null;confirmarCambio();return;}
      if(e.ctrlKey||e.metaKey){var kl=(k||'').toLowerCase();if(kl==='z'&&!e.shiftKey){e.preventDefault();deshacer();}else if(kl==='y'||(kl==='z'&&e.shiftKey)){e.preventDefault();rehacer();}}
    };
    document.addEventListener('keydown',window._tvGlobalKeydown);

    // ==========================================================================
    // CÁLCULOS MATEMÁTICOS DE INDICADORES TÉCNICOS
    // ==========================================================================
    function calcularSMA(datos, periodo){
      var out = [];
      for (var i = periodo - 1; i < datos.length; i++){
        var suma = 0;
        for (var j = i - periodo + 1; j <= i; j++){ suma += datos[j].close; }
        out.push({ time: datos[i].time, value: suma / periodo });
      }
      return out;
    }

    function calcularEMA(datos, periodo){
      var out = [];
      var multiplicador = 2 / (periodo + 1);
      var emaPrevio = 0;
      for (var i = 0; i < datos.length; i++){
        if (i < periodo - 1) continue;
        if (i === periodo - 1) {
          var suma = 0;
          for (var j = 0; j <= i; j++) suma += datos[j].close;
          emaPrevio = suma / periodo;
          out.push({ time: datos[i].time, value: emaPrevio });
        } else {
          emaPrevio = (datos[i].close - emaPrevio) * multiplicador + emaPrevio;
          out.push({ time: datos[i].time, value: emaPrevio });
        }
      }
      return out;
    }

    function calcularBollinger(datos, periodo, desviaciones){
      var sma = calcularSMA(datos, periodo);
      var superiores = [];
      var inferiores = [];
      var medias = [];
      
      for (var i = 0; i < sma.length; i++){
        var idxDatos = i + periodo - 1;
        var sumaCuadrados = 0;
        var mediaVal = sma[i].value;
        for (var j = idxDatos - periodo + 1; j <= idxDatos; j++){
          var diff = datos[j].close - mediaVal;
          sumaCuadrados += diff * diff;
        }
        var desviacionEst = Math.sqrt(sumaCuadrados / periodo);
        var tiempo = sma[i].time;
        medias.push({ time: tiempo, value: mediaVal });
        superiores.push({ time: tiempo, value: mediaVal + (desviaciones * desviacionEst) });
        inferiores.push({ time: tiempo, value: mediaVal - (desviaciones * desviacionEst) });
      }
      return { medias: medias, superiores: superiores, inferiores: inferiores };
    }

    function rsiDesde(ganancia, perdida){
      if (perdida === 0) return ganancia === 0 ? 50 : 100;
      return 100 - (100 / (1 + ganancia / perdida));
    }

    function calcularRSI(datos, periodo){
      var out = [];
      if (datos.length <= periodo) return out;

      for (var k = 0; k < periodo; k++){ out.push({ time: datos[k].time }); }

      var ganancias = 0, perdidas = 0;
      for (var i = 1; i <= periodo; i++){
        var cambio = datos[i].close - datos[i-1].close;
        if (cambio >= 0) ganancias += cambio;
        else perdidas -= cambio;
      }
      var mediaGanancia = ganancias / periodo;
      var mediaPerdida = perdidas / periodo;
      out.push({ time: datos[periodo].time, value: rsiDesde(mediaGanancia, mediaPerdida) });
      
      for (var n = periodo + 1; n < datos.length; n++){
        var cam = datos[n].close - datos[n-1].close;
        var g = cam >= 0 ? cam : 0;
        var p = cam < 0 ? -cam : 0;
        mediaGanancia = (mediaGanancia * (periodo - 1) + g) / periodo;
        mediaPerdida = (mediaPerdida * (periodo - 1) + p) / periodo;
        out.push({ time: datos[n].time, value: rsiDesde(mediaGanancia, mediaPerdida) });
      }
      return out;
    }

    function inicializarRSIChart(){
      if (chartRsi) return;
      var rsiEl = document.getElementById('rsi-container');
      rsiEl.style.display = 'block';
      chartRsi = LightweightCharts.createChart(rsiEl, {
        autoSize: true,
        layout: { background: { color: '#0d1117' }, textColor: '#d1d4dc', fontSize: 11 },
        grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } },
        timeScale: { visible: false },
        rightPriceScale: { borderColor: '#30363d', minimumWidth: 72, scaleMargins: { top: 0.1, bottom: 0.1 } },
        handleScroll: false,
        handleScale: false
      });
      serieRsi = chartRsi.addLineSeries({
        color: '#a78bfa', lineWidth: 2,
        priceFormat: { type: 'price', precision: 2, minMove: 0.01 }
      });
      serieRsi.createPriceLine({ price: 70, color: '#8b949e', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '' });
      serieRsi.createPriceLine({ price: 30, color: '#8b949e', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '' });
    }

    function actualizarIndicadoresActivos(){
      if (indicadores.sma20) {
        if (!seriesInd.sma20) seriesInd.sma20 = chart.addLineSeries({ color: '#f5c518', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.sma20.setData(calcularSMA(datosActuales, 20));
      } else if (seriesInd.sma20) {
        chart.removeSeries(seriesInd.sma20); seriesInd.sma20 = null;
      }

      if (indicadores.sma50) {
        if (!seriesInd.sma50) seriesInd.sma50 = chart.addLineSeries({ color: '#3399ff', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.sma50.setData(calcularSMA(datosActuales, 50));
      } else if (seriesInd.sma50) {
        chart.removeSeries(seriesInd.sma50); seriesInd.sma50 = null;
      }

      if (indicadores.ema20) {
        if (!seriesInd.ema20) seriesInd.ema20 = chart.addLineSeries({ color: '#ff6600', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.ema20.setData(calcularEMA(datosActuales, 20));
      } else if (seriesInd.ema20) {
        chart.removeSeries(seriesInd.ema20); seriesInd.ema20 = null;
      }

      if (indicadores.bollinger) {
        var bb = calcularBollinger(datosActuales, 20, 2);
        if (!seriesInd.bolsuper) {
          seriesInd.bolsuper = chart.addLineSeries({ color: 'rgba(41, 98, 255, 0.7)', lineWidth: 1, priceLineVisible: false, priceFormat: PF });
          seriesInd.bolmedia = chart.addLineSeries({ color: 'rgba(255, 152, 0, 0.7)', lineWidth: 1, priceLineVisible: false, priceFormat: PF });
          seriesInd.bolinf = chart.addLineSeries({ color: 'rgba(41, 98, 255, 0.7)', lineWidth: 1, priceLineVisible: false, priceFormat: PF });
        }
        seriesInd.bolsuper.setData(bb.superiores);
        seriesInd.bolmedia.setData(bb.medias);
        seriesInd.bolinf.setData(bb.inferiores);
      } else if (seriesInd.bolsuper) {
        chart.removeSeries(seriesInd.bolsuper); seriesInd.bolsuper = null;
        chart.removeSeries(seriesInd.bolmedia); seriesInd.bolmedia = null;
        chart.removeSeries(seriesInd.bolinf); seriesInd.bolinf = null;
      }

      if (indicadores.rsi) {
        inicializarRSIChart();
        if (serieRsi) {
          serieRsi.setData(calcularRSI(datosActuales, 14));
          var rango = chart.timeScale().getVisibleLogicalRange();
          if (rango && chartRsi) chartRsi.timeScale().setVisibleLogicalRange(rango);
        }
      } else {
        var rsiEl = document.getElementById('rsi-container');
        rsiEl.style.display = 'none';
        if (chartRsi) { chartRsi.remove(); chartRsi = null; serieRsi = null; }
      }
    }

    function calcularHeikinAshi(datos){
      var ha = [];
      for (var i = 0; i < datos.length; i++){
        var d = datos[i];
        var haClose = (d.open + d.high + d.low + d.close) / 4;
        var haOpen = (i === 0) ? (d.open + d.close) / 2 : (ha[i-1].open + ha[i-1].close) / 2;
        var haHigh = Math.max(d.high, haOpen, haClose);
        var haLow = Math.min(d.low, haOpen, haClose);
        ha.push({ time: d.time, open: haOpen, high: haHigh, low: haLow, close: haClose, volume: d.volume });
      }
      return ha;
    }

    function formatearDatos(datos, tipo){
      if (tipo === "line" || tipo === "area") {
        return datos.map(function(v){ return { time: v.time, value: v.close }; });
      }
      if (tipo === "heikin") {
        var ha = calcularHeikinAshi(datos);
        return ha.map(function(v){ return { time: v.time, open: v.open, high: v.high, low: v.low, close: v.close }; });
      }
      return datos.map(function(v){ return { time: v.time, open: v.open, high: v.high, low: v.low, close: v.close }; });
    }

    function aPuntoVolumen(v){
      return { time: v.time, value: v.volume || 0, color: (v.close >= v.open ? 'rgba(63,185,80,0.5)' : 'rgba(248,81,73,0.5)') };
    }

    function fmtVol(v){
      v = v || 0;
      if (v >= 1e9) return (v/1e9).toFixed(2) + 'B';
      if (v >= 1e6) return (v/1e6).toFixed(2) + 'M';
      if (v >= 1e3) return (v/1e3).toFixed(2) + 'K';
      return String(v);
    }

    function actualizarLeyenda(v){
      if (!v) return;
      var elOhlc = document.getElementById('tv-ohlc-vals');
      var elVol = document.getElementById('tv-vol-val');
      if (!elOhlc) return;
      
      var cierreAnt = v.open;
      if (datosActuales.length > 1) {
        var idxActual = datosActuales.findIndex(function(d){ return d.time === v.time; });
        if (idxActual > 0) {
          cierreAnt = datosActuales[idxActual - 1].close;
        } else if (idxActual === -1 && datosActuales.length > 0) {
          cierreAnt = datosActuales[datosActuales.length - 2].close;
        }
      }

      var delta = v.close - cierreAnt;
      var pct = cierreAnt ? (delta / cierreAnt) * 100 : 0;
      var col = (v.close >= v.open) ? '#3fb950' : '#f85149';
      var colD = (delta >= 0) ? '#3fb950' : '#f85149';
      function c(l, n){ return l + '<b style="color:' + col + '">' + n.toFixed(DIGITS) + '</b>'; }
      elOhlc.innerHTML =
        c('O', v.open) + c('H', v.high) + c('L', v.low) + c('C', v.close) +
        '<b style="color:' + colD + '">' + (delta >= 0 ? '+' : '') + delta.toFixed(DIGITS) +
        ' (' + (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%)</b>';
      if (elVol) elVol.innerText = 'Vol ' + fmtVol(v.volume);
    }

    function cargar(tf, n, ajustarFit){
      tfActual = tf;
      var elTf = document.getElementById('lg-tf');
      if (elTf) elTf.innerText = (tf === 'MN1' ? 'MN' : tf);
      nBarrasActual = n;
      var miId = ++cargaId;
      cargando = true;
      fetch(API + "/velas/" + encodeURIComponent(SIMBOLO) + "?tf=" + tf + "&n=" + n)
        .then(function(r){
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function(velas){
          if (miId !== cargaId) return;
          cargando = false;
          if (velas && velas.length){
            datosActuales = velas;
            serie.setData(formatearDatos(velas, tipoActual));
            serieVolumen.setData(velas.map(aPuntoVolumen));
            if (ajustarFit === 'ultimas') {
              var nv = datosActuales.length;
              chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, nv - 150), to: nv + 8 });
            } else if (ajustarFit) {
              chart.timeScale().fitContent();
            }
            actualizarLeyenda(velas[velas.length - 1]);
            actualizarIndicadoresActivos();
            redibujarTodo();
          }
        })
        .catch(function(){
          if (miId !== cargaId) return;
          cargando = false;
          if (!datosActuales.length) {
            var elOhlc = document.getElementById('tv-ohlc-vals');
            if (elOhlc) elOhlc.innerText = 'Sin conexión con la API (' + API + ')';
          }
        });
    }

    cargar(tfActual, nBarrasActual, 'ultimas');

    var btnTypeSelect = document.getElementById('btn-type-select');
    var typeMenu = document.getElementById('type-menu');
    var btnIndSelect = document.getElementById('btn-ind-select');
    var indMenu = document.getElementById('ind-menu');

    btnTypeSelect.addEventListener('click', function(e){ e.stopPropagation(); typeMenu.classList.toggle('show'); indMenu.classList.remove('show'); });
    btnIndSelect.addEventListener('click', function(e){ e.stopPropagation(); indMenu.classList.toggle('show'); typeMenu.classList.remove('show'); });

    window.addEventListener('click', function(){
      typeMenu.classList.remove('show');
      indMenu.classList.remove('show');
    });

    document.querySelectorAll('#type-menu .tv-drop-item').forEach(function(item){
      item.addEventListener('click', function(){
        tipoActual = item.getAttribute('data-type');
        btnTypeSelect.innerHTML = item.querySelector('svg').outerHTML + '<span>' + item.getAttribute('data-label') + '</span><svg class="caret" viewBox="0 0 10 10"><path d="M2 3.5L5 6.5L8 3.5"/></svg>';
        crearSerie(tipoActual);
        if (datosActuales.length){
          serie.setData(formatearDatos(datosActuales, tipoActual));
          serieVolumen.setData(datosActuales.map(aPuntoVolumen));
          actualizarIndicadoresActivos();
        }
        redibujarTodo();
      });
    });

    document.querySelectorAll('#ind-menu .tv-drop-item').forEach(function(item){
      item.addEventListener('click', function(){
        var indKey = item.getAttribute('data-ind');
        indicadores[indKey] = !indicadores[indKey];
        var stSpan = document.getElementById('st-' + indKey);
        if (indicadores[indKey]) {
          item.classList.add('active-ind');
          stSpan.innerText = 'On';
        } else {
          item.classList.remove('active-ind');
          stSpan.innerText = 'Off';
        }
        actualizarIndicadoresActivos();
      });
    });

    setInterval(function(){
      if (cargando || pollEnCurso || !datosActuales.length) return;
      var tfLlamada = tfActual;
      var idLlamada = cargaId;
      pollEnCurso = true;
      fetch(API + "/ultima/" + encodeURIComponent(SIMBOLO) + "?tf=" + tfLlamada)
        .then(function(r){ return r.json(); })
        .then(function(v){
          if (tfLlamada !== tfActual || idLlamada !== cargaId) return;
          if (v && v.time){
            var ultima = datosActuales[datosActuales.length - 1];
            if (v.time < ultima.time) return;
            if (ultima.time === v.time){
              datosActuales[datosActuales.length - 1] = v;
            } else {
              datosActuales.push(v);
            }
            var datosFormateados = formatearDatos(datosActuales, tipoActual);
            serie.update(datosFormateados[datosFormateados.length - 1]);
            serieVolumen.update(aPuntoVolumen(v));
            actualizarLeyenda(v);
            actualizarIndicadoresActivos();
            redibujarTodo();
          }
        })
        .catch(function(){})
        .then(function(){ pollEnCurso = false; });
    }, 1500);

    chart.subscribeCrosshairMove(function(param){
      if (!param || !param.time){
        if (datosActuales.length) actualizarLeyenda(datosActuales[datosActuales.length - 1]);
        return;
      }
      var idx = datosActuales.findIndex(function(d){ return d.time === param.time; });
      if (idx >= 0) actualizarLeyenda(datosActuales[idx]);
    });

    function marcarTF(tf){
      document.querySelectorAll('.tvtf').forEach(function(b){
        b.classList.toggle('active', b.getAttribute('data-tf') === tf);
      });
    }

    document.querySelectorAll('.tvtf').forEach(function(btn){
      btn.addEventListener('click', function(){
        var tf = btn.getAttribute('data-tf');
        marcarTF(tf);
        document.querySelectorAll('.tvrange').forEach(function(b){ b.classList.remove('active'); });
        cargar(tf, parseInt(btn.getAttribute('data-n'), 10), 'ultimas');
      });
    });

    document.querySelectorAll('.tvrange').forEach(function(btn){
      btn.addEventListener('click', function(){
        var tf = btn.getAttribute('data-tf');
        document.querySelectorAll('.tvrange').forEach(function(b){ b.classList.remove('active'); });
        btn.classList.add('active');
        marcarTF(tf);
        cargar(tf, parseInt(btn.getAttribute('data-n'), 10), true);
      });
    });

    var btnShot = document.getElementById('btn-shot');
    if (btnShot){
      btnShot.addEventListener('click', function(){
        try {
          var canvasScreenshot = chart.takeScreenshot();
          var enlace = document.createElement('a');
          enlace.download = SIMBOLO + '_indicadores.png';
          enlace.href = canvasScreenshot.toDataURL();
          enlace.click();
        } catch (e) {}
      });
    }

    var btnFull = document.getElementById('btn-full');
    var wrap = document.getElementById('tv-wrap');
    if (btnFull && wrap){
      btnFull.addEventListener('click', function(){
        if (!document.fullscreenElement){
          if (wrap.requestFullscreen) wrap.requestFullscreen();
        } else {
          if (document.exitFullscreen) document.exitFullscreen();
        }
      });
    }
  }
  iniciar();
})();
