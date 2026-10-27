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
   -------------------------------- INICIO Piña y Jara 20_dibujo_base .JS --------------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Dibujo: estado, historial, lienzo y conversión de coordenadas
    // ==========================================================================
    // SISTEMA DE DIBUJO PROFESIONAL CON MENÚ FLOTANTE DE LÍNEAS
    // ==========================================================================
    // Lienzo 2D (#dibujo-lienzo) superpuesto al gráfico donde se pintan todos los dibujos del usuario.
    var canvas = document.getElementById('dibujo-lienzo');
    // Contexto de dibujo 2D del lienzo.
    var ctx = canvas.getContext('2d');
    // Contenedor (#grafico-contenedor) que envuelve gráfico y lienzo; define el tamaño del lienzo y recibe las clases de cursor.
    var contenedorEl = document.getElementById('grafico-contenedor');
    // Herramienta de dibujo activa ('cross' = sin dibujar, solo cruz).
    var activoHerramienta = 'cross';
    // Si es true, los dibujos no se pueden mover ni editar.
    var bloqueado = false;
    // Si es true, los puntos nuevos se pegan al OHLC de la vela más cercana (imán).
    var imanActivo = true;

    // Id del dibujo seleccionado (null = ninguno).
    var seleccionadoId = null;
    // Id del dibujo bajo el cursor (null = ninguno).
    var encimaId = null;
    // Dibujo que se está creando en este momento (null si no hay).
    var dibujoEnCurso = null;
    // Indica que la herramienta activa espera el segundo clic para completar el dibujo.
    var esperandoSegundoClick = false;
    // Primer punto fijado del dibujo en curso.
    var inicioClick = null;
    // Estado del arrastre en curso (mover dibujo o editar un punto); null si no se arrastra.
    var arrastre = null;

    // Niveles del retroceso de Fibonacci: valor relativo (0 a 1) y color de cada línea.
    var NIVELES_FIB = [
      { val: 0.0,   color: '#f85149' }, { val: 0.236, color: '#ff9800' },
      { val: 0.382, color: '#f5c518' }, { val: 0.5,   color: '#3fb950' },
      { val: 0.618, color: '#58a6ff' }, { val: 0.786, color: '#a78bfa' },
      { val: 1.0,   color: '#f85149' }
    ];
    // Extensión de Fibonacci (basada en tendencia): se proyecta desde el punto C
    // Extensión de Fibonacci (basada en tendencia): se proyecta desde el punto C
    var NIVELES_FIB_EXT = [
      { val: 0.0,   color: '#f85149' }, { val: 0.236, color: '#ff9800' },
      { val: 0.382, color: '#f5c518' }, { val: 0.5,   color: '#3fb950' },
      { val: 0.618, color: '#58a6ff' }, { val: 0.786, color: '#a78bfa' },
      { val: 1.0,   color: '#f85149' }, { val: 1.272, color: '#26c6da' },
      { val: 1.618, color: '#e056fd' }, { val: 2.0,   color: '#ff9800' },
      { val: 2.618, color: '#58a6ff' }
    ];
    // Canal de Fibonacci: rectas paralelas a la base A-B, separadas en proporción a la distancia hasta C
    // Canal de Fibonacci: rectas paralelas a la base A-B, separadas en proporción a la distancia hasta C
    var NIVELES_FIB_CANAL = [
      { val: 0.0,   color: '#8b949e' }, { val: 0.236, color: '#ff9800' },
      { val: 0.382, color: '#f5c518' }, { val: 0.5,   color: '#3fb950' },
      { val: 0.618, color: '#58a6ff' }, { val: 0.786, color: '#a78bfa' },
      { val: 1.0,   color: '#f85149' }, { val: 1.618, color: '#e056fd' },
      { val: 2.618, color: '#26c6da' }
    ];

    // Hoja de estilo inyectada que fuerza el cursor (mover, puntero, cruz) sobre el gráfico según la clase cur-* de #grafico-contenedor.
    var estiloCursor = document.createElement('style');
    estiloCursor.textContent =
      '#grafico-contenedor.cur-mover, #grafico-contenedor.cur-mover * { cursor: move !important; }' +
      '#grafico-contenedor.cur-punto, #grafico-contenedor.cur-punto * { cursor: pointer !important; }' +
      '#grafico-contenedor.cur-dibujar, #grafico-contenedor.cur-dibujar * { cursor: crosshair !important; }';
    document.head.appendChild(estiloCursor);
    // TITULO SET CURSOR

    /** Aplica al contenedor del gráfico la clase de cursor indicada (cur-mover, cur-punto o cur-dibujar) quitando antes las otras; sin argumento deja el cursor normal. Recibe la clase como cadena o vacío. */
    function fijarCursor(cls){
      contenedorEl.classList.remove('cur-mover', 'cur-punto', 'cur-dibujar');
      if (cls) contenedorEl.classList.add(cls);
    }

    // Clave de localStorage donde se guardan los dibujos de este símbolo.
    var storageKey = 'dibujos_' + SIMBOLO;
    // Lista de dibujos actuales (objetos con tipo, id, puntos tiempo/precio y estilo).
    var elementosDibujados = [];
    // Carga los dibujos guardados del símbolo; si el JSON es inválido, parte de una lista vacía.
    try {
      var guardados = localStorage.getItem(storageKey);
      if (guardados) { elementosDibujados = JSON.parse(guardados); }
    } catch(e) { elementosDibujados = []; }

    // Pila de estados para deshacer/rehacer: cada entrada es el JSON de elementosDibujados (máximo 60).
    var historial = [JSON.stringify(elementosDibujados)];
    // Posición actual dentro de la pila de historial.
    var posicionHistorial = 0;

    // TITULO GUARDAR DIBUJOS LOCAL

    /** Guarda la lista de dibujos actual en localStorage (clave por símbolo); ignora errores de almacenamiento. */
    function guardarDibujosLocal() {
      try { localStorage.setItem(storageKey, JSON.stringify(elementosDibujados)); } catch(e) {}
    }
    // TITULO CONFIRMAR CAMBIO

    /** Registra un cambio en los dibujos: descarta el futuro del historial, apila el nuevo estado (máx. 60), lo guarda en localStorage y pide repintar. */
    function confirmarCambio(){
      historial = historial.slice(0, posicionHistorial + 1);
      historial.push(JSON.stringify(elementosDibujados));
      if (historial.length > 60) historial.shift();
      posicionHistorial = historial.length - 1;
      guardarDibujosLocal();
      redibujarTodo();
    }
    // TITULO RESTAURAR HISTORIAL

    /** Restaura la lista de dibujos desde la posición actual del historial, limpia selección y hover, guarda y pide repintar. Lo usan deshacer y rehacer. */
    function restaurarHistorial(){
      elementosDibujados = JSON.parse(historial[posicionHistorial]);
      seleccionadoId = null; encimaId = null;
      guardarDibujosLocal();
      redibujarTodo();
    }
    // TITULO DESHACER

    /** Retrocede un paso en el historial de dibujos si hay estados anteriores. */
    function deshacer(){ if (posicionHistorial > 0) { posicionHistorial--; restaurarHistorial(); } }
    // TITULO REHACER

    /** Avanza un paso en el historial de dibujos si hay estados posteriores. */
    function rehacer(){ if (posicionHistorial < historial.length - 1) { posicionHistorial++; restaurarHistorial(); } }

    // Ancho y alto del lienzo en píxeles CSS.
    var cssW = 0, cssH = 0;
    // Marca de repintado pendiente: el bucle de render solo dibuja cuando es true.
    var sucio = true;

    // TITULO REDIBUJAR TODO

    /** Marca el lienzo como sucio para que el bucle de render lo repinte en el siguiente fotograma (no dibuja directamente). */
    function redibujarTodo(){ sucio = true; }

    // TITULO RESIZE CANVAS

    /** Ajusta el tamaño del lienzo al del contenedor teniendo en cuenta la densidad de píxeles (devicePixelRatio) para que se vea nítido, reinicia la transformación y pide repintar. */
    function resizeLienzo() {
      var dpr = window.devicePixelRatio || 1;
      cssW = contenedorEl.clientWidth;
      cssH = contenedorEl.clientHeight;
      canvas.width = Math.max(1, Math.round(cssW * dpr));
      canvas.height = Math.max(1, Math.round(cssH * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      redibujarTodo();
    }

    // Reajusta el lienzo cuando cambia el tamaño del contenedor (ResizeObserver o, si no existe, el evento resize); y se ajusta una vez al inicio.
    if (window.ResizeObserver) {
      new ResizeObserver(resizeLienzo).observe(contenedorEl);
    } else {
      window.addEventListener('resize', resizeLienzo);
    }
    resizeLienzo();

    // TITULO AREA TRAZADO

    /** Calcula el área útil de trazado: tamaño del lienzo menos el ancho del eje de precios y el alto del eje de tiempo. Devuelve { w, h }; usa valores por defecto si no puede leer los ejes. */
    function areaTrazado(){
      var anchoEje = 60, altoEje = 28;
      try { anchoEje = chart.priceScale('right').width(); } catch (e) {}
      try { altoEje = chart.timeScale().height(); } catch (e) {}
      return { w: Math.max(0, cssW - anchoEje), h: Math.max(0, cssH - altoEje) };
    }

    // Al mover o hacer zoom en el eje de tiempo se repinta el lienzo y se sincronizan los paneles de osciladores con el mismo rango.
    chart.timeScale().subscribeVisibleLogicalRangeChange(function(range){
      redibujarTodo();
      sincronizarPaneles(range);
    });

    // TITULO OK

    /** Comprueba que todos los argumentos sean números finitos (no null, undefined ni NaN). Devuelve true si lo son; sirve para validar coordenadas antes de dibujar. */
    function ok(){
      for (var i = 0; i < arguments.length; i++){
        var v = arguments[i];
        if (v === null || v === undefined || typeof v !== 'number' || !isFinite(v)) return false;
      }
      return true;
    }

    // Caché de la duración típica de una barra: se invalida si cambian el nº de velas o el último tiempo.
    var cacheSegundos = { n: -1, t: -1, v: 60 };
    // TITULO SEG BARRA

    /** Calcula la duración típica de una barra en segundos (mediana de las diferencias de las últimas 60 velas); devuelve 60 si hay pocos datos. Se usa para extrapolar tiempos fuera del rango de datos. */
    function segundosBarra(){
      var n = datosActuales.length;
      if (n < 2) return 60;
      var tUltimo = datosActuales[n - 1].time;
      if (cacheSegundos.n === n && cacheSegundos.t === tUltimo) return cacheSegundos.v;
      var difs = [];
      for (var i = Math.max(1, n - 60); i < n; i++){
        var d = datosActuales[i].time - datosActuales[i - 1].time;
        if (d > 0) difs.push(d);
      }
      difs.sort(function(a, b){ return a - b; });
      cacheSegundos = { n: n, t: tUltimo, v: difs.length ? difs[Math.floor(difs.length / 2)] : 60 };
      return cacheSegundos.v;
    }

    // TITULO TIEMPO ALOGICO

    /** Convierte un tiempo UNIX en un índice lógico (fraccionario) de vela, interpolando entre velas y extrapolando antes de la primera o después de la última con la duración de barra. Devuelve null si no hay datos o el tiempo es inválido. */
    function tiempoALogico(t){
      var n = datosActuales.length;
      if (!n || typeof t !== 'number' || !isFinite(t)) return null;
      var seg = segundosBarra();
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

    // TITULO LOGICO ATIEMPO

    /** Operación inversa de tiempoALogico: convierte un índice lógico de vela en tiempo UNIX, interpolando o extrapolando fuera del rango. Devuelve null si el dato es inválido. */
    function logicoATiempo(l){
      var n = datosActuales.length;
      if (!n || typeof l !== 'number' || !isFinite(l)) return null;
      var seg = segundosBarra();
      if (l <= 0) return datosActuales[0].time + l * seg;
      if (l >= n - 1) return datosActuales[n - 1].time + (l - (n - 1)) * seg;
      var i = Math.floor(l);
      var t0 = datosActuales[i].time, t1 = datosActuales[i + 1].time;
      return t0 + (l - i) * (t1 - t0);
    }

    // TITULO X DE TIEMPO

    /** Convierte un tiempo UNIX en la coordenada X (píxeles) del gráfico, pasando por el índice lógico. Devuelve null si no se puede. */
    function xDeTiempo(t){
      var l = tiempoALogico(t);
      if (l === null) return null;
      return chart.timeScale().logicalToCoordinate(l);
    }
    // TITULO Y DE PRECIO

    /** Convierte un precio en la coordenada Y (píxeles) de la serie de precio. Devuelve null si no hay serie o el precio no es numérico. */
    function yDePrecio(p){
      if (!serie || typeof p !== 'number') return null;
      return serie.priceToCoordinate(p);
    }

    // TITULO MAGNET EFECTIVO

    /** Indica si el imán debe aplicarse en este evento: el imán global se invierte mientras se mantiene Ctrl. Recibe el evento del ratón. */
    function imanEfectivo(e){ return imanActivo !== !!(e && e.ctrlKey); }

    // TITULO PUNTO DESDE MOUSE

    /** Convierte una posición del ratón (x, y en píxeles) en un punto de dibujo { l, time, price }. Con imán, se ajusta a la vela más cercana y al valor OHLC más próximo si está a menos de 14 px. Devuelve null si no hay serie, datos o coordenadas válidas. */
    function puntoDesdeRaton(x, y, conIman){
      if (!serie || !datosActuales.length) return null;
      var l = chart.timeScale().coordinateToLogical(x);
      var p = serie.coordinateToPrice(y);
      if (l === null || p === null) return null;
      if (conIman){
        var i = Math.round(l);
        if (i >= 0 && i < datosActuales.length){
          var v = datosActuales[i];
          var mejor = null, mejorD = 14;
          [v.open, v.high, v.low, v.close].forEach(function(candidato){
            var cy = serie.priceToCoordinate(candidato);
            if (cy !== null){
              var d = Math.abs(cy - y);
              if (d < mejorD){ mejorD = d; mejor = candidato; }
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

    // TITULO PUNTO VISUAL

    /** Devuelve las coordenadas en pantalla { x, y } del punto número n (1, 2 o 3) de un dibujo, leyendo sus campos time{n} y price{n}. */
    function puntoVisual(el, n){
      var t = el['time' + n], p = el['price' + n];
      return { x: xDeTiempo(t), y: yDePrecio(p) };
    }

    // TITULO GEOM

    /** Calcula la geometría en pantalla de un dibujo: para líneas horizontales/verticales, texto y cruz devuelve la coordenada necesaria; para el resto devuelve x1,y1..x3,y3. Devuelve null si algún punto principal no es visible/válido. */
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


/* -------------------------------------------------------------------------------------------------------
   ---------------------------------- FIN Piña y Jara 20_dibujo_base .JS ---------------------------------
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
