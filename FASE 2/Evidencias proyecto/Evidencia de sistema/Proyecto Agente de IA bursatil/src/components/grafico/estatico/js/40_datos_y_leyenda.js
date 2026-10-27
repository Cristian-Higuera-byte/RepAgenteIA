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
   ------------------------------ INICIO Piña y Jara 40_datos_y_leyenda .JS ------------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Datos: carga de velas, leyenda, tipo de gráfico
    /**
     * Convierte las velas normales en velas Heikin-Ashi (cierre = promedio OHLC; apertura = media de la vela HA
     * anterior). Devuelve el nuevo array de velas.
     */
    function calcularHeikinAshi(datos){
      var ha = [];
      for (var i = 0; i < datos.length; i++){
        var d = datos[i];
        var haClose = (d.open + d.high + d.low + d.close) / 4;
        var haOpen = (i === 0) ? (d.open + d.close) / 2 : (ha[i-1].open + ha[i-1].close) / 2;
        var haHigh = Math.max(d.high, haOpen, haClose);
        var haLow = Math.min(d.low, haOpen, haClose);
        ha.push({ time: d.time, open: haOpen, high: haHigh, low: haLow, close: haClose, volume: d.volume });
      }
      return ha;
    }

    /**
     * Adapta las velas al formato que necesita la serie del tipo de gráfico: valor de cierre para línea y área, o
     * velas Heikin-Ashi u OHLC normales para las demás. Devuelve el array para setData/update.
     */
    function formatearDatos(datos, tipo){
      if (tipo === "line" || tipo === "area") {
        return datos.map(function(v){ return { time: v.time, value: v.close }; });
      }
      if (tipo === "heikin") {
        var ha = calcularHeikinAshi(datos);
        return ha.map(function(v){ return { time: v.time, open: v.open, high: v.high, low: v.low, close: v.close }; });
      }
      return datos.map(function(v){ return { time: v.time, open: v.open, high: v.high, low: v.low, close: v.close }; });
    }

    /**
     * Convierte una vela en un punto del histograma de volumen, verde si cierra al alza y rojo en caso contrario.
     */
    function aPuntoVolumen(v){
      return { time: v.time, value: v.volume || 0, color: (v.close >= v.open ? 'rgba(63,185,80,0.5)' : 'rgba(248,81,73,0.5)') };
    }

    /** Da formato abreviado al volumen v con sufijos K, M o B y dos decimales. */
    function fmtVol(v){
      v = v || 0;
      if (v >= 1e9) return (v/1e9).toFixed(2) + 'B';
      if (v >= 1e6) return (v/1e6).toFixed(2) + 'M';
      if (v >= 1e3) return (v/1e3).toFixed(2) + 'K';
      return String(v);
    }

    /**
     * Escribe en la leyenda del gráfico los valores OHLC de la vela v con la variación respecto al cierre anterior
     * (importe y porcentaje) y el volumen. Colorea en verde o rojo.
     */
    function actualizarLeyenda(v){
      if (!v) return;
      var elOhlc = document.getElementById('tv-ohlc-vals');
      var elVol = document.getElementById('tv-vol-val');
      if (!elOhlc) return;
      
      var cierreAnt = v.open;
      if (datosActuales.length > 1) {
        var idxActual = datosActuales.findIndex(function(d){ return d.time === v.time; });
        if (idxActual > 0) {
          cierreAnt = datosActuales[idxActual - 1].close;
        } else if (idxActual === -1 && datosActuales.length > 0) {
          cierreAnt = datosActuales[datosActuales.length - 2].close;
        }
      }

      var delta = v.close - cierreAnt;
      var pct = cierreAnt ? (delta / cierreAnt) * 100 : 0;
      var col = (v.close >= v.open) ? '#3fb950' : '#f85149';
      var colD = (delta >= 0) ? '#3fb950' : '#f85149';
      /**
       * Auxiliar de actualizarLeyenda: devuelve el HTML de una etiqueta l y un valor n con los decimales del símbolo,
       * coloreado según la vela.
       */
      function c(l, n){ return l + '<b style="color:' + col + '">' + n.toFixed(DIGITS) + '</b>'; }
      elOhlc.innerHTML =
        c('O', v.open) + c('H', v.high) + c('L', v.low) + c('C', v.close) +
        '<b style="color:' + colD + '">' + (delta >= 0 ? '+' : '') + delta.toFixed(DIGITS) +
        ' (' + (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%)</b>';
      if (elVol) elVol.innerText = 'Vol ' + fmtVol(v.volume);
    }

    /**
     * Descarga de la API las velas del símbolo para la temporalidad tf y n barras, y actualiza serie, volumen,
     * leyenda, indicadores y comparados. ajustarFit puede ser ultimas (últimas 150 velas), true (ajustar todo) o
     * falso. Ignora respuestas obsoletas con cargaId.
     */
    function cargar(tf, n, ajustarFit){
      if (typeof rpAlCambiarDatos === 'function') rpAlCambiarDatos();   // si hay un replay en curso, se sale de él antes de cargar datos nuevos
      tfActual = tf;
      var elTf = document.getElementById('lg-tf');
      if (elTf) elTf.innerText = (tf === 'MN1' ? 'MN' : tf);
      nBarrasActual = n;
      var miId = ++cargaId;
      cargando = true;
      fetch(API + "/velas/" + encodeURIComponent(SIMBOLO) + "?tf=" + tf + "&n=" + n)
        .then(function(r){
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function(velas){
          if (miId !== cargaId) return;
          cargando = false;
          if (velas && velas.length){
            datosActuales = velas;
            serie.setData(formatearDatos(velas, tipoActual));
            serieVolumen.setData(velas.map(aPuntoVolumen));
            if (ajustarFit === 'ultimas') {
              var nv = datosActuales.length;
              chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, nv - 150), to: nv + 8 });
            } else if (ajustarFit) {
              chart.timeScale().fitContent();
            }
            actualizarLeyenda(velas[velas.length - 1]);
            actualizarIndicadoresActivos();
            redibujarTodo();
            recargarComparados();   // los símbolos comparados se piden con la misma temporalidad y nº de barras
            if (typeof rpPrecargar === 'function') rpPrecargar(false);   // el historial del replay se pide por adelantado, ya con el gráfico dibujado
          }
        })
        .catch(function(){
          if (miId !== cargaId) return;
          cargando = false;
          if (!datosActuales.length) {
            var elOhlc = document.getElementById('tv-ohlc-vals');
            if (elOhlc) elOhlc.innerText = 'Sin conexión con la API (' + API + ')';
          }
        });
    }

    // Primera carga de velas al abrir el gráfico, mostrando las últimas
    cargar(tfActual, nBarrasActual, 'ultimas');

    // Menú desplegable del tipo de gráfico (velas, huecas, barras, línea, área, Heikin-Ashi)
    var btnTypeSelect = document.getElementById('btn-type-select');
    var typeMenu = document.getElementById('type-menu');

    // Abre y cierra el menú de tipos al pulsar el botón
    btnTypeSelect.addEventListener('click', function(e){ e.stopPropagation(); typeMenu.classList.toggle('show'); });

    // Un clic fuera cierra el menú de tipos
    window.addEventListener('click', function(){
      typeMenu.classList.remove('show');
    });

    // Al elegir un tipo: se guarda, se actualiza el botón, se recrea la serie y se vuelcan datos, indicadores y dibujos
    document.querySelectorAll('#type-menu .tv-drop-item').forEach(function(item){
      item.addEventListener('click', function(){
        tipoActual = item.getAttribute('data-type');
        guardarConfig();
        btnTypeSelect.innerHTML = item.querySelector('svg').outerHTML + '<span>' + item.getAttribute('data-label') + '</span><svg class="caret" viewBox="0 0 10 10"><path d="M2 3.5L5 6.5L8 3.5"/></svg>';
        crearSerie(tipoActual);
        if (datosActuales.length){
          serie.setData(formatearDatos(datosActuales, tipoActual));
          serieVolumen.setData(datosActuales.map(aPuntoVolumen));
          actualizarIndicadoresActivos();
        }
        redibujarTodo();
      });
    });

    // Restaura en la interfaz lo que se recordó: temporalidad, rango y tipo de gráfico
    marcarTF(tfActual);
    if (cfgRango >= 0) { var rbtn = document.querySelectorAll('.tvrange')[cfgRango]; if (rbtn) rbtn.classList.add('active'); }
    var itemTipo = document.querySelector('#type-menu .tv-drop-item[data-type="' + tipoActual + '"]');
    if (itemTipo) {
      btnTypeSelect.innerHTML = itemTipo.querySelector('svg').outerHTML + '<span>' + itemTipo.getAttribute('data-label') + '</span><svg class="caret" viewBox="0 0 10 10"><path d="M2 3.5L5 6.5L8 3.5"/></svg>';
    }


/* -------------------------------------------------------------------------------------------------------
   -------------------------------- FIN Piña y Jara 40_datos_y_leyenda .JS -------------------------------
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
