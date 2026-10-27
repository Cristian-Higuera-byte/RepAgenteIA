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
   ----------------------------- INICIO Piña y Jara 32_indicadores_modal .JS -----------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Indicadores: ventana de selección y ventana de ajustes
    // Elementos de la ventana de selección de indicadores (fondo, botones, buscador y pestañas)
    var modalOverlay = document.getElementById('ind-modal-overlay');
    var btnIndSelect = document.getElementById('btn-ind-select');
    var modalClose = document.getElementById('ind-modal-close');
    var searchInput = document.getElementById('ind-search-input');
    var tabsInd = document.getElementById('ind-tabs');
    // tabActiva: pestaña seleccionada de la ventana (Todos, un grupo o Activos)
    var tabActiva = 'Todos';

    /** Cuenta cuántas instancias activas hay del indicador con identificador id. */
    function cantidadDe(id){ return indActivos.filter(function(i){ return i.id === id; }).length; }

    /**
     * Dibuja las pestañas de la ventana de selección (Todos, un grupo por categoría y Activos con su contador) y
     * marca la pestaña activa.
     */
    function renderizarTabs(){
      var nombres = ['Todos'].concat(GRUPOS_IND).concat(['Activos']);
      tabsInd.innerHTML = '';
      nombres.forEach(function(n){
        var b = document.createElement('button'); b.className = 'ind-tab' + (n === tabActiva ? ' on' : '');
        b.textContent = n === 'Activos' ? 'Activos (' + indActivos.length + ')' : n;
        b.addEventListener('click', function(){ tabActiva = n; renderizarTabs(); renderizarListaIndicadores(searchInput.value); });
        tabsInd.appendChild(b);
      });
    }

    /**
     * Crea la fila del catálogo para la definición df (nombre, descripción, estado y aviso de modo comparar); al
     * pulsarla añade el indicador y refresca la lista. Devuelve el elemento.
     */
    function filaIndicador(df){
      var n = cantidadDe(df.id);
      var fila = document.createElement('div'); fila.className = 'ind-fila'; fila.title = df.desc;
      var txt = document.createElement('div'); txt.className = 'ind-txt';
      var nom = document.createElement('span'); nom.className = 'ind-nom'; nom.textContent = df.nombre;
      var sub = document.createElement('span'); sub.className = 'ind-sub';
      sub.textContent = (df.destino === 'panel' ? 'Panel propio · ' : 'Sobre el precio · ') + df.desc;
      if (modoComparar && df.destino === 'precio') { sub.textContent += '  ·  ⚠ Oculto mientras haya símbolos comparados'; sub.style.color = '#d29922'; }
      txt.appendChild(nom); txt.appendChild(sub);
      var est = document.createElement('span'); est.className = 'ind-estado' + (n ? ' on' : '');
      est.textContent = n ? (n > 1 ? n + ' activos · +' : 'Activo · +') : 'Añadir';
      fila.appendChild(txt); fila.appendChild(est);
      fila.addEventListener('click', function(){ anadirIndicador(df.id); renderizarTabs(); renderizarListaIndicadores(searchInput.value); });
      return fila;
    }

    /**
     * Crea la fila de un indicador activo inst con botones para mostrar/ocultar, abrir ajustes y quitar. Devuelve el
     * elemento.
     */
    function filaInstancia(inst){
      var df = DEFS[inst.id];
      var fila = document.createElement('div'); fila.className = 'ind-fila';
      var txt = document.createElement('div'); txt.className = 'ind-txt';
      var nom = document.createElement('span'); nom.className = 'ind-nom'; nom.textContent = tituloInstancia(inst) + (inst.oculto ? '  (oculto)' : '');
      var sub = document.createElement('span'); sub.className = 'ind-sub'; sub.textContent = df.nombre;
      if (modoComparar && df.destino === 'precio') { sub.textContent += '  ·  ⚠ Oculto mientras compares'; sub.style.color = '#d29922'; }
      txt.appendChild(nom); txt.appendChild(sub);
      var acc = document.createElement('div'); acc.className = 'ind-acciones';
      /**
       * Auxiliar de filaInstancia: crea un botón pequeño con texto t, título titulo y clase opcional cls que ejecuta
       * fn sin propagar el clic.
       */
      function mini(t, titulo, fn, cls){
        var b = document.createElement('button'); b.className = 'ind-mini' + (cls ? ' ' + cls : ''); b.textContent = t; b.title = titulo;
        b.addEventListener('click', function(ev){ ev.stopPropagation(); fn(); });
        acc.appendChild(b);
      }
      mini(inst.oculto ? 'Mostrar' : 'Ocultar', 'Mostrar u ocultar', function(){ inst.oculto = !inst.oculto; cambioIndicadores(); renderizarTabs(); renderizarListaIndicadores(searchInput.value); });
      mini(String.fromCharCode(9881), 'Ajustes', function(){ abrirAjustesInd(inst.uid); });
      mini(String.fromCharCode(10005), 'Quitar', function(){ quitarIndicador(inst.uid); renderizarTabs(); renderizarListaIndicadores(searchInput.value); }, 'rojo');
      fila.appendChild(txt); fila.appendChild(acc);
      return fila;
    }

    /**
     * Rellena la lista de la ventana según la pestaña activa y el texto de búsqueda filtro (en nombre, abreviatura,
     * descripción y grupo); muestra un mensaje si no hay resultados.
     */
    function renderizarListaIndicadores(filtro){
      var cont = document.getElementById('ind-list-container');
      cont.innerHTML = '';
      var q = (filtro || '').toLowerCase().trim(), hay = false;
      if (tabActiva === 'Activos') {
        indActivos.forEach(function(inst){
          if (q && (tituloInstancia(inst) + DEFS[inst.id].nombre).toLowerCase().indexOf(q) < 0) return;
          cont.appendChild(filaInstancia(inst)); hay = true;
        });
        if (!hay) { var v = document.createElement('div'); v.className = 'ind-vacio'; v.textContent = 'No hay indicadores activos.'; cont.appendChild(v); }
        return;
      }
      GRUPOS_IND.forEach(function(g){
        if (tabActiva !== 'Todos' && tabActiva !== g) return;
        var items = LISTA_DEFS.filter(function(df){
          return df.grupo === g && (!q || (df.nombre + ' ' + df.corto + ' ' + df.desc + ' ' + df.grupo).toLowerCase().indexOf(q) >= 0);
        });
        if (!items.length) return;
        hay = true;
        if (tabActiva === 'Todos') { var h = document.createElement('div'); h.className = 'ind-grupo'; h.textContent = g; cont.appendChild(h); }
        items.forEach(function(df){ cont.appendChild(filaIndicador(df)); });
      });
      if (!hay) { var nv = document.createElement('div'); nv.className = 'ind-vacio'; nv.textContent = 'Ningún indicador coincide con la búsqueda.'; cont.appendChild(nv); }
    }

    /** Muestra la ventana de selección de indicadores, dibuja pestañas y lista y da foco al buscador. */
    function abrirModalIndicadores(){
      modalOverlay.style.display = 'flex';
      renderizarTabs();
      renderizarListaIndicadores(searchInput.value);
      setTimeout(function(){ searchInput.focus(); }, 50);
    }
    // Eventos de la ventana de selección: abrir, cerrar con la X o con clic fuera, y filtrar al escribir
    btnIndSelect.addEventListener('click', function(e){ e.stopPropagation(); abrirModalIndicadores(); });
    modalClose.addEventListener('click', function(){ modalOverlay.style.display = 'none'; });
    modalOverlay.addEventListener('click', function(e){ if (e.target === modalOverlay) modalOverlay.style.display = 'none'; });
    searchInput.addEventListener('input', function(e){ renderizarListaIndicadores(e.target.value); });

    // ---------- Ajustes de un indicador (Entradas de datos / Estilo / Visibilidad) ----------
    // Elementos de la ventana de ajustes de un indicador
    var cfgOverlay = document.getElementById('indcfg-overlay');
    var cfgCuerpo = document.getElementById('indcfg-cuerpo');
    var cfgTabs = document.getElementById('indcfg-tabs');
    // cfgUid: instancia en edición; cfgSnap: copia para Cancelar; cfgTab: pestaña visible
    var cfgUid = null, cfgSnap = null, cfgTab = 'entradas';

    /** Oculta la ventana de ajustes de un indicador y olvida la instancia y la copia de seguridad. */
    function cerrarAjustes(){ cfgOverlay.style.display = 'none'; cfgUid = null; cfgSnap = null; }
    /** Cierra la ventana de ajustes solo si está mostrando la instancia uid (se usa al quitar un indicador). */
    function cerrarAjustesSiEs(uid){ if (cfgUid === uid) cerrarAjustes(); }
    /** Devuelve la instancia cuyos ajustes están abiertos (cfgUid) o undefined si no hay ninguna. */
    function instAjustes(){ return indActivos.filter(function(i){ return i.uid === cfgUid; })[0]; }
    /**
     * Descarta los cambios hechos desde que se abrió la ventana restaurando la copia (cfgSnap), redibuja y cierra.
     */
    function cancelarAjustes(){   // descarta lo cambiado desde que se abrió la ventana
      var inst = instAjustes();
      if (inst && cfgSnap) { restaurarInstancia(inst, cfgSnap); reconstruirIndicador(inst); }
      cerrarAjustes();
    }
    /**
     * Aplica un cambio hecho en la ventana de ajustes: reconstruye el indicador y actualiza el título de la ventana.
     */
    function aplicarCambio(inst){
      reconstruirIndicador(inst);
      document.getElementById('indcfg-titulo').textContent = tituloInstancia(inst) + '  ·  ' + DEFS[inst.id].nombre;
    }

    /**
     * Crea un elemento HTML de etiqueta tag con clase opcional cls y texto opcional txt. Es el ayudante de creación
     * de DOM que reutiliza también el backtest.
     */
    function el(tag, cls, txt){ var e = document.createElement(tag); if (cls) e.className = cls; if (txt !== undefined) e.textContent = txt; return e; }
    /** Añade al cuerpo de la ventana de ajustes una fila con la etiqueta y el control indicados. */
    function fila(etiqueta, control){
      var f = el('div', 'cfg-fila'); f.appendChild(el('span', '', etiqueta)); f.appendChild(control); cfgCuerpo.appendChild(f);
    }
    /** Añade al cuerpo de la ventana de ajustes un título de sección con el texto t. */
    function seccion(t){ cfgCuerpo.appendChild(el('div', 'cfg-sec', t)); }
    /**
     * Crea un desplegable con las opciones [valor, texto], seleccionando la actual; al cambiar llama a alCambiar con
     * el valor elegido. Devuelve el select.
     */
    function selector(opciones, actual, alCambiar){
      var s = document.createElement('select');
      opciones.forEach(function(o){ var op = el('option', '', o[1]); op.value = o[0]; if (String(o[0]) === String(actual)) op.selected = true; s.appendChild(op); });
      s.addEventListener('change', function(){ alCambiar(s.value); });
      return s;
    }
    /**
     * Crea una casilla de verificación con texto y estado inicial marcada; al cambiar llama a alCambiar con el
     * booleano. Devuelve la etiqueta.
     */
    function casilla(texto, marcada, alCambiar){
      var l = el('label', 'cfg-check'); var c = document.createElement('input'); c.type = 'checkbox'; c.checked = marcada;
      c.addEventListener('change', function(){ alCambiar(c.checked); });
      l.appendChild(c); l.appendChild(el('span', '', texto)); return l;
    }
    /**
     * Garantiza que inst[campo] sea un array de n posiciones (relleno con null) para poder guardar valores por capa.
     */
    function asegurarLista(inst, campo, n){
      if (!inst[campo]) inst[campo] = new Array(n).fill(null);
    }

    /**
     * Pinta la pestaña Entradas de datos: un selector o campo numérico por cada parámetro del indicador, que valida y
     * aplica el cambio.
     */
    function pestanaEntradas(inst, df){
      if (!df.params.length) { cfgCuerpo.appendChild(el('div', 'cfg-vacio', 'Este indicador no tiene parámetros.')); return; }
      df.params.forEach(function(pd){
        var ctl;
        if (pd.t === 'sel') {
          ctl = selector(pd.o, inst.p[pd.k], function(v){ inst.p[pd.k] = valorParam(pd, v); aplicarCambio(inst); });
        } else {
          ctl = document.createElement('input'); ctl.type = 'number'; ctl.min = pd.min; ctl.max = pd.max; ctl.step = pd.paso; ctl.value = inst.p[pd.k];
          ctl.addEventListener('change', function(){ inst.p[pd.k] = valorParam(pd, ctl.value); ctl.value = inst.p[pd.k]; aplicarCambio(inst); });
        }
        fila(pd.n, ctl);
      });
    }

    // ESTILOS_LINEA: opciones de tipo de trazo [valor de LightweightCharts, texto]
    var ESTILOS_LINEA = [[0, 'Sólida'], [2, 'Discontinua'], [1, 'Punteada']];
    /**
     * Pinta la pestaña Estilo: por cada capa su visibilidad, color, tipo de trazo y grosor, más las opciones de
     * precisión, etiquetas en la escala y valores en la línea de estado.
     */
    function pestanaEstilo(inst, df){
      df.capas.forEach(function(cp, i){
        var tipo = cp[2] || 'linea';
        var f = el('div', 'cfg-fila cfg-estilo');
        f.appendChild(casilla(cp[0], capaVisible(inst, i), function(v){ asegurarLista(inst, 'v', df.capas.length); inst.v[i] = v ? null : 0; if (inst.v.every(function(x){ return x === null; })) inst.v = null; aplicarCambio(inst); }));
        var ctl = el('div', 'cfg-controles');
        var autoColor = (tipo === 'hist') && ['macd', 'osma', 'bulls', 'bears', 'ao', 'ac', 'gator', 'bwmfi', 'volumenes'].indexOf(df.id) >= 0;
        if (!autoColor) {
          var c = document.createElement('input'); c.type = 'color'; c.value = colorCapa(inst, i);
          c.addEventListener('input', function(){ asegurarLista(inst, 'c', df.capas.length); inst.c[i] = c.value; aplicarCambio(inst); });
          ctl.appendChild(c);
        }
        if (tipo === 'linea') {
          ctl.appendChild(selector(ESTILOS_LINEA, estiloLineaCapa(inst, i), function(v){ asegurarLista(inst, 's', df.capas.length); inst.s[i] = Number(v); aplicarCambio(inst); }));
          ctl.appendChild(selector([1, 2, 3, 4, 5].map(function(n){ return [n, n + ' px']; }), anchoCapa(inst, i), function(v){ asegurarLista(inst, 'w', df.capas.length); inst.w[i] = Number(v); aplicarCambio(inst); }));
        }
        f.appendChild(ctl); cfgCuerpo.appendChild(f);
      });
      seccion('Salidas');
      var precisiones = [['', 'Por defecto']].concat([0, 1, 2, 3, 4, 5, 6, 7, 8].map(function(n){ return [n, String(n) + (n === 1 ? ' decimal' : ' decimales')]; }));
      fila('Precisión', selector(precisiones, inst.pr === null ? '' : inst.pr, function(v){ inst.pr = (v === '') ? null : Number(v); aplicarCambio(inst); }));
      cfgCuerpo.appendChild(casilla('Etiquetas en la escala de precios', inst.et, function(v){ inst.et = v; aplicarCambio(inst); }));
      cfgCuerpo.appendChild(casilla('Valores en la línea de estado', inst.sl, function(v){ inst.sl = v; aplicarCambio(inst); }));
    }

    /**
     * Pinta la pestaña Visibilidad: para cada grupo de temporalidad una casilla y un rango mínimo-máximo (campos
     * numéricos y deslizadores) que limitan dónde se muestra el indicador.
     */
    function pestanaVisibilidad(inst){
      GRUPOS_TF.forEach(function(g){
        var r = inst.vis[g[0]], f = el('div', 'cfg-vis');
        f.appendChild(casilla(g[1], r[0], function(v){ r[0] = v; aplicarCambio(inst); }));
        var mn = document.createElement('input'), mx = document.createElement('input');
        mn.type = mx.type = 'number'; mn.min = mx.min = g[2]; mn.max = mx.max = g[3]; mn.value = r[1]; mx.value = r[2];
        var dual = el('div', 'cfg-dual'), rmn = document.createElement('input'), rmx = document.createElement('input');
        rmn.type = rmx.type = 'range'; rmn.min = rmx.min = g[2]; rmn.max = rmx.max = g[3]; rmn.value = r[1]; rmx.value = r[2];
        dual.appendChild(rmn); dual.appendChild(rmx);
        /**
         * Auxiliar de pestanaVisibilidad: colorea la pista del doble deslizador resaltando el tramo entre el mínimo y
         * el máximo.
         */
        function pintaPista(){
          var span = g[3] - g[2] || 1, a = (r[1] - g[2]) / span * 100, b = (r[2] - g[2]) / span * 100;
          dual.style.background = 'linear-gradient(to right,#3a3f47 ' + a + '%,#d1d4dc ' + a + '%,#d1d4dc ' + b + '%,#3a3f47 ' + b + '%)';
        }
        /**
         * Auxiliar de pestanaVisibilidad: valida, ordena y fija el rango [a, b] (quien indica qué extremo movió el
         * usuario), sincroniza campos y deslizadores y aplica el cambio.
         */
        function fija(a, b, quien){
          a = Math.round(Number(a)); b = Math.round(Number(b));
          if (!isFinite(a)) a = r[1]; if (!isFinite(b)) b = r[2];
          a = Math.min(g[3], Math.max(g[2], a)); b = Math.min(g[3], Math.max(g[2], b));
          if (a > b) { if (quien === 'min') a = b; else b = a; }
          r[1] = a; r[2] = b; mn.value = rmn.value = a; mx.value = rmx.value = b; pintaPista(); aplicarCambio(inst);
        }
        mn.addEventListener('change', function(){ fija(mn.value, r[2], 'min'); });
        mx.addEventListener('change', function(){ fija(r[1], mx.value, 'max'); });
        rmn.addEventListener('input', function(){ fija(rmn.value, r[2], 'min'); });
        rmx.addEventListener('input', function(){ fija(r[1], rmx.value, 'max'); });
        pintaPista();
        f.appendChild(mn); f.appendChild(dual); f.appendChild(mx);
        cfgCuerpo.appendChild(f);
      });
      cfgCuerpo.appendChild(el('div', 'cfg-nota', 'El indicador solo se muestra en las temporalidades marcadas y dentro del rango indicado (p. ej. Minutos 1–15: M1, M5 y M15).'));
    }

    /**
     * Dibuja la ventana de ajustes de la instancia abierta: título, pestañas (Entradas, Estilo, Visibilidad) y el
     * contenido de la pestaña activa.
     */
    function pintarAjustes(){
      var inst = instAjustes();
      if (!inst) return;
      var df = DEFS[inst.id];
      document.getElementById('indcfg-titulo').textContent = tituloInstancia(inst) + '  ·  ' + df.nombre;
      cfgTabs.innerHTML = '';
      [['entradas', 'Entradas de datos'], ['estilo', 'Estilo'], ['visibilidad', 'Visibilidad']].forEach(function(tb){
        var b = el('button', 'cfg-tab' + (cfgTab === tb[0] ? ' on' : ''), tb[1]);
        b.addEventListener('click', function(){ cfgTab = tb[0]; pintarAjustes(); });
        cfgTabs.appendChild(b);
      });
      cfgCuerpo.innerHTML = '';
      if (cfgTab === 'entradas') pestanaEntradas(inst, df);
      else if (cfgTab === 'estilo') pestanaEstilo(inst, df);
      else pestanaVisibilidad(inst);
    }

    /**
     * Abre la ventana de ajustes del indicador uid guardando una copia para poder cancelar y mostrando la pestaña de
     * entradas.
     */
    function abrirAjustesInd(uid){
      var inst = indActivos.filter(function(i){ return i.uid === uid; })[0];
      if (!inst) return;
      cfgUid = uid;
      cfgSnap = JSON.parse(JSON.stringify(serializarInstancia(inst)));
      cfgTab = 'entradas';
      pintarAjustes();
      cfgOverlay.style.display = 'flex';
    }

    // Botones de la ventana de ajustes: cerrar y cancelar descartan, Aceptar guarda y Restablecer vuelve a los valores por defecto
    document.getElementById('indcfg-close').addEventListener('click', cancelarAjustes);
    document.getElementById('indcfg-cancel').addEventListener('click', cancelarAjustes);
    document.getElementById('indcfg-ok').addEventListener('click', function(){ cambioIndicadores(); cerrarAjustes(); });
    document.getElementById('indcfg-reset').addEventListener('click', function(){
      var inst = instAjustes();
      if (!inst) return;
      restaurarInstancia(inst, { id: inst.id });
      reconstruirIndicador(inst);
      pintarAjustes();
    });
    cfgOverlay.addEventListener('click', function(e){ if (e.target === cfgOverlay) cancelarAjustes(); });
    // Escape cierra primero la ventana de ajustes y, si no está abierta, la de selección
    document.addEventListener('keydown', function(e){
      if (e.key !== 'Escape') return;
      if (cfgOverlay.style.display !== 'none') cancelarAjustes();
      else if (modalOverlay.style.display !== 'none') modalOverlay.style.display = 'none';
    });

/* -------------------------------------------------------------------------------------------------------
   ------------------------------- FIN Piña y Jara 32_indicadores_modal .JS ------------------------------
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
