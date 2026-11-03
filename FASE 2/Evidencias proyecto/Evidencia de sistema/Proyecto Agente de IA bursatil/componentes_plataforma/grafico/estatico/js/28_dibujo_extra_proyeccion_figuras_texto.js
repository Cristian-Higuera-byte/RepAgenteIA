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
   ------------------- INICIO Piña y Jara 28_dibujo_extra_proyeccion_figuras_texto .JS -------------------
   ------------------------------------------------------------------------------------------------------- */

    // TITULO CABEZA FLECHA

// [grafico] Dibujo: proyección, medidor, flechas, figuras, textos y notas, iconos
    /** Devuelve los tres vértices de la punta de una flecha: la punta en (x, y) y dos alas separadas 30 grados del ángulo ang, con longitud tam. */
    function cabezaFlecha(x, y, ang, tam){
      return [{ x: x, y: y }, { x: x - tam * Math.cos(ang - Math.PI / 6), y: y - tam * Math.sin(ang - Math.PI / 6) },
              { x: x - tam * Math.cos(ang + Math.PI / 6), y: y - tam * Math.sin(ang + Math.PI / 6) }];
    }
    // TITULO FLECHA PRIMS

    /** Crea las primitivas de una flecha entre a y b: la línea y una punta triangular rellena (tamaño 10 por defecto, color opcional). */
    function flechaPrims(a, b, tam, col){
      var ang = Math.atan2(b.y - a.y, b.x - a.x);
      return [{ k: 'l', pts: [a, b], col: col }, { k: 'f', pts: cabezaFlecha(b.x, b.y, ang, tam || 10), a: 1, col: col, sinTocar: true }];
    }
    // TITULO RECT PTS

    /** Devuelve los cuatro vértices de un rectángulo alineado a los ejes, empezando arriba a la izquierda y siguiendo el sentido horario. */
    function rectPuntos(x0, y0, x1, y1){ return [{ x: x0, y: y0 }, { x: x1, y: y0 }, { x: x1, y: y1 }, { x: x0, y: y1 }]; }
    // TITULO SIGNO

    /** Devuelve '+' si el valor es positivo o cero y cadena vacía si es negativo (el signo menos ya lo trae el número). */
    function signo(v){ return v >= 0 ? '+' : ''; }
    // TITULO TEXTO CAMBIO

    /** Genera el texto de cambio entre los puntos i y j del dibujo: diferencia de precio (pips o decimales) y porcentaje respecto al punto i, con signo. */
    function textoCambio(el, i, j){
      var diferencia = pr(el, j) - pr(el, i), pct = pr(el, i) ? diferencia / pr(el, i) * 100 : 0;
      return signo(diferencia) + formatoPrecioDiferencia(diferencia) + ' (' + signo(pct) + pct.toFixed(2) + '%)';
    }

    // TITULO FORMA POSICION

    // ================= PROYECCIÓN =================
    /** Crea la función de forma de una posición larga (compra) o corta (venta): dibuja la zona de objetivo en verde, la de stop en rojo, la línea de entrada y etiquetas con objetivo, stop y relación riesgo/beneficio. Recibe true para larga y false para corta; devuelve una función (el, P, S). */
    function formaPosicion(largo){
      return function(el, P, S){
        if (P.length < 2) return [{ k: 'l', pts: P }];
        var xa = Math.min(P[0].x, P[1].x), xb = Math.max(P[0].x, P[1].x); if (xb - xa < 40) xb = xa + 40;
        var y0 = P[0].y, yT = P[1].y, pStop = el.price3 !== undefined ? el.price3 : 2 * pr(el, 1) - pr(el, 2), yS = yDePrecio(pStop);
        if (!ok(yS)) return [];
        var gan = largo ? pr(el, 2) - pr(el, 1) : pr(el, 1) - pr(el, 2), per = largo ? pStop - pr(el, 1) : pr(el, 1) - pStop;
        var riesgoBeneficio = per ? Math.abs(gan / per) : 0, porcentajeG = pr(el, 1) ? gan / pr(el, 1) * 100 : 0, porcentajeP = pr(el, 1) ? per / pr(el, 1) * 100 : 0;
        var cx = (xa + xb) / 2, cO = el.colObj || '#089981', cS = el.colStop || '#f23645';
        return [
          { k: 'f', pts: rectPuntos(xa, y0, xb, yT), a: 0.2, col: cO }, { k: 'f', pts: rectPuntos(xa, y0, xb, yS), a: 0.2, col: cS },
          { k: 'l', pts: rectPuntos(xa, y0, xb, yT), cerrar: true, col: cO, w: 1 }, { k: 'l', pts: rectPuntos(xa, y0, xb, yS), cerrar: true, col: cS, w: 1 },
          { k: 'l', pts: [{ x: xa, y: y0 }, { x: xb, y: y0 }], col: '#8b949e', w: 1.5 },
          etq(cx, yT + (yT < y0 ? -12 : 12), 'Objetivo: ' + signo(gan) + formatoPrecioDiferencia(gan) + ' (' + signo(porcentajeG) + porcentajeG.toFixed(2) + '%)', '#fff', { bg: cO }),
          etq(cx, yS + (yS > y0 ? 12 : -12), 'Stop: ' + signo(per) + formatoPrecioDiferencia(per) + ' (' + signo(porcentajeP) + porcentajeP.toFixed(2) + '%)', '#fff', { bg: cS }),
          etq(cx, y0, (largo ? 'Compra' : 'Venta') + ' · R:R ' + riesgoBeneficio.toFixed(2), '#fff', { bg: 'rgba(80,88,100,0.95)' })
        ];
      };
    }
    // TITULO STOP POR DEFECTO

    /** Gancho alFinalizar de las posiciones larga y corta: fija el punto 3 (stop) por defecto a la mitad de la distancia del objetivo, en sentido contrario, sobre el mismo tiempo del punto 2. */
    function stopPorDefecto(d){ d.time3 = d.time2; d.price3 = d.price1 - (d.price2 - d.price1) / 2; }
    // Herramientas 'long_pos' y 'short_pos' (posición larga y corta): se crean con 2 clics y el stop (punto 3) se completa solo con stopPorDefecto.
    registroHerramienta('long_pos', { n: 3, crea: 2, alFinalizar: stopPorDefecto, col: '#089981', sinGrosor: true, forma: formaPosicion(true) });
    registroHerramienta('short_pos', { n: 3, crea: 2, alFinalizar: stopPorDefecto, col: '#f23645', sinGrosor: true, forma: formaPosicion(false) });

    // Herramienta 'forecast' (pronóstico): flecha del punto 1 al 2 con guías punteadas y etiqueta del cambio de precio, barras y duración.
    registroHerramienta('forecast', { n: 2, col: '#2962ff', forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      var sube = pr(el, 2) >= pr(el, 1), col = sube ? '#089981' : '#f23645', barras = barrasEntreTiempos(el.time1, el.time2);
      var seg = Math.abs(el.time2 - el.time1);
      return [{ k: 'l', pts: [{ x: P[0].x, y: P[0].y }, { x: P[1].x, y: P[0].y }], d: 'dot', w: 1, col: col }, { k: 'l', pts: [{ x: P[1].x, y: P[0].y }, P[1]], d: 'dot', w: 1, col: col }]
        .concat(flechaPrims(P[0], P[1], 11, col))
        .concat([etq(P[1].x, P[1].y + (sube ? -22 : 22), textoCambio(el, 1, 2) + '\n' + barras + ' barras · ' + formatoDuracion(seg), '#fff', { bg: col })]);
    } });

    // Herramienta 'barpattern' (patrón de barras): copia las velas del rango entre los puntos 1 y 2 y las proyecta desplazadas al precio del punto 3; dibuja el rango original punteado.
    registroHerramienta('barpattern', { n: 3, col: '#58a6ff', sinGrosor: true, forma: function(el, P, S){
      if (P.length < 3) return [{ k: 'f', pts: P.length > 1 ? rectPuntos(P[0].x, 0, P[1].x, S.H) : [], a: 0.08, sinTocar: true }].filter(function(p){ return p.pts.length; });
      var n = datosActuales.length, l1 = tiempoALogico(el.time1), l2 = tiempoALogico(el.time2);
      if (l1 === null || l2 === null || !n) return [];
      var i0 = Math.max(0, Math.round(Math.min(l1, l2))), i1 = Math.min(n - 1, Math.round(Math.max(l1, l2)));
      if (i1 <= i0) return [];
      var ts = chart.timeScale(), esp = Math.abs(ts.logicalToCoordinate(1) - ts.logicalToCoordinate(0)) || 6, ref = datosActuales[i0].open;
      var velas = [], ymin = Infinity, ymax = -Infinity, hi = -Infinity, lo = Infinity;
      for (var i = i0; i <= i1; i++){
        var d = datosActuales[i], x = P[2].x + (i - i0) * esp;
        var yo = yDePrecio(pr(el, 3) + d.open - ref), yc = yDePrecio(pr(el, 3) + d.close - ref), yh = yDePrecio(pr(el, 3) + d.high - ref), yl = yDePrecio(pr(el, 3) + d.low - ref);
        if (!ok(yo, yc, yh, yl)) continue;
        velas.push({ x: x, yo: yo, yc: yc, yh: yh, yl: yl, sube: d.close >= d.open });
        ymin = Math.min(ymin, yh); ymax = Math.max(ymax, yl);
        hi = Math.max(hi, d.high); lo = Math.min(lo, d.low);
      }
      var xr0 = ts.logicalToCoordinate(i0 - 0.5), xr1 = ts.logicalToCoordinate(i1 + 0.5), yr0 = yDePrecio(hi), yr1 = yDePrecio(lo);
      var prims = [];
      if (ok(xr0, xr1, yr0, yr1)) prims.push({ k: 'l', pts: rectPuntos(xr0, yr0, xr1, yr1), cerrar: true, d: 'dash', w: 1, col: '#8b949e' });
      if (!velas.length) return prims;
      var x0 = velas[0].x - esp, x1 = velas[velas.length - 1].x + esp;
      prims.push({ k: 'p', box: [x0, ymin, x1, ymax],
        // Pintado libre de las velas copiadas con su caja punteada.
        draw: function(c){
          c.globalAlpha = 0.75; var w = Math.max(1, esp * 0.65);
          velas.forEach(function(v){
            var col = v.sube ? '#3fb950' : '#f85149'; c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 1;
            c.beginPath(); c.moveTo(v.x, v.yh); c.lineTo(v.x, v.yl); c.stroke();
            c.fillRect(v.x - w / 2, Math.min(v.yo, v.yc), w, Math.max(1, Math.abs(v.yc - v.yo)));
          });
          c.globalAlpha = 1; c.strokeStyle = S.col; c.setLineDash([4, 3]); c.strokeRect(x0, ymin - 4, x1 - x0, ymax - ymin + 8); c.setLineDash([]);
        },
        // Detección de clic sobre la caja de las velas copiadas.
        hit: function(x, y){ return x >= x0 && x <= x1 && y >= ymin - 4 && y <= ymax + 4; } });
      return prims;
    } });

    // TITULO RNG SEMILLA

    // Pseudoaleatorio determinista: el "feed fantasma" no cambia entre repintados
    // Pseudoaleatorio determinista: el "feed fantasma" no cambia entre repintados
    /** Crea un generador pseudoaleatorio determinista (congruencial) a partir de una semilla. Devuelve una función que produce números en (0, 1) y que repite siempre la misma secuencia para la misma semilla. */
    function rangoSemilla(sem){
      var s = (Math.abs(Math.floor(sem)) % 2147483646) + 1;
      return function(){ s = (s * 48271) % 2147483647; return s / 2147483647; };
    }
    // TITULO NORMAL

    /** Genera un número con distribución normal estándar a partir de dos uniformes (transformación de Box-Muller). Recibe el generador y devuelve el valor. */
    function normal(rnd){ var u = Math.max(1e-9, rnd()), v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
    // Herramienta 'ghostfeed' (feed fantasma): simula velas entre los puntos 1 y 2 con un paseo aleatorio determinista (puente browniano) que termina en el precio del punto 2, con volatilidad estimada de las últimas 50 velas.
    registroHerramienta('ghostfeed', { n: 2, col: '#8b949e', sinGrosor: true, forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      var nb = Math.max(2, Math.min(300, Math.abs(barrasEntreTiempos(el.time1, el.time2))));
      var n = datosActuales.length, sum = 0, cnt = 0;
      for (var q = Math.max(0, n - 50); q < n; q++){ sum += datosActuales[q].high - datosActuales[q].low; cnt++; }
      var sigma = cnt ? sum / cnt * 0.6 : Math.abs(pr(el, 2) - pr(el, 1)) / nb;
      var rnd = rangoSemilla(el.time1), w = [0], k;
      for (k = 1; k <= nb; k++) w.push(w[k - 1] + normal(rnd) * sigma);
      var cierres = [pr(el, 1)];
      for (k = 1; k <= nb; k++) cierres.push(pr(el, 1) + (pr(el, 2) - pr(el, 1)) * k / nb + (w[k] - w[nb] * k / nb));
      var esp = (P[1].x - P[0].x) / nb, velas = [], ymin = Infinity, ymax = -Infinity;
      for (k = 1; k <= nb; k++){
        var o = cierres[k - 1], c2 = cierres[k], hh = Math.max(o, c2) + Math.abs(normal(rnd)) * sigma * 0.5, ll = Math.min(o, c2) - Math.abs(normal(rnd)) * sigma * 0.5;
        var x = P[0].x + (k - 0.5) * esp, yo = yDePrecio(o), yc = yDePrecio(c2), yh = yDePrecio(hh), yl = yDePrecio(ll);
        if (!ok(yo, yc, yh, yl)) continue;
        velas.push({ x: x, yo: yo, yc: yc, yh: yh, yl: yl, sube: c2 >= o }); ymin = Math.min(ymin, yh); ymax = Math.max(ymax, yl);
      }
      if (!velas.length) return [{ k: 'l', pts: P }];
      var xa = Math.min(P[0].x, P[1].x), xb = Math.max(P[0].x, P[1].x), anch = Math.max(1, Math.abs(esp) * 0.65);
      return [{ k: 'p', box: [xa, ymin, xb, ymax],
        // Pintado libre de las velas simuladas.
        draw: function(c){
          c.globalAlpha = 0.55;
          velas.forEach(function(v){
            var col = v.sube ? '#3fb950' : '#f85149'; c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 1;
            c.beginPath(); c.moveTo(v.x, v.yh); c.lineTo(v.x, v.yl); c.stroke(); c.fillRect(v.x - anch / 2, Math.min(v.yo, v.yc), anch, Math.max(1, Math.abs(v.yc - v.yo)));
          });
          c.globalAlpha = 1;
        },
        // Detección de clic sobre la zona de las velas simuladas.
        hit: function(x, y){ return x >= xa && x <= xb && y >= ymin - 4 && y <= ymax + 4; } },
        { k: 'l', pts: P, d: 'dot', w: 1 }, etq((xa + xb) / 2, ymin - 14, 'Ghost Feed (simulado)', '#8b949e')];
    } });

    // Herramienta 'projection' (proyección): copia el tramo A-B a partir del punto 3 con relleno, flecha y etiqueta del cambio.
    registroHerramienta('projection', { n: 3, col: '#a78bfa', forma: function(el, P, S){
      if (P.length < 3) return [{ k: 'l', pts: P }];
      var v = pResultado(P[1], P[0]), fin = pMas(P[2], v);
      return [{ k: 'f', pts: [P[0], P[1], fin, P[2]], a: 0.07 }, { k: 'l', pts: [P[0], P[1]] }]
        .concat(flechaPrims(P[2], fin, 10, S.col))
        .concat([{ k: 'l', pts: [P[0], P[2]], d: 'dot', w: 1 }, { k: 'l', pts: [P[1], fin], d: 'dot', w: 1 }, etq(fin.x, fin.y - 16, textoCambio(el, 1, 2), '#fff', { bg: S.col })]);
    } });

    // ================= MEDIDOR =================
    // Herramienta 'price_range' (rango de precio): rectángulo entre los dos precios con flecha vertical y etiqueta del cambio.
    registroHerramienta('price_range', { n: 2, col: '#2962ff', forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      var xa = Math.min(P[0].x, P[1].x), xb = Math.max(P[0].x, P[1].x), xm = (P[0].x + P[1].x) / 2, col = pr(el, 2) >= pr(el, 1) ? S.col : '#f23645';
      return [{ k: 'f', pts: rectPuntos(xa, P[0].y, xb, P[1].y), a: 0.1, col: col },
              { k: 'l', pts: [{ x: xa, y: P[0].y }, { x: xb, y: P[0].y }], col: col, w: 1 }, { k: 'l', pts: [{ x: xa, y: P[1].y }, { x: xb, y: P[1].y }], col: col, w: 1 }]
        .concat(flechaPrims({ x: xm, y: P[0].y }, { x: xm, y: P[1].y }, 8, col))
        .concat([etq(xm, (P[0].y + P[1].y) / 2, textoCambio(el, 1, 2), '#fff', { bg: col })]);
    } });
    // Herramienta 'date_range' (rango de fechas): banda vertical entre los dos tiempos con flecha horizontal, número de barras y duración.
    registroHerramienta('date_range', { n: 2, col: '#2962ff', forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      var ym = (P[0].y + P[1].y) / 2, y0 = Math.min(P[0].y, P[1].y) - 18, y1 = Math.max(P[0].y, P[1].y) + 18, b = barrasEntreTiempos(el.time1, el.time2);
      return [{ k: 'f', pts: rectPuntos(P[0].x, y0, P[1].x, y1), a: 0.08 },
              { k: 'l', pts: [{ x: P[0].x, y: y0 }, { x: P[0].x, y: y1 }], d: 'dash', w: 1 }, { k: 'l', pts: [{ x: P[1].x, y: y0 }, { x: P[1].x, y: y1 }], d: 'dash', w: 1 }]
        .concat(flechaPrims({ x: P[0].x, y: ym }, { x: P[1].x, y: ym }, 8, S.col))
        .concat([etq((P[0].x + P[1].x) / 2, ym - 16, Math.abs(b) + ' barras · ' + formatoDuracion(el.time2 - el.time1), '#fff', { bg: S.col })]);
    } });

    // ================= FLECHAS =================
    // Herramienta 'arrow_marker' (flecha ancha): flecha rellena con cola fina y cuello que se ensancha hasta la punta.
    registroHerramienta('arrow_marker', { n: 2, col: '#3fb950', sinGrosor: true, forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      var v = pResultado(P[1], P[0]), len = Math.hypot(v.x, v.y) || 1, u = { x: v.x / len, y: v.y / len }, nrm = { x: -u.y, y: u.x };
      var cuello = pMas(P[1], u, -Math.min(len * 0.45, 34)), tail = P[0];
      var pts = [pMas(tail, nrm, 2.5), pMas(cuello, nrm, 5), pMas(cuello, nrm, 12), P[1], pMas(cuello, nrm, -12), pMas(cuello, nrm, -5), pMas(tail, nrm, -2.5)];
      return [{ k: 'f', pts: pts, a: 0.92 }, { k: 'l', pts: pts, cerrar: true, w: 1 }];
    } });

    // ================= FIGURAS =================
    // Herramienta 'rotrect' (rectángulo rotado): la base la definen los puntos 1 y 2 y el tercero da la altura perpendicular.
    registroHerramienta('rotrect', { n: 3, col: '#58a6ff', forma: function(el, P, S){
      if (P.length < 3) return [{ k: 'l', pts: P }];
      var v = pResultado(P[1], P[0]), len = Math.hypot(v.x, v.y) || 1, nrm = { x: -v.y / len, y: v.x / len };
      var dist = (P[2].x - P[0].x) * nrm.x + (P[2].y - P[0].y) * nrm.y, pts = [P[0], P[1], pMas(P[1], nrm, dist), pMas(P[0], nrm, dist)];
      return [{ k: 'f', pts: pts, a: 0.1 }, { k: 'l', pts: pts, cerrar: true }];
    } });
    // Herramienta 'circle' (círculo): centro en el punto 1 y radio hasta el punto 2.
    registroHerramienta('circle', { n: 2, col: '#58a6ff', forma: function(el, P, S){
      if (P.length < 2) return [];
      return [{ k: 'c', x: P[0].x, y: P[0].y, r: Math.hypot(P[1].x - P[0].x, P[1].y - P[0].y), a: 0.08 }];
    } });
    // TITULO CIRC3

    /** Calcula el círculo que pasa por tres puntos (circuncírculo). Devuelve { x, y, r } o null si los puntos son casi colineales. */
    function circ3(a, b, c){
      var d = 2 * (a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y));
      if (Math.abs(d) < 1e-6) return null;
      var a2 = a.x * a.x + a.y * a.y, b2 = b.x * b.x + b.y * b.y, c2 = c.x * c.x + c.y * c.y;
      var ux = (a2 * (b.y - c.y) + b2 * (c.y - a.y) + c2 * (a.y - b.y)) / d, uy = (a2 * (c.x - b.x) + b2 * (a.x - c.x) + c2 * (b.x - a.x)) / d;
      return { x: ux, y: uy, r: Math.hypot(a.x - ux, a.y - uy) };
    }
    // Herramienta 'arc' (arco): arco de circunferencia que pasa por los tres puntos, con relleno suave.
    registroHerramienta('arc', { n: 3, col: '#58a6ff', forma: function(el, P, S){
      if (P.length < 3) return [{ k: 'l', pts: P }];
      var ci = circ3(P[0], P[1], P[2]);
      if (!ci || ci.r > 20000) return [{ k: 'l', pts: [P[0], P[1]] }];
      var TAU = Math.PI * 2, a1 = Math.atan2(P[0].y - ci.y, P[0].x - ci.x), a2 = Math.atan2(P[1].y - ci.y, P[1].x - ci.x), a3 = Math.atan2(P[2].y - ci.y, P[2].x - ci.x);
      var d12 = ((a2 - a1) % TAU + TAU) % TAU, d13 = ((a3 - a1) % TAU + TAU) % TAU;
      var fin = d13 <= d12 ? a1 + d12 : a1 - (TAU - d12), pts = muestrearArco(ci, ci.r, a1, fin, 60);
      return [{ k: 'f', pts: pts, a: 0.06, sinTocar: true }, { k: 'l', pts: pts }];
    } });
    // Herramienta 'curve' (curva): curva cuadrática de Bézier de A a B cuyo punto de control se calcula para que pase por el tercer punto.
    registroHerramienta('curve', { n: 3, col: '#58a6ff', forma: function(el, P, S){
      if (P.length < 3) return [{ k: 'l', pts: P }];
      var cp = { x: 2 * P[2].x - (P[0].x + P[1].x) / 2, y: 2 * P[2].y - (P[0].y + P[1].y) / 2 }, pts = [];
      for (var i = 0; i <= 40; i++){ var t = i / 40, u = 1 - t; pts.push({ x: u * u * P[0].x + 2 * u * t * cp.x + t * t * P[1].x, y: u * u * P[0].y + 2 * u * t * cp.y + t * t * P[1].y }); }
      return [{ k: 'l', pts: pts }];
    } });
    // Herramienta 'polyline' (polilínea, nº variable de puntos): se cierra y rellena si el último punto queda a menos de 10 px del primero.
    registroHerramienta('polyline', { v: true, col: '#58a6ff', forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'c', x: P[0].x, y: P[0].y, r: 3, a: 1 }];
      var cerrada = P.length >= 3 && Math.hypot(P[P.length - 1].x - P[0].x, P[P.length - 1].y - P[0].y) < 10;
      var pts = cerrada ? P.slice(0, -1) : P;
      return (cerrada ? [{ k: 'f', pts: pts, a: 0.08 }] : []).concat([{ k: 'l', pts: pts, cerrar: cerrada }]);
    } });
    // Herramienta 'path' (trayectoria): polilínea de nº variable de puntos con punta de flecha al final.
    registroHerramienta('path', { v: true, col: '#58a6ff', forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'c', x: P[0].x, y: P[0].y, r: 3, a: 1 }];
      var a = P[P.length - 2], b = P[P.length - 1];
      return [{ k: 'l', pts: P }, { k: 'f', pts: cabezaFlecha(b.x, b.y, Math.atan2(b.y - a.y, b.x - a.x), 11), a: 1, sinTocar: true }];
    } });

    // TITULO TAM TEXTO

    // ================= TEXTO Y NOTAS =================
    /** Devuelve el tamaño de letra del dibujo, o el valor por defecto si no tiene. */
    function tamTexto(el, def){ return el.tamano || def; }
    // TITULO CAJA TEXTO

    /** Calcula la caja de texto de una primitiva con el lienzo actual (mismo cálculo que medirTexto). */
    function cajaTexto(primario){ return medirTexto(ctx, primario); }

    // Herramienta 'text_anchored' (texto fijo a la pantalla): texto editable en una fracción fija del área de trazado.
    registroHerramienta('text_anchored', { ancla: true, texto: true, textoObligatorio: true, textoDef: '', tamano: true, col: '#ffffff', sinGrosor: true, forma: function(el, P, S){
      return [{ k: 't', x: P[0].x, y: P[0].y, txt: el.texto || 'Texto', size: tamTexto(el, 16), fg: S.col, al: 'l', hitbox: true, bold: !!el.negrita }];
    } });
    // Herramienta 'note' (nota): etiqueta amarilla con conector hasta el punto anclado.
    registroHerramienta('note', { n: 1, texto: true, textoObligatorio: true, textoDef: 'Nota', col: '#f5c518', sinGrosor: true, forma: function(el, P, S){
      var t = { k: 't', x: P[0].x + 12, y: P[0].y - 30, txt: el.texto || 'Nota', size: 12, fg: '#1b1f24', bg: S.col, al: 'l', pad: 7, radio: 5 }, m = cajaTexto(t);
      return [{ k: 'l', pts: [P[0], { x: m.x0 + 10, y: m.y0 + m.h }], w: 1.5 }, { k: 'c', x: P[0].x, y: P[0].y, r: 3.5, a: 1, sinTrazo: true }, t];
    } });
    // Herramienta 'price_note' (nota de precio): punto 1 unido con guía punteada a un cuadro con el texto y el precio del punto.
    registroHerramienta('price_note', { n: 2, texto: true, textoObligatorio: true, textoDef: 'Nota', textoEnUltimo: true, col: '#2962ff', sinGrosor: true, forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      return [{ k: 'l', pts: [P[0], P[1]], d: 'dot', w: 1 }, { k: 'c', x: P[0].x, y: P[0].y, r: 4, a: 1, sinTrazo: true },
              { k: 't', x: P[1].x, y: P[1].y, txt: (el.texto || 'Nota') + '\n' + pr(el, 1).toFixed(DIGITS), size: 12, fg: '#fff', bg: S.col, al: 'l', pad: 6, radio: 4 }];
    } });
    // Herramienta 'pin' (chincheta): marcador en forma de gota sobre el punto, con texto opcional al lado.
    registroHerramienta('pin', { n: 1, texto: true, textoDef: '', col: '#f23645', sinGrosor: true, forma: function(el, P, S){
      var x = P[0].x, y = P[0].y, cy = y - 24, prims = [];
      prims.push({ k: 'p', box: [x - 11, cy - 11, x + 11, y],
        // Pintado libre de la gota de la chincheta.
        draw: function(c){
          c.fillStyle = S.col; c.beginPath(); c.arc(x, cy, 10, Math.PI * 0.82, Math.PI * 2.18, false); c.lineTo(x, y); c.closePath(); c.fill();
          c.fillStyle = '#ffffff'; c.beginPath(); c.arc(x, cy, 3.6, 0, Math.PI * 2); c.fill();
        },
        // Detección de clic sobre la cabeza o el palo de la chincheta.
        hit: function(px, py){ return Math.hypot(px - x, py - cy) <= 13 || (Math.abs(px - x) <= 6 && py >= cy && py <= y); } });
      if (el.texto) prims.push({ k: 't', x: x + 16, y: cy, txt: el.texto, size: 12, fg: '#fff', bg: 'rgba(22,27,34,0.92)', al: 'l', pad: 5 });
      return prims;
    } });
    // Herramienta 'table' (tabla): tabla anclada a la pantalla; cada línea de texto es una fila y las columnas se separan con el carácter |; la primera fila es el encabezado.
    registroHerramienta('table', { ancla: true, texto: true, multilinea: true, textoObligatorio: true, textoDef: 'Columna 1 | Columna 2 | Columna 3\nA | B | C\nD | E | F', tamano: true, col: '#58a6ff', sinGrosor: true, forma: function(el, P, S){
      var filas = String(el.texto || '').split('\n').map(function(f){ return f.split('|').map(function(c){ return c.trim(); }); });
      var sz = tamTexto(el, 12), pad = 7, anchos = [], x0 = P[0].x, y0 = P[0].y, alto = sz * 1.3 + pad * 2;
      ctx.font = sz + 'px sans-serif';
      filas.forEach(function(f){ f.forEach(function(c, j){ anchos[j] = Math.max(anchos[j] || 40, ctx.measureText(c).width + pad * 2); }); });
      var total = anchos.reduce(function(a, b){ return a + b; }, 0), hTot = alto * filas.length;
      return [{ k: 'p', box: [x0, y0, x0 + total, y0 + hTot],
        // Pintado libre de la tabla: fondo, encabezado, bordes, líneas de filas y columnas y texto de cada celda.
        draw: function(c){
          c.fillStyle = 'rgba(13,17,23,0.92)'; c.fillRect(x0, y0, total, hTot);
          c.fillStyle = 'rgba(88,166,255,0.22)'; c.fillRect(x0, y0, total, alto);
          c.strokeStyle = S.col; c.lineWidth = 1; c.strokeRect(x0, y0, total, hTot);
          c.font = sz + 'px sans-serif'; c.textBaseline = 'middle'; c.textAlign = 'left';
          filas.forEach(function(f, i){
            var x = x0; if (i > 0) { c.beginPath(); c.moveTo(x0, y0 + alto * i); c.lineTo(x0 + total, y0 + alto * i); c.stroke(); }
            f.forEach(function(cel, j){ c.fillStyle = i === 0 ? '#ffffff' : '#d1d4dc'; c.font = (i === 0 ? 'bold ' : '') + sz + 'px sans-serif'; c.fillText(cel, x + pad, y0 + alto * (i + 0.5)); x += anchos[j]; if (j < f.length - 1) { c.beginPath(); c.moveTo(x, y0); c.lineTo(x, y0 + hTot); c.stroke(); } });
          });
        },
        // Detección de clic sobre toda la tabla.
        hit: function(px, py){ return px >= x0 && px <= x0 + total && py >= y0 && py <= y0 + hTot; } }];
    } });
    // Herramienta 'callout' (leyenda): línea desde el punto 1 hasta un globo de texto en el punto 2.
    registroHerramienta('callout', { n: 2, texto: true, textoObligatorio: true, textoDef: 'Leyenda', textoEnUltimo: true, col: '#2962ff', sinGrosor: true, forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      return [{ k: 'l', pts: [P[0], P[1]], w: 1.5 }, { k: 'c', x: P[0].x, y: P[0].y, r: 3.5, a: 1, sinTrazo: true },
              { k: 't', x: P[1].x, y: P[1].y, txt: el.texto || 'Leyenda', size: 12, fg: '#fff', bg: S.col, al: 'c', pad: 7, radio: 5 }];
    } });
    // Herramienta 'comment' (comentario): globo de texto redondeado con una cola triangular hacia el punto anclado.
    registroHerramienta('comment', { n: 1, texto: true, textoObligatorio: true, textoDef: 'Comentario', col: '#1f6feb', sinGrosor: true, forma: function(el, P, S){
      var t = { k: 't', x: P[0].x - 6, y: P[0].y - 34, txt: el.texto || 'Comentario', size: 12, fg: '#fff', bg: S.col, al: 'l', pad: 8, radio: 12 }, m = cajaTexto(t);
      var by = m.y0 + m.h;
      return [{ k: 'f', pts: [P[0], { x: m.x0 + 6, y: by - 2 }, { x: m.x0 + 22, y: by - 2 }], a: 1 }, t];
    } });
    // Herramienta 'price_label' (etiqueta de precio): etiqueta con forma de flecha que muestra el precio del punto.
    registroHerramienta('price_label', { n: 1, col: '#2962ff', sinGrosor: true, forma: function(el, P, S){
      var txt = pr(el, 1).toFixed(DIGITS), t = { k: 't', x: P[0].x + 8, y: P[0].y, txt: txt, size: 11, fg: '#fff', al: 'l', pad: 6 }, w = cajaTexto({ k: 't', x: 0, y: 0, txt: txt, size: 11, bg: '#000', pad: 6 }).w;
      return [{ k: 'f', pts: [P[0], { x: P[0].x + 8, y: P[0].y - 10 }, { x: P[0].x + 8 + w, y: P[0].y - 10 }, { x: P[0].x + 8 + w, y: P[0].y + 10 }, { x: P[0].x + 8, y: P[0].y + 10 }], a: 1 },
              { k: 't', x: P[0].x + 8, y: P[0].y, txt: txt, size: 11, fg: '#fff', al: 'l', pad: 6, bg: 'rgba(0,0,0,0)' }];
    } });
    // Herramienta 'signpost' (poste indicador): poste con un círculo y una estrella.
    registroHerramienta('signpost', { n: 1, col: '#f5c518', sinGrosor: true, forma: function(el, P, S){
      var x = P[0].x, y = P[0].y;
      return [{ k: 'l', pts: [P[0], { x: x, y: y - 24 }], w: 2 }, { k: 'c', x: x, y: y - 36, r: 12, a: 1 },
              { k: 't', x: x, y: y - 36, txt: '★', size: 15, fg: '#1b1f24', al: 'c' }];
    } });
    // Herramienta 'flag' (bandera): asta con una bandera triangular.
    registroHerramienta('flag', { n: 1, col: '#3fb950', sinGrosor: true, forma: function(el, P, S){
      var x = P[0].x, y = P[0].y;
      return [{ k: 'l', pts: [P[0], { x: x, y: y - 34 }], w: 2 }, { k: 'f', pts: [{ x: x, y: y - 34 }, { x: x + 24, y: y - 27 }, { x: x, y: y - 18 }], a: 1 }];
    } });
    // Herramienta 'emoji' (icono): muestra el emoji elegido en el selector de iconos, con tamaño editable.
    registroHerramienta('emoji', { n: 1, tamano: true, col: '#ffffff', sinColor: true, sinGrosor: true, forma: function(el, P, S){
      return [{ k: 't', x: P[0].x, y: P[0].y, txt: el.texto || '😀', size: tamTexto(el, 30), fg: '#ffffff', al: 'c', hitbox: true }];
    } });

/* -------------------------------------------------------------------------------------------------------
   --------------------- FIN Piña y Jara 28_dibujo_extra_proyeccion_figuras_texto .JS --------------------
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
