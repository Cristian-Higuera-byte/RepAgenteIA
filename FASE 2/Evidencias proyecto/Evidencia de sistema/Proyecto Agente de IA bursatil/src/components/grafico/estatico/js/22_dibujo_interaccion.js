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
   ----------------------------- INICIO Piña y Jara 22_dibujo_interaccion .JS ----------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Dibujo: selección de herramienta, ratón y teclado
    /** Activa o desactiva el desplazamiento y el zoom nativos del gráfico. Recibe true para bloquearlos (mientras se dibuja o arrastra un dibujo) y false para liberarlos. */
    function bloquearGrafico(b){
      try { chart.applyOptions({ handleScroll: !b, handleScale: !b }); } catch (e) {}
    }

    /** Cancela el dibujo que se está creando: borra el dibujo en curso y sus banderas de clic y pide repintar. */
    function cancelarDibujoEnCurso(){
      dibujoEnCurso = null; esperandoSegundoClick = false; inicioClick = null;
      redibujarTodo();
    }

    // Los grupos de herramientas se leen del HTML (cada .tvtool-group = botón + menú desplegable)
    // Grupos de herramientas leídos del HTML: cada uno guarda su botón (.tvtool) y su menú desplegable (.tvtool-flyout).
    var gruposFlyout = Array.prototype.map.call(document.querySelectorAll('.tvtool-group'), function(g){
      return { boton: g.querySelector('.tvtool'), menu: g.querySelector('.tvtool-flyout') };
    });
    /** Cierra todos los menús desplegables de herramientas salvo el indicado. Recibe el menú que debe quedar abierto (o null para cerrar todos). */
    function cerrarFlyouts(excepto){ gruposFlyout.forEach(function(g){if(g.menu&&g.menu!==excepto)g.menu.classList.remove('show');}); }
    // El menú se abre junto al botón pero se desplaza hacia arriba si no cabe en la altura visible
    /** Coloca el menú desplegable de un grupo junto a su botón; lo desplaza hacia arriba o abajo y limita su altura para que quepa en la ventana visible. Recibe el grupo { boton, menu }. */
    function colocarFlyout(g){
      var m = g.menu, alto = window.innerHeight;
      m.style.top = '0px'; m.style.maxHeight = (alto - 34) + 'px';
      var r = m.getBoundingClientRect(), b = g.boton.getBoundingClientRect();
      var desp = 0;
      if (r.bottom > alto - 8) desp = (alto - 8) - r.bottom;
      if (r.top + desp < 8) desp = 8 - r.top;
      m.style.top = desp + 'px';
    }
    // Para cada grupo: clic en el botón abre/cierra su menú (cerrando los demás) y clic en una opción activa esa herramienta, cambia el icono del botón y lo marca como activo.
    gruposFlyout.forEach(function(g){
      g.boton.addEventListener('click',function(e){e.stopPropagation();var abierto=g.menu.classList.contains('show');cerrarFlyouts(g.menu);g.menu.classList.toggle('show',!abierto);if(!abierto)colocarFlyout(g);});
      g.menu.querySelectorAll('.tvtool-flyout-item').forEach(function(item){
        item.addEventListener('click',function(e){e.stopPropagation();var tool=item.getAttribute('data-tool');g.menu.classList.remove('show');activarHerramienta(tool);var svg=item.querySelector('svg');if(svg)g.boton.innerHTML=svg.outerHTML+'<span class="tvtool-arrow">▼</span>';g.boton.setAttribute('data-tool',g.boton.id==='tool-cross'?(tool==='eraser'?'eraser':'cross'):tool);g.boton.classList.toggle('active',true);});
      });
    });
    // Un clic en cualquier parte de la ventana cierra los menús desplegables.
    window.addEventListener('click',function(){cerrarFlyouts(null);});

    // Número de puntos (clics) que requiere cada herramienta de dibujo; las no listadas usan 2.
    var TOOL_POINTS={
      trend:2,ray:2,extended:2,angle:2,hline:1,hray:1,vline:1,crossline:1,channel:3,
      fib:2,fib_extension:3,fib_channel:3,rectangle:2,ellipse:2,triangle:2,arrow:2,
      text:1,measure:2
    };
    /** Devuelve cuántos puntos necesita la herramienta indicada (por defecto 2). */
    function puntosHerramienta(tool){return TOOL_POINTS[tool]||2;}
    // Si es true, la herramienta sigue activa después de terminar un dibujo (botón "mantener").
    var mantenerHerramienta=false;

    /** Activa una herramienta de dibujo: cancela el dibujo en curso si cambia de herramienta, marca el botón correspondiente (salvo los de acción: limpiar, bloquear, imán y mantener) y ajusta el cursor. Recibe el nombre de la herramienta ('cross' para ninguna). */
    function activarHerramienta(toolName){
      if(dibujoEnCurso&&toolName!==activeTool)cancelarDibujoEnCurso();
      activeTool=toolName;
      document.querySelectorAll('.tvtool').forEach(function(b){
        var t=b.getAttribute('data-tool');
        if(t!=='clear'&&t!=='lock'&&t!=='magnet'&&t!=='keep')b.classList.toggle('active',t===toolName);
      });
      setCursor(toolName==='cross'?'':'cur-dibujar');
    }

    // Conecta los botones de la barra: limpiar borra todos los dibujos (con confirmación), bloquear impide editar, imán y mantener alternan su opción, y el resto activa su herramienta (los botones de grupo solo abren su menú).
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
        if(btn.parentNode&&btn.parentNode.classList&&btn.parentNode.classList.contains('tvtool-group'))return;   // los botones de grupo solo abren su menú
        activarHerramienta(tool);
      });
    });

    /** Convierte un evento del ratón en coordenadas relativas al contenedor del gráfico { x, y }. */
    function posMouse(e){var r=wrapEl.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};}

    /** Crea el dibujo inicial de la herramienta indicada con todos sus puntos en el punto del primer clic (también el tercero si la herramienta usa tres). Recibe herramienta y punto { time, price } y devuelve el objeto del dibujo. */
    function crearDibujoInicial(tool,pt){
      var d={tipo:tool,time1:pt.time,price1:pt.price,time2:pt.time,price2:pt.price};
      if(puntosHerramienta(tool)>=3){d.time3=pt.time;d.price3=pt.price;}
      return d;
    }

    /** Actualiza el punto activo (_puntoActual) del dibujo en curso con la posición del ratón (con imán si corresponde) y pide repintar. Recibe la posición y el evento. */
    function actualizarDibujoEnCurso(pos,e){
      if(!dibujoEnCurso)return;
      var pt=puntoDesdeMouse(pos.x,pos.y,magnetEfectivo(e));if(!pt)return;
      var n=dibujoEnCurso._puntoActual||2;
      dibujoEnCurso['time'+n]=pt.time;dibujoEnCurso['price'+n]=pt.price;redibujarTodo();
    }

    /** Termina el dibujo en curso: si es válido y tiene tamaño suficiente (más de 3 px y, para tres puntos, el tercero válido) lo agrega a la lista, lo selecciona y confirma el cambio; si no, lo descarta. Después vuelve a la herramienta de cruz o conserva la actual si "mantener" está activo. Recibe true si el usuario lo completó. */
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

    /** Devuelve las anclas originales de un dibujo (precio y/o posición lógica de sus puntos) al empezar un arrastre, para calcular el movimiento relativo sin acumular errores. Recibe el dibujo. */
    function anclasOriginales(el){
      if(el.tipo==='hline')return{price:el.price};
      if(el.tipo==='vline')return{l:tiempoALogico(el.time)};
      if(el.tipo==='crossline')return{l:tiempoALogico(el.time),price:el.price};
      if(el.tipo==='text')return{l:tiempoALogico(el.time),price:el.price};
      return{l1:tiempoALogico(el.time1),price1:el.price1,l2:tiempoALogico(el.time2),price2:el.price2,l3:el.time3!==undefined?tiempoALogico(el.time3):null,price3:el.price3};
    }

    /** Aplica el arrastre en curso al dibujo: en modo 'move' desplaza todos sus puntos por el cambio en barras y precio desde el inicio; en modo 'p1'/'p2'/'p3' mueve solo ese tirador (con imán si corresponde). Recibe la posición del ratón y el evento y pide repintar. */
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

    // Mouse abajo (fase de captura): según el estado completa el siguiente punto del dibujo en curso, empieza uno nuevo con la herramienta activa (las de un solo clic se crean al instante y el texto abre su editor) o selecciona/arrastra el dibujo bajo el cursor. Ignora la interfaz flotante (.tv-ui), los clics fuera del área de trazado y con el bloqueo activo.
    wrapEl.addEventListener('mousedown',function(e){
      if(e.target&&e.target.closest&&e.target.closest('.tv-ui'))return;
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
          editarTexto(null,pos,pt);
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

    // Si el script se ejecutó antes (recarga del bloque), retira los escuchas globales anteriores para no duplicarlos.
    if(window._tvGlobalMousemove){window.removeEventListener('mousemove',window._tvGlobalMousemove);window.removeEventListener('mouseup',window._tvGlobalMouseup);document.removeEventListener('keydown',window._tvGlobalKeydown);}

    /** Manejador global de mousemove: si hay arrastre lo aplica (tras superar 3 px de umbral); si hay dibujo en curso lo actualiza; si no, calcula el dibujo bajo el cursor para el resaltado y elige el cursor (mover, punto o dibujar). */
    window._tvGlobalMousemove=function(e){
      var pos=posMouse(e);
      if(arrastre){if(!arrastre.movido&&Math.hypot(pos.x-arrastre.x0,pos.y-arrastre.y0)<3)return;arrastre.movido=true;aplicarArrastre(pos,e);return;}
      if(dibujoEnCurso){actualizarDibujoEnCurso(pos,e);return;}
      var nuevoHover=null,cls='',dentro=pos.x>=0&&pos.y>=0&&pos.x<=cssW&&pos.y<=cssH;
      if(dentro&&!bloqueado&&activeTool==='cross'){var ap=areaTrazado();if(pos.x<=ap.w&&pos.y<=ap.h){var h=elementoBajo(pos.x,pos.y);if(h){nuevoHover=h.idx;cls=h.parte==='body'?'cur-mover':'cur-punto';}}}
      if(nuevoHover!==hoverId){hoverId=nuevoHover;redibujarTodo();}setCursor(activeTool!=='cross'?'cur-dibujar':cls);
    };
    window.addEventListener('mousemove',window._tvGlobalMousemove);

    /** Manejador global de mouseup: termina el arrastre confirmando el cambio si hubo movimiento; o, si hay dibujo en curso, decide según la distancia recorrida (más de 6 px) entre completar el dibujo, pasar al siguiente punto o esperar un segundo clic. Siempre desbloquea el gráfico. */
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

    // Si la ventana pierde el foco se termina cualquier arrastre (confirmando si hubo cambio) y se libera el gráfico.
    window.addEventListener('blur',function(){if(arrastre){var huboCambio=arrastre.movido;arrastre=null;if(huboCambio)confirmarCambio();}bloquearGrafico(false);});

    /** Manejador global de teclado (ignora campos de texto): Escape cancela el dibujo y la selección, Supr/Retroceso borra el dibujo seleccionado y Ctrl/Cmd+Z deshace, Ctrl/Cmd+Y o Ctrl/Cmd+Mayús+Z rehace. */
    window._tvGlobalKeydown=function(e){
      var tag=(e.target&&e.target.tagName)||'';if(tag==='INPUT'||tag==='TEXTAREA')return;var k=e.key;
      if(k==='Escape'){if(dibujoEnCurso)cancelarDibujoEnCurso();activarHerramienta('cross');if(seleccionadoId!==null){seleccionadoId=null;redibujarTodo();}return;}
      if((k==='Delete'||k==='Backspace')&&seleccionadoId!==null&&!bloqueado){e.preventDefault();elementosDibujados.splice(seleccionadoId,1);seleccionadoId=null;hoverId=null;confirmarCambio();return;}
      if(e.ctrlKey||e.metaKey){var kl=(k||'').toLowerCase();if(kl==='z'&&!e.shiftKey){e.preventDefault();deshacer();}else if(kl==='y'||(kl==='z'&&e.shiftKey)){e.preventDefault();rehacer();}}
    };
    document.addEventListener('keydown',window._tvGlobalKeydown);


/* -------------------------------------------------------------------------------------------------------
   ------------------------------ FIN Piña y Jara 22_dibujo_interaccion .JS ------------------------------
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
