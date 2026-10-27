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
   ---------------------------- INICIO Piña y Jara 33_indicadores_catalogo .JS ---------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Indicadores: catálogo (qué indicadores existen, sus parámetros, colores y cómo se calculan)
    // Para añadir un indicador basta con otra llamada a `def({...})` al final de la lista:
    //   id, nombre, corto (nombre en el título), grupo, destino ('precio' = sobre el gráfico, 'panel' = ventana propia),
    //   desc, params [..], capas [[nombre, color, tipo]] (tipo: 'linea' por defecto, 'puntos' o 'hist'),
    //   calc(datos, p) -> una capa por cada entrada de `capas`: { vals, cols?, desp?, pasos? }
    //   y opcionales: niveles [..], rango [min, max], dec (decimales, 'auto'), etiq, sug (periodos sugeridos).
    // DEFS: catálogo por id; LISTA_DEFS: el mismo catálogo en orden de alta
    var DEFS = {};
    var LISTA_DEFS = [];
    // GRUPOS_IND: categorías que muestra la ventana de selección
    var GRUPOS_IND = ['Tendencia', 'Osciladores', 'Volatilidad', 'Volumen', 'Bill Williams', 'Niveles'];
    // PALETA_IND: colores que se asignan a las segundas y siguientes instancias de un mismo indicador
    var PALETA_IND = ['#f5c518', '#3399ff', '#a78bfa', '#ff6600', '#e056fd', '#26a69a', '#ef5350', '#00bcd4'];

    /** Registra la definición d de un indicador en el catálogo (DEFS por id y LISTA_DEFS en orden) y la devuelve. */
    function def(d){ DEFS[d.id] = d; LISTA_DEFS.push(d); return d; }
    /**
     * Crea la descripción de un parámetro numérico: clave k, nombre n, valor por defecto d, límites min y max y paso
     * (1 por defecto).
     */
    function pNum(k, n, d, min, max, paso){ return { k: k, n: n, t: 'num', d: d, min: min, max: max, paso: paso || 1 }; }
    /**
     * Crea la descripción de un parámetro de lista desplegable: clave k, nombre n, valor por defecto d y opciones o
     * [[valor, texto]].
     */
    function pSel(k, n, d, o){ return { k: k, n: n, t: 'sel', d: d, o: o }; }

    // OPC_PRECIO: opciones del parámetro «Aplicar a» [valor, texto]
    var OPC_PRECIO = [['close', 'Cierre'], ['open', 'Apertura'], ['high', 'Máximo'], ['low', 'Mínimo'], ['hl2', 'Mediana (H+L)/2'],
                      ['hlc3', 'Típico (H+L+C)/3'], ['ohlc4', 'Promedio (O+H+L+C)/4'], ['hlcc4', 'Ponderado (H+L+2C)/4']];
    // OPC_MA: métodos de media móvil disponibles [valor, texto]
    var OPC_MA = [['sma', 'Simple'], ['ema', 'Exponencial'], ['smma', 'Suavizada'], ['lwma', 'Ponderada lineal']];
    /**
     * Parámetro estándar «Aplicar a» (tipo de precio de entrada) con d como valor por defecto (cierre si no se
     * indica).
     */
    function pPrecio(d){ return pSel('precio', 'Aplicar a', d || 'close', OPC_PRECIO); }
    /** Parámetro estándar «Periodo» con valor por defecto d y máximo max (500 si no se indica). */
    function pPeriodo(d, max){ return pNum('periodo', 'Periodo', d, 1, max || 500, 1); }
    /** Parámetro estándar «Desplazamiento (velas)» entre -100 y 100, por defecto 0. */
    function pDesp(){ return pNum('desp', 'Desplazamiento (velas)', 0, -100, 100, 1); }

    // Colores de histograma: más intenso cuando la barra crece en su sentido
    /**
     * Calcula los colores de un histograma con signo: verde o rojo según el signo y más intenso cuando la barra crece
     * en su sentido. Devuelve un array de colores alineado.
     */
    function colHistSigno(vals){
      return vals.map(function(h, i){
        if (!esNum(h)) return null;
        var prev = (i > 0 && esNum(vals[i-1])) ? vals[i-1] : 0;
        return h >= 0 ? (h >= prev ? 'rgba(63,185,80,0.9)' : 'rgba(63,185,80,0.45)')
                      : (h <= prev ? 'rgba(248,81,73,0.9)' : 'rgba(248,81,73,0.45)');
      });
    }
    // Verde si sube respecto a la barra anterior, rojo si baja (Awesome, Accelerator…)
    /**
     * Calcula los colores de un histograma por dirección: verde si sube respecto a la barra anterior y rojo si baja
     * (Awesome, Accelerator). Devuelve un array de colores alineado.
     */
    function colHistSube(vals){
      return vals.map(function(h, i){
        if (!esNum(h)) return null;
        var prev = (i > 0 && esNum(vals[i-1])) ? vals[i-1] : h;
        return h >= prev ? '#3fb950' : '#f85149';
      });
    }

    // ================= TENDENCIA (sobre el precio) =================
    /**
     * Atajo para registrar una media móvil sobre el precio: recibe id, nombre, abreviatura, función de cálculo
     * fn(array, parámetros, velas), color, descripción, parámetros opcionales y periodos sugeridos.
     */
    function defMedia(id, nombre, corto, fn, color, desc, params, sug){
      def({ id: id, nombre: nombre, corto: corto, grupo: 'Tendencia', destino: 'precio', desc: desc, sug: sug || null,
        params: params || [pPeriodo(20), pPrecio(), pDesp()], capas: [[corto, color]],
        calc: function(d, p){ return [{ vals: fn(precioDe(d, p.precio), p, d), desp: p.desp }]; } });
    }
    // SUG_MA: periodos sugeridos para las siguientes instancias de una media móvil
    var SUG_MA = [20, 50, 200, 100, 10, 5, 30];
    // Indicador «SMA — Media móvil simple» (id sma)
    defMedia('sma', 'SMA — Media móvil simple', 'SMA', function(a, p){ return mSMA(a, p.periodo); }, '#f5c518', 'Promedio simple de los últimos N cierres.', null, SUG_MA);
    // Indicador «EMA — Media móvil exponencial» (id ema)
    defMedia('ema', 'EMA — Media móvil exponencial', 'EMA', function(a, p){ return mEMA(a, p.periodo); }, '#ff6600', 'Da más peso a los precios recientes.', null, SUG_MA);
    // Indicador «SMMA — Media móvil suavizada» (id smma)
    defMedia('smma', 'SMMA — Media móvil suavizada', 'SMMA', function(a, p){ return mSMMA(a, p.periodo); }, '#00bcd4', 'Media suavizada de Wilder (RMA).', null, SUG_MA);
    // Indicador «LWMA — Media móvil ponderada» (id lwma)
    defMedia('lwma', 'LWMA — Media móvil ponderada', 'LWMA', function(a, p){ return mLWMA(a, p.periodo); }, '#e056fd', 'Ponderación lineal: la última vela pesa N, la anterior N-1…', null, SUG_MA);
    // Indicador «DEMA — Media exponencial doble» (id dema)
    defMedia('dema', 'DEMA — Media exponencial doble', 'DEMA', function(a, p){ return mDEMA(a, p.periodo); }, '#26a69a', 'Reduce el retraso de la EMA.', null, SUG_MA);
    // Indicador «TEMA — Media exponencial triple» (id tema)
    defMedia('tema', 'TEMA — Media exponencial triple', 'TEMA', function(a, p){ return mTEMA(a, p.periodo); }, '#ab47bc', 'Aún menos retraso que la DEMA.', null, SUG_MA);
    // Indicador «HMA — Media de Hull» (id hma)
    defMedia('hma', 'HMA — Media de Hull', 'HMA', function(a, p){ return mHMA(a, p.periodo); }, '#ff7043', 'Media muy suave y rápida.', null, SUG_MA);
    // Indicador «AMA — Media adaptativa (Kaufman)» (id ama)
    defMedia('ama', 'AMA — Media adaptativa (Kaufman)', 'AMA', function(a, p){ return mAMA(a, p.periodo, p.rapida, p.lenta); }, '#26c6da',
      'Se acelera con tendencia y se frena en rango.', [pPeriodo(10), pNum('rapida', 'Periodo rápido', 2, 1, 100, 1), pNum('lenta', 'Periodo lento', 30, 2, 300, 1), pPrecio(), pDesp()]);
    // Indicador «VIDYA — Media dinámica de índice variable» (id vidya)
    defMedia('vidya', 'VIDYA — Media dinámica de índice variable', 'VIDYA', function(a, p){ return mVIDYA(a, p.cmo, p.periodo); }, '#9ccc65',
      'Media que ajusta su velocidad según la volatilidad (CMO).', [pNum('cmo', 'Periodo CMO', 9, 2, 200, 1), pPeriodo(12), pPrecio(), pDesp()]);
    // Indicador «FRAMA — Media adaptativa fractal» (id frama)
    defMedia('frama', 'FRAMA — Media adaptativa fractal', 'FRAMA', function(a, p, d){ return mFRAMA(d, p.periodo); }, '#ffa726',
      'Media que usa la dimensión fractal del precio.', [pPeriodo(14, 200), pDesp()]);

    // Indicador «Ichimoku Kinko Hyo» (id ichimoku)
    def({ id: 'ichimoku', nombre: 'Ichimoku Kinko Hyo', corto: 'Ichimoku', grupo: 'Tendencia', destino: 'precio', etiq: false,
      desc: 'Tenkan, Kijun, nube (Senkou A/B) y Chikou.',
      params: [pNum('tenkan', 'Tenkan-sen', 9, 1, 200, 1), pNum('kijun', 'Kijun-sen', 26, 1, 300, 1), pNum('senkou', 'Senkou Span B', 52, 1, 500, 1)],
      capas: [['Tenkan-sen', '#2962ff'], ['Kijun-sen', '#b71c1c'], ['Senkou A', '#3fb950'], ['Senkou B', '#f85149'], ['Chikou', '#a78bfa']],
      calc: function(d, p){
        var h = columna(d, 'high'), l = columna(d, 'low'), c = precioDe(d, 'close');
        /** Auxiliar de Ichimoku: punto medio entre el máximo y el mínimo de las últimas n velas. */
        function medio(n){ return mOp(mMax(h, n), mMin(l, n), function(x, y){ return (x + y) / 2; }); }
        var ten = medio(p.tenkan), kij = medio(p.kijun);
        return [{ vals: ten }, { vals: kij },
                { vals: mOp(ten, kij, function(x, y){ return (x + y) / 2; }), desp: p.kijun },
                { vals: medio(p.senkou), desp: p.kijun },
                { vals: c, desp: -p.kijun }];
      } });

    // Indicador «Parabolic SAR» (id sar)
    def({ id: 'sar', nombre: 'Parabolic SAR', corto: 'SAR', grupo: 'Tendencia', destino: 'precio',
      desc: 'Puntos de parada y reversa; verde = alcista, rojo = bajista.',
      params: [pNum('paso', 'Paso', 0.02, 0.001, 1, 0.001), pNum('maximo', 'Máximo', 0.2, 0.01, 2, 0.01)],
      capas: [['SAR', '#f85149', 'puntos']],
      calc: function(d, p){ var r = mSAR(d, p.paso, p.maximo); return [{ vals: r.vals, cols: r.cols }]; } });

    // Indicador «Supertrend» (id supertrend)
    def({ id: 'supertrend', nombre: 'Supertrend', corto: 'Supertrend', grupo: 'Tendencia', destino: 'precio',
      desc: 'Línea de tendencia basada en ATR; cambia de color al girar.',
      params: [pPeriodo(10, 200), pNum('mult', 'Multiplicador ATR', 3, 0.1, 20, 0.1)],
      capas: [['Supertrend', '#3fb950']],
      calc: function(d, p){ var r = mSupertrend(d, p.periodo, p.mult); return [{ vals: r.vals, cols: r.cols }]; } });

    // Indicador «VWAP — Precio medio ponderado por volumen» (id vwap)
    def({ id: 'vwap', nombre: 'VWAP — Precio medio ponderado por volumen', corto: 'VWAP', grupo: 'Tendencia', destino: 'precio',
      desc: 'Precio medio del día ponderado por volumen (se reinicia cada día, UTC).',
      params: [], capas: [['VWAP', '#00e5ff']], calc: function(d){ return [{ vals: mVWAP(d) }]; } });

    // Indicador «Canal de regresión lineal» (id regresion)
    def({ id: 'regresion', nombre: 'Canal de regresión lineal', corto: 'Regresión', grupo: 'Tendencia', destino: 'precio', etiq: false,
      desc: 'Recta de regresión de las últimas N velas con canal de desviación.',
      params: [pNum('periodo', 'Velas', 100, 5, 2000, 1), pNum('desv', 'Desviaciones', 2, 0.1, 10, 0.1)],
      capas: [['Regresión', '#ff9800'], ['Superior', '#2962ff'], ['Inferior', '#2962ff']],
      calc: function(d, p){ var r = mRegresion(d, p.periodo, p.desv); return [{ vals: r.med }, { vals: r.sup }, { vals: r.inf }]; } });

    // ================= VOLATILIDAD =================
    // Indicador «Bandas de Bollinger» (id bollinger)
    def({ id: 'bollinger', nombre: 'Bandas de Bollinger', corto: 'BB', grupo: 'Volatilidad', destino: 'precio', etiq: false,
      desc: 'Media móvil con bandas a N desviaciones típicas.',
      params: [pPeriodo(20), pNum('desv', 'Desviaciones', 2, 0.1, 10, 0.1), pPrecio(), pDesp()],
      capas: [['Superior', '#2962ff'], ['Media', '#ff9800'], ['Inferior', '#2962ff']],
      calc: function(d, p){ var b = mBollinger(precioDe(d, p.precio), p.periodo, p.desv); return [{ vals: b.sup, desp: p.desp }, { vals: b.media, desp: p.desp }, { vals: b.inf, desp: p.desp }]; } });

    // Indicador «Envelopes (sobres)» (id envelopes)
    def({ id: 'envelopes', nombre: 'Envelopes (sobres)', corto: 'Env', grupo: 'Volatilidad', destino: 'precio', etiq: false,
      desc: 'Media móvil con bandas a un porcentaje fijo.',
      params: [pPeriodo(14), pNum('pct', 'Desviación %', 0.1, 0.001, 50, 0.01), pSel('metodo', 'Método', 'sma', OPC_MA), pPrecio(), pDesp()],
      capas: [['Superior', '#3399ff'], ['Inferior', '#3399ff']],
      calc: function(d, p){
        var m = mMA(precioDe(d, p.precio), p.periodo, p.metodo);
        return [{ vals: mMul(m, 1 + p.pct / 100), desp: p.desp }, { vals: mMul(m, 1 - p.pct / 100), desp: p.desp }];
      } });

    // Indicador «Canal de Keltner» (id keltner)
    def({ id: 'keltner', nombre: 'Canal de Keltner', corto: 'Keltner', grupo: 'Volatilidad', destino: 'precio', etiq: false,
      desc: 'EMA con bandas a N veces el ATR.',
      params: [pPeriodo(20), pNum('atr', 'Periodo ATR', 10, 1, 200, 1), pNum('mult', 'Multiplicador', 2, 0.1, 20, 0.1)],
      capas: [['Superior', '#e056fd'], ['Media', '#ff9800'], ['Inferior', '#e056fd']],
      calc: function(d, p){
        var m = mEMA(precioDe(d, 'close'), p.periodo), a = mATR(d, p.atr, 'wilder');
        return [{ vals: mOp(m, a, function(x, y){ return x + p.mult * y; }) }, { vals: m }, { vals: mOp(m, a, function(x, y){ return x - p.mult * y; }) }];
      } });

    // Indicador «Canal de Donchian» (id donchian)
    def({ id: 'donchian', nombre: 'Canal de Donchian', corto: 'Donchian', grupo: 'Volatilidad', destino: 'precio', etiq: false,
      desc: 'Máximo y mínimo de las últimas N velas.',
      params: [pPeriodo(20)], capas: [['Superior', '#26a69a'], ['Inferior', '#26a69a'], ['Media', '#8b949e']],
      calc: function(d, p){ var r = mDonchian(d, p.periodo); return [{ vals: r.sup }, { vals: r.inf }, { vals: r.med }]; } });

    // Indicador «ATR — Rango verdadero medio» (id atr)
    def({ id: 'atr', nombre: 'ATR — Rango verdadero medio', corto: 'ATR', grupo: 'Volatilidad', destino: 'panel',
      desc: 'Mide la volatilidad como el rango medio de las velas.',
      params: [pPeriodo(14, 200), pSel('metodo', 'Suavizado', 'sma', [['sma', 'Simple (MT5)'], ['wilder', 'Wilder']])],
      capas: [['ATR', '#ff9800']], dec: 'auto',
      calc: function(d, p){ return [{ vals: mATR(d, p.periodo, p.metodo) }]; } });

    // Indicador «Desviación típica» (id stddev)
    def({ id: 'stddev', nombre: 'Desviación típica', corto: 'StdDev', grupo: 'Volatilidad', destino: 'panel',
      desc: 'Dispersión del precio respecto a su media.',
      params: [pPeriodo(20, 300), pPrecio()], capas: [['StdDev', '#a78bfa']], dec: 'auto',
      calc: function(d, p){ return [{ vals: mDesv(precioDe(d, p.precio), p.periodo) }]; } });

    // Indicador «%B de Bollinger» (id pctb)
    def({ id: 'pctb', nombre: '%B de Bollinger', corto: '%B', grupo: 'Volatilidad', destino: 'panel',
      desc: 'Posición del precio dentro de las bandas (0 = banda inferior, 100 = superior).',
      params: [pPeriodo(20), pNum('desv', 'Desviaciones', 2, 0.1, 10, 0.1), pPrecio()],
      capas: [['%B', '#2962ff']], niveles: [100, 50, 0], dec: 2,
      calc: function(d, p){
        var a = precioDe(d, p.precio), b = mBollinger(a, p.periodo, p.desv), out = nulos(a.length);
        for (var i = 0; i < a.length; i++) if (esNum(b.sup[i]) && b.sup[i] !== b.inf[i]) out[i] = (a[i] - b.inf[i]) / (b.sup[i] - b.inf[i]) * 100;
        return [{ vals: out }];
      } });

    // Indicador «Ancho de bandas de Bollinger» (id bbw)
    def({ id: 'bbw', nombre: 'Ancho de bandas de Bollinger', corto: 'BBW', grupo: 'Volatilidad', destino: 'panel',
      desc: 'Distancia entre bandas en % de la media: mide compresión y expansión.',
      params: [pPeriodo(20), pNum('desv', 'Desviaciones', 2, 0.1, 10, 0.1), pPrecio()],
      capas: [['BBW', '#ff9800']], dec: 3,
      calc: function(d, p){
        var b = mBollinger(precioDe(d, p.precio), p.periodo, p.desv), out = nulos(d.length);
        for (var i = 0; i < d.length; i++) if (esNum(b.media[i]) && b.media[i] !== 0) out[i] = (b.sup[i] - b.inf[i]) / b.media[i] * 100;
        return [{ vals: out }];
      } });

    // ================= OSCILADORES =================
    // Indicador «RSI — Índice de fuerza relativa» (id rsi)
    def({ id: 'rsi', nombre: 'RSI — Índice de fuerza relativa', corto: 'RSI', grupo: 'Osciladores', destino: 'panel',
      desc: 'Momento del precio entre 0 y 100; sobrecompra > 70, sobreventa < 30.',
      params: [pPeriodo(14, 300), pPrecio()], capas: [['RSI', '#a78bfa']], niveles: [70, 30], rango: [0, 100], dec: 2,
      calc: function(d, p){ return [{ vals: mRSI(precioDe(d, p.precio), p.periodo) }]; } });

    // Indicador «MACD — Convergencia/divergencia de medias» (id macd)
    def({ id: 'macd', nombre: 'MACD — Convergencia/divergencia de medias', corto: 'MACD', grupo: 'Osciladores', destino: 'panel',
      desc: 'Diferencia entre dos EMA, su señal e histograma.',
      params: [pNum('rapida', 'EMA rápida', 12, 1, 200, 1), pNum('lenta', 'EMA lenta', 26, 2, 400, 1), pNum('senal', 'Señal', 9, 1, 200, 1),
               pSel('metodo', 'Media de la señal', 'ema', [['ema', 'Exponencial'], ['sma', 'Simple (MT5)']]), pPrecio()],
      capas: [['Histograma', '#3fb950', 'hist'], ['MACD', '#2962ff'], ['Señal', '#ff9800']], niveles: [0], dec: 'auto',
      calc: function(d, p){
        var m = mMACD(precioDe(d, p.precio), p.rapida, p.lenta, p.senal, p.metodo);
        return [{ vals: m.hist, cols: colHistSigno(m.hist) }, { vals: m.macd }, { vals: m.senal }];
      } });

    // Indicador «OsMA — Media móvil del oscilador» (id osma)
    def({ id: 'osma', nombre: 'OsMA — Media móvil del oscilador', corto: 'OsMA', grupo: 'Osciladores', destino: 'panel',
      desc: 'Histograma del MACD (MACD menos su señal).',
      params: [pNum('rapida', 'EMA rápida', 12, 1, 200, 1), pNum('lenta', 'EMA lenta', 26, 2, 400, 1), pNum('senal', 'Señal', 9, 1, 200, 1), pPrecio()],
      capas: [['OsMA', '#3fb950', 'hist']], niveles: [0], dec: 'auto',
      calc: function(d, p){ var m = mMACD(precioDe(d, p.precio), p.rapida, p.lenta, p.senal, 'sma'); return [{ vals: m.hist, cols: colHistSigno(m.hist) }]; } });

    // Indicador «Estocástico» (id stoch)
    def({ id: 'stoch', nombre: 'Estocástico', corto: 'Estoc', grupo: 'Osciladores', destino: 'panel',
      desc: 'Posición del cierre dentro del rango reciente (0–100).',
      params: [pNum('k', '%K', 14, 1, 200, 1), pNum('suav', 'Suavizado', 3, 1, 50, 1), pNum('d', '%D', 3, 1, 50, 1)],
      capas: [['%K', '#2962ff'], ['%D', '#ff9800']], niveles: [80, 20], rango: [0, 100], dec: 2,
      calc: function(d, p){ var e = mEstocastico(d, p.k, p.suav, p.d); return [{ vals: e.k }, { vals: e.d }]; } });

    // Indicador «Estocástico del RSI» (id stochrsi)
    def({ id: 'stochrsi', nombre: 'Estocástico del RSI', corto: 'StochRSI', grupo: 'Osciladores', destino: 'panel',
      desc: 'Estocástico aplicado al RSI: más sensible que el RSI.',
      params: [pNum('rsi', 'Periodo RSI', 14, 2, 200, 1), pNum('est', 'Periodo estocástico', 14, 2, 200, 1), pNum('k', '%K', 3, 1, 50, 1), pNum('d', '%D', 3, 1, 50, 1), pPrecio()],
      capas: [['%K', '#2962ff'], ['%D', '#ff9800']], niveles: [80, 20], rango: [0, 100], dec: 2,
      calc: function(d, p){ var e = mEstocRSI(precioDe(d, p.precio), p.rsi, p.est, p.k, p.d); return [{ vals: e.k }, { vals: e.d }]; } });

    // Indicador «ADX — Índice direccional medio» (id adx)
    def({ id: 'adx', nombre: 'ADX — Índice direccional medio', corto: 'ADX', grupo: 'Osciladores', destino: 'panel', etiq: false,
      desc: 'Fuerza de la tendencia (ADX) y dirección (+DI / −DI).',
      params: [pPeriodo(14, 200), pSel('metodo', 'Suavizado', 'wilder', [['wilder', 'Wilder (ADXW)'], ['ema', 'Exponencial (MT5)']])],
      capas: [['ADX', '#d1d4dc'], ['+DI', '#3fb950'], ['−DI', '#f85149']], niveles: [20], dec: 2,
      calc: function(d, p){ var a = mADX(d, p.periodo, p.metodo); return [{ vals: a.adx }, { vals: a.pdi }, { vals: a.mdi }]; } });

    // Indicador «CCI — Índice del canal de materias primas» (id cci)
    def({ id: 'cci', nombre: 'CCI — Índice del canal de materias primas', corto: 'CCI', grupo: 'Osciladores', destino: 'panel',
      desc: 'Desviación del precio típico respecto a su media; ±100 marcan extremos.',
      params: [pPeriodo(14, 300)], capas: [['CCI', '#26a69a']], niveles: [100, 0, -100], dec: 2,
      calc: function(d, p){ return [{ vals: mCCI(d, p.periodo) }]; } });

    // Indicador «Williams %R» (id wpr)
    def({ id: 'wpr', nombre: 'Williams %R', corto: '%R', grupo: 'Osciladores', destino: 'panel',
      desc: 'Posición del cierre en el rango reciente, de −100 a 0.',
      params: [pPeriodo(14, 300)], capas: [['%R', '#e056fd']], niveles: [-20, -80], rango: [-100, 0], dec: 2,
      calc: function(d, p){ return [{ vals: mWilliamsR(d, p.periodo) }]; } });

    // Indicador «Momentum» (id momentum)
    def({ id: 'momentum', nombre: 'Momentum', corto: 'Momentum', grupo: 'Osciladores', destino: 'panel',
      desc: 'Cierre actual como % del cierre de hace N velas (100 = sin cambio).',
      params: [pPeriodo(14, 300), pPrecio()], capas: [['Momentum', '#3399ff']], niveles: [100], dec: 3,
      calc: function(d, p){ return [{ vals: mMomentum(precioDe(d, p.precio), p.periodo) }]; } });

    // Indicador «ROC — Tasa de cambio» (id roc)
    def({ id: 'roc', nombre: 'ROC — Tasa de cambio', corto: 'ROC', grupo: 'Osciladores', destino: 'panel',
      desc: 'Variación porcentual respecto a hace N velas.',
      params: [pPeriodo(12, 300), pPrecio()], capas: [['ROC', '#ff6600']], niveles: [0], dec: 3,
      calc: function(d, p){ return [{ vals: mROC(precioDe(d, p.precio), p.periodo) }]; } });

    // Indicador «CMO — Oscilador de momento de Chande» (id cmo)
    def({ id: 'cmo', nombre: 'CMO — Oscilador de momento de Chande', corto: 'CMO', grupo: 'Osciladores', destino: 'panel',
      desc: 'Momento entre −100 y 100.',
      params: [pPeriodo(14, 300), pPrecio()], capas: [['CMO', '#9ccc65']], niveles: [50, 0, -50], rango: [-100, 100], dec: 2,
      calc: function(d, p){ return [{ vals: mCMO(precioDe(d, p.precio), p.periodo) }]; } });

    // Indicador «DeMarker» (id demarker)
    def({ id: 'demarker', nombre: 'DeMarker', corto: 'DeMarker', grupo: 'Osciladores', destino: 'panel',
      desc: 'Detecta agotamiento comparando máximos y mínimos consecutivos (0–1).',
      params: [pPeriodo(14, 300)], capas: [['DeMarker', '#ffa726']], niveles: [0.7, 0.3], rango: [0, 1], dec: 3,
      calc: function(d, p){ return [{ vals: mDeMarker(d, p.periodo) }]; } });

    // Indicador «TRIX — EMA triple» (id trix)
    def({ id: 'trix', nombre: 'TRIX — EMA triple', corto: 'TRIX', grupo: 'Osciladores', destino: 'panel',
      desc: 'Variación % de una EMA triple; filtra el ruido.',
      params: [pPeriodo(14, 300), pPrecio()], capas: [['TRIX', '#ab47bc']], niveles: [0], dec: 'auto',
      calc: function(d, p){ return [{ vals: mTRIX(precioDe(d, p.precio), p.periodo) }]; } });

    // Indicador «RVI — Índice de vigor relativo» (id rvi)
    def({ id: 'rvi', nombre: 'RVI — Índice de vigor relativo', corto: 'RVI', grupo: 'Osciladores', destino: 'panel',
      desc: 'Compara el cierre con la apertura frente al rango de la vela.',
      params: [pPeriodo(10, 200)], capas: [['RVI', '#3fb950'], ['Señal', '#f85149']], niveles: [0], dec: 'auto',
      calc: function(d, p){ var r = mRVI(d, p.periodo); return [{ vals: r.rvi }, { vals: r.senal }]; } });

    // Indicador «Aroon» (id aroon)
    def({ id: 'aroon', nombre: 'Aroon', corto: 'Aroon', grupo: 'Osciladores', destino: 'panel', etiq: false,
      desc: 'Tiempo transcurrido desde el último máximo y mínimo: detecta nuevas tendencias.',
      params: [pPeriodo(14, 300)], capas: [['Aroon alcista', '#3fb950'], ['Aroon bajista', '#f85149']], niveles: [50], rango: [0, 100], dec: 2,
      calc: function(d, p){ var a = mAroon(d, p.periodo); return [{ vals: a.up }, { vals: a.dn }]; } });

    // Indicador «Oscilador último (Ultimate)» (id uo)
    def({ id: 'uo', nombre: 'Oscilador último (Ultimate)', corto: 'UO', grupo: 'Osciladores', destino: 'panel',
      desc: 'Combina el momento en tres periodos (0–100).',
      params: [pNum('p1', 'Periodo 1', 7, 1, 100, 1), pNum('p2', 'Periodo 2', 14, 1, 200, 1), pNum('p3', 'Periodo 3', 28, 1, 400, 1)],
      capas: [['UO', '#00bcd4']], niveles: [70, 30], rango: [0, 100], dec: 2,
      calc: function(d, p){ return [{ vals: mUltimate(d, p.p1, p.p2, p.p3) }]; } });

    /**
     * Atajo para registrar Bulls Power y Bears Power: histograma de (máximo o mínimo) menos la EMA del cierre,
     * coloreado por signo.
     */
    function defPoder(id, nombre, corto, campo, desc){
      def({ id: id, nombre: nombre, corto: corto, grupo: 'Osciladores', destino: 'panel', desc: desc,
        params: [pPeriodo(13, 300)], capas: [[corto, campo === 'high' ? '#3fb950' : '#f85149', 'hist']], niveles: [0], dec: 'auto',
        calc: function(d, p){ var v = mResta(columna(d, campo), mEMA(columna(d, 'close'), p.periodo)); return [{ vals: v, cols: colHistSigno(v) }]; } });
    }
    // Indicador «Bulls Power — Fuerza alcista» (id bulls)
    defPoder('bulls', 'Bulls Power — Fuerza alcista', 'Bulls', 'high', 'Máximo menos EMA: fuerza de los compradores.');
    // Indicador «Bears Power — Fuerza bajista» (id bears)
    defPoder('bears', 'Bears Power — Fuerza bajista', 'Bears', 'low', 'Mínimo menos EMA: fuerza de los vendedores.');

    // Indicador «Force Index — Índice de fuerza» (id force)
    def({ id: 'force', nombre: 'Force Index — Índice de fuerza', corto: 'Force', grupo: 'Osciladores', destino: 'panel',
      desc: 'Variación del precio multiplicada por el volumen.',
      params: [pPeriodo(13, 300), pSel('metodo', 'Método', 'ema', OPC_MA)], capas: [['Force', '#26a69a']], niveles: [0], dec: 'auto',
      calc: function(d, p){
        var f = d.map(function(v, i){ return i === 0 ? null : (v.close - d[i-1].close) * volDe(v); });
        return [{ vals: mMA(f, p.periodo, p.metodo) }];
      } });

    // ================= VOLUMEN =================
    // Indicador «Volúmenes» (id volumenes)
    def({ id: 'volumenes', nombre: 'Volúmenes', corto: 'Volumen', grupo: 'Volumen', destino: 'panel',
      desc: 'Volumen de ticks de cada vela en su propio panel.',
      params: [], capas: [['Volumen', '#3fb950', 'hist']], dec: 0,
      calc: function(d){ return [{ vals: d.map(volDe), cols: d.map(function(v){ return v.close >= v.open ? 'rgba(63,185,80,0.6)' : 'rgba(248,81,73,0.6)'; }) }]; } });

    // Indicador «OBV — Volumen en balance» (id obv)
    def({ id: 'obv', nombre: 'OBV — Volumen en balance', corto: 'OBV', grupo: 'Volumen', destino: 'panel',
      desc: 'Volumen acumulado: suma si el cierre sube, resta si baja.',
      params: [], capas: [['OBV', '#3399ff']], dec: 'auto', calc: function(d){ return [{ vals: mOBV(d) }]; } });

    // Indicador «A/D — Acumulación/distribución» (id ad)
    def({ id: 'ad', nombre: 'A/D — Acumulación/distribución', corto: 'A/D', grupo: 'Volumen', destino: 'panel',
      desc: 'Flujo de dinero acumulado según dónde cierra la vela dentro de su rango.',
      params: [], capas: [['A/D', '#ff9800']], dec: 'auto', calc: function(d){ return [{ vals: mAD(d) }]; } });

    // Indicador «CMF — Flujo de dinero de Chaikin» (id cmf)
    def({ id: 'cmf', nombre: 'CMF — Flujo de dinero de Chaikin', corto: 'CMF', grupo: 'Volumen', destino: 'panel',
      desc: 'Presión compradora/vendedora de las últimas N velas (−1 a 1).',
      params: [pPeriodo(20, 300)], capas: [['CMF', '#26a69a']], niveles: [0], dec: 3,
      calc: function(d, p){ return [{ vals: mCMF(d, p.periodo) }]; } });

    // Indicador «Oscilador de Chaikin» (id chaikin)
    def({ id: 'chaikin', nombre: 'Oscilador de Chaikin', corto: 'Chaikin', grupo: 'Volumen', destino: 'panel',
      desc: 'Diferencia de dos EMA de la línea de acumulación/distribución.',
      params: [pNum('rapida', 'EMA rápida', 3, 1, 100, 1), pNum('lenta', 'EMA lenta', 10, 2, 300, 1)],
      capas: [['Chaikin', '#e056fd']], niveles: [0], dec: 'auto',
      calc: function(d, p){ var ad = mAD(d); return [{ vals: mResta(mEMA(ad, p.rapida), mEMA(ad, p.lenta)) }]; } });

    // Indicador «MFI — Índice de flujo de dinero» (id mfi)
    def({ id: 'mfi', nombre: 'MFI — Índice de flujo de dinero', corto: 'MFI', grupo: 'Volumen', destino: 'panel',
      desc: 'RSI ponderado por volumen (0–100); > 80 sobrecompra, < 20 sobreventa.',
      params: [pPeriodo(14, 300)], capas: [['MFI', '#a78bfa']], niveles: [80, 20], rango: [0, 100], dec: 2,
      calc: function(d, p){ return [{ vals: mMFI(d, p.periodo) }]; } });

    // ================= BILL WILLIAMS =================
    /** Devuelve el precio mediano (H+L)/2 de cada vela, base de los indicadores de Bill Williams. */
    function mediana(d){ return precioDe(d, 'hl2'); }
    /**
     * Awesome Oscillator: diferencia entre la SMA rápida r y la lenta l de la mediana. Devuelve un array alineado.
     */
    function ao(d, r, l){ return mResta(mSMA(mediana(d), r), mSMA(mediana(d), l)); }

    // Indicador «Awesome Oscillator» (id ao)
    def({ id: 'ao', nombre: 'Awesome Oscillator', corto: 'AO', grupo: 'Bill Williams', destino: 'panel',
      desc: 'Diferencia entre SMA 5 y SMA 34 de la mediana; verde sube, rojo baja.',
      params: [pNum('rapida', 'Periodo rápido', 5, 1, 100, 1), pNum('lenta', 'Periodo lento', 34, 2, 300, 1)],
      capas: [['AO', '#3fb950', 'hist']], niveles: [0], dec: 'auto',
      calc: function(d, p){ var v = ao(d, p.rapida, p.lenta); return [{ vals: v, cols: colHistSube(v) }]; } });

    // Indicador «Accelerator Oscillator» (id ac)
    def({ id: 'ac', nombre: 'Accelerator Oscillator', corto: 'AC', grupo: 'Bill Williams', destino: 'panel',
      desc: 'Aceleración del Awesome Oscillator.',
      params: [pNum('rapida', 'Periodo rápido', 5, 1, 100, 1), pNum('lenta', 'Periodo lento', 34, 2, 300, 1), pNum('suav', 'Suavizado', 5, 1, 100, 1)],
      capas: [['AC', '#3fb950', 'hist']], niveles: [0], dec: 'auto',
      calc: function(d, p){ var a = ao(d, p.rapida, p.lenta), v = mResta(a, mSMA(a, p.suav)); return [{ vals: v, cols: colHistSube(v) }]; } });

    // P_ALLIGATOR: parámetros compartidos por el Alligator y el Gator
    var P_ALLIGATOR = [pNum('mand', 'Mandíbula', 13, 1, 200, 1), pNum('mandd', 'Desplazamiento mandíbula', 8, 0, 100, 1),
                       pNum('dien', 'Dientes', 8, 1, 200, 1), pNum('diend', 'Desplazamiento dientes', 5, 0, 100, 1),
                       pNum('lab', 'Labios', 5, 1, 200, 1), pNum('labd', 'Desplazamiento labios', 3, 0, 100, 1)];
    /**
     * Calcula las tres medias suavizadas del Alligator (mandíbula, dientes y labios) sobre la mediana; los
     * desplazamientos se aplican al dibujar. Devuelve {jaw, teeth, lips}.
     */
    function lineasAlligator(d, p){
      var m = mediana(d);
      return { jaw: mSMMA(m, p.mand), teeth: mSMMA(m, p.dien), lips: mSMMA(m, p.lab) };
    }
    // Indicador «Alligator (Bill Williams)» (id alligator)
    def({ id: 'alligator', nombre: 'Alligator (Bill Williams)', corto: 'Alligator', grupo: 'Bill Williams', destino: 'precio', etiq: false,
      desc: 'Tres medias suavizadas desplazadas: mandíbula, dientes y labios.',
      params: P_ALLIGATOR, capas: [['Mandíbula', '#2962ff'], ['Dientes', '#f85149'], ['Labios', '#3fb950']],
      calc: function(d, p){ var a = lineasAlligator(d, p); return [{ vals: a.jaw, desp: p.mandd }, { vals: a.teeth, desp: p.diend }, { vals: a.lips, desp: p.labd }]; } });

    // Indicador «Gator Oscillator» (id gator)
    def({ id: 'gator', nombre: 'Gator Oscillator', corto: 'Gator', grupo: 'Bill Williams', destino: 'panel',
      desc: 'Muestra cuándo el Alligator "duerme" o "come" (histograma doble).',
      params: P_ALLIGATOR, capas: [['Superior', '#3fb950', 'hist'], ['Inferior', '#3fb950', 'hist']], niveles: [0], dec: 'auto',
      calc: function(d, p){
        var a = lineasAlligator(d, p), jaw = mDesplazar(a.jaw, p.mandd), teeth = mDesplazar(a.teeth, p.diend), lips = mDesplazar(a.lips, p.labd);
        var sup = mOp(jaw, teeth, function(x, y){ return Math.abs(x - y); });
        var inf = mOp(teeth, lips, function(x, y){ return -Math.abs(x - y); });
        var cS = sup.map(function(v, i){ return esNum(v) ? ((i > 0 && esNum(sup[i-1]) && v < sup[i-1]) ? '#f85149' : '#3fb950') : null; });
        var cI = inf.map(function(v, i){ return esNum(v) ? ((i > 0 && esNum(inf[i-1]) && v > inf[i-1]) ? '#f85149' : '#3fb950') : null; });
        return [{ vals: sup, cols: cS }, { vals: inf, cols: cI }];
      } });

    // Indicador «Market Facilitation Index (BW MFI)» (id bwmfi)
    def({ id: 'bwmfi', nombre: 'Market Facilitation Index (BW MFI)', corto: 'BW MFI', grupo: 'Bill Williams', destino: 'panel',
      desc: 'Rango por unidad de volumen. Verde: sube MFI y volumen · Marrón: bajan ambos · Azul: sube MFI, baja volumen · Rosa: baja MFI, sube volumen.',
      params: [], capas: [['BW MFI', '#3fb950', 'hist']], dec: 'auto',
      calc: function(d){
        var punto = Math.pow(10, -DIGITS), v = d.map(function(c){ var vo = volDe(c); return vo > 0 ? (c.high - c.low) / vo / punto : null; });
        var cols = v.map(function(m, i){
          if (!esNum(m) || i === 0 || !esNum(v[i-1])) return esNum(m) ? '#8b949e' : null;
          var mSube = m > v[i-1], vSube = volDe(d[i]) > volDe(d[i-1]);
          return mSube && vSube ? '#3fb950' : (!mSube && !vSube ? '#8d6e63' : (mSube ? '#2962ff' : '#e056fd'));
        });
        return [{ vals: v, cols: cols }];
      } });

    // Indicador «Fractales (Bill Williams)» (id fractales)
    def({ id: 'fractales', nombre: 'Fractales (Bill Williams)', corto: 'Fractales', grupo: 'Bill Williams', destino: 'precio',
      desc: 'Máximos y mínimos locales confirmados por 2 velas a cada lado.',
      params: [pNum('lados', 'Velas a cada lado', 2, 1, 10, 1)],
      capas: [['Fractal alcista (máximo)', '#3fb950', 'puntos'], ['Fractal bajista (mínimo)', '#f85149', 'puntos']],
      calc: function(d, p){ var f = mFractales(d, p.lados); return [{ vals: f.arriba }, { vals: f.abajo }]; } });

    // ================= NIVELES =================
    // Indicador «Puntos pivote (día anterior)» (id pivotes)
    def({ id: 'pivotes', nombre: 'Puntos pivote (día anterior)', corto: 'Pivotes', grupo: 'Niveles', destino: 'precio', etiq: false,
      desc: 'Pivote clásico, R1/R2 y S1/S2 calculados con el máximo, mínimo y cierre del día anterior.',
      params: [], capas: [['Pivote', '#f5c518'], ['R1', '#f85149'], ['R2', '#b71c1c'], ['S1', '#3fb950'], ['S2', '#1b5e20']],
      calc: function(d){
        var r = mPivotes(d);
        return [{ vals: r.p, pasos: true }, { vals: r.r1, pasos: true }, { vals: r.r2, pasos: true }, { vals: r.s1, pasos: true }, { vals: r.s2, pasos: true }];
      } });

    // Indicador «ZigZag» (id zigzag)
    def({ id: 'zigzag', nombre: 'ZigZag', corto: 'ZigZag', grupo: 'Niveles', destino: 'precio',
      desc: 'Une los extremos relevantes ignorando retrocesos menores al % indicado.',
      params: [pNum('pct', 'Desviación mínima (%)', 0.5, 0.01, 50, 0.01)], capas: [['ZigZag', '#ff9800']], etiq: false,
      calc: function(d, p){ return [{ vals: mZigZag(d, p.pct) }]; } });

    // ================= Instancias =================
    // seqUid: contador que genera el identificador único de cada instancia
    var seqUid = 0;
    /**
     * Valida el valor v de un parámetro pd: en listas exige una opción válida; en numéricos lo convierte, lo limita a
     * [min, max] y lo redondea según el paso. Si no es válido devuelve el valor por defecto.
     */
    function valorParam(pd, v){
      if (pd.t === 'sel') { for (var i = 0; i < pd.o.length; i++) if (pd.o[i][0] === v) return v; return pd.d; }
      var x = Number(v);
      if (!isFinite(x)) return pd.d;
      x = Math.min(pd.max, Math.max(pd.min, x));
      return pd.paso >= 1 ? Math.round(x) : Math.round(x * 1e6) / 1e6;
    }
    /**
     * Construye el objeto de parámetros de un indicador d validando cada uno contra el objeto crudo (o usando los
     * valores por defecto).
     */
    function validarParams(d, crudo){
      var p = {};
      d.params.forEach(function(pd){ p[pd.k] = valorParam(pd, crudo && typeof crudo === 'object' ? crudo[pd.k] : undefined); });
      return p;
    }
    // COLOR_OK: expresión regular que acepta colores #rrggbb
    var COLOR_OK = /^#[0-9a-fA-F]{6}$/;
    // Visibilidad por temporalidad: grupo -> [activo, mínimo, máximo] (como en TradingView)
    // GRUPOS_TF: grupos de visibilidad por temporalidad [clave, nombre, mínimo, máximo]
    var GRUPOS_TF = [['m', 'Minutos', 1, 59], ['h', 'Horas', 1, 24], ['d', 'Días', 1, 366], ['w', 'Semanas', 1, 52], ['M', 'Meses', 1, 12]];
    // TF_GRUPO: temporalidad -> [grupo, cantidad] usada para evaluar la visibilidad
    var TF_GRUPO = { M1: ['m', 1], M5: ['m', 5], M15: ['m', 15], M30: ['m', 30], H1: ['h', 1], H4: ['h', 4], D1: ['d', 1], W1: ['w', 1], MN1: ['M', 1] };
    /** Devuelve la visibilidad inicial por temporalidad: todos los grupos activos y con el rango completo. */
    function visibilidadPorDefecto(){
      var v = {};
      GRUPOS_TF.forEach(function(g){ v[g[0]] = [true, g[2], g[3]]; });
      return v;
    }
    /**
     * Valida la visibilidad recordada (grupo -> [activo, mínimo, máximo]) y la corrige al formato correcto,
     * completando con los valores por defecto.
     */
    function validarVisibilidad(crudo){
      var v = visibilidadPorDefecto();
      if (!crudo || typeof crudo !== 'object') return v;
      GRUPOS_TF.forEach(function(g){
        var c = crudo[g[0]];
        if (!Array.isArray(c) || c.length !== 3) return;
        var mn = Math.round(Number(c[1])), mx = Math.round(Number(c[2]));
        if (!isFinite(mn) || !isFinite(mx)) return;
        mn = Math.min(g[3], Math.max(g[2], mn)); mx = Math.min(g[3], Math.max(g[2], mx));
        v[g[0]] = [c[0] !== false, Math.min(mn, mx), Math.max(mn, mx)];
      });
      return v;
    }
    /** Indica si la instancia inst debe mostrarse en la temporalidad actual según sus reglas de visibilidad. */
    function visibleEnTF(inst){
      var g = TF_GRUPO[tfActual];
      if (!g || !inst.vis) return true;
      var r = inst.vis[g[0]];
      return !r || (r[0] && g[1] >= r[1] && g[1] <= r[2]);
    }
    // Lista de n elementos validados (null = valor por defecto)
    /**
     * Valida una lista de n elementos con la función ok (que devuelve el valor válido o null). Devuelve null si
     * ninguno es distinto de null, para no guardar listas vacías.
     */
    function listaValidada(crudo, n, ok){
      var out = [], hay = false;
      for (var i = 0; i < n; i++){
        var x = (Array.isArray(crudo) && i < crudo.length) ? ok(crudo[i]) : null;
        out.push(x); if (x !== null) hay = true;
      }
      return hay ? out : null;
    }
    /**
     * Crea una instancia de indicador { uid, id, p, c, w, s, v, pr, et, sl, vis, oculto } a partir del id y de datos
     * recordados (crudo), validándolo todo. Devuelve null si el id no existe.
     */
    function nuevaInstancia(id, crudo){
      var d = DEFS[id];
      if (!d) return null;
      var n = d.capas.length, r = crudo || {};
      var inst = { uid: 'i' + (++seqUid), id: id, p: validarParams(d, r.p), oculto: !!r.o };
      inst.c = listaValidada(r.c, n, function(x){ return (typeof x === 'string' && COLOR_OK.test(x)) ? x : null; });
      var w = (typeof r.w === 'number') ? r.w : null;   // formato antiguo: un solo grosor para todas las líneas
      inst.w = listaValidada(Array.isArray(r.w) ? r.w : (w ? new Array(n).fill(w) : null), n, function(x){ return (typeof x === 'number' && x >= 1 && x <= 5) ? Math.round(x) : null; });
      inst.s = listaValidada(r.s, n, function(x){ return (x === 0 || x === 1 || x === 2) ? x : null; });
      inst.v = listaValidada(r.v, n, function(x){ return x === 0 ? 0 : (x === 1 ? 1 : null); });
      inst.pr = (typeof r.pr === 'number' && r.pr >= 0 && r.pr <= 8) ? Math.round(r.pr) : null;
      inst.et = r.et !== 0 && r.et !== false;   // etiquetas en la escala de precios
      inst.sl = r.sl !== 0 && r.sl !== false;   // valores en la línea de estado
      inst.vis = validarVisibilidad(r.vis);
      return inst;
    }
    // Vuelve a dejar `inst` como estaba en `snap` (Cancelar en la ventana de ajustes)
    /** Deja la instancia inst como estaba en la copia snap (usado por Cancelar y Restablecer en los ajustes). */
    function restaurarInstancia(inst, snap){
      var n = nuevaInstancia(inst.id, snap);
      ['p', 'c', 'w', 's', 'v', 'pr', 'et', 'sl', 'vis', 'oculto'].forEach(function(k){ inst[k] = n[k]; });
    }

    // Restaura lo recordado (descarta lo que ya no existe o está mal formado)
    // Restaura las instancias recordadas en el almacenamiento local (el estado indActivos se declara en 01_estado_y_configuracion.js)
    indActivos = (cfgIndRaw || []).map(function(r){
      return (r && typeof r.id === 'string') ? nuevaInstancia(r.id, r) : null;
    }).filter(function(x){ return x; });

    /**
     * Devuelve el título de una instancia: abreviatura y parámetros numéricos entre paréntesis (sin el
     * desplazamiento), por ejemplo SMA (20).
     */
    function tituloInstancia(inst){
      var d = DEFS[inst.id], partes = [];
      d.params.forEach(function(pd){ if (pd.t === 'num' && pd.k !== 'desp') partes.push(inst.p[pd.k]); });
      return d.corto + (partes.length ? ' (' + partes.join(', ') + ')' : '');
    }
    /** Devuelve el color de la capa i de la instancia: el elegido por el usuario o el del catálogo. */
    function colorCapa(inst, i){ return (inst.c && inst.c[i]) || DEFS[inst.id].capas[i][1]; }
    /** Devuelve el grosor de línea de la capa i de la instancia (2 por defecto). */
    function anchoCapa(inst, i){ return (inst.w && inst.w[i]) || 2; }
    /** Devuelve el tipo de trazo de la capa i de la instancia (0 = sólida por defecto). */
    function estiloLineaCapa(inst, i){ return (inst.s && inst.s[i]) || 0; }
    /** Indica si la capa i de la instancia está visible (solo se oculta cuando se marcó explícitamente). */
    function capaVisible(inst, i){ return !(inst.v && inst.v[i] === 0); }

/* -------------------------------------------------------------------------------------------------------
   ----------------------------- FIN Piña y Jara 33_indicadores_catalogo .JS -----------------------------
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
