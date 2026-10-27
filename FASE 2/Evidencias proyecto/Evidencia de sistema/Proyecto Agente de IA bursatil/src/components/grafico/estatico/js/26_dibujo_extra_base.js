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
   ----------------------------- INICIO Piña y Jara 26_dibujo_extra_base .JS -----------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Dibujo: infraestructura de herramientas adicionales (registro, pintado, selección, arrastre y creación)
    // Cada herramienta nueva se declara con `regHerramienta(id, {...})` (ver 27_ y 28_). Una herramienta describe su
    // forma como una lista de "primitivas" y este archivo se encarga de pintarla, detectar clics, moverla y editarla.
    //   n          nº de puntos fijos (time1/price1 … timeN/priceN)       v: true -> nº variable (el.puntos)
    //   ancla: true -> se fija a la pantalla (el.fx, el.fy en fracción del área)   texto: true -> tiene texto editable
    //   forma(el, P, S) -> primitivas:
    //     { k:'l', pts:[{x,y}..], d:'dash'|'dot', w, col, cerrar }  línea o polilínea
    //     { k:'f', pts, a, col }                                    relleno (a = opacidad)
    //     { k:'t', x, y, txt, col, bg, size, bold, al:'c'|'l'|'r' } texto (con fondo opcional)
    //     { k:'c', x, y, r, a, col }                                círculo (a = opacidad del relleno)
    //     { k:'p', draw(c), hit(x,y) }                              pintado libre
    // Registro de herramientas adicionales: id -> descriptor (n, v, ancla, texto, forma...) registrado con regHerramienta.
    var REG = {};
    // Emoji o icono elegido en el selector; es el texto que usará la herramienta 'emoji' al colocarse.
    var emojiActual = '😀';

    /** Registra una herramienta adicional: guarda su descriptor en REG y da de alta sus valores por defecto en las tablas compartidas (puntos de la herramienta, color, grosor, estilo y qué opciones admite la barra de estilos). Recibe el id y el descriptor (n, v, ancla, crea, col, w, estilo, sinColor, sinGrosor...). */
    function regHerramienta(id, o){
      o.id = id;
      REG[id] = o;
      if (o.n && !o.v && !o.ancla) TOOL_POINTS[id] = o.crea || o.n;   // crea: clics para crearla (el resto se completa solo)
      COLOR_DEF[id] = o.col || '#2962ff';
      if (o.w) ANCHO_DEF[id] = o.w;
      if (o.estilo === 'dash') ESTILO_DEF[id] = 'dash';
      if (!o.sinColor) TIPOS_COLOR[id] = 1;
      if (!o.sinGrosor) { TIPOS_ANCHO[id] = 1; TIPOS_TRAZO[id] = 1; }
    }

    // ---------- Utilidades de geometría ----------
    /** Devuelve un punto muy lejano en la dirección a -> b (más allá del borde de la pantalla); sirve para prolongar rayas y rectas. Recibe dos puntos {x, y}. */
    function lejos(a, b){   // punto muy lejano en la dirección a -> b
      var dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1, k = (cssW + cssH + 4000) / len;
      return { x: b.x + dx * k, y: b.y + dy * k };
    }
    /** Devuelve el punto medio entre dos puntos {x, y}. */
    function pMed(a, b){ return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }; }
    /** Suma a un punto a el vector d multiplicado por k (1 por defecto) y devuelve el nuevo punto. */
    function pMas(a, d, k){ return { x: a.x + d.x * (k === undefined ? 1 : k), y: a.y + d.y * (k === undefined ? 1 : k) }; }
    /** Resta dos puntos {x, y} (a menos b) y devuelve el vector resultante. */
    function pRes(a, b){ return { x: a.x - b.x, y: a.y - b.y }; }
    /** Formatea un cociente con 3 decimales (0 si no es finito) para mostrarlo en etiquetas. */
    function fmtRatio(v){ return (isFinite(v) ? v : 0).toFixed(3); }
    /** Formatea una diferencia de precio: en pips si PIP está definido, o con los decimales del símbolo. */
    function fmtPrecioDif(d){ return PIP > 0 ? (d / PIP).toFixed(1) + ' pips' : d.toFixed(DIGITS); }
    /** Cuenta cuántas barras separan dos tiempos UNIX (diferencia de índices lógicos redondeada; 0 si alguno es inválido). */
    function barrasEntreTiempos(t1, t2){
      var l1 = tiempoALogico(t1), l2 = tiempoALogico(t2);
      return (l1 === null || l2 === null) ? 0 : Math.round(l2 - l1);
    }
    /** Formatea una duración en segundos como texto con días, horas y minutos (por ejemplo "2 d 3 h 5 min"). */
    function fmtDuracion(seg){
      seg = Math.abs(Math.round(seg));
      var d = Math.floor(seg / 86400), h = Math.floor((seg % 86400) / 3600), m = Math.floor((seg % 3600) / 60);
      return (d ? d + ' d ' : '') + (h ? h + ' h ' : '') + ((m || (!d && !h)) ? m + ' min' : '');
    }
    /** Prueba si el punto (x, y) está dentro de un polígono (algoritmo de trazado de rayo). Recibe los vértices {x, y} y devuelve true o false. */
    function puntoEnPoligono(x, y, pts){
      var dentro = false;
      for (var i = 0, j = pts.length - 1; i < pts.length; j = i++){
        if (((pts[i].y > y) !== (pts[j].y > y)) && (x < (pts[j].x - pts[i].x) * (y - pts[i].y) / (pts[j].y - pts[i].y) + pts[i].x)) dentro = !dentro;
      }
      return dentro;
    }
    /** Genera n+1 puntos de un arco de círculo con centro c0, radio r y ángulos de a0 a a1 (radianes). Devuelve el arreglo de puntos {x, y}. */
    function muestrearArco(c0, r, a0, a1, n){
      var out = [];
      for (var i = 0; i <= n; i++){ var a = a0 + (a1 - a0) * i / n; out.push({ x: c0.x + r * Math.cos(a), y: c0.y + r * Math.sin(a) }); }
      return out;
    }

    // ---------- Puntos en pantalla ----------
    /** Alias de areaTrazado: devuelve el área útil de trazado { w, h } para uso de las herramientas registradas. */
    function areaTraz(){ return areaTrazado(); }
    /** Convierte los puntos de un dibujo registrado a coordenadas de pantalla: las herramientas ancladas usan una fracción del área (fx, fy); las de nº variable usan la lista el.puntos; el resto lee time1/price1...timeN/priceN. Devuelve null si algún punto no es válido. Aplica el ajuste ajustarP de la herramienta si lo define. */
    function puntosReg(el, r){
      if (r.ancla) {
        var ap = areaTrazado();
        return [{ x: (el.fx === undefined ? 0.1 : el.fx) * ap.w, y: (el.fy === undefined ? 0.1 : el.fy) * ap.h }];
      }
      var P = [], i, q;
      if (r.v) {
        var pts = el.puntos || [];
        for (i = 0; i < pts.length; i++){
          var x = xDeTiempo(pts[i][0]), y = yDePrecio(pts[i][1]);
          if (!ok(x, y)) return null;
          P.push({ x: x, y: y });
        }
        return P;
      }
      for (i = 1; i <= r.n; i++){
        if (el['time' + i] === undefined) break;
        q = puntoVisual(el, i);
        if (!ok(q.x, q.y)) return null;
        P.push(q);
      }
      if (r.ajustarP) r.ajustarP(el, P);
      return P;
    }

    /** Devuelve el estilo de trazo de un dibujo para las primitivas: 'dash', 'dot' o null (continuo). */
    function estiloPrim(el){
      var est = valorEfectivo(el, 'estilo');
      return est === 'dash' ? 'dash' : (est === 'dot' ? 'dot' : null);
    }
    /** Traza una polilínea (cerrada si se pide) con color, grosor y discontinuidad ('dash' o 'dot'); no hace nada con menos de 2 puntos. */
    function trazoLinea(c, pts, cerrar, col, w, dash){
      if (pts.length < 2) return;
      c.strokeStyle = col; c.lineWidth = w; c.lineCap = 'round'; c.lineJoin = 'round';
      c.setLineDash(dash === 'dash' ? [8, 5] : (dash === 'dot' ? [2, 4] : []));
      c.beginPath(); c.moveTo(pts[0].x, pts[0].y);
      for (var i = 1; i < pts.length; i++) c.lineTo(pts[i].x, pts[i].y);
      if (cerrar) c.closePath();
      c.stroke(); c.setLineDash([]);
    }
    /** Mide un texto de una primitiva (multilínea, con fuente, relleno y alineación) y devuelve su caja { lineas, x0, y0, w, h, pad, alto } para pintarlo y para el hit-test. */
    function medirTexto(c, p){
      c.font = (p.bold ? 'bold ' : '') + (p.size || 11) + 'px sans-serif';
      var lineas = String(p.txt === undefined ? '' : p.txt).split('\n'), w = 0;
      lineas.forEach(function(l){ w = Math.max(w, c.measureText(l).width); });
      var pad = p.bg ? (p.pad === undefined ? 5 : p.pad) : 0, alto = (p.size || 11) * 1.25;
      var ancho = w + pad * 2, altura = alto * lineas.length + pad * 2 - (p.bg ? 0 : 0);
      var x0 = p.al === 'c' ? p.x - ancho / 2 : (p.al === 'r' ? p.x - ancho : p.x);
      return { lineas: lineas, x0: x0, y0: p.y - altura / 2, w: ancho, h: altura, pad: pad, alto: alto };
    }

    /** Pinta una primitiva de la forma de una herramienta: 'l' línea o polilínea, 'f' relleno (respeta los ajustes de relleno del dibujo), 't' texto con fondo opcional, 'c' círculo y 'p' pintado libre. Recibe contexto, primitiva y el contexto de estilo S. */
    function pintarPrim(c, p, S){
      var col = p.col || S.col;
      if (p.k === 'l') {
        trazoLinea(c, p.pts, p.cerrar, col, (p.w || S.w) + S.hover, p.d !== undefined ? p.d : S.dash);
      } else if (p.k === 'f') {
        var elF = S.el, a0 = p.a === undefined ? 0.1 : p.a, solido = a0 >= 0.5;
        if (!solido && elF && elF.relleno === false) return;
        if (!solido && elF && elF.rellenoColor) col = elF.rellenoColor;
        if (!solido && elF && elF.rellenoOp !== undefined) a0 = Math.min(1, a0 * elF.rellenoOp / 0.1);
        c.save(); c.globalAlpha = a0; c.fillStyle = col;
        c.beginPath(); c.moveTo(p.pts[0].x, p.pts[0].y); for (var i = 1; i < p.pts.length; i++) c.lineTo(p.pts[i].x, p.pts[i].y);
        c.closePath(); c.fill(); c.restore();
      } else if (p.k === 't') {
        var m = medirTexto(c, p);
        if (p.bg) {
          c.fillStyle = p.bg;
          if (c.roundRect) { c.beginPath(); c.roundRect(m.x0, m.y0, m.w, m.h, p.radio === undefined ? 4 : p.radio); c.fill(); }
          else c.fillRect(m.x0, m.y0, m.w, m.h);
        }
        c.fillStyle = p.fg || (p.bg ? '#ffffff' : col); c.textBaseline = 'middle'; c.textAlign = 'left';
        m.lineas.forEach(function(l, k){ c.fillText(l, m.x0 + m.pad, m.y0 + m.pad + m.alto * (k + 0.5)); });
      } else if (p.k === 'c') {
        c.save(); c.beginPath(); c.arc(p.x, p.y, Math.max(0.5, p.r), 0, Math.PI * 2);
        if (p.a) { c.globalAlpha = p.a; c.fillStyle = col; c.fill(); c.globalAlpha = 1; }
        if (!p.sinTrazo) { c.strokeStyle = col; c.lineWidth = (p.w || S.w) + S.hover; c.setLineDash(p.d === 'dash' ? [8, 5] : []); c.stroke(); }
        c.restore();
      } else if (p.k === 'p') {
        c.save(); p.draw(c); c.restore();
      }
    }

    /** Prueba si el punto (x, y) toca una primitiva (tolerancia de 7 px): línea por distancia a sus segmentos, relleno por pertenencia al polígono, texto por su caja, círculo por su borde o su interior, y libre mediante su función hit. Devuelve true o false. */
    function tocaPrim(p, x, y){
      var tol = 7, i;
      if (p.k === 'l') {
        for (i = 1; i < p.pts.length; i++) if (distSeg(x, y, p.pts[i - 1].x, p.pts[i - 1].y, p.pts[i].x, p.pts[i].y) <= tol) return true;
        if (p.cerrar && p.pts.length > 2 && distSeg(x, y, p.pts[p.pts.length - 1].x, p.pts[p.pts.length - 1].y, p.pts[0].x, p.pts[0].y) <= tol) return true;
        return false;
      }
      if (p.k === 'f') return !p.sinTocar && puntoEnPoligono(x, y, p.pts);
      if (p.k === 't') { var m = medirTexto(ctx, p); return (!!p.bg || !!p.hitbox) && x >= m.x0 - 2 && x <= m.x0 + m.w + 2 && y >= m.y0 - 2 && y <= m.y0 + m.h + 2; }
      if (p.k === 'c') { var d = Math.hypot(x - p.x, y - p.y); return p.a ? d <= p.r + 4 : Math.abs(d - p.r) <= tol; }
      if (p.k === 'p') return p.hit ? p.hit(x, y) : false;
      return false;
    }

    /** Crea el contexto de estilo S de un dibujo registrado: dibujo, color, grosor, trazo efectivos, selección, hover, sobreancho de hover y área de trazado. */
    function contextoReg(el, sel, hov){
      return { el: el, col: valorEfectivo(el, 'color'), w: valorEfectivo(el, 'ancho'), dash: estiloPrim(el), sel: !!sel, hov: !!hov, hover: (hov && !sel) ? 1 : 0, ap: areaTrazado() };
    }
    // Si el usuario desactiva las etiquetas, se quitan los textos de la herramienta (salvo los marcados `fijo`)
    /** Filtra las primitivas de un dibujo: si el usuario desactivó las etiquetas (etiq === false) y la herramienta las admite, quita los textos salvo los marcados como fijos. Devuelve las primitivas resultantes. */
    function filtrarPrims(el, r, prims){
      if (el.etiq === false && r.etiquetas) return prims.filter(function(p){ return p.k !== 't' || p.fijo; });
      return prims;
    }
    /** Calcula las primitivas de un dibujo registrado sin pintarlas, para el hit-test; devuelve una lista vacía si la función forma falla. Recibe el dibujo y sus puntos en pantalla. */
    function primitivasReg(el, P){
      var r = REG[el.tipo], S = contextoReg(el, false, false);
      S.W = S.ap.w; S.H = S.ap.h;
      try { return filtrarPrims(el, r, r.forma(el, P, S) || []); } catch (e) { return []; }
    }
    /** Indica si un dibujo debe mostrarse en la temporalidad actual: visible si no tiene restricción o si visibleEnTF (definida en otro fragmento) lo permite. */
    function dibujoVisibleTF(el){ return !el.vis || typeof visibleEnTF !== 'function' || visibleEnTF(el); }

    // ---------- Enganche en el pintado / hit / arrastre existentes ----------
    // Se extienden por última vez las funciones centrales (dibujo, hit-test, anclas, arrastre, pegado) para soportar las herramientas del registro REG; los tipos no registrados se delegan a la versión anterior.
    var dibujarElementoAntesExtra = dibujarElemento;
    /** Versión de dibujarElemento que, para herramientas registradas, calcula sus primitivas, las pinta y (si está seleccionada) añade tiradores en cada punto o un marco punteado si está fijada a la pantalla; para el resto delega en la anterior. */
    dibujarElemento = function(c, el, sel, hov){
      var r = REG[el.tipo];
      if (!dibujoVisibleTF(el)) return;
      if (!r) { dibujarElementoAntesExtra(c, el, sel, hov); return; }
      var P = puntosReg(el, r);
      if (!P || !P.length) return;
      var S = contextoReg(el, sel, hov); S.W = S.ap.w; S.H = S.ap.h;
      var prims;
      try { prims = filtrarPrims(el, r, r.forma(el, P, S) || []); } catch (e) { prims = []; }
      c.save();
      prims.forEach(function(p){ pintarPrim(c, p, S); });
      if (sel) {
        if (r.ancla) {
          // marco de selección de los elementos fijados a la pantalla
          var bb = cajaPrims(c, prims);
          if (bb) { c.strokeStyle = 'rgba(88,166,255,.8)'; c.lineWidth = 1; c.setLineDash([3, 3]); c.strokeRect(bb.x0 - 3, bb.y0 - 3, bb.x1 - bb.x0 + 6, bb.y1 - bb.y0 + 6); c.setLineDash([]); }
        } else {
          P.forEach(function(q){ dibujarHandle(c, q.x, q.y, S.col); });
        }
      }
      c.restore();
    };
    /** Calcula la caja envolvente { x0, y0, x1, y1 } de una lista de primitivas (textos, polilíneas, círculos y cajas); devuelve null si no hay ninguna. */
    function cajaPrims(c, prims){
      var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      /** Auxiliar local sumar: amplía la caja envolvente para incluir el punto (x, y). */
      function sumar(x, y){ if (x < x0) x0 = x; if (y < y0) y0 = y; if (x > x1) x1 = x; if (y > y1) y1 = y; }
      prims.forEach(function(p){
        if (p.k === 't') { var m = medirTexto(c, p); sumar(m.x0, m.y0); sumar(m.x0 + m.w, m.y0 + m.h); }
        else if (p.pts) p.pts.forEach(function(q){ sumar(q.x, q.y); });
        else if (p.k === 'c') { sumar(p.x - p.r, p.y - p.r); sumar(p.x + p.r, p.y + p.r); }
        else if (p.box) { sumar(p.box[0], p.box[1]); sumar(p.box[2], p.box[3]); }
      });
      return x0 === Infinity ? null : { x0: x0, y0: y0, x1: x1, y1: y1 };
    }

    var hitTestAntesExtra = hitTest;
    /** Versión de hitTest que, para herramientas registradas, detecta tiradores (p1, p2...) del dibujo seleccionado y luego el cuerpo (primitiva más alta primero); para el resto delega en la anterior. */
    hitTest = function(el, x, y, sel){
      var r = REG[el.tipo];
      if (!dibujoVisibleTF(el)) return null;
      if (!r) return hitTestAntesExtra(el, x, y, sel);
      var P = puntosReg(el, r);
      if (!P || !P.length) return null;
      if (sel && !r.ancla) {
        for (var i = 0; i < P.length; i++) if (Math.hypot(x - P[i].x, y - P[i].y) <= 10) return 'p' + (i + 1);
      }
      var prims = primitivasReg(el, P);
      for (var k = prims.length - 1; k >= 0; k--) if (tocaPrim(prims[k], x, y)) return 'body';
      return null;
    };

    var anclasAntesExtra = anclasOriginales;
    /** Versión de anclasOriginales que, para herramientas registradas, guarda la posición inicial: fracción (fx, fy) si está anclada a pantalla, puntos (índice lógico, precio) si es variable o L/Pr para las de puntos fijos; para el resto delega. */
    anclasOriginales = function(el){
      var r = REG[el.tipo];
      if (!r) return anclasAntesExtra(el);
      if (r.ancla) return { fx: el.fx, fy: el.fy };
      if (r.v) return { pts: (el.puntos || []).map(function(q){ return [tiempoALogico(q[0]), q[1]]; }) };
      var L = [], Pr = [];
      for (var i = 1; i <= r.n; i++){ L.push(el['time' + i] === undefined ? null : tiempoALogico(el['time' + i])); Pr.push(el['price' + i]); }
      return { L: L, Pr: Pr };
    };

    var arrastreAntesExtra = aplicarArrastre;
    /** Versión de aplicarArrastre que mueve o edita un dibujo registrado: arrastre completo (en pantalla o por barras y precio) o de un tirador concreto; para el resto delega en la anterior. Recibe la posición del ratón y el evento. */
    aplicarArrastre = function(pos, e){
      var el = arrastre ? elementosDibujados[arrastre.idx] : null, r = el ? REG[el.tipo] : null;
      if (!r) { arrastreAntesExtra(pos, e); return; }
      var o = arrastre.orig;
      if (arrastre.modo === 'move') {
        if (r.ancla) {
          var ap = areaTrazado();
          el.fx = Math.max(0, Math.min(1, o.fx + (pos.x - arrastre.x0) / Math.max(1, ap.w)));
          el.fy = Math.max(0, Math.min(1, o.fy + (pos.y - arrastre.y0) / Math.max(1, ap.h)));
        } else {
          var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
          if (l === null || p === null) return;
          var dl = l - arrastre.l0, dp = p - arrastre.p0;
          if (r.v) el.puntos = o.pts.map(function(q){ return [Math.round(logicoATiempo(q[0] + dl)), q[1] + dp]; });
          else o.L.forEach(function(lq, i){ if (lq !== null) { el['time' + (i + 1)] = logicoATiempo(lq + dl); el['price' + (i + 1)] = o.Pr[i] + dp; } });
        }
      } else {
        var pt = puntoDesdeMouse(pos.x, pos.y, magnetEfectivo(e)); if (!pt) return;
        var n = parseInt(arrastre.modo.slice(1), 10);
        if (r.v) { if (el.puntos[n - 1]) el.puntos[n - 1] = [Math.round(pt.time), pt.price]; }
        else { el['time' + n] = pt.time; el['price' + n] = pt.price; }
      }
      redibujarTodo();
    };

    var pegarAntesExtra = pegar;
    /** Versión de pegar que pega con desplazamiento las herramientas ancladas y las de puntos variables; para el resto delega en la versión anterior. */
    pegar = function(){
      if (portapapeles && !bloqueado && serie) {
        var e0 = JSON.parse(portapapeles), r = REG[e0.tipo];
        if (r && r.ancla) { e0.fx = Math.min(1, (e0.fx || 0) + 0.03); e0.fy = Math.min(1, (e0.fy || 0) + 0.04); elementosDibujados.push(e0); seleccionadoId = elementosDibujados.length - 1; confirmarCambio(); return; }
        if (r && r.v && e0.puntos && e0.puntos.length) {
          var yRef = yDePrecio(e0.puntos[0][1]), pDesp = ok(yRef) ? serie.coordinateToPrice(yRef + 24) : null, dp0 = pDesp !== null ? pDesp - e0.puntos[0][1] : 0;
          e0.puntos = e0.puntos.map(function(q){ var l = tiempoALogico(q[0]); return [l === null ? q[0] : Math.round(logicoATiempo(l + 4)), q[1] + dp0]; });
          elementosDibujados.push(e0); seleccionadoId = elementosDibujados.length - 1; confirmarCambio(); return;
        }
      }
      pegarAntesExtra();
    };

    // ---------- Editor de texto de las herramientas con texto ----------
    // Campo de entrada del editor de texto de las herramientas registradas; null si no hay ninguno abierto.
    var editorReg = null;
    /** Cierra y elimina del DOM el editor de texto de las herramientas registradas, si existe. */
    function cerrarEditorReg(){ if (editorReg && editorReg.parentNode) editorReg.parentNode.removeChild(editorReg); editorReg = null; }
    /** Calcula dónde mostrar el editor de texto de una herramienta registrada (primer o último punto, o una posición por defecto). Devuelve { x, y }. */
    function posicionTextoReg(el, r){
      var P = puntosReg(el, r);
      return (P && P.length) ? P[P.length > 1 && r.textoEnUltimo ? P.length - 1 : 0] : { x: 60, y: 60 };
    }
    /** Abre el editor (input o textarea multilínea) para el texto de una herramienta registrada. Recibe el índice del dibujo y si es nuevo (si se cancela o queda vacío un texto obligatorio, el dibujo nuevo se elimina). Enter (o Ctrl+Enter en multilínea) guarda, Escape cancela. */
    function editarTextoReg(idx, nuevo){
      cerrarEditorReg();
      var el = elementosDibujados[idx], r = el ? REG[el.tipo] : null;
      if (!r || !r.texto) return;
      var multi = !!r.multilinea, pos = posicionTextoReg(el, r);
      var inp = document.createElement(multi ? 'textarea' : 'input');
      if (!multi) inp.type = 'text';
      inp.className = 'tv-texto-input tv-ui';
      inp.value = el.texto === undefined ? (r.textoDef || '') : el.texto;
      inp.placeholder = multi ? 'Una fila por línea; columnas separadas por |' : 'Escribe y pulsa Enter';
      inp.style.fontSize = '13px'; inp.style.color = '#e6edf3';
      inp.style.left = Math.round(Math.max(4, pos.x - 5)) + 'px'; inp.style.top = Math.round(Math.max(4, pos.y - 24)) + 'px';
      inp.style.width = multi ? '260px' : '220px';
      if (multi) { inp.rows = 4; inp.style.resize = 'both'; }
      wrapEl.appendChild(inp); editorReg = inp;
      var terminado = false;
      /** Cierra el editor una sola vez; guarda el texto si cambió (confirmando el cambio) y elimina el dibujo nuevo si se cancela o queda vacío un texto obligatorio. Recibe true para guardar y false para descartar. */
      function cerrar(guardar){
        if (terminado) return; terminado = true;
        var valor = inp.value.replace(/\s+$/, '');
        if (inp.parentNode) inp.parentNode.removeChild(inp);
        if (editorReg === inp) editorReg = null;
        var actual = elementosDibujados[idx];
        if (actual !== el) return;
        if (!guardar) { if (nuevo && r.textoObligatorio) { elementosDibujados.splice(idx, 1); seleccionadoId = null; confirmarCambio(); } else redibujarTodo(); return; }
        if (!valor && r.textoObligatorio) { if (nuevo) { elementosDibujados.splice(idx, 1); seleccionadoId = null; confirmarCambio(); } else redibujarTodo(); return; }
        if (el.texto !== valor) { el.texto = valor; confirmarCambio(); } else redibujarTodo();
      }
      // Teclado del editor: Enter (o Ctrl+Enter en multilínea) guarda y Escape cancela, sin propagar al resto de atajos.
      inp.addEventListener('keydown', function(e){
        e.stopPropagation();
        if (e.key === 'Enter' && (!multi || e.ctrlKey)) { e.preventDefault(); cerrar(true); }
        else if (e.key === 'Escape') cerrar(false);
      });
      // Al perder el foco el editor guarda.
      inp.addEventListener('blur', function(){ cerrar(true); });
      // Da foco y selecciona el texto en el siguiente ciclo.
      setTimeout(function(){ inp.focus(); inp.select(); }, 0);
    }

    // doble clic sobre una herramienta con texto: editarlo
    // Doble clic sobre cualquier dibujo (fase de captura): lo selecciona y abre la ventana de ajustes (o, si no existe, el editor de texto de la herramienta).
    wrapEl.addEventListener('dblclick', function(e){
      if (bloqueado || activeTool !== 'cross') return;
      if (e.target && e.target.closest && e.target.closest('.tv-ui')) return;
      var pos = posMouse(e), hit = elementoBajo(pos.x, pos.y);
      if (hit) {   // doble clic sobre cualquier dibujo: ventana de ajustes (estilo, coordenadas, visibilidad)
        e.preventDefault(); e.stopPropagation();
        seleccionadoId = hit.idx; redibujarTodo();
        if (typeof abrirAjustesDibujo === 'function') abrirAjustesDibujo(hit.idx);
        else if (REG[elementosDibujados[hit.idx].tipo] && REG[elementosDibujados[hit.idx].tipo].texto) editarTextoReg(hit.idx, false);
      }
    }, true);

    // tras terminar de dibujar una herramienta con texto, se pide el texto
    // Guarda la versión anterior de finalizarDibujo.
    var finalizarDibujoAntesExtra = finalizarDibujo;
    /** Versión de finalizarDibujo que ejecuta el gancho alFinalizar de la herramienta, delega en la anterior y, si la herramienta tiene texto, abre el editor para pedirlo. Recibe true si el dibujo se completó. */
    finalizarDibujo = function(valido){
      var d = dibujoEnCurso;
      if (valido && d && REG[d.tipo] && REG[d.tipo].alFinalizar) REG[d.tipo].alFinalizar(d);
      finalizarDibujoAntesExtra(valido);
      if (valido && d && REG[d.tipo] && REG[d.tipo].texto) {
        var idx = elementosDibujados.indexOf(d);
        if (idx >= 0) editarTextoReg(idx, true);
      }
    };

    // ---------- Colocación inmediata (1 punto, fijadas a pantalla), polilíneas y zoom ----------
    // Dibujo de polilínea en curso { tipo, puntos [[t, p]...], flotante [t, p] o null }.
    var enCursoVar = null;   // { tipo, puntos:[[t,p]..], flotante:[t,p]|null }
    // Rectángulo de zoom en curso { x0, y0, x1, y1 } en píxeles; null si no se está haciendo zoom.
    var rectZoom = null;
    /** Agrega un dibujo ya completo (herramientas de un clic o ancladas), lo selecciona, confirma el cambio, abre el editor de texto si la herramienta lo tiene y vuelve a la cruz salvo que "mantener" esté activo. Recibe el dibujo. */
    function colocarElemento(el){
      elementosDibujados.push(el); seleccionadoId = elementosDibujados.length - 1; confirmarCambio();
      var r = REG[el.tipo];
      if (r && r.texto) editarTextoReg(seleccionadoId, true);
      if (!mantenerHerramienta) activarHerramienta('cross');
    }
    /** Cancela la polilínea en curso, si hay, y repinta. */
    function cancelarVariable(){ if (enCursoVar) { enCursoVar = null; redibujarTodo(); } }
    /** Termina la polilínea en curso: quita el último punto si el doble clic lo duplicó, la guarda si tiene al menos 2 puntos y vuelve a la cruz (o conserva la herramienta con "mantener"). */
    function terminarVariable(){
      if (!enCursoVar) return;
      var v = enCursoVar; enCursoVar = null;
      var pts = v.puntos.slice();
      // el doble clic añade el último punto dos veces: se quita el duplicado
      if (pts.length >= 2) {
        var a = pts[pts.length - 1], b = pts[pts.length - 2];
        var xa = xDeTiempo(a[0]), ya = yDePrecio(a[1]), xb = xDeTiempo(b[0]), yb = yDePrecio(b[1]);
        if (ok(xa, ya, xb, yb) && Math.hypot(xa - xb, ya - yb) < 8) pts.pop();
      }
      if (pts.length >= 2) {
        elementosDibujados.push({ tipo: v.tipo, puntos: pts });
        seleccionadoId = elementosDibujados.length - 1; confirmarCambio();
      } else redibujarTodo();
      activarHerramienta(mantenerHerramienta ? v.tipo : 'cross');
    }

    // Mouse abajo (fase de captura) con una herramienta registrada o el zoom: inicia el rectángulo de zoom, coloca de inmediato las herramientas de un clic o ancladas, o agrega un vértice a las de nº variable. Las de varios puntos fijos siguen el flujo normal.
    window.addEventListener('mousedown', function(e){
      var tool = activeTool, r = REG[tool];
      var esZoom = tool === 'zoom';
      if ((!r && !esZoom) || e.button !== 0 || bloqueado || !serie || !datosActuales.length) return;
      if (!wrapEl.contains(e.target) || (e.target.closest && e.target.closest('.tv-ui'))) return;
      var pos = posMouse(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      if (esZoom) { e.preventDefault(); e.stopPropagation(); bloquearGrafico(true); rectZoom = { x0: pos.x, y0: pos.y, x1: pos.x, y1: pos.y }; return; }
      var inmediata = r.ancla || (r.n === 1 && !r.v);
      if (!inmediata && !r.v) return;   // las de varios puntos fijos siguen el flujo de creación existente
      e.preventDefault(); e.stopPropagation();
      if (r.ancla) {
        colocarElemento({ tipo: tool, fx: pos.x / ap.w, fy: pos.y / ap.h, texto: r.textoDef || '' });
        return;
      }
      var pt = puntoDesdeMouse(pos.x, pos.y, magnetEfectivo(e)); if (!pt) return;
      if (r.v) {
        seleccionadoId = null;
        if (!enCursoVar) enCursoVar = { tipo: tool, puntos: [], flotante: null };
        var ult = enCursoVar.puntos[enCursoVar.puntos.length - 1];
        enCursoVar.puntos.push([Math.round(pt.time), pt.price]);
        enCursoVar.flotante = null; redibujarTodo();
        return;
      }
      var el = { tipo: tool, time1: pt.time, price1: pt.price };
      if (tool === 'emoji') el.texto = emojiActual;
      colocarElemento(el);
    }, true);

    // Mouse move: actualiza el rectángulo de zoom o el punto flotante de la polilínea en curso.
    window.addEventListener('mousemove', function(e){
      if (rectZoom) { var p = posMouse(e); rectZoom.x1 = p.x; rectZoom.y1 = p.y; redibujarTodo(); return; }
      if (!enCursoVar) return;
      if (activeTool !== enCursoVar.tipo) { cancelarVariable(); return; }
      var pos = posMouse(e), pt = puntoDesdeMouse(pos.x, pos.y, magnetEfectivo(e));
      if (pt) { enCursoVar.flotante = [Math.round(pt.time), pt.price]; redibujarTodo(); }
    });

    // Mouse up: cierra el rectángulo de zoom y, si mide más de 8 px y abarca al menos 3 barras, ajusta el rango visible del gráfico a esa zona; luego vuelve a la cruz.
    window.addEventListener('mouseup', function(e){
      if (!rectZoom) return;
      var z = rectZoom; rectZoom = null; bloquearGrafico(false);
      if (Math.abs(z.x1 - z.x0) > 8) {
        var ts = chart.timeScale(), l0 = ts.coordinateToLogical(Math.min(z.x0, z.x1)), l1 = ts.coordinateToLogical(Math.max(z.x0, z.x1));
        if (l0 !== null && l1 !== null && l1 - l0 >= 3) ts.setVisibleLogicalRange({ from: l0, to: l1 });
      }
      activarHerramienta('cross'); redibujarTodo();
    });

    // Doble clic (fase de captura) termina la polilínea en curso.
    wrapEl.addEventListener('dblclick', function(e){
      if (!enCursoVar) return;
      e.preventDefault(); e.stopPropagation(); terminarVariable();
    }, true);
    // Teclado: Enter termina y Escape cancela la polilínea en curso (se ignoran los campos de texto).
    document.addEventListener('keydown', function(e){
      var tag = (e.target && e.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      if (e.key === 'Enter' && enCursoVar) { e.preventDefault(); terminarVariable(); }
      else if (e.key === 'Escape' && enCursoVar) cancelarVariable();
    });
    // Guarda la versión anterior de activarHerramienta.
    var activarHerramientaAntesExtra = activarHerramienta;
    /** Versión de activarHerramienta que cancela la polilínea o el zoom pendientes al cambiar de herramienta y delega en la anterior. Recibe el nombre de la herramienta. */
    activarHerramienta = function(t){
      if (enCursoVar && enCursoVar.tipo !== t) cancelarVariable();
      if (rectZoom && t !== 'zoom') rectZoom = null;
      activarHerramientaAntesExtra(t);
    };

    // Guarda la versión anterior de pintar.
    var pintarAntesExtra = pintar;
    /** Versión de pintar que, tras pintar lo normal, dibuja la polilínea en curso con su punto flotante y el rectángulo de zoom (relleno y borde punteado). */
    pintar = function(){
      pintarAntesExtra();
      if (!dibujosVisibles || !serie) return;
      var ap = areaTrazado();
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, ap.w, ap.h); ctx.clip();
      if (enCursoVar) {
        var tmp = { tipo: enCursoVar.tipo, puntos: enCursoVar.puntos.concat(enCursoVar.flotante ? [enCursoVar.flotante] : []) };
        if (tmp.puntos.length) dibujarElemento(ctx, tmp, true, false);
      }
      if (rectZoom) {
        var x = Math.min(rectZoom.x0, rectZoom.x1), w = Math.abs(rectZoom.x1 - rectZoom.x0);
        ctx.fillStyle = 'rgba(88,166,255,0.15)'; ctx.fillRect(x, 0, w, ap.h);
        ctx.strokeStyle = 'rgba(88,166,255,0.8)'; ctx.lineWidth = 1; ctx.setLineDash([4, 3]); ctx.strokeRect(x, 0, w, ap.h); ctx.setLineDash([]);
      }
      ctx.restore();
    };

    // ---------- Selector de iconos / emojis ----------
    // ---------- Selector de iconos / emojis ----------
    /** Función autoejecutable que conecta el menú de emojis (#icons-flyout) con su botón (#tool-icons): al elegir un emoji lo guarda en emojiActual, activa la herramienta 'emoji' y muestra el emoji elegido en el botón. No hace nada si falta el menú o el botón. */
    (function(){
      var menu = document.getElementById('icons-flyout'), boton = document.getElementById('tool-icons');
      if (!menu || !boton) return;
      menu.querySelectorAll('.emoji-item').forEach(function(b){
        b.addEventListener('click', function(e){
          e.stopPropagation();
          emojiActual = b.getAttribute('data-emoji');
          menu.classList.remove('show');
          activarHerramienta('emoji');
          boton.innerHTML = '<span class="emoji-actual">' + emojiActual + '</span><span class="tvtool-arrow">▼</span>';
          boton.classList.add('active');
        });
      });
    })();

/* -------------------------------------------------------------------------------------------------------
   ------------------------------- FIN Piña y Jara 26_dibujo_extra_base .JS ------------------------------
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
