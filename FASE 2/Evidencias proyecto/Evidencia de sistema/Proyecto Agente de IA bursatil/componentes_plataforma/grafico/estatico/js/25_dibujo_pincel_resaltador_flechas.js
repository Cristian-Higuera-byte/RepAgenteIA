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
   ---------------------- INICIO Piña y Jara 25_dibujo_pincel_resaltador_flechas .JS ---------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Dibujo: pincel, resaltador y flechas
    // Estilo recordado del pincel: color y grosor del último pincel confirmado, que usarán los trazos nuevos.
    var estiloPincel = { color: COLOR_DEF.brush, ancho: ANCHO_DEF.brush };
    // Trazo de pincel en curso { pts (puntos lógico/precio), color, ancho, ultimoPx }; null si no se está pintando.
    var trazoPincel = null;
    // Caché (WeakMap por dibujo) de los puntos del pincel ya convertidos a píxeles, para no recalcular en cada fotograma.
    var cachePincel = new WeakMap();

    // TITULO FIRMA PINCEL

    /** Genera una firma del estado de la vista (cantidad de velas, primer y último tiempo y escala) que sirve para invalidar la caché de puntos del pincel. Devuelve cadena vacía sin datos. */
    function firmaPincel(){
      var n = datosActuales.length;
      return n ? (n + ':' + datosActuales[0].time + ':' + datosActuales[n - 1].time + ':' + firmaVista()) : '';
    }

    // TITULO PUNTOS PANTALLA

    /** Convierte los puntos (tiempo, precio) de un trazo a coordenadas de pantalla {x, y}, descartando los inválidos y usando la caché mientras la vista no cambie. Recibe el dibujo y devuelve el arreglo de puntos. */
    function puntosPantalla(el){
      var firma = firmaPincel();
      var c = cachePincel.get(el);
      if (c && c.ref === el.puntos && c.firma === firma) return c.pts;
      var out = [];
      (el.puntos || []).forEach(function(q){
        var x = xDeTiempo(q[0]), y = yDePrecio(q[1]);
        if (ok(x, y)) out.push({ x: x, y: y });
      });
      cachePincel.set(el, { ref: el.puntos, firma: firma, pts: out });
      return out;
    }

    // TITULO TRAZAR SUAVE

    /** Pinta una curva suave (curvas cuadráticas con los puntos medios) por los puntos dados; si es un solo punto dibuja un círculo. Recibe contexto, puntos, color y grosor. */
    function trazarSuave(c, pts, col, ancho){
      var v = pts.filter(function(q){ return ok(q.x, q.y); });
      if (!v.length) return;
      c.save();
      c.strokeStyle = col; c.fillStyle = col; c.lineWidth = ancho;
      c.lineCap = 'round'; c.lineJoin = 'round';
      var punto = v.length === 1 || (v.length === 2 && v[0].x === v[1].x && v[0].y === v[1].y);
      if (punto) {
        c.beginPath(); c.arc(v[0].x, v[0].y, ancho / 2, 0, 2 * Math.PI); c.fill();
      } else {
        c.beginPath(); c.moveTo(v[0].x, v[0].y);
        for (var i = 1; i < v.length - 1; i++) {
          var mx = (v[i].x + v[i + 1].x) / 2, my = (v[i].y + v[i + 1].y) / 2;
          c.quadraticCurveTo(v[i].x, v[i].y, mx, my);
        }
        c.lineTo(v[v.length - 1].x, v[v.length - 1].y);
        c.stroke();
      }
      c.restore();
    }

    // TITULO DIBUJAR PINCEL

    /** Pinta un trazo de pincel: si está seleccionado añade un halo azul detrás y si el cursor está encima lo engrosa 1 px. Recibe contexto, dibujo, selección y hover. */
    function dibujarPincel(c, el, sel, hov){
      var v = puntosPantalla(el);
      if (!v.length) return;
      var col = el.color || COLOR_DEF.brush, w = el.ancho || ANCHO_DEF.brush;
      if (sel) trazarSuave(c, v, 'rgba(88,166,255,0.35)', w + 6);
      trazarSuave(c, v, col, w + ((hov && !sel) ? 1 : 0));
    }

    // TITULO HIT PINCEL

    /** Prueba si el punto (x, y) toca un trazo de pincel o resaltador comparando con la distancia a cada segmento (tolerancia según el grosor, mínimo 6 px). Devuelve true o false. */
    function impactoPincel(el, x, y){
      var v = puntosPantalla(el);
      if (!v.length) return false;
      var tol = Math.max(6, (el.ancho || ANCHO_DEF.brush) / 2 + 4);
      if (v.length === 1) return Math.hypot(x - v[0].x, y - v[0].y) <= tol;
      for (var i = 1; i < v.length; i++) {
        if (distanciaSegundos(x, y, v[i - 1].x, v[i - 1].y, v[i].x, v[i].y) <= tol) return true;
      }
      return false;
    }

    // Se extienden las funciones centrales con el soporte del pincel: cada versión nueva atiende el tipo 'brush' y delega en la anterior para los demás tipos.
    var dibujarElementoBase = dibujarElemento;
    /** Versión de dibujarElemento que pinta el tipo 'brush' con dibujarPincel y delega el resto en la versión anterior. */
    dibujarElemento = function(c, el, sel, hov){
      if (el.tipo === 'brush') { dibujarPincel(c, el, sel, hov); return; }
      dibujarElementoBase(c, el, sel, hov);
    };

    var impactoPruebaBase = impactoPrueba;
    /** Versión de hitTest que detecta el tipo 'brush' con hitPincel y delega el resto en la versión anterior. */
    impactoPrueba = function(el, x, y, sel){
      if (el.tipo === 'brush') return impactoPincel(el, x, y) ? 'body' : null;
      return impactoPruebaBase(el, x, y, sel);
    };

    var anclasOriginalesBase = anclasOriginales;
    /** Versión de anclasOriginales que para 'brush' guarda todos sus puntos como (índice lógico, precio) y delega el resto. */
    anclasOriginales = function(el){
      if (el.tipo === 'brush') {
        return { pts: el.puntos.map(function(q){ return [tiempoALogico(q[0]), q[1]]; }) };
      }
      return anclasOriginalesBase(el);
    };

    var aplicarArrastreBase = aplicarArrastre;
    /** Versión de aplicarArrastre que desplaza todos los puntos de un pincel al moverlo (en barras y precio) y delega el resto en la versión anterior. Recibe la posición del ratón y el evento. */
    aplicarArrastre = function(pos, e){
      var el = arrastre ? elementosDibujados[arrastre.idx] : null;
      if (el && el.tipo === 'brush' && arrastre.modo === 'move') {
        var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
        if (l === null || p === null) return;
        var dl = l - arrastre.l0, dp = p - arrastre.p0;
        el.puntos = arrastre.orig.pts.map(function(q){
          return [Math.round(logicoATiempo(q[0] + dl)), q[1] + dp];
        });
        redibujarTodo();
        return;
      }
      aplicarArrastreBase(pos, e);
    };

    var pegarBase = pegar;
    /** Versión de pegar que, si el portapapeles contiene un pincel, lo pega desplazado 4 barras y unos 24 px hacia abajo; para cualquier otro dibujo delega en la versión anterior. */
    pegar = function(){
      if (portapapeles && !bloqueado && serie) {
        var el0 = JSON.parse(portapapeles);
        if (el0.tipo === 'brush' && el0.puntos && el0.puntos.length) {
          var yReferencia = yDePrecio(el0.puntos[0][1]);
          var pDesp = ok(yReferencia) ? serie.coordinateToPrice(yReferencia + 24) : null;
          var dp0 = (pDesp !== null) ? (pDesp - el0.puntos[0][1]) : 0;
          el0.puntos = el0.puntos.map(function(q){
            var l = tiempoALogico(q[0]);
            return [l === null ? q[0] : Math.round(logicoATiempo(l + 4)), q[1] + dp0];
          });
          elementosDibujados.push(el0);
          seleccionadoId = elementosDibujados.length - 1;
          confirmarCambio();
          return;
        }
      }
      pegarBase();
    };

    var confirmarCambioBase = confirmarCambio;
    /** Versión de confirmarCambio que, si el dibujo seleccionado es un pincel, recuerda su color y grosor como estilo del siguiente pincel y luego delega en la versión anterior. */
    confirmarCambio = function(){
      var s = (seleccionadoId !== null) ? elementosDibujados[seleccionadoId] : null;
      if (s && s.tipo === 'brush') {
        if (s.color) estiloPincel.color = s.color;
        if (s.ancho) estiloPincel.ancho = s.ancho;
      }
      confirmarCambioBase();
    };

    var pintarPrevioPincel = pintar;
    /** Versión de pintar que tras pintar lo existente dibuja encima el trazo de pincel en curso (recortado al área de trazado). */
    pintar = function(){
      pintarPrevioPincel();
      if (!trazoPincel || !dibujosVisibles || !serie) return;
      var ap = areaTrazado(), ts = chart.timeScale();
      ctx.save();
      ctx.beginPath(); ctx.rect(0, 0, ap.w, ap.h); ctx.clip();
      trazarSuave(ctx, trazoPincel.pts.map(function(q){
        return { x: ts.logicalToCoordinate(q.l), y: yDePrecio(q.p) };
      }), trazoPincel.color, trazoPincel.ancho);
      ctx.restore();
    };

    // TITULO FINALIZAR TRAZO

    /** Termina el trazo de pincel en curso: convierte sus puntos a (tiempo, precio) redondeados, agrega el dibujo 'brush', lo selecciona, confirma el cambio y vuelve a la cruz (o conserva el pincel si "mantener" está activo). Descarta el trazo si queda vacío. */
    function finalizarTrazo(){
      if (!trazoPincel) return;
      var t = trazoPincel;
      trazoPincel = null;
      bloquearGrafico(false);
      var puntos = [];
      t.pts.forEach(function(q){
        var tm = logicoATiempo(q.l);
        if (tm !== null) puntos.push([Math.round(tm), Math.round(q.p * 1e8) / 1e8]);
      });
      if (!puntos.length) { redibujarTodo(); return; }
      if (puntos.length === 1) puntos.push([puntos[0][0], puntos[0][1]]);
      elementosDibujados.push({ tipo: 'brush', puntos: puntos, color: t.color, ancho: t.ancho });
      seleccionadoId = elementosDibujados.length - 1;
      confirmarCambio();
      activarHerramienta(mantenerHerramienta ? 'brush' : 'cross');
    }

    // TITULO SUMAR PUNTO TRAZO

    /** Agrega al trazo en curso el punto bajo el cursor (en coordenadas lógica/precio), ignorando movimientos menores de 2 px, y pide repintar. Recibe la posición del ratón. */
    function sumarPuntoTrazo(pos){
      var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
      if (l === null || p === null) return;
      var u = trazoPincel.ultimoPx;
      if (u && Math.hypot(pos.x - u.x, pos.y - u.y) < 2) return;
      trazoPincel.ultimoPx = { x: pos.x, y: pos.y };
      trazoPincel.pts.push({ l: l, p: p });
      redibujarTodo();
    }

    // Mouse abajo con el pincel activo (fase de captura): empieza un trazo nuevo dentro del área de trazado, bloquea el gráfico y agrega el primer punto.
    window.addEventListener('mousedown', function(e){
      if (activoHerramienta !== 'brush' || e.button !== 0 || bloqueado || !serie || !datosActuales.length) return;
      if (!contenedorEl.contains(e.target)) return;
      if (e.target.closest && e.target.closest('.tradingview-ui')) return;
      var pos = posicionRaton(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      e.preventDefault(); e.stopPropagation();
      bloquearGrafico(true);
      seleccionadoId = null; encimaId = null;
      trazoPincel = { pts: [], color: estiloPincel.color, ancho: estiloPincel.ancho, ultimoPx: null };
      sumarPuntoTrazo(pos);
    }, true);

    // Mouse move: agrega puntos al trazo mientras el botón izquierdo siga pulsado; cancela el trazo si cambia la herramienta y lo termina si se soltó el botón.
    window.addEventListener('mousemove', function(e){
      if (!trazoPincel) return;
      if (activoHerramienta !== 'brush') { trazoPincel = null; bloquearGrafico(false); redibujarTodo(); return; }
      if (!(e.buttons & 1)) { finalizarTrazo(); return; }
      var pos = posicionRaton(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      sumarPuntoTrazo(pos);
    });

    // Al soltar el botón del ratón en cualquier parte se termina el trazo del pincel.
    window.addEventListener('mouseup', function(){ finalizarTrazo(); });

    // Estilo recordado del resaltador (color translúcido y grosor grande).
    var estiloResaltador = { color: COLOR_DEF.highlighter, ancho: ANCHO_DEF.highlighter };
    // Trazo de resaltador en curso; null si no se está resaltando.
    var trazoResaltador = null;

    // TITULO DIBUJAR RESALTADOR

    /** Pinta un trazo de resaltador: línea gruesa translúcida con modo de mezcla 'multiply' (más opaca si está seleccionado) y, al seleccionarlo, un contorno punteado azul. Recibe contexto, dibujo, selección y hover. */
    function dibujarResaltador(c, el, sel, hov){
      var v = puntosPantalla(el);
      if (!v.length) return;
      var w = el.ancho || ANCHO_DEF.highlighter;
      c.save();
      c.globalCompositeOperation = 'multiply';
      c.globalAlpha = sel ? 0.55 : 0.35;
      c.strokeStyle = el.color || COLOR_DEF.highlighter;
      c.lineWidth = w + ((hov && !sel) ? 2 : 0);
      c.lineCap = 'round'; c.lineJoin = 'round';
      c.beginPath();
      v.forEach(function(p, i){ i === 0 ? c.moveTo(p.x, p.y) : c.lineTo(p.x, p.y); });
      c.stroke();
      if (sel) {
        c.globalCompositeOperation = 'source-over';
        c.globalAlpha = 1;
        c.strokeStyle = 'rgba(88,166,255,0.5)';
        c.lineWidth = w + 8; c.setLineDash([6, 4]);
        c.beginPath();
        v.forEach(function(p, i){ i === 0 ? c.moveTo(p.x, p.y) : c.lineTo(p.x, p.y); });
        c.stroke();
      }
      c.restore();
    }

    // Se extienden de nuevo las funciones centrales, ahora con el soporte del resaltador (tipo 'highlighter').
    var dibujarElementoBase2 = dibujarElemento;
    /** Versión de dibujarElemento que pinta el tipo 'highlighter' con dibujarResaltador y delega el resto. */
    dibujarElemento = function(c, el, sel, hov){
      if (el.tipo === 'highlighter') { dibujarResaltador(c, el, sel, hov); return; }
      dibujarElementoBase2(c, el, sel, hov);
    };

    var impactoPruebaBase2 = impactoPrueba;
    /** Versión de hitTest que detecta el resaltador con hitPincel y delega el resto. */
    impactoPrueba = function(el, x, y, sel){
      if (el.tipo === 'highlighter') return impactoPincel(el, x, y) ? 'body' : null;
      return impactoPruebaBase2(el, x, y, sel);
    };

    var anclasOriginalesBase2 = anclasOriginales;
    /** Versión de anclasOriginales que para 'highlighter' guarda sus puntos como (índice lógico, precio) y delega el resto. */
    anclasOriginales = function(el){
      if (el.tipo === 'highlighter') return { pts: el.puntos.map(function(q){ return [tiempoALogico(q[0]), q[1]]; }) };
      return anclasOriginalesBase2(el);
    };

    var aplicarArrastreBase2 = aplicarArrastre;
    /** Versión de aplicarArrastre que mueve todos los puntos del resaltador al arrastrarlo y delega el resto. Recibe la posición del ratón y el evento. */
    aplicarArrastre = function(pos, e){
      var el = arrastre ? elementosDibujados[arrastre.idx] : null;
      if (el && el.tipo === 'highlighter' && arrastre.modo === 'move') {
        var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
        if (l === null || p === null) return;
        var dl = l - arrastre.l0, dp = p - arrastre.p0;
        el.puntos = arrastre.orig.pts.map(function(q){ return [Math.round(logicoATiempo(q[0] + dl)), q[1] + dp]; });
        redibujarTodo(); return;
      }
      aplicarArrastreBase2(pos, e);
    };

    // Mouse abajo con el resaltador activo (fase de captura): empieza un trazo nuevo dentro del área de trazado y bloquea el gráfico.
    window.addEventListener('mousedown', function(e){
      if (activoHerramienta !== 'highlighter' || e.button !== 0 || bloqueado || !serie || !datosActuales.length) return;
      if (!contenedorEl.contains(e.target)) return;
      if (e.target.closest && e.target.closest('.tradingview-ui')) return;
      var pos = posicionRaton(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      e.preventDefault(); e.stopPropagation();
      bloquearGrafico(true);
      seleccionadoId = null; encimaId = null;
      trazoResaltador = { pts: [], color: estiloResaltador.color, ancho: estiloResaltador.ancho, ultimoPx: null };
      var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
      if (l !== null && p !== null) trazoResaltador.pts.push({ l: l, p: p });
    }, true);

    // Mouse move: suma puntos al trazo del resaltador (separados al menos 3 px) mientras el botón izquierdo siga pulsado.
    window.addEventListener('mousemove', function(e){
      if (!trazoResaltador) return;
      if (activoHerramienta !== 'highlighter') { trazoResaltador = null; bloquearGrafico(false); redibujarTodo(); return; }
      if (!(e.buttons & 1)) { finalizarResaltador(); return; }
      var pos = posicionRaton(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      var u = trazoResaltador.ultimoPx;
      if (u && Math.hypot(pos.x - u.x, pos.y - u.y) < 3) return;
      trazoResaltador.ultimoPx = { x: pos.x, y: pos.y };
      var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
      if (l !== null && p !== null) { trazoResaltador.pts.push({ l: l, p: p }); redibujarTodo(); }
    });

    // TITULO FINALIZAR RESALTADOR

    /** Termina el trazo del resaltador: convierte sus puntos a (tiempo, precio), agrega el dibujo 'highlighter', lo selecciona, confirma el cambio y vuelve a la cruz (o conserva el resaltador si "mantener" está activo). */
    function finalizarResaltador(){
      if (!trazoResaltador) return;
      var t = trazoResaltador; trazoResaltador = null;
      bloquearGrafico(false);
      var puntos = t.pts.map(function(q){ return [Math.round(logicoATiempo(q.l)), Math.round(q.p * 1e8) / 1e8]; });
      if (!puntos.length) { redibujarTodo(); return; }
      if (puntos.length === 1) puntos.push([puntos[0][0], puntos[0][1]]);
      elementosDibujados.push({ tipo: 'highlighter', puntos: puntos, color: t.color, ancho: t.ancho });
      seleccionadoId = elementosDibujados.length - 1;
      confirmarCambio();
      activarHerramienta(mantenerHerramienta ? 'highlighter' : 'cross');
    }

    // Al soltar el botón del ratón se termina el trazo del resaltador.
    window.addEventListener('mouseup', function(){ finalizarResaltador(); });

    // Configuración de las flechas de marca (arriba, abajo, izquierda, derecha): color y símbolo de cada una.
    var ARROW_CONFIGURACION = {
      arrow_up:    { color: '#3fb950', label: '▲' },
      arrow_down:  { color: '#f85149', label: '▼' },
      arrow_left:  { color: '#58a6ff', label: '◄' },
      arrow_right: { color: '#ff9800', label: '►' }
    };
    // Registra el color por defecto, el tamaño por defecto (14) y la edición de color de cada tipo de flecha en las tablas de la barra de estilos.
    Object.keys(ARROW_CONFIGURACION).forEach(function(t){
      COLOR_DEF[t] = ARROW_CONFIGURACION[t].color;
      ANCHO_DEF[t] = 14;
      TIPOS_COLOR[t] = 1;
    });

    // Trazadores del triángulo de cada flecha: cada función define el camino (path) en el contexto c con centro (x, y) y radio r.
    var ARROW_DIRS = {
      // Triángulo apuntando hacia arriba.
      arrow_up:    function(c, x, y, r){ c.moveTo(x, y - r); c.lineTo(x + r * 0.75, y + r * 0.6); c.lineTo(x - r * 0.75, y + r * 0.6); c.closePath(); },
      // Triángulo apuntando hacia abajo.
      arrow_down:  function(c, x, y, r){ c.moveTo(x, y + r); c.lineTo(x + r * 0.75, y - r * 0.6); c.lineTo(x - r * 0.75, y - r * 0.6); c.closePath(); },
      // Triángulo apuntando hacia la izquierda.
      arrow_left:  function(c, x, y, r){ c.moveTo(x - r, y); c.lineTo(x + r * 0.6, y - r * 0.75); c.lineTo(x + r * 0.6, y + r * 0.75); c.closePath(); },
      // Triángulo apuntando hacia la derecha.
      arrow_right: function(c, x, y, r){ c.moveTo(x + r, y); c.lineTo(x - r * 0.6, y - r * 0.75); c.lineTo(x - r * 0.6, y + r * 0.75); c.closePath(); }
    };

    // TITULO COORD FLECHA

    /** Devuelve la posición en pantalla { x, y } de una flecha de marca, o null si no es visible o válida. Recibe el dibujo. */
    function coordenadaFlecha(el){
      var x = xDeTiempo(el.time1), y = yDePrecio(el.price1);
      return ok(x, y) ? { x: x, y: y } : null;
    }

    // TITULO DIBUJAR FLECHA

    /** Pinta una flecha de marca como triángulo relleno en su punto (más opaco y con borde blanco y tirador si está seleccionada) y su etiqueta de precio en el eje. Recibe contexto, dibujo, selección y hover. */
    function dibujarFlecha(c, el, sel, hov){
      var g = coordenadaFlecha(el); if (!g) return;
      var configuracion = ARROW_CONFIGURACION[el.tipo], col = el.color || configuracion.color;
      var r = (el.ancho || 14) + (hov && !sel ? 2 : 0);
      c.save();
      c.beginPath();
      ARROW_DIRS[el.tipo](c, g.x, g.y, r);
      c.fillStyle = col;
      c.globalAlpha = sel ? 1 : 0.85;
      c.fill();
      if (sel) {
        c.strokeStyle = '#ffffff'; c.lineWidth = 1.5; c.globalAlpha = 0.9; c.stroke();
        dibujarHandle(c, g.x, g.y, col);
      }
      c.restore();
      insigniaPrecio(c, g.y, el.price1, col, '#fff', areaTrazado());
    }

    // TITULO HIT FLECHA

    /** Prueba si el punto (x, y) toca una flecha de marca (círculo de radio igual a su tamaño más 6 px). Devuelve true o false. */
    function impactoFlecha(el, x, y){
      var g = coordenadaFlecha(el); if (!g) return false;
      var r = (el.ancho || 14) + 6;
      return Math.hypot(x - g.x, y - g.y) <= r;
    }

    // Se extienden por tercera vez dibujarElemento y hitTest, ahora con las flechas de marca.
    var dibujarElementoBase3 = dibujarElemento;
    /** Versión de dibujarElemento que pinta las flechas de marca con dibujarFlecha y delega el resto. */
    dibujarElemento = function(c, el, sel, hov){
      if (ARROW_CONFIGURACION[el.tipo]) { dibujarFlecha(c, el, sel, hov); return; }
      dibujarElementoBase3(c, el, sel, hov);
    };

    var impactoPruebaBase3 = impactoPrueba;
    /** Versión de hitTest que detecta las flechas de marca con hitFlecha y delega el resto. */
    impactoPrueba = function(el, x, y, sel){
      if (ARROW_CONFIGURACION[el.tipo]) return impactoFlecha(el, x, y) ? 'body' : null;
      return impactoPruebaBase3(el, x, y, sel);
    };


/* -------------------------------------------------------------------------------------------------------
   ----------------------- FIN Piña y Jara 25_dibujo_pincel_resaltador_flechas .JS -----------------------
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
