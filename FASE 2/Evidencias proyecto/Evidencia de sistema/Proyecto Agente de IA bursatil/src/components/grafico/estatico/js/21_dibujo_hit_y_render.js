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
   ---------------------------- INICIO Piña y Jara 21_dibujo_hit_y_render .JS ----------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Dibujo: detección de clics y pintado de cada figura
    /** Calcula la distancia mínima en píxeles entre el punto (px, py) y el segmento (x1,y1)-(x2,y2), proyectando el punto sobre el segmento y limitando la proyección a los extremos. Se usa en la detección de clics sobre líneas. */
    function distSeg(px, py, x1, y1, x2, y2){
      var dx = x2 - x1, dy = y2 - y1;
      var l2 = dx * dx + dy * dy;
      var t = l2 ? ((px - x1) * dx + (py - y1) * dy) / l2 : 0;
      t = Math.max(0, Math.min(1, t));
      return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
    }

    /** Calcula el desplazamiento (dx, dy) de la línea paralela de un canal respecto a la base: si hay tercer punto, es la distancia perpendicular de ese punto a la base; si no, solo el desnivel vertical. Recibe la geometría g. */
    function offsetCanal(g){
      if (!ok(g.x3, g.y3)) return { dx: 0, dy: g.y2 - g.y1 };
      var dx = g.x2 - g.x1, dy = g.y2 - g.y1;
      var len = Math.hypot(dx, dy) || 1;
      var nx = -dy / len, ny = dx / len;
      var signed = ((g.x3 - g.x1) * nx) + ((g.y3 - g.y1) * ny);
      return { dx: nx * signed, dy: ny * signed };
    }

    /** Calcula los extremos en pantalla de una línea prolongada: 'ray' sigue desde el punto 1 pasando por el 2 hasta salir de la pantalla; 'extended' se prolonga en ambos sentidos. Devuelve { ax, ay, bx, by }. */
    function extremosLinea(g, tipo){
      var dx = g.x2 - g.x1, dy = g.y2 - g.y1, len = Math.hypot(dx, dy);
      if (!len) return { ax: g.x1, ay: g.y1, bx: g.x2, by: g.y2 };
      var k = (cssW + cssH + 4000) / len;
      var r = { ax: g.x1, ay: g.y1, bx: g.x2 + dx * k, by: g.y2 + dy * k };
      if (tipo === 'extended') { r.ax = g.x1 - dx * k; r.ay = g.y1 - dy * k; }
      return r;
    }

    /** Prueba si el punto (x, y) toca un dibujo. Devuelve 'p1', 'p2' o 'p3' si cae sobre un tirador (solo si está seleccionado), 'body' si cae sobre el cuerpo (con tolerancias de 6 a 8 px según la figura) o null si no toca nada. Recibe el dibujo, la posición del ratón y si está seleccionado. */
    function hitTest(el, x, y, seleccionado){
      var g = geom(el);
      if (!g) return null;
      if (el.tipo === 'hline') return Math.abs(y - g.y) <= 6 ? 'body' : null;
      if (el.tipo === 'vline') return Math.abs(x - g.x) <= 6 ? 'body' : null;
      if (el.tipo === 'crossline') return (Math.abs(x - g.x) <= 6 || Math.abs(y - g.y) <= 6) ? 'body' : null;
      if (el.tipo === 'text'){
        ctx.font = fuenteTexto(el);
        var w = ctx.measureText(el.texto || 'Texto').width, sz = el.tamano || 13;
        return (x >= g.x - 4 && x <= g.x + w + 4 && y >= g.y - sz - 3 && y <= g.y + 6) ? 'body' : null;
      }
      if (seleccionado){
        if (Math.hypot(x - g.x1, y - g.y1) <= 10) return 'p1';
        if (Math.hypot(x - g.x2, y - g.y2) <= 10) return 'p2';
        if (ok(g.x3, g.y3) && Math.hypot(x - g.x3, y - g.y3) <= 10) return 'p3';
      }
      if (['trend','angle','arrow'].indexOf(el.tipo) >= 0){
        return distSeg(x, y, g.x1, g.y1, g.x2, g.y2) <= 7 ? 'body' : null;
      }
      if (el.tipo === 'ray' || el.tipo === 'extended'){
        var ex = extremosLinea(g, el.tipo);
        return distSeg(x, y, ex.ax, ex.ay, ex.bx, ex.by) <= 7 ? 'body' : null;
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
      var xa = Math.min(g.x1, g.x2), xb = Math.max(g.x1, g.x2);
      var ya = Math.min(g.y1, g.y2), yb = Math.max(g.y1, g.y2);
      if (['measure', 'rectangle', 'ellipse', 'triangle'].indexOf(el.tipo) >= 0){
        return (x >= xa - 7 && x <= xb + 7 && y >= ya - 7 && y <= yb + 7) ? 'body' : null;
      }
      if (el.tipo === 'fib'){
        if (x < xa - 8 || x > xb + 8) return null;
        for (var i = 0; i < NIVELES_FIB.length; i++){
          var yn = g.y1 + (g.y2 - g.y1) * NIVELES_FIB[i].val;
          if (Math.abs(y - yn) <= 6) return 'body';
        }
        return null;
      }
      if (el.tipo === 'fib_extension'){
        var xe = [g.x1, g.x2].concat(ok(g.x3) ? [g.x3] : []);
        if (x < Math.min.apply(null, xe) - 8 || x > Math.max.apply(null, xe) + 8) return null;
        if (distSeg(x, y, g.x1, g.y1, g.x2, g.y2) <= 6) return 'body';
        if (ok(g.x3, g.y3) && distSeg(x, y, g.x2, g.y2, g.x3, g.y3) <= 6) return 'body';
        var pBase = (el.price3 !== undefined) ? el.price3 : el.price2;
        for (var j = 0; j < NIVELES_FIB_EXT.length; j++){
          var ye = yDePrecio(pBase + (el.price2 - el.price1) * NIVELES_FIB_EXT[j].val);
          if (ok(ye) && Math.abs(y - ye) <= 6) return 'body';
        }
        return null;
      }
      if (el.tipo === 'fib_channel'){
        var offH = offsetCanal(g);
        for (var m = 0; m < NIVELES_FIB_CANAL.length; m++){
          var f = NIVELES_FIB_CANAL[m].val;
          if (distSeg(x, y, g.x1 + offH.dx * f, g.y1 + offH.dy * f, g.x2 + offH.dx * f, g.y2 + offH.dy * f) <= 6) return 'body';
        }
        return null;
      }
      return null;
    }

    /** Busca el dibujo bajo el cursor: primero comprueba el seleccionado (incluidos sus tiradores) y luego recorre los demás del último al primero (el de arriba gana). Devuelve { idx, parte } o null. */
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

    /** Pinta un tirador (círculo blanco con borde de color) en (x, y) para indicar un punto editable de un dibujo seleccionado. Recibe el contexto, la posición y el color del borde. */
    function dibujarHandle(c, x, y, col){
      if (!ok(x,y)) return;
      c.save(); c.fillStyle = '#ffffff'; c.strokeStyle = col; c.lineWidth = 2;
      c.beginPath(); c.arc(x, y, 5, 0, 2 * Math.PI); c.fill(); c.stroke(); c.restore();
    }

    // Estilo de trazo temporal del dibujo que se está pintando: ancho y estilo propios del dibujo y sobreancho por hover; lo lee dibujarLinea.
    var trazoActual = { ancho: null, estilo: null, hover: 0 };
    /** Traza una línea de (x1,y1) a (x2,y2) con el color dado, aplicando el ancho y el estilo (continua, rayas o puntos) del dibujo actual si los tiene, o el ancho y la discontinuidad indicados. Restablece la discontinuidad al terminar. */
    function dibujarLinea(c, x1, y1, x2, y2, col, width, dash){
      c.strokeStyle = col; c.lineCap = 'round';
      c.lineWidth = trazoActual.ancho ? trazoActual.ancho + trazoActual.hover : (width || 2);
      var d = dash;
      if (trazoActual.estilo === 'solid') d = [];
      else if (trazoActual.estilo === 'dash') d = [8, 5];
      else if (trazoActual.estilo === 'dot') d = [2, 4];
      if (d) c.setLineDash(d);
      c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke();
      if (d) c.setLineDash([]);
    }

    // Relleno de las figuras: se puede apagar, cambiar de color y de opacidad desde la ventana de ajustes
    /** Devuelve la opacidad del relleno de una figura: 0 si el relleno está apagado, la opacidad propia si existe o la opacidad base indicada. */
    function alfaRell(el, base){ return el.relleno === false ? 0 : (el.rellenoOp !== undefined ? el.rellenoOp : base); }
    /** Devuelve el color del relleno de una figura: el propio si lo definió el usuario o el color de la línea. */
    function colRell(el, col){ return el.rellenoColor || col; }
    /** Pinta un dibujo completo en el lienzo según su tipo (tendencia, rayo, extendida, ángulo, líneas horizontal/vertical/cruz, canal, Fibonacci, rectángulo, elipse, triángulo, flecha, texto, medida). Recibe el contexto, el dibujo, si está seleccionado y si el cursor está encima; los seleccionados muestran tiradores y el hover engrosa el trazo. */
    function dibujarElemento(c, el, sel, hov){
      var g = geom(el); if (!g) return;
      c.save();
      trazoActual.ancho = el.ancho || null; trazoActual.estilo = el.estilo || null; trazoActual.hover = (hov && !sel) ? 1 : 0;
      var hoverExtra = (hov && !sel) ? 1 : 0;

      // Línea de tendencia: segmento entre los dos puntos.
      if (el.tipo === 'trend'){
        var col = el.color || '#2962ff'; dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,col,(el.ancho||2)+hoverExtra);
        if (sel){ dibujarHandle(c,g.x1,g.y1,col); dibujarHandle(c,g.x2,g.y2,col); }
      } else if (el.tipo === 'ray'){
        // Rayo: parte del punto 1, pasa por el 2 y sigue hasta el borde.
        var colR = el.color || '#2962ff'; var exR = extremosLinea(g, 'ray');
        dibujarLinea(c,exR.ax,exR.ay,exR.bx,exR.by,colR,(el.ancho||2)+hoverExtra);
        if(sel){dibujarHandle(c,g.x1,g.y1,colR);dibujarHandle(c,g.x2,g.y2,colR);}
      } else if (el.tipo === 'extended'){
        // Línea extendida: se prolonga en ambos sentidos.
        var colE = el.color || '#2962ff'; var exE = extremosLinea(g, 'extended');
        dibujarLinea(c,exE.ax,exE.ay,exE.bx,exE.by,colE,(el.ancho||2)+hoverExtra);
        if(sel){dibujarHandle(c,g.x1,g.y1,colE);dibujarHandle(c,g.x2,g.y2,colE);}
      } else if (el.tipo === 'angle'){
        // Ángulo: línea con la inclinación en grados junto al punto final.
        var colA=el.color||'#a78bfa'; dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,colA,(el.ancho||2)+hoverExtra);
        var ang=Math.atan2(-(g.y2-g.y1),g.x2-g.x1)*180/Math.PI;
        c.font='11px sans-serif'; c.fillStyle=colA; c.fillText((ang>=0?'+':'')+ang.toFixed(1)+'°',g.x2+7,g.y2-7);
        if(sel){dibujarHandle(c,g.x1,g.y1,colA);dibujarHandle(c,g.x2,g.y2,colA);}
      } else if (el.tipo === 'hline'){
        // Línea horizontal: recorre todo el ancho y se marca con un cuadro en el borde izquierdo si está seleccionada.
        var colH=el.color||'#f5c518'; dibujarLinea(c,0,g.y,cssW,g.y,colH,(el.ancho||1.5)+hoverExtra,[6,4]);
        if(sel){c.fillStyle=colH;c.fillRect(0,g.y-4,6,8);}
      } else if (el.tipo === 'hray'){
        // Rayo horizontal: desde el punto 1 hasta el borde derecho.
        var colHR=el.color||'#f5c518'; dibujarLinea(c,g.x1,g.y1,cssW,g.y1,colHR,(el.ancho||1.5)+hoverExtra);
        if(sel)dibujarHandle(c,g.x1,g.y1,colHR);
      } else if (el.tipo === 'vline'){
        // Línea vertical: recorre todo el alto.
        var colV=el.color||'#58a6ff'; dibujarLinea(c,g.x,0,g.x,cssH,colV,1.5,[4,4]);
        if(sel){c.fillStyle=colV;c.fillRect(g.x-4,0,8,6);}
      } else if (el.tipo === 'crossline'){
        // Cruz (línea horizontal y vertical a la vez).
        var colX=el.color||'#8b949e'; dibujarLinea(c,g.x,0,g.x,cssH,colX,1,[4,4]); dibujarLinea(c,0,g.y,cssW,g.y,colX,1,[4,4]);
        if(sel)dibujarHandle(c,g.x,g.y,colX);
      } else if (el.tipo === 'channel'){
        // Canal paralelo: zona rellena entre la base y su paralela más las dos líneas.
        var colC=el.color||'#2962ff', oc=offsetCanal(g);
        c.globalAlpha=alfaRell(el,.08);c.fillStyle=colRell(el,colC);c.beginPath();c.moveTo(g.x1,g.y1);c.lineTo(g.x2,g.y2);c.lineTo(g.x2+oc.dx,g.y2+oc.dy);c.lineTo(g.x1+oc.dx,g.y1+oc.dy);c.closePath();c.fill();c.globalAlpha=1;
        dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,colC,2+hoverExtra);dibujarLinea(c,g.x1+oc.dx,g.y1+oc.dy,g.x2+oc.dx,g.y2+oc.dy,colC,2+hoverExtra);
        if(sel){dibujarHandle(c,g.x1,g.y1,colC);dibujarHandle(c,g.x2,g.y2,colC);dibujarHandle(c,g.x3,g.y3,colC);}
      } else if (el.tipo === 'fib'){
        // Retroceso de Fibonacci: franjas de color entre niveles, líneas con su valor y precio y diagonal de referencia.
        var xa=Math.min(g.x1,g.x2), xb=Math.max(g.x1,g.x2), dY=g.y2-g.y1, dP=el.price2-el.price1;
        var nv=NIVELES_FIB.map(function(n){return {n:n,y:g.y1+dY*n.val,precio:el.price1+dP*n.val};});
        c.globalAlpha=.07; for(var fi=0;fi<nv.length-1;fi++){c.fillStyle=nv[fi+1].n.color;c.fillRect(xa,Math.min(nv[fi].y,nv[fi+1].y),xb-xa,Math.abs(nv[fi+1].y-nv[fi].y));} c.globalAlpha=1;
        c.font='11px sans-serif'; nv.forEach(function(q){c.strokeStyle=q.n.color;c.fillStyle=q.n.color;c.beginPath();c.moveTo(xa,q.y);c.lineTo(xb,q.y);c.stroke();c.fillText(String(+q.n.val.toFixed(3))+' ('+q.precio.toFixed(DIGITS)+')',xa+5,q.y-3);});
        dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,'rgba(139,148,158,.8)',1,[4,4]);
        if(sel){dibujarHandle(c,g.x1,g.y1,'#a78bfa');dibujarHandle(c,g.x2,g.y2,'#a78bfa');}
      } else if (el.tipo === 'fib_extension'){
        // Extensión de Fibonacci: niveles proyectados desde el punto C usando el tramo A-B.
        var dPe=el.price2-el.price1, pBaseE=(el.price3!==undefined)?el.price3:el.price2;
        var xsE=[g.x1,g.x2].concat(ok(g.x3)?[g.x3]:[]), xaE=Math.min.apply(null,xsE), xbE=Math.max.apply(null,xsE);
        var nvE=NIVELES_FIB_EXT.map(function(n){var pr=pBaseE+dPe*n.val;return {n:n,precio:pr,y:yDePrecio(pr)};}).filter(function(q){return ok(q.y);});
        c.globalAlpha=.06; for(var fe=0;fe<nvE.length-1;fe++){c.fillStyle=nvE[fe+1].n.color;c.fillRect(xaE,Math.min(nvE[fe].y,nvE[fe+1].y),xbE-xaE,Math.abs(nvE[fe+1].y-nvE[fe].y));} c.globalAlpha=1;
        c.font='11px sans-serif'; nvE.forEach(function(q){c.strokeStyle=q.n.color;c.fillStyle=q.n.color;c.lineWidth=1;c.beginPath();c.moveTo(xaE,q.y);c.lineTo(xbE,q.y);c.stroke();c.fillText(String(+q.n.val.toFixed(3))+' ('+q.precio.toFixed(DIGITS)+')',xaE+5,q.y-3);});
        dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,'rgba(139,148,158,.8)',1,[4,4]);
        if(ok(g.x3,g.y3))dibujarLinea(c,g.x2,g.y2,g.x3,g.y3,'rgba(139,148,158,.8)',1,[4,4]);
        if(sel){dibujarHandle(c,g.x1,g.y1,'#a78bfa');dibujarHandle(c,g.x2,g.y2,'#a78bfa');if(ok(g.x3,g.y3))dibujarHandle(c,g.x3,g.y3,'#a78bfa');}
      } else if (el.tipo === 'fib_channel'){
        // Canal de Fibonacci: paralelas a la base escaladas por cada nivel, con franjas entre ellas.
        var offC=offsetCanal(g), nvC=NIVELES_FIB_CANAL;
        c.globalAlpha=.06; for(var fc=0;fc<nvC.length-1;fc++){var fa=nvC[fc].val,fb=nvC[fc+1].val;c.fillStyle=nvC[fc+1].color;c.beginPath();c.moveTo(g.x1+offC.dx*fa,g.y1+offC.dy*fa);c.lineTo(g.x2+offC.dx*fa,g.y2+offC.dy*fa);c.lineTo(g.x2+offC.dx*fb,g.y2+offC.dy*fb);c.lineTo(g.x1+offC.dx*fb,g.y1+offC.dy*fb);c.closePath();c.fill();} c.globalAlpha=1;
        c.font='11px sans-serif'; nvC.forEach(function(n){var ox=offC.dx*n.val,oy=offC.dy*n.val;dibujarLinea(c,g.x1+ox,g.y1+oy,g.x2+ox,g.y2+oy,n.color,1.2+hoverExtra);c.fillStyle=n.color;c.fillText(String(+n.val.toFixed(3)),Math.max(g.x1,g.x2)+ox+6,g.y2+oy-3);});
        if(sel){dibujarHandle(c,g.x1,g.y1,'#a78bfa');dibujarHandle(c,g.x2,g.y2,'#a78bfa');if(ok(g.x3,g.y3))dibujarHandle(c,g.x3,g.y3,'#a78bfa');}
      } else if (el.tipo === 'rectangle'){
        // Rectángulo con relleno translúcido y borde.
        var colG=el.color||'#58a6ff'; var rw=g.x2-g.x1,rh=g.y2-g.y1;
        c.globalAlpha=alfaRell(el,.08);c.fillStyle=colRell(el,colG);c.fillRect(Math.min(g.x1,g.x2),Math.min(g.y1,g.y2),Math.abs(rw),Math.abs(rh));c.globalAlpha=1;
        c.strokeStyle=colG;c.lineWidth=(el.ancho||2)+hoverExtra;c.strokeRect(Math.min(g.x1,g.x2),Math.min(g.y1,g.y2),Math.abs(rw),Math.abs(rh));
        if(sel){dibujarHandle(c,g.x1,g.y1,colG);dibujarHandle(c,g.x2,g.y2,colG);}
      } else if (el.tipo === 'ellipse'){
        // Elipse inscrita en el rectángulo de los dos puntos.
        var colEl=el.color||'#58a6ff'; var cx=(g.x1+g.x2)/2,cy=(g.y1+g.y2)/2,rx=Math.abs(g.x2-g.x1)/2,ry=Math.abs(g.y2-g.y1)/2;
        c.globalAlpha=alfaRell(el,.08);c.fillStyle=colRell(el,colEl);c.beginPath();c.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);c.fill();c.globalAlpha=1;c.strokeStyle=colEl;c.lineWidth=(el.ancho||2)+hoverExtra;c.beginPath();c.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);c.stroke();
        if(sel){dibujarHandle(c,g.x1,g.y1,colEl);dibujarHandle(c,g.x2,g.y2,colEl);}
      } else if (el.tipo === 'triangle'){
        // Triángulo rectángulo formado por los dos puntos.
        var colT=el.color||'#58a6ff';
        c.globalAlpha=alfaRell(el,.08);c.fillStyle=colRell(el,colT);c.beginPath();c.moveTo(g.x1,g.y1);c.lineTo(g.x2,g.y2);c.lineTo(g.x1,g.y2);c.closePath();c.fill();c.globalAlpha=1;c.strokeStyle=colT;c.lineWidth=(el.ancho||2)+hoverExtra;c.beginPath();c.moveTo(g.x1,g.y1);c.lineTo(g.x2,g.y2);c.lineTo(g.x1,g.y2);c.closePath();c.stroke();
        if(sel){dibujarHandle(c,g.x1,g.y1,colT);dibujarHandle(c,g.x2,g.y2,colT);}
      } else if (el.tipo === 'arrow'){
        // Flecha: línea con punta triangular en el segundo punto.
        var colAr=el.color||'#3fb950';dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,colAr,2+hoverExtra);var a=Math.atan2(g.y2-g.y1,g.x2-g.x1),hs=10;
        c.fillStyle=colAr;c.beginPath();c.moveTo(g.x2,g.y2);c.lineTo(g.x2-hs*Math.cos(a-Math.PI/6),g.y2-hs*Math.sin(a-Math.PI/6));c.lineTo(g.x2-hs*Math.cos(a+Math.PI/6),g.y2-hs*Math.sin(a+Math.PI/6));c.closePath();c.fill();
        if(sel){dibujarHandle(c,g.x1,g.y1,colAr);dibujarHandle(c,g.x2,g.y2,colAr);}
      } else if (el.tipo === 'text'){
        // Texto: se pinta con su fuente y, al seleccionarlo o pasar el cursor, se enmarca con borde punteado.
        c.font=fuenteTexto(el);c.fillStyle=el.color||'#ffffff';c.fillText(el.texto||'Texto',g.x,g.y);
        if(sel||hov){var tw=c.measureText(el.texto||'Texto').width,sz=el.tamano||13;c.strokeStyle='rgba(88,166,255,.8)';c.lineWidth=1;c.setLineDash([3,3]);c.strokeRect(g.x-4,g.y-sz-3,tw+8,sz+9);c.setLineDash([]);}
      } else if (el.tipo === 'measure'){
        // Medida: rectángulo azul (sube) o rojo (baja) con etiqueta de diferencia en pips o precio, porcentaje y número de barras.
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

    /** Formatea un tiempo UNIX (segundos) como texto dd/mm hh:mm en UTC para las etiquetas del eje de tiempo. */
    function fmtTiempo(t){
      // Auxiliar local p: rellena con un cero a la izquierda los números menores de 10.
      var d=new Date(t*1000); function p(n){return (n<10?'0':'')+n;}
      return p(d.getUTCDate())+'/'+p(d.getUTCMonth()+1)+' '+p(d.getUTCHours())+':'+p(d.getUTCMinutes());
    }

    /** Pinta una etiqueta de precio en el eje derecho a la altura y (rectángulo de color con el precio). No pinta si y es inválida o queda fuera del área de trazado. Recibe contexto, y, precio, colores de fondo y texto y el área de trazado ap. */
    function badgePrecio(c,y,precio,fondo,texto,ap){
      if(!ok(y)||y<0||y>ap.h)return;var w=cssW-ap.w;c.save();c.fillStyle=fondo;c.fillRect(ap.w,y-10,w,20);c.fillStyle=texto;c.font='11px sans-serif';c.textBaseline='middle';c.textAlign='left';c.fillText(precio.toFixed(DIGITS),ap.w+6,y);c.restore();
    }
    /** Pinta una etiqueta de tiempo en el eje inferior centrada en x (limitada al área de trazado). Recibe contexto, x, tiempo, color de fondo y el área ap. */
    function badgeTiempo(c,x,t,fondo,ap){
      var h=cssH-ap.h;if(!ok(x)||x<0||x>ap.w||h<10)return;var w=92,bx=Math.max(0,Math.min(ap.w-w,x-w/2));c.save();c.fillStyle=fondo;c.fillRect(bx,ap.h,w,h);c.fillStyle='#fff';c.font='11px sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillText(fmtTiempo(t),bx+w/2,ap.h+h/2);c.restore();
    }
    /** Pinta en los ejes las etiquetas de precio y tiempo asociadas a un dibujo (las de sus puntos 1 y 2, o la de la propia línea para horizontal, vertical, rayo horizontal y cruz); el texto no lleva etiquetas. */
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

    /** Repinta todo el lienzo: lo limpia, recorta al área de trazado, dibuja todos los dibujos y el que está en curso, y luego (fuera del recorte) pinta las etiquetas de los ejes del seleccionado, de las líneas horizontales y verticales y del dibujo en curso. No hace nada sin serie o sin datos. */
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

    // Última firma de la vista; permite detectar movimientos del gráfico (escala vertical o zoom) que no avisan por evento.
    var ultimaFirma = '';
    /** Genera una firma de texto de la vista actual (coordenadas de dos precios de referencia y de dos índices lógicos). Si cambia entre fotogramas, la escala de precio o de tiempo se movió y hay que repintar. Devuelve cadena vacía sin datos o serie. */
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

    /** Bucle de renderizado con requestAnimationFrame: repinta solo si el lienzo está marcado como sucio o, cuando hay dibujos, si la firma de la vista cambió; así se evita pintar en vano. Se reprograma a sí mismo cada fotograma. */
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


/* -------------------------------------------------------------------------------------------------------
   ------------------------------ FIN Piña y Jara 21_dibujo_hit_y_render .JS -----------------------------
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
