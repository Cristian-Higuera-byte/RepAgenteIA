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
   -------------------------------- INICIO Piña y Jara 62_replay_motor .JS -------------------------------
   ------------------------------------------------------------------------------------------------------- */

    // =====================================================================================================
    // REPLAY (práctica sobre el pasado) · MOTOR DE LA CUENTA DE PRÁCTICA
    // Funciones puras sobre un objeto "cuenta"; no tocan el DOM ni el gráfico (eso lo hace 63_replay_ui.js).
    // La cuenta puede tener VARIAS posiciones a la vez, una por símbolo (cta.pos[simbolo]). Usa la misma
    // contabilidad que el backtest: cada posición expone una fracción f del capital disponible al abrirla y su
    // resultado es f x variación del precio, con el mismo trato de spread, huecos y stops. El capital solo cambia
    // cuando se cierra una posición (resultado realizado); el patrimonio suma además lo no realizado.
    // =====================================================================================================

    /**
     * Crea una cuenta de práctica vacía con el capital indicado: sin posiciones abiertas (cta.pos es un objeto
     * símbolo -> posición) y sin operaciones cerradas.
     */
    function rpCuentaNueva(capital){
      return { capital0: capital, capital: capital, pos: {}, trades: [] };
    }

    /**
     * Devuelve el spread de una vela en unidades de precio: el spread histórico de MT5 (en puntos) por el tamaño
     * del punto (10 elevado a menos dec). Si la vela no trae spread devuelve 0 (sin costo de spread).
     */
    function rpSpread(b, dec){
      return (b && b.spread > 0) ? b.spread * Math.pow(10, -dec) : 0;
    }

    /**
     * Calcula los precios de stop loss y take profit de una posición a partir de porcentajes sobre el precio de
     * entrada. Un porcentaje vacío, 0 o inválido significa "sin nivel" (null). Devuelve { sl, tp }.
     */
    function rpNiveles(dir, fill, slPct, tpPct){
      return {
        sl: slPct > 0 ? fill * (1 - dir * slPct / 100) : null,
        tp: tpPct > 0 ? fill * (1 + dir * tpPct / 100) : null
      };
    }

    /**
     * Abre una posición del símbolo sym al precio de cierre de la vela b. dir es 1 (compra) o -1 (venta); la
     * compra paga el spread (entra al ask) y la venta entra al bid. tamPct es el % del capital disponible que se
     * expone (100 = todo el capital, sin apalancamiento) y dec son los decimales del precio del símbolo. Devuelve
     * true si abrió; false si ese símbolo ya tiene posición, no queda capital o los datos no son válidos.
     */
    function rpAbrir(cta, sym, dir, b, idx, tamPct, slPct, tpPct, dec){
      if (cta.pos[sym] || cta.capital <= 0 || !b || !(tamPct > 0)) return false;
      var fill = dir > 0 ? b.close + rpSpread(b, dec) : b.close;
      var n = rpNiveles(dir, fill, slPct, tpPct);
      cta.pos[sym] = { sym: sym, dir: dir, idx: idx, t: b.time, fill: fill, f: tamPct / 100, eqBase: cta.capital,
                       sl: n.sl, tp: n.tp, barras: 0, dec: dec };
      return true;
    }

    /**
     * Cambia el stop loss y el take profit de la posición abierta del símbolo (en % sobre su precio de entrada).
     * No hace nada si ese símbolo no tiene posición.
     */
    function rpCambiarNiveles(cta, sym, slPct, tpPct){
      var p = cta.pos[sym];
      if (!p) return;
      var n = rpNiveles(p.dir, p.fill, slPct, tpPct);
      p.sl = n.sl; p.tp = n.tp;
    }

    /**
     * Cierra la posición del símbolo al precio indicado (ya con el spread aplicado por quien llama): la mueve a la
     * lista de operaciones con su resultado y suma ese resultado al capital. Devuelve la operación cerrada o null.
     */
    function rpCerrar(cta, sym, precio, idx, b, motivo){
      var p = cta.pos[sym];
      if (!p) return null;
      var pnl = p.eqBase * p.f * p.dir * (precio / p.fill - 1);
      if (cta.capital + pnl < 0) pnl = -cta.capital;   // no se puede perder más del capital
      var op = { sym: sym, dir: p.dir, i0: p.idx, i1: idx, t0: p.t, t1: b ? b.time : p.t, p0: p.fill, p1: precio,
                 motivo: motivo, barras: p.barras, ret: p.eqBase > 0 ? pnl / p.eqBase : -1, pnl: pnl, f: p.f, dec: p.dec };
      cta.capital += pnl;
      delete cta.pos[sym];
      cta.trades.push(op);
      return op;
    }

    /**
     * Cierra a mano la posición del símbolo al precio de cierre de la vela b: la compra sale al bid (el cierre) y
     * la venta paga el spread. Devuelve la operación cerrada o null si no había posición.
     */
    function rpCerrarAMercado(cta, sym, b, idx){
      var p = cta.pos[sym];
      if (!p) return null;
      return rpCerrar(cta, sym, p.dir > 0 ? b.close : b.close + rpSpread(b, p.dec), idx, b, 'Cierre manual');
    }

    /**
     * Procesa una vela NUEVA del símbolo contra su posición abierta: revisa primero el stop loss y luego el take
     * profit (criterio conservador), con tratamiento de huecos de apertura. Devuelve la operación cerrada si la
     * vela tocó algún nivel, o null si la posición sigue abierta (o no había posición).
     */
    function rpProcesarVela(cta, sym, b, idx){
      var p = cta.pos[sym];
      if (!p) return null;
      p.barras++;
      var sp = rpSpread(b, p.dec), d = p.dir;
      if (p.sl !== null){
        if (d > 0){
          if (b.open <= p.sl) return rpCerrar(cta, sym, b.open, idx, b, 'Stop (hueco)');
          if (b.low <= p.sl) return rpCerrar(cta, sym, Math.min(p.sl, b.open), idx, b, 'Stop');
        } else {
          if (b.open + sp >= p.sl) return rpCerrar(cta, sym, b.open + sp, idx, b, 'Stop (hueco)');
          if (b.high + sp >= p.sl) return rpCerrar(cta, sym, Math.max(p.sl, b.open + sp), idx, b, 'Stop');
        }
      }
      if (p.tp !== null){
        if (d > 0){
          if (b.open >= p.tp) return rpCerrar(cta, sym, b.open, idx, b, 'Objetivo (hueco)');
          if (b.high >= p.tp) return rpCerrar(cta, sym, p.tp, idx, b, 'Objetivo');
        } else {
          if (b.open + sp <= p.tp) return rpCerrar(cta, sym, b.open + sp, idx, b, 'Objetivo (hueco)');
          if (b.low + sp <= p.tp) return rpCerrar(cta, sym, p.tp, idx, b, 'Objetivo');
        }
      }
      return null;
    }

    /**
     * Devuelve el resultado no realizado de la posición del símbolo con la vela b (liquidada al bid en compras y
     * al ask en ventas). 0 si no hay posición o no hay vela.
     */
    function rpFlotante(cta, sym, b){
      var p = cta.pos[sym];
      if (!p || !b) return 0;
      var liq = p.dir > 0 ? b.close : b.close + rpSpread(b, p.dec);
      return p.eqBase * p.f * p.dir * (liq / p.fill - 1);
    }

    /**
     * Devuelve el patrimonio (equity): el capital realizado más el resultado no realizado de todas las posiciones
     * abiertas. ultimas es un objeto símbolo -> última vela visible de ese símbolo.
     */
    function rpEquity(cta, ultimas){
      var eq = cta.capital;
      Object.keys(cta.pos).forEach(function(s){ eq += rpFlotante(cta, s, ultimas[s]); });
      return eq;
    }

    /**
     * Resume las operaciones cerradas: cantidad, ganadoras, porcentaje de aciertos y resultado total (en dinero y
     * en % del capital inicial).
     */
    function rpResumen(cta){
      var n = cta.trades.length, g = 0, total = 0;
      cta.trades.forEach(function(t){ if (t.pnl > 0) g++; total += t.pnl; });
      return { n: n, ganadas: g, acierto: n ? g / n * 100 : 0, total: total,
               totalPct: cta.capital0 > 0 ? total / cta.capital0 * 100 : 0 };
    }

/* -------------------------------------------------------------------------------------------------------
   --------------------------------- FIN Piña y Jara 62_replay_motor .JS ---------------------------------
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
