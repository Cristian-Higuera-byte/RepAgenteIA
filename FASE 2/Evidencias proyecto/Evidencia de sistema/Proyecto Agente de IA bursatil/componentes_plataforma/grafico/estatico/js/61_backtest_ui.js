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
   -------------------------------- INICIO Piña y Jara 61_backtest_ui .JS --------------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Backtest: ventana (formulario de estrategia, resultados, curva de capital y marcas en el gráfico)
    // BT_KEY: clave de localStorage; las variables siguientes son los elementos de la ventana y el estado del backtest
    var BACKTEST_KEY = 'pj_backtest_cfg';
    var backtestSuperposicion = document.getElementById('backtest-superposicion');
    var backtestFormulario = document.getElementById('backtest-formulario');
    var backtestResultado = document.getElementById('backtest-resultado');
    // marcasBT: marcas de las operaciones sobre el gráfico principal
    var marcasBacktest = null;          // marcas de las operaciones sobre el gráfico principal
    // btUltimo: último resultado { r, datos, est, cost }
    var backtestUltimo = null;          // último resultado { r, datos, est, cost }
    // btCharts: gráficos de la curva de capital
    var backtestCharts = null;          // gráficos de la curva de capital
    // btPestana: pestaña de resultados visible
    var backtestPestana = 'resumen';

    // TITULO BT OP IND

    // ---------- Estrategia por defecto: el ejemplo EMA 20/50 + RSI > 50, SL 2 %, TP 4 % ----------
    /** Crea un operando de condición que apunta a la capa capa (0 por defecto) del indicador id con parámetros p. */
    function backtestOperacionIndicador(id, p, capa){ return { k: 'ind', id: id, capa: capa || 0, p: p || {} }; }
    // TITULO BT OP NUM

    /** Crea un operando de condición con un número fijo v. */
    function backtestOperacionNumero(v){ return { k: 'num', v: v }; }
    // TITULO BT OP PRECIO

    /** Crea un operando de condición que usa el precio f (close, open, high, low, hl2, hlc3 o volume). */
    function backtestOperacionPrecio(f){ return { k: 'precio', f: f }; }
    // TITULO BT EJEMPLO

    /**
     * Devuelve la estrategia de ejemplo: compra con cruce de EMA 20/50 y RSI > 50, venta con lo contrario, SL 2 % y
     * TP 4 %.
     */
    function backtestEjemplo(){
      return {
        dir: 'largo', sl: 2, tp: 4, trail: 0, maxBarras: 0, invertir: false,
        tam: { modo: 'nominal', valor: 100, apalMax: 5 },
        largo: { entrada: { logica: 'y', cond: [
                  { a: backtestOperacionIndicador('ema', { periodo: 20 }), op: 'cruzaArriba', b: backtestOperacionIndicador('ema', { periodo: 50 }) },
                  { a: backtestOperacionIndicador('rsi', { periodo: 14 }), op: 'gt', b: backtestOperacionNumero(50) }] },
                 salida: { logica: 'o', cond: [] } },
        corto: { entrada: { logica: 'y', cond: [
                  { a: backtestOperacionIndicador('ema', { periodo: 20 }), op: 'cruzaAbajo', b: backtestOperacionIndicador('ema', { periodo: 50 }) },
                  { a: backtestOperacionIndicador('rsi', { periodo: 14 }), op: 'lt', b: backtestOperacionNumero(50) }] },
                 salida: { logica: 'o', cond: [] } }
      };
    }
    // TITULO BT CFG POR DEFECTO

    /**
     * Devuelve la configuración completa del backtest por defecto: estrategia de ejemplo, costes, capital de 10.000 y
     * 5.000 velas.
     */
    function backtestConfiguracionPorDefecto(){
      return { est: backtestEjemplo(), cost: { spreadModo: 'mt5', spreadPips: 1.5, slipPips: 0.5, comision: 0.003 }, capital: 10000, n: 5000 };
    }
    // btCfg: configuración actual del backtest (estrategia, costes, capital y número de velas)
    var backtestConfiguracion = backtestConfiguracionPorDefecto();
    /**
     * Lee de localStorage la configuración del backtest recordada y la fusiona con la de defecto, corrigiendo bloques
     * mal formados; si falla vuelve a los valores por defecto.
     */
    (function backtestLeer(){
      try {
        var c = JSON.parse(localStorage.getItem(BACKTEST_KEY) || 'null');
        if (!c || !c.est || !c.est.largo || !c.est.corto || !c.est.tam || !c.cost) return;
        var d = backtestConfiguracionPorDefecto();
        backtestConfiguracion = { est: Object.assign(d.est, c.est), cost: Object.assign(d.cost, c.cost), capital: Number(c.capital) > 0 ? Number(c.capital) : d.capital, n: Number(c.n) > 0 ? Math.min(Number(c.n), 20000, PLAN.backtest_velas || 20000) : d.n };
        ['largo', 'corto'].forEach(function(l){
          ['entrada', 'salida'].forEach(function(s){
            var b = backtestConfiguracion.est[l][s];
            if (!b || !Array.isArray(b.cond)) backtestConfiguracion.est[l][s] = { logica: s === 'entrada' ? 'y' : 'o', cond: [] };
          });
        });
      } catch (e) { backtestConfiguracion = backtestConfiguracionPorDefecto(); }
    })();
    // TITULO BT GUARDAR

    /** Guarda la configuración actual del backtest en localStorage. */
    function backtestGuardar(){ try { localStorage.setItem(BACKTEST_KEY, JSON.stringify(backtestConfiguracion)); } catch (e) {} }

    // TITULO FMT PCT

    // ---------- Utilidades ----------
    /**
     * Formatea una fracción x como porcentaje con signo y d decimales (2 por defecto); devuelve un guion largo si no
     * es un número.
     */
    function formatoPorcentaje(x, d){ return (x === null || x === undefined || !isFinite(x)) ? '—' : (x >= 0 ? '+' : '') + (x * 100).toFixed(d === undefined ? 2 : d) + '%'; }
    // TITULO FMT NUM

    /** Formatea un número con d decimales (2 por defecto); muestra ∞ para infinito y un guion largo si es nulo. */
    function formatoNumero(x, d){ return (x === null || x === undefined) ? '—' : (x === Infinity ? '∞' : x.toFixed(d === undefined ? 2 : d)); }
    // TITULO FMT FECHA

    /** Convierte un tiempo UNIX en segundos en texto aaaa-mm-dd hh:mm (UTC). */
    function formatoFecha(t){ return new Date(t * 1000).toISOString().slice(0, 16).replace('T', ' '); }
    // TITULO TONO

    /** Devuelve la clase CSS de color según el signo de x: positivo, negativo o neutro. */
    function tono(x){ return x > 0 ? 'backtest-posicion' : (x < 0 ? 'backtest-negativo' : 'backtest-neutro'); }
    // TITULO NUM INPUT

    /**
     * Crea un campo numérico con valor, mínimo y paso; al cambiar valida, corrige al mínimo si es inválido, llama a
     * alCambiar con el número y guarda. Devuelve el input.
     */
    function numeroInput(valor, min, paso, alCambiar, ancho){
      var i = document.createElement('input'); i.type = 'number'; i.value = valor; i.step = paso || 'any'; if (min !== null && min !== undefined) i.min = min;
      if (ancho) i.style.width = ancho;
      i.addEventListener('change', function(){ var v = Number(i.value); if (!isFinite(v) || (min !== null && min !== undefined && v < min)) { v = (min !== null && min !== undefined) ? min : 0; i.value = v; } alCambiar(v); backtestGuardar(); });
      return i;
    }
    // TITULO FILA FORM

    /** Crea una fila del formulario con la etiqueta y el control indicados y la devuelve. */
    function filaFormulario(etiqueta, control){ var f = el('div', 'backtest-fila'); f.appendChild(el('span', '', etiqueta)); f.appendChild(control); return f; }
    // TITULO SELECTOR BT

    /**
     * Crea un desplegable con opciones [valor, texto] que llama a alCambiar y guarda al elegir. Devuelve el select.
     */
    function selectorBacktest(opciones, actual, alCambiar, bloqueada, mensajeBloqueo){
      var s = document.createElement('select');
      opciones.forEach(function(o){ var bl = bloqueada && bloqueada(o[0]); var op = el('option', '', (bl ? '\uD83D\uDD12 ' : '') + o[1]); op.value = o[0]; if (String(o[0]) === String(actual)) op.selected = true; s.appendChild(op); });
      var previo = String(actual);
      s.addEventListener('change', function(){
        // Una opción con candado que el plan no incluye no se aplica: se vuelve a la anterior y se avisa.
        if (bloqueada && bloqueada(s.value)) { s.value = previo; avisoPlan(mensajeBloqueo); return; }
        previo = String(s.value); alCambiar(s.value); backtestGuardar();
      });
      return s;
    }

    // TITULO OPCIONES OPERANDO

    // ---------- Editor de un operando (precio, número o indicador con sus parámetros) ----------
    /**
     * Crea el desplegable de operandos agrupado: precios, número fijo y los indicadores del catálogo (sin los que
     * usan velas futuras ni la capa Chikou).
     */
    function opcionesOperando(){
      var s = document.createElement('select'), g;
      g = document.createElement('optgroup'); g.label = 'Precio';
      BACKTEST_PRECIOS.forEach(function(o){ var op = el('option', '', o[1].replace('Precio: ', '')); op.value = 'precio:' + o[0]; g.appendChild(op); });
      s.appendChild(g);
      g = document.createElement('optgroup'); g.label = 'Valor fijo';
      var on = el('option', '', 'Número…'); on.value = 'num'; g.appendChild(on); s.appendChild(g);
      GRUPOS_INDICADOR.forEach(function(gr){
        var og = document.createElement('optgroup'); og.label = gr;
        LISTA_DEFS.forEach(function(tablaDatos){
          if (tablaDatos.grupo !== gr || BACKTEST_NO_CAUSAL[tablaDatos.id]) return;
          tablaDatos.capas.forEach(function(cp, i){
            if (tablaDatos.id === 'ichimoku' && i === 4) return;   // Chikou mira al futuro
            var op = el('option', '', tablaDatos.corto + (tablaDatos.capas.length > 1 ? ' · ' + cp[0] : '')); op.value = 'ind:' + tablaDatos.id + ':' + i; og.appendChild(op);
          });
        });
        if (og.children.length) s.appendChild(og);
      });
      return s;
    }
    // TITULO CLAVE OPERANDO

    /** Devuelve la clave de texto del operando op usada como valor del desplegable (num, precio:x o ind:id:capa). */
    function claveOperando(op){ return op.k === 'num' ? 'num' : (op.k === 'precio' ? 'precio:' + op.f : 'ind:' + op.id + ':' + (op.capa || 0)); }
    // TITULO EDITOR OPERANDO

    /**
     * Crea el editor de un operando: desplegable de tipo más los campos que corresponden (número o parámetros del
     * indicador). reemplazar recibe el operando nuevo y redibujar repinta el formulario.
     */
    function editorOperando(op, reemplazar, redibujar){
      var cont = el('div', 'backtest-operacion');
      var sel = opcionesOperando(); sel.value = claveOperando(op);
      if (sel.value !== claveOperando(op)) sel.selectedIndex = 0;
      sel.addEventListener('change', function(){
        var v = sel.value, nuevo;
        if (v === 'num') nuevo = backtestOperacionNumero(50);
        else if (v.indexOf('precio:') === 0) nuevo = backtestOperacionPrecio(v.slice(7));
        else { var q = v.split(':'); nuevo = backtestOperacionIndicador(q[1], validarParametros(DEFS[q[1]], null), Number(q[2])); }
        reemplazar(nuevo); backtestGuardar(); redibujar();
      });
      cont.appendChild(sel);
      if (op.k === 'num') {
        cont.appendChild(numeroInput(op.v, null, 'any', function(v){ op.v = v; }, '80px'));
      } else if (op.k === 'ind') {
        var tablaDatos = DEFS[op.id];
        tablaDatos.params.forEach(function(pd){
          if (pd.k === 'desp') return;
          var w = el('label', 'backtest-p'); w.appendChild(document.createTextNode(pd.n.replace('Periodo ', 'P. ').replace('Aplicar a', 'sobre') + ' '));
          if (pd.t === 'sel') w.appendChild(selectorBacktest(pd.o, op.p[pd.k] !== undefined ? op.p[pd.k] : pd.d, function(v){ op.p[pd.k] = v; }));
          else { var i = numeroInput(op.p[pd.k] !== undefined ? op.p[pd.k] : pd.d, pd.min, pd.paso, function(v){ op.p[pd.k] = v; }); i.max = pd.max; w.appendChild(i); }
          cont.appendChild(w);
        });
      }
      return cont;
    }

    // TITULO BLOQUE CONDICIONES

    // ---------- Bloque de condiciones ----------
    /**
     * Crea la caja de un bloque de condiciones (entrada o salida) con selector Y/O, filas editables de condición,
     * botón para quitarlas y botón para añadir. Devuelve el elemento.
     */
    function bloqueCondiciones(titulo, bloque, nota){
      var caja = el('div', 'backtest-bloque');
      var cab = el('div', 'backtest-bloque-cabecera'); cab.appendChild(el('span', '', titulo));
      if (bloque.cond.length > 1) {
        cab.appendChild(selectorBacktest([['y', 'Se cumplen TODAS'], ['o', 'Se cumple ALGUNA']], bloque.logica, function(v){ bloque.logica = v; }));
      }
      caja.appendChild(cab);
      if (nota && !bloque.cond.length) caja.appendChild(el('div', 'backtest-nota', nota));
      bloque.cond.forEach(function(c, idx){
        var fila = el('div', 'backtest-condicion');
        fila.appendChild(editorOperando(c.a, function(n){ c.a = n; }, backtestPintarFormulario));
        var os = selectorBacktest(BACKTEST_OPERACIONES, c.op, function(v){ c.op = v; }); os.className = 'backtest-operacion-seleccion'; fila.appendChild(os);
        fila.appendChild(editorOperando(c.b, function(n){ c.b = n; }, backtestPintarFormulario));
        var x = el('button', 'backtest-condicion-x', '✕ quitar condición'); x.title = 'Quitar condición';
        x.addEventListener('click', function(){ bloque.cond.splice(idx, 1); backtestGuardar(); backtestPintarFormulario(); });
        fila.appendChild(x);
        caja.appendChild(fila);
      });
      var add = el('button', 'backtest-boton', '+ Añadir condición');
      add.addEventListener('click', function(){
        bloque.cond.push({ a: backtestOperacionIndicador('ema', { periodo: 20 }), op: 'cruzaArriba', b: backtestOperacionIndicador('ema', { periodo: 50 }) });
        backtestGuardar(); backtestPintarFormulario();
      });
      caja.appendChild(add);
      return caja;
    }
    // TITULO INVERTIR OP

    /**
     * Devuelve el operador contrario (mayor <-> menor, cruce hacia arriba <-> hacia abajo) usado al copiar
     * condiciones de compra a venta.
     */
    function invertirOperacion(op){ return { cruzaArriba: 'cruzaAbajo', cruzaAbajo: 'cruzaArriba', gt: 'lt', lt: 'gt', ge: 'le', le: 'ge' }[op] || op; }
    // TITULO COPIAR INVERTIDO

    /** Copia la lógica y las condiciones del bloque desde al bloque hacia invirtiendo los operadores. */
    function copiarInvertido(desde, hacia){
      hacia.logica = desde.logica;
      hacia.cond = JSON.parse(JSON.stringify(desde.cond)).map(function(c){ c.op = invertirOperacion(c.op); return c; });
    }

    // TITULO BT PINTAR FORM

    // ---------- Formulario ----------
    /**
     * Dibuja el formulario completo del backtest: datos, dirección, condiciones de compra y venta, gestión de la
     * operación, costes, capital y botones de acción.
     */
    function backtestPintarFormulario(){
      var e = backtestConfiguracion.est, c = backtestConfiguracion.cost;
      backtestFormulario.innerHTML = '';
      /** Auxiliar de btPintarForm: añade al formulario un título de sección con el texto t. */
      function sec(t){ backtestFormulario.appendChild(el('div', 'backtest-seccion', t)); }

      sec('Datos');
      backtestFormulario.appendChild(filaFormulario('Símbolo y temporalidad', el('b', '', SIMBOLO + ' · ' + (temporalidadActual === 'MN1' ? 'MN' : temporalidadActual))));
      // Las cantidades que el plan no incluye se muestran con candado (al elegirlas sale el aviso); si lo guardado supera el tope, se baja al máximo permitido.
      var opcionesVelas = [[2000, '2.000'], [5000, '5.000'], [10000, '10.000'], [20000, '20.000']];
      var velasBloqueada = function(v){ return PLAN.backtest_velas != null && Number(v) > PLAN.backtest_velas; };
      var velasPermitidas = opcionesVelas.filter(function(o){ return !velasBloqueada(o[0]); });
      if (velasPermitidas.length && backtestConfiguracion.n > velasPermitidas[velasPermitidas.length - 1][0]) backtestConfiguracion.n = velasPermitidas[velasPermitidas.length - 1][0];
      backtestFormulario.appendChild(filaFormulario('Velas históricas', selectorBacktest(opcionesVelas, backtestConfiguracion.n, function(v){ backtestConfiguracion.n = Number(v); }, velasBloqueada, PLAN.mensajes.backtest_velas)));
      backtestFormulario.appendChild(el('div', 'backtest-nota', 'Se descargan de MT5 al ejecutar. Más velas = resultado más fiable.' + (PLAN.backtest_velas != null && PLAN.backtest_velas < 20000 ? ' ' + PLAN.mensajes.backtest_velas : '')));

      sec('Dirección');
      backtestFormulario.appendChild(filaFormulario('Operar', selectorBacktest([['largo', 'Solo compras'], ['corto', 'Solo ventas'], ['ambos', 'Compras y ventas']], e.dir, function(v){ e.dir = v; backtestPintarFormulario(); })));
      if (e.dir === 'ambos') {
        var ck = el('label', 'backtest-revisar'); var ci = document.createElement('input'); ci.type = 'checkbox'; ci.checked = !!e.invertir;
        ci.addEventListener('change', function(){ e.invertir = ci.checked; backtestGuardar(); });
        ck.appendChild(ci); ck.appendChild(el('span', '', 'Si aparece la señal contraria, cerrar y girar la posición')); backtestFormulario.appendChild(ck);
      }

      if (e.dir !== 'corto') {
        sec('Compra');
        backtestFormulario.appendChild(bloqueCondiciones('Entrada (la señal se evalúa al cierre de la vela)', e.largo.entrada));
        backtestFormulario.appendChild(bloqueCondiciones('Salida adicional (opcional)', e.largo.salida, 'Sin condiciones: solo salen el Stop, el Objetivo y el resto de reglas de abajo.'));
      }
      if (e.dir !== 'largo') {
        sec('Venta');
        if (e.dir !== 'corto') { var cp = el('button', 'backtest-boton', 'Copiar condiciones de compra (invertidas)'); cp.addEventListener('click', function(){ copiarInvertido(e.largo.entrada, e.corto.entrada); copiarInvertido(e.largo.salida, e.corto.salida); backtestGuardar(); backtestPintarFormulario(); }); backtestFormulario.appendChild(cp); backtestFormulario.appendChild(el('div', 'backtest-nota', ' ')); }
        backtestFormulario.appendChild(bloqueCondiciones('Entrada (la señal se evalúa al cierre de la vela)', e.corto.entrada));
        backtestFormulario.appendChild(bloqueCondiciones('Salida adicional (opcional)', e.corto.salida, 'Sin condiciones: solo salen el Stop, el Objetivo y el resto de reglas de abajo.'));
      }

      sec('Gestión de la operación');
      backtestFormulario.appendChild(filaFormulario('Stop Loss (%)', numeroInput(e.sl, 0, 0.1, function(v){ e.sl = v; })));
      backtestFormulario.appendChild(filaFormulario('Take Profit (%)', numeroInput(e.tp, 0, 0.1, function(v){ e.tp = v; })));
      backtestFormulario.appendChild(filaFormulario('Trailing stop (%)', numeroInput(e.trail, 0, 0.1, function(v){ e.trail = v; })));
      backtestFormulario.appendChild(filaFormulario('Máx. velas en la operación', numeroInput(e.maxBarras, 0, 1, function(v){ e.maxBarras = Math.round(v); })));
      backtestFormulario.appendChild(el('div', 'backtest-nota', 'Los porcentajes se miden desde el precio real de entrada. 0 = desactivado.'));

      sec('Costes (reales, no los ignores)');
      backtestFormulario.appendChild(filaFormulario('Spread', selectorBacktest([['mt5', 'Histórico de MT5 (por vela)'], ['fijo', 'Fijo']], c.spreadModo, function(v){ c.spreadModo = v; })));
      backtestFormulario.appendChild(filaFormulario('Spread fijo (pips)', numeroInput(c.spreadPips, 0, 0.1, function(v){ c.spreadPips = v; })));
      backtestFormulario.appendChild(filaFormulario('Slippage por ejecución (pips)', numeroInput(c.slipPips, 0, 0.1, function(v){ c.slipPips = v; })));
      backtestFormulario.appendChild(filaFormulario('Comisión por lado (% del nominal)', numeroInput(c.comision, 0, 0.001, function(v){ c.comision = v; })));
      backtestFormulario.appendChild(el('div', 'backtest-nota', '1 pip = ' + PIP + ' · Con spread histórico, el fijo solo se usa en las velas sin dato. El slippage se aplica en contra en entradas, stops y salidas a mercado.'));

      sec('Capital y tamaño');
      backtestFormulario.appendChild(filaFormulario('Capital inicial', numeroInput(backtestConfiguracion.capital, 1, 100, function(v){ backtestConfiguracion.capital = v; })));
      backtestFormulario.appendChild(filaFormulario('Tamaño de la posición', selectorBacktest([['nominal', '% del capital (nominal)'], ['riesgo', 'Riesgo % del capital'] ], e.tam.modo, function(v){ e.tam.modo = v; backtestPintarFormulario(); })));
      backtestFormulario.appendChild(filaFormulario(e.tam.modo === 'riesgo' ? 'Riesgo por operación (%)' : 'Nominal (% del capital)', numeroInput(e.tam.valor, 0.01, 0.1, function(v){ e.tam.valor = v; })));
      if (e.tam.modo === 'riesgo') backtestFormulario.appendChild(filaFormulario('Apalancamiento máximo (x)', numeroInput(e.tam.apalMax, 1, 1, function(v){ e.tam.apalMax = v; })));
      backtestFormulario.appendChild(el('div', 'backtest-nota', e.tam.modo === 'riesgo' ? 'Tamaño = riesgo ÷ stop; necesita Stop Loss.' : '100 % = sin apalancamiento; 200 % = doble del capital.'));

      var run = el('button', 'backtest-boton primario', 'Ejecutar backtest'); run.id = 'backtest-ejecutar';
      run.addEventListener('click', backtestEjecutarUI); backtestFormulario.appendChild(run);
      var acc = el('div', 'backtest-acciones');
      var ej = el('button', 'backtest-boton', 'Cargar ejemplo (EMA 20/50 + RSI)'); ej.addEventListener('click', function(){ backtestConfiguracion.est = backtestEjemplo(); backtestGuardar(); backtestPintarFormulario(); });
      var resumen = el('button', 'backtest-boton', 'Restablecer todo'); resumen.addEventListener('click', function(){ backtestConfiguracion = backtestConfiguracionPorDefecto(); backtestGuardar(); backtestPintarFormulario(); });
      acc.appendChild(ej); acc.appendChild(resumen); backtestFormulario.appendChild(acc);
    }

    // TITULO BT AVISO

    // ---------- Ejecución ----------
    /** Crea un aviso de tipo (error, aviso o info) con el texto dado y lo devuelve. */
    function backtestAviso(tipo, texto){ var d = el('div', 'backtest-aviso ' + tipo); d.textContent = texto; return d; }
    // TITULO BT EJECUTAR UI

    /**
     * Descarga las velas de la API, ejecuta el backtest, guarda el resultado en btUltimo y pinta los resultados;
     * muestra el progreso en el botón y los errores como aviso.
     */
    function backtestEjecutarUI(){
      var boton = document.getElementById('backtest-ejecutar'), configuracion = backtestConfiguracion;
      backtestResultado.innerHTML = '';
      boton.disabled = true; boton.textContent = 'Descargando ' + configuracion.n + ' velas…';
      fetch(API + '/velas/' + encodeURIComponent(SIMBOLO) + '?tf=' + temporalidadActual + '&n=' + configuracion.n)
        .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function(datos){
          if (!Array.isArray(datos) || datos.length < 50) throw new Error('MT5 devolvió muy pocas velas (' + (datos ? datos.length : 0) + ').');
          boton.textContent = 'Calculando…';
          return new Promise(function(res){ setTimeout(function(){ res(datos); }, 30); });
        })
        .then(function(datos){
          var cost = { spreadModo: configuracion.cost.spreadModo, spreadPips: configuracion.cost.spreadPips, slipPips: configuracion.cost.slipPips, comision: configuracion.cost.comision, pip: PIP, punto: Math.pow(10, -DIGITS) };
          var est = JSON.parse(JSON.stringify(configuracion.est));
          var r = backtestEjecutar(datos, est, cost, configuracion.capital);
          backtestUltimo = { r: r, datos: datos, est: est, cost: cost, histSpread: datos.some(function(d){ return d.spread > 0; }) };
          backtestPestana = 'resumen';
          backtestPintarResultados();
          document.getElementById('backtest-subtitulo').textContent = SIMBOLO + ' · ' + temporalidadActual + ' · ' + datos.length + ' velas (' + formatoFecha(datos[0].time).slice(0, 10) + ' → ' + formatoFecha(datos[datos.length - 1].time).slice(0, 10) + ')';
        })
        .catch(function(e){
          backtestResultado.innerHTML = ''; backtestResultado.appendChild(backtestAviso('error', 'No se pudo ejecutar: ' + (e && e.message ? e.message : e) + (String(e && e.message).indexOf('Failed to fetch') >= 0 ? ' (¿está abierto servidor_datos.py?)' : '')));
        })
        .then(function(){ boton.disabled = false; boton.textContent = 'Ejecutar backtest'; });
    }

    // TITULO KPI

    // ---------- Resultados ----------
    /**
     * Crea una tarjeta de indicador con título k, valor v, subtexto s y clase de color cls. Devuelve el elemento.
     */
    function kpi(k, v, s, cls){
      var d = el('div', 'backtest-kpi'); d.appendChild(el('div', 'k', k));
      var vv = el('div', 'v ' + (cls || 'backtest-neutro'), v); d.appendChild(vv);
      if (s) d.appendChild(el('div', 's', s));
      return d;
    }
    // TITULO BT PINTAR RESULTADOS

    /**
     * Dibuja el panel de resultados del último backtest: avisos de honestidad, pestañas Resumen, Operaciones y Cómo
     * se simula, acciones de gráfico y CSV, tarjetas de métricas y curvas.
     */
    function backtestPintarResultados(){
      var u = backtestUltimo; if (!u) return;
      var r = u.r, m = r.m, m0 = r.mSinCostes;
      backtestResultado.innerHTML = '';
      // avisos honestos
      if (!u.histSpread && u.cost.spreadModo === 'mt5') backtestResultado.appendChild(backtestAviso('info', 'El servidor no envió el spread histórico (reinicia servidor_datos.py): se usó el spread fijo de ' + u.cost.spreadPips + ' pips.'));
      if (m.ruina) backtestResultado.appendChild(backtestAviso('error', 'La cuenta quedó liquidada (capital 0) durante la prueba.'));
      if (m.operaciones < 30) backtestResultado.appendChild(backtestAviso('aviso', 'Solo ' + m.operaciones + ' operaciones: con tan pocas, el resultado no es estadísticamente fiable. Usa más velas o una temporalidad menor.'));
      if (m0.rentabilidad > 0 && m.rentabilidad <= 0) backtestResultado.appendChild(backtestAviso('aviso', 'Sin costes la estrategia ganaba (' + formatoPorcentaje(m0.rentabilidad) + '), pero con spread, slippage y comisiones pierde: la ventaja no cubre los costes.'));
      if (m.sharpe !== null && m.sharpe > 3 && m.operaciones < 60) backtestResultado.appendChild(backtestAviso('aviso', 'Sharpe muy alto con pocas operaciones: desconfía, suele ser casualidad o sobreajuste.'));
      if (m.maxDrawdown < -0.5) backtestResultado.appendChild(backtestAviso('aviso', 'El drawdown máximo supera el 50 %: difícilmente soportable en la práctica.'));
      if (m.rentabilidad < m.buyHold && m.operaciones >= 1) backtestResultado.appendChild(backtestAviso('info', 'No supera a comprar y mantener (' + formatoPorcentaje(m.buyHold) + ') en el mismo periodo.'));

      var tabs = el('div', 'backtest-pestanas');
      [['resumen', 'Resumen'], ['ops', 'Operaciones (' + r.trades.length + ')'], ['supuestos', 'Cómo se simula']].forEach(function(t){
        var b = el('button', backtestPestana === t[0] ? 'on' : '', t[1]); b.addEventListener('click', function(){ backtestPestana = t[0]; backtestPintarResultados(); }); tabs.appendChild(b);
      });
      // acciones
      var acc = el('div', 'backtest-acciones');
      var bm = el('button', 'backtest-boton', marcasBacktest ? 'Quitar operaciones del gráfico' : 'Ver operaciones en el gráfico');
      bm.addEventListener('click', function(){ if (marcasBacktest) { marcasBacktest = null; aplicarMarcasBacktest(); } else { backtestMarcar(); } backtestPintarResultados(); });
      var bc = el('button', 'backtest-boton', 'Exportar operaciones (CSV)'); bc.addEventListener('click', backtestCSV);
      acc.appendChild(bm); acc.appendChild(bc);
      backtestResultado.appendChild(acc); backtestResultado.appendChild(tabs);

      if (backtestPestana === 'resumen') {
        var g = el('div', 'backtest-kpis');
        g.appendChild(kpi('Rentabilidad neta', formatoPorcentaje(m.rentabilidad), formatoNumero(m.capitalFinal, 2) + ' de ' + formatoNumero(r.capital, 0) + (m.anualizada !== null ? ' · ' + formatoPorcentaje(m.anualizada, 1) + ' anual' : ''), tono(m.rentabilidad)));
        g.appendChild(kpi('Sin costes', formatoPorcentaje(m0.rentabilidad), 'Los costes restan ' + formatoPorcentaje(m0.rentabilidad - m.rentabilidad).replace('+', ''), tono(m0.rentabilidad)));
        g.appendChild(kpi('Comprar y mantener', formatoPorcentaje(m.buyHold), 'mismo periodo', tono(m.buyHold)));
        g.appendChild(kpi('Operaciones', String(m.operaciones), m.ganadoras + ' ganadoras · ' + m.perdedoras + ' perdedoras'));
        g.appendChild(kpi('Win rate', m.winRate === null ? '—' : (m.winRate * 100).toFixed(1) + '%', 'ganancia media ' + formatoPorcentaje(m.mediaGana) + ' / pérdida media ' + formatoPorcentaje(m.mediaPierde)));
        g.appendChild(kpi('Profit factor', formatoNumero(m.profitFactor), 'ganancias brutas ÷ pérdidas brutas', m.profitFactor !== null && m.profitFactor > 1 ? 'backtest-posicion' : 'backtest-negativo'));
        g.appendChild(kpi('Drawdown máximo', formatoPorcentaje(m.maxDrawdown), 'caída desde un máximo de capital', 'backtest-negativo'));
        g.appendChild(kpi('Sharpe (anualizado)', formatoNumero(m.sharpe), 'sin tasa libre de riesgo', m.sharpe !== null && m.sharpe > 0 ? 'backtest-posicion' : 'backtest-negativo'));
        g.appendChild(kpi('Mejor operación', m.mejor ? formatoPorcentaje(m.mejor.ret) : '—', m.mejor ? formatoFecha(datosT(m.mejor.i1)) : '', 'backtest-posicion'));
        g.appendChild(kpi('Peor operación', m.peor ? formatoPorcentaje(m.peor.ret) : '—', m.peor ? formatoFecha(datosT(m.peor.i1)) : '', 'backtest-negativo'));
        g.appendChild(kpi('Resultado medio por operación', formatoPorcentaje(m.mediaOp, 3), 'expectativa', tono(m.mediaOp)));
        g.appendChild(kpi('Tiempo en mercado', (m.exposicion * 100).toFixed(1) + '%', m.barrasMedias === null ? '' : 'media ' + m.barrasMedias.toFixed(1) + ' velas por operación'));
        g.appendChild(kpi('Rachas', 'G ' + m.rachaGanadoraMax + ' / P ' + m.rachaPerdedoraMax, 'máx. ganadoras / perdedoras seguidas'));
        backtestResultado.appendChild(g);
        var ge = el('div', 'backtest-grafico'); ge.appendChild(el('div', 'backtest-titulo', 'Curva de capital (azul) frente a comprar y mantener (gris)')); var de = el('div'); de.id = 'backtest-equity'; ge.appendChild(de); backtestResultado.appendChild(ge);
        var gd = el('div', 'backtest-grafico'); gd.appendChild(el('div', 'backtest-titulo', 'Drawdown')); var dd = el('div'); dd.id = 'backtest-drawdown'; gd.appendChild(dd); backtestResultado.appendChild(gd);
        backtestDibujarCurvas();
      } else if (backtestPestana === 'ops') {
        backtestResultado.appendChild(backtestTabla());
      } else {
        var ul = el('ul', 'backtest-supuestos');
        ['Las señales se evalúan al cierre de cada vela y la orden se ejecuta en la apertura de la siguiente: nunca se usa información futura.',
         'Las velas de MT5 son precios bid. Las compras entran al ask (bid + spread); las ventas, al bid. El spread se paga una vez por operación (histórico real de cada vela si el servidor lo envía).',
         'El slippage se aplica siempre en contra al entrar, en los stops y en las salidas a mercado. El Take Profit es una orden límite: se ejecuta a su precio (o a la apertura si hay un hueco a favor).',
         'La comisión se cobra en cada lado como % del nominal.',
         'Dentro de una misma vela no se conoce el orden de los movimientos: si toca el Stop y el Objetivo a la vez, se asume el Stop. Si la vela abre más allá del Stop (hueco), se sale a la apertura.',
         'Los porcentajes de Stop/Objetivo/Trailing se miden desde el precio real de entrada (ya con spread y slippage).',
         'Una sola posición a la vez. Al final de los datos, lo abierto se cierra al último precio.',
         'Drawdown y Sharpe se calculan sobre la curva de capital valorada vela a vela. Sharpe anualizado con las velas reales por año, sin tasa libre de riesgo.',
         'Rentabilidades expresadas sobre el capital: no se convierten divisas ni se simulan swaps, márgenes ni márgenes de llamada.',
         'No se pueden usar indicadores que miran al futuro (fractales, ZigZag, regresión); los desplazamientos negativos están bloqueados.',
         'Un buen resultado histórico NO garantiza resultados futuros. Cuantas más operaciones y más variedad de mercado, más fiable.'
        ].forEach(function(t){ ul.appendChild(el('li', '', t)); });
        backtestResultado.appendChild(ul);
      }
    }
    // TITULO DATOS T

    /** Devuelve el tiempo de la vela de índice i de las velas del último backtest (limitado al último índice). */
    function datosT(i){ return backtestUltimo.datos[Math.min(i, backtestUltimo.datos.length - 1)].time; }

    // TITULO BT TABLA

    /**
     * Construye la tabla de operaciones del último backtest (hasta 1.500 filas) con notas si hay más o ninguna
     * operación. Devuelve el contenedor.
     */
    function backtestTabla(){
      var u = backtestUltimo, t = el('table', 'backtest-tabla'), cab = el('tr');
      ['#', 'Lado', 'Entrada', 'Precio entrada', 'Salida', 'Precio salida', 'Motivo', 'Velas', 'Resultado', 'Capital'].forEach(function(h){ cab.appendChild(el('th', '', h)); });
      t.appendChild(cab);
      var dg = DIGITS, lim = Math.min(u.r.trades.length, 1500);
      for (var i = 0; i < lim; i++){
        var x = u.r.trades[i], tr = el('tr');
        var celdas = [i + 1, x.dir > 0 ? 'Compra' : 'Venta', formatoFecha(datosT(x.i0)), x.p0.toFixed(dg), formatoFecha(datosT(x.i1)), x.p1.toFixed(dg), x.motivo, x.barras, formatoPorcentaje(x.ret), x.eqFin.toFixed(2)];
        celdas.forEach(function(c, j){ var td = el('td', j === 8 ? tono(x.ret) : '', String(c)); tr.appendChild(td); });
        t.appendChild(tr);
      }
      var cont = el('div'); var envoltorio = el('div', 'backtest-tabla-contenedor'); envoltorio.appendChild(t); cont.appendChild(envoltorio);
      if (u.r.trades.length > lim) cont.appendChild(el('div', 'backtest-nota', 'Se muestran las primeras ' + lim + ' de ' + u.r.trades.length + '. El CSV las incluye todas.'));
      if (!u.r.trades.length) cont.appendChild(el('div', 'backtest-vacio', 'La estrategia no generó ninguna operación con estas reglas y estos datos.'));
      return cont;
    }

    // TITULO BT DIBUJAR CURVAS

    /**
     * Dibuja la curva de capital frente a comprar y mantener y la de drawdown en dos gráficos sincronizados dentro
     * del panel de resultados.
     */
    function backtestDibujarCurvas(){
      var u = backtestUltimo, r = u.r, d = u.datos, ini = r.inicio, n = d.length;
      if (backtestCharts) { try { backtestCharts.eq.remove(); backtestCharts.dd.remove(); } catch (e) {} backtestCharts = null; }
      /**
       * Auxiliar de btDibujarCurvas: devuelve las opciones comunes de los gráficos de curvas, ampliadas con extra.
       */
      var opts = function(extra){ return Object.assign({ autoSize: true, layout: { background: { color: '#0d1117' }, textColor: '#d1d4dc', fontSize: 11 },
        grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } }, rightPriceScale: { borderColor: '#30363d', minimumWidth: 64 },
        timeScale: { borderColor: '#30363d', timeVisible: true, secondsVisible: false } }, extra || {}); };
      var ceq = LightweightCharts.createChart(document.getElementById('backtest-equity'), opts());
      var cdd = LightweightCharts.createChart(document.getElementById('backtest-drawdown'), opts());
      var s = ceq.addAreaSeries({ lineColor: '#2962ff', topColor: 'rgba(41,98,255,0.25)', bottomColor: 'rgba(41,98,255,0.02)', lineWidth: 2, priceLineVisible: false, priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });
      var bh = ceq.addLineSeries({ color: '#6e7681', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false, priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });
      var datosEquity = [], datosBH = [], datosDrawdown = [], base = d[Math.min(ini + 1, n - 1)].open;
      for (var i = ini; i < n; i++){
        if (r.curva[i] !== null) datosEquity.push({ time: d[i].time, value: r.curva[i] });
        if (i > ini) datosBH.push({ time: d[i].time, value: r.capital * d[i].close / base });
        if (r.m.dd[i] !== null) datosDrawdown.push({ time: d[i].time, value: r.m.dd[i] * 100 });
      }
      s.setData(datosEquity); bh.setData(datosBH);
      var sd = cdd.addAreaSeries({ lineColor: '#f85149', topColor: 'rgba(248,81,73,0.02)', bottomColor: 'rgba(248,81,73,0.3)', lineWidth: 1, priceLineVisible: false, priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });
      sd.setData(datosDrawdown);
      ceq.timeScale().fitContent(); cdd.timeScale().fitContent();
      var bloqueo = false;   // los dos gráficos se desplazan juntos
      /**
       * Auxiliar de btDibujarCurvas: hace que al desplazar el gráfico a también se desplace b, evitando bucles con la
       * bandera bloqueo.
       */
      function enlazar(a, b){ a.timeScale().subscribeVisibleLogicalRangeChange(function(rg){ if (bloqueo || !rg) return; bloqueo = true; b.timeScale().setVisibleLogicalRange(rg); bloqueo = false; }); }
      enlazar(ceq, cdd); enlazar(cdd, ceq);
      backtestCharts = { eq: ceq, dd: cdd };
    }

    // TITULO BT MARCAR

    // ---------- Marcas en el gráfico principal ----------
    /**
     * Crea las marcas de entrada y salida de las operaciones sobre el gráfico principal (flechas y círculos con el
     * resultado), limitadas a las 600 más recientes, y las aplica.
     */
    function backtestMarcar(){
      var u = backtestUltimo; if (!u) return;
      var ms = [], tInicio = datosActuales.length ? datosActuales[0].time : 0, d = u.datos;
      u.r.trades.forEach(function(t){
        var t0 = d[t.i0].time, t1 = d[t.i1].time, largo = t.dir > 0, gan = t.pnl > 0;
        if (t1 < tInicio) return;
        if (t0 >= tInicio) ms.push({ time: t0, position: largo ? 'belowBar' : 'aboveBar', color: largo ? '#3fb950' : '#f85149', shape: largo ? 'arrowUp' : 'arrowDown', text: '' });
        ms.push({ time: t1, position: largo ? 'aboveBar' : 'belowBar', color: gan ? '#3fb950' : '#f85149', shape: 'circle', text: formatoPorcentaje(t.ret, 1) });
      });
      ms.sort(function(a, b){ return a.time - b.time; });
      marcasBacktest = ms.length > 600 ? ms.slice(-600) : ms;   // más de eso ilegible; se muestran las más recientes
      aplicarMarcasBacktest();
    }
    // TITULO APLICAR MARCAS BT

    /** Aplica a la serie principal las marcas de backtest guardadas (o las borra si no hay). */
    function aplicarMarcasBacktest(){
      try { if (serie) serie.setMarkers(marcasBacktest || []); } catch (e) {}
    }

    // TITULO BT CSV

    /** Exporta las operaciones del último backtest a un CSV separado por punto y coma y lo descarga. */
    function backtestCSV(){
      var u = backtestUltimo; if (!u) return;
      var filas = ['n;lado;entrada;precio_entrada;salida;precio_salida;motivo;velas;resultado_pct;capital'];
      u.r.trades.forEach(function(t, i){
        filas.push([i + 1, t.dir > 0 ? 'compra' : 'venta', formatoFecha(datosT(t.i0)), t.p0.toFixed(DIGITS), formatoFecha(datosT(t.i1)), t.p1.toFixed(DIGITS), t.motivo, t.barras, (t.ret * 100).toFixed(4), t.eqFin.toFixed(2)].join(';'));
      });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob(['﻿' + filas.join('\n')], { type: 'text/csv;charset=utf-8' }));
      a.download = 'backtest_' + SIMBOLO + '_' + temporalidadActual + '.csv'; document.body.appendChild(a); a.click();
      setTimeout(function(){ document.body.removeChild(a); URL.revokeObjectURL(a.href); }, 500);
    }

    // TITULO BT ABRIR

    // ---------- Abrir / cerrar ----------
    /** Abre la ventana del backtest, dibuja el formulario y, si hay un resultado previo, lo muestra. */
    function backtestAbrir(){
      backtestSuperposicion.style.display = 'flex';
      backtestPintarFormulario();
      if (backtestUltimo) backtestPintarResultados();
    }
    // TITULO BT CERRAR

    /** Cierra la ventana del backtest. */
    function backtestCerrar(){ backtestSuperposicion.style.display = 'none'; }
    // Eventos de la ventana: abrir con el botón, cerrar con la X, con clic fuera o con Escape (si no hay otra ventana abierta)
    document.getElementById('boton-backtest-abrir').addEventListener('click', function(e){ e.stopPropagation(); backtestAbrir(); });
    document.getElementById('backtest-cerrar').addEventListener('click', backtestCerrar);
    backtestSuperposicion.addEventListener('click', function(e){ if (e.target === backtestSuperposicion) backtestCerrar(); });
    document.addEventListener('keydown', function(e){
      if (e.key === 'Escape' && backtestSuperposicion.style.display !== 'none' && configuracionSuperposicion.style.display === 'none' && modalSuperposicion.style.display === 'none') backtestCerrar();
    });

/* -------------------------------------------------------------------------------------------------------
   ---------------------------------- FIN Piña y Jara 61_backtest_ui .JS ---------------------------------
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
