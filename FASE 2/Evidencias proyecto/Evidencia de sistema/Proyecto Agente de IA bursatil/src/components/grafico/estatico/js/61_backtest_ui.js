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
    var BT_KEY = 'pj_backtest_cfg';
    var btOverlay = document.getElementById('bt-overlay');
    var btForm = document.getElementById('bt-form');
    var btRes = document.getElementById('bt-res');
    // marcasBT: marcas de las operaciones sobre el gráfico principal
    var marcasBT = null;          // marcas de las operaciones sobre el gráfico principal
    // btUltimo: último resultado { r, datos, est, cost }
    var btUltimo = null;          // último resultado { r, datos, est, cost }
    // btCharts: gráficos de la curva de capital
    var btCharts = null;          // gráficos de la curva de capital
    // btPestana: pestaña de resultados visible
    var btPestana = 'resumen';

    // ---------- Estrategia por defecto: el ejemplo EMA 20/50 + RSI > 50, SL 2 %, TP 4 % ----------
    /** Crea un operando de condición que apunta a la capa capa (0 por defecto) del indicador id con parámetros p. */
    function btOpInd(id, p, capa){ return { k: 'ind', id: id, capa: capa || 0, p: p || {} }; }
    /** Crea un operando de condición con un número fijo v. */
    function btOpNum(v){ return { k: 'num', v: v }; }
    /** Crea un operando de condición que usa el precio f (close, open, high, low, hl2, hlc3 o volume). */
    function btOpPrecio(f){ return { k: 'precio', f: f }; }
    /**
     * Devuelve la estrategia de ejemplo: compra con cruce de EMA 20/50 y RSI > 50, venta con lo contrario, SL 2 % y
     * TP 4 %.
     */
    function btEjemplo(){
      return {
        dir: 'largo', sl: 2, tp: 4, trail: 0, maxBarras: 0, invertir: false,
        tam: { modo: 'nominal', valor: 100, apalMax: 5 },
        largo: { entrada: { logica: 'y', cond: [
                  { a: btOpInd('ema', { periodo: 20 }), op: 'cruzaArriba', b: btOpInd('ema', { periodo: 50 }) },
                  { a: btOpInd('rsi', { periodo: 14 }), op: 'gt', b: btOpNum(50) }] },
                 salida: { logica: 'o', cond: [] } },
        corto: { entrada: { logica: 'y', cond: [
                  { a: btOpInd('ema', { periodo: 20 }), op: 'cruzaAbajo', b: btOpInd('ema', { periodo: 50 }) },
                  { a: btOpInd('rsi', { periodo: 14 }), op: 'lt', b: btOpNum(50) }] },
                 salida: { logica: 'o', cond: [] } }
      };
    }
    /**
     * Devuelve la configuración completa del backtest por defecto: estrategia de ejemplo, costes, capital de 10.000 y
     * 5.000 velas.
     */
    function btCfgPorDefecto(){
      return { est: btEjemplo(), cost: { spreadModo: 'mt5', spreadPips: 1.5, slipPips: 0.5, comision: 0.003 }, capital: 10000, n: 5000 };
    }
    // btCfg: configuración actual del backtest (estrategia, costes, capital y número de velas)
    var btCfg = btCfgPorDefecto();
    /**
     * Lee de localStorage la configuración del backtest recordada y la fusiona con la de defecto, corrigiendo bloques
     * mal formados; si falla vuelve a los valores por defecto.
     */
    (function btLeer(){
      try {
        var c = JSON.parse(localStorage.getItem(BT_KEY) || 'null');
        if (!c || !c.est || !c.est.largo || !c.est.corto || !c.est.tam || !c.cost) return;
        var d = btCfgPorDefecto();
        btCfg = { est: Object.assign(d.est, c.est), cost: Object.assign(d.cost, c.cost), capital: Number(c.capital) > 0 ? Number(c.capital) : d.capital, n: Number(c.n) > 0 ? Number(c.n) : d.n };
        ['largo', 'corto'].forEach(function(l){
          ['entrada', 'salida'].forEach(function(s){
            var b = btCfg.est[l][s];
            if (!b || !Array.isArray(b.cond)) btCfg.est[l][s] = { logica: s === 'entrada' ? 'y' : 'o', cond: [] };
          });
        });
      } catch (e) { btCfg = btCfgPorDefecto(); }
    })();
    /** Guarda la configuración actual del backtest en localStorage. */
    function btGuardar(){ try { localStorage.setItem(BT_KEY, JSON.stringify(btCfg)); } catch (e) {} }

    // ---------- Utilidades ----------
    /**
     * Formatea una fracción x como porcentaje con signo y d decimales (2 por defecto); devuelve un guion largo si no
     * es un número.
     */
    function fmtPct(x, d){ return (x === null || x === undefined || !isFinite(x)) ? '—' : (x >= 0 ? '+' : '') + (x * 100).toFixed(d === undefined ? 2 : d) + '%'; }
    /** Formatea un número con d decimales (2 por defecto); muestra ∞ para infinito y un guion largo si es nulo. */
    function fmtNum(x, d){ return (x === null || x === undefined) ? '—' : (x === Infinity ? '∞' : x.toFixed(d === undefined ? 2 : d)); }
    /** Convierte un tiempo UNIX en segundos en texto aaaa-mm-dd hh:mm (UTC). */
    function fmtFecha(t){ return new Date(t * 1000).toISOString().slice(0, 16).replace('T', ' '); }
    /** Devuelve la clase CSS de color según el signo de x: positivo, negativo o neutro. */
    function tono(x){ return x > 0 ? 'bt-pos' : (x < 0 ? 'bt-neg' : 'bt-neu'); }
    /**
     * Crea un campo numérico con valor, mínimo y paso; al cambiar valida, corrige al mínimo si es inválido, llama a
     * alCambiar con el número y guarda. Devuelve el input.
     */
    function numInput(valor, min, paso, alCambiar, ancho){
      var i = document.createElement('input'); i.type = 'number'; i.value = valor; i.step = paso || 'any'; if (min !== null && min !== undefined) i.min = min;
      if (ancho) i.style.width = ancho;
      i.addEventListener('change', function(){ var v = Number(i.value); if (!isFinite(v) || (min !== null && min !== undefined && v < min)) { v = (min !== null && min !== undefined) ? min : 0; i.value = v; } alCambiar(v); btGuardar(); });
      return i;
    }
    /** Crea una fila del formulario con la etiqueta y el control indicados y la devuelve. */
    function filaForm(etiqueta, control){ var f = el('div', 'bt-fila'); f.appendChild(el('span', '', etiqueta)); f.appendChild(control); return f; }
    /**
     * Crea un desplegable con opciones [valor, texto] que llama a alCambiar y guarda al elegir. Devuelve el select.
     */
    function selectorBT(opciones, actual, alCambiar){
      var s = document.createElement('select');
      opciones.forEach(function(o){ var op = el('option', '', o[1]); op.value = o[0]; if (String(o[0]) === String(actual)) op.selected = true; s.appendChild(op); });
      s.addEventListener('change', function(){ alCambiar(s.value); btGuardar(); });
      return s;
    }

    // ---------- Editor de un operando (precio, número o indicador con sus parámetros) ----------
    /**
     * Crea el desplegable de operandos agrupado: precios, número fijo y los indicadores del catálogo (sin los que
     * usan velas futuras ni la capa Chikou).
     */
    function opcionesOperando(){
      var s = document.createElement('select'), g;
      g = document.createElement('optgroup'); g.label = 'Precio';
      BT_PRECIOS.forEach(function(o){ var op = el('option', '', o[1].replace('Precio: ', '')); op.value = 'precio:' + o[0]; g.appendChild(op); });
      s.appendChild(g);
      g = document.createElement('optgroup'); g.label = 'Valor fijo';
      var on = el('option', '', 'Número…'); on.value = 'num'; g.appendChild(on); s.appendChild(g);
      GRUPOS_IND.forEach(function(gr){
        var og = document.createElement('optgroup'); og.label = gr;
        LISTA_DEFS.forEach(function(df){
          if (df.grupo !== gr || BT_NO_CAUSAL[df.id]) return;
          df.capas.forEach(function(cp, i){
            if (df.id === 'ichimoku' && i === 4) return;   // Chikou mira al futuro
            var op = el('option', '', df.corto + (df.capas.length > 1 ? ' · ' + cp[0] : '')); op.value = 'ind:' + df.id + ':' + i; og.appendChild(op);
          });
        });
        if (og.children.length) s.appendChild(og);
      });
      return s;
    }
    /** Devuelve la clave de texto del operando op usada como valor del desplegable (num, precio:x o ind:id:capa). */
    function claveOperando(op){ return op.k === 'num' ? 'num' : (op.k === 'precio' ? 'precio:' + op.f : 'ind:' + op.id + ':' + (op.capa || 0)); }
    /**
     * Crea el editor de un operando: desplegable de tipo más los campos que corresponden (número o parámetros del
     * indicador). reemplazar recibe el operando nuevo y redibujar repinta el formulario.
     */
    function editorOperando(op, reemplazar, redibujar){
      var cont = el('div', 'bt-oper');
      var sel = opcionesOperando(); sel.value = claveOperando(op);
      if (sel.value !== claveOperando(op)) sel.selectedIndex = 0;
      sel.addEventListener('change', function(){
        var v = sel.value, nuevo;
        if (v === 'num') nuevo = btOpNum(50);
        else if (v.indexOf('precio:') === 0) nuevo = btOpPrecio(v.slice(7));
        else { var q = v.split(':'); nuevo = btOpInd(q[1], validarParams(DEFS[q[1]], null), Number(q[2])); }
        reemplazar(nuevo); btGuardar(); redibujar();
      });
      cont.appendChild(sel);
      if (op.k === 'num') {
        cont.appendChild(numInput(op.v, null, 'any', function(v){ op.v = v; }, '80px'));
      } else if (op.k === 'ind') {
        var df = DEFS[op.id];
        df.params.forEach(function(pd){
          if (pd.k === 'desp') return;
          var w = el('label', 'bt-p'); w.appendChild(document.createTextNode(pd.n.replace('Periodo ', 'P. ').replace('Aplicar a', 'sobre') + ' '));
          if (pd.t === 'sel') w.appendChild(selectorBT(pd.o, op.p[pd.k] !== undefined ? op.p[pd.k] : pd.d, function(v){ op.p[pd.k] = v; }));
          else { var i = numInput(op.p[pd.k] !== undefined ? op.p[pd.k] : pd.d, pd.min, pd.paso, function(v){ op.p[pd.k] = v; }); i.max = pd.max; w.appendChild(i); }
          cont.appendChild(w);
        });
      }
      return cont;
    }

    // ---------- Bloque de condiciones ----------
    /**
     * Crea la caja de un bloque de condiciones (entrada o salida) con selector Y/O, filas editables de condición,
     * botón para quitarlas y botón para añadir. Devuelve el elemento.
     */
    function bloqueCondiciones(titulo, bloque, nota){
      var caja = el('div', 'bt-bloque');
      var cab = el('div', 'bt-bloque-cab'); cab.appendChild(el('span', '', titulo));
      if (bloque.cond.length > 1) {
        cab.appendChild(selectorBT([['y', 'Se cumplen TODAS'], ['o', 'Se cumple ALGUNA']], bloque.logica, function(v){ bloque.logica = v; }));
      }
      caja.appendChild(cab);
      if (nota && !bloque.cond.length) caja.appendChild(el('div', 'bt-nota', nota));
      bloque.cond.forEach(function(c, idx){
        var fila = el('div', 'bt-cond');
        fila.appendChild(editorOperando(c.a, function(n){ c.a = n; }, btPintarForm));
        var os = selectorBT(BT_OPS, c.op, function(v){ c.op = v; }); os.className = 'bt-op-sel'; fila.appendChild(os);
        fila.appendChild(editorOperando(c.b, function(n){ c.b = n; }, btPintarForm));
        var x = el('button', 'bt-cond-x', '✕ quitar condición'); x.title = 'Quitar condición';
        x.addEventListener('click', function(){ bloque.cond.splice(idx, 1); btGuardar(); btPintarForm(); });
        fila.appendChild(x);
        caja.appendChild(fila);
      });
      var add = el('button', 'bt-btn', '+ Añadir condición');
      add.addEventListener('click', function(){
        bloque.cond.push({ a: btOpInd('ema', { periodo: 20 }), op: 'cruzaArriba', b: btOpInd('ema', { periodo: 50 }) });
        btGuardar(); btPintarForm();
      });
      caja.appendChild(add);
      return caja;
    }
    /**
     * Devuelve el operador contrario (mayor <-> menor, cruce hacia arriba <-> hacia abajo) usado al copiar
     * condiciones de compra a venta.
     */
    function invertirOp(op){ return { cruzaArriba: 'cruzaAbajo', cruzaAbajo: 'cruzaArriba', gt: 'lt', lt: 'gt', ge: 'le', le: 'ge' }[op] || op; }
    /** Copia la lógica y las condiciones del bloque desde al bloque hacia invirtiendo los operadores. */
    function copiarInvertido(desde, hacia){
      hacia.logica = desde.logica;
      hacia.cond = JSON.parse(JSON.stringify(desde.cond)).map(function(c){ c.op = invertirOp(c.op); return c; });
    }

    // ---------- Formulario ----------
    /**
     * Dibuja el formulario completo del backtest: datos, dirección, condiciones de compra y venta, gestión de la
     * operación, costes, capital y botones de acción.
     */
    function btPintarForm(){
      var e = btCfg.est, c = btCfg.cost;
      btForm.innerHTML = '';
      /** Auxiliar de btPintarForm: añade al formulario un título de sección con el texto t. */
      function sec(t){ btForm.appendChild(el('div', 'bt-sec', t)); }

      sec('Datos');
      btForm.appendChild(filaForm('Símbolo y temporalidad', el('b', '', SIMBOLO + ' · ' + (tfActual === 'MN1' ? 'MN' : tfActual))));
      btForm.appendChild(filaForm('Velas históricas', selectorBT([[2000, '2.000'], [5000, '5.000'], [10000, '10.000'], [20000, '20.000'], [50000, '50.000']], btCfg.n, function(v){ btCfg.n = Number(v); })));
      btForm.appendChild(el('div', 'bt-nota', 'Se descargan de MT5 al ejecutar. Más velas = resultado más fiable.'));

      sec('Dirección');
      btForm.appendChild(filaForm('Operar', selectorBT([['largo', 'Solo compras'], ['corto', 'Solo ventas'], ['ambos', 'Compras y ventas']], e.dir, function(v){ e.dir = v; btPintarForm(); })));
      if (e.dir === 'ambos') {
        var ck = el('label', 'bt-check'); var ci = document.createElement('input'); ci.type = 'checkbox'; ci.checked = !!e.invertir;
        ci.addEventListener('change', function(){ e.invertir = ci.checked; btGuardar(); });
        ck.appendChild(ci); ck.appendChild(el('span', '', 'Si aparece la señal contraria, cerrar y girar la posición')); btForm.appendChild(ck);
      }

      if (e.dir !== 'corto') {
        sec('Compra');
        btForm.appendChild(bloqueCondiciones('Entrada (la señal se evalúa al cierre de la vela)', e.largo.entrada));
        btForm.appendChild(bloqueCondiciones('Salida adicional (opcional)', e.largo.salida, 'Sin condiciones: solo salen el Stop, el Objetivo y el resto de reglas de abajo.'));
      }
      if (e.dir !== 'largo') {
        sec('Venta');
        if (e.dir !== 'corto') { var cp = el('button', 'bt-btn', 'Copiar condiciones de compra (invertidas)'); cp.addEventListener('click', function(){ copiarInvertido(e.largo.entrada, e.corto.entrada); copiarInvertido(e.largo.salida, e.corto.salida); btGuardar(); btPintarForm(); }); btForm.appendChild(cp); btForm.appendChild(el('div', 'bt-nota', ' ')); }
        btForm.appendChild(bloqueCondiciones('Entrada (la señal se evalúa al cierre de la vela)', e.corto.entrada));
        btForm.appendChild(bloqueCondiciones('Salida adicional (opcional)', e.corto.salida, 'Sin condiciones: solo salen el Stop, el Objetivo y el resto de reglas de abajo.'));
      }

      sec('Gestión de la operación');
      btForm.appendChild(filaForm('Stop Loss (%)', numInput(e.sl, 0, 0.1, function(v){ e.sl = v; })));
      btForm.appendChild(filaForm('Take Profit (%)', numInput(e.tp, 0, 0.1, function(v){ e.tp = v; })));
      btForm.appendChild(filaForm('Trailing stop (%)', numInput(e.trail, 0, 0.1, function(v){ e.trail = v; })));
      btForm.appendChild(filaForm('Máx. velas en la operación', numInput(e.maxBarras, 0, 1, function(v){ e.maxBarras = Math.round(v); })));
      btForm.appendChild(el('div', 'bt-nota', 'Los porcentajes se miden desde el precio real de entrada. 0 = desactivado.'));

      sec('Costes (reales, no los ignores)');
      btForm.appendChild(filaForm('Spread', selectorBT([['mt5', 'Histórico de MT5 (por vela)'], ['fijo', 'Fijo']], c.spreadModo, function(v){ c.spreadModo = v; })));
      btForm.appendChild(filaForm('Spread fijo (pips)', numInput(c.spreadPips, 0, 0.1, function(v){ c.spreadPips = v; })));
      btForm.appendChild(filaForm('Slippage por ejecución (pips)', numInput(c.slipPips, 0, 0.1, function(v){ c.slipPips = v; })));
      btForm.appendChild(filaForm('Comisión por lado (% del nominal)', numInput(c.comision, 0, 0.001, function(v){ c.comision = v; })));
      btForm.appendChild(el('div', 'bt-nota', '1 pip = ' + PIP + ' · Con spread histórico, el fijo solo se usa en las velas sin dato. El slippage se aplica en contra en entradas, stops y salidas a mercado.'));

      sec('Capital y tamaño');
      btForm.appendChild(filaForm('Capital inicial', numInput(btCfg.capital, 1, 100, function(v){ btCfg.capital = v; })));
      btForm.appendChild(filaForm('Tamaño de la posición', selectorBT([['nominal', '% del capital (nominal)'], ['riesgo', 'Riesgo % del capital'] ], e.tam.modo, function(v){ e.tam.modo = v; btPintarForm(); })));
      btForm.appendChild(filaForm(e.tam.modo === 'riesgo' ? 'Riesgo por operación (%)' : 'Nominal (% del capital)', numInput(e.tam.valor, 0.01, 0.1, function(v){ e.tam.valor = v; })));
      if (e.tam.modo === 'riesgo') btForm.appendChild(filaForm('Apalancamiento máximo (x)', numInput(e.tam.apalMax, 1, 1, function(v){ e.tam.apalMax = v; })));
      btForm.appendChild(el('div', 'bt-nota', e.tam.modo === 'riesgo' ? 'Tamaño = riesgo ÷ stop; necesita Stop Loss.' : '100 % = sin apalancamiento; 200 % = doble del capital.'));

      var run = el('button', 'bt-btn primario', 'Ejecutar backtest'); run.id = 'bt-run';
      run.addEventListener('click', btEjecutarUI); btForm.appendChild(run);
      var acc = el('div', 'bt-acciones');
      var ej = el('button', 'bt-btn', 'Cargar ejemplo (EMA 20/50 + RSI)'); ej.addEventListener('click', function(){ btCfg.est = btEjemplo(); btGuardar(); btPintarForm(); });
      var rs = el('button', 'bt-btn', 'Restablecer todo'); rs.addEventListener('click', function(){ btCfg = btCfgPorDefecto(); btGuardar(); btPintarForm(); });
      acc.appendChild(ej); acc.appendChild(rs); btForm.appendChild(acc);
    }

    // ---------- Ejecución ----------
    /** Crea un aviso de tipo (error, aviso o info) con el texto dado y lo devuelve. */
    function btAviso(tipo, texto){ var d = el('div', 'bt-aviso ' + tipo); d.textContent = texto; return d; }
    /**
     * Descarga las velas de la API, ejecuta el backtest, guarda el resultado en btUltimo y pinta los resultados;
     * muestra el progreso en el botón y los errores como aviso.
     */
    function btEjecutarUI(){
      var boton = document.getElementById('bt-run'), cfg = btCfg;
      btRes.innerHTML = '';
      boton.disabled = true; boton.textContent = 'Descargando ' + cfg.n + ' velas de MT5…';
      fetch(API + '/velas/' + encodeURIComponent(SIMBOLO) + '?tf=' + tfActual + '&n=' + cfg.n)
        .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function(datos){
          if (!Array.isArray(datos) || datos.length < 50) throw new Error('MT5 devolvió muy pocas velas (' + (datos ? datos.length : 0) + ').');
          boton.textContent = 'Calculando…';
          return new Promise(function(res){ setTimeout(function(){ res(datos); }, 30); });
        })
        .then(function(datos){
          var cost = { spreadModo: cfg.cost.spreadModo, spreadPips: cfg.cost.spreadPips, slipPips: cfg.cost.slipPips, comision: cfg.cost.comision, pip: PIP, punto: Math.pow(10, -DIGITS) };
          var est = JSON.parse(JSON.stringify(cfg.est));
          var r = btEjecutar(datos, est, cost, cfg.capital);
          btUltimo = { r: r, datos: datos, est: est, cost: cost, histSpread: datos.some(function(d){ return d.spread > 0; }) };
          btPestana = 'resumen';
          btPintarResultados();
          document.getElementById('bt-sub').textContent = SIMBOLO + ' · ' + tfActual + ' · ' + datos.length + ' velas (' + fmtFecha(datos[0].time).slice(0, 10) + ' → ' + fmtFecha(datos[datos.length - 1].time).slice(0, 10) + ')';
        })
        .catch(function(e){
          btRes.innerHTML = ''; btRes.appendChild(btAviso('error', 'No se pudo ejecutar: ' + (e && e.message ? e.message : e) + (String(e && e.message).indexOf('Failed to fetch') >= 0 ? ' (¿está abierto servidor_datos.py?)' : '')));
        })
        .then(function(){ boton.disabled = false; boton.textContent = 'Ejecutar backtest'; });
    }

    // ---------- Resultados ----------
    /**
     * Crea una tarjeta de indicador con título k, valor v, subtexto s y clase de color cls. Devuelve el elemento.
     */
    function kpi(k, v, s, cls){
      var d = el('div', 'bt-kpi'); d.appendChild(el('div', 'k', k));
      var vv = el('div', 'v ' + (cls || 'bt-neu'), v); d.appendChild(vv);
      if (s) d.appendChild(el('div', 's', s));
      return d;
    }
    /**
     * Dibuja el panel de resultados del último backtest: avisos de honestidad, pestañas Resumen, Operaciones y Cómo
     * se simula, acciones de gráfico y CSV, tarjetas de métricas y curvas.
     */
    function btPintarResultados(){
      var u = btUltimo; if (!u) return;
      var r = u.r, m = r.m, m0 = r.mSinCostes;
      btRes.innerHTML = '';
      // avisos honestos
      if (!u.histSpread && u.cost.spreadModo === 'mt5') btRes.appendChild(btAviso('info', 'El servidor no envió el spread histórico (reinicia servidor_datos.py): se usó el spread fijo de ' + u.cost.spreadPips + ' pips.'));
      if (m.ruina) btRes.appendChild(btAviso('error', 'La cuenta quedó liquidada (capital 0) durante la prueba.'));
      if (m.operaciones < 30) btRes.appendChild(btAviso('aviso', 'Solo ' + m.operaciones + ' operaciones: con tan pocas, el resultado no es estadísticamente fiable. Usa más velas o una temporalidad menor.'));
      if (m0.rentabilidad > 0 && m.rentabilidad <= 0) btRes.appendChild(btAviso('aviso', 'Sin costes la estrategia ganaba (' + fmtPct(m0.rentabilidad) + '), pero con spread, slippage y comisiones pierde: la ventaja no cubre los costes.'));
      if (m.sharpe !== null && m.sharpe > 3 && m.operaciones < 60) btRes.appendChild(btAviso('aviso', 'Sharpe muy alto con pocas operaciones: desconfía, suele ser casualidad o sobreajuste.'));
      if (m.maxDrawdown < -0.5) btRes.appendChild(btAviso('aviso', 'El drawdown máximo supera el 50 %: difícilmente soportable en la práctica.'));
      if (m.rentabilidad < m.buyHold && m.operaciones >= 1) btRes.appendChild(btAviso('info', 'No supera a comprar y mantener (' + fmtPct(m.buyHold) + ') en el mismo periodo.'));

      var tabs = el('div', 'bt-tabs');
      [['resumen', 'Resumen'], ['ops', 'Operaciones (' + r.trades.length + ')'], ['supuestos', 'Cómo se simula']].forEach(function(t){
        var b = el('button', btPestana === t[0] ? 'on' : '', t[1]); b.addEventListener('click', function(){ btPestana = t[0]; btPintarResultados(); }); tabs.appendChild(b);
      });
      // acciones
      var acc = el('div', 'bt-acciones');
      var bm = el('button', 'bt-btn', marcasBT ? 'Quitar operaciones del gráfico' : 'Ver operaciones en el gráfico');
      bm.addEventListener('click', function(){ if (marcasBT) { marcasBT = null; aplicarMarcasBT(); } else { btMarcar(); } btPintarResultados(); });
      var bc = el('button', 'bt-btn', 'Exportar operaciones (CSV)'); bc.addEventListener('click', btCSV);
      acc.appendChild(bm); acc.appendChild(bc);
      btRes.appendChild(acc); btRes.appendChild(tabs);

      if (btPestana === 'resumen') {
        var g = el('div', 'bt-kpis');
        g.appendChild(kpi('Rentabilidad neta', fmtPct(m.rentabilidad), fmtNum(m.capitalFinal, 2) + ' de ' + fmtNum(r.capital, 0) + (m.anualizada !== null ? ' · ' + fmtPct(m.anualizada, 1) + ' anual' : ''), tono(m.rentabilidad)));
        g.appendChild(kpi('Sin costes', fmtPct(m0.rentabilidad), 'Los costes restan ' + fmtPct(m0.rentabilidad - m.rentabilidad).replace('+', ''), tono(m0.rentabilidad)));
        g.appendChild(kpi('Comprar y mantener', fmtPct(m.buyHold), 'mismo periodo', tono(m.buyHold)));
        g.appendChild(kpi('Operaciones', String(m.operaciones), m.ganadoras + ' ganadoras · ' + m.perdedoras + ' perdedoras'));
        g.appendChild(kpi('Win rate', m.winRate === null ? '—' : (m.winRate * 100).toFixed(1) + '%', 'ganancia media ' + fmtPct(m.mediaGana) + ' / pérdida media ' + fmtPct(m.mediaPierde)));
        g.appendChild(kpi('Profit factor', fmtNum(m.profitFactor), 'ganancias brutas ÷ pérdidas brutas', m.profitFactor !== null && m.profitFactor > 1 ? 'bt-pos' : 'bt-neg'));
        g.appendChild(kpi('Drawdown máximo', fmtPct(m.maxDrawdown), 'caída desde un máximo de capital', 'bt-neg'));
        g.appendChild(kpi('Sharpe (anualizado)', fmtNum(m.sharpe), 'sin tasa libre de riesgo', m.sharpe !== null && m.sharpe > 0 ? 'bt-pos' : 'bt-neg'));
        g.appendChild(kpi('Mejor operación', m.mejor ? fmtPct(m.mejor.ret) : '—', m.mejor ? fmtFecha(datosT(m.mejor.i1)) : '', 'bt-pos'));
        g.appendChild(kpi('Peor operación', m.peor ? fmtPct(m.peor.ret) : '—', m.peor ? fmtFecha(datosT(m.peor.i1)) : '', 'bt-neg'));
        g.appendChild(kpi('Resultado medio por operación', fmtPct(m.mediaOp, 3), 'expectativa', tono(m.mediaOp)));
        g.appendChild(kpi('Tiempo en mercado', (m.exposicion * 100).toFixed(1) + '%', m.barrasMedias === null ? '' : 'media ' + m.barrasMedias.toFixed(1) + ' velas por operación'));
        g.appendChild(kpi('Rachas', 'G ' + m.rachaGanadoraMax + ' / P ' + m.rachaPerdedoraMax, 'máx. ganadoras / perdedoras seguidas'));
        btRes.appendChild(g);
        var ge = el('div', 'bt-grafico'); ge.appendChild(el('div', 'bt-tit', 'Curva de capital (azul) frente a comprar y mantener (gris)')); var de = el('div'); de.id = 'bt-eq'; ge.appendChild(de); btRes.appendChild(ge);
        var gd = el('div', 'bt-grafico'); gd.appendChild(el('div', 'bt-tit', 'Drawdown')); var dd = el('div'); dd.id = 'bt-dd'; gd.appendChild(dd); btRes.appendChild(gd);
        btDibujarCurvas();
      } else if (btPestana === 'ops') {
        btRes.appendChild(btTabla());
      } else {
        var ul = el('ul', 'bt-supuestos');
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
        btRes.appendChild(ul);
      }
    }
    /** Devuelve el tiempo de la vela de índice i de las velas del último backtest (limitado al último índice). */
    function datosT(i){ return btUltimo.datos[Math.min(i, btUltimo.datos.length - 1)].time; }

    /**
     * Construye la tabla de operaciones del último backtest (hasta 1.500 filas) con notas si hay más o ninguna
     * operación. Devuelve el contenedor.
     */
    function btTabla(){
      var u = btUltimo, t = el('table', 'bt-tabla'), cab = el('tr');
      ['#', 'Lado', 'Entrada', 'Precio entrada', 'Salida', 'Precio salida', 'Motivo', 'Velas', 'Resultado', 'Capital'].forEach(function(h){ cab.appendChild(el('th', '', h)); });
      t.appendChild(cab);
      var dg = DIGITS, lim = Math.min(u.r.trades.length, 1500);
      for (var i = 0; i < lim; i++){
        var x = u.r.trades[i], tr = el('tr');
        var celdas = [i + 1, x.dir > 0 ? 'Compra' : 'Venta', fmtFecha(datosT(x.i0)), x.p0.toFixed(dg), fmtFecha(datosT(x.i1)), x.p1.toFixed(dg), x.motivo, x.barras, fmtPct(x.ret), x.eqFin.toFixed(2)];
        celdas.forEach(function(c, j){ var td = el('td', j === 8 ? tono(x.ret) : '', String(c)); tr.appendChild(td); });
        t.appendChild(tr);
      }
      var cont = el('div'); var envoltorio = el('div', 'bt-tabla-wrap'); envoltorio.appendChild(t); cont.appendChild(envoltorio);
      if (u.r.trades.length > lim) cont.appendChild(el('div', 'bt-nota', 'Se muestran las primeras ' + lim + ' de ' + u.r.trades.length + '. El CSV las incluye todas.'));
      if (!u.r.trades.length) cont.appendChild(el('div', 'bt-vacio', 'La estrategia no generó ninguna operación con estas reglas y estos datos.'));
      return cont;
    }

    /**
     * Dibuja la curva de capital frente a comprar y mantener y la de drawdown en dos gráficos sincronizados dentro
     * del panel de resultados.
     */
    function btDibujarCurvas(){
      var u = btUltimo, r = u.r, d = u.datos, ini = r.inicio, n = d.length;
      if (btCharts) { try { btCharts.eq.remove(); btCharts.dd.remove(); } catch (e) {} btCharts = null; }
      /**
       * Auxiliar de btDibujarCurvas: devuelve las opciones comunes de los gráficos de curvas, ampliadas con extra.
       */
      var opts = function(extra){ return Object.assign({ autoSize: true, layout: { background: { color: '#0d1117' }, textColor: '#d1d4dc', fontSize: 11 },
        grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } }, rightPriceScale: { borderColor: '#30363d', minimumWidth: 64 },
        timeScale: { borderColor: '#30363d', timeVisible: true, secondsVisible: false } }, extra || {}); };
      var ceq = LightweightCharts.createChart(document.getElementById('bt-eq'), opts());
      var cdd = LightweightCharts.createChart(document.getElementById('bt-dd'), opts());
      var s = ceq.addAreaSeries({ lineColor: '#2962ff', topColor: 'rgba(41,98,255,0.25)', bottomColor: 'rgba(41,98,255,0.02)', lineWidth: 2, priceLineVisible: false, priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });
      var bh = ceq.addLineSeries({ color: '#6e7681', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false, priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });
      var datosEq = [], datosBH = [], datosDD = [], base = d[Math.min(ini + 1, n - 1)].open;
      for (var i = ini; i < n; i++){
        if (r.curva[i] !== null) datosEq.push({ time: d[i].time, value: r.curva[i] });
        if (i > ini) datosBH.push({ time: d[i].time, value: r.capital * d[i].close / base });
        if (r.m.dd[i] !== null) datosDD.push({ time: d[i].time, value: r.m.dd[i] * 100 });
      }
      s.setData(datosEq); bh.setData(datosBH);
      var sd = cdd.addAreaSeries({ lineColor: '#f85149', topColor: 'rgba(248,81,73,0.02)', bottomColor: 'rgba(248,81,73,0.3)', lineWidth: 1, priceLineVisible: false, priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });
      sd.setData(datosDD);
      ceq.timeScale().fitContent(); cdd.timeScale().fitContent();
      var bloqueo = false;   // los dos gráficos se desplazan juntos
      /**
       * Auxiliar de btDibujarCurvas: hace que al desplazar el gráfico a también se desplace b, evitando bucles con la
       * bandera bloqueo.
       */
      function enlazar(a, b){ a.timeScale().subscribeVisibleLogicalRangeChange(function(rg){ if (bloqueo || !rg) return; bloqueo = true; b.timeScale().setVisibleLogicalRange(rg); bloqueo = false; }); }
      enlazar(ceq, cdd); enlazar(cdd, ceq);
      btCharts = { eq: ceq, dd: cdd };
    }

    // ---------- Marcas en el gráfico principal ----------
    /**
     * Crea las marcas de entrada y salida de las operaciones sobre el gráfico principal (flechas y círculos con el
     * resultado), limitadas a las 600 más recientes, y las aplica.
     */
    function btMarcar(){
      var u = btUltimo; if (!u) return;
      var ms = [], tIni = datosActuales.length ? datosActuales[0].time : 0, d = u.datos;
      u.r.trades.forEach(function(t){
        var t0 = d[t.i0].time, t1 = d[t.i1].time, largo = t.dir > 0, gan = t.pnl > 0;
        if (t1 < tIni) return;
        if (t0 >= tIni) ms.push({ time: t0, position: largo ? 'belowBar' : 'aboveBar', color: largo ? '#3fb950' : '#f85149', shape: largo ? 'arrowUp' : 'arrowDown', text: '' });
        ms.push({ time: t1, position: largo ? 'aboveBar' : 'belowBar', color: gan ? '#3fb950' : '#f85149', shape: 'circle', text: fmtPct(t.ret, 1) });
      });
      ms.sort(function(a, b){ return a.time - b.time; });
      marcasBT = ms.length > 600 ? ms.slice(-600) : ms;   // más de eso ilegible; se muestran las más recientes
      aplicarMarcasBT();
    }
    /** Aplica a la serie principal las marcas de backtest guardadas (o las borra si no hay). */
    function aplicarMarcasBT(){
      try { if (serie) serie.setMarkers(marcasBT || []); } catch (e) {}
    }

    /** Exporta las operaciones del último backtest a un CSV separado por punto y coma y lo descarga. */
    function btCSV(){
      var u = btUltimo; if (!u) return;
      var filas = ['n;lado;entrada;precio_entrada;salida;precio_salida;motivo;velas;resultado_pct;capital'];
      u.r.trades.forEach(function(t, i){
        filas.push([i + 1, t.dir > 0 ? 'compra' : 'venta', fmtFecha(datosT(t.i0)), t.p0.toFixed(DIGITS), fmtFecha(datosT(t.i1)), t.p1.toFixed(DIGITS), t.motivo, t.barras, (t.ret * 100).toFixed(4), t.eqFin.toFixed(2)].join(';'));
      });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob(['﻿' + filas.join('\n')], { type: 'text/csv;charset=utf-8' }));
      a.download = 'backtest_' + SIMBOLO + '_' + tfActual + '.csv'; document.body.appendChild(a); a.click();
      setTimeout(function(){ document.body.removeChild(a); URL.revokeObjectURL(a.href); }, 500);
    }

    // ---------- Abrir / cerrar ----------
    /** Abre la ventana del backtest, dibuja el formulario y, si hay un resultado previo, lo muestra. */
    function btAbrir(){
      btOverlay.style.display = 'flex';
      btPintarForm();
      if (btUltimo) btPintarResultados();
    }
    /** Cierra la ventana del backtest. */
    function btCerrar(){ btOverlay.style.display = 'none'; }
    // Eventos de la ventana: abrir con el botón, cerrar con la X, con clic fuera o con Escape (si no hay otra ventana abierta)
    document.getElementById('btn-bt-open').addEventListener('click', function(e){ e.stopPropagation(); btAbrir(); });
    document.getElementById('bt-close').addEventListener('click', btCerrar);
    btOverlay.addEventListener('click', function(e){ if (e.target === btOverlay) btCerrar(); });
    document.addEventListener('keydown', function(e){
      if (e.key === 'Escape' && btOverlay.style.display !== 'none' && cfgOverlay.style.display === 'none' && modalOverlay.style.display === 'none') btCerrar();
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
