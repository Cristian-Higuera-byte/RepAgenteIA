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
   ------------------------------- INICIO Piña y Jara 60_backtest_motor .JS ------------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Backtest: motor de simulación (reglas -> señales -> operaciones -> métricas). Sin acceso a la pantalla.
    //
    // Reglas de realismo (para que el resultado no salga artificialmente bueno):
    //  - La señal se evalúa al CIERRE de la vela y la orden se ejecuta en la APERTURA de la siguiente (sin mirar al futuro).
    //  - Las velas de MT5 son precios BID. Compras entran al ASK (bid + spread); las ventas entran al bid. El cierre de
    //    una compra es al bid y el de una venta al ask, así el spread se paga una vez por operación.
    //  - Slippage: se resta siempre en contra en entradas, stops y salidas a mercado (el take profit es una orden
    //    límite: se ejecuta a su precio, o a la apertura si hay hueco a favor).
    //  - Comisión: % del nominal en cada lado (entrada y salida).
    //  - Dentro de una misma vela no se sabe qué ocurrió antes: si toca stop y objetivo a la vez, se asume el STOP.
    //  - Si la vela abre más allá del stop (hueco), se sale a la apertura (peor que el nivel).
    //  - Los indicadores que usan velas futuras (fractales, ZigZag, regresión) no se pueden usar en reglas.

    // BT_NO_CAUSAL: indicadores que usan velas futuras y no se permiten en reglas
    var BACKTEST_NO_CAUSAL = { fractales: true, zigzag: true, regresion: true };
    // BT_OPS: operadores de comparación disponibles [valor, texto]
    var BACKTEST_OPERACIONES = [['gt', 'es mayor que'], ['lt', 'es menor que'], ['ge', 'es mayor o igual que'], ['le', 'es menor o igual que'],
                  ['cruzaArriba', 'cruza hacia arriba'], ['cruzaAbajo', 'cruza hacia abajo']];
    // BT_PRECIOS: operandos de precio disponibles [valor, texto]
    var BACKTEST_PRECIOS = [['close', 'Precio: Cierre'], ['open', 'Precio: Apertura'], ['high', 'Precio: Máximo'], ['low', 'Precio: Mínimo'],
                      ['hl2', 'Precio: Mediana (H+L)/2'], ['hlc3', 'Precio: Típico (H+L+C)/3'], ['volume', 'Volumen (ticks)']];

    // TITULO BT OPERANDO

    // ---------- Reglas -> señales ----------
    // Devuelve el valor de un operando en cada vela: { arr: [...], num: null } o { arr: null, num: valor }
    /**
     * Evalúa un operando de una condición (número fijo, precio o salida de indicador) sobre las velas. Devuelve {
     * arr, num }; usa una caché de indicadores y lanza Error si es inválido o usa velas futuras.
     */
    function backtestOperando(op, datos, cache){
      if (!op) throw new Error('Falta un operando en una condición.');
      if (op.k === 'num') {
        if (!isFinite(Number(op.v)) || op.v === '' || op.v === null) throw new Error('Un número de una condición no es válido.');
        return { arr: null, num: Number(op.v) };
      }
      if (op.k === 'precio') {
        return { arr: op.f === 'volume' ? datos.map(volumenDe) : precioDe(datos, op.f), num: null };
      }
      var tablaDatos = DEFS[op.id];
      if (!tablaDatos || BACKTEST_NO_CAUSAL[op.id]) throw new Error('El indicador «' + (tablaDatos ? tablaDatos.nombre : op.id) + '» no se puede usar en un backtest (usa velas futuras).');
      var p = validarParametros(tablaDatos, op.p), clave = op.id + JSON.stringify(p);
      var capas = cache[clave];
      if (!capas) capas = cache[clave] = tablaDatos.calc(datos, p);
      var c = capas[op.capa || 0];
      if (!c) throw new Error('Salida de indicador no válida en una condición.');
      var d = c.desp || 0;
      if (d < 0) throw new Error('«' + tablaDatos.nombre + '» con desplazamiento negativo usaría velas futuras; ponlo en 0 o más.');
      var arr = c.vals;
      if (d > 0) arr = arr.map(function(_, i){ return i - d >= 0 ? c.vals[i - d] : null; });   // un desplazamiento positivo solo usa datos pasados
      return { arr: arr, num: null };
    }
    // TITULO BT PRIMER VALIDO

    /**
     * Devuelve el índice desde el que un operando tiene datos (0 si es un número fijo, Infinity si nunca los tiene).
     */
    function backtestPrimerValido(o){
      if (o.arr === null) return 0;
      var i = primerValido(o.arr);
      return i < 0 ? Infinity : i;
    }
    // TITULO BT EVALUAR CONDICIONES

    // Lista de condiciones (unidas con 'y' u 'o') -> array de booleanos por vela, y la primera vela con todos los datos
    /**
     * Evalúa una lista de condiciones unidas con y/o sobre todas las velas. Devuelve { sig (booleanos por vela),
     * inicio (primera vela con datos), vacio }.
     */
    function backtestEvaluarCondiciones(conds, logica, datos, cache){
      var n = datos.length, out = new Array(n).fill(false), inicio = 0;
      if (!conds || !conds.length) return { sig: out, inicio: 0, vacio: true };
      var ev = conds.map(function(c){
        var a = backtestOperando(c.a, datos, cache), b = backtestOperando(c.b, datos, cache);
        var cruz = (c.op === 'cruzaArriba' || c.op === 'cruzaAbajo');
        inicio = Math.max(inicio, backtestPrimerValido(a) + (cruz ? 1 : 0), backtestPrimerValido(b) + (cruz ? 1 : 0));
        return { a: a, b: b, op: c.op };
      });
      /**
       * Auxiliar de btEvaluarCondiciones: devuelve el valor del operando o en la vela i (número fijo o elemento del
       * array).
       */
      function val(o, i){ return o.arr === null ? o.num : o.arr[i]; }
      for (var i = 0; i < n; i++){
        var resultados = ev.map(function(e){
          var x = val(e.a, i), y = val(e.b, i);
          if (!esNumero(x) || !esNumero(y)) return false;
          switch (e.op){
            case 'gt': return x > y;
            case 'lt': return x < y;
            case 'ge': return x >= y;
            case 'le': return x <= y;
            case 'cruzaArriba': { var x0 = val(e.a, i - 1), y0 = val(e.b, i - 1); return i > 0 && esNumero(x0) && esNumero(y0) && x0 <= y0 && x > y; }
            case 'cruzaAbajo': { var x1 = val(e.a, i - 1), y1 = val(e.b, i - 1); return i > 0 && esNumero(x1) && esNumero(y1) && x1 >= y1 && x < y; }
          }
          return false;
        });
        out[i] = (logica === 'o') ? resultados.some(function(r){ return r; }) : resultados.every(function(r){ return r; });
      }
      return { sig: out, inicio: inicio, vacio: false };
    }
    // TITULO BT SENALES

    /**
     * Traduce la estrategia est a señales por vela: entrada y salida de compra (el, xl) y de venta (es, xs), y la
     * primera vela utilizable. Lanza Error si falta una condición de entrada.
     */
    function backtestSenales(datos, est){
      var cache = {}, n = datos.length, vacio = new Array(n).fill(false), inicio = 0;
      var quiereLargo = est.dir !== 'corto', quiereCorto = est.dir !== 'largo';
      /**
       * Auxiliar de btSenales: evalúa un bloque de condiciones si está activo (y exige al menos una condición si es
       * obligatorio) y actualiza el inicio común.
       */
      function bloque(b, activo, nombre, obligatoria){
        if (!activo || !b) return { sig: vacio, inicio: 0 };
        var r = backtestEvaluarCondiciones(b.cond, b.logica, datos, cache);
        if (obligatoria && r.vacio) throw new Error('Añade al menos una condición de ' + nombre + '.');
        inicio = Math.max(inicio, r.inicio);
        return r;
      }
      var el = bloque(est.largo && est.largo.entrada, quiereLargo, 'entrada en compra', true);
      var xl = bloque(est.largo && est.largo.salida, quiereLargo, 'salida en compra', false);
      var es = bloque(est.corto && est.corto.entrada, quiereCorto, 'entrada en venta', true);
      var xs = bloque(est.corto && est.corto.salida, quiereCorto, 'salida en venta', false);
      return { el: el.sig, xl: xl.sig, es: es.sig, xs: xs.sig, inicio: inicio };
    }

    // TITULO BT SIMULAR

    // ---------- Simulación ----------
    // est: { dir, sl, tp, trail, maxBarras, invertir, tam: { modo, valor, apalMax } }
    // cost: { spreadModo ('fijo'|'mt5'), spreadPips, slipPips, comision, pip, punto }
    /**
     * Simula la estrategia con las señales: ejecuta las órdenes en la apertura siguiente, aplica spread, slippage y
     * comisión, gestiona stop, objetivo, trailing y tiempo máximo, y valora la cuenta vela a vela. Devuelve { trades,
     * curva, ruina }.
     */
    function backtestSimular(datos, sig, est, cost, capital){
      var n = datos.length, inicio = sig.inicio, eq = capital, trades = [], curva = new Array(n).fill(null), pos = null, pend = null, ruina = false;
      var slip = (cost.slipPips || 0) * cost.pip, comis = (cost.comision || 0) / 100;
      /** Auxiliar de btSimular: devuelve el spread en precio de la vela i (histórico de MT5 o fijo en pips). */
      function spread(i){
        if (cost.spreadModo === 'mt5' && datos[i].spread > 0) return datos[i].spread * cost.punto;
        return (cost.spreadPips || 0) * cost.pip;
      }
      /**
       * Auxiliar de btSimular: abre una posición de dirección dir en la apertura de la vela i, con precio de entrada,
       * tamaño, stop y objetivo, y descuenta la comisión de entrada.
       */
      function abrir(dir, i){
        var b = datos[i], sp = spread(i);
        var fill = dir > 0 ? b.open + sp + slip : b.open - slip;
        var f = est.tam.modo === 'riesgo' ? Math.min(est.tam.apalMax, (est.tam.valor / 100) / (est.sl / 100)) : est.tam.valor / 100;
        pos = { dir: dir, idx: i, fill: fill, f: f, eqAntes: eq, sl: est.sl > 0 ? fill * (1 - dir * est.sl / 100) : null,
                tp: est.tp > 0 ? fill * (1 + dir * est.tp / 100) : null, extremo: fill, trailNivel: null, barras: 0 };
        eq -= eq * f * comis;   // comisión de entrada
        pos.eqBase = eq;
      }
      /**
       * Auxiliar de btSimular: cierra la posición al precio dado en la vela i por el motivo indicado, descuenta la
       * comisión de salida, registra la operación y detecta la ruina.
       */
      function cerrar(precio, i, motivo){
        var ret = pos.f * pos.dir * (precio / pos.fill - 1);
        eq = pos.eqBase * (1 + ret);
        eq -= Math.max(eq, 0) * pos.f * comis;   // comisión de salida
        if (eq < 0) eq = 0;
        trades.push({ dir: pos.dir, i0: pos.idx, i1: i, p0: pos.fill, p1: precio, motivo: motivo, barras: pos.barras,
                      ret: pos.eqAntes > 0 ? eq / pos.eqAntes - 1 : -1, pnl: eq - pos.eqAntes, f: pos.f, eqFin: eq });
        pos = null;
        if (eq <= 0) ruina = true;
      }
      for (var i = inicio; i < n && !ruina; i++){
        var b = datos[i], sp = spread(i);
        // 1) órdenes pendientes de la señal de la vela anterior: se ejecutan a la apertura
        if (pend){
          if (pos && pend.salir) cerrar(pos.dir > 0 ? b.open - slip : b.open + sp + slip, i, pend.motivo);
          if (!pos && pend.entrar && !ruina) abrir(pend.entrar, i);
          pend = null;
        }
        // 2) gestión dentro de la vela: stop, objetivo, trailing y tiempo
        if (pos){
          pos.barras++;
          var d = pos.dir, nivelStopLoss = pos.sl;
          if (pos.trailNivel !== null) nivelStopLoss = (nivelStopLoss === null) ? pos.trailNivel : (d > 0 ? Math.max(nivelStopLoss, pos.trailNivel) : Math.min(nivelStopLoss, pos.trailNivel));
          var cerrada = false;
          if (nivelStopLoss !== null){
            if (d > 0){
              if (b.open <= nivelStopLoss && i > pos.idx) { cerrar(b.open - slip, i, 'Stop (hueco)'); cerrada = true; }
              else if (b.low <= nivelStopLoss) { cerrar(Math.min(nivelStopLoss, b.open) - slip, i, pos.trailNivel !== null && nivelStopLoss === pos.trailNivel ? 'Trailing' : 'Stop'); cerrada = true; }
            } else {
              if (b.open + sp >= nivelStopLoss && i > pos.idx) { cerrar(b.open + sp + slip, i, 'Stop (hueco)'); cerrada = true; }
              else if (b.high + sp >= nivelStopLoss) { cerrar(Math.max(nivelStopLoss, b.open + sp) + slip, i, pos.trailNivel !== null && nivelStopLoss === pos.trailNivel ? 'Trailing' : 'Stop'); cerrada = true; }
            }
          }
          if (!cerrada && pos.tp !== null){
            if (d > 0){
              if (b.open >= pos.tp && i > pos.idx) { cerrar(b.open, i, 'Objetivo (hueco)'); cerrada = true; }
              else if (b.high >= pos.tp) { cerrar(pos.tp, i, 'Objetivo'); cerrada = true; }
            } else {
              if (b.open + sp <= pos.tp && i > pos.idx) { cerrar(b.open + sp, i, 'Objetivo (hueco)'); cerrada = true; }
              else if (b.low + sp <= pos.tp) { cerrar(pos.tp, i, 'Objetivo'); cerrada = true; }
            }
          }
          if (!cerrada && est.maxBarras > 0 && pos.barras >= est.maxBarras){
            cerrar(d > 0 ? b.close - slip : b.close + sp + slip, i, 'Tiempo máximo'); cerrada = true;
          }
          if (!cerrada && est.trail > 0){   // el trailing se ajusta con los extremos de esta vela y rige desde la siguiente
            pos.extremo = d > 0 ? Math.max(pos.extremo, b.high) : Math.min(pos.extremo, b.low);
            pos.trailNivel = pos.extremo * (1 - d * est.trail / 100);
          }
        }
        // 3) valor de la cuenta al cierre (la posición abierta se valora al precio de salida: bid en compras, ask en ventas)
        if (pos){
          var liq = pos.dir > 0 ? b.close : b.close + sp;
          curva[i] = pos.eqBase * (1 + pos.f * pos.dir * (liq / pos.fill - 1));
        } else curva[i] = eq;
        // 4) señales al cierre de esta vela -> orden para la apertura de la siguiente
        if (i < n - 1 && !ruina){
          if (pos){
            var sale = pos.dir > 0 ? sig.xl[i] : sig.xs[i];
            var contraria = est.invertir && est.dir === 'ambos' && (pos.dir > 0 ? sig.es[i] : sig.el[i]);
            if (sale || contraria) pend = { salir: true, motivo: contraria ? 'Señal contraria' : 'Señal de salida', entrar: contraria ? -pos.dir : 0 };
          } else {
            var l = est.dir !== 'corto' && sig.el[i], s = est.dir !== 'largo' && sig.es[i];
            if (l && !s) pend = { entrar: 1 };
            else if (s && !l) pend = { entrar: -1 };
          }
        }
      }
      if (pos){   // al acabar los datos se cierra lo que quede abierto
        var u = datos[n - 1], spu = spread(n - 1);
        cerrar(pos.dir > 0 ? u.close - slip : u.close + spu + slip, n - 1, 'Fin de datos');
        curva[n - 1] = eq;
      }
      if (ruina) for (var k = i; k < n; k++) curva[k] = 0;
      return { trades: trades, curva: curva, ruina: ruina };
    }

    // TITULO BT METRICAS

    // ---------- Métricas ----------
    /**
     * Calcula las métricas de una simulación: rentabilidad, anualizada, win rate, profit factor, drawdown, Sharpe,
     * mejor y peor operación, rachas, exposición y comparación con comprar y mantener.
     */
    function backtestMetricas(datos, sim, inicio, capital, bh){
      var n = datos.length, trades = sim.trades, curva = sim.curva;
      var eqFin = curva[n - 1] === null ? capital : curva[n - 1];
      var anios = (datos[n - 1].time - datos[inicio].time) / (365.25 * 86400);
      var ganadoras = trades.filter(function(t){ return t.pnl > 0; }), perdedoras = trades.filter(function(t){ return t.pnl <= 0; });
      var sumaG = ganadoras.reduce(function(s, t){ return s + t.pnl; }, 0), sumaP = perdedoras.reduce(function(s, t){ return s + t.pnl; }, 0);
      // drawdown sobre la curva de capital (valorada vela a vela)
      var pico = capital, drawdownMaximo = 0, dd = new Array(n).fill(null);
      for (var i = inicio; i < n; i++){
        var v = curva[i]; if (v === null) continue;
        if (v > pico) pico = v;
        dd[i] = pico > 0 ? v / pico - 1 : -1;
        if (dd[i] < drawdownMaximo) drawdownMaximo = dd[i];
      }
      // Sharpe: rentabilidad por vela (sin tasa libre de riesgo), anualizada con las velas reales por año
      var rets = [];
      for (var j = inicio + 1; j < n; j++){ if (curva[j] !== null && curva[j-1] !== null && curva[j-1] > 0) rets.push(curva[j] / curva[j-1] - 1); }
      var media = rets.length ? rets.reduce(function(s, x){ return s + x; }, 0) / rets.length : 0;
      var varianza = rets.length > 1 ? rets.reduce(function(s, x){ return s + (x - media) * (x - media); }, 0) / (rets.length - 1) : 0;
      var ppy = anios > 0 ? rets.length / anios : 0;
      var sharpe = (varianza > 0 && ppy > 0) ? media / Math.sqrt(varianza) * Math.sqrt(ppy) : null;
      var mejor = null, peor = null, rachaP = 0, rachaMaximo = 0, rachaG = 0, rachaGMaximo = 0, barrasEnMercado = 0;
      trades.forEach(function(t){
        if (!mejor || t.ret > mejor.ret) mejor = t;
        if (!peor || t.ret < peor.ret) peor = t;
        if (t.pnl > 0) { rachaG++; rachaP = 0; } else { rachaP++; rachaG = 0; }
        rachaMaximo = Math.max(rachaMaximo, rachaP); rachaGMaximo = Math.max(rachaGMaximo, rachaG);
        barrasEnMercado += t.barras;
      });
      var rentab = eqFin / capital - 1;
      return {
        capitalFinal: eqFin, rentabilidad: rentab,
        anualizada: (anios >= 0.25 && eqFin > 0) ? Math.pow(eqFin / capital, 1 / anios) - 1 : null,
        operaciones: trades.length, ganadoras: ganadoras.length, perdedoras: perdedoras.length,
        winRate: trades.length ? ganadoras.length / trades.length : null,
        profitFactor: sumaP < 0 ? sumaG / -sumaP : (sumaG > 0 ? Infinity : null),
        maxDrawdown: drawdownMaximo, sharpe: sharpe, mejor: mejor, peor: peor,
        mediaOp: trades.length ? trades.reduce(function(s, t){ return s + t.ret; }, 0) / trades.length : null,
        mediaGana: ganadoras.length ? ganadoras.reduce(function(s, t){ return s + t.ret; }, 0) / ganadoras.length : null,
        mediaPierde: perdedoras.length ? perdedoras.reduce(function(s, t){ return s + t.ret; }, 0) / perdedoras.length : null,
        rachaPerdedoraMax: rachaMaximo, rachaGanadoraMax: rachaGMaximo,
        exposicion: (n - inicio) > 0 ? barrasEnMercado / (n - inicio) : 0,
        barrasMedias: trades.length ? barrasEnMercado / trades.length : null,
        buyHold: bh, anios: anios, dd: dd, ruina: sim.ruina
      };
    }

    // TITULO BT EJECUTAR

    // Ejecuta todo: devuelve { m (con costes), mSinCostes, trades, curva, inicio, ... } o lanza un Error con un mensaje claro
    /**
     * Orquesta el backtest: valida los datos, genera señales, simula con y sin costes y calcula métricas. Devuelve {
     * m, mSinCostes, trades, curva, inicio, capital } o lanza un Error con un mensaje claro.
     */
    function backtestEjecutar(datos, est, cost, capital){
      if (!datos || datos.length < 50) throw new Error('Hay muy pocas velas para probar la estrategia.');
      if (est.tam.modo === 'riesgo' && !(est.sl > 0)) throw new Error('El tamaño por riesgo necesita un Stop Loss (%).');
      var sig = backtestSenales(datos, est), inicio = sig.inicio;
      if (!isFinite(inicio) || inicio >= datos.length - 2) throw new Error('Los indicadores elegidos no tienen datos suficientes con las velas cargadas.');
      var n = datos.length, bh = datos[n - 1].close / datos[inicio + 1].open - 1;
      var sim = backtestSimular(datos, sig, est, cost, capital), m = backtestMetricas(datos, sim, inicio, capital, bh);
      var sinCostes = Object.assign({}, cost, { spreadPips: 0, slipPips: 0, comision: 0, spreadModo: 'fijo' });
      var sim0 = backtestSimular(datos, sig, est, sinCostes, capital), m0 = backtestMetricas(datos, sim0, inicio, capital, bh);
      return { m: m, mSinCostes: m0, trades: sim.trades, curva: sim.curva, inicio: inicio, capital: capital };
    }

/* -------------------------------------------------------------------------------------------------------
   -------------------------------- FIN Piña y Jara 60_backtest_motor .JS --------------------------------
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
