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
   ------------------------------ INICIO Piña y Jara 29_dibujo_cursores .JS ------------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Dibujo: tipos de cursor (cruce, punto, flecha, demostración) y borrador
    // Modo de cursor activo: 'cross' (cruz con líneas), 'dot' (punto), 'pointer' (flecha) o 'demo' (puntero láser con estela).
    var modoCursor = 'cross';
    // Puntos recientes {x, y, t} del ratón para dibujar la estela del modo demostración (máximo 60).
    var demoPuntos = [];
    // Modos de cursor que no son una herramienta de dibujo: al activarlos solo cambian el cursor y se vuelve a la herramienta de cruz.
    var CURSORES_PUROS = { dot: 1, pointer: 1, demo: 1 };

    // TITULO APLICAR MODO CURSOR

    /** Aplica un modo de cursor al gráfico: muestra u oculta las líneas de la cruz (y sus etiquetas), alterna las clases modo-punto, modo-flecha y modo-demo del contenedor y limpia la estela si no es la demostración. Recibe 'cross', 'dot', 'pointer' o 'demo'. */
    function aplicarModoCursor(m){
      modoCursor = m;
      var linea = (m === 'cross');
      try {
        chart.applyOptions({ crosshair: { vertLine: { visible: linea, labelVisible: m === 'cross' || m === 'dot' }, horzLine: { visible: linea, labelVisible: m === 'cross' || m === 'dot' } } });
      } catch (e) {}
      contenedorEl.classList.toggle('modo-punto', m === 'dot');
      contenedorEl.classList.toggle('modo-flecha', m === 'pointer');
      contenedorEl.classList.toggle('modo-demo', m === 'demo');
      if (m !== 'demo') { demoPuntos = []; redibujarTodo(); }
    }

    // El borrador es un modo de la herramienta de selección: con un clic sobre un dibujo lo elimina
    // El borrador es un modo de la herramienta de selección: con un clic sobre un dibujo lo elimina
    // Indica si el modo borrador está activo (herramienta 'eraser').
    var modoBorrador = false;
    // Guarda la versión anterior de activarHerramienta.
    var activarAntesCursores = activarHerramienta;
    /** Versión de activarHerramienta que añade los modos de cursor y el borrador: los cursores puros solo aplican su modo y el borrador deja la herramienta de cruz con el botón marcado como 'eraser'. Delega en la versión anterior con la herramienta ya resuelta. Recibe el nombre de la herramienta. */
    activarHerramienta = function(t){
      var borrador = (t === 'eraser');
      if (CURSORES_PUROS[t]) { aplicarModoCursor(t); t = 'cross'; }
      if (borrador) t = 'cross';
      modoBorrador = borrador;
      activarAntesCursores(t);
      var btn = document.getElementById('herramienta-cruz');
      if (btn) { btn.setAttribute('data-tool', borrador ? 'eraser' : 'cross'); if (borrador) btn.classList.add('active'); }
      contenedorEl.classList.toggle('modo-borrador', borrador);
      if (borrador) { seleccionadoId = null; redibujarTodo(); }
    };
    // elegir "Cruce" en el menú devuelve el cursor normal
    // elegir "Cruce" en el menú devuelve el cursor normal
    /** Función autoejecutable que conecta la opción "Cruce" del menú de cursores (#cursor-desplegable) para restablecer el modo de cursor normal. */
    (function(){
      var it = document.querySelector('#cursor-desplegable .tvtool-desplegable-elemento[data-tool="cross"]');
      if (it) it.addEventListener('click', function(){ aplicarModoCursor('cross'); });
    })();

    // Clic con el borrador activo (fase de captura): elimina el dibujo bajo el cursor y confirma el cambio.
    window.addEventListener('mousedown', function(e){
      if (!modoBorrador || e.button !== 0 || bloqueado || !serie) return;
      if (!contenedorEl.contains(e.target) || (e.target.closest && e.target.closest('.tradingview-ui'))) return;
      var pos = posicionRaton(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      var hit = elementoBajo(pos.x, pos.y);
      if (!hit) return;
      e.preventDefault(); e.stopPropagation();
      elementosDibujados.splice(hit.idx, 1); seleccionadoId = null; encimaId = null; confirmarCambio();
    }, true);
    // Mouse move en modo demostración: acumula los puntos del ratón (máximo 60) para la estela láser y repinta.
    window.addEventListener('mousemove', function(e){
      if (modoCursor === 'demo' && activoHerramienta === 'cross' && !modoBorrador) {
        var p = posicionRaton(e);
        if (p.x >= 0 && p.y >= 0 && p.x <= cssW && p.y <= cssH) { demoPuntos.push({ x: p.x, y: p.y, t: Date.now() }); if (demoPuntos.length > 60) demoPuntos.shift(); redibujarTodo(); }
      }
    });
    // Al salir el ratón del gráfico se borra la estela de la demostración.
    contenedorEl.addEventListener('mouseleave', function(){ if (demoPuntos.length) { demoPuntos = []; redibujarTodo(); } });

    // ---------- Demostración: puntero láser con estela ----------
    // ---------- Demostración: puntero láser con estela ----------
    // Guarda la versión anterior de pintar.
    var pintarAntesCursores = pintar;
    /** Versión de pintar que, en el modo demostración, dibuja encima la estela del ratón (puntos rojos que se desvanecen en 650 ms) y un resplandor radial en la posición actual. */
    pintar = function(){
      pintarAntesCursores();
      if (modoCursor !== 'demo' || !demoPuntos.length) return;
      var ahora = Date.now();
      demoPuntos = demoPuntos.filter(function(q){ return ahora - q.t < 650; });
      if (!demoPuntos.length) return;
      ctx.save();
      demoPuntos.forEach(function(q, i){
        var edad = (ahora - q.t) / 650;
        ctx.globalAlpha = Math.max(0, 0.5 * (1 - edad)); ctx.fillStyle = '#f23645';
        ctx.beginPath(); ctx.arc(q.x, q.y, 6 * (1 - edad * 0.5), 0, Math.PI * 2); ctx.fill();
      });
      var u = demoPuntos[demoPuntos.length - 1];
      var g = ctx.createRadialGradient(u.x, u.y, 0, u.x, u.y, 18);
      g.addColorStop(0, 'rgba(242,54,69,0.55)'); g.addColorStop(1, 'rgba(242,54,69,0)');
      ctx.globalAlpha = 1; ctx.fillStyle = g; ctx.beginPath(); ctx.arc(u.x, u.y, 18, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#f23645'; ctx.beginPath(); ctx.arc(u.x, u.y, 6, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.restore();
    };
    /** Bucle por fotograma de la demostración: pide repintar mientras haya estela para que se apague sola con el tiempo. Se reprograma con requestAnimationFrame. */
    (function bucleDemo(){
      if (modoCursor === 'demo' && demoPuntos.length) redibujarTodo();   // la estela se apaga sola
      requestAnimationFrame(bucleDemo);
    })();

/* -------------------------------------------------------------------------------------------------------
   -------------------------------- FIN Piña y Jara 29_dibujo_cursores .JS -------------------------------
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
