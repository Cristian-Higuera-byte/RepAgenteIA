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
   ---------------------------- INICIO Piña y Jara 23_dibujo_barra_estilos .JS ---------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Dibujo: barra de estilos, copiar/pegar, ocultar y bloquear
    // Indica si los dibujos se muestran (false = ocultos con el botón del ojo).
    var dibujosVisibles = true;
    // Portapapeles interno: JSON del dibujo copiado con Ctrl+C (o con Duplicar), a la espera de pegarse.
    var portapapeles = null;

    // Colores de la paleta rápida de la barra de estilos.
    var PALETA_DIBUJO = ['#2962ff', '#58a6ff', '#089981', '#3fb950', '#f5c518', '#ff9800', '#f23645', '#a78bfa', '#ffffff'];
    // Grosores (px) ofrecidos en la barra de estilos.
    var ANCHOS_DIBUJO = [1, 2, 3, 4];
    // Color por defecto de cada tipo de dibujo cuando no tiene color propio.
    var COLOR_DEF = { trend: '#2962ff', ray: '#2962ff', extended: '#2962ff', angle: '#a78bfa', hline: '#f5c518',
      hray: '#f5c518', vline: '#58a6ff', crossline: '#8b949e', channel: '#2962ff', rectangle: '#58a6ff',
      ellipse: '#58a6ff', triangle: '#58a6ff', arrow: '#3fb950', text: '#ffffff', brush: '#ff9800', highlighter: 'rgba(255,235,59,0.35)' };
    // Grosor por defecto de los tipos que no usan 2 px.
    var ANCHO_DEF = { hline: 1.5, hray: 1.5, vline: 1.5, crossline: 1, brush: 3, highlighter: 18 };
    // Estilo de trazo por defecto de los tipos que no son continuos.
    var ESTILO_DEF = { hline: 'dash', vline: 'dash', crossline: 'dash' };
    // Tipos de dibujo a los que se les puede cambiar el estilo de trazo (continuo, raya, punto).
    var TIPOS_TRAZO = { trend: 1, ray: 1, extended: 1, angle: 1, hline: 1, hray: 1, vline: 1, crossline: 1, channel: 1, arrow: 1 };
    // Tipos de dibujo a los que se les puede cambiar el grosor.
    var TIPOS_ANCHO = { trend: 1, ray: 1, extended: 1, angle: 1, hline: 1, hray: 1, vline: 1, crossline: 1, channel: 1, arrow: 1,
      rectangle: 1, ellipse: 1, triangle: 1, brush: 1, highlighter: 1 };
    // Tipos de dibujo a los que se les puede cambiar el color.
    var TIPOS_COLOR = { trend: 1, ray: 1, extended: 1, angle: 1, hline: 1, hray: 1, vline: 1, crossline: 1, channel: 1, arrow: 1,
      rectangle: 1, ellipse: 1, triangle: 1, text: 1, brush: 1, highlighter: 1 };

    // Hoja de estilo con las reglas de la barra de estilos flotante (#tradingview-stylebar), sus botones (.sb-*) y el botón de ocultar (.tvtool.on).
    var estiloUI2 = document.createElement('style');
    estiloUI2.textContent = [
      '.tvtool.on { background: rgba(139,92,246,0.18); color: #a78bfa; }',
      '#tradingview-stylebar { position: absolute; top: 10px; left: calc(50% + 22px); transform: translateX(-50%); z-index: 30; display: none; align-items: center; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 5px 8px; box-shadow: 0 6px 20px rgba(0,0,0,0.5); user-select: none; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; }',
      '#tradingview-stylebar.show { display: flex; }',
      '#tradingview-stylebar .barra-lateral-bloque { display: flex; align-items: center; gap: 3px; padding-right: 8px; margin-right: 8px; border-right: 1px solid #30363d; }',
      '#tradingview-stylebar .barra-lateral-bloque.ultimo { border-right: none; margin-right: 0; padding-right: 0; }',
      '.barra-lateral-color { width: 18px; height: 18px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; padding: 0; }',
      '.barra-lateral-color.on { border-color: #ffffff; }',
      '.barra-lateral-ancho, .barra-lateral-estilo, .barra-lateral-boton { background: transparent; border: 1px solid transparent; color: #8b949e; width: 30px; height: 26px; border-radius: 5px; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0; }',
      '.barra-lateral-ancho.on, .barra-lateral-estilo.on { background: rgba(88,166,255,0.18); color: #58a6ff; border-color: rgba(88,166,255,0.3); }',
      '.barra-lateral-boton:hover { background: rgba(255,255,255,0.08); color: #ffffff; }',
      '.barra-lateral-boton.peligro:hover { color: #f85149; }',
      '.barra-lateral-boton svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }',
      '#tradingview-stylebar input[type=color] { width: 22px; height: 22px; border: none; padding: 0; background: none; cursor: pointer; }',
      '#tradingview-actions .tvbtn[disabled] { opacity: 0.35; cursor: default; }',
      /* Pantallas tactiles (clase pj-tactil): la barra se ajusta al ancho del grafico (antes quedaba centrada y mas ancha: Duplicar y Eliminar salian por el borde)
         y se desplaza si no cabe; las acciones pasan al principio para que Eliminar siempre se vea. */
      'html.pj-tactil #tradingview-stylebar { left: 46px; right: 6px; transform: none; max-width: none; overflow-x: auto; }',
      'html.pj-tactil #tradingview-stylebar > * { flex-shrink: 0; }',
      'html.pj-tactil #tradingview-stylebar .barra-lateral-bloque.ultimo { order: -1; border-right: 1px solid #30363d; margin-right: 8px; padding-right: 8px; }',
      'html.pj-tactil .barra-lateral-boton, html.pj-tactil .barra-lateral-ancho, html.pj-tactil .barra-lateral-estilo { width: 36px; height: 34px; }',
      '.barra-lateral-boton[data-accion="cerrar"] { display: none; }',
      'html.pj-tactil .barra-lateral-boton[data-accion="cerrar"] { display: flex; }'
    ].join(' ');
    document.head.appendChild(estiloUI2);

    // TITULO VALOR EFECTIVO

    /** Devuelve el valor efectivo de una propiedad de estilo (color, ancho o estilo) de un dibujo: el propio si existe o el valor por defecto de su tipo. Recibe el dibujo y el nombre de la propiedad. */
    function valorEfectivo(el, k){
      if (el[k] !== undefined && el[k] !== null) return el[k];
      if (k === 'color') return COLOR_DEF[el.tipo] || '#2962ff';
      if (k === 'ancho') return ANCHO_DEF[el.tipo] || 2;
      return ESTILO_DEF[el.tipo] || 'solid';
    }

    // Contenedor del gráfico (#tradingview-principal-lienzo-area) donde se inserta la barra de estilos.
    var areaDibujoEl = document.getElementById('tradingview-principal-lienzo-area');
    // Barra de estilos flotante (#tradingview-stylebar), visible solo cuando hay un dibujo seleccionado.
    var barraEl = document.createElement('div');
    barraEl.id = 'tradingview-stylebar';

    // Bloque de colores: un botón por color de la paleta más un selector de color personalizado.
    var bloqueColor = document.createElement('div'); bloqueColor.className = 'barra-lateral-bloque';
    PALETA_DIBUJO.forEach(function(col){
      var b = document.createElement('button');
      b.className = 'barra-lateral-color'; b.title = 'Color'; b.setAttribute('data-color', col); b.style.background = col;
      bloqueColor.appendChild(b);
    });
    // Selector de color personalizado de la barra.
    var pickerEl = document.createElement('input');
    pickerEl.type = 'color'; pickerEl.title = 'Color personalizado'; pickerEl.value = '#2962ff';
    bloqueColor.appendChild(pickerEl);

    // Bloque de grosores: un botón con una línea del grosor correspondiente por cada valor de ANCHOS_DIB.
    var bloqueAncho = document.createElement('div'); bloqueAncho.className = 'barra-lateral-bloque';
    ANCHOS_DIBUJO.forEach(function(a){
      var b = document.createElement('button');
      b.className = 'barra-lateral-ancho'; b.title = 'Grosor ' + a + ' px'; b.setAttribute('data-ancho', String(a));
      b.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18"><path d="M3 12h18" stroke="currentColor" stroke-width="' + a + '" fill="none"/></svg>';
      bloqueAncho.appendChild(b);
    });

    // Bloque de estilos de trazo: continuo, discontinuo y punteado.
    var bloqueEstilo = document.createElement('div'); bloqueEstilo.className = 'barra-lateral-bloque';
    [['solid', '', 'Línea continua'], ['dash', '6 4', 'Línea discontinua'], ['dot', '1.5 3.5', 'Línea punteada']].forEach(function(par){
      var b = document.createElement('button');
      b.className = 'barra-lateral-estilo'; b.title = par[2]; b.setAttribute('data-estilo', par[0]);
      b.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18"><path d="M2 12h20" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="' + par[1] + '"/></svg>';
      bloqueEstilo.appendChild(b);
    });

    // Bloque de acciones: botones Duplicar y Eliminar.
    var bloqueCuenta = document.createElement('div'); bloqueCuenta.className = 'barra-lateral-bloque ultimo';
    var bDup = document.createElement('button');
    bDup.className = 'barra-lateral-boton'; bDup.title = 'Duplicar'; bDup.setAttribute('data-accion', 'duplicar');
    bDup.innerHTML = '<svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h8"/></svg>';
    var bDel = document.createElement('button');
    bDel.className = 'barra-lateral-boton peligro'; bDel.title = 'Eliminar'; bDel.setAttribute('data-accion', 'borrar');
    bDel.innerHTML = '<svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>';
    bloqueCuenta.appendChild(bDup); bloqueCuenta.appendChild(bDel);
    // Botón «Ocultar barra» (solo pantallas táctiles, ver la hoja de estilos): quita la selección del dibujo y con ello esta barra; en táctil no hay clic en vacío fiable.
    var bCerrar = document.createElement('button');
    bCerrar.className = 'barra-lateral-boton'; bCerrar.title = 'Ocultar barra'; bCerrar.setAttribute('data-accion', 'cerrar');
    bCerrar.innerHTML = '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>';
    bloqueCuenta.appendChild(bCerrar);

    // Se arma la barra con los cuatro bloques y se inserta en el área del gráfico.
    barraEl.appendChild(bloqueColor); barraEl.appendChild(bloqueAncho);
    barraEl.appendChild(bloqueEstilo); barraEl.appendChild(bloqueCuenta);
    areaDibujoEl.appendChild(barraEl);

    // TITULO ELEMENTO SELECCIONADO

    /** Devuelve el dibujo seleccionado si se puede editar (hay selección, no está bloqueado y los dibujos están visibles); si no, devuelve null. */
    function elementoSeleccionado(){
      return (seleccionadoId !== null && !bloqueado && dibujosVisibles) ? (elementosDibujados[seleccionadoId] || null) : null;
    }

    // TITULO REFRESCAR BARRA

    /** Actualiza la barra de estilos para el dibujo indicado: la oculta si es null; si no, la muestra, enseña solo los bloques aplicables a su tipo y marca el color, grosor y estilo vigentes. Recibe el dibujo seleccionado o null. */
    function refrescarBarra(el){
      if (!el) { barraEl.classList.remove('show'); return; }
      barraEl.classList.add('show');
      var t = el.tipo;
      bloqueColor.style.display = TIPOS_COLOR[t] ? 'flex' : 'none';
      bloqueAncho.style.display = TIPOS_ANCHO[t] ? 'flex' : 'none';
      bloqueEstilo.style.display = TIPOS_TRAZO[t] ? 'flex' : 'none';
      if (TIPOS_COLOR[t]) {
        var col = valorEfectivo(el, 'color');
        bloqueColor.querySelectorAll('.barra-lateral-color').forEach(function(b){
          b.classList.toggle('on', b.getAttribute('data-color') === col);
        });
        if (/^#[0-9a-fA-F]{6}$/.test(col)) pickerEl.value = col;
      }
      if (TIPOS_ANCHO[t]) {
        var a = valorEfectivo(el, 'ancho'), mejor = ANCHOS_DIBUJO[0];
        ANCHOS_DIBUJO.forEach(function(w){ if (Math.abs(w - a) < Math.abs(mejor - a)) mejor = w; });
        bloqueAncho.querySelectorAll('.barra-lateral-ancho').forEach(function(b){
          b.classList.toggle('on', parseFloat(b.getAttribute('data-ancho')) === mejor);
        });
      }
      if (TIPOS_TRAZO[t]) {
        var est = valorEfectivo(el, 'estilo');
        bloqueEstilo.querySelectorAll('.barra-lateral-estilo').forEach(function(b){
          b.classList.toggle('on', b.getAttribute('data-estilo') === est);
        });
      }
    }

    // Clic en la barra: aplica color, grosor o estilo al dibujo seleccionado, o ejecuta Duplicar/Eliminar; luego confirma el cambio y refresca la barra.
    barraEl.addEventListener('click', function(e){
      var btn = e.target.closest ? e.target.closest('button') : null;
      var el = elementoSeleccionado();
      if (!btn || !el) return;
      if (btn.hasAttribute('data-color')) { el.color = btn.getAttribute('data-color'); }
      else if (btn.hasAttribute('data-ancho')) { el.ancho = parseFloat(btn.getAttribute('data-ancho')); }
      else if (btn.hasAttribute('data-estilo')) { el.estilo = btn.getAttribute('data-estilo'); }
      else if (btn.getAttribute('data-accion') === 'borrar') { borrarSeleccionado(); return; }
      else if (btn.getAttribute('data-accion') === 'duplicar') { copiarSeleccionado(); pegar(); return; }
      else if (btn.getAttribute('data-accion') === 'cerrar') { seleccionadoId = null; redibujarTodo(); return; }
      else return;
      confirmarCambio();
      refrescarBarra(el);
    });
    // Mientras se arrastra el selector de color se previsualiza el color en el dibujo seleccionado.
    pickerEl.addEventListener('input', function(){
      var el = elementoSeleccionado();
      if (!el) return;
      el.color = pickerEl.value;
      redibujarTodo();
    });
    // Al soltar el selector de color se confirma el cambio (entra al historial).
    pickerEl.addEventListener('change', function(){
      var el = elementoSeleccionado();
      if (!el) return;
      confirmarCambio();
      refrescarBarra(el);
    });

    // TITULO BORRAR SELECCIONADO

    /** Elimina del gráfico el dibujo seleccionado (si no está bloqueado), limpia selección y hover y confirma el cambio. */
    function borrarSeleccionado(){
      if (seleccionadoId === null || bloqueado) return;
      elementosDibujados.splice(seleccionadoId, 1);
      seleccionadoId = null; encimaId = null;
      confirmarCambio();
    }

    // TITULO COPIAR SELECCIONADO

    /** Copia el dibujo seleccionado al portapapeles interno (como JSON). */
    function copiarSeleccionado(){
      var el = elementoSeleccionado();
      if (el) portapapeles = JSON.stringify(el);
    }

    // TITULO PEGAR

    /** Pega el dibujo del portapapeles: lo desplaza 4 barras a la derecha y unos 24 px hacia abajo en precio para que no se solape con el original, lo agrega, lo selecciona y confirma el cambio. */
    function pegar(){
      if (!portapapeles || bloqueado || !serie) return;
      var el = JSON.parse(portapapeles);
      var clavesT = [], clavesP = [];
      Object.keys(el).forEach(function(k){
        if (/^time[0-9]?$/.test(k) && typeof el[k] === 'number') clavesT.push(k);
        if (/^price[0-9]?$/.test(k) && typeof el[k] === 'number') clavesP.push(k);
      });
      clavesT.forEach(function(k){
        var l = tiempoALogico(el[k]);
        if (l !== null) el[k] = logicoATiempo(l + 4);
      });
      if (clavesP.length) {
        var yReferencia = yDePrecio(el[clavesP[0]]);
        var pDesp = ok(yReferencia) ? serie.coordinateToPrice(yReferencia + 24) : null;
        if (pDesp !== null) {
          var dp = pDesp - el[clavesP[0]];
          clavesP.forEach(function(k){ el[k] = el[k] + dp; });
        }
      }
      elementosDibujados.push(el);
      seleccionadoId = elementosDibujados.length - 1;
      confirmarCambio();
    }

    // TITULO BOTON ICONO

    /** Crea un botón de icono para la barra de acciones. Recibe el contenido SVG interno, el título (tooltip) y la función a ejecutar al hacer clic; devuelve el botón. */
    function botonIcono(interior, titulo, fn){
      var b = document.createElement('button');
      b.className = 'tvbtn icon'; b.title = titulo;
      b.innerHTML = '<svg viewBox="0 0 20 20">' + interior + '</svg>';
      b.addEventListener('click', fn);
      return b;
    }
    // Contenedor de botones de acción (#tradingview-actions) donde se agregan Deshacer y Rehacer.
    var accionesEl = document.getElementById('tradingview-actions');
    // Botón Deshacer: llama a deshacer() al hacer clic.
    var botonDeshacer = botonIcono('<path d="M7 5L3.5 8.5 7 12"/><path d="M3.5 8.5H12a4 4 0 0 1 0 8H9"/>', 'Deshacer', function(){ deshacer(); });
    // Botón Rehacer: llama a rehacer() al hacer clic.
    var botonRehacer = botonIcono('<path d="M13 5l3.5 3.5L13 12"/><path d="M16.5 8.5H8a4 4 0 0 0 0 8h3"/>', 'Rehacer', function(){ rehacer(); });
    // Se colocan al inicio de la barra de acciones (Deshacer primero, luego Rehacer).
    accionesEl.insertBefore(botonRehacer, accionesEl.firstChild);
    accionesEl.insertBefore(botonDeshacer, botonRehacer);
    // Pantallas táctiles: la barra superior se desplaza hacia los lados y Deshacer/Rehacer quedaban escondidos a la derecha; se pasan a la barra de rangos,
    // junto al botón de ampliar (los tres quedan fijos a la derecha, ver css/60_barra_rangos.css), y vuelven a la barra de acciones en escritorio.
    botonDeshacer.id = 'boton-deshacer'; botonRehacer.id = 'boton-rehacer';
    function ubicarDeshacerRehacer(){
      var rangos = document.getElementById('tradingview-rangebar'), ampliar = document.getElementById('boton-expandir-movil');
      if (!rangos || !ampliar) return;
      var tactil = false; try { tactil = window.parent.innerWidth <= 1024; } catch (e) {}
      var enRangos = botonDeshacer.parentNode === rangos;
      if (tactil && !enRangos) { rangos.insertBefore(botonDeshacer, ampliar); rangos.insertBefore(botonRehacer, ampliar); }
      else if (!tactil && enRangos) { accionesEl.insertBefore(botonRehacer, accionesEl.firstChild); accionesEl.insertBefore(botonDeshacer, botonRehacer); }
    }
    setInterval(ubicarDeshacerRehacer, 400);
    ubicarDeshacerRehacer();

    // Reasignación redundante del estado de visibilidad (conserva el mismo valor inicial true).
    var dibujosVisibles = true;
    // Botón de ojo que oculta o muestra todos los dibujos; se inserta junto al botón de bloqueo.
    var botonOcultar = document.createElement('button');
    botonOcultar.className = 'tvtool';
    // Iconos SVG del botón de ocultar: ojo abierto y ojo tachado.
    var ICONO_OJO = '<svg viewBox="0 0 20 20"><path d="M2 10s3-5.5 8-5.5S18 10 18 10s-3 5.5-8 5.5S2 10 2 10z"/><circle cx="10" cy="10" r="2.4"/></svg>';
    var ICONO_OJO_OFF = '<svg viewBox="0 0 20 20"><path d="M2 10s3-5.5 8-5.5S18 10 18 10s-3 5.5-8 5.5S2 10 2 10z"/><circle cx="10" cy="10" r="2.4"/><path d="M3 3l14 14"/></svg>';
    // TITULO REFRESCAR OCULTAR

    /** Actualiza el botón de ocultar: icono, tooltip y estado resaltado según dibujosVisibles. */
    function refrescarOcultar(){
      botonOcultar.innerHTML = dibujosVisibles ? ICONO_OJO : ICONO_OJO_OFF;
      botonOcultar.title = dibujosVisibles ? 'Ocultar dibujos' : 'Mostrar dibujos';
      botonOcultar.classList.toggle('on', !dibujosVisibles);
    }
    refrescarOcultar();
    var botonCandadoReferencia = document.getElementById('herramienta-candado');
    botonCandadoReferencia.parentNode.insertBefore(botonOcultar, botonCandadoReferencia);
    // Clic en el botón de ocultar: alterna la visibilidad; al ocultar cancela el dibujo en curso y deselecciona.
    botonOcultar.addEventListener('click', function(e){
      e.stopPropagation();
      dibujosVisibles = !dibujosVisibles;
      if (!dibujosVisibles) { cancelarDibujoEnCurso(); activarHerramienta('cross'); seleccionadoId = null; encimaId = null; }
      refrescarOcultar();
      redibujarTodo();
    });

    // Se envuelven pintar, elementoBajo y activarHerramienta (definidas en fragmentos anteriores) para respetar la visibilidad de los dibujos; se guarda cada original.
    var pintarOriginal = pintar;
    /** Versión envolvente de pintar: si los dibujos están ocultos solo limpia el lienzo; si no, delega en la original. */
    pintar = function(){
      if (!dibujosVisibles) { ctx.clearRect(0, 0, cssW, cssH); return; }
      pintarOriginal();
    };
    // Guarda la función original elementoBajo.
    var elementoBajoOriginal = elementoBajo;
    /** Versión envolvente de elementoBajo: no detecta ningún dibujo cuando están ocultos; si no, delega en la original. */
    elementoBajo = function(x, y){ return dibujosVisibles ? elementoBajoOriginal(x, y) : null; };
    // Guarda la función original activarHerramienta.
    var activarHerramientaOriginal = activarHerramienta;
    /** Versión envolvente de activarHerramienta: al elegir una herramienta de dibujo estando ocultos, vuelve a mostrar los dibujos y luego delega en la original. Recibe el nombre de la herramienta. */
    activarHerramienta = function(t){
      if (t !== 'cross' && !dibujosVisibles) { dibujosVisibles = true; refrescarOcultar(); redibujarTodo(); }
      activarHerramientaOriginal(t);
    };

    // Estado de vigilancia de la interfaz: última selección, último objeto y última marca del historial ya reflejados en la UI.
    var vigilanciaSeleccion = -2, vigilanciaObj = null, vigilanciaHistorial = '';
    // TITULO VIGILAR UI

    /** Bucle por fotograma que mantiene la interfaz sincronizada: refresca la barra de estilos cuando cambia la selección y habilita o deshabilita Deshacer/Rehacer según el historial. Se reprograma con requestAnimationFrame. */
    function vigilarUI(){
      var el = elementoSeleccionado();
      if (seleccionadoId !== vigilanciaSeleccion || el !== vigilanciaObj) { vigilanciaSeleccion = seleccionadoId; vigilanciaObj = el; refrescarBarra(el); }
      var h = posicionHistorial + '/' + historial.length;
      if (h !== vigilanciaHistorial) {
        vigilanciaHistorial = h;
        botonDeshacer.disabled = posicionHistorial <= 0;
        botonRehacer.disabled = posicionHistorial >= historial.length - 1;
      }
      requestAnimationFrame(vigilarUI);
    }
    requestAnimationFrame(vigilarUI);

    // Atajos de teclado (ignora campos de texto): Ctrl/Cmd+C copia, Ctrl/Cmd+V pega y Alt+T/H/V/F/B activa tendencia, horizontal, vertical, Fibonacci o pincel.
    document.addEventListener('keydown', function(e){
      var tag = (e.target && e.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      if (e.ctrlKey || e.metaKey) {
        var kl = (e.key || '').toLowerCase();
        if (kl === 'c') copiarSeleccionado();
        else if (kl === 'v') pegar();
        return;
      }
      if (e.altKey) {
        var mapa = { KeyT: 'trend', KeyH: 'hline', KeyV: 'vline', KeyF: 'fib', KeyB: 'brush' };
        var t = mapa[e.code];
        if (t) {
          e.preventDefault();
          var item = document.querySelector('.tvtool-desplegable-elemento[data-tool="' + t + '"]');
          if (item) item.click(); else activarHerramienta(t);
        }
      }
    });


/* -------------------------------------------------------------------------------------------------------
   ----------------------------- FIN Piña y Jara 23_dibujo_barra_estilos .JS -----------------------------
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
