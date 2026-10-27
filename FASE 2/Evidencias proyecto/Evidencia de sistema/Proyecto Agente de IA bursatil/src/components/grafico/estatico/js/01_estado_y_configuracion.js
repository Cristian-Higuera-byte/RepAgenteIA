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
   --------------------------- INICIO Piña y Jara 01_estado_y_configuracion .JS --------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Estado global y configuración recordada
// Envoltura (IIFE) que abre el ámbito compartido por todos los fragmentos JS; se cierra en 99_cierre.js.
(function(){
  // URL base de la API local que sirve las velas, posiciones y demás datos (la inyecta Python).
  var API = __API_URL_JS__;
  // Símbolo que muestra este gráfico (inyectado por Python).
  var SIMBOLO = __SIMBOLO_JS__;
  // Número de decimales del símbolo (inyectado por Python).
  var DIGITS = __DIGITS__;
  // Tamaño de un pip en unidades de precio (inyectado por Python).
  var PIP = __PIP__;

  // Formato de precio de lightweight-charts: precisión según los decimales del símbolo y paso mínimo de 10^-DIGITS.
  var PF = { type: 'price', precision: DIGITS, minMove: Math.pow(10, -DIGITS) };

  // Temporalidad activa (M1..MN1).
  var tfActual = "H1";
  // Cantidad de velas pedidas a la API.
  var nBarrasActual = 1500;
  // Tipo de serie de precio activo: candlestick, hollow, bars, line, area o heikin.
  var tipoActual = "candlestick";
  // Últimas velas cargadas (arreglo de objetos time/open/high/low/close/volume); lo leen indicadores, dibujo y backtest.
  var datosActuales = [];

  // Contador de cargas: cada carga nueva lo incrementa para descartar respuestas viejas que lleguen tarde.
  var cargaId = 0;
  // Indica que hay una carga completa de velas en curso.
  var cargando = false;
  // Indica que hay una consulta periódica (polling) en curso, para no solaparlas.
  var pollEnCurso = false;
  var rpActivo = false;   // true mientras el modo Replay está activo: apaga las actualizaciones en vivo y las órdenes reales (62/63_replay_*.js)

  // Indicadores activos: cada uno es una instancia { uid, id, p (parámetros), c (colores), w (grosor), oculto }.
  // El catálogo (qué indicadores existen y cómo se calculan) está en 33_indicadores_catalogo.js
  var indActivos = [];
  var cfgIndRaw = null;   // lo recordado entre recargas; se valida cuando el catálogo ya está cargado
  /** Convierte una instancia de indicador activo en el objeto mínimo que se guarda en localStorage (id, parámetros, colores, grosor, estilos, visibilidad, oculto). Recibe la instancia y devuelve el objeto serializable. */
  function serializarInstancia(i){   // lo que se recuerda de cada indicador (formato de nuevaInstancia, en el catálogo)
    return { id: i.id, p: i.p, c: i.c, w: i.w, s: i.s, v: i.v, pr: i.pr, et: i.et ? 1 : 0, sl: i.sl ? 1 : 0, vis: i.vis, o: i.oculto ? 1 : 0 };
  }
  var IND_LEGADO = {      // formato antiguo (un true/false por indicador) -> instancias, con los colores de entonces
    sma20: ['sma', { periodo: 20 }], sma50: ['sma', { periodo: 50 }, '#3399ff'], sma200: ['sma', { periodo: 200 }, '#a78bfa'],
    ema20: ['ema', { periodo: 20 }], ema50: ['ema', { periodo: 50 }, '#e056fd'], bollinger: ['bollinger', {}],
    rsi: ['rsi', {}], macd: ['macd', {}], atr: ['atr', {}], stochastic: ['stoch', {}], parabolic: ['sar', {}]
  };


  // Paneles de osciladores abiertos: id -> { el (contenedor), chart (gráfico propio), s (series) }.
  var PANES = {};   // paneles de osciladores abiertos: id -> { el, chart, s }

  // Configuración del gráfico que se recuerda entre recargas del iframe (temporalidad, tipo, indicadores)
  // Clave de localStorage bajo la que se recuerda la configuración del gráfico.
  var CFG_KEY = 'pj_grafico_cfg';
  var cfgRango = -1;   // índice del botón de rango activo (-1 = ninguno)
  var cfgComparar = [];       // símbolos comparados que se recordaron
  var listaCmpGuardada = [];  // símbolos comparados ahora mismo (los guarda guardarConfig)
  var modoComparar = false;   // hay símbolos comparados: el eje pasa a % y los indicadores sobre el precio se ocultan
  /** Lee la configuración guardada en localStorage (temporalidad, nº de barras, tipo, rango, comparaciones, indicadores) y la valida antes de aplicarla a las variables de estado; acepta también el formato legado de indicadores. Se ejecuta una sola vez al cargar; ante cualquier error la ignora. */
  (function leerConfig(){
    try {
      var c = JSON.parse(localStorage.getItem(CFG_KEY) || 'null');
      if (!c) return;
      if (['M1','M5','M15','M30','H1','H4','D1','W1','MN1'].indexOf(c.tf) >= 0) tfActual = c.tf;
      if (typeof c.n === 'number' && c.n >= 50 && c.n <= 5000) nBarrasActual = c.n;
      if (['candlestick','hollow','bars','line','area','heikin'].indexOf(c.tipo) >= 0) tipoActual = c.tipo;
      if (typeof c.rango === 'number') cfgRango = c.rango;
      if (Array.isArray(c.cmp)) cfgComparar = c.cmp.filter(function(x){ return typeof x === 'string' && /^[A-Za-z0-9._#+\-]{1,24}$/.test(x); }).slice(0, 5);
      if (Array.isArray(c.ind2)) cfgIndRaw = c.ind2.slice(0, 40);
      else if (c.ind && typeof c.ind === 'object') {
        cfgIndRaw = Object.keys(IND_LEGADO).filter(function(k){ return c.ind[k] === true; })
          .map(function(k){ return { id: IND_LEGADO[k][0], p: IND_LEGADO[k][1], c: IND_LEGADO[k][2] ? [IND_LEGADO[k][2]] : null }; });
      }
    } catch (e) {}
  })();
  /** Guarda en localStorage la configuración actual (temporalidad, barras, tipo, botón de rango activo, indicadores serializados y símbolos comparados) para restaurarla tras recargar el iframe. Los errores de almacenamiento se ignoran. */
  function guardarConfig(){
    try {
      var rg = -1;
      document.querySelectorAll('.tvrange').forEach(function(b, i){ if (b.classList.contains('active')) rg = i; });
      localStorage.setItem(CFG_KEY, JSON.stringify({ tf: tfActual, n: nBarrasActual, tipo: tipoActual, rango: rg, ind2: indActivos.map(serializarInstancia), cmp: listaCmpGuardada }));
    } catch (e) {}
  }


/* -------------------------------------------------------------------------------------------------------
   ---------------------------- FIN Piña y Jara 01_estado_y_configuracion .JS ----------------------------
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
