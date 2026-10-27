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
   ------------------------ INICIO Piña y Jara 27_dibujo_extra_lineas_patrones .JS -----------------------
   ------------------------------------------------------------------------------------------------------- */

    // TITULO ETQ

// [grafico] Dibujo: líneas de información, canales, tridentes, patrones, ondas de Elliott y ciclos
    /** Crea una primitiva de texto 't' con fondo oscuro translúcido, tamaño 11, centrada, para etiquetas de las herramientas. Recibe posición, texto, color de texto y propiedades extra que sobrescriben las predeterminadas; devuelve la primitiva. */
    function etq(x, y, txt, fg, extra){
      var o = { k: 't', x: x, y: y, txt: txt, fg: fg || '#d1d4dc', bg: 'rgba(13,17,23,0.88)', size: 11, al: 'c', pad: 3 };
      if (extra) Object.keys(extra).forEach(function(k){ o[k] = extra[k]; });
      return o;
    }
    // TITULO LETRA PUNTO

    // Letra o número junto a un punto: encima si es un máximo local, debajo si es un mínimo
    /** Crea la primitiva de texto (letra o número) de un vértice del patrón: la coloca encima si el vértice es un máximo local (sus vecinos están más abajo) y debajo si es un mínimo. Recibe los puntos P, el índice, el texto y el color. */
    function letraPunto(P, i, txt, col){
      var arriba = true, a = P[i - 1], b = P[i + 1];
      if (a && b) arriba = P[i].y <= a.y && P[i].y <= b.y;
      else if (a) arriba = P[i].y <= a.y;
      else if (b) arriba = P[i].y <= b.y;
      return { k: 't', x: P[i].x, y: P[i].y + (arriba ? -13 : 13), txt: txt, fg: col, size: 12, bold: true, al: 'c' };
    }
    // TITULO PR

    /** Devuelve el precio del punto i (1, 2, ...) del dibujo. */
    function pr(el, i){ return el['price' + i]; }
    // TITULO RATIO ABS

    /** Calcula la razón entre el tramo de precio a-b y el tramo c-d (valores absolutos) de un dibujo; devuelve 0 si el denominador es cero. */
    function ratioAbs(el, a, b, c, d){ var den = Math.abs(pr(el, d) - pr(el, c)); return den ? Math.abs(pr(el, b) - pr(el, a)) / den : 0; }
    // TITULO EXT

    /** Devuelve un punto muy lejano desde Q en la dirección del vector d (fuera de la pantalla), para prolongar líneas. */
    function ext(Q, d){   // punto lejano desde Q en la dirección d
      var len = Math.hypot(d.x, d.y) || 1, K = cssW + cssH + 4000;
      return { x: Q.x + d.x / len * K, y: Q.y + d.y / len * K };
    }

    // ================= LÍNEAS =================
    // Herramienta 'infoline' (línea de información): segmento entre dos puntos con etiqueta de diferencia de precio, porcentaje, número de barras y ángulo.
    registroHerramienta('infoline', { n: 2, col: '#2962ff', forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      var diferencia = pr(el, 2) - pr(el, 1), pct = pr(el, 1) ? diferencia / pr(el, 1) * 100 : 0;
      var ang = Math.atan2(-(P[1].y - P[0].y), P[1].x - P[0].x) * 180 / Math.PI, barras = barrasEntreTiempos(el.time1, el.time2);
      var m = pMed(P[0], P[1]);
      return [{ k: 'l', pts: [P[0], P[1]] },
              etq(m.x, m.y - 20, (diferencia >= 0 ? '+' : '') + formatoPrecioDiferencia(diferencia) + ' (' + (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%)\n' + barras + ' barras · ' + ang.toFixed(1) + '°', '#fff', { bg: S.col })];
    } });

    // ================= CANALES =================
    // Herramienta 'regresion' (canal de regresión lineal): ajustarP acopla los extremos a la recta de regresión y forma dibuja la banda de desviaciones y la línea central.
    registroHerramienta('regresion', { n: 2, col: '#2962ff',
      // Reemplaza los dos puntos del usuario por los extremos de la recta de regresión calculada sobre las velas del rango.
      ajustarP: function(el, P){
        var r = calcRegresion(el); if (!r || P.length < 2) return;
        var ts = chart.timeScale(), y1 = yDePrecio(r.y0), y2 = yDePrecio(r.y1), x1 = ts.logicalToCoordinate(r.i0), x2 = ts.logicalToCoordinate(r.i1);
        if (ok(x1, x2, y1, y2)) { P[0] = { x: x1, y: y1 }; P[1] = { x: x2, y: y2 }; }
      },
      // Dibuja la banda de más/menos k desviaciones estándar, sus bordes y la recta media punteada.
      forma: function(el, P, S){
        var r = calcRegresion(el); if (!r) return [{ k: 'l', pts: P }];
        var ts = chart.timeScale(), xa = ts.logicalToCoordinate(r.i0), xb = ts.logicalToCoordinate(r.i1);
        var d = r.k * r.sd, ya0 = yDePrecio(r.y0 + d), ya1 = yDePrecio(r.y1 + d), yb0 = yDePrecio(r.y0 - d), yb1 = yDePrecio(r.y1 - d), ym0 = yDePrecio(r.y0), ym1 = yDePrecio(r.y1);
        if (!ok(xa, xb, ya0, ya1, yb0, yb1, ym0, ym1)) return [];
        return [{ k: 'f', pts: [{ x: xa, y: ya0 }, { x: xb, y: ya1 }, { x: xb, y: yb1 }, { x: xa, y: yb0 }], a: 0.08 },
                { k: 'l', pts: [{ x: xa, y: ya0 }, { x: xb, y: ya1 }] }, { k: 'l', pts: [{ x: xa, y: yb0 }, { x: xb, y: yb1 }] },
                { k: 'l', pts: [{ x: xa, y: ym0 }, { x: xb, y: ym1 }], d: 'dash' }];
      } });
    // TITULO CALC REGRESION

    /** Calcula la regresión lineal de los cierres entre los dos tiempos del dibujo. Devuelve { i0, i1 (índices de las velas extremas), y0, y1 (precio de la recta en cada extremo), sd (desviación típica de los residuos), k (multiplicador de desviaciones) } o null si el rango es inválido o tiene menos de 3 velas. */
    function calcRegresion(el){
      var n = datosActuales.length, l1 = tiempoALogico(el.time1), l2 = tiempoALogico(el.time2);
      if (el.time2 === undefined || l1 === null || l2 === null || !n) return null;
      var i0 = Math.max(0, Math.round(Math.min(l1, l2))), i1 = Math.min(n - 1, Math.round(Math.max(l1, l2)));
      if (i1 - i0 < 2) return null;
      var m = i1 - i0 + 1, sx = 0, sy = 0, sxy = 0, sxx = 0, i;
      for (i = 0; i < m; i++){ var y = datosActuales[i0 + i].close; sx += i; sy += y; sxy += i * y; sxx += i * i; }
      var den = m * sxx - sx * sx; if (!den) return null;
      var b = (m * sxy - sx * sy) / den, a = (sy - b * sx) / m, res = 0;
      for (i = 0; i < m; i++){ var e = datosActuales[i0 + i].close - (a + b * i); res += e * e; }
      return { i0: i0, i1: i1, y0: a, y1: a + b * (m - 1), sd: Math.sqrt(res / m), k: el.desv || 2 };
    }

    // Herramienta 'flat' (techo/suelo plano): dos puntos definen el borde superior y el tercero fija el nivel horizontal del borde opuesto.
    registroHerramienta('flat', { n: 3, col: '#2962ff', forma: function(el, P, S){
      if (P.length < 3) return [{ k: 'l', pts: P }];
      var a = P[0], b = P[1], c = { x: a.x, y: P[2].y }, d = { x: b.x, y: P[2].y };
      return [{ k: 'f', pts: [a, b, d, c], a: 0.08 }, { k: 'l', pts: [a, b] }, { k: 'l', pts: [c, d] }];
    } });
    // Herramienta 'disjoint' (canal disjunto): segmento A-B y un segmento paralelo desplazado al tercer punto.
    registroHerramienta('disjoint', { n: 3, col: '#2962ff', forma: function(el, P, S){
      if (P.length < 3) return [{ k: 'l', pts: P }];
      var v = pResultado(P[1], P[0]), c = P[2], d = pMas(c, v);
      return [{ k: 'f', pts: [P[0], P[1], d, c], a: 0.07 }, { k: 'l', pts: [P[0], P[1]] }, { k: 'l', pts: [c, d] }];
    } });

    // TITULO FORMA TRIDENTE

    // ================= TRIDENTES =================
    /** Crea la función de forma de un tridente (horquilla) de la variante indicada: 'andrews' (origen en A), 'schiff' y 'mschiff' (origen desplazado) o 'inside' (con líneas intermedias). Devuelve una función (el, P, S) que produce las primitivas de la mediana, las dos paralelas y el relleno. */
    function formaTridente(variante){
      return function(el, P, S){
        if (P.length < 3) return [{ k: 'l', pts: P.length > 1 ? [P[0], P[1]] : P }];
        var A = P[0], B = P[1], C = P[2];
        var O = variante === 'schiff' ? { x: A.x, y: (A.y + B.y) / 2 } : (variante === 'mschiff' ? pMed(A, B) : A);
        var M = pMed(B, C), d = pResultado(M, O);
        if (!d.x && !d.y) return [{ k: 'l', pts: [A, B, C] }];
        var fm = ext(O, d), retroalimentacion = ext(B, d), fc = ext(C, d), prims = [];
        prims.push({ k: 'f', pts: [B, retroalimentacion, fc, C], a: 0.07 });
        prims.push({ k: 'l', pts: [O, fm], w: S.w }); prims.push({ k: 'l', pts: [B, retroalimentacion] }); prims.push({ k: 'l', pts: [C, fc] });
        prims.push({ k: 'l', pts: [B, C], d: 'dot' });
        if (variante === 'inside') {
          var hb = pMed(B, M), hc = pMed(C, M);
          prims.push({ k: 'l', pts: [hb, ext(hb, d)], d: 'dash' }); prims.push({ k: 'l', pts: [hc, ext(hc, d)], d: 'dash' });
        }
        if (variante === 'schiff' || variante === 'mschiff') prims.push({ k: 'l', pts: [A, O], d: 'dot' });
        return prims;
      };
    }
    // Herramientas de tridentes: horquilla de Andrews, Schiff, Schiff modificada y horquilla interior.
    registroHerramienta('pf_andrews', { n: 3, col: '#a78bfa', forma: formaTridente('andrews') });
    registroHerramienta('pf_schiff', { n: 3, col: '#a78bfa', forma: formaTridente('schiff') });
    registroHerramienta('pf_mschiff', { n: 3, col: '#a78bfa', forma: formaTridente('mschiff') });
    registroHerramienta('pf_inside', { n: 3, col: '#a78bfa', forma: formaTridente('inside') });

    // TITULO RAZONES TRAMOS

    // ================= PATRONES =================
    // Devuelve las etiquetas de razón entre tramos consecutivos del polígono P (a partir del tramo 2)
    /** Genera las etiquetas con la razón entre tramos consecutivos del polígono P (a partir del tramo indicado, por defecto el 2), colocadas en el punto medio de cada tramo. */
    function razonesTramos(el, P, col, desde){
      var out = [];
      for (var k = (desde || 2); k < P.length; k++){
        var a = Math.abs(pr(el, k + 1) - pr(el, k)), b = Math.abs(pr(el, k) - pr(el, k - 1));
        if (b) { var m = pMed(P[k - 1], P[k]); out.push(etq(m.x, m.y, formatoRatio(a / b), col)); }
      }
      return out;
    }
    // TITULO POLILINEA

    /** Crea una primitiva de polilínea que une los puntos P. */
    function polilinea(P){ return { k: 'l', pts: P }; }
    // TITULO TRIANGULOS RELLENO

    /** Crea primitivas de relleno triangular para cada terna de índices indicada, omitiendo las ternas con puntos que aún no existen. Los rellenos no son tocables. */
    function triangulosRelleno(P, ternas){
      return ternas.filter(function(t){ return P[t[0]] && P[t[1]] && P[t[2]]; }).map(function(t){ return { k: 'f', pts: [P[t[0]], P[t[1]], P[t[2]]], a: 0.1, sinTocar: true }; });
    }
    // TITULO LETRAS PATRON

    /** Crea las etiquetas de letra o número de cada vértice de un patrón. Recibe los puntos, la lista de textos y el color. */
    function letrasPatron(P, txts, col){ return P.map(function(q, i){ return letraPunto(P, i, txts[i] || '', col); }); }

    // Herramienta 'xabcd' (patrón XABCD / armónico): dos triángulos de relleno, la polilínea, diagonales de referencia, razones de Fibonacci entre tramos y letras X, A, B, C, D.
    registroHerramienta('xabcd', { n: 5, col: '#2962ff', forma: function(el, P, S){
      var prims = triangulosRelleno(P, [[0, 1, 2], [2, 3, 4]]);
      prims.push(polilinea(P));
      [[0, 2], [2, 4], [1, 3], [0, 4]].forEach(function(s){ if (P[s[0]] && P[s[1]]) prims.push({ k: 'l', pts: [P[s[0]], P[s[1]]], d: 'dash', w: 1 }); });
      if (P.length >= 3) { var m = pMed(P[0], P[2]); prims.push(etq(m.x, m.y, formatoRatio(ratioAbs(el, 2, 3, 1, 2)), S.col)); }
      if (P.length >= 4) { var m2 = pMed(P[1], P[3]); prims.push(etq(m2.x, m2.y, formatoRatio(ratioAbs(el, 3, 4, 2, 3)), S.col)); }
      if (P.length >= 5) {
        var m3 = pMed(P[2], P[4]); prims.push(etq(m3.x, m3.y, formatoRatio(ratioAbs(el, 4, 5, 3, 4)), S.col));
        var m4 = pMed(P[0], P[4]); prims.push(etq(m4.x, m4.y, formatoRatio(Math.abs(pr(el, 5) - pr(el, 1)) / (Math.abs(pr(el, 2) - pr(el, 1)) || 1)), '#ff9800'));
      }
      return prims.concat(letrasPatron(P, ['X', 'A', 'B', 'C', 'D'], S.col));
    } });
    // Herramienta 'cypher' (patrón Cypher): como el XABCD pero con sus propias diagonales y razones.
    registroHerramienta('cypher', { n: 5, col: '#e056fd', forma: function(el, P, S){
      var prims = triangulosRelleno(P, [[0, 1, 2], [2, 3, 4]]);
      prims.push(polilinea(P));
      [[0, 2], [0, 3], [2, 4]].forEach(function(s){ if (P[s[0]] && P[s[1]]) prims.push({ k: 'l', pts: [P[s[0]], P[s[1]]], d: 'dash', w: 1 }); });
      if (P.length >= 3) { var m = pMed(P[0], P[2]); prims.push(etq(m.x, m.y, formatoRatio(ratioAbs(el, 2, 3, 1, 2)), S.col)); }
      if (P.length >= 4) { var m2 = pMed(P[0], P[3]); prims.push(etq(m2.x, m2.y, formatoRatio(ratioAbs(el, 1, 4, 1, 2)), S.col)); }
      if (P.length >= 5) { var m3 = pMed(P[2], P[4]); prims.push(etq(m3.x, m3.y, formatoRatio(ratioAbs(el, 4, 5, 1, 4)), S.col)); }
      return prims.concat(letrasPatron(P, ['X', 'A', 'B', 'C', 'D'], S.col));
    } });
    // Herramienta 'abcd' (patrón AB=CD): polilínea de 4 puntos, diagonales de referencia, razones y letras A, B, C, D.
    registroHerramienta('abcd', { n: 4, col: '#3fb950', forma: function(el, P, S){
      var prims = [polilinea(P)];
      [[0, 2], [1, 3]].forEach(function(s){ if (P[s[0]] && P[s[1]]) prims.push({ k: 'l', pts: [P[s[0]], P[s[1]]], d: 'dash', w: 1 }); });
      if (P.length >= 3) { var m = pMed(P[0], P[2]); prims.push(etq(m.x, m.y, formatoRatio(ratioAbs(el, 2, 3, 1, 2)), S.col)); }
      if (P.length >= 4) { var m2 = pMed(P[1], P[3]); prims.push(etq(m2.x, m2.y, formatoRatio(ratioAbs(el, 3, 4, 2, 3)), S.col)); }
      return prims.concat(letrasPatron(P, ['A', 'B', 'C', 'D'], S.col));
    } });
    // Herramienta 'headshoulders' (hombro-cabeza-hombro): polilínea de 7 puntos, rellenos, línea de cuello prolongada y rótulos de los hombros y la cabeza.
    registroHerramienta('headshoulders', { n: 7, col: '#ff9800', forma: function(el, P, S){
      var prims = triangulosRelleno(P, [[0, 1, 2], [2, 3, 4], [4, 5, 6]]);
      prims.push(polilinea(P));
      if (P.length >= 5) { var fin = ext(P[2], pResultado(P[4], P[2])); prims.push({ k: 'l', pts: [P[2], fin], d: 'dash', w: 1.5, col: '#f23645' }); prims.push(etq(P[4].x + 26, P[4].y, 'Línea de cuello', '#f23645')); }
      if (P[1]) prims.push(etq(P[1].x, P[1].y - 26, 'Hombro izq.', S.col));
      if (P[3]) prims.push(etq(P[3].x, P[3].y - 26, 'Cabeza', S.col));
      if (P[5]) prims.push(etq(P[5].x, P[5].y - 26, 'Hombro der.', S.col));
      return prims;
    } });
    // Herramienta 'trianglepat' (patrón de triángulo): polilínea de 4 puntos y las dos líneas de tendencia prolongadas hasta su intersección (ápice) con relleno.
    registroHerramienta('trianglepat', { n: 4, col: '#26a69a', forma: function(el, P, S){
      var prims = [polilinea(P)];
      if (P.length >= 4) {
        var A = P[0], B = P[1], C = P[2], D = P[3], d1 = pResultado(C, A), d2 = pResultado(D, B);
        var den = d1.x * d2.y - d1.y * d2.x, apex = null;
        if (Math.abs(den) > 1e-6) { var t = ((B.x - A.x) * d2.y - (B.y - A.y) * d2.x) / den; if (t > 1) apex = { x: A.x + d1.x * t, y: A.y + d1.y * t }; }
        var e1 = apex || ext(C, d1), e2 = apex || ext(D, d2);
        prims.unshift({ k: 'f', pts: [A, e1, e2, B], a: 0.07, sinTocar: true });
        prims.push({ k: 'l', pts: [C, e1], d: 'dash' }); prims.push({ k: 'l', pts: [D, e2], d: 'dash' });
      }
      return prims.concat(letrasPatron(P, ['A', 'B', 'C', 'D'], S.col));
    } });
    // Herramienta 'threedrives' (tres impulsos): polilínea de 7 puntos con la razón entre tramos y numeración 0 a 6.
    registroHerramienta('threedrives', { n: 7, col: '#58a6ff', forma: function(el, P, S){
      var prims = [polilinea(P)].concat(razonesTramos(el, P, S.col, 2));
      return prims.concat(letrasPatron(P, ['0', '1', '2', '3', '4', '5', '6'], S.col));
    } });

    // TITULO FORMA ELLIOTT

    // ================= ONDAS DE ELLIOTT =================
    /** Crea la función de forma de una onda de Elliott: dibuja la polilínea y rotula cada vértice con las etiquetas dadas. Recibe los rótulos y el color; devuelve una función (el, P, S). */
    function formaElliott(rotulos, col){
      return function(el, P, S){
        return [polilinea(P)].concat(P.map(function(q, i){ return letraPunto(P, i, rotulos[i] || '', S.col); }));
      };
    }
    // Herramientas de ondas de Elliott: impulso (0 a 5), corrección ABC, triángulo (ABCDE), doble combinación (WXY) y triple combinación (WXYXZ).
    registroHerramienta('ell_impulse', { n: 6, col: '#2962ff', forma: formaElliott(['(0)', '(1)', '(2)', '(3)', '(4)', '(5)']) });
    registroHerramienta('ell_abc', { n: 4, col: '#f5c518', forma: formaElliott(['(0)', '(A)', '(B)', '(C)']) });
    registroHerramienta('ell_triangle', { n: 6, col: '#3fb950', forma: formaElliott(['(0)', '(A)', '(B)', '(C)', '(D)', '(E)']) });
    registroHerramienta('ell_wxy', { n: 4, col: '#e056fd', forma: formaElliott(['(0)', '(W)', '(X)', '(Y)']) });
    registroHerramienta('ell_wxyxz', { n: 6, col: '#ff9800', forma: formaElliott(['(0)', '(W)', '(X)', '(Y)', '(X)', '(Z)']) });

    // TITULO POSICIONES CICLO

    // ================= CICLOS =================
    /** Calcula las coordenadas X de las líneas de un ciclo: repite el período definido por los dos tiempos del dibujo hacia ambos lados, dentro del área visible (máximo maxN, 400 por defecto). Devuelve el arreglo de X o null si el período es inválido. */
    function posicionesCiclo(el, P, maximoN){
      var l1 = tiempoALogico(el.time1), l2 = tiempoALogico(el.time2);
      if (el.time2 === undefined || l1 === null || l2 === null || Math.abs(l2 - l1) < 0.5) return null;
      var per = Math.abs(l2 - l1), ts = chart.timeScale(), ap = areaTrazado();
      var lIzquierda = ts.coordinateToLogical(0), lDer = ts.coordinateToLogical(ap.w);
      if (lIzquierda === null || lDer === null) return null;
      var base = Math.min(l1, l2), kmin = Math.ceil((lIzquierda - base) / per) - 1, kmax = Math.floor((lDer - base) / per) + 1, xs = [];
      for (var k = kmin; k <= kmax && xs.length < (maximoN || 400); k++){ var x = ts.logicalToCoordinate(base + k * per); if (ok(x)) xs.push(x); }
      return xs;
    }
    // Herramienta 'cyclic' (líneas cíclicas): líneas verticales punteadas separadas por el período definido por los dos puntos.
    registroHerramienta('cyclic', { n: 2, col: '#58a6ff', estilo: 'dash', forma: function(el, P, S){
      var xs = posicionesCiclo(el, P); if (!xs) return [{ k: 'l', pts: P }];
      return xs.map(function(x){ return { k: 'l', pts: [{ x: x, y: 0 }, { x: x, y: S.H }], w: 1 }; });
    } });
    // Herramienta 'timecycles' (ciclos de tiempo): semicírculos consecutivos entre las líneas del ciclo, con relleno suave.
    registroHerramienta('timecycles', { n: 2, col: '#58a6ff', forma: function(el, P, S){
      var xs = posicionesCiclo(el, P); if (!xs || xs.length < 2) return [{ k: 'l', pts: P }];
      var y0 = P[0].y, h = Math.max(14, Math.abs(P[1].y - P[0].y)), out = [];
      for (var i = 1; i < xs.length; i++){
        var xc = (xs[i - 1] + xs[i]) / 2, rx = Math.abs(xs[i] - xs[i - 1]) / 2, pts = [];
        for (var j = 0; j <= 28; j++){ var th = Math.PI * j / 28; pts.push({ x: xc + rx * Math.cos(th), y: y0 - h * Math.sin(th) }); }
        out.push({ k: 'f', pts: pts, a: 0.05, sinTocar: true }); out.push({ k: 'l', pts: pts });
      }
      return out;
    } });
    // Herramienta 'sine' (línea sinusoidal): onda coseno entre los dos puntos, con la amplitud dada por su separación vertical, repetida a todo lo ancho.
    registroHerramienta('sine', { n: 2, col: '#a78bfa', forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      var x1 = P[0].x, x2 = P[1].x, dx = x2 - x1; if (Math.abs(dx) < 4) return [{ k: 'l', pts: P }];
      var ym = (P[0].y + P[1].y) / 2, A = P[0].y - ym, pts = [];
      for (var x = -4; x <= S.W + 4; x += 3) pts.push({ x: x, y: ym + A * Math.cos(Math.PI * (x - x1) / dx) });
      return [{ k: 'l', pts: pts }];
    } });

/* -------------------------------------------------------------------------------------------------------
   ------------------------- FIN Piña y Jara 27_dibujo_extra_lineas_patrones .JS -------------------------
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
