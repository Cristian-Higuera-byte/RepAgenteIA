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
   --------------------------- INICIO Piña y Jara 50_tiempo_real_y_acciones .JS --------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Tiempo real, temporalidades, captura y pantalla completa
    // --- Ticks en vivo del feed SSE (componentes_plataforma/flujo_precios/) ---------------
    // El feed reenvía cada tick por BroadcastChannel('pj-ticks'); aquí se mueve
    // la vela actual (o se abre una nueva al cambiar de periodo) al instante.
    // TF_SEG: duración en segundos de cada temporalidad, para calcular a qué vela pertenece un tick
    var TEMPORALIDAD_SEGUNDOS = {M1: 60, M5: 300, M15: 900, M30: 1800, H1: 3600, H4: 14400, D1: 86400, W1: 604800};
    // ultimoTickBC / ultimoPoll: instantes del último tick recibido y del último sondeo; rafTick evita repintados múltiples por fotograma
    var ultimoTickBC = 0, ultimoSondeo = 0, rafTick = false;
    // Escucha el canal pj-ticks si el navegador lo soporta
    if ('BroadcastChannel' in window){
      var bcTicks = new BroadcastChannel('pj-ticks');
      /**
       * Manejador del feed de ticks: lee el tick del símbolo, abre una vela nueva o actualiza la última con el Bid, y
       * programa un único repintado por fotograma de serie, volumen, leyenda e indicadores.
       */
      bcTicks.onmessage = function(ev){
        var t = ev.data && ev.data.t && ev.data.t[SIMBOLO];
        if (!t || !t.b || cargando || repeticionActivo || !datosActuales.length) return;   // en replay no se mezcla el precio en vivo con el pasado
        ultimoTickBC = Date.now();
        var px = t.b;                       // las velas de MT5 se construyen con el Bid
        var ultima = datosActuales[datosActuales.length - 1];
        var seg = TEMPORALIDAD_SEGUNDOS[temporalidadActual];
        // La vela del tick se calcula a partir de la última vela cargada (no del reloj UNIX): así coincide con el horario de apertura
        // de H4, D1 y W1 de la fuente, que no empiezan en múltiplos exactos de su duración.
        var inicio = seg ? ultima.time + Math.floor((t.t - ultima.time) / seg) * seg : ultima.time;
        if (inicio > ultima.time){
          datosActuales.push({time: inicio, open: px, high: px, low: px, close: px, volume: 0});
        } else if (inicio === ultima.time){
          datosActuales[datosActuales.length - 1] = Object.assign({}, ultima, {
            close: px, high: Math.max(ultima.high, px), low: Math.min(ultima.low, px)
          });
        } else {
          return;
        }
        if (rafTick) return;                // como máximo un repintado por frame
        rafTick = true;
        requestAnimationFrame(function(){
          rafTick = false;
          var v = datosActuales[datosActuales.length - 1];
          var f = formatearDatos(datosActuales, tipoActual);
          serie.update(f[f.length - 1]);
          serieVolumen.update(aPuntoVolumen(v));
          actualizarLeyenda(v);
          actualizarIndicadoresTick();
          redibujarTodo();
        });
      };
    }

    // Sondeo cada 1,5 s de la última vela a la API; con el feed activo solo resincroniza cada 5 s
    setInterval(function(){
      if (cargando || sondeoEnCurso || repeticionActivo || !datosActuales.length) return;   // en replay no se consulta la última vela real
      // Con el feed entregando ticks, el polling solo resincroniza (volumen real,
      // vela cerrada) cada 5 s en vez de cada 1,5 s.
      if (Date.now() - ultimoTickBC < 4000 && Date.now() - ultimoSondeo < 5000) return;
      ultimoSondeo = Date.now();
      var temporalidadLlamada = temporalidadActual;
      var idLlamada = cargaId;
      sondeoEnCurso = true;
      fetch(API + "/ultima/" + encodeURIComponent(SIMBOLO) + "?tf=" + temporalidadLlamada)
        .then(function(r){ return r.json(); })
        .then(function(v){
          if (temporalidadLlamada !== temporalidadActual || idLlamada !== cargaId) return;
          if (v && v.time){
            var ultima = datosActuales[datosActuales.length - 1];
            if (v.time < ultima.time) return;
            if (ultima.time === v.time){
              // Con el feed activo el cierre lo manda el último tick (Bid): el sondeo solo aporta el
              // volumen y los extremos, para que la línea del precio no salte y quede igual al recuadro.
              if (Date.now() - ultimoTickBC < 4000) {
                v = Object.assign({}, v, {close: ultima.close,
                  high: Math.max(v.high, ultima.high), low: Math.min(v.low, ultima.low)});
              }
              datosActuales[datosActuales.length - 1] = v;
            } else {
              datosActuales.push(v);
            }
            var datosFormateados = formatearDatos(datosActuales, tipoActual);
            serie.update(datosFormateados[datosFormateados.length - 1]);
            serieVolumen.update(aPuntoVolumen(v));
            actualizarLeyenda(v);
            actualizarIndicadoresTick();
            redibujarTodo();
          }
        })
        .catch(function(){})
        .then(function(){ sondeoEnCurso = false; });
    }, 1500);

    // Al mover el cursor, la leyenda muestra la vela señalada (o la última si el cursor sale)
    chart.subscribeCrosshairMove(function(parametro){
      if (!parametro || !parametro.time){
        if (datosActuales.length) actualizarLeyenda(datosActuales[datosActuales.length - 1]);
        return;
      }
      var idx = datosActuales.findIndex(function(d){ return d.time === parametro.time; });
      if (idx >= 0) actualizarLeyenda(datosActuales[idx]);
    });

    // TITULO MARCAR TF

    /** Resalta en la barra el botón de la temporalidad tf y quita el resalte de los demás. */
    function marcarTemporalidad(tf){
      document.querySelectorAll('.tvtf').forEach(function(b){
        b.classList.toggle('active', b.getAttribute('data-tf') === tf);
      });
    }

    // Botones de temporalidad: cargan la serie con ese tf y guardan la configuración
    document.querySelectorAll('.tvtf').forEach(function(btn){
      btn.addEventListener('click', function(){
        var tf = btn.getAttribute('data-tf');
        marcarTemporalidad(tf);
        document.querySelectorAll('.tvrange').forEach(function(b){ b.classList.remove('active'); });
        cargar(tf, parseInt(btn.getAttribute('data-n'), 10), 'ultimas');
        guardarConfiguracion();
      });
    });

    // Botones de rango rápido (1D, 5D, 1M…): cargan datos y ajustan la vista a todo el contenido
    document.querySelectorAll('.tvrange').forEach(function(btn){
      btn.addEventListener('click', function(){
        var tf = btn.getAttribute('data-tf');
        document.querySelectorAll('.tvrange').forEach(function(b){ b.classList.remove('active'); });
        btn.classList.add('active');
        marcarTemporalidad(tf);
        cargar(tf, parseInt(btn.getAttribute('data-n'), 10), true);
        guardarConfiguracion();
      });
    });

    // Botón de captura: compone en un canvas el gráfico y los dibujos, añade símbolo, temporalidad y fecha, y descarga un PNG
    var botonCaptura = document.getElementById('boton-captura');
    if (botonCaptura){
      botonCaptura.addEventListener('click', function(){
        try {
          var captura = chart.takeScreenshot();
          var seleccionAnterior = seleccionadoId, hovAnterior = encimaId;
          seleccionadoId = null; encimaId = null;
          pintar();
          var out = document.createElement('canvas');
          out.width = captura.width; out.height = captura.height;
          var oc = out.getContext('2d');
          oc.drawImage(captura, 0, 0);
          oc.drawImage(canvas, 0, 0, captura.width, captura.height);
          seleccionadoId = seleccionAnterior; encimaId = hovAnterior;
          redibujarTodo();

          var esc = captura.width / Math.max(1, cssW);
          var ahora = new Date();
          /** Auxiliar de la captura: rellena con cero a la izquierda los números menores de 10. */
          function dos(n){ return (n < 10 ? '0' : '') + n; }
          var fecha = ahora.getFullYear() + '-' + dos(ahora.getMonth() + 1) + '-' + dos(ahora.getDate()) + ' ' + dos(ahora.getHours()) + ':' + dos(ahora.getMinutes());
          oc.save();
          oc.textBaseline = 'top';
          oc.font = 'bold ' + Math.round(15 * esc) + 'px sans-serif';
          oc.fillStyle = '#ffffff';
          oc.fillText(SIMBOLO + '  ·  ' + temporalidadActual, 14 * esc, 10 * esc);
          oc.font = Math.round(11 * esc) + 'px sans-serif';
          oc.fillStyle = '#8b949e';
          oc.textAlign = 'right';
          oc.fillText('P&J  ·  ' + fecha, captura.width - 74 * esc, 12 * esc);
          oc.restore();

          out.toBlob(function(blob){
            if (!blob) return;
            var url = URL.createObjectURL(blob);
            var enlace = document.createElement('a');
            enlace.download = SIMBOLO + '_' + temporalidadActual + '_' + fecha.replace(/[- :]/g, '') + '.png';
            enlace.href = url;
            document.body.appendChild(enlace);
            enlace.click();
            document.body.removeChild(enlace);
            setTimeout(function(){ URL.revokeObjectURL(url); }, 2000);
          }, 'image/png');
        } catch (e) {}
      });
    }

    // (el botón de pantalla completa vive ahora en js/55_pantalla_completa.js)

/* -------------------------------------------------------------------------------------------------------
   ---------------------------- FIN Piña y Jara 50_tiempo_real_y_acciones .JS ----------------------------
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
