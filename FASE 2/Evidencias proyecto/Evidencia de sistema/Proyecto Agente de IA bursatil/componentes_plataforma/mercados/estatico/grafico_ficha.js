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
   --------------------------------- INICIO Piña y Jara grafico_ficha .JS --------------------------------
   ------------------------------------------------------------------------------------------------------- */

/** Funcion autoejecutable que crea el grafico de area de la ficha, sus pestanas de periodo y el modo en vivo. */
(function(){
  // Estado de entrada inyectado por grafico.py: series por periodo (d1, h1, m5), decimales del precio y simbolo
  var D = __DATA__, DIG = __DIG__, SYM = __SYM__;
  // Contenedor del grafico dentro del iframe
  var el = document.getElementById('chart');
  // Si la libreria no cargo (sin internet), se muestra un aviso y se aborta
  if (!window.LightweightCharts){ el.innerHTML = '<div style="color:#8b949e;font-size:12px;padding:20px;">No se pudo cargar el gráfico (sin internet).</div>'; return; }
  // Grafico con estilo oscuro y transparente; sin desplazamiento ni zoom para que no choque con el scroll de la ficha
  var ch = LightweightCharts.createChart(el, {
    autoSize: true,
    layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#8b949e', fontSize: 11 },
    grid: { vertLines: { visible: false }, horzLines: { color: '#161d27' } },
    rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.12, bottom: 0.08 } },
    timeScale: { borderVisible: false, timeVisible: true, secondsVisible: false },
    crosshair: { mode: 1, vertLine: { color: '#30363d', labelBackgroundColor: '#202a37' },
                 horzLine: { color: '#30363d', labelBackgroundColor: '#202a37' } },
    handleScroll: false, handleScale: false,
    localization: { priceFormatter: function(p){ return p.toLocaleString('en-US', {minimumFractionDigits: DIG, maximumFractionDigits: DIG}); } }
  });
  // Serie de area unica; su color se ajusta en colorear() segun suba o baje el periodo
  var serie = ch.addAreaSeries({ lineWidth: 2, priceLineVisible: false, lastValueVisible: true });
  // Periodos: [etiqueta, modo]; 'd' = 1 dia con velas M5, 'w' = 1 semana con H1, numero = cantidad de velas diarias
  var PER = [['1D','d'],['1S','w'],['1M',22],['3M',66],['6M',132],['1A',260]];
  // Referencias al DOM y texto de leyenda "actual" (rendimiento del periodo) para restaurarlo al salir del cursor
  var tabs = document.getElementById('tabs'), ley = document.getElementById('leyenda'), actual = null;
  var modo = 'd', horas = true;   // 'd' = 1 día (M5), 'w' = 1 semana (H1), número = días (D1)
  // TITULO FUENTE

  /** Devuelve la serie de datos original (m5, h1 o d1) que corresponde al modo activo. */
  function fuente(){ return modo === 'd' ? D.m5 : (modo === 'w' ? D.h1 : D.d1); }
  // TITULO PASO

  /** Devuelve la duracion en segundos de una vela del modo activo (5 min, 1 h o 1 dia). */
  function paso(){ return modo === 'd' ? 300 : (modo === 'w' ? 3600 : 86400); }
  // datos: puntos mostrados ahora; sobre: true si el cursor esta sobre el grafico; raf: hay un repintado pendiente
  var datos = [], sobre = false, raf = false;
  // TITULO FMT

  /** Formatea un numero con los decimales del instrumento (formato en-US). */
  function fmt(v){ return v.toLocaleString('en-US', {minimumFractionDigits: DIG, maximumFractionDigits: DIG}); }
  // TITULO PONER

  /** Cambia de periodo: elige los datos del modo k, los carga en la serie, recolorea y ajusta la vista. */
  function poner(k){
    modo = k; horas = (k === 'd' || k === 'w');
    // Para periodos numericos se toman las ultimas k velas diarias; si no, la serie del modo
    datos = (typeof k === 'number' ? D.d1.slice(-k) : fuente()).slice();
    if (!datos.length) return;
    serie.setData(datos);
    colorear();
    ch.timeScale().fitContent();
  }
  // TITULO COLOREAR

  /** Colorea la serie de verde o rojo segun el periodo suba o baje, y actualiza la leyenda con el porcentaje. */
  function colorear(){
    var a = datos[0].value, b = datos[datos.length - 1].value, sube = b >= a;
    var c = sube ? '#3fb950' : '#f85149';
    serie.applyOptions({ lineColor: c, topColor: sube ? 'rgba(63,185,80,.28)' : 'rgba(248,81,73,.28)',
                         bottomColor: 'rgba(0,0,0,0)' });
    var p = (b / a - 1) * 100;
    actual = '<span style="color:' + c + ';font-weight:700;">' + (p >= 0 ? '+' : '') + p.toFixed(2) + '%</span> en el periodo' +
             ' &nbsp;<span style="color:#3fb950;">&#9679;</span> en vivo';
    // Solo se actualiza la leyenda si el cursor no esta mostrando un valor puntual
    if (!sobre) ley.innerHTML = actual;
  }
  // TITULO APLICAR TICK

  // EN VIVO: el feed reenvía cada tick por BroadcastChannel('pj-ticks'); se mueve el
  // último punto (o se agrega uno al empezar otra hora / otro día). Bid, como MT5.
  /** Aplica un tick en vivo: t.t es el tiempo unix y t.b el bid. Actualiza el ultimo punto o agrega uno nuevo y agenda un repintado. */
  function aplicarTick(t){
    if (!datos.length) return;
    // Inicio de la vela a la que pertenece el tick, redondeando al paso del modo activo
    var seg = paso(), ini = Math.floor(t.t / seg) * seg;
    var src = fuente(), ult = datos[datos.length - 1];
    var punto = {time: Math.max(ini, ult.time), value: t.b};
    // Vela nueva: se agrega; misma vela: se reemplaza el ultimo punto (tanto en datos como en la fuente)
    if (punto.time > ult.time){ datos.push(punto); src.push(punto); }
    else { datos[datos.length - 1] = punto; src[src.length - 1] = punto; }
    // Se agrupan los ticks en un solo repintado por fotograma
    if (raf) return; raf = true;
    requestAnimationFrame(function(){ raf = false; serie.update(datos[datos.length - 1]); colorear(); });
  }
  // Suscripcion al canal de ticks del feed; solo se procesan los del simbolo de esta ficha
  if ('BroadcastChannel' in window){
    new BroadcastChannel('pj-ticks').onmessage = function(ev){
      var t = ev.data && ev.data.t && ev.data.t[SYM];
      if (t && t.b && t.t) aplicarTick(t);
    };
  }
  // Creacion de los botones de periodo; al hacer clic se marca el activo y se carga ese periodo
  PER.forEach(function(x, i){
    var b = document.createElement('button'); b.textContent = x[0];
    b.onclick = function(){ [].forEach.call(tabs.children, function(y){ y.className = ''; }); b.className = 'on'; poner(x[1]); };
    tabs.appendChild(b);
    if (x[0] === '1D'){ b.className = 'on'; }
  });
  // Periodo inicial: 1 dia si hay velas M5; si no, 6 meses (132 velas diarias)
  poner(D.m5.length ? 'd' : 132);
  // Leyenda interactiva: al pasar el cursor muestra precio y fecha del punto; al salir restaura el rendimiento del periodo
  ch.subscribeCrosshairMove(function(pm){
    sobre = !!(pm && pm.time && pm.seriesData.get(serie));
    if (!sobre){ ley.innerHTML = actual; return; }
    var v = pm.seriesData.get(serie).value, f = new Date(pm.time * 1000);
    ley.innerHTML = '<span style="color:#e6edf3;font-weight:700;">' + fmt(v) + '</span> &nbsp;' +
      f.toLocaleDateString('es-CL', {day:'2-digit', month:'short', year:'numeric', timeZone:'UTC'}) +
      (horas ? ' ' + f.toISOString().substr(11, 5) : '');
  });
})();

/* -------------------------------------------------------------------------------------------------------
   ---------------------------------- FIN Piña y Jara grafico_ficha .JS ----------------------------------
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
