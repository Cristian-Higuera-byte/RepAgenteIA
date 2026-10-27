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
   ---------------------------- INICIO Piña y Jara 30_indicadores_calculo .JS ----------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Indicadores: biblioteca matemática (medias, volatilidad, osciladores, volumen)
    // Todas las funciones trabajan con ARRAYS ALINEADOS con las velas (misma longitud que `datos`):
    // posición i = vela i, y null donde el indicador aún no tiene valor. Así se pueden componer entre sí
    // (p. ej. MACD = EMA - EMA) y el motor las dibuja sin que los paneles se desalineen del gráfico principal.

    /**
     * Crea un array de longitud n lleno de null; es la base de todos los indicadores (null = sin valor todavía en esa
     * vela).
     */
    function nulos(n){ var a = new Array(n); for (var i = 0; i < n; i++) a[i] = null; return a; }
    /**
     * Indica si v es un número finito utilizable (descarta null, undefined, NaN e Infinity). Recibe cualquier valor y
     * devuelve un booleano.
     */
    function esNum(v){ return v !== null && v !== undefined && typeof v === 'number' && isFinite(v); }
    /**
     * Devuelve el índice del primer elemento numérico del array a, o -1 si no hay ninguno. Sirve para saber desde
     * dónde empieza a haber datos.
     */
    function primerValido(a){ for (var i = 0; i < a.length; i++) if (esNum(a[i])) return i; return -1; }

    // Precio de entrada: cierre, apertura, máximo, mínimo o combinaciones (como en MT5)
    /**
     * Calcula la serie de precios de entrada de un indicador. Recibe las velas y el tipo (open, high, low, hl2, hlc3,
     * ohlc4, hlcc4; cualquier otro valor usa el cierre) y devuelve un array alineado con las velas.
     */
    function precioDe(datos, tipo){
      var out = new Array(datos.length);
      for (var i = 0; i < datos.length; i++){
        var d = datos[i], v;
        switch (tipo){
          case 'open':  v = d.open; break;
          case 'high':  v = d.high; break;
          case 'low':   v = d.low; break;
          case 'hl2':   v = (d.high + d.low) / 2; break;
          case 'hlc3':  v = (d.high + d.low + d.close) / 3; break;
          case 'ohlc4': v = (d.open + d.high + d.low + d.close) / 4; break;
          case 'hlcc4': v = (d.high + d.low + 2 * d.close) / 4; break;
          default:      v = d.close;
        }
        out[i] = v;
      }
      return out;
    }
    /** Extrae de las velas la columna indicada (por ejemplo high o low) como array alineado con ellas. */
    function columna(datos, campo){ return datos.map(function(d){ return d[campo]; }); }
    /** Devuelve el volumen de una vela, o 0 si no lo trae. */
    function volDe(d){ return d.volume || 0; }

    // ---------- Medias móviles ----------
    /**
     * Media móvil simple de periodo n sobre el array a. Devuelve un array alineado con null mientras no haya n datos
     * válidos.
     */
    function mSMA(a, n){
      var out = nulos(a.length), s0 = primerValido(a);
      if (s0 < 0 || n < 1) return out;
      var suma = 0;
      for (var i = s0; i < a.length; i++){
        suma += a[i];
        if (i - s0 >= n) suma -= a[i - n];
        if (i - s0 >= n - 1) out[i] = suma / n;
      }
      return out;
    }
    /**
     * Media móvil exponencial de periodo n. Se inicializa con la media simple de las primeras n muestras y después
     * aplica el factor 2/(n+1). Devuelve un array alineado.
     */
    function mEMA(a, n){
      var out = nulos(a.length), s0 = primerValido(a);
      if (s0 < 0 || s0 + n > a.length) return out;
      var k = 2 / (n + 1), suma = 0;
      for (var i = s0; i < s0 + n; i++) suma += a[i];
      var prev = suma / n; out[s0 + n - 1] = prev;
      for (var j = s0 + n; j < a.length; j++){ prev = (a[j] - prev) * k + prev; out[j] = prev; }
      return out;
    }
    // Media suavizada (Wilder / RMA / SMMA)
    /**
     * Media móvil suavizada de Wilder (RMA/SMMA) de periodo n; se inicializa con la media simple y después pondera
     * (n-1)/n el valor previo. Devuelve un array alineado.
     */
    function mSMMA(a, n){
      var out = nulos(a.length), s0 = primerValido(a);
      if (s0 < 0 || s0 + n > a.length) return out;
      var suma = 0;
      for (var i = s0; i < s0 + n; i++) suma += a[i];
      var prev = suma / n; out[s0 + n - 1] = prev;
      for (var j = s0 + n; j < a.length; j++){ prev = (prev * (n - 1) + a[j]) / n; out[j] = prev; }
      return out;
    }
    // Media ponderada lineal (el dato más reciente pesa más)
    /**
     * Media móvil ponderada linealmente de periodo n: la muestra más reciente pesa n y la más antigua 1. Devuelve un
     * array alineado.
     */
    function mLWMA(a, n){
      var out = nulos(a.length), s0 = primerValido(a);
      if (s0 < 0) return out;
      var den = n * (n + 1) / 2;
      for (var i = s0 + n - 1; i < a.length; i++){
        var s = 0;
        for (var j = 0; j < n; j++) s += a[i - n + 1 + j] * (j + 1);
        out[i] = s / den;
      }
      return out;
    }
    /**
     * Selector de media móvil: devuelve la EMA, SMMA o LWMA según metodo y, por defecto, la SMA, con periodo n sobre
     * el array a.
     */
    function mMA(a, n, metodo){
      if (metodo === 'ema') return mEMA(a, n);
      if (metodo === 'smma') return mSMMA(a, n);
      if (metodo === 'lwma') return mLWMA(a, n);
      return mSMA(a, n);
    }
    /**
     * Media exponencial doble (DEMA = 2*EMA - EMA(EMA)); reduce el retraso de la EMA. Devuelve un array alineado.
     */
    function mDEMA(a, n){
      var e1 = mEMA(a, n), e2 = mEMA(e1, n);
      return e1.map(function(v, i){ return esNum(v) && esNum(e2[i]) ? 2 * v - e2[i] : null; });
    }
    /**
     * Media exponencial triple (TEMA = 3*EMA1 - 3*EMA2 + EMA3); aún menos retraso que la DEMA. Devuelve un array
     * alineado.
     */
    function mTEMA(a, n){
      var e1 = mEMA(a, n), e2 = mEMA(e1, n), e3 = mEMA(e2, n);
      return e1.map(function(v, i){ return esNum(e3[i]) ? 3 * v - 3 * e2[i] + e3[i] : null; });
    }
    /**
     * Media de Hull: LWMA de periodo raíz(n) aplicada a 2*LWMA(n/2) - LWMA(n). Es rápida y muy suave. Devuelve un
     * array alineado.
     */
    function mHMA(a, n){
      var mitad = Math.max(1, Math.round(n / 2)), raiz = Math.max(1, Math.round(Math.sqrt(n)));
      var w1 = mLWMA(a, mitad), w2 = mLWMA(a, n);
      var dif = w1.map(function(v, i){ return esNum(v) && esNum(w2[i]) ? 2 * v - w2[i] : null; });
      return mLWMA(dif, raiz);
    }

    // ---------- Estadística y extremos ----------
    /**
     * Desviación típica poblacional de ventana n sobre el array a (usa la SMA como media). Devuelve un array
     * alineado.
     */
    function mDesv(a, n){   // desviación típica poblacional
      var out = nulos(a.length), med = mSMA(a, n);
      for (var i = 0; i < a.length; i++){
        if (!esNum(med[i])) continue;
        var s = 0;
        for (var j = i - n + 1; j <= i; j++){ var d = a[j] - med[i]; s += d * d; }
        out[i] = Math.sqrt(s / n);
      }
      return out;
    }
    /**
     * Máximo móvil de ventana n; queda en null si algún valor de la ventana no es numérico. Devuelve un array
     * alineado.
     */
    function mMax(a, n){
      var out = nulos(a.length);
      for (var i = n - 1; i < a.length; i++){
        var m = -Infinity, ok = true;
        for (var j = i - n + 1; j <= i; j++){ if (!esNum(a[j])) { ok = false; break; } if (a[j] > m) m = a[j]; }
        if (ok) out[i] = m;
      }
      return out;
    }
    /**
     * Mínimo móvil de ventana n; queda en null si algún valor de la ventana no es numérico. Devuelve un array
     * alineado.
     */
    function mMin(a, n){
      var out = nulos(a.length);
      for (var i = n - 1; i < a.length; i++){
        var m = Infinity, ok = true;
        for (var j = i - n + 1; j <= i; j++){ if (!esNum(a[j])) { ok = false; break; } if (a[j] < m) m = a[j]; }
        if (ok) out[i] = m;
      }
      return out;
    }
    /**
     * Suma móvil de las últimas n muestras (ventana deslizante). Devuelve un array alineado con null hasta completar
     * la ventana.
     */
    function mSumaVentana(a, n){
      var out = nulos(a.length), s0 = primerValido(a);
      if (s0 < 0) return out;
      var suma = 0;
      for (var i = s0; i < a.length; i++){
        suma += a[i];
        if (i - s0 >= n) suma -= a[i - n];
        if (i - s0 >= n - 1) out[i] = suma;
      }
      return out;
    }
    /**
     * Aplica la función f(x, y, i) elemento a elemento entre el array a y b (que puede ser otro array o un número
     * constante). Solo calcula donde ambos son números y el resultado lo es; en el resto deja null.
     */
    function mOp(a, b, f){
      var out = nulos(a.length);
      for (var i = 0; i < a.length; i++){
        var x = a[i], y = (typeof b === 'number') ? b : b[i];
        if (esNum(x) && esNum(y)) { var r = f(x, y, i); if (esNum(r)) out[i] = r; }
      }
      return out;
    }
    /** Resta elemento a elemento a - b (b puede ser array o número). Devuelve un array alineado. */
    function mResta(a, b){ return mOp(a, b, function(x, y){ return x - y; }); }
    /** Suma elemento a elemento a + b (b puede ser array o número). Devuelve un array alineado. */
    function mSuma(a, b){ return mOp(a, b, function(x, y){ return x + y; }); }
    /** Multiplica elemento a elemento a * b (b puede ser array o número). Devuelve un array alineado. */
    function mMul(a, b){ return mOp(a, b, function(x, y){ return x * y; }); }
    /**
     * Desplaza la serie k velas: en la posición i deja el valor de la posición i-k (k positivo mira hacia atrás).
     * Devuelve un array alineado.
     */
    function mDesplazar(a, k){   // valor de hace k velas en la posición i (k > 0 mira hacia atrás)
      var out = nulos(a.length);
      for (var i = 0; i < a.length; i++){ var j = i - k; if (j >= 0 && j < a.length && esNum(a[j])) out[i] = a[j]; }
      return out;
    }

    // ---------- Volatilidad ----------
    /**
     * Calcula el rango verdadero (True Range) de cada vela: el mayor entre high-low y las distancias al cierre
     * anterior. La primera vela usa solo high-low.
     */
    function mRangoVerdadero(datos){
      var out = new Array(datos.length);
      for (var i = 0; i < datos.length; i++){
        var d = datos[i];
        out[i] = (i === 0) ? (d.high - d.low)
               : Math.max(d.high - d.low, Math.abs(d.high - datos[i-1].close), Math.abs(d.low - datos[i-1].close));
      }
      return out;
    }
    // ATR: MT5 usa media simple del rango verdadero; 'wilder' usa la media suavizada clásica
    /**
     * ATR (rango verdadero medio) de periodo n. Con metodo wilder usa la media suavizada clásica; en otro caso la
     * media simple, como MT5. La primera vela queda sin valor porque no tiene cierre previo.
     */
    function mATR(datos, n, metodo){
      var tr = mRangoVerdadero(datos);
      tr[0] = null;   // la primera vela no tiene cierre previo
      return (metodo === 'wilder') ? mSMMA(tr, n) : mSMA(tr, n);
    }
    /**
     * Bandas de Bollinger sobre el array a: devuelve {media, sup, inf} con la SMA de periodo n y bandas a k
     * desviaciones típicas.
     */
    function mBollinger(a, n, k){
      var med = mSMA(a, n), sd = mDesv(a, n);
      return {
        media: med,
        sup: mOp(med, sd, function(m, s){ return m + k * s; }),
        inf: mOp(med, sd, function(m, s){ return m - k * s; })
      };
    }

    // ---------- Osciladores ----------
    /**
     * RSI de Wilder de periodo n sobre el array a. Devuelve un array alineado con valores de 0 a 100 desde la vela
     * s0+n.
     */
    function mRSI(a, n){
      var out = nulos(a.length), s0 = primerValido(a);
      if (s0 < 0 || s0 + n >= a.length) return out;
      var g = 0, p = 0;
      for (var i = s0 + 1; i <= s0 + n; i++){ var c = a[i] - a[i-1]; if (c >= 0) g += c; else p -= c; }
      g /= n; p /= n;
      out[s0 + n] = rsiDe(g, p);
      for (var j = s0 + n + 1; j < a.length; j++){
        var cam = a[j] - a[j-1];
        g = (g * (n - 1) + (cam > 0 ? cam : 0)) / n;
        p = (p * (n - 1) + (cam < 0 ? -cam : 0)) / n;
        out[j] = rsiDe(g, p);
      }
      return out;
    }
    /** Convierte la ganancia media g y la pérdida media p en el valor del RSI (0 a 100); maneja el caso p = 0. */
    function rsiDe(g, p){ if (p === 0) return g === 0 ? 50 : 100; return 100 - 100 / (1 + g / p); }

    /**
     * MACD: línea = EMA rápida - EMA lenta; señal = EMA (o SMA si metodoSenal es sma) de la línea; histograma = línea
     * - señal. Devuelve {macd, senal, hist}.
     */
    function mMACD(a, rapida, lenta, senal, metodoSenal){
      var linea = mResta(mEMA(a, rapida), mEMA(a, lenta));
      var sen = (metodoSenal === 'sma') ? mSMA(linea, senal) : mEMA(linea, senal);
      return { macd: linea, senal: sen, hist: mResta(linea, sen) };
    }
    /**
     * Oscilador estocástico: %K bruto = posición del cierre en el rango máximo-mínimo de n velas, suavizado con SMA
     * de suav periodos; %D = SMA de %K con sucd periodos. Devuelve {k, d}.
     */
    function mEstocastico(datos, n, suav, sucd){
      var hh = mMax(columna(datos, 'high'), n), ll = mMin(columna(datos, 'low'), n);
      var bruto = nulos(datos.length);
      for (var i = 0; i < datos.length; i++){
        if (!esNum(hh[i])) continue;
        bruto[i] = (hh[i] - ll[i] === 0) ? 50 : (datos[i].close - ll[i]) / (hh[i] - ll[i]) * 100;
      }
      var k = suav > 1 ? mSMA(bruto, suav) : bruto;
      return { k: k, d: mSMA(k, sucd) };
    }
    /**
     * Índice del canal de materias primas (CCI) de periodo n sobre el precio típico (H+L+C)/3 con constante 0,015.
     * Devuelve un array alineado.
     */
    function mCCI(datos, n){
      var tp = precioDe(datos, 'hlc3'), med = mSMA(tp, n), out = nulos(datos.length);
      for (var i = 0; i < datos.length; i++){
        if (!esNum(med[i])) continue;
        var s = 0;
        for (var j = i - n + 1; j <= i; j++) s += Math.abs(tp[j] - med[i]);
        var md = s / n;
        out[i] = md === 0 ? 0 : (tp[i] - med[i]) / (0.015 * md);
      }
      return out;
    }
    /**
     * Williams %R de periodo n: posición del cierre dentro del rango reciente, entre -100 y 0. Devuelve un array
     * alineado.
     */
    function mWilliamsR(datos, n){
      var hh = mMax(columna(datos, 'high'), n), ll = mMin(columna(datos, 'low'), n), out = nulos(datos.length);
      for (var i = 0; i < datos.length; i++){
        if (!esNum(hh[i])) continue;
        out[i] = (hh[i] - ll[i] === 0) ? -50 : (hh[i] - datos[i].close) / (hh[i] - ll[i]) * -100;
      }
      return out;
    }
    /**
     * ADX y direccionales +DI/-DI de periodo n. metodo wilder suaviza con SMMA (ADXW) y metodo ema con EMA (estilo
     * MT5). Devuelve {adx, pdi, mdi}.
     */
    function mADX(datos, n, metodo){   // metodo 'wilder' (ADXW) o 'ema' (como el ADX de MT5)
      var N = datos.length, pdm = nulos(N), mdm = nulos(N), tr = nulos(N);
      for (var i = 1; i < N; i++){
        var arriba = datos[i].high - datos[i-1].high, abajo = datos[i-1].low - datos[i].low;
        pdm[i] = (arriba > abajo && arriba > 0) ? arriba : 0;
        mdm[i] = (abajo > arriba && abajo > 0) ? abajo : 0;
        tr[i] = Math.max(datos[i].high - datos[i].low, Math.abs(datos[i].high - datos[i-1].close), Math.abs(datos[i].low - datos[i-1].close));
      }
      var suav = (metodo === 'ema') ? mEMA : mSMMA;
      var atr = suav(tr, n), pS = suav(pdm, n), mS = suav(mdm, n);
      var pdi = nulos(N), mdi = nulos(N), dx = nulos(N);
      for (var j = 0; j < N; j++){
        if (!esNum(atr[j]) || atr[j] === 0) continue;
        pdi[j] = 100 * pS[j] / atr[j]; mdi[j] = 100 * mS[j] / atr[j];
        var s = pdi[j] + mdi[j];
        dx[j] = s === 0 ? 0 : 100 * Math.abs(pdi[j] - mdi[j]) / s;
      }
      return { adx: suav(dx, n), pdi: pdi, mdi: mdi };
    }
    /**
     * Momentum de periodo n: cierre actual como porcentaje del de hace n velas (100 = sin cambio). Devuelve un array
     * alineado.
     */
    function mMomentum(a, n){ return mOp(a, mDesplazar(a, n), function(x, y){ return y === 0 ? null : x / y * 100; }); }
    /**
     * Tasa de cambio (ROC) de periodo n: variación porcentual respecto a hace n velas. Devuelve un array alineado.
     */
    function mROC(a, n){ return mOp(a, mDesplazar(a, n), function(x, y){ return y === 0 ? null : (x / y - 1) * 100; }); }
    /** DeMarker de periodo n: compara máximos y mínimos consecutivos y devuelve un oscilador entre 0 y 1. */
    function mDeMarker(datos, n){
      var N = datos.length, mx = nulos(N), mn = nulos(N);
      for (var i = 1; i < N; i++){
        mx[i] = Math.max(datos[i].high - datos[i-1].high, 0);
        mn[i] = Math.max(datos[i-1].low - datos[i].low, 0);
      }
      var a = mSMA(mx, n), b = mSMA(mn, n);
      return mOp(a, b, function(x, y){ return (x + y) === 0 ? 0.5 : x / (x + y); });
    }
    /** TRIX: variación porcentual de una EMA triple de periodo n; filtra el ruido. Devuelve un array alineado. */
    function mTRIX(a, n){
      var e3 = mEMA(mEMA(mEMA(a, n), n), n);
      return mOp(e3, mDesplazar(e3, 1), function(x, y){ return y === 0 ? null : (x - y) / y * 100; });
    }
    /**
     * Índice de vigor relativo (RVI) de periodo n con su línea de señal (media ponderada de 4 valores). Devuelve
     * {rvi, senal}.
     */
    function mRVI(datos, n){
      var N = datos.length, num = nulos(N), den = nulos(N);
      /** Auxiliar de mRVI: aplica la función f a la vela de índice i y devuelve el resultado. */
      function v(i, f){ return f(datos[i]); }
      for (var i = 3; i < N; i++){
        /**
         * Auxiliares de mRVI: c devuelve cierre - apertura (cuerpo) y r devuelve máximo - mínimo (rango) de la vela d
         * que reciben.
         */
        var c = function(d){ return d.close - d.open; }, r = function(d){ return d.high - d.low; };
        num[i] = (v(i, c) + 2 * v(i-1, c) + 2 * v(i-2, c) + v(i-3, c)) / 6;
        den[i] = (v(i, r) + 2 * v(i-1, r) + 2 * v(i-2, r) + v(i-3, r)) / 6;
      }
      var rvi = mOp(mSMA(num, n), mSMA(den, n), function(x, y){ return y === 0 ? 0 : x / y; });
      var sen = nulos(N);
      for (var j = 3; j < N; j++){
        if (esNum(rvi[j]) && esNum(rvi[j-1]) && esNum(rvi[j-2]) && esNum(rvi[j-3]))
          sen[j] = (rvi[j] + 2 * rvi[j-1] + 2 * rvi[j-2] + rvi[j-3]) / 6;
      }
      return { rvi: rvi, senal: sen };
    }
    /**
     * Oscilador final (Ultimate) de Williams con tres periodos p1, p2 y p3: promedia la presión compradora frente al
     * rango verdadero con pesos 4, 2 y 1. Devuelve un array de 0 a 100.
     */
    function mUltimate(datos, p1, p2, p3){
      var N = datos.length, bp = nulos(N), tr = nulos(N);
      for (var i = 1; i < N; i++){
        var minL = Math.min(datos[i].low, datos[i-1].close), maxH = Math.max(datos[i].high, datos[i-1].close);
        bp[i] = datos[i].close - minL; tr[i] = maxH - minL;
      }
      /**
       * Auxiliar de mUltimate: devuelve la razón entre la suma móvil de la presión compradora y la del rango
       * verdadero en una ventana n.
       */
      function prom(n){ return mOp(mSumaVentana(bp, n), mSumaVentana(tr, n), function(x, y){ return y === 0 ? 0 : x / y; }); }
      var a1 = prom(p1), a2 = prom(p2), a3 = prom(p3), out = nulos(N);
      for (var j = 0; j < N; j++){
        if (esNum(a1[j]) && esNum(a2[j]) && esNum(a3[j])) out[j] = 100 * (4 * a1[j] + 2 * a2[j] + a3[j]) / 7;
      }
      return out;
    }
    /**
     * Aroon de periodo n: mide cuánto hace del último máximo y mínimo de la ventana de n+1 velas. Devuelve {up, dn}
     * con valores de 0 a 100.
     */
    function mAroon(datos, n){
      var N = datos.length, up = nulos(N), dn = nulos(N);
      for (var i = n; i < N; i++){
        var iH = i - n, iL = i - n;   // el extremo más reciente de la ventana de n+1 velas
        for (var j = i - n; j <= i; j++){
          if (datos[j].high >= datos[iH].high) iH = j;
          if (datos[j].low <= datos[iL].low) iL = j;
        }
        up[i] = 100 * (n - (i - iH)) / n;
        dn[i] = 100 * (n - (i - iL)) / n;
      }
      return { up: up, dn: dn };
    }
    /**
     * Oscilador de momento de Chande (CMO) de periodo n: (suma de subidas - suma de bajadas) / (suma de ambas) por
     * 100. Devuelve un array de -100 a 100.
     */
    function mCMO(a, n){
      var N = a.length, up = nulos(N), dn = nulos(N);
      for (var i = 1; i < N; i++){ var c = a[i] - a[i-1]; up[i] = c > 0 ? c : 0; dn[i] = c < 0 ? -c : 0; }
      return mOp(mSumaVentana(up, n), mSumaVentana(dn, n), function(u, d){ return (u + d) === 0 ? 0 : 100 * (u - d) / (u + d); });
    }
    /**
     * Estocástico del RSI: aplica la fórmula estocástica (nEst velas) al RSI de periodo nRsi y suaviza %K con sK y %D
     * con sD. Devuelve {k, d}.
     */
    function mEstocRSI(a, nRsi, nEst, sK, sD){
      var rsi = mRSI(a, nRsi), hh = mMax(rsi, nEst), ll = mMin(rsi, nEst), bruto = nulos(a.length);
      for (var i = 0; i < a.length; i++){
        if (!esNum(hh[i])) continue;
        bruto[i] = (hh[i] - ll[i] === 0) ? 50 : (rsi[i] - ll[i]) / (hh[i] - ll[i]) * 100;
      }
      var k = sK > 1 ? mSMA(bruto, sK) : bruto;
      return { k: k, d: mSMA(k, sD) };
    }

    // ---------- Volumen ----------
    /**
     * Volumen en balance (OBV): acumula el volumen sumándolo si el cierre sube y restándolo si baja. Devuelve un
     * array alineado.
     */
    function mOBV(datos){
      var out = new Array(datos.length), acc = 0;
      for (var i = 0; i < datos.length; i++){
        if (i > 0){
          if (datos[i].close > datos[i-1].close) acc += volDe(datos[i]);
          else if (datos[i].close < datos[i-1].close) acc -= volDe(datos[i]);
        }
        out[i] = acc;
      }
      return out;
    }
    /**
     * Calcula el flujo de dinero de cada vela: multiplicador de posición del cierre en el rango (de -1 a 1) por el
     * volumen. Es la base de A/D y CMF.
     */
    function mFlujoDinero(datos){   // multiplicador de flujo × volumen, por vela
      return datos.map(function(d){
        var r = d.high - d.low;
        return r === 0 ? 0 : ((d.close - d.low) - (d.high - d.close)) / r * volDe(d);
      });
    }
    /**
     * Línea de acumulación/distribución: suma acumulada del flujo de dinero de cada vela. Devuelve un array alineado.
     */
    function mAD(datos){
      var f = mFlujoDinero(datos), out = new Array(f.length), acc = 0;
      for (var i = 0; i < f.length; i++){ acc += f[i]; out[i] = acc; }
      return out;
    }
    /**
     * Flujo de dinero de Chaikin (CMF) de periodo n: suma del flujo de dinero entre suma del volumen en la ventana
     * (rango -1 a 1).
     */
    function mCMF(datos, n){
      var fl = mSumaVentana(mFlujoDinero(datos), n), vol = mSumaVentana(datos.map(volDe), n);
      return mOp(fl, vol, function(x, y){ return y === 0 ? 0 : x / y; });
    }
    /**
     * Índice de flujo de dinero (MFI) de periodo n: un RSI ponderado por volumen sobre el precio típico (0 a 100).
     */
    function mMFI(datos, n){
      var tp = precioDe(datos, 'hlc3'), N = datos.length, pos = nulos(N), neg = nulos(N);
      for (var i = 1; i < N; i++){
        var f = tp[i] * volDe(datos[i]);
        pos[i] = tp[i] > tp[i-1] ? f : 0;
        neg[i] = tp[i] < tp[i-1] ? f : 0;
      }
      return mOp(mSumaVentana(pos, n), mSumaVentana(neg, n), function(p, q){ return q === 0 ? (p === 0 ? 50 : 100) : 100 - 100 / (1 + p / q); });
    }
    /**
     * Precio medio ponderado por volumen (VWAP) que se reinicia cada día UTC. Si una vela no tiene volumen pondera
     * con 1. Devuelve un array alineado.
     */
    function mVWAP(datos){   // se reinicia cada día (UTC)
      var out = new Array(datos.length), dia = -1, sPV = 0, sV = 0;
      for (var i = 0; i < datos.length; i++){
        var d = datos[i], dk = Math.floor(d.time / 86400);
        if (dk !== dia) { dia = dk; sPV = 0; sV = 0; }
        var tp = (d.high + d.low + d.close) / 3, v = volDe(d) || 1;
        sPV += tp * v; sV += v;
        out[i] = sPV / sV;
      }
      return out;
    }

    // ---------- Tendencia avanzada ----------
    /**
     * Media adaptativa de Kaufman de periodo n con constantes rapida y lenta: usa el ratio de eficiencia para
     * acelerarse con tendencia y frenarse en rango.
     */
    function mAMA(a, n, rapida, lenta){   // media adaptativa de Kaufman
      var N = a.length, out = nulos(N);
      if (N <= n) return out;
      var sf = 2 / (rapida + 1), ss = 2 / (lenta + 1), prev = a[n - 1];
      out[n - 1] = prev;
      for (var i = n; i < N; i++){
        var dir = Math.abs(a[i] - a[i-n]), vol = 0;
        for (var j = i - n + 1; j <= i; j++) vol += Math.abs(a[j] - a[j-1]);
        var er = vol === 0 ? 0 : dir / vol, sc = Math.pow(er * (sf - ss) + ss, 2);
        prev = prev + sc * (a[i] - prev); out[i] = prev;
      }
      return out;
    }
    /**
     * VIDYA: media dinámica de índice variable que ajusta su velocidad según el valor absoluto del CMO (periodo nCmo)
     * y un periodo base nEma.
     */
    function mVIDYA(a, nCmo, nEma){
      var cmo = mCMO(a, nCmo), N = a.length, out = nulos(N), al = 2 / (nEma + 1), prev = null;
      for (var i = 0; i < N; i++){
        if (!esNum(cmo[i])) continue;
        var k = al * Math.abs(cmo[i]) / 100;
        prev = (prev === null) ? a[i] : a[i] * k + prev * (1 - k);
        out[i] = prev;
      }
      return out;
    }
    /**
     * FRAMA: media adaptativa fractal de periodo n (se fuerza par) que calcula la dimensión fractal del rango de las
     * velas y ajusta su factor de suavizado.
     */
    function mFRAMA(datos, n){
      if (n % 2) n += 1;
      var N = datos.length, out = nulos(N), h = n / 2, prev = null;
      for (var i = n - 1; i < N; i++){
        /**
         * Auxiliar de mFRAMA: devuelve el rango (máximo - mínimo) de las velas entre los índices a y b, ambos
         * incluidos.
         */
        function rng(a, b){ var mx = -Infinity, mn = Infinity; for (var j = a; j <= b; j++){ if (datos[j].high > mx) mx = datos[j].high; if (datos[j].low < mn) mn = datos[j].low; } return mx - mn; }
        var n1 = rng(i - h + 1, i) / h, n2 = rng(i - n + 1, i - h) / h, n3 = rng(i - n + 1, i) / n;
        var dim = (n1 > 0 && n2 > 0 && n3 > 0) ? (Math.log(n1 + n2) - Math.log(n3)) / Math.LN2 : 1;
        var al = Math.min(1, Math.max(0.01, Math.exp(-4.6 * (dim - 1))));
        var px = (datos[i].high + datos[i].low) / 2;
        prev = (prev === null) ? px : al * px + (1 - al) * prev;
        out[i] = prev;
      }
      return out;
    }
    /**
     * Parabolic SAR con factor de aceleración inicial paso y máximo. Devuelve {vals, cols}: el valor del SAR en cada
     * vela y su color (verde = alcista, rojo = bajista).
     */
    function mSAR(datos, paso, maximo){
      var N = datos.length, out = nulos(N), cols = new Array(N);
      if (N < 3) return { vals: out, cols: cols };
      var af = paso, largo = datos[1].close > datos[0].close;
      var sar = largo ? datos[0].low : datos[0].high, ep = largo ? datos[0].high : datos[0].low;
      for (var i = 2; i < N; i++){
        sar = sar + af * (ep - sar);
        if (largo){
          if (datos[i].low < sar){ largo = false; sar = ep; ep = datos[i].low; af = paso; }
          else {
            if (datos[i].high > ep){ ep = datos[i].high; af = Math.min(af + paso, maximo); }
            if (datos[i-1].low < sar) sar = datos[i-1].low;
            if (datos[i-2].low < sar) sar = datos[i-2].low;
          }
        } else {
          if (datos[i].high > sar){ largo = true; sar = ep; ep = datos[i].high; af = paso; }
          else {
            if (datos[i].low < ep){ ep = datos[i].low; af = Math.min(af + paso, maximo); }
            if (datos[i-1].high > sar) sar = datos[i-1].high;
            if (datos[i-2].high > sar) sar = datos[i-2].high;
          }
        }
        out[i] = sar; cols[i] = largo ? '#3fb950' : '#f85149';
      }
      return { vals: out, cols: cols };
    }
    /**
     * Supertrend de periodo n y multiplicador mult sobre el ATR de Wilder. Devuelve {vals, cols}: la línea de
     * tendencia y su color según la dirección.
     */
    function mSupertrend(datos, n, mult){
      var N = datos.length, atr = mATR(datos, n, 'wilder'), out = nulos(N), cols = new Array(N);
      var sup = null, inf = null, tend = 1, cierrePrev = null;
      for (var i = 0; i < N; i++){
        if (!esNum(atr[i])) continue;
        var hl2 = (datos[i].high + datos[i].low) / 2;
        var bs = hl2 + mult * atr[i], bi = hl2 - mult * atr[i];
        if (sup === null){ sup = bs; inf = bi; }
        else {
          sup = (bs < sup || cierrePrev > sup) ? bs : sup;
          inf = (bi > inf || cierrePrev < inf) ? bi : inf;
        }
        if (tend === 1 && datos[i].close < inf) tend = -1;
        else if (tend === -1 && datos[i].close > sup) tend = 1;
        out[i] = tend === 1 ? inf : sup;
        cols[i] = tend === 1 ? '#3fb950' : '#f85149';
        cierrePrev = datos[i].close;
      }
      return { vals: out, cols: cols };
    }
    /**
     * Canal de Donchian de periodo n: devuelve {sup, inf, med} con el máximo, el mínimo y el punto medio de las
     * últimas n velas.
     */
    function mDonchian(datos, n){
      var s = mMax(columna(datos, 'high'), n), i = mMin(columna(datos, 'low'), n);
      return { sup: s, inf: i, med: mOp(s, i, function(x, y){ return (x + y) / 2; }) };
    }
    /**
     * Fractales de Bill Williams con n velas a cada lado. Devuelve {arriba, abajo} con el máximo o mínimo en la vela
     * donde se confirma un fractal y null en las demás.
     */
    function mFractales(datos, n){   // n = velas a cada lado (2 en Bill Williams)
      var N = datos.length, arriba = nulos(N), abajo = nulos(N);
      for (var i = n; i < N - n; i++){
        var hi = true, lo = true;
        for (var j = 1; j <= n; j++){
          if (!(datos[i].high > datos[i-j].high && datos[i].high > datos[i+j].high)) hi = false;
          if (!(datos[i].low < datos[i-j].low && datos[i].low < datos[i+j].low)) lo = false;
        }
        if (hi) arriba[i] = datos[i].high;
        if (lo) abajo[i] = datos[i].low;
      }
      return { arriba: arriba, abajo: abajo };
    }
    // ZigZag por porcentaje: une los extremos cuando el precio retrocede al menos `pct` %
    /**
     * ZigZag por porcentaje: localiza pivotes cuando el precio retrocede al menos pct % y une los extremos con líneas
     * rectas. Devuelve un array alineado (el último tramo es provisional).
     */
    function mZigZag(datos, pct){
      var N = datos.length, out = nulos(N);
      if (N < 2) return out;
      var umbral = pct / 100, piv = [], tend = 0, extI = 0, extP = datos[0].close;
      for (var i = 1; i < N; i++){
        var h = datos[i].high, l = datos[i].low;
        if (tend === 0){
          if (h >= datos[0].low * (1 + umbral)) { piv.push([0, datos[0].low]); tend = 1; extI = i; extP = h; }
          else if (l <= datos[0].high * (1 - umbral)) { piv.push([0, datos[0].high]); tend = -1; extI = i; extP = l; }
        } else if (tend === 1){
          if (h > extP) { extP = h; extI = i; }
          else if (l <= extP * (1 - umbral)) { piv.push([extI, extP]); tend = -1; extP = l; extI = i; }
        } else {
          if (l < extP) { extP = l; extI = i; }
          else if (h >= extP * (1 + umbral)) { piv.push([extI, extP]); tend = 1; extP = h; extI = i; }
        }
      }
      if (tend !== 0) piv.push([extI, extP]);   // último tramo, aún provisional
      for (var k = 0; k + 1 < piv.length; k++){
        var a = piv[k], b = piv[k+1];
        for (var x = a[0]; x <= b[0]; x++) out[x] = a[1] + (b[1] - a[1]) * (x - a[0]) / Math.max(1, b[0] - a[0]);
      }
      return out;
    }
    // Puntos pivote clásicos del día anterior (en D1 o superior, de la vela anterior)
    /**
     * Puntos pivote clásicos (P, R1, R2, S1, S2) calculados con el máximo, mínimo y cierre del día anterior (UTC).
     * Devuelve un objeto con un array alineado por nivel.
     */
    function mPivotes(datos){
      var N = datos.length, claves = [], dias = {}, orden = [];
      for (var i = 0; i < N; i++){
        var dk = Math.floor(datos[i].time / 86400);
        claves.push(dk);
        if (!dias[dk]) { dias[dk] = { h: datos[i].high, l: datos[i].low, c: datos[i].close }; orden.push(dk); }
        else { var d = dias[dk]; if (datos[i].high > d.h) d.h = datos[i].high; if (datos[i].low < d.l) d.l = datos[i].low; d.c = datos[i].close; }
      }
      var res = { p: nulos(N), r1: nulos(N), r2: nulos(N), s1: nulos(N), s2: nulos(N) }, prevDe = {};
      for (var q = 1; q < orden.length; q++) prevDe[orden[q]] = dias[orden[q-1]];
      for (var j = 0; j < N; j++){
        var pd = prevDe[claves[j]];
        if (!pd) continue;
        var P = (pd.h + pd.l + pd.c) / 3;
        res.p[j] = P; res.r1[j] = 2 * P - pd.l; res.s1[j] = 2 * P - pd.h;
        res.r2[j] = P + (pd.h - pd.l); res.s2[j] = P - (pd.h - pd.l);
      }
      return res;
    }
    // Canal de regresión lineal de las últimas n velas
    /**
     * Canal de regresión lineal de las últimas n velas con bandas a k desviaciones. Devuelve {med, sup, inf}; solo
     * las últimas n posiciones llevan valor.
     */
    function mRegresion(datos, n, k){
      var N = datos.length, out = { med: nulos(N), sup: nulos(N), inf: nulos(N) };
      n = Math.min(n, N);
      if (n < 3) return out;
      var i0 = N - n, sx = 0, sy = 0, sxy = 0, sxx = 0;
      for (var i = 0; i < n; i++){ var y = datos[i0 + i].close; sx += i; sy += y; sxy += i * y; sxx += i * i; }
      var m = (n * sxy - sx * sy) / (n * sxx - sx * sx), b = (sy - m * sx) / n, res = 0;
      for (var j = 0; j < n; j++){ var e = datos[i0 + j].close - (b + m * j); res += e * e; }
      var sd = Math.sqrt(res / n);
      for (var t = 0; t < n; t++){
        var v = b + m * t;
        out.med[i0 + t] = v; out.sup[i0 + t] = v + k * sd; out.inf[i0 + t] = v - k * sd;
      }
      return out;
    }

/* -------------------------------------------------------------------------------------------------------
   ------------------------------ FIN Piña y Jara 30_indicadores_calculo .JS -----------------------------
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
