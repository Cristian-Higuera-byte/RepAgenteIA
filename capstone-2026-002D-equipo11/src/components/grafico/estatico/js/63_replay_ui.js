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

    var RP_MAX_VELAS = 5000;       // historial que se pide al servidor al entrar al replay
    var RP_MIN_PREVIAS = 30;       // velas mínimas que deben quedar a la vista antes del punto de inicio (menos si el activo tiene poco historial)
    var RP_MIN_TOTAL = 12;         // velas mínimas con las que se acepta usar el replay en un activo (activos nuevos o temporalidades largas)
    var RP_CACHE_MS = 120000;      // cuánto tiempo vale el historial precargado antes de volver a pedirlo
    var rpPrecarga = {};           // historial ya pedido: 'SÍMBOLO|TF' → { t: instante, p: promesa con las velas }
    var rpPrecTimer = null;        // espera antes de precargar, para no pedir en cada clic de temporalidad
    var rpCompleto = [];           // todas las velas disponibles (las que se irán revelando)
    var rpIdx = -1;                // posición en rpCompleto de la última vela visible
    var rpFase = '';               // '' (inactivo) | 'cargando' | 'elegir' | 'listo'
    var rpTimer = null;            // temporizador de la reproducción automática
    var rpSaliendo = false;        // evita que cargar() reinicie la salida mientras ya se está saliendo
    var rpCuenta = rpCuentaNueva(10000);
    var rpLineas = { entrada: null, sl: null, tp: null };   // líneas de precio de la posición abierta del símbolo principal
    var rpEl = {};                 // referencias a los elementos de la interfaz

    /** Formatea un número con separador de miles y los decimales indicados (por defecto 2). */
    function rpFmt(n, dec){
      return (typeof n === 'number' && isFinite(n)) ? n.toLocaleString('es-CL', { minimumFractionDigits: dec == null ? 2 : dec, maximumFractionDigits: dec == null ? 2 : dec }) : '—';
    }

    /** Convierte una marca de tiempo (segundos) en texto "AAAA-MM-DD HH:MM" (hora UTC, como el eje del gráfico). */
    function rpFecha(t){
      var d = new Date(t * 1000);
      function dos(n){ return (n < 10 ? '0' : '') + n; }
      return d.getUTCFullYear() + '-' + dos(d.getUTCMonth() + 1) + '-' + dos(d.getUTCDate()) + ' ' + dos(d.getUTCHours()) + ':' + dos(d.getUTCMinutes());
    }

    /**
     * Estima los decimales del precio de un símbolo. El principal usa los del gráfico (DIGITS); para los comparados
     * se deduce del nivel de precio (por ejemplo 5 decimales para ~1,1; 3 para ~150; 2 para precios de miles).
     */
    function rpDecimales(sym, precio){
      if (sym === SIMBOLO) return DIGITS;
      return precio >= 1000 ? 2 : (precio >= 10 ? 3 : 5);
    }

    /** Devuelve la lista de símbolos con los que se puede operar: el principal y los comparados sin error. */
    function rpSimbolos(){
      return [SIMBOLO].concat(comparados.filter(function(c){ return !c.error; }).map(function(c){ return c.sym; }));
    }

    /** Devuelve el objeto comparado de un símbolo (o null si es el principal o ya no está). */
    function rpComparadoDe(sym){
      for (var i = 0; i < comparados.length; i++) if (comparados[i].sym === sym) return comparados[i];
      return null;
    }

    /** Devuelve la última vela visible de un símbolo en este momento del replay (undefined si aún no tiene velas). */
    function rpUltimaVela(sym){
      if (sym === SIMBOLO) return datosActuales[datosActuales.length - 1];
      var c = rpComparadoDe(sym);
      return c && c.datos ? c.datos[c.datos.length - 1] : undefined;
    }

    /** Devuelve un objeto símbolo -> última vela visible, para todos los símbolos con posición abierta. */
    function rpUltimas(){
      var o = {};
      Object.keys(rpCuenta.pos).forEach(function(s){ o[s] = rpUltimaVela(s); });
      return o;
    }

    /**
     * Devuelve una promesa con el historial (hasta RP_MAX_VELAS velas) de un símbolo en una temporalidad. Si ya se pidió
     * hace menos de RP_CACHE_MS se reutiliza la misma petición (en curso o terminada), así que entrar al replay con el
     * historial precargado es instantáneo. Una petición fallida o vacía no se guarda, para que se pueda reintentar.
     */
    function rpHistorial(sym, tf){
      var k = sym + '|' + tf, h = rpPrecarga[k];
      if (h && Date.now() - h.t < RP_CACHE_MS) return h.p;
      var p = fetch(API + '/velas/' + encodeURIComponent(sym) + '?tf=' + tf + '&n=' + RP_MAX_VELAS)
        .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function(v){ if (!Array.isArray(v) || !v.length) throw new Error('sin datos'); return v; });
      rpPrecarga[k] = { t: Date.now(), p: p };
      p.catch(function(){ if (rpPrecarga[k] && rpPrecarga[k].p === p) delete rpPrecarga[k]; });
      return p;
    }

    /**
     * Pide por adelantado el historial del símbolo y la temporalidad actuales, sin esperar a que el usuario pulse
     * «Replay». inmediato = true lo hace al instante (por ejemplo al pasar el ratón por el botón); si no, espera un
     * momento para no pedir en cada clic de temporalidad. No hace nada mientras hay un replay en curso.
     */
    function rpPrecargar(inmediato){
      clearTimeout(rpPrecTimer);
      if (rpActivo) return;
      var lanzar = function(){ if (!rpActivo) rpHistorial(SIMBOLO, tfActual).catch(function(){}); };
      if (inmediato) lanzar(); else rpPrecTimer = setTimeout(lanzar, 900);
    }

    /** Velas mínimas previas al punto de inicio: RP_MIN_PREVIAS, o menos si el historial es corto (un tercio como máximo). */
    function rpMinPrevias(){ return Math.max(5, Math.min(RP_MIN_PREVIAS, Math.floor(rpCompleto.length / 3))); }

    /**
     * Carga el historial completo de un símbolo comparado (hasta 5000 velas de la temporalidad actual) y lo
     * recorta a la hora del replay: mientras se elige el punto de inicio se ve entero; después solo hasta la vela
     * principal actual. Lo llama el gancho de cargarComparado() cuando hay un replay activo.
     */
    function rpCargarComparado(c){
      var miId = ++c.req, tf = tfActual;
      rpHistorial(c.sym, tf)
        .then(function(v){
          if (miId !== c.req || comparados.indexOf(c) < 0 || !rpActivo) return;
          if (!Array.isArray(v) || !v.length){ c.error = 'sin datos'; c.completo = []; c.datos = []; c.serie.setData([]); }
          else { c.error = ''; c.completo = v; rpCortarComparado(c, rpFase === 'listo' ? datosActuales[datosActuales.length - 1].time : Infinity); }
          actualizarPctCmp(); redibujarTodo(); rpRefrescarPanel();
        })
        .catch(function(){ if (miId !== c.req || comparados.indexOf(c) < 0) return; c.error = 'sin conexión'; actualizarPctCmp(); rpRefrescarPanel(); });
    }

    /** Deja visibles en un comparado solo las velas con hora menor o igual a t (Infinity = todas) y reinicia su puntero. */
    function rpCortarComparado(c, t){
      var todas = c.completo || [];
      c.datos = todas.filter(function(b){ return b.time <= t; });
      c.ptr = c.datos.length;
      c.serie.setData(c.datos.map(function(p){ return { time: p.time, value: p.close }; }));
      actualizarPctCmp();
    }

    /**
     * Revela en un comparado las velas que ya ocurrieron hasta la hora t (la de la vela principal): las agrega a su
     * serie en el gráfico y devuelve la lista de velas reveladas (puede ser vacía) para procesar sus stops.
     */
    function rpAvanzarComparado(c, t){
      var nuevas = [], todas = c.completo || [];
      while (c.ptr < todas.length && todas[c.ptr].time <= t){
        var b = todas[c.ptr++];
        c.datos.push(b);
        c.serie.update({ time: b.time, value: b.close });
        nuevas.push(b);
      }
      if (nuevas.length) actualizarPctCmp();
      return nuevas;
    }

    /**
     * Gancho de quitarComparado(): si el símbolo que se quita tiene una posición abierta en la práctica, se cierra
     * al último precio visible (motivo "Cierre manual") para que no quede una posición sin datos que la gobiernen.
     */
    function rpAlQuitarComparado(c){
      if (!rpActivo || !rpCuenta.pos[c.sym]) return;
      var b = rpUltimaVela(c.sym);
      if (b) rpCerrarAMercado(rpCuenta, c.sym, b, rpIdx);
      else delete rpCuenta.pos[c.sym];
      rpPintarLineas(); rpRefrescarPanel();
      setTimeout(rpRefrescarPanel, 0);   // otra vez cuando el comparado ya salió de la lista, para actualizar el selector «Operar en»
    }

    /**
     * Construye una sola vez la interfaz del replay (barra de control y panel de práctica) dentro del
     * contenedor del gráfico, la deja oculta y conecta todos sus botones.
     */
    function rpConstruirUI(){
      var wrap = document.getElementById('chart-wrapper');
      if (!wrap || rpEl.barra) return;
      var barra = document.createElement('div');
      barra.id = 'rp-barra'; barra.className = 'rp-oculto';
      barra.innerHTML =
        '<button id="rp-plegar" class="rp-btn rp-ico" type="button" title="Ocultar / mostrar la barra del replay">▴</button>' +
        '<span class="rp-tag">REPLAY</span>' +
        '<span id="rp-estado" class="rp-estado"></span>' +
        '<span id="rp-elegir" class="rp-grupo">' +
          '<label>Retroceder <input id="rp-cant" type="number" min="1" step="1" value="1"></label>' +
          '<select id="rp-unidad" title="Unidad de tiempo a retroceder">' +
            '<option value="vela">velas</option><option value="min">minutos</option><option value="hora">horas</option>' +
            '<option value="dia">días</option><option value="sem">semanas</option><option value="mes" selected>meses</option>' +
            '<option value="anio">años</option></select>' +
          '<button id="rp-empezar" class="rp-btn rp-prim" type="button">Empezar</button>' +
        '</span>' +
        '<span id="rp-ctrl" class="rp-grupo">' +
          '<button id="rp-play" class="rp-btn rp-ico" type="button" title="Reproducir / pausar (Espacio)">▶</button>' +
          '<button id="rp-paso" class="rp-btn rp-ico" type="button" title="Siguiente vela (→)">⏭</button>' +
          '<select id="rp-vel" title="Velocidad">' +
            '<option value="1500">0,5x</option><option value="1000" selected>1x</option><option value="500">2x</option>' +
            '<option value="200">5x</option><option value="100">10x</option></select>' +
          '<button id="rp-otro" class="rp-btn" type="button" title="Elegir otro punto de inicio (reinicia la práctica)">Otro punto</button>' +
        '</span>' +
        '<button id="rp-salir" class="rp-btn rp-sal" type="button" title="Volver al gráfico en vivo">Salir</button>';
      wrap.appendChild(barra);

      var panel = document.createElement('div');
      panel.id = 'rp-panel'; panel.className = 'rp-oculto';
      panel.innerHTML =
        '<div class="rp-ph" id="rp-ph" title="Plegar / desplegar">▾ Práctica (dinero de prueba)</div>' +
        '<div class="rp-fila"><span>Capital inicial</span><input id="rp-cap" type="number" min="100" step="100" value="10000"></div>' +
        '<div class="rp-fila"><span>Operar en</span><select id="rp-sim" title="Activo con el que se opera (el principal o uno de «Comparar»)"></select></div>' +
        '<div class="rp-fila"><span>Tamaño (% del capital)</span><input id="rp-tam" type="number" min="1" max="1000" step="10" value="100"></div>' +
        '<div class="rp-fila"><span>Stop loss (%)</span><input id="rp-sl" type="number" min="0" step="0.1" placeholder="sin SL"></div>' +
        '<div class="rp-fila"><span>Take profit (%)</span><input id="rp-tp" type="number" min="0" step="0.1" placeholder="sin TP"></div>' +
        '<div class="rp-ops">' +
          '<button id="rp-comprar" class="rp-btn rp-compra" type="button">COMPRAR</button>' +
          '<button id="rp-vender" class="rp-btn rp-venta" type="button">VENDER</button>' +
        '</div>' +
        '<button id="rp-cerrar" class="rp-btn rp-cierre" type="button">Cerrar posición</button>' +
        '<div id="rp-info" class="rp-info"></div>' +
        '<div id="rp-res" class="rp-res"></div>' +
        '<div id="rp-hist" class="rp-hist"></div>' +
        '<div class="rp-nota">Simulación: no envía órdenes ni usa tu cuenta de MetaTrader.</div>';
      wrap.appendChild(panel);

      ['barra', 'panel'].forEach(function(k){ rpEl[k] = k === 'barra' ? barra : panel; });
      ['estado', 'elegir', 'ctrl', 'plegar', 'cant', 'unidad', 'empezar', 'play', 'paso', 'vel', 'otro', 'salir', 'cap', 'sim', 'tam', 'sl', 'tp',
       'comprar', 'vender', 'cerrar', 'info', 'res', 'hist'].forEach(function(k){ rpEl[k] = document.getElementById('rp-' + k); });

      // Evita que los clics y arrastres sobre la interfaz lleguen al gráfico.
      [barra, panel].forEach(function(el){
        ['mousedown', 'click', 'dblclick', 'wheel', 'contextmenu'].forEach(function(ev){ el.addEventListener(ev, function(e){ e.stopPropagation(); }); });
      });
      document.getElementById('rp-ph').onclick = function(){
        var min = panel.classList.toggle('rp-min');
        this.textContent = (min ? '▸' : '▾') + ' Práctica (dinero de prueba)';
      };
      rpEl.empezar.onclick = rpEmpezarRetroceso;
      rpEl.cant.addEventListener('keydown', function(e){ if (e.key === 'Enter') rpEmpezarRetroceso(); });
      rpEl.plegar.onclick = function(){ rpPlegarBarra(!rpEl.barra.classList.contains('rp-min')); };
      rpRecordarRetroceso(false);
      rpPlegarBarra(rpLeerPref('barraMin') === '1');
      [rpEl.cant, rpEl.unidad].forEach(function(el){ el.addEventListener('change', function(){ rpRecordarRetroceso(true); }); });
      rpEl.play.onclick = rpAlternarReproduccion;
      rpEl.paso.onclick = function(){ rpPausar(); rpAvanzar(); };
      rpEl.vel.onchange = function(){ if (rpTimer) { rpPausar(); rpReproducir(); } };
      rpEl.otro.onclick = rpVolverAElegir;
      rpEl.salir.onclick = function(){ rpSalir(false); };
      rpEl.comprar.onclick = function(){ rpOperar(1); };
      rpEl.vender.onclick = function(){ rpOperar(-1); };
      rpEl.cerrar.onclick = rpCerrarManual;
      [rpEl.sl, rpEl.tp].forEach(function(inp){ inp.addEventListener('change', rpAplicarNiveles); });
      rpEl.sim.onchange = rpRefrescarPanel;
      // Botón ✕ de cada posición abierta de la lista: la cierra a mano.
      rpEl.info.addEventListener('click', function(e){
        var sym = e.target && e.target.getAttribute && e.target.getAttribute('data-cierra');
        if (sym) rpCerrarManual(sym);
      });
    }

    /** Escribe el mensaje de estado de la barra (por ejemplo, la instrucción del paso actual). */
    function rpEstado(txt){ if (rpEl.estado) rpEl.estado.textContent = txt; }

    /**
     * Muestra u oculta los grupos de la barra según la fase: en 'elegir' aparece el selector de punto de inicio;
     * en 'listo', los controles de reproducción. También habilita o deshabilita el panel de práctica.
     */
    function rpActualizarFase(){
      if (!rpEl.barra) return;
      rpEl.elegir.style.display = rpFase === 'elegir' ? '' : 'none';
      rpEl.ctrl.style.display = rpFase === 'listo' ? '' : 'none';
      var op = rpFase === 'listo';
      [rpEl.comprar, rpEl.vender, rpEl.cerrar].forEach(function(b){ b.disabled = !op; });
      [rpEl.cap].forEach(function(i){ i.disabled = rpFase === 'listo' && (rpCuenta.trades.length > 0 || Object.keys(rpCuenta.pos).length > 0); });
      rpEl.play.textContent = rpTimer ? '⏸' : '▶';
    }

    /**
     * Activa el modo replay: pide al servidor hasta 5000 velas de la temporalidad actual (si falla usa las que ya
     * hay cargadas), las muestra completas y pasa a la fase de elegir el punto de inicio (clic en el gráfico o
     * número de velas hacia atrás). Apaga las actualizaciones en vivo mientras dure.
     */
    function rpEntrar(){
      if (rpFase) return;
      rpConstruirUI();
      rpFase = 'cargando';
      rpActivo = true;
      document.getElementById('tv-wrap').classList.add('rp-activo');
      rpEl.barra.classList.remove('rp-oculto'); rpEl.panel.classList.remove('rp-oculto');
      rpEstado('Cargando historial…'); rpActualizarFase(); rpRefrescarPanel();
      var tfLlamada = tfActual;
      rpHistorial(SIMBOLO, tfLlamada)
        .then(function(v){ if (v.length < RP_MIN_TOTAL) throw new Error('pocas velas'); return v.slice(); })
        .catch(function(){ return datosActuales.length >= RP_MIN_TOTAL ? datosActuales.slice() : null; })
        .then(function(v){
          if (!rpActivo) return;
          if (!v){ rpEstado('No hay suficiente historial para usar el replay.'); setTimeout(function(){ rpSalir(false); }, 1800); return; }
          rpCompleto = v;
          rpMostrarTodo();
          rpFase = 'elegir';
          rpEstado('Haz clic en el gráfico o elige cuánto retroceder.');
          rpActualizarFase();
        });
    }

    /** Muestra TODO el historial cargado (fase de elegir el punto de inicio) y ajusta la vista para verlo entero. */
    function rpMostrarTodo(){
      datosActuales = rpCompleto.slice();
      serie.setData(formatearDatos(datosActuales, tipoActual));
      serieVolumen.setData(datosActuales.map(aPuntoVolumen));
      chart.timeScale().fitContent();
      actualizarLeyenda(datosActuales[datosActuales.length - 1]);
      actualizarIndicadoresActivos();
      redibujarTodo();
      comparados.forEach(function(c){ if (c.completo) rpCortarComparado(c, Infinity); else rpCargarComparado(c); });   // los comparados también se ven enteros
    }

    /** Vuelve a la fase de elegir el punto de inicio: detiene la reproducción, descarta la práctica y muestra todo el historial. */
    function rpVolverAElegir(){
      rpPausar();
      rpCuenta = rpCuentaNueva(rpCuenta.capital0);
      rpPintarLineas();
      rpMostrarTodo();
      rpFase = 'elegir';
      rpEstado('Haz clic en el gráfico o elige cuánto retroceder.');
      rpActualizarFase(); rpRefrescarPanel();
    }

    var RP_PREF_KEY = 'pj_replay_pref';
    var RP_SEGUNDOS = { min: 60, hora: 3600, dia: 86400, sem: 604800, mes: 2592000, anio: 31536000 };   // mes = 30 días, año = 365 días

    /** Lee una preferencia recordada del replay (o '' si no hay). Nunca falla aunque el almacenamiento no esté disponible. */
    function rpLeerPref(clave){
      try { var o = JSON.parse(localStorage.getItem(RP_PREF_KEY) || '{}'); return o[clave] == null ? '' : String(o[clave]); } catch (e) { return ''; }
    }

    /** Guarda una preferencia del replay (por ejemplo, si la barra está plegada o el último retroceso usado). */
    function rpGuardarPref(clave, valor){
      try { var o = JSON.parse(localStorage.getItem(RP_PREF_KEY) || '{}'); o[clave] = valor; localStorage.setItem(RP_PREF_KEY, JSON.stringify(o)); } catch (e) {}
    }

    /**
     * Restaura (guardar = false) o guarda (guardar = true) la cantidad y la unidad de retroceso elegidas, para que la
     * próxima vez el replay ofrezca lo último que se usó.
     */
    function rpRecordarRetroceso(guardar){
      if (guardar){ rpGuardarPref('cant', rpEl.cant.value); rpGuardarPref('unidad', rpEl.unidad.value); return; }
      var c = parseFloat(rpLeerPref('cant')), u = rpLeerPref('unidad');
      if (c > 0) rpEl.cant.value = c;
      if (u && rpEl.unidad.querySelector('option[value="' + u + '"]')) rpEl.unidad.value = u;
    }

    /**
     * Pliega (true) o despliega (false) la barra de control: plegada, solo queda un pequeño botón pegado al borde
     * superior del gráfico para no tapar nada. Recuerda la elección para la próxima vez.
     */
    function rpPlegarBarra(plegar){
      rpEl.barra.classList.toggle('rp-min', plegar);
      rpEl.plegar.textContent = plegar ? '▾' : '▴';
      rpEl.plegar.title = plegar ? 'Mostrar la barra del replay' : 'Ocultar la barra del replay';
      rpGuardarPref('barraMin', plegar ? '1' : '0');
    }

    /**
     * Calcula el índice de la vela donde empezar tras retroceder cantidad x unidad desde la última vela del historial.
     * Con unidad "vela" retrocede esa cantidad de velas; con una unidad de tiempo busca la última vela con hora menor o
     * igual a (última hora - tiempo pedido). Devuelve { idx, limitado }: limitado es true si el historial no alcanza y se
     * usó el punto más antiguo permitido.
     */
    function rpIndiceRetroceso(cantidad, unidad){
      var ult = rpCompleto.length - 1, idx;
      if (unidad === 'vela') idx = ult - Math.round(cantidad);
      else {
        var objetivo = rpCompleto[ult].time - cantidad * RP_SEGUNDOS[unidad];
        var lo = 0, hi = ult; idx = -1;
        while (lo <= hi){ var mid = (lo + hi) >> 1; if (rpCompleto[mid].time <= objetivo){ idx = mid; lo = mid + 1; } else hi = mid - 1; }
      }
      return { idx: idx, limitado: idx < rpMinPrevias() };
    }

    /**
     * Empieza el replay retrocediendo la cantidad y la unidad de tiempo escritas en la barra (velas, minutos, horas,
     * días, semanas, meses o años). Si el historial cargado no alcanza, empieza en el punto más antiguo permitido y lo
     * avisa en el estado.
     */
    function rpEmpezarRetroceso(){
      var cant = parseFloat(rpEl.cant.value);
      if (!(cant > 0)){ rpEstado('Escribe una cantidad mayor que 0.'); return; }
      rpRecordarRetroceso(true);
      var r = rpIndiceRetroceso(cant, rpEl.unidad.value);
      rpComenzar(r.idx);
      if (r.limitado) rpEstado(rpEl.estado.textContent + ' · (el historial disponible no llega tan atrás)');
    }

    /**
     * Corta el gráfico en la vela de índice idx (la ve el usuario como "hoy"), reinicia la cuenta de práctica con
     * el capital indicado y pasa a la fase 'listo'. Ajusta idx a los límites: al menos rpMinPrevias() velas
     * previas y al menos una vela por revelar.
     */
    function rpComenzar(idx){
      idx = Math.max(rpMinPrevias(), Math.min(rpCompleto.length - 2, Math.round(idx)));
      var cap = parseFloat(rpEl.cap.value);
      if (!(cap > 0)) { cap = 10000; rpEl.cap.value = cap; }
      rpCuenta = rpCuentaNueva(cap);
      rpIdx = idx;
      datosActuales = rpCompleto.slice(0, idx + 1);
      serie.setData(formatearDatos(datosActuales, tipoActual));
      serieVolumen.setData(datosActuales.map(aPuntoVolumen));
      var nv = datosActuales.length;
      chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, nv - 120), to: nv + 12 });
      actualizarLeyenda(datosActuales[nv - 1]);
      actualizarIndicadoresActivos();
      redibujarTodo();
      comparados.forEach(function(c){ if (c.completo) rpCortarComparado(c, datosActuales[nv - 1].time); });   // los comparados se recortan a la misma hora
      rpFase = 'listo';
      rpEstado('Desde ' + rpFecha(datosActuales[nv - 1].time) + ' · usa ▶ o ⏭ para avanzar');
      rpActualizarFase(); rpPintarLineas(); rpRefrescarPanel();
    }

    /**
     * Revela la siguiente vela del historial: la agrega al gráfico y al volumen, actualiza la leyenda y los
     * indicadores, procesa la cuenta de práctica (stop loss / take profit) y refresca el panel. Si no quedan
     * velas, detiene la reproducción y avisa.
     */
    function rpAvanzar(){
      if (rpFase !== 'listo') return;
      if (rpIdx >= rpCompleto.length - 1){ rpPausar(); rpEstado('Fin de los datos disponibles.'); return; }
      rpIdx++;
      var b = rpCompleto[rpIdx];
      datosActuales.push(b);
      var f = formatearDatos(datosActuales, tipoActual);
      serie.update(f[f.length - 1]);
      serieVolumen.update(aPuntoVolumen(b));
      actualizarLeyenda(b);
      actualizarIndicadoresActivos();
      redibujarTodo();
      // Los comparados revelan las velas que ocurrieron hasta la hora de esta vela; cada una se procesa contra su posición.
      var cerradas = [];
      var cp = rpProcesarVela(rpCuenta, SIMBOLO, b, rpIdx);
      if (cp) cerradas.push(cp);
      comparados.forEach(function(c){
        rpAvanzarComparado(c, b.time).forEach(function(bc){
          var cc = rpProcesarVela(rpCuenta, c.sym, bc, rpIdx);
          if (cc) cerradas.push(cc);
        });
      });
      if (cerradas.length){
        var u = cerradas[cerradas.length - 1];
        rpEstado(u.sym + ': ' + (u.pnl >= 0 ? 'ganancia' : 'pérdida') + ' por ' + u.motivo.toLowerCase() + ' (' + rpFmt(u.pnl) + ')');
      } else rpEstado(rpFecha(b.time) + ' · vela ' + (rpIdx + 1) + ' de ' + rpCompleto.length);
      rpPintarLineas(); rpRefrescarPanel();
      if (rpIdx >= rpCompleto.length - 1){ rpPausar(); rpEstado('Fin de los datos disponibles.'); }
    }

    /** Inicia la reproducción automática con la velocidad elegida (una vela por intervalo). */
    function rpReproducir(){
      if (rpFase !== 'listo' || rpTimer) return;
      rpTimer = setInterval(rpAvanzar, parseInt(rpEl.vel.value, 10) || 1000);
      rpActualizarFase();
    }

    /** Detiene la reproducción automática. */
    function rpPausar(){
      if (rpTimer){ clearInterval(rpTimer); rpTimer = null; }
      rpActualizarFase();
    }

    /** Alterna entre reproducir y pausar (botón ▶/⏸ y tecla Espacio). */
    function rpAlternarReproduccion(){ if (rpTimer) rpPausar(); else rpReproducir(); }

    /**
     * Sale del replay: detiene la reproducción, borra las líneas y oculta la interfaz. Si silencioso es falso,
     * recarga el gráfico en vivo; si es verdadero (porque otra acción ya va a recargar los datos) no lo hace.
     */
    function rpSalir(silencioso){
      if (!rpFase || rpSaliendo) return;
      rpSaliendo = true;
      rpPausar();
      rpFase = ''; rpActivo = false;
      rpCuenta = rpCuentaNueva(rpCuenta.capital0);
      rpPintarLineas();
      document.getElementById('tv-wrap').classList.remove('rp-activo');
      if (rpEl.barra){ rpEl.barra.classList.add('rp-oculto'); rpEl.panel.classList.add('rp-oculto'); }
      rpCompleto = []; rpIdx = -1;
      comparados.forEach(function(c){ c.completo = null; c.ptr = 0; });   // se libera el historial largo de los comparados
      if (!silencioso) cargar(tfActual, nBarrasActual, 'ultimas');
      rpSaliendo = false;
    }

    /** Gancho que llama cargar(): si hay un replay en curso y otra acción recarga los datos, sale del replay sin recargar. */
    function rpAlCambiarDatos(){ if (rpActivo && !rpSaliendo) rpSalir(true); }

    /** Gancho que llama crearSerie(): al cambiar el tipo de gráfico se pierden las líneas de la serie anterior y se vuelven a pintar. */
    function rpTrasCrearSerie(){ rpLineas = { entrada: null, sl: null, tp: null }; if (rpActivo) rpPintarLineas(); }

    /** Lee un porcentaje opcional de un campo del panel (vacío o inválido = 0, es decir, sin nivel). */
    function rpPct(inp){ var v = parseFloat(inp.value); return v > 0 ? v : 0; }

    /** Abre una compra (dir = 1) o una venta (dir = -1) del símbolo elegido en el panel, con el tamaño, SL y TP del panel. */
    function rpOperar(dir){
      if (rpFase !== 'listo') return;
      var sym = rpEl.sim.value || SIMBOLO;
      var b = rpUltimaVela(sym);
      if (!b){ rpEstado('Todavía no hay velas de ' + sym + ' en este punto: avanza un poco.'); return; }
      if (rpCuenta.pos[sym]){ rpEstado('Ya hay una posición abierta en ' + sym + ': ciérrala primero.'); return; }
      if (!rpAbrir(rpCuenta, sym, dir, b, rpIdx, parseFloat(rpEl.tam.value), rpPct(rpEl.sl), rpPct(rpEl.tp), rpDecimales(sym, b.close))){
        rpEstado(rpCuenta.capital <= 0 ? 'Sin capital para operar.' : 'Revisa el tamaño de la operación.'); return;
      }
      var p = rpCuenta.pos[sym];
      rpEstado((dir > 0 ? 'Compra' : 'Venta') + ' de ' + sym + ' abierta a ' + rpFmt(p.fill, p.dec));
      rpActualizarFase(); rpPintarLineas(); rpRefrescarPanel();
    }

    /** Cierra a mano la posición del símbolo indicado (por defecto, el elegido en el panel) al precio de su vela actual. */
    function rpCerrarManual(sym){
      sym = typeof sym === 'string' ? sym : (rpEl.sim.value || SIMBOLO);
      if (!rpCuenta.pos[sym]) return;
      var op = rpCerrarAMercado(rpCuenta, sym, rpUltimaVela(sym), rpIdx);
      if (op) rpEstado(sym + ': ' + (op.pnl >= 0 ? 'ganancia' : 'pérdida') + ' al cerrar (' + rpFmt(op.pnl) + ')');
      rpActualizarFase(); rpPintarLineas(); rpRefrescarPanel();
    }

    /** Si el símbolo elegido tiene una posición abierta, aplica los nuevos valores de stop loss y take profit del panel. */
    function rpAplicarNiveles(){
      var sym = rpEl.sim.value || SIMBOLO;
      if (!rpCuenta.pos[sym]) return;
      rpCambiarNiveles(rpCuenta, sym, rpPct(rpEl.sl), rpPct(rpEl.tp));
      rpPintarLineas();
    }

    /**
     * Dibuja en el gráfico las líneas de precio de la posición abierta del símbolo PRINCIPAL (entrada en azul, stop
     * loss en rojo, take profit en verde) y quita las anteriores. Las posiciones de símbolos comparados no llevan
     * líneas (el gráfico está en % mientras se compara) y se ven en el panel. Sin posición, no hay líneas.
     */
    function rpPintarLineas(){
      ['entrada', 'sl', 'tp'].forEach(function(k){
        if (rpLineas[k]){ try { serie.removePriceLine(rpLineas[k]); } catch (e) {} rpLineas[k] = null; }
      });
      var p = rpCuenta.pos[SIMBOLO];
      if (!p || !rpActivo) return;
      function linea(precio, color, titulo, estilo){
        return serie.createPriceLine({ price: precio, color: color, lineWidth: 1, lineStyle: estilo, axisLabelVisible: true, title: titulo });
      }
      rpLineas.entrada = linea(p.fill, '#58a6ff', (p.dir > 0 ? 'Compra' : 'Venta'), 0);
      if (p.sl !== null) rpLineas.sl = linea(p.sl, '#f85149', 'SL', 2);
      if (p.tp !== null) rpLineas.tp = linea(p.tp, '#3fb950', 'TP', 2);
    }

    /** Reconstruye el selector «Operar en» con el principal y los comparados, conservando la selección si sigue existiendo. */
    function rpActualizarSelector(){
      var sims = rpSimbolos(), actual = rpEl.sim.value;
      var firma = sims.join('|');
      if (rpEl.sim.getAttribute('data-firma') !== firma){
        rpEl.sim.innerHTML = sims.map(function(x){ return '<option value="' + x + '">' + x + '</option>'; }).join('');
        rpEl.sim.setAttribute('data-firma', firma);
        rpEl.sim.value = sims.indexOf(actual) >= 0 ? actual : SIMBOLO;
      }
    }

    /**
     * Refresca el panel: selector de símbolo, patrimonio, lista de posiciones abiertas (cada una con su resultado
     * no realizado y un botón ✕), resumen de operaciones y las últimas operaciones cerradas con su símbolo.
     */
    function rpRefrescarPanel(){
      if (!rpEl.panel) return;
      rpActualizarSelector();
      var ult = rpUltimas(), eq = rpEquity(rpCuenta, ult), syms = Object.keys(rpCuenta.pos);
      var filasPos = syms.map(function(s){
        var p = rpCuenta.pos[s], fl = rpFlotante(rpCuenta, s, ult[s]);
        return '<div class="rp-fila"><span>' + s + ' · ' + (p.dir > 0 ? 'C' : 'V') + ' @ ' + rpFmt(p.fill, p.dec) + '</span>' +
               '<b class="' + (fl >= 0 ? 'rp-pos' : 'rp-neg') + '">' + rpFmt(fl) + ' <button class="rp-x" type="button" data-cierra="' + s + '" title="Cerrar ' + s + '">✕</button></b></div>';
      }).join('');
      rpEl.info.innerHTML =
        '<div class="rp-fila"><span>Patrimonio</span><b>' + rpFmt(eq) + '</b></div>' +
        '<div class="rp-sub">Posiciones abiertas</div>' + (filasPos || '<div class="rp-fila"><span>Ninguna</span><b>—</b></div>');
      rpEl.cerrar.style.display = rpCuenta.pos[rpEl.sim.value] ? '' : 'none';
      var r = rpResumen(rpCuenta);
      rpEl.res.innerHTML =
        '<div class="rp-fila"><span>Operaciones</span><b>' + r.n + (r.n ? ' · ' + rpFmt(r.acierto, 0) + '% ganadoras' : '') + '</b></div>' +
        '<div class="rp-fila"><span>Resultado total</span><b class="' + (r.total >= 0 ? 'rp-pos' : 'rp-neg') + '">' + rpFmt(r.total) + ' (' + rpFmt(r.totalPct) + '%)</b></div>';
      var filas = rpCuenta.trades.slice(-6).reverse().map(function(t){
        return '<tr><td class="' + (t.dir > 0 ? 'rp-pos' : 'rp-neg') + '">' + (t.dir > 0 ? 'C' : 'V') + '</td><td class="rp-izq">' + t.sym + '</td><td>' + rpFmt(t.p0, t.dec) + '</td><td>' + rpFmt(t.p1, t.dec) +
               '</td><td class="' + (t.pnl >= 0 ? 'rp-pos' : 'rp-neg') + '">' + rpFmt(t.pnl) + '</td></tr>';
      }).join('');
      rpEl.hist.innerHTML = filas ? '<table><thead><tr><th></th><th class="rp-izq">Activo</th><th>Entrada</th><th>Salida</th><th>P/G</th></tr></thead><tbody>' + filas + '</tbody></table>' : '';
    }

    // Clic en el gráfico durante la fase de elegir: la vela pulsada pasa a ser el punto de inicio del replay.
    chart.subscribeClick(function(param){
      if (rpFase !== 'elegir' || !param || !param.time) return;
      var lo = 0, hi = rpCompleto.length - 1, idx = -1;
      while (lo <= hi){ var mid = (lo + hi) >> 1; if (rpCompleto[mid].time <= param.time){ idx = mid; lo = mid + 1; } else hi = mid - 1; }
      if (idx >= 0) rpComenzar(idx);
    });

    // Atajos de teclado en modo replay (fuera de campos de texto): Espacio = reproducir/pausar, flecha derecha = siguiente vela.
    document.addEventListener('keydown', function(e){
      if (!rpActivo || rpFase !== 'listo') return;
      var tag = (e.target && e.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
      if (e.key === ' '){ e.preventDefault(); rpAlternarReproduccion(); }
      else if (e.key === 'ArrowRight'){ e.preventDefault(); rpPausar(); rpAvanzar(); }
    });

    // Botón "Replay" de la barra superior: entra al modo replay o, si ya está activo, sale de él.
    (function(){
      var btn = document.getElementById('btn-rp-open');
      if (btn) btn.addEventListener('click', function(e){ e.stopPropagation(); if (rpFase) rpSalir(false); else rpEntrar(); });
      // Al acercar el ratón o enfocar el botón ya se va pidiendo el historial, para que al pulsar esté listo.
      if (btn){ btn.addEventListener('mouseenter', function(){ rpPrecargar(true); }); btn.addEventListener('focus', function(){ rpPrecargar(true); }); }
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
