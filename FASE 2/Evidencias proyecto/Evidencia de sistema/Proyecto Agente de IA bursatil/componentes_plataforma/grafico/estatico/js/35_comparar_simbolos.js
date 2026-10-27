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
   ----------------------------- INICIO Piña y Jara 35_comparar_simbolos .JS -----------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Comparar con otros símbolos (varias series superpuestas, en % sobre el mismo gráfico)
    // Como "Comparar o añadir símbolo" de XM/TradingView: cada símbolo se dibuja como una línea con su cierre y el
    // eje de precios pasa a porcentaje (todas las series parten de 0 % en la primera barra visible).
    // Los símbolos comparados se piden a la API con la misma temporalidad y número de barras que el gráfico principal
    // (/velas) y se actualizan cada pocos segundos (/ultima). La lista de símbolos sale de /simbolos (servidor_datos.py).
    // COLORES_CMP: colores asignados a los símbolos comparados; MAX_CMP: máximo de símbolos a la vez
    var COLORES_COMPARAR = ['#a855f7', '#f59e0b', '#06b6d4', '#ec4899', '#84cc16'];
    var MAXIMO_COMPARAR = 5;
    // comparados: símbolos comparados ahora mismo (símbolo, color, serie, datos, error, contador de peticiones y elemento del %)
    var comparados = [];            // { sym, color, serie, datos, error, req, elPct }
    // catalogoSimbolos: símbolos que ofrece el servidor para elegir
    var catalogoSimbolos = null;    // lista del servidor [{n, d, c}]; null = aún no disponible
    // catalogoEstado: estado de la descarga del catálogo
    var catalogoEstado = '';        // '' | 'cargando' | 'sin_servidor'

    // Elementos de la ventana de comparar símbolos
    var modalComparar = document.getElementById('comparar-modal-superposicion');
    var compararInput = document.getElementById('comparar-buscar-entrada');
    var compararLista = document.getElementById('comparar-lista-contenedor');
    var compararMensaje = document.getElementById('comparar-mensaje');

    // TITULO SIMBOLO VALIDO

    /**
     * Comprueba que s sea un nombre de símbolo admisible (1 a 24 caracteres alfanuméricos y . _ # + -). Devuelve un
     * booleano.
     */
    function simboloValido(s){ return /^[A-Za-z0-9._#+\-]{1,24}$/.test(s); }
    // TITULO BUSCAR CMP

    /** Busca en la lista comparados el símbolo sym sin distinguir mayúsculas. Devuelve su registro o null. */
    function buscarComparar(sym){
      for (var i = 0; i < comparados.length; i++) if (comparados[i].sym.toUpperCase() === String(sym).toUpperCase()) return comparados[i];
      return null;
    }
    // TITULO COLOR LIBRE CMP

    /**
     * Devuelve el primer color de COLORES_CMP que no usa ningún símbolo comparado (o el primero si todos están
     * usados).
     */
    function colorLibreComparar(){
      var usados = comparados.map(function(c){ return c.color; });
      for (var i = 0; i < COLORES_COMPARAR.length; i++) if (usados.indexOf(COLORES_COMPARAR[i]) < 0) return COLORES_COMPARAR[i];
      return COLORES_COMPARAR[0];
    }

    // TITULO APLICAR MODO COMPARAR

    // Eje en % mientras haya algo comparado; al volver a normal se recuperan los indicadores sobre el precio
    /**
     * Activa o desactiva el modo comparar según haya símbolos comparados: pone el eje de precios en porcentaje o
     * normal, actualiza el botón Comparar y, si cambió el modo, recalcula los indicadores y redibuja.
     */
    function aplicarModoComparar(){
      var activo = comparados.length > 0;
      var cambio = (activo !== modoComparar);
      modoComparar = activo;
      try {
        chart.priceScale('right').applyOptions({
          mode: activo ? LightweightCharts.PriceScaleMode.Percentage : LightweightCharts.PriceScaleMode.Normal
        });
      } catch (e) {}
      var b = document.getElementById('boton-comparar-seleccionar');
      if (b) {
        b.classList.toggle('activo', activo);
        var sp = b.querySelector('span');
        if (sp) sp.textContent = activo ? 'Comparar (' + comparados.length + ')' : 'Comparar';
      }
      if (cambio) actualizarIndicadoresActivos();
      redibujarTodo();
    }

    // TITULO PCT VISIBLE CMP

    // Variación (%) de una serie entre la primera barra visible y la última
    /**
     * Calcula la variación porcentual de una serie entre la primera barra visible y la última. Recibe las velas y
     * devuelve el porcentaje o null.
     */
    function porcentajeVisibleComparar(datos){
      if (!datos || !datos.length) return null;
      var r = null;
      try { r = chart.timeScale().getVisibleRange(); } catch (e) {}
      var i0 = 0;
      if (r && r.from !== undefined) { while (i0 < datos.length - 1 && datos[i0].time < r.from) i0++; }
      var base = datos[i0].close, ult = datos[datos.length - 1].close;
      return base ? (ult / base - 1) * 100 : null;
    }
    // TITULO ACTUALIZAR PCT CMP

    /**
     * Actualiza en la leyenda el porcentaje de cada símbolo comparado, con su color (verde/rojo) o un mensaje de
     * error.
     */
    function actualizarPorcentajeComparar(){
      comparados.forEach(function(c){
        if (!c.elPct) return;
        if (c.error) { c.elPct.textContent = c.error; c.elPct.style.color = '#f85149'; return; }
        var p = porcentajeVisibleComparar(c.datos);
        if (p === null) { c.elPct.textContent = '…'; c.elPct.style.color = '#8b949e'; return; }
        c.elPct.textContent = (p >= 0 ? '+' : '') + p.toFixed(2) + '%';
        c.elPct.style.color = p >= 0 ? '#3fb950' : '#f85149';
      });
    }
    // TITULO HAY INDICADOR SOBRE PRECIO

    /**
     * Indica si hay algún indicador activo y visible que se dibuje sobre el precio (los que se ocultan al comparar).
     */
    function hayIndicadorSobrePrecio(){
      return indicadorActivos.some(function(i){ return DEFS[i.id] && DEFS[i.id].destino === 'precio' && !i.oculto; });
    }
    // TITULO REFRESCAR LEYENDA CMP

    /**
     * Reconstruye la leyenda de símbolos comparados (punto de color, nombre, porcentaje y botón de quitar) y el aviso
     * de indicadores ocultos.
     */
    function refrescarLeyendaComparar(){
      var cont = document.getElementById('tradingview-comparar-leyenda');
      if (!cont) return;
      cont.innerHTML = '';
      comparados.forEach(function(c){
        var it = document.createElement('div'); it.className = 'comparar-elemento';
        var pto = document.createElement('span'); pto.className = 'comparar-punto'; pto.style.background = c.color;
        var nom = document.createElement('span'); nom.className = 'comparar-simbolo'; nom.textContent = c.sym;
        var pct = document.createElement('span'); pct.className = 'comparar-porcentaje';
        var x = document.createElement('button'); x.className = 'comparar-x'; x.title = 'Quitar ' + c.sym; x.textContent = String.fromCharCode(10005);
        x.addEventListener('click', function(ev){ ev.stopPropagation(); quitarComparado(c); });
        it.appendChild(pto); it.appendChild(nom); it.appendChild(pct); it.appendChild(x);
        cont.appendChild(it);
        c.elPct = pct;
      });
      if (comparados.length && hayIndicadorSobrePrecio()) {
        var nota = document.createElement('div'); nota.className = 'comparar-nota';
        nota.textContent = 'Indicadores sobre el precio ocultos mientras compares';
        cont.appendChild(nota);
      }
      actualizarPorcentajeComparar();
    }

    // TITULO GUARDAR SELECCION CMP

    /** Guarda los símbolos comparados en la configuración recordada y refresca la leyenda. */
    function guardarSeleccionComparar(){
      listaCompararGuardada = comparados.map(function(c){ return c.sym; });
      guardarConfiguracion();
      refrescarLeyendaComparar();
    }

    // TITULO CARGAR COMPARADO

    /**
     * Pide a la API las velas del símbolo comparado c con la temporalidad y el número de barras actuales y actualiza
     * su serie; ignora respuestas obsoletas mediante c.req y anota errores.
     */
    function cargarComparado(c){
      if (repeticionActivo){ repeticionCargarComparado(c); return; }   // en replay el comparado carga su historial largo y avanza con el principal
      var iconoMaterialId = ++c.req, tf = temporalidadActual, n = nBarrasActual;
      fetch(API + '/velas/' + encodeURIComponent(c.sym) + '?tf=' + tf + '&n=' + n)
        .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function(v){
          if (iconoMaterialId !== c.req || comparados.indexOf(c) < 0) return;
          if (!Array.isArray(v) || !v.length) { c.error = 'sin datos'; c.datos = []; c.serie.setData([]); }
          else { c.error = ''; c.datos = v; c.serie.setData(v.map(function(p){ return { time: p.time, value: p.close }; })); }
          actualizarPorcentajeComparar(); redibujarTodo();
        })
        .catch(function(){
          if (iconoMaterialId !== c.req || comparados.indexOf(c) < 0) return;
          c.error = 'sin conexión'; actualizarPorcentajeComparar();
        });
    }
    // TITULO RECARGAR COMPARADOS

    /**
     * Vuelve a cargar los datos de todos los símbolos comparados (se llama al cambiar de temporalidad o de número de
     * barras).
     */
    function recargarComparados(){ comparados.forEach(cargarComparado); }

    // TITULO AGREGAR COMPARADO

    // Devuelve '' si se añadió, o el motivo por el que no se pudo
    /**
     * Añade el símbolo sym a la comparación creando su serie de línea. Devuelve una cadena vacía si se añadió o el
     * motivo del rechazo; sinGuardar evita guardar la configuración (restauración inicial).
     */
    function agregarComparado(sym, sinGuardar){
      sym = String(sym || '').trim();
      if (!simboloValido(sym)) return 'Símbolo no válido.';
      if (sym.toUpperCase() === SIMBOLO.toUpperCase()) return 'Ese ya es el símbolo principal del gráfico.';
      if (buscarComparar(sym)) return 'Ya está en la comparación.';
      if (comparados.length >= MAXIMO_COMPARAR) return 'Máximo ' + MAXIMO_COMPARAR + ' símbolos comparados.';
      if (PLAN.comparar != null && comparados.length >= PLAN.comparar) { avisoPlan(PLAN.mensajes.comparar); return PLAN.mensajes.comparar; }   // límite del plan del usuario
      var color = colorLibreComparar();
      var serieC = chart.addLineSeries({
        color: color, lineWidth: 2, priceLineVisible: false, lastValueVisible: true, title: sym,
        priceFormat: { type: 'price', precision: 2, minMove: 0.01 }
      });
      var c = { sym: sym, color: color, serie: serieC, datos: [], error: '', req: 0, elPct: null };
      comparados.push(c);
      aplicarModoComparar();
      cargarComparado(c);
      if (sinGuardar) { listaCompararGuardada = comparados.map(function(x){ return x.sym; }); refrescarLeyendaComparar(); }
      else guardarSeleccionComparar();
      return '';
    }
    // TITULO QUITAR COMPARADO

    /**
     * Quita el símbolo comparado c: cancela sus peticiones, elimina su serie, actualiza el modo comparar y guarda.
     */
    function quitarComparado(c){
      var i = comparados.indexOf(c);
      if (i < 0) return;
      if (typeof repeticionAlQuitarComparado === 'function') repeticionAlQuitarComparado(c);   // el replay cierra la posición que tuviera en ese símbolo
      comparados.splice(i, 1); c.req++;
      try { chart.removeSeries(c.serie); } catch (e) {}
      aplicarModoComparar();
      guardarSeleccionComparar();
    }

    // TITULO MENSAJE CMP

    // --- Ventana de búsqueda ---
    /** Muestra el texto t en la línea de mensajes de la ventana de comparar (vacía si no se indica). */
    function mensajeComparar(t){ compararMensaje.textContent = t || ''; }
    // TITULO NOTA CMP

    /** Añade a la lista de la ventana de comparar una nota informativa con el texto t. */
    function notaComparar(t){
      var d = document.createElement('div'); d.className = 'comparar-nota'; d.textContent = t; compararLista.appendChild(d);
    }
    // TITULO RENDERIZAR LISTA CMP

    /**
     * Dibuja la lista de símbolos de la ventana de comparar filtrada por texto (hasta 150), con su estado (Principal,
     * Añadir, Quitar); al pulsar una fila añade o quita el símbolo. Muestra notas si se está cargando o no hay
     * servidor.
     */
    function renderizarListaComparar(filtro){
      compararLista.innerHTML = '';
      if (catalogoEstado === 'cargando') { notaComparar('Cargando símbolos…'); return; }
      if (catalogoSimbolos === null) {
        notaComparar('No se pudo cargar la lista de símbolos (reinicia servidor_datos.py para activarla). Mientras tanto escribe el símbolo exacto y pulsa Enter.');
        return;
      }
      var f = String(filtro || '').trim().toLowerCase(), mostrados = 0;
      for (var i = 0; i < catalogoSimbolos.length && mostrados < 150; i++) {
        // Cierre de ámbito por símbolo del catálogo: cada fila conserva su propio it en el manejador de clic
        (function(it){
          var texto = (it.n + ' ' + (it.d || '') + ' ' + (it.c || '')).toLowerCase();
          if (f && texto.indexOf(f) < 0) return;
          mostrados++;
          var principal = it.n.toUpperCase() === SIMBOLO.toUpperCase();
          var c = buscarComparar(it.n);
          var fila = document.createElement('div'); fila.className = 'comparar-fila' + (principal ? ' deshab' : '');
          var txt = document.createElement('div'); txt.className = 'comparar-texto';
          var l1 = document.createElement('div');
          var nom = document.createElement('span'); nom.className = 'comparar-nombre'; nom.textContent = it.n;
          l1.appendChild(nom);
          if (it.c) { var cat = document.createElement('span'); cat.className = 'comparar-categoria'; cat.textContent = it.c; l1.appendChild(cat); }
          txt.appendChild(l1);
          if (it.d) { var de = document.createElement('div'); de.className = 'comparar-descripcion'; de.textContent = it.d; txt.appendChild(de); }
          var est = document.createElement('span'); est.className = 'comparar-estado' + (c ? ' on' : '');
          est.textContent = principal ? 'Principal' : (c ? 'Quitar' : 'Añadir');
          fila.appendChild(txt); fila.appendChild(est);
          if (!principal) fila.addEventListener('click', function(){
            var actual = buscarComparar(it.n);
            if (actual) { quitarComparado(actual); mensajeComparar(''); } else { mensajeComparar(agregarComparado(it.n)); }
            renderizarListaComparar(compararInput.value);
          });
          compararLista.appendChild(fila);
        })(catalogoSimbolos[i]);
      }
      if (!mostrados) notaComparar('Sin resultados. Pulsa Enter para intentar con «' + filtro + '».');
    }
    // TITULO CARGAR CATALOGO

    /**
     * Descarga de la API (/simbolos) el catálogo de símbolos disponibles una sola vez y redibuja la lista; marca el
     * estado de carga o de servidor no disponible.
     */
    function cargarCatalogo(){
      if (catalogoSimbolos !== null || catalogoEstado === 'cargando') return;
      catalogoEstado = 'cargando'; renderizarListaComparar(compararInput.value);
      fetch(API + '/simbolos')
        .then(function(r){ return r.json(); })
        .then(function(v){
          if (Array.isArray(v) && v.length) { catalogoSimbolos = v; catalogoEstado = ''; } else { catalogoEstado = 'sin_servidor'; }
          renderizarListaComparar(compararInput.value);
        })
        .catch(function(){ catalogoEstado = 'sin_servidor'; renderizarListaComparar(compararInput.value); });
    }
    // TITULO ABRIR MODAL CMP

    /**
     * Abre la ventana de comparar, limpia buscador y mensaje, dibuja la lista, solicita el catálogo y da foco al
     * buscador.
     */
    function abrirModalComparar(){
      modalComparar.style.display = 'flex'; mensajeComparar(''); compararInput.value = '';
      if (catalogoSimbolos === null) catalogoEstado = '';
      renderizarListaComparar('');
      cargarCatalogo();
      setTimeout(function(){ compararInput.focus(); }, 50);
    }
    // TITULO CERRAR MODAL CMP

    /** Cierra la ventana de comparar. */
    function cerrarModalComparar(){ modalComparar.style.display = 'none'; }

    // Eventos de la ventana: abrir, cerrar, filtrar al escribir y añadir con Enter el símbolo exacto escrito
    document.getElementById('boton-comparar-seleccionar').addEventListener('click', function(e){ e.stopPropagation(); abrirModalComparar(); });
    document.getElementById('comparar-modal-cerrar').addEventListener('click', cerrarModalComparar);
    modalComparar.addEventListener('click', function(e){ if (e.target === modalComparar) cerrarModalComparar(); });
    compararInput.addEventListener('input', function(){ mensajeComparar(''); renderizarListaComparar(compararInput.value); });
    compararInput.addEventListener('keydown', function(e){
      if (e.key === 'Escape') { cerrarModalComparar(); return; }
      if (e.key !== 'Enter') return;
      var t = compararInput.value.trim();
      if (!t) return;
      var exacto = (catalogoSimbolos || []).filter(function(it){ return it.n.toLowerCase() === t.toLowerCase(); })[0];
      mensajeComparar(agregarComparado(exacto ? exacto.n : t));
      renderizarListaComparar(compararInput.value);
    });

    // El % de la leyenda sigue al zoom/desplazamiento (a lo sumo una vez por fotograma)
    // rafCmp: evita repintar el % más de una vez por fotograma
    var rafComparar = false;
    chart.timeScale().subscribeVisibleTimeRangeChange(function(){
      if (!comparados.length || rafComparar) return;
      rafComparar = true;
      requestAnimationFrame(function(){ rafComparar = false; actualizarPorcentajeComparar(); });
    });

    // Actualización en vivo de los símbolos comparados (el feed de ticks solo cubre los símbolos de la página)
    // Temporizador de 6 s: pide la última vela de cada símbolo comparado y la integra en su serie
    setInterval(function(){
      if (!comparados.length || document.hidden || repeticionActivo) return;   // en replay no se consulta la última vela real de los comparados
      comparados.forEach(function(c){
        if (!c.datos.length || c.error) return;
        var tf = temporalidadActual, id = c.req;
        fetch(API + '/ultima/' + encodeURIComponent(c.sym) + '?tf=' + tf)
          .then(function(r){ return r.json(); })
          .then(function(v){
            if (tf !== temporalidadActual || id !== c.req || !v || !v.time || comparados.indexOf(c) < 0) return;
            var ultima = c.datos[c.datos.length - 1];
            if (v.time < ultima.time) return;
            if (v.time === ultima.time) c.datos[c.datos.length - 1] = v; else c.datos.push(v);
            c.serie.update({ time: v.time, value: v.close });
            actualizarPorcentajeComparar();
          })
          .catch(function(){});
      });
    }, 6000);

    // Restaurar la comparación recordada (sin volver a guardar mientras se arma el gráfico)
    configuracionComparar.forEach(function(s){ agregarComparado(s, true); });

/* -------------------------------------------------------------------------------------------------------
   ------------------------------- FIN Piña y Jara 35_comparar_simbolos .JS ------------------------------
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
