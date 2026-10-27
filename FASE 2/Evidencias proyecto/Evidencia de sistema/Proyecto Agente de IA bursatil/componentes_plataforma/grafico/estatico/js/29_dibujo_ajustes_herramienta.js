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
   ------------------------- INICIO Piña y Jara 29_dibujo_ajustes_herramienta .JS ------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Dibujo: ventana de ajustes de cada herramienta (doble clic): Estilo, Texto, Coordenadas y Visibilidad
    // ---- La línea de tendencia admite extenderse a izquierda y derecha ----
    // Se vuelve a registrar la herramienta 'trend' (tendencia) con la opción ext: si el usuario marca extender a la izquierda o a la derecha, el segmento se prolonga con lejos() hasta fuera de la pantalla.
    registroHerramienta('trend', { n: 2, col: '#2962ff', ext: true, forma: function(el, P, S){
      if (P.length < 2) return [{ k: 'l', pts: P }];
      return [{ k: 'l', pts: [el.extIzq ? lejos(P[1], P[0]) : P[0], el.extDer ? lejos(P[0], P[1]) : P[1]] }];
    } });
    // TITULO MARCAR

    // ---- Qué opciones tiene cada herramienta ----
    /** Marca con una bandera (por ejemplo 'rell' o 'etiquetas') las herramientas registradas cuyos ids se pasan separados por espacios; ignora los ids que no existen en REG. Recibe la cadena de ids y el nombre de la bandera. */
    function marcar(ids, flag){ ids.split(' ').forEach(function(id){ if (REGISTRO[id]) REGISTRO[id][flag] = true; }); }
    // Herramientas cuyo relleno se puede ajustar en la ventana de ajustes.
    marcar('flat disjoint pf_andrews pf_schiff pf_mschiff pf_inside xabcd cypher headshoulders trianglepat regresion timecycles rotrect circle arc polyline projection price_range date_range', 'rell');
    // Herramientas con etiquetas de texto que se pueden ocultar.
    marcar('infoline xabcd cypher abcd threedrives headshoulders trianglepat ell_impulse ell_abc ell_triangle ell_wxy ell_wxyxz forecast projection price_range date_range long_pos short_pos pf_andrews pf_schiff pf_mschiff pf_inside', 'etiquetas');
    // La línea de información admite extenderse a los lados.
    marcar('infoline', 'ext');
    // Posiciones larga y corta con colores propios de objetivo y stop.
    marcar('long_pos short_pos', 'coloresPos');
    // Campos de ajuste de los tipos de dibujo antiguos (que no están en el registro REG): lista de propiedades editables por tipo.
    var AJ_VIEJOS = {
      ray: ['color', 'ancho', 'estilo'], extended: ['color', 'ancho', 'estilo'], angle: ['color', 'ancho', 'estilo'], hline: ['color', 'ancho', 'estilo'],
      hray: ['color', 'ancho', 'estilo'], vline: ['color', 'ancho', 'estilo'], crossline: ['color', 'ancho', 'estilo'], arrow: ['color', 'ancho', 'estilo'],
      channel: ['color', 'ancho', 'estilo', 'relleno'], rectangle: ['color', 'ancho', 'relleno'], ellipse: ['color', 'ancho', 'relleno'], triangle: ['color', 'ancho', 'relleno'],
      text: ['color', 'tamano', 'negrita'], brush: ['color', 'ancho'], highlighter: ['color', 'ancho'],
      arrow_up: ['color', 'ancho'], arrow_down: ['color', 'ancho'], arrow_left: ['color', 'ancho'], arrow_right: ['color', 'ancho'], measure: []
    };
    // Tamaño de letra por defecto de las herramientas con texto.
    var TAMANO_DEF = { text: 13, text_anchored: 16, table: 12, emoji: 30 };
    // Etiqueta del campo de grosor cuando no es "Grosor de línea" (en flechas es el tamaño, en pincel y resaltador el grosor).
    var ETIQUETA_ANCHO = { arrow_up: 'Tamaño', arrow_down: 'Tamaño', arrow_left: 'Tamaño', arrow_right: 'Tamaño', brush: 'Grosor', highlighter: 'Grosor' };

    // Elementos de la ventana de ajustes: fondo (#dibujo-configuracion-superposicion), cuerpo (#dibujo-configuracion-cuerpo) y pestañas (#dibujo-configuracion-pestanas).
    var dibujoSuperposicion = document.getElementById('dibujo-configuracion-superposicion'), dibujoCuerpo = document.getElementById('dibujo-configuracion-cuerpo'), dibujoPestanas = document.getElementById('dibujo-configuracion-pestanas');
    // Estado de la ventana: índice del dibujo editado, copia JSON para cancelar y pestaña activa.
    var dibujoIndice = null, dibujoSnap = null, dibujoPestana = 'estilo';

    // TITULO NOMBRE HERRAMIENTA

    /** Devuelve el nombre visible de una herramienta tomándolo del texto de su botón en el menú de herramientas; si no existe devuelve el propio tipo. */
    function nombreHerramienta(tipo){
      var it = document.querySelector('.tvtool-desplegable-elemento[data-tool="' + tipo + '"]');
      return it ? it.textContent.trim() : tipo;
    }
    // TITULO CAMPOS DE

    /** Calcula la lista de campos editables (color, ancho, estilo, relleno, etiquetas, tamaño, niveles...) de un dibujo, según su descriptor en REG o la tabla AJ_VIEJOS para los tipos antiguos; sin duplicados. Recibe el dibujo. */
    function camposDe(el){
      var r = REGISTRO[el.tipo], c = [];
      if (r) {
        if (!r.sinColor) c.push('color');
        if (!r.sinGrosor) c.push('ancho', 'estilo');
        if (r.fib && r.sinGrosor !== true) { /* los niveles usan el grosor y el estilo de línea */ }
        if (r.coloresPos) c.push('coloresPos');
        if (r.rell) c.push('relleno');
        if (r.ext) c.push('ext');
        if (r.fib) c.push('tendencia', 'relleno');
        if (r.fib && r.invertir) c.push('invertir');
        if (r.divisiones) c.push('divisiones');
        if (r.etiquetas) c.push(r.niveles ? 'etiqFib' : 'etiq');
        if (r.tamano) c.push('tamano');
        if (el.tipo === 'text_anchored') c.push('negrita');
        if (r.niveles) c.push('niveles');
      } else c = (AJ_VIEJOS[el.tipo] || []).slice();
      return c.filter(function(x, i){ return c.indexOf(x) === i; });
    }
    // Tipos de línea que pueden llevar un texto encima (girado a lo largo de la línea).
    // Las herramientas de línea pueden llevar un texto encima (se dibuja girado a lo largo de la línea)
    var LINEAS_TEXTO = { trend: 1, ray: 1, extended: 1, angle: 1, arrow: 1, infoline: 1, hline: 1, hray: 1, vline: 1 };
    // TITULO TIENE TEXTO

    /** Indica si el dibujo admite pestaña de texto: los textos, las líneas de LINEAS_TEXTO y las herramientas registradas con texto. */
    function tieneTexto(el){ var r = REGISTRO[el.tipo]; return el.tipo === 'text' || !!LINEAS_TEXTO[el.tipo] || !!(r && r.texto); }

    // TITULO CERRAR DIB

    /** Cierra la ventana de ajustes y borra el estado de edición. */
    function cerrarDibujo(){ dibujoSuperposicion.style.display = 'none'; dibujoIndice = null; dibujoSnap = null; }
    // TITULO EL DIB

    /** Devuelve el dibujo que se está editando en la ventana de ajustes, o null si no hay. */
    function elDibujo(){ return dibujoIndice === null ? null : (elementosDibujados[dibujoIndice] || null); }
    // TITULO CAMBIO DIB

    /** Aplica en vivo un cambio hecho en la ventana: repinta el lienzo y refresca la barra de estilos del dibujo seleccionado. */
    function cambioDibujo(){
      var el = elDibujo(); if (!el) return;
      redibujarTodo();
      if (typeof refrescarBarra === 'function') refrescarBarra(elementoSeleccionado());
    }
    // TITULO CANCELAR DIB

    /** Cancela la edición: restaura el dibujo desde la copia guardada al abrir la ventana y la cierra. */
    function cancelarDibujo(){
      if (dibujoIndice !== null && dibujoSnap && elementosDibujados[dibujoIndice]) { elementosDibujados[dibujoIndice] = JSON.parse(dibujoSnap); redibujarTodo(); }
      cerrarDibujo();
    }
    // TITULO ACEPTAR DIB

    /** Acepta la edición: confirma el cambio (entra al historial para deshacer) y cierra la ventana. */
    function aceptarDibujo(){ if (dibujoIndice !== null) confirmarCambio(); cerrarDibujo(); }

    // TITULO C

    // ---------- Componentes ----------
    // ---------- Componentes ----------
    /** Auxiliar de DOM: crea un elemento con la etiqueta, clase y texto opcionales y lo devuelve. */
    function c_(tag, cls, txt){ var e = document.createElement(tag); if (cls) e.className = cls; if (txt !== undefined) e.textContent = txt; return e; }
    // TITULO FILA DIB

    /** Agrega al cuerpo de la ventana una fila con una etiqueta y su control (y un control extra opcional). Devuelve la fila. */
    function filaDibujo(etiqueta, control, extra){
      var f = c_('div', 'configuracion-fila'); f.appendChild(c_('span', '', etiqueta)); var d = c_('div', 'configuracion-controles'); d.appendChild(control); if (extra) d.appendChild(extra); f.appendChild(d); dibujoCuerpo.appendChild(f); return f;
    }
    // TITULO CHECK DIB

    /** Crea una casilla con texto que llama a alCambiar(marcada) al cambiar y aplica el cambio en vivo; se agrega al destino indicado o al cuerpo. Devuelve la etiqueta. */
    function revisarDibujo(texto, marcada, alCambiar, destino){
      var l = c_('label', 'configuracion-revisar'); var i = document.createElement('input'); i.type = 'checkbox'; i.checked = marcada;
      i.addEventListener('change', function(){ alCambiar(i.checked); cambioDibujo(); });
      l.appendChild(i); l.appendChild(c_('span', '', texto)); (destino || dibujoCuerpo).appendChild(l); return l;
    }
    // TITULO COLOR DIB

    /** Crea un selector de color inicializado con el valor (o azul si no es hexadecimal) que llama a alCambiar(color) al elegir. Devuelve el input. */
    function colorDibujo(valor, alCambiar){
      var i = document.createElement('input'); i.type = 'color'; i.value = /^#[0-9a-fA-F]{6}$/.test(valor) ? valor : '#2962ff';
      i.addEventListener('input', function(){ alCambiar(i.value); cambioDibujo(); }); return i;
    }
    // TITULO COLOR HEX

    /** Devuelve el valor si es un color hexadecimal de 6 dígitos válido; si no, el valor por defecto. */
    function colorHex(v, def){ return (typeof v === 'string' && /^#[0-9a-fA-F]{6}$/.test(v)) ? v : def; }
    // TITULO SEL DIB

    /** Crea un menú desplegable con las opciones [valor, texto], marca la actual y llama a alCambiar(valor) al cambiar. Devuelve el select. */
    function seleccionDibujo(opciones, actual, alCambiar){
      var s = document.createElement('select');
      opciones.forEach(function(o){ var op = c_('option', '', o[1]); op.value = o[0]; if (String(o[0]) === String(actual)) op.selected = true; s.appendChild(op); });
      s.addEventListener('change', function(){ alCambiar(s.value); cambioDibujo(); }); return s;
    }
    // TITULO NUM DIB

    /** Crea un campo numérico limitado a [min, max] con el paso dado; al cambiar corrige valores inválidos y llama a alCambiar(número). Devuelve el input. */
    function numeroDibujo(valor, min, max, paso, alCambiar){
      var i = document.createElement('input'); i.type = 'number'; i.value = valor; i.min = min; i.max = max; i.step = paso;
      i.addEventListener('change', function(){ var v = Number(i.value); if (!isFinite(v)) v = valor; v = Math.min(max, Math.max(min, v)); i.value = v; alCambiar(v); cambioDibujo(); }); return i;
    }
    // TITULO SEC DIB

    /** Agrega un título de sección al cuerpo de la ventana. */
    function seccionDibujo(t){ dibujoCuerpo.appendChild(c_('div', 'configuracion-seccion', t)); }

    // Opciones del tipo de línea en la ventana de ajustes: [valor, texto].
    var ESTILOS_DIBUJO = [['solid', 'Sólida'], ['dash', 'Discontinua'], ['dot', 'Punteada']];

    // TITULO PESTANA ESTILO DIB

    /** Construye la pestaña Estilo según los campos del dibujo: color, colores de objetivo/stop, grosor, tipo de línea, línea de tendencia, relleno con color y opacidad, extensión, inversión, divisiones, etiquetas, tamaño, negrita y editor de niveles. */
    function pestanaEstiloDibujo(el){
      var campos = camposDe(el), tipo = el.tipo;
      if (!campos.length) { dibujoCuerpo.appendChild(c_('div', 'configuracion-vacio', 'Esta herramienta no tiene opciones de estilo.')); return; }
      if (campos.indexOf('color') >= 0) filaDibujo('Color', colorDibujo(colorHex(valorEfectivo(el, 'color'), '#2962ff'), function(v){ el.color = v; }));
      if (campos.indexOf('coloresPos') >= 0) {
        filaDibujo('Color del objetivo', colorDibujo(colorHex(el.colObj, '#089981'), function(v){ el.colObj = v; }));
        filaDibujo('Color del stop', colorDibujo(colorHex(el.colStop, '#f23645'), function(v){ el.colStop = v; }));
      }
      if (campos.indexOf('ancho') >= 0) {
        var anchoMaximo = (tipo === 'highlighter') ? 60 : 12;
        filaDibujo(ETIQUETA_ANCHO[tipo] || 'Grosor de línea', numeroDibujo(valorEfectivo(el, 'ancho'), 0.5, anchoMaximo, 0.5, function(v){ el.ancho = v; }));
      }
      if (campos.indexOf('estilo') >= 0) filaDibujo('Tipo de línea', seleccionDibujo(ESTILOS_DIBUJO, valorEfectivo(el, 'estilo'), function(v){ el.estilo = v; }));
      if (campos.indexOf('tendencia') >= 0) {
        var f = c_('div', 'configuracion-fila'); revisarDibujo('Línea de tendencia', el.lineaTendencia !== false, function(v){ el.lineaTendencia = v; }, f);
        f.appendChild(colorDibujo(colorHex(el.colorTendencia, '#787b86'), function(v){ el.colorTendencia = v; })); dibujoCuerpo.appendChild(f);
      }
      if (campos.indexOf('relleno') >= 0) {
        var base = colorHex(valorEfectivo(el, 'color'), '#2962ff'), fr = c_('div', 'configuracion-fila');
        revisarDibujo('Relleno', el.relleno !== false, function(v){ el.relleno = v; }, fr);
        var ctl = c_('div', 'configuracion-controles');
        ctl.appendChild(colorDibujo(colorHex(el.rellenoColor, base), function(v){ el.rellenoColor = v; }));
        var op = document.createElement('input'); op.type = 'range'; op.min = 2; op.max = 60; op.value = Math.round((el.rellenoOp !== undefined ? el.rellenoOp : 0.1) * 100); op.title = 'Opacidad';
        op.addEventListener('input', function(){ el.rellenoOp = Number(op.value) / 100; cambioDibujo(); }); ctl.appendChild(op);
        fr.appendChild(ctl); dibujoCuerpo.appendChild(fr);
      }
      if (campos.indexOf('ext') >= 0) {
        revisarDibujo('Extender la línea a la izquierda', !!el.extIzq, function(v){ el.extIzq = v; });
        revisarDibujo('Extender la línea a la derecha', !!el.extDer, function(v){ el.extDer = v; });
      }
      if (campos.indexOf('invertir') >= 0) revisarDibujo(tipo === 'fib_spiral' ? 'Girar en sentido contrario' : 'Invertir niveles', !!el.invertir, function(v){ el.invertir = v; });
      if (campos.indexOf('divisiones') >= 0) filaDibujo('Divisiones', numeroDibujo(el.divisiones || 8, 2, 24, 1, function(v){ el.divisiones = Math.round(v); }));
      if (campos.indexOf('etiq') >= 0) revisarDibujo('Mostrar etiquetas', el.etiq !== false, function(v){ el.etiq = v; });
      if (campos.indexOf('etiqFib') >= 0) {
        revisarDibujo('Mostrar niveles', el.mostrarNivel !== false, function(v){ el.mostrarNivel = v; });
        if (['fib', 'fib_extension'].indexOf(tipo) >= 0) revisarDibujo('Mostrar precios', el.mostrarPrecio !== false, function(v){ el.mostrarPrecio = v; });
      }
      if (campos.indexOf('tamano') >= 0) filaDibujo('Tamaño del texto', numeroDibujo(el.tamano || TAMANO_DEF[tipo] || 13, 8, 80, 1, function(v){ el.tamano = Math.round(v); }));
      if (campos.indexOf('negrita') >= 0) revisarDibujo('Negrita', !!el.negrita, function(v){ el.negrita = v; });
      if (campos.indexOf('niveles') >= 0) editorNiveles(el);
    }

    // TITULO EDITOR NIVELES

    /** Construye el editor de niveles (por ejemplo de Fibonacci): una casilla, un valor y un color por nivel; cada cambio guarda la lista en el dibujo. Usa nivelesDe(el), definida en el fragmento de Fibonacci. */
    function editorNiveles(el){
      seccionDibujo('Niveles');
      var lista = nivelesDe(el).map(function(l){ return { v: l.v, on: l.on, c: l.c }; });
      /** Auxiliar local guardar: copia la lista editada de niveles al dibujo y aplica el cambio en vivo. */
      function guardar(){ el.niveles = lista.map(function(l){ return { v: l.v, on: l.on, c: l.c }; }); cambioDibujo(); }
      var grid = c_('div', 'configuracion-niveles');
      lista.forEach(function(l, i){
        var celda = c_('div', 'configuracion-nivel');
        var ck = document.createElement('input'); ck.type = 'checkbox'; ck.checked = l.on; ck.addEventListener('change', function(){ l.on = ck.checked; guardar(); });
        var nm = document.createElement('input'); nm.type = 'number'; nm.step = 'any'; nm.value = l.v;
        nm.addEventListener('change', function(){ var v = Number(nm.value); if (isFinite(v)) { l.v = v; guardar(); } else nm.value = l.v; });
        var co = document.createElement('input'); co.type = 'color'; co.value = colorHex(l.c, '#787b86'); co.addEventListener('input', function(){ l.c = co.value; guardar(); });
        celda.appendChild(ck); celda.appendChild(nm); celda.appendChild(co); grid.appendChild(celda);
      });
      dibujoCuerpo.appendChild(grid);
    }

    // TITULO PESTANA TEXTO

    /** Construye la pestaña Texto: un campo (o área multilínea) para editar el texto del dibujo o el texto sobre la línea, y para las líneas también su color, tamaño y negrita. */
    function pestanaTexto(el){
      var multi = !!(REGISTRO[el.tipo] && REGISTRO[el.tipo].multilinea), esLinea = !!LINEAS_TEXTO[el.tipo], clave = esLinea ? 'textoLinea' : 'texto';
      var campo = document.createElement(multi ? 'textarea' : 'input'); if (!multi) campo.type = 'text'; else campo.rows = 5;
      campo.className = 'configuracion-texto'; campo.value = el[clave] === undefined ? (esLinea ? '' : ((REGISTRO[el.tipo] && REGISTRO[el.tipo].textoDef) || '')) : el[clave];
      if (esLinea) campo.placeholder = 'Texto sobre la línea';
      campo.addEventListener('input', function(){ el[clave] = campo.value; cambioDibujo(); });
      dibujoCuerpo.appendChild(c_('div', 'configuracion-seccion', multi ? 'Contenido (una fila por línea, columnas separadas por |)' : 'Texto'));
      dibujoCuerpo.appendChild(campo);
      if (esLinea) {
        filaDibujo('Color del texto', colorDibujo(colorHex(el.colorTexto, colorHex(valorEfectivo(el, 'color'), '#2962ff')), function(v){ el.colorTexto = v; }));
        filaDibujo('Tamaño', numeroDibujo(el.tamanoTexto || 12, 8, 60, 1, function(v){ el.tamanoTexto = Math.round(v); }));
        revisarDibujo('Negrita', !!el.negritaTexto, function(v){ el.negritaTexto = v; });
      }
      setTimeout(function(){ try { campo.focus(); } catch (e) {} }, 0);
    }

    // TITULO FMT FH

    // ---------- Coordenadas ----------
    // ---------- Coordenadas ----------
    /** Formatea un tiempo UNIX como fecha y hora UTC con formato AAAA-MM-DD HH:MM. */
    function formatoFH(t){ return new Date(t * 1000).toISOString().slice(0, 16).replace('T', ' '); }
    // TITULO PARSE FH

    /** Interpreta un texto de fecha y hora (UTC por defecto) y devuelve el tiempo UNIX en segundos, o null si es inválido. */
    function parseFH(s){ var t = Date.parse(String(s).trim().replace(' ', 'T') + (/Z|[+-]\d\d:?\d\d$/.test(s) ? '' : 'Z')); return isFinite(t) ? t / 1000 : null; }
    // TITULO FILA PUNTO

    /** Agrega una fila editable con el precio y/o la fecha y hora de un punto. Recibe el título y las funciones para leer y escribir el tiempo y el precio; las entradas inválidas se revierten. */
    function filaPunto(titulo, tiempoObtener, tiempoFijar, precioObtener, precioFijar){
      var f = c_('div', 'configuracion-fila configuracion-punto'); f.appendChild(c_('span', '', titulo)); var d = c_('div', 'configuracion-controles');
      if (precioObtener) {
        var pr_ = document.createElement('input'); pr_.type = 'number'; pr_.step = 'any'; pr_.value = +Number(precioObtener()).toFixed(DIGITS + 1); pr_.title = 'Precio';
        pr_.addEventListener('change', function(){ var v = Number(pr_.value); if (isFinite(v)) { precioFijar(v); cambioDibujo(); } else pr_.value = precioObtener(); }); d.appendChild(pr_);
      }
      if (tiempoObtener) {
        var tm = document.createElement('input'); tm.type = 'text'; tm.value = formatoFH(tiempoObtener()); tm.title = 'Fecha y hora (UTC): AAAA-MM-DD HH:MM';
        tm.addEventListener('change', function(){ var v = parseFH(tm.value); if (v !== null) { tiempoFijar(v); cambioDibujo(); } else tm.value = formatoFH(tiempoObtener()); }); d.appendChild(tm);
      }
      f.appendChild(d); dibujoCuerpo.appendChild(f);
    }
    // TITULO PESTANA COORDENADAS

    /** Construye la pestaña Coordenadas: posición en porcentaje para los elementos fijados a la pantalla, precio para las horizontales, fecha para las verticales y precio y fecha por punto para el resto (máximo 40 puntos en los de nº variable). Los trazos libres no se pueden editar. */
    function pestanaCoordenadas(el){
      var r = REGISTRO[el.tipo], tipo = el.tipo;
      if (tipo === 'brush' || tipo === 'highlighter') { dibujoCuerpo.appendChild(c_('div', 'configuracion-vacio', 'Un trazo libre no tiene coordenadas editables.')); return; }
      if (r && r.ancla) {
        filaDibujo('Posición horizontal (%)', numeroDibujo(Math.round((el.fx || 0) * 100), 0, 100, 1, function(v){ el.fx = v / 100; }));
        filaDibujo('Posición vertical (%)', numeroDibujo(Math.round((el.fy || 0) * 100), 0, 100, 1, function(v){ el.fy = v / 100; })); return;
      }
      if (tipo === 'hline') { filaPunto('Precio', null, null, function(){ return el.price; }, function(v){ el.price = v; }); return; }
      if (tipo === 'vline') { filaPunto('Fecha y hora', function(){ return el.time; }, function(v){ el.time = v; }); return; }
      if (tipo === 'crossline' || tipo === 'text') { filaPunto('Punto', function(){ return el.time; }, function(v){ el.time = v; }, function(){ return el.price; }, function(v){ el.price = v; }); return; }
      if (r && r.v) {
        var pts = el.puntos || [];
        pts.slice(0, 40).forEach(function(q, i){ filaPunto('Punto ' + (i + 1), function(){ return q[0]; }, function(v){ q[0] = Math.round(v); }, function(){ return q[1]; }, function(v){ q[1] = v; }); });
        if (pts.length > 40) dibujoCuerpo.appendChild(c_('div', 'configuracion-nota', 'Se muestran los 40 primeros puntos de ' + pts.length + '.'));
        return;
      }
      var hay = false;
      for (var i = 1; i <= 9; i++){
        if (el['time' + i] === undefined) break; hay = true;
        // Cierre inmediato que captura el valor de i para cada fila de punto.
        (function(n){ filaPunto('Punto ' + n, function(){ return el['time' + n]; }, function(v){ el['time' + n] = v; }, function(){ return el['price' + n]; }, function(v){ el['price' + n] = v; }); })(i);
      }
      if (!hay) dibujoCuerpo.appendChild(c_('div', 'configuracion-vacio', 'Esta herramienta no tiene coordenadas editables.'));
    }

    // TITULO PESTANA VISIBILIDAD DIB

    // ---------- Visibilidad por temporalidad ----------
    // ---------- Visibilidad por temporalidad ----------
    /** Construye la pestaña Visibilidad: por cada grupo de temporalidades (GRUPOS_TF) una casilla y un rango mínimo/máximo con campos numéricos y control deslizante doble. Usa validarVisibilidad y GRUPOS_TF del fragmento de visibilidad. */
    function pestanaVisibilidadDibujo(el){
      el.vis = validarVisibilidad(el.vis);
      GRUPOS_TEMPORALIDAD.forEach(function(g){
        var r = el.vis[g[0]], f = c_('div', 'configuracion-visible');
        var ck = c_('label', 'configuracion-revisar'); var ci = document.createElement('input'); ci.type = 'checkbox'; ci.checked = r[0];
        ci.addEventListener('change', function(){ r[0] = ci.checked; cambioDibujo(); }); ck.appendChild(ci); ck.appendChild(c_('span', '', g[1])); f.appendChild(ck);
        var mn = document.createElement('input'), mx = document.createElement('input'), doble = c_('div', 'configuracion-doble'), rmn = document.createElement('input'), rmx = document.createElement('input');
        mn.type = mx.type = 'number'; mn.min = mx.min = g[2]; mn.max = mx.max = g[3]; mn.value = r[1]; mx.value = r[2];
        rmn.type = rmx.type = 'range'; rmn.min = rmx.min = g[2]; rmn.max = rmx.max = g[3]; rmn.value = r[1]; rmx.value = r[2]; doble.appendChild(rmn); doble.appendChild(rmx);
        /** Auxiliar local pista: pinta el degradado de la pista del control doble según el rango elegido. */
        function pista(){ var s = g[3] - g[2] || 1, a = (r[1] - g[2]) / s * 100, b = (r[2] - g[2]) / s * 100; doble.style.background = 'linear-gradient(to right,#3a3f47 ' + a + '%,#d1d4dc ' + a + '%,#d1d4dc ' + b + '%,#3a3f47 ' + b + '%)'; }
        /** Auxiliar local fija: normaliza y limita el rango mínimo/máximo, lo guarda en el dibujo, sincroniza campos y deslizadores y aplica el cambio. */
        function fija(a, b, quien){
          a = Math.round(Number(a)); b = Math.round(Number(b)); if (!isFinite(a)) a = r[1]; if (!isFinite(b)) b = r[2];
          a = Math.min(g[3], Math.max(g[2], a)); b = Math.min(g[3], Math.max(g[2], b)); if (a > b) { if (quien === 'min') a = b; else b = a; }
          r[1] = a; r[2] = b; mn.value = rmn.value = a; mx.value = rmx.value = b; pista(); cambioDibujo();
        }
        mn.addEventListener('change', function(){ fija(mn.value, r[2], 'min'); }); mx.addEventListener('change', function(){ fija(r[1], mx.value, 'max'); });
        rmn.addEventListener('input', function(){ fija(rmn.value, r[2], 'min'); }); rmx.addEventListener('input', function(){ fija(r[1], rmx.value, 'max'); });
        pista(); f.appendChild(mn); f.appendChild(doble); f.appendChild(mx); dibujoCuerpo.appendChild(f);
      });
      dibujoCuerpo.appendChild(c_('div', 'configuracion-nota', 'El dibujo solo se muestra en las temporalidades marcadas y dentro del rango indicado (p. ej. Horas 1–1: solo en H1).'));
    }

    // TITULO PINTAR AJUSTES DIB

    /** Redibuja el contenido de la ventana de ajustes: título con el nombre de la herramienta, pestañas disponibles (Estilo, Texto si procede, Coordenadas y Visibilidad) y el cuerpo de la pestaña activa. */
    function pintarAjustesDibujo(){
      var el = elDibujo(); if (!el) return;
      document.getElementById('dibujo-configuracion-titulo').textContent = nombreHerramienta(el.tipo);
      var pestanas = [['estilo', 'Estilo']];
      if (tieneTexto(el)) pestanas.push(['texto', 'Texto']);
      pestanas.push(['coord', 'Coordenadas'], ['vis', 'Visibilidad']);
      if (!pestanas.some(function(p){ return p[0] === dibujoPestana; })) dibujoPestana = 'estilo';
      dibujoPestanas.innerHTML = '';
      pestanas.forEach(function(p){
        var b = c_('button', 'configuracion-pestana' + (dibujoPestana === p[0] ? ' on' : ''), p[1]);
        b.addEventListener('click', function(){ dibujoPestana = p[0]; pintarAjustesDibujo(); }); dibujoPestanas.appendChild(b);
      });
      dibujoCuerpo.innerHTML = '';
      if (dibujoPestana === 'estilo') pestanaEstiloDibujo(el); else if (dibujoPestana === 'texto') pestanaTexto(el); else if (dibujoPestana === 'coord') pestanaCoordenadas(el); else pestanaVisibilidadDibujo(el);
    }

    // TITULO ABRIR AJUSTES DIBUJO

    /** Abre la ventana de ajustes para el dibujo indicado (no si no existe o está bloqueado): cierra el editor de texto, guarda una copia para poder cancelar y muestra la ventana en la pestaña pedida (Estilo por defecto). */
    function abrirAjustesDibujo(idx, pestana){
      var el = elementosDibujados[idx]; if (!el || bloqueado) return;
      if (editorRegistro) cerrarEditorRegistro();
      dibujoIndice = idx; dibujoSnap = JSON.stringify(el); dibujoPestana = pestana || 'estilo';
      pintarAjustesDibujo(); dibujoSuperposicion.style.display = 'flex';
    }

    // Botones de la ventana: cerrar y cancelar descartan los cambios; aceptar los confirma.
    document.getElementById('dibujo-configuracion-cerrar').addEventListener('click', cancelarDibujo);
    document.getElementById('dibujo-configuracion-cancelar').addEventListener('click', cancelarDibujo);
    document.getElementById('dibujo-configuracion-aceptar').addEventListener('click', aceptarDibujo);
    // Botón Restablecer: borra todas las personalizaciones del dibujo (color, grosor, relleno, niveles, visibilidad, textos...) para volver a los valores por defecto.
    document.getElementById('dibujo-configuracion-reiniciar').addEventListener('click', function(){
      var el = elDibujo(); if (!el) return;
      ['color', 'ancho', 'estilo', 'relleno', 'rellenoColor', 'rellenoOp', 'extIzq', 'extDer', 'etiq', 'niveles', 'tamano', 'negrita', 'lineaTendencia', 'colorTendencia',
       'mostrarNivel', 'mostrarPrecio', 'invertir', 'divisiones', 'vis', 'colObj', 'colStop', 'textoLinea', 'colorTexto', 'tamanoTexto', 'negritaTexto'].forEach(function(k){ delete el[k]; });
      cambioDibujo(); pintarAjustesDibujo();
    });
    // Clic en el fondo oscuro cierra la ventana sin guardar.
    dibujoSuperposicion.addEventListener('click', function(e){ if (e.target === dibujoSuperposicion) cancelarDibujo(); });
    // Teclado dentro de la ventana: Escape cancela; el resto de teclas no se propagan al gráfico salvo en los campos de texto.
    dibujoSuperposicion.addEventListener('keydown', function(e){
      if (e.key === 'Escape') { e.stopPropagation(); cancelarDibujo(); }
      else if (e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'INPUT') e.stopPropagation();   // Supr/Ctrl+Z no deben actuar sobre el gráfico
    });

    // botón de ajustes en la barra de estilo del dibujo seleccionado
    // botón de ajustes en la barra de estilo del dibujo seleccionado
    // Función autoejecutable que agrega a la barra de estilos el botón de engranaje que abre la ventana de ajustes del dibujo seleccionado; no hace nada si la barra aún no existe.
    (function(){
      if (typeof barraEl === 'undefined' || typeof bloqueCuenta === 'undefined') return;
      var b = document.createElement('button'); b.className = 'barra-lateral-boton'; b.title = 'Ajustes (o doble clic)';
      b.innerHTML = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>';
      b.addEventListener('click', function(){ if (seleccionadoId !== null) abrirAjustesDibujo(seleccionadoId); });
      bloqueCuenta.insertBefore(b, bloqueCuenta.firstChild);
    })();

    // ---------- Texto sobre las líneas ----------
    // ---------- Texto sobre las líneas ----------
    // Zona del "+ Añadir texto" de la línea seleccionada, para detectar el clic (null si no hay).
    var marcadorCaja = null;   // zona del "+ Añadir texto" de la línea seleccionada (para detectar el clic)
    // TITULO ANCLA TEXTO LINEA

    /** Calcula dónde y con qué giro se pinta el texto sobre una línea: extremo derecho de la horizontal, inicio del rayo horizontal, centro de la vertical (girado 90 grados) o punto medio de la línea inclinada sin dejar el texto boca abajo. Devuelve { x, y, ang, al } o null. */
    function anclaTextoLinea(el){
      var g = geom(el); if (!g) return null;
      var ap = areaTrazado(), t = el.tipo;
      if (t === 'hline') return ok(g.y) ? { x: ap.w - 12, y: g.y, ang: 0, al: 'right' } : null;
      if (t === 'hray') return ok(g.x1, g.y1) ? { x: Math.min(g.x1 + 12, ap.w - 90), y: g.y1, ang: 0, al: 'left' } : null;
      if (t === 'vline') return ok(g.x) ? { x: g.x, y: ap.h / 2, ang: -Math.PI / 2, al: 'center' } : null;
      if (!ok(g.x1, g.y1, g.x2, g.y2)) return null;
      var ang = Math.atan2(g.y2 - g.y1, g.x2 - g.x1);
      if (ang > Math.PI / 2 || ang < -Math.PI / 2) ang += Math.PI;   // el texto nunca queda boca abajo
      return { x: (g.x1 + g.x2) / 2, y: (g.y1 + g.y2) / 2, ang: ang, al: 'center' };
    }
    // TITULO PINTAR TEXTO LINEA

    /** Pinta el texto de una línea girado a lo largo de ella; si no tiene texto y está seleccionada muestra "+ Añadir texto" atenuado y guarda su zona en phCaja. Recibe contexto, dibujo y si está seleccionado. */
    function pintarTextoLinea(c, el, sel){
      var txt = el.textoLinea, hayTexto = !!txt;
      if (!hayTexto && !sel) return;
      var a = anclaTextoLinea(el); if (!a) return;
      var sz = el.tamanoTexto || 12, col = el.colorTexto || valorEfectivo(el, 'color');
      c.save(); c.translate(a.x, a.y); c.rotate(a.ang);
      c.font = (el.negritaTexto ? 'bold ' : '') + sz + 'px sans-serif'; c.textAlign = a.al; c.textBaseline = 'bottom';
      var mostrado = hayTexto ? txt : '+ Añadir texto';
      c.globalAlpha = hayTexto ? 1 : 0.55; c.fillStyle = col; c.fillText(mostrado, 0, -6);
      var w = c.measureText(mostrado).width; c.restore();
      if (!hayTexto && sel && elementosDibujados.indexOf(el) >= 0) marcadorCaja = { el: el, x: a.x, y: a.y, ang: a.ang, al: a.al, w: w, h: sz };
    }
    // Se extienden dibujarElemento y pintar para el texto sobre las líneas.
    var dibujarAntesTextoLinea = dibujarElemento;
    /** Versión de dibujarElemento que tras pintar el dibujo añade el texto sobre la línea si el tipo lo admite y es visible en la temporalidad actual. */
    dibujarElemento = function(c, el, sel, hov){
      dibujarAntesTextoLinea(c, el, sel, hov);
      if (LINEAS_TEXTO[el.tipo] && dibujoVisibleTemporalidad(el)) pintarTextoLinea(c, el, sel);
    };
    // Guarda la versión anterior de pintar.
    var pintarAntesTextoLinea = pintar;
    /** Versión de pintar que reinicia la zona del "+ Añadir texto" antes de pintar (cada fotograma la vuelve a calcular). */
    pintar = function(){ marcadorCaja = null; pintarAntesTextoLinea(); };
    // Clic sobre el "+ Añadir texto" de la línea seleccionada (fase de captura): abre la ventana de ajustes en la pestaña Texto. Convierte el clic al sistema de coordenadas girado de la caja para comprobar si cae dentro.
    window.addEventListener('mousedown', function(e){
      if (!marcadorCaja || e.button !== 0 || bloqueado || activoHerramienta !== 'cross' || !contenedorEl.contains(e.target)) return;
      if (e.target.closest && e.target.closest('.tradingview-ui')) return;
      if (elementoSeleccionado() !== marcadorCaja.el) return;
      var pos = posicionRaton(e), dx = pos.x - marcadorCaja.x, dy = pos.y - marcadorCaja.y, cartera = Math.cos(marcadorCaja.ang), sa = Math.sin(marcadorCaja.ang);
      var lx = dx * cartera + dy * sa, ly = -dx * sa + dy * cartera;
      var x0 = marcadorCaja.al === 'center' ? -marcadorCaja.w / 2 : (marcadorCaja.al === 'right' ? -marcadorCaja.w : 0);
      if (lx >= x0 - 3 && lx <= x0 + marcadorCaja.w + 3 && ly >= -marcadorCaja.h - 9 && ly <= 3) {
        e.preventDefault(); e.stopPropagation();
        var idx = elementosDibujados.indexOf(marcadorCaja.el);
        if (idx >= 0) abrirAjustesDibujo(idx, 'texto');
      }
    }, true);

/* -------------------------------------------------------------------------------------------------------
   -------------------------- FIN Piña y Jara 29_dibujo_ajustes_herramienta .JS --------------------------
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
