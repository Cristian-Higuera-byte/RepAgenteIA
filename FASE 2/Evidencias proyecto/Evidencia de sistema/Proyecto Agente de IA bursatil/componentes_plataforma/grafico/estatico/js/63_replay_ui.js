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
   --------------------------------- INICIO Piña y Jara 63_replay_ui .JS ---------------------------------
   ------------------------------------------------------------------------------------------------------- */

    // =====================================================================================================
    // REPLAY (práctica sobre el pasado) · INTERFAZ
    // Permite volver a un punto del pasado, avanzar vela por vela (o en reproducción automática) y practicar
    // compras y ventas con dinero de prueba. Todo es simulado: NO envía órdenes ni toca la cuenta de MT5.
    // Varios activos: los símbolos añadidos con «Comparar» avanzan sincronizados con el símbolo principal (solo se
    // revelan sus velas hasta la hora de la vela principal) y también se puede operar en cualquiera de ellos, con
    // una posición por símbolo y un capital compartido. El motor de la cuenta está en 62_replay_motor.js.
    // =====================================================================================================

    var REPETICION_MAXIMO_VELAS = 5000;       // historial que se pide al servidor al entrar al replay
    var REPETICION_MINIMO_PREVIAS = 30;       // velas mínimas que deben quedar a la vista antes del punto de inicio (menos si el activo tiene poco historial)
    var REPETICION_MINIMO_TOTAL = 12;         // velas mínimas con las que se acepta usar el replay en un activo (activos nuevos o temporalidades largas)
    var REPETICION_CACHE_MS = 120000;      // cuánto tiempo vale el historial precargado antes de volver a pedirlo
    var repeticionPrecarga = {};           // historial ya pedido: 'SÍMBOLO|TF' → { t: instante, p: promesa con las velas }
    var repeticionPrecioTemporizador = null;        // espera antes de precargar, para no pedir en cada clic de temporalidad
    var repeticionCompleto = [];           // todas las velas disponibles (las que se irán revelando)
    var repeticionIndice = -1;                // posición en rpCompleto de la última vela visible
    var repeticionFase = '';               // '' (inactivo) | 'cargando' | 'elegir' | 'listo'
    var repeticionTemporizador = null;            // temporizador de la reproducción automática
    var repeticionSaliendo = false;        // evita que cargar() reinicie la salida mientras ya se está saliendo
    var repeticionCuenta = repeticionCuentaNueva(10000);
    var repeticionLineas = { entrada: null, sl: null, tp: null };   // líneas de precio de la posición abierta del símbolo principal
    var repeticionEl = {};                 // referencias a los elementos de la interfaz

    // TITULO RP FMT

    /** Formatea un número con separador de miles y los decimales indicados (por defecto 2). */
    function repeticionFormato(n, dec){
      return (typeof n === 'number' && isFinite(n)) ? n.toLocaleString('es-CL', { minimumFractionDigits: dec == null ? 2 : dec, maximumFractionDigits: dec == null ? 2 : dec }) : '—';
    }

    // TITULO RP FECHA

    /** Convierte una marca de tiempo (segundos) en texto "AAAA-MM-DD HH:MM" (hora UTC, como el eje del gráfico). */
    function repeticionFecha(t){
      var d = new Date(t * 1000);
      function dos(n){ return (n < 10 ? '0' : '') + n; }
      return d.getUTCFullYear() + '-' + dos(d.getUTCMonth() + 1) + '-' + dos(d.getUTCDate()) + ' ' + dos(d.getUTCHours()) + ':' + dos(d.getUTCMinutes());
    }

    // TITULO RP DECIMALES

    /**
     * Estima los decimales del precio de un símbolo. El principal usa los del gráfico (DIGITS); para los comparados
     * se deduce del nivel de precio (por ejemplo 5 decimales para ~1,1; 3 para ~150; 2 para precios de miles).
     */
    function repeticionDecimales(sym, precio){
      if (sym === SIMBOLO) return DIGITS;
      return precio >= 1000 ? 2 : (precio >= 10 ? 3 : 5);
    }

    // TITULO RP SIMBOLOS

    /** Devuelve la lista de símbolos con los que se puede operar: el principal y los comparados sin error. */
    function repeticionSimbolos(){
      return [SIMBOLO].concat(comparados.filter(function(c){ return !c.error; }).map(function(c){ return c.sym; }));
    }

    // TITULO RP COMPARADO DE

    /** Devuelve el objeto comparado de un símbolo (o null si es el principal o ya no está). */
    function repeticionComparadoDe(sym){
      for (var i = 0; i < comparados.length; i++) if (comparados[i].sym === sym) return comparados[i];
      return null;
    }

    // TITULO RP ULTIMA VELA

    /** Devuelve la última vela visible de un símbolo en este momento del replay (undefined si aún no tiene velas). */
    function repeticionUltimaVela(sym){
      if (sym === SIMBOLO) return datosActuales[datosActuales.length - 1];
      var c = repeticionComparadoDe(sym);
      return c && c.datos ? c.datos[c.datos.length - 1] : undefined;
    }

    // TITULO RP ULTIMAS

    /** Devuelve un objeto símbolo -> última vela visible, para todos los símbolos con posición abierta. */
    function repeticionUltimas(){
      var o = {};
      Object.keys(repeticionCuenta.pos).forEach(function(s){ o[s] = repeticionUltimaVela(s); });
      return o;
    }

    // TITULO RP HISTORIAL

    /**
     * Devuelve una promesa con el historial (hasta RP_MAX_VELAS velas) de un símbolo en una temporalidad. Si ya se pidió
     * hace menos de RP_CACHE_MS se reutiliza la misma petición (en curso o terminada), así que entrar al replay con el
     * historial precargado es instantáneo. Una petición fallida o vacía no se guarda, para que se pueda reintentar.
     */
    function repeticionHistorial(sym, tf){
      var k = sym + '|' + tf, h = repeticionPrecarga[k];
      if (h && Date.now() - h.t < REPETICION_CACHE_MS) return h.p;
      var p = fetch(API + '/velas/' + encodeURIComponent(sym) + '?tf=' + tf + '&n=' + REPETICION_MAXIMO_VELAS)
        .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function(v){ if (!Array.isArray(v) || !v.length) throw new Error('sin datos'); return v; });
      repeticionPrecarga[k] = { t: Date.now(), p: p };
      p.catch(function(){ if (repeticionPrecarga[k] && repeticionPrecarga[k].p === p) delete repeticionPrecarga[k]; });
      return p;
    }

    // TITULO RP PRECARGAR

    /**
     * Pide por adelantado el historial del símbolo y la temporalidad actuales, sin esperar a que el usuario pulse
     * «Replay». inmediato = true lo hace al instante (por ejemplo al pasar el ratón por el botón); si no, espera un
     * momento para no pedir en cada clic de temporalidad. No hace nada mientras hay un replay en curso.
     */
    function repeticionPrecargar(inmediato){
      clearTimeout(repeticionPrecioTemporizador);
      if (repeticionActivo) return;
      var lanzar = function(){ if (!repeticionActivo) repeticionHistorial(SIMBOLO, temporalidadActual).catch(function(){}); };
      if (inmediato) lanzar(); else repeticionPrecioTemporizador = setTimeout(lanzar, 900);
    }

    // TITULO RP MIN PREVIAS

    /** Velas mínimas previas al punto de inicio: RP_MIN_PREVIAS, o menos si el historial es corto (un tercio como máximo). */
    function repeticionMinimoPrevias(){ return Math.max(5, Math.min(REPETICION_MINIMO_PREVIAS, Math.floor(repeticionCompleto.length / 3))); }

    // TITULO RP CARGAR COMPARADO

    /**
     * Carga el historial completo de un símbolo comparado (hasta 5000 velas de la temporalidad actual) y lo
     * recorta a la hora del replay: mientras se elige el punto de inicio se ve entero; después solo hasta la vela
     * principal actual. Lo llama el gancho de cargarComparado() cuando hay un replay activo.
     */
    function repeticionCargarComparado(c){
      var iconoMaterialId = ++c.req, tf = temporalidadActual;
      repeticionHistorial(c.sym, tf)
        .then(function(v){
          if (iconoMaterialId !== c.req || comparados.indexOf(c) < 0 || !repeticionActivo) return;
          if (!Array.isArray(v) || !v.length){ c.error = 'sin datos'; c.completo = []; c.datos = []; c.serie.setData([]); }
          else { c.error = ''; c.completo = v; repeticionCortarComparado(c, repeticionFase === 'listo' ? datosActuales[datosActuales.length - 1].time : Infinity); }
          actualizarPorcentajeComparar(); redibujarTodo(); repeticionRefrescarPanel();
        })
        .catch(function(){ if (iconoMaterialId !== c.req || comparados.indexOf(c) < 0) return; c.error = 'sin conexión'; actualizarPorcentajeComparar(); repeticionRefrescarPanel(); });
    }

    // TITULO RP CORTAR COMPARADO

    /** Deja visibles en un comparado solo las velas con hora menor o igual a t (Infinity = todas) y reinicia su puntero. */
    function repeticionCortarComparado(c, t){
      var todas = c.completo || [];
      c.datos = todas.filter(function(b){ return b.time <= t; });
      c.ptr = c.datos.length;
      c.serie.setData(c.datos.map(function(p){ return { time: p.time, value: p.close }; }));
      actualizarPorcentajeComparar();
    }

    // TITULO RP AVANZAR COMPARADO

    /**
     * Revela en un comparado las velas que ya ocurrieron hasta la hora t (la de la vela principal): las agrega a su
     * serie en el gráfico y devuelve la lista de velas reveladas (puede ser vacía) para procesar sus stops.
     */
    function repeticionAvanzarComparado(c, t){
      var nuevas = [], todas = c.completo || [];
      while (c.ptr < todas.length && todas[c.ptr].time <= t){
        var b = todas[c.ptr++];
        c.datos.push(b);
        c.serie.update({ time: b.time, value: b.close });
        nuevas.push(b);
      }
      if (nuevas.length) actualizarPorcentajeComparar();
      return nuevas;
    }

    // TITULO RP AL QUITAR COMPARADO

    /**
     * Gancho de quitarComparado(): si el símbolo que se quita tiene una posición abierta en la práctica, se cierra
     * al último precio visible (motivo "Cierre manual") para que no quede una posición sin datos que la gobiernen.
     */
    function repeticionAlQuitarComparado(c){
      if (!repeticionActivo || !repeticionCuenta.pos[c.sym]) return;
      var b = repeticionUltimaVela(c.sym);
      if (b) repeticionCerrarAMercado(repeticionCuenta, c.sym, b, repeticionIndice);
      else delete repeticionCuenta.pos[c.sym];
      repeticionPintarLineas(); repeticionRefrescarPanel();
      setTimeout(repeticionRefrescarPanel, 0);   // otra vez cuando el comparado ya salió de la lista, para actualizar el selector «Operar en»
    }

    // TITULO RP CONSTRUIR UI

    /**
     * Construye una sola vez la interfaz del replay (barra de control y panel de práctica) dentro del
     * contenedor del gráfico, la deja oculta y conecta todos sus botones.
     */
    function repeticionConstruirUI(){
      var wrap = document.getElementById('grafico-contenedor');
      if (!wrap || repeticionEl.barra) return;
      var barra = document.createElement('div');
      barra.id = 'repeticion-barra'; barra.className = 'repeticion-oculto';
      barra.innerHTML =
        '<button id="repeticion-plegar" class="repeticion-btn repeticion-ico" type="button" title="Ocultar / mostrar la barra del replay">▴</button>' +
        '<span class="repeticion-tag">REPLAY</span>' +
        '<span id="repeticion-estado" class="repeticion-estado"></span>' +
        '<span id="repeticion-elegir" class="repeticion-grupo">' +
          '<label>Retroceder <input id="repeticion-cant" type="number" min="1" step="1" value="1"></label>' +
          '<select id="repeticion-unidad" title="Unidad de tiempo a retroceder">' +
            '<option value="vela">velas</option><option value="min">minutos</option><option value="hora">horas</option>' +
            '<option value="dia">días</option><option value="sem">semanas</option><option value="mes" selected>meses</option>' +
            '<option value="anio">años</option></select>' +
          '<button id="repeticion-empezar" class="repeticion-btn repeticion-prim" type="button">Empezar</button>' +
        '</span>' +
        '<span id="repeticion-ctrl" class="repeticion-grupo">' +
          '<button id="repeticion-play" class="repeticion-btn repeticion-ico" type="button" title="Reproducir / pausar (Espacio)">▶</button>' +
          '<button id="repeticion-paso" class="repeticion-btn repeticion-ico" type="button" title="Siguiente vela (→)">⏭</button>' +
          '<select id="repeticion-vel" title="Velocidad">' +
            '<option value="1500">0,5x</option><option value="1000" selected>1x</option><option value="500">2x</option>' +
            '<option value="200">5x</option><option value="100">10x</option></select>' +
          '<button id="repeticion-otro" class="repeticion-btn" type="button" title="Elegir otro punto de inicio (reinicia la práctica)">Otro punto</button>' +
        '</span>' +
        '<button id="repeticion-salir" class="repeticion-btn repeticion-sal" type="button" title="Volver al gráfico en vivo">Salir</button>';
      wrap.appendChild(barra);

      var panel = document.createElement('div');
      panel.id = 'repeticion-panel'; panel.className = 'repeticion-oculto';
      panel.innerHTML =
        '<div class="repeticion-ph" id="repeticion-ph" title="Plegar / desplegar">▾ Práctica (dinero de prueba)</div>' +
        '<div class="repeticion-fila"><span>Capital inicial</span><input id="repeticion-cap" type="number" min="100" step="100" value="10000"></div>' +
        '<div class="repeticion-fila"><span>Operar en</span><select id="repeticion-sim" title="Activo con el que se opera (el principal o uno de «Comparar»)"></select></div>' +
        '<div class="repeticion-fila"><span>Tamaño (% del capital)</span><input id="repeticion-tam" type="number" min="1" max="1000" step="10" value="100"></div>' +
        '<div class="repeticion-fila"><span>Stop loss (%)</span><input id="repeticion-sl" type="number" min="0" step="0.1" placeholder="sin SL"></div>' +
        '<div class="repeticion-fila"><span>Take profit (%)</span><input id="repeticion-tp" type="number" min="0" step="0.1" placeholder="sin TP"></div>' +
        '<div class="repeticion-ops">' +
          '<button id="repeticion-comprar" class="repeticion-btn repeticion-compra" type="button">COMPRAR</button>' +
          '<button id="repeticion-vender" class="repeticion-btn repeticion-venta" type="button">VENDER</button>' +
        '</div>' +
        '<button id="repeticion-cerrar" class="repeticion-btn repeticion-cierre" type="button">Cerrar posición</button>' +
        '<div id="repeticion-info" class="repeticion-info"></div>' +
        '<div id="repeticion-res" class="repeticion-res"></div>' +
        '<div id="repeticion-hist" class="repeticion-hist"></div>' +
        '<div class="repeticion-nota">Simulación: no envía órdenes ni usa tu cuenta de MetaTrader.</div>';
      wrap.appendChild(panel);

      ['barra', 'panel'].forEach(function(k){ repeticionEl[k] = k === 'barra' ? barra : panel; });
      ['estado', 'elegir', 'ctrl', 'plegar', 'cant', 'unidad', 'empezar', 'play', 'paso', 'vel', 'otro', 'salir', 'cap', 'sim', 'tam', 'sl', 'tp',
       'comprar', 'vender', 'cerrar', 'info', 'res', 'hist'].forEach(function(k){ repeticionEl[k] = document.getElementById('repeticion-' + k); });

      // Evita que los clics y arrastres sobre la interfaz lleguen al gráfico.
      [barra, panel].forEach(function(el){
        ['mousedown', 'click', 'dblclick', 'wheel', 'contextmenu'].forEach(function(ev){ el.addEventListener(ev, function(e){ e.stopPropagation(); }); });
      });
      document.getElementById('repeticion-ph').onclick = function(){
        var min = panel.classList.toggle('repeticion-min');
        this.textContent = (min ? '▸' : '▾') + ' Práctica (dinero de prueba)';
      };
      repeticionEl.empezar.onclick = repeticionEmpezarRetroceso;
      repeticionEl.cant.addEventListener('keydown', function(e){ if (e.key === 'Enter') repeticionEmpezarRetroceso(); });
      repeticionEl.plegar.onclick = function(){ repeticionPlegarBarra(!repeticionEl.barra.classList.contains('repeticion-min')); };
      repeticionRecordarRetroceso(false);
      repeticionPlegarBarra(repeticionLeerPref('barraMin') === '1');
      [repeticionEl.cant, repeticionEl.unidad].forEach(function(el){ el.addEventListener('change', function(){ repeticionRecordarRetroceso(true); }); });
      repeticionEl.play.onclick = repeticionAlternarReproduccion;
      repeticionEl.paso.onclick = function(){ repeticionPausar(); repeticionAvanzar(); };
      repeticionEl.vel.onchange = function(){ if (repeticionTemporizador) { repeticionPausar(); repeticionReproducir(); } };
      repeticionEl.otro.onclick = repeticionVolverAElegir;
      repeticionEl.salir.onclick = function(){ repeticionSalir(false); };
      repeticionEl.comprar.onclick = function(){ repeticionOperar(1); };
      repeticionEl.vender.onclick = function(){ repeticionOperar(-1); };
      repeticionEl.cerrar.onclick = repeticionCerrarManual;
      [repeticionEl.sl, repeticionEl.tp].forEach(function(inp){ inp.addEventListener('change', repeticionAplicarNiveles); });
      repeticionEl.sim.onchange = repeticionRefrescarPanel;
      // Botón ✕ de cada posición abierta de la lista: la cierra a mano.
      repeticionEl.info.addEventListener('click', function(e){
        var sym = e.target && e.target.getAttribute && e.target.getAttribute('data-cierra');
        if (sym) repeticionCerrarManual(sym);
      });
    }

    // TITULO RP ESTADO

    /** Escribe el mensaje de estado de la barra (por ejemplo, la instrucción del paso actual). */
    function repeticionEstado(txt){ if (repeticionEl.estado) repeticionEl.estado.textContent = txt; }

    // TITULO RP ACTUALIZAR FASE

    /**
     * Muestra u oculta los grupos de la barra según la fase: en 'elegir' aparece el selector de punto de inicio;
     * en 'listo', los controles de reproducción. También habilita o deshabilita el panel de práctica.
     */
    function repeticionActualizarFase(){
      if (!repeticionEl.barra) return;
      repeticionEl.elegir.style.display = repeticionFase === 'elegir' ? '' : 'none';
      repeticionEl.ctrl.style.display = repeticionFase === 'listo' ? '' : 'none';
      var op = repeticionFase === 'listo';
      [repeticionEl.comprar, repeticionEl.vender, repeticionEl.cerrar].forEach(function(b){ b.disabled = !op; });
      [repeticionEl.cap].forEach(function(i){ i.disabled = repeticionFase === 'listo' && (repeticionCuenta.trades.length > 0 || Object.keys(repeticionCuenta.pos).length > 0); });
      repeticionEl.play.textContent = repeticionTemporizador ? '⏸' : '▶';
    }

    // TITULO RP ENTRAR

    /**
     * Activa el modo replay: pide al servidor hasta 5000 velas de la temporalidad actual (si falla usa las que ya
     * hay cargadas), las muestra completas y pasa a la fase de elegir el punto de inicio (clic en el gráfico o
     * número de velas hacia atrás). Apaga las actualizaciones en vivo mientras dure.
     */
    function repeticionEntrar(){
      if (repeticionFase) return;
      repeticionConstruirUI();
      repeticionFase = 'cargando';
      repeticionActivo = true;
      document.getElementById('tradingview-contenedor').classList.add('repeticion-activo');
      repeticionEl.barra.classList.remove('repeticion-oculto'); repeticionEl.panel.classList.remove('repeticion-oculto');
      repeticionEstado('Cargando historial…'); repeticionActualizarFase(); repeticionRefrescarPanel();
      var temporalidadLlamada = temporalidadActual;
      repeticionHistorial(SIMBOLO, temporalidadLlamada)
        .then(function(v){ if (v.length < REPETICION_MINIMO_TOTAL) throw new Error('pocas velas'); return v.slice(); })
        .catch(function(){ return datosActuales.length >= REPETICION_MINIMO_TOTAL ? datosActuales.slice() : null; })
        .then(function(v){
          if (!repeticionActivo) return;
          if (!v){ repeticionEstado('No hay suficiente historial para usar el replay.'); setTimeout(function(){ repeticionSalir(false); }, 1800); return; }
          repeticionCompleto = v;
          repeticionMostrarTodo();
          repeticionFase = 'elegir';
          repeticionEstado('Haz clic en el gráfico o elige cuánto retroceder.');
          repeticionActualizarFase();
        });
    }

    // TITULO RP MOSTRAR TODO

    /** Muestra TODO el historial cargado (fase de elegir el punto de inicio) y ajusta la vista para verlo entero. */
    function repeticionMostrarTodo(){
      datosActuales = repeticionCompleto.slice();
      serie.setData(formatearDatos(datosActuales, tipoActual));
      serieVolumen.setData(datosActuales.map(aPuntoVolumen));
      chart.timeScale().fitContent();
      actualizarLeyenda(datosActuales[datosActuales.length - 1]);
      actualizarIndicadoresActivos();
      redibujarTodo();
      comparados.forEach(function(c){ if (c.completo) repeticionCortarComparado(c, Infinity); else repeticionCargarComparado(c); });   // los comparados también se ven enteros
    }

    // TITULO RP VOLVER AELEGIR

    /** Vuelve a la fase de elegir el punto de inicio: detiene la reproducción, descarta la práctica y muestra todo el historial. */
    function repeticionVolverAElegir(){
      repeticionPausar();
      repeticionCuenta = repeticionCuentaNueva(repeticionCuenta.capital0);
      repeticionPintarLineas();
      repeticionMostrarTodo();
      repeticionFase = 'elegir';
      repeticionEstado('Haz clic en el gráfico o elige cuánto retroceder.');
      repeticionActualizarFase(); repeticionRefrescarPanel();
    }

    var REPETICION_PREF_KEY = 'pj_replay_pref';
    var REPETICION_SEGUNDOS = { min: 60, hora: 3600, dia: 86400, sem: 604800, mes: 2592000, anio: 31536000 };   // mes = 30 días, año = 365 días

    // TITULO RP LEER PREF

    /** Lee una preferencia recordada del replay (o '' si no hay). Nunca falla aunque el almacenamiento no esté disponible. */
    function repeticionLeerPref(clave){
      try { var o = JSON.parse(localStorage.getItem(REPETICION_PREF_KEY) || '{}'); return o[clave] == null ? '' : String(o[clave]); } catch (e) { return ''; }
    }

    // TITULO RP GUARDAR PREF

    /** Guarda una preferencia del replay (por ejemplo, si la barra está plegada o el último retroceso usado). */
    function repeticionGuardarPref(clave, valor){
      try { var o = JSON.parse(localStorage.getItem(REPETICION_PREF_KEY) || '{}'); o[clave] = valor; localStorage.setItem(REPETICION_PREF_KEY, JSON.stringify(o)); } catch (e) {}
    }

    // TITULO RP RECORDAR RETROCESO

    /**
     * Restaura (guardar = false) o guarda (guardar = true) la cantidad y la unidad de retroceso elegidas, para que la
     * próxima vez el replay ofrezca lo último que se usó.
     */
    function repeticionRecordarRetroceso(guardar){
      if (guardar){ repeticionGuardarPref('cant', repeticionEl.cant.value); repeticionGuardarPref('unidad', repeticionEl.unidad.value); return; }
      var c = parseFloat(repeticionLeerPref('cant')), u = repeticionLeerPref('unidad');
      if (c > 0) repeticionEl.cant.value = c;
      if (u && repeticionEl.unidad.querySelector('option[value="' + u + '"]')) repeticionEl.unidad.value = u;
    }

    // TITULO RP PLEGAR BARRA

    /**
     * Pliega (true) o despliega (false) la barra de control: plegada, solo queda un pequeño botón pegado al borde
     * superior del gráfico para no tapar nada. Recuerda la elección para la próxima vez.
     */
    function repeticionPlegarBarra(plegar){
      repeticionEl.barra.classList.toggle('repeticion-min', plegar);
      repeticionEl.plegar.textContent = plegar ? '▾' : '▴';
      repeticionEl.plegar.title = plegar ? 'Mostrar la barra del replay' : 'Ocultar la barra del replay';
      repeticionGuardarPref('barraMin', plegar ? '1' : '0');
    }

    // TITULO RP INDICE RETROCESO

    /**
     * Calcula el índice de la vela donde empezar tras retroceder cantidad x unidad desde la última vela del historial.
     * Con unidad "vela" retrocede esa cantidad de velas; con una unidad de tiempo busca la última vela con hora menor o
     * igual a (última hora - tiempo pedido). Devuelve { idx, limitado }: limitado es true si el historial no alcanza y se
     * usó el punto más antiguo permitido.
     */
    function repeticionIndiceRetroceso(cantidad, unidad){
      var ult = repeticionCompleto.length - 1, idx;
      if (unidad === 'vela') idx = ult - Math.round(cantidad);
      else {
        var objetivo = repeticionCompleto[ult].time - cantidad * REPETICION_SEGUNDOS[unidad];
        var lo = 0, hi = ult; idx = -1;
        while (lo <= hi){ var mid = (lo + hi) >> 1; if (repeticionCompleto[mid].time <= objetivo){ idx = mid; lo = mid + 1; } else hi = mid - 1; }
      }
      return { idx: idx, limitado: idx < repeticionMinimoPrevias() };
    }

    // TITULO RP EMPEZAR RETROCESO

    /**
     * Empieza el replay retrocediendo la cantidad y la unidad de tiempo escritas en la barra (velas, minutos, horas,
     * días, semanas, meses o años). Si el historial cargado no alcanza, empieza en el punto más antiguo permitido y lo
     * avisa en el estado.
     */
    function repeticionEmpezarRetroceso(){
      var cant = parseFloat(repeticionEl.cant.value);
      if (!(cant > 0)){ repeticionEstado('Escribe una cantidad mayor que 0.'); return; }
      repeticionRecordarRetroceso(true);
      var r = repeticionIndiceRetroceso(cant, repeticionEl.unidad.value);
      repeticionComenzar(r.idx);
      if (r.limitado) repeticionEstado(repeticionEl.estado.textContent + ' · (el historial disponible no llega tan atrás)');
    }

    // TITULO RP COMENZAR

    /**
     * Corta el gráfico en la vela de índice idx (la ve el usuario como "hoy"), reinicia la cuenta de práctica con
     * el capital indicado y pasa a la fase 'listo'. Ajusta idx a los límites: al menos rpMinPrevias() velas
     * previas y al menos una vela por revelar.
     */
    function repeticionComenzar(idx){
      idx = Math.max(repeticionMinimoPrevias(), Math.min(repeticionCompleto.length - 2, Math.round(idx)));
      var cap = parseFloat(repeticionEl.cap.value);
      if (!(cap > 0)) { cap = 10000; repeticionEl.cap.value = cap; }
      repeticionCuenta = repeticionCuentaNueva(cap);
      repeticionIndice = idx;
      datosActuales = repeticionCompleto.slice(0, idx + 1);
      serie.setData(formatearDatos(datosActuales, tipoActual));
      serieVolumen.setData(datosActuales.map(aPuntoVolumen));
      var nv = datosActuales.length;
      chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, nv - 120), to: nv + 12 });
      actualizarLeyenda(datosActuales[nv - 1]);
      actualizarIndicadoresActivos();
      redibujarTodo();
      comparados.forEach(function(c){ if (c.completo) repeticionCortarComparado(c, datosActuales[nv - 1].time); });   // los comparados se recortan a la misma hora
      repeticionFase = 'listo';
      repeticionEstado('Desde ' + repeticionFecha(datosActuales[nv - 1].time) + ' · usa ▶ o ⏭ para avanzar');
      repeticionActualizarFase(); repeticionPintarLineas(); repeticionRefrescarPanel();
    }

    // TITULO RP AVANZAR

    /**
     * Revela la siguiente vela del historial: la agrega al gráfico y al volumen, actualiza la leyenda y los
     * indicadores, procesa la cuenta de práctica (stop loss / take profit) y refresca el panel. Si no quedan
     * velas, detiene la reproducción y avisa.
     */
    function repeticionAvanzar(){
      if (repeticionFase !== 'listo') return;
      if (repeticionIndice >= repeticionCompleto.length - 1){ repeticionPausar(); repeticionEstado('Fin de los datos disponibles.'); return; }
      repeticionIndice++;
      var b = repeticionCompleto[repeticionIndice];
      datosActuales.push(b);
      var f = formatearDatos(datosActuales, tipoActual);
      serie.update(f[f.length - 1]);
      serieVolumen.update(aPuntoVolumen(b));
      actualizarLeyenda(b);
      actualizarIndicadoresActivos();
      redibujarTodo();
      // Los comparados revelan las velas que ocurrieron hasta la hora de esta vela; cada una se procesa contra su posición.
      var cerradas = [];
      var cp = repeticionProcesarVela(repeticionCuenta, SIMBOLO, b, repeticionIndice);
      if (cp) cerradas.push(cp);
      comparados.forEach(function(c){
        repeticionAvanzarComparado(c, b.time).forEach(function(bc){
          var cc = repeticionProcesarVela(repeticionCuenta, c.sym, bc, repeticionIndice);
          if (cc) cerradas.push(cc);
        });
      });
      if (cerradas.length){
        var u = cerradas[cerradas.length - 1];
        repeticionEstado(u.sym + ': ' + (u.pnl >= 0 ? 'ganancia' : 'pérdida') + ' por ' + u.motivo.toLowerCase() + ' (' + repeticionFormato(u.pnl) + ')');
      } else repeticionEstado(repeticionFecha(b.time) + ' · vela ' + (repeticionIndice + 1) + ' de ' + repeticionCompleto.length);
      repeticionPintarLineas(); repeticionRefrescarPanel();
      if (repeticionIndice >= repeticionCompleto.length - 1){ repeticionPausar(); repeticionEstado('Fin de los datos disponibles.'); }
    }

    // TITULO RP REPRODUCIR

    /** Inicia la reproducción automática con la velocidad elegida (una vela por intervalo). */
    function repeticionReproducir(){
      if (repeticionFase !== 'listo' || repeticionTemporizador) return;
      repeticionTemporizador = setInterval(repeticionAvanzar, parseInt(repeticionEl.vel.value, 10) || 1000);
      repeticionActualizarFase();
    }

    // TITULO RP PAUSAR

    /** Detiene la reproducción automática. */
    function repeticionPausar(){
      if (repeticionTemporizador){ clearInterval(repeticionTemporizador); repeticionTemporizador = null; }
      repeticionActualizarFase();
    }

    // TITULO RP ALTERNAR REPRODUCCION

    /** Alterna entre reproducir y pausar (botón ▶/⏸ y tecla Espacio). */
    function repeticionAlternarReproduccion(){ if (repeticionTemporizador) repeticionPausar(); else repeticionReproducir(); }

    // TITULO RP SALIR

    /**
     * Sale del replay: detiene la reproducción, borra las líneas y oculta la interfaz. Si silencioso es falso,
     * recarga el gráfico en vivo; si es verdadero (porque otra acción ya va a recargar los datos) no lo hace.
     */
    function repeticionSalir(silencioso){
      if (!repeticionFase || repeticionSaliendo) return;
      repeticionSaliendo = true;
      repeticionPausar();
      repeticionFase = ''; repeticionActivo = false;
      repeticionCuenta = repeticionCuentaNueva(repeticionCuenta.capital0);
      repeticionPintarLineas();
      document.getElementById('tradingview-contenedor').classList.remove('repeticion-activo');
      if (repeticionEl.barra){ repeticionEl.barra.classList.add('repeticion-oculto'); repeticionEl.panel.classList.add('repeticion-oculto'); }
      repeticionCompleto = []; repeticionIndice = -1;
      comparados.forEach(function(c){ c.completo = null; c.ptr = 0; });   // se libera el historial largo de los comparados
      if (!silencioso) cargar(temporalidadActual, nBarrasActual, 'ultimas');
      repeticionSaliendo = false;
    }

    // TITULO RP AL CAMBIAR DATOS

    /** Gancho que llama cargar(): si hay un replay en curso y otra acción recarga los datos, sale del replay sin recargar. */
    function repeticionAlCambiarDatos(){ if (repeticionActivo && !repeticionSaliendo) repeticionSalir(true); }

    // TITULO RP TRAS CREAR SERIE

    /** Gancho que llama crearSerie(): al cambiar el tipo de gráfico se pierden las líneas de la serie anterior y se vuelven a pintar. */
    function repeticionTrasCrearSerie(){ repeticionLineas = { entrada: null, sl: null, tp: null }; if (repeticionActivo) repeticionPintarLineas(); }

    // TITULO RP PCT

    /** Lee un porcentaje opcional de un campo del panel (vacío o inválido = 0, es decir, sin nivel). */
    function repeticionPorcentaje(inp){ var v = parseFloat(inp.value); return v > 0 ? v : 0; }

    // TITULO RP OPERAR

    /** Abre una compra (dir = 1) o una venta (dir = -1) del símbolo elegido en el panel, con el tamaño, SL y TP del panel. */
    function repeticionOperar(dir){
      if (repeticionFase !== 'listo') return;
      var sym = repeticionEl.sim.value || SIMBOLO;
      var b = repeticionUltimaVela(sym);
      if (!b){ repeticionEstado('Todavía no hay velas de ' + sym + ' en este punto: avanza un poco.'); return; }
      if (repeticionCuenta.pos[sym]){ repeticionEstado('Ya hay una posición abierta en ' + sym + ': ciérrala primero.'); return; }
      if (!repeticionAbrir(repeticionCuenta, sym, dir, b, repeticionIndice, parseFloat(repeticionEl.tam.value), repeticionPorcentaje(repeticionEl.sl), repeticionPorcentaje(repeticionEl.tp), repeticionDecimales(sym, b.close))){
        repeticionEstado(repeticionCuenta.capital <= 0 ? 'Sin capital para operar.' : 'Revisa el tamaño de la operación.'); return;
      }
      var p = repeticionCuenta.pos[sym];
      repeticionEstado((dir > 0 ? 'Compra' : 'Venta') + ' de ' + sym + ' abierta a ' + repeticionFormato(p.fill, p.dec));
      repeticionActualizarFase(); repeticionPintarLineas(); repeticionRefrescarPanel();
    }

    // TITULO RP CERRAR MANUAL

    /** Cierra a mano la posición del símbolo indicado (por defecto, el elegido en el panel) al precio de su vela actual. */
    function repeticionCerrarManual(sym){
      sym = typeof sym === 'string' ? sym : (repeticionEl.sim.value || SIMBOLO);
      if (!repeticionCuenta.pos[sym]) return;
      var op = repeticionCerrarAMercado(repeticionCuenta, sym, repeticionUltimaVela(sym), repeticionIndice);
      if (op) repeticionEstado(sym + ': ' + (op.pnl >= 0 ? 'ganancia' : 'pérdida') + ' al cerrar (' + repeticionFormato(op.pnl) + ')');
      repeticionActualizarFase(); repeticionPintarLineas(); repeticionRefrescarPanel();
    }

    // TITULO RP APLICAR NIVELES

    /** Si el símbolo elegido tiene una posición abierta, aplica los nuevos valores de stop loss y take profit del panel. */
    function repeticionAplicarNiveles(){
      var sym = repeticionEl.sim.value || SIMBOLO;
      if (!repeticionCuenta.pos[sym]) return;
      repeticionCambiarNiveles(repeticionCuenta, sym, repeticionPorcentaje(repeticionEl.sl), repeticionPorcentaje(repeticionEl.tp));
      repeticionPintarLineas();
    }

    // TITULO RP PINTAR LINEAS

    /**
     * Dibuja en el gráfico las líneas de precio de la posición abierta del símbolo PRINCIPAL (entrada en azul, stop
     * loss en rojo, take profit en verde) y quita las anteriores. Las posiciones de símbolos comparados no llevan
     * líneas (el gráfico está en % mientras se compara) y se ven en el panel. Sin posición, no hay líneas.
     */
    function repeticionPintarLineas(){
      ['entrada', 'sl', 'tp'].forEach(function(k){
        if (repeticionLineas[k]){ try { serie.removePriceLine(repeticionLineas[k]); } catch (e) {} repeticionLineas[k] = null; }
      });
      var p = repeticionCuenta.pos[SIMBOLO];
      if (!p || !repeticionActivo) return;
      function linea(precio, color, titulo, estilo){
        return serie.createPriceLine({ price: precio, color: color, lineWidth: 1, lineStyle: estilo, axisLabelVisible: true, title: titulo });
      }
      repeticionLineas.entrada = linea(p.fill, '#58a6ff', (p.dir > 0 ? 'Compra' : 'Venta'), 0);
      if (p.sl !== null) repeticionLineas.sl = linea(p.sl, '#f85149', 'SL', 2);
      if (p.tp !== null) repeticionLineas.tp = linea(p.tp, '#3fb950', 'TP', 2);
    }

    // TITULO RP ACTUALIZAR SELECTOR

    /** Reconstruye el selector «Operar en» con el principal y los comparados, conservando la selección si sigue existiendo. */
    function repeticionActualizarSelector(){
      var sims = repeticionSimbolos(), actual = repeticionEl.sim.value;
      var firma = sims.join('|');
      if (repeticionEl.sim.getAttribute('data-firma') !== firma){
        repeticionEl.sim.innerHTML = sims.map(function(x){ return '<option value="' + x + '">' + x + '</option>'; }).join('');
        repeticionEl.sim.setAttribute('data-firma', firma);
        repeticionEl.sim.value = sims.indexOf(actual) >= 0 ? actual : SIMBOLO;
      }
    }

    // TITULO RP REFRESCAR PANEL

    /**
     * Refresca el panel: selector de símbolo, patrimonio, lista de posiciones abiertas (cada una con su resultado
     * no realizado y un botón ✕), resumen de operaciones y las últimas operaciones cerradas con su símbolo.
     */
    function repeticionRefrescarPanel(){
      if (!repeticionEl.panel) return;
      repeticionActualizarSelector();
      var ult = repeticionUltimas(), eq = repeticionEquity(repeticionCuenta, ult), syms = Object.keys(repeticionCuenta.pos);
      var filasPosicion = syms.map(function(s){
        var p = repeticionCuenta.pos[s], fl = repeticionFlotante(repeticionCuenta, s, ult[s]);
        return '<div class="repeticion-fila"><span>' + s + ' · ' + (p.dir > 0 ? 'C' : 'V') + ' @ ' + repeticionFormato(p.fill, p.dec) + '</span>' +
               '<b class="' + (fl >= 0 ? 'repeticion-pos' : 'repeticion-neg') + '">' + repeticionFormato(fl) + ' <button class="repeticion-x" type="button" data-cierra="' + s + '" title="Cerrar ' + s + '">✕</button></b></div>';
      }).join('');
      repeticionEl.info.innerHTML =
        '<div class="repeticion-fila"><span>Patrimonio</span><b>' + repeticionFormato(eq) + '</b></div>' +
        '<div class="repeticion-sub">Posiciones abiertas</div>' + (filasPosicion || '<div class="repeticion-fila"><span>Ninguna</span><b>—</b></div>');
      repeticionEl.cerrar.style.display = repeticionCuenta.pos[repeticionEl.sim.value] ? '' : 'none';
      var r = repeticionResumen(repeticionCuenta);
      repeticionEl.res.innerHTML =
        '<div class="repeticion-fila"><span>Operaciones</span><b>' + r.n + (r.n ? ' · ' + repeticionFormato(r.acierto, 0) + '% ganadoras' : '') + '</b></div>' +
        '<div class="repeticion-fila"><span>Resultado total</span><b class="' + (r.total >= 0 ? 'repeticion-pos' : 'repeticion-neg') + '">' + repeticionFormato(r.total) + ' (' + repeticionFormato(r.totalPct) + '%)</b></div>';
      var filas = repeticionCuenta.trades.slice(-6).reverse().map(function(t){
        return '<tr><td class="' + (t.dir > 0 ? 'repeticion-pos' : 'repeticion-neg') + '">' + (t.dir > 0 ? 'C' : 'V') + '</td><td class="repeticion-izq">' + t.sym + '</td><td>' + repeticionFormato(t.p0, t.dec) + '</td><td>' + repeticionFormato(t.p1, t.dec) +
               '</td><td class="' + (t.pnl >= 0 ? 'repeticion-pos' : 'repeticion-neg') + '">' + repeticionFormato(t.pnl) + '</td></tr>';
      }).join('');
      repeticionEl.hist.innerHTML = filas ? '<table><thead><tr><th></th><th class="repeticion-izq">Activo</th><th>Entrada</th><th>Salida</th><th>P/G</th></tr></thead><tbody>' + filas + '</tbody></table>' : '';
    }

    // Clic en el gráfico durante la fase de elegir: la vela pulsada pasa a ser el punto de inicio del replay.
    chart.subscribeClick(function(parametro){
      if (repeticionFase !== 'elegir' || !parametro || !parametro.time) return;
      var lo = 0, hi = repeticionCompleto.length - 1, idx = -1;
      while (lo <= hi){ var mid = (lo + hi) >> 1; if (repeticionCompleto[mid].time <= parametro.time){ idx = mid; lo = mid + 1; } else hi = mid - 1; }
      if (idx >= 0) repeticionComenzar(idx);
    });

    // Atajos de teclado en modo replay (fuera de campos de texto): Espacio = reproducir/pausar, flecha derecha = siguiente vela.
    document.addEventListener('keydown', function(e){
      if (!repeticionActivo || repeticionFase !== 'listo') return;
      var tag = (e.target && e.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
      if (e.key === ' '){ e.preventDefault(); repeticionAlternarReproduccion(); }
      else if (e.key === 'ArrowRight'){ e.preventDefault(); repeticionPausar(); repeticionAvanzar(); }
    });

    // Botón "Replay" de la barra superior: entra al modo replay o, si ya está activo, sale de él.
    (function(){
      var btn = document.getElementById('boton-repeticion-abrir');
      // Sin Replay en el plan: el botón lleva un candado y al pulsarlo sale el aviso con el acceso a Planes.
      if (btn && !PLAN.replay) { btn.classList.add('bloqueado-plan'); btn.style.opacity = '.65'; var cand = document.createElement('i'); cand.textContent = '\uD83D\uDD12'; cand.style.cssText = 'position:absolute;right:2px;bottom:1px;font-size:10px;font-style:normal;line-height:1;pointer-events:none;'; btn.style.position = 'relative'; btn.appendChild(cand); }
      if (btn) btn.addEventListener('click', function(e){ e.stopPropagation(); if (!PLAN.replay) { avisoPlan(PLAN.mensajes.replay); return; } if (repeticionFase) repeticionSalir(false); else repeticionEntrar(); });
      // Al acercar el ratón o enfocar el botón ya se va pidiendo el historial, para que al pulsar esté listo.
      if (btn){ btn.addEventListener('mouseenter', function(){ repeticionPrecargar(true); }); btn.addEventListener('focus', function(){ repeticionPrecargar(true); }); }
    })();

/* -------------------------------------------------------------------------------------------------------
   ----------------------------------- FIN Piña y Jara 63_replay_ui .JS ----------------------------------
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
