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
  // Límites del plan del usuario (los inyecta Python con herramientas/permisos_plan.py): plan, indicadores por gráfico, símbolos comparados, velas
  // del backtest (null = sin tope), si el plan incluye Replay y los textos de aviso ya escritos para cada límite.
  var PLAN = __PLAN_JSON__;

  /**
   * Abre un cuadro centrado con el motivo del bloqueo (por ejemplo, que el plan no deja agregar más indicadores) y el botón
   * «Ir al plan correspondiente», que lleva a la vista de Planes de Streamlit. Reutiliza el mismo cuadro si ya existe.
   */
  function avisoPlan(texto){
    var vel = document.getElementById('aviso-plan');
    if (!vel) {
      vel = document.createElement('div');
      vel.id = 'aviso-plan';
      vel.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:0;z-index:99999;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.55);' +
        'font:13px/1.45 system-ui,sans-serif;';
      vel.innerHTML = '<div style="max-width:380px;width:84%;padding:20px 22px;background:#1b2634;color:#e6edf3;border:1px solid #30363d;border-top:3px solid #d29922;' +
        'border-radius:10px;box-shadow:0 10px 36px rgba(0,0,0,.6);text-align:center;">' +
        '<div style="font-size:30px;line-height:1;">\uD83D\uDD12</div>' +
        '<div id="aviso-plan-texto" style="margin:10px 0 16px;"></div>' +
        '<button id="aviso-plan-ir" style="background:#2ea043;color:#fff;border:0;border-radius:6px;padding:8px 16px;font:600 13px system-ui,sans-serif;cursor:pointer;margin-right:8px;">Ir al plan correspondiente</button>' +
        '<button id="aviso-plan-cerrar" style="background:transparent;color:#9fb0c3;border:1px solid #30363d;border-radius:6px;padding:8px 14px;font:13px system-ui,sans-serif;cursor:pointer;">Cerrar</button></div>';
      document.body.appendChild(vel);
      var cerrar = function(){ vel.style.display = 'none'; };
      vel.addEventListener('click', function(e){ if (e.target === vel) cerrar(); });
      vel.querySelector('#aviso-plan-cerrar').addEventListener('click', cerrar);
      vel.querySelector('#aviso-plan-ir').addEventListener('click', function(){
        cerrar();
        // El botón «Planes» de la barra lateral de Streamlit vive en el documento padre; al pulsarlo se abre la vista de Planes.
        try { var b = window.parent.document.querySelector('.st-key-navegacion_boton_planes button'); if (b) b.click(); } catch (e) {}
      });
    }
    vel.querySelector('#aviso-plan-texto').textContent = texto;
    vel.style.display = 'flex';
  }

  // Formato de precio de lightweight-charts: precisión según los decimales del símbolo y paso mínimo de 10^-DIGITS.
  var PF = { type: 'price', precision: DIGITS, minMove: Math.pow(10, -DIGITS) };

  // Temporalidad activa (M1..MN1).
  var temporalidadActual = "H1";
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
  var sondeoEnCurso = false;
  var repeticionActivo = false;   // true mientras el modo Replay está activo: apaga las actualizaciones en vivo y las órdenes reales (62/63_replay_*.js)

  // Indicadores activos: cada uno es una instancia { uid, id, p (parámetros), c (colores), w (grosor), oculto }.
  // El catálogo (qué indicadores existen y cómo se calculan) está en 33_indicadores_catalogo.js
  var indicadorActivos = [];
  var configuracionIndicadorRaw = null;   // lo recordado entre recargas; se valida cuando el catálogo ya está cargado
  // TITULO SERIALIZAR INSTANCIA

  /** Convierte una instancia de indicador activo en el objeto mínimo que se guarda en localStorage (id, parámetros, colores, grosor, estilos, visibilidad, oculto). Recibe la instancia y devuelve el objeto serializable. */
  function serializarInstancia(i){   // lo que se recuerda de cada indicador (formato de nuevaInstancia, en el catálogo)
    return { id: i.id, p: i.p, c: i.c, w: i.w, s: i.s, v: i.v, pr: i.pr, et: i.et ? 1 : 0, sl: i.sl ? 1 : 0, vis: i.vis, o: i.oculto ? 1 : 0 };
  }
  var INDICADOR_LEGADO = {      // formato antiguo (un true/false por indicador) -> instancias, con los colores de entonces
    sma20: ['sma', { periodo: 20 }], sma50: ['sma', { periodo: 50 }, '#3399ff'], sma200: ['sma', { periodo: 200 }, '#a78bfa'],
    ema20: ['ema', { periodo: 20 }], ema50: ['ema', { periodo: 50 }, '#e056fd'], bollinger: ['bollinger', {}],
    rsi: ['rsi', {}], macd: ['macd', {}], atr: ['atr', {}], stochastic: ['stoch', {}], parabolic: ['sar', {}]
  };


  // Paneles de osciladores abiertos: id -> { el (contenedor), chart (gráfico propio), s (series) }.
  var PANELES = {};   // paneles de osciladores abiertos: id -> { el, chart, s }

  // Configuración del gráfico que se recuerda entre recargas del iframe (temporalidad, tipo, indicadores)
  // Clave de localStorage bajo la que se recuerda la configuración del gráfico.
  var CONFIGURACION_KEY = 'pj_grafico_cfg';
  var configuracionRango = -1;   // índice del botón de rango activo (-1 = ninguno)
  var configuracionComparar = [];       // símbolos comparados que se recordaron
  var listaCompararGuardada = [];  // símbolos comparados ahora mismo (los guarda guardarConfig)
  var modoComparar = false;   // hay símbolos comparados: el eje pasa a % y los indicadores sobre el precio se ocultan
  /** Lee la configuración guardada en localStorage (temporalidad, nº de barras, tipo, rango, comparaciones, indicadores) y la valida antes de aplicarla a las variables de estado; acepta también el formato legado de indicadores. Se ejecuta una sola vez al cargar; ante cualquier error la ignora. */
  (function leerConfiguracion(){
    try {
      var c = JSON.parse(localStorage.getItem(CONFIGURACION_KEY) || 'null');
      if (!c) return;
      if (['M1','M5','M15','M30','H1','H4','D1','W1','MN1'].indexOf(c.tf) >= 0) temporalidadActual = c.tf;
      if (typeof c.n === 'number' && c.n >= 50 && c.n <= 5000) nBarrasActual = c.n;
      if (['candlestick','hollow','bars','line','area','heikin'].indexOf(c.tipo) >= 0) tipoActual = c.tipo;
      if (typeof c.rango === 'number') configuracionRango = c.rango;
      if (Array.isArray(c.cmp)) configuracionComparar = c.cmp.filter(function(x){ return typeof x === 'string' && /^[A-Za-z0-9._#+\-]{1,24}$/.test(x); }).slice(0, 5);
      if (Array.isArray(c.ind2)) configuracionIndicadorRaw = c.ind2.slice(0, 40);
      else if (c.ind && typeof c.ind === 'object') {
        configuracionIndicadorRaw = Object.keys(INDICADOR_LEGADO).filter(function(k){ return c.ind[k] === true; })
          .map(function(k){ return { id: INDICADOR_LEGADO[k][0], p: INDICADOR_LEGADO[k][1], c: INDICADOR_LEGADO[k][2] ? [INDICADOR_LEGADO[k][2]] : null }; });
      }
    } catch (e) {}
  })();
  // TITULO GUARDAR CONFIG

  /** Guarda en localStorage la configuración actual (temporalidad, barras, tipo, botón de rango activo, indicadores serializados y símbolos comparados) para restaurarla tras recargar el iframe. Los errores de almacenamiento se ignoran. */
  function guardarConfiguracion(){
    try {
      var rg = -1;
      document.querySelectorAll('.tvrange').forEach(function(b, i){ if (b.classList.contains('active')) rg = i; });
      localStorage.setItem(CONFIGURACION_KEY, JSON.stringify({ tf: temporalidadActual, n: nBarrasActual, tipo: tipoActual, rango: rg, ind2: indicadorActivos.map(serializarInstancia), cmp: listaCompararGuardada }));
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
