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
   --------------------------------- INICIO Piña y Jara 10_sparklines .JS --------------------------------
   ------------------------------------------------------------------------------------------------------- */

  // TITULO SEMBRAR SPARKS

  // --- Mini-gráficos (sparklines) -----------------------------------------
  /**
   * Carga la semilla histórica de cada mini-gráfico presente en el DOM.
   * Lee data-pj-spark (símbolo) y data-pj-vals (valores separados por comas) y llena `spark[s]`.
   * Solo siembra una vez por símbolo y solo si la semilla trae al menos 5 puntos.
   */
  function sembrarSparks(){
    D.querySelectorAll('[data-pj-spark]').forEach(function(el){
      var s = el.getAttribute('data-pj-spark');
      var v = (el.getAttribute('data-pj-vals') || '').split(',').map(parseFloat)
                .filter(function(x){ return isFinite(x); });
      // La semilla del servidor (histórico M1) se usa UNA vez por símbolo: los
      // ticks ya recibidos se agregan detrás. Si aún no trae histórico real
      // (< 5 puntos, símbolo recién agregado) se reintenta en el próximo refresco.
      if (sembrado[s] || !v.length) return;
      if (v.length >= 5){
        spark[s] = v.concat(spark[s] || []).slice(-SPARK_MAX);
        sembrado[s] = true;
      } else if (!spark[s]) {
        spark[s] = v.slice();
      }
      sparkT[s] = Date.now();
    });
  }
  // TITULO EMPUJAR SPARK

  /**
   * Añade el precio de un tick a la serie del símbolo `s`.
   * Si pasó al menos SPARK_PASO ms desde el último punto agrega uno nuevo (recortando a SPARK_MAX);
   * si no, solo mueve el último punto. No devuelve nada.
   */
  function empujarSpark(s, precio){
    if (!precio) return;
    var buf = spark[s] || (spark[s] = []);
    var ahora = Date.now();
    if (!buf.length || ahora - (sparkT[s] || 0) >= SPARK_PASO){
      buf.push(precio); sparkT[s] = ahora;
      if (buf.length > SPARK_MAX) buf.splice(0, buf.length - SPARK_MAX);
    } else {
      buf[buf.length - 1] = precio;          // dentro del paso: mueve el último punto
    }
  }
  // TITULO SVG SPARK

  /**
   * Construye el SVG (cadena) de un mini-gráfico: área con degradé y línea del color `col`.
   * Recibe el símbolo `s` (para el id único del degradé), la serie `vals` y el color. Devuelve el SVG.
   */
  function svgSpark(s, vals, col){
    // Dimensiones del lienzo SVG y margen vertical.
    var w = 92, h = 40, pad = 3;
    if (vals.length < 2) vals = [vals[0], vals[0]];
    // Rango de la serie para escalar al alto del lienzo (rng evita división por cero).
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), rng = (hi - lo) || 1;
    var n = vals.length, pts = [];
    // Convierte cada valor en un punto "x,y" (el eje Y crece hacia abajo, por eso se invierte).
    for (var i = 0; i < n; i++){
      var x = i * (w / (n - 1)), y = h - pad - ((vals[i] - lo) / rng) * (h - 2 * pad);
      pts.push(x.toFixed(1) + ',' + y.toFixed(1));
    }
    // Cadena de puntos de la línea y id único del degradado por símbolo.
    var linea = pts.join(' '), gid = 'pjs' + s.replace(/\W/g, '');
    return "<svg xmlns='http://www.w3.org/2000/svg' width='" + w + "' height='" + h +
      "' viewBox='0 0 " + w + " " + h + "' preserveAspectRatio='none'>" +
      "<defs><linearGradient id='" + gid + "' x1='0' y1='0' x2='0' y2='1'>" +
      "<stop offset='0' stop-color='" + col + "' stop-opacity='0.30'/>" +
      "<stop offset='1' stop-color='" + col + "' stop-opacity='0'/></linearGradient></defs>" +
      "<polygon points='0," + h + " " + linea + " " + w + "," + h + "' fill='url(#" + gid + ")'/>" +
      "<polyline points='" + linea + "' fill='none' stroke='" + col + "' stroke-width='1.6' " +
      "stroke-linejoin='round' stroke-linecap='round'/></svg>";
  }
  // TITULO PINTAR SPARK

  /**
   * Redibuja el mini-gráfico contenido en `el` para el símbolo `s`.
   * Elige verde o rojo según el cambio del día y evita repintar si la serie no cambió
   * (usa data-pj-k como huella). Modifica el innerHTML del elemento.
   */
  function pintarSpark(el, s){
    // SVG EN LÍNEA (no <img> data-URI): se dibuja en el mismo frame, sin
    // decodificar imagen → al reemplazar el dibujo del servidor no hay parpadeo.
    var buf = spark[s];
    if (!buf || !buf.length) return;
    // Último tick del símbolo: define el color según el signo del cambio.
    var t = ultimo[s];
    var col = (t && t.ch < 0) ? '#f85149' : '#3fb950';
    // Huella del estado actual para saltar repintados innecesarios.
    var clave = buf.length + '|' + buf[buf.length - 1] + '|' + buf[0] + '|' + col;
    if (el.getAttribute('data-pj-k') === clave) return;
    el.setAttribute('data-pj-k', clave);
    el.innerHTML = svgSpark(s, buf, col);
  }


/* -------------------------------------------------------------------------------------------------------
   ---------------------------------- FIN Piña y Jara 10_sparklines .JS ----------------------------------
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
