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
    var modalSuperposicion = document.getElementById('indicador-modal-superposicion');
    var botonIndicadorSeleccionar = document.getElementById('boton-indicador-seleccionar');
    var modalCerrar = document.getElementById('indicador-modal-cerrar');
    var buscarInput = document.getElementById('indicador-buscar-entrada');
    var pestanasIndicador = document.getElementById('indicador-pestanas');
    // tabActiva: pestaña seleccionada de la ventana (Todos, un grupo o Activos)
    var pestanaActiva = 'Todos';

    // TITULO CANTIDAD DE

    /** Cuenta cuántas instancias activas hay del indicador con identificador id. */
    function cantidadDe(id){ return indicadorActivos.filter(function(i){ return i.id === id; }).length; }

    // TITULO RENDERIZAR TABS

    /**
     * Dibuja las pestañas de la ventana de selección (Todos, un grupo por categoría y Activos con su contador) y
     * marca la pestaña activa.
     */
    function renderizarPestanas(){
      var nombres = ['Todos'].concat(GRUPOS_INDICADOR).concat(['Activos']);
      pestanasIndicador.innerHTML = '';
      nombres.forEach(function(n){
        var b = document.createElement('button'); b.className = 'indicador-pestana' + (n === pestanaActiva ? ' on' : '');
        b.textContent = n === 'Activos' ? 'Activos (' + indicadorActivos.length + ')' : n;
        b.addEventListener('click', function(){ pestanaActiva = n; renderizarPestanas(); renderizarListaIndicadores(buscarInput.value); });
        pestanasIndicador.appendChild(b);
      });
    }

    // TITULO FILA INDICADOR

    /**
     * Crea la fila del catálogo para la definición df (nombre, descripción, estado y aviso de modo comparar); al
     * pulsarla añade el indicador y refresca la lista. Devuelve el elemento.
     */
    function filaIndicador(tablaDatos){
      var n = cantidadDe(tablaDatos.id);
      var fila = document.createElement('div'); fila.className = 'indicador-fila'; fila.title = tablaDatos.desc;
      var txt = document.createElement('div'); txt.className = 'indicador-texto';
      var nom = document.createElement('span'); nom.className = 'indicador-nombre'; nom.textContent = tablaDatos.nombre;
      var subtitulo = document.createElement('span'); subtitulo.className = 'indicador-subtitulo';
      subtitulo.textContent = (tablaDatos.destino === 'panel' ? 'Panel propio · ' : 'Sobre el precio · ') + tablaDatos.desc;
      if (modoComparar && tablaDatos.destino === 'precio') { subtitulo.textContent += '  ·  ⚠ Oculto mientras haya símbolos comparados'; subtitulo.style.color = '#d29922'; }
      txt.appendChild(nom); txt.appendChild(subtitulo);
      var est = document.createElement('span'); est.className = 'indicador-estado' + (n ? ' on' : '');
      est.textContent = n ? (n > 1 ? n + ' activos · +' : 'Activo · +') : 'Añadir';
      fila.appendChild(txt); fila.appendChild(est);
      fila.addEventListener('click', function(){ anadirIndicador(tablaDatos.id); renderizarPestanas(); renderizarListaIndicadores(buscarInput.value); });
      return fila;
    }

    // TITULO FILA INSTANCIA

    /**
     * Crea la fila de un indicador activo inst con botones para mostrar/ocultar, abrir ajustes y quitar. Devuelve el
     * elemento.
     */
    function filaInstancia(inst){
      var tablaDatos = DEFS[inst.id];
      var fila = document.createElement('div'); fila.className = 'indicador-fila';
      var txt = document.createElement('div'); txt.className = 'indicador-texto';
      var nom = document.createElement('span'); nom.className = 'indicador-nombre'; nom.textContent = tituloInstancia(inst) + (inst.oculto ? '  (oculto)' : '');
      var subtitulo = document.createElement('span'); subtitulo.className = 'indicador-subtitulo'; subtitulo.textContent = tablaDatos.nombre;
      if (modoComparar && tablaDatos.destino === 'precio') { subtitulo.textContent += '  ·  ⚠ Oculto mientras compares'; subtitulo.style.color = '#d29922'; }
      txt.appendChild(nom); txt.appendChild(subtitulo);
      var acc = document.createElement('div'); acc.className = 'indicador-acciones';
      /**
       * Auxiliar de filaInstancia: crea un botón pequeño con texto t, título titulo y clase opcional cls que ejecuta
       * fn sin propagar el clic.
       */
      function mini(t, titulo, fn, cls){
        var b = document.createElement('button'); b.className = 'indicador-mini' + (cls ? ' ' + cls : ''); b.textContent = t; b.title = titulo;
        b.addEventListener('click', function(ev){ ev.stopPropagation(); fn(); });
        acc.appendChild(b);
      }
      mini(inst.oculto ? 'Mostrar' : 'Ocultar', 'Mostrar u ocultar', function(){ inst.oculto = !inst.oculto; cambioIndicadores(); renderizarPestanas(); renderizarListaIndicadores(buscarInput.value); });
      mini(String.fromCharCode(9881), 'Ajustes', function(){ abrirAjustesIndicador(inst.uid); });
      mini(String.fromCharCode(10005), 'Quitar', function(){ quitarIndicador(inst.uid); renderizarPestanas(); renderizarListaIndicadores(buscarInput.value); }, 'rojo');
      fila.appendChild(txt); fila.appendChild(acc);
      return fila;
    }

    // TITULO RENDERIZAR LISTA INDICADORES

    /**
     * Rellena la lista de la ventana según la pestaña activa y el texto de búsqueda filtro (en nombre, abreviatura,
     * descripción y grupo); muestra un mensaje si no hay resultados.
     */
    function renderizarListaIndicadores(filtro){
      var cont = document.getElementById('indicador-lista-contenedor');
      cont.innerHTML = '';
      var q = (filtro || '').toLowerCase().trim(), hay = false;
      if (pestanaActiva === 'Activos') {
        indicadorActivos.forEach(function(inst){
          if (q && (tituloInstancia(inst) + DEFS[inst.id].nombre).toLowerCase().indexOf(q) < 0) return;
          cont.appendChild(filaInstancia(inst)); hay = true;
        });
        if (!hay) { var v = document.createElement('div'); v.className = 'indicador-vacio'; v.textContent = 'No hay indicadores activos.'; cont.appendChild(v); }
        return;
      }
      GRUPOS_INDICADOR.forEach(function(g){
        if (pestanaActiva !== 'Todos' && pestanaActiva !== g) return;
        var items = LISTA_DEFS.filter(function(tablaDatos){
          return tablaDatos.grupo === g && (!q || (tablaDatos.nombre + ' ' + tablaDatos.corto + ' ' + tablaDatos.desc + ' ' + tablaDatos.grupo).toLowerCase().indexOf(q) >= 0);
        });
        if (!items.length) return;
        hay = true;
        if (pestanaActiva === 'Todos') { var h = document.createElement('div'); h.className = 'indicador-grupo'; h.textContent = g; cont.appendChild(h); }
        items.forEach(function(tablaDatos){ cont.appendChild(filaIndicador(tablaDatos)); });
      });
      if (!hay) { var nv = document.createElement('div'); nv.className = 'indicador-vacio'; nv.textContent = 'Ningún indicador coincide con la búsqueda.'; cont.appendChild(nv); }
    }

    // TITULO ABRIR MODAL INDICADORES

    /** Muestra la ventana de selección de indicadores, dibuja pestañas y lista y da foco al buscador. */
    function abrirModalIndicadores(){
      modalSuperposicion.style.display = 'flex';
      renderizarPestanas();
      renderizarListaIndicadores(buscarInput.value);
      setTimeout(function(){ buscarInput.focus(); }, 50);
    }
    // Eventos de la ventana de selección: abrir, cerrar con la X o con clic fuera, y filtrar al escribir
    botonIndicadorSeleccionar.addEventListener('click', function(e){ e.stopPropagation(); abrirModalIndicadores(); });
    modalCerrar.addEventListener('click', function(){ modalSuperposicion.style.display = 'none'; });
    modalSuperposicion.addEventListener('click', function(e){ if (e.target === modalSuperposicion) modalSuperposicion.style.display = 'none'; });
    buscarInput.addEventListener('input', function(e){ renderizarListaIndicadores(e.target.value); });

    // ---------- Ajustes de un indicador (Entradas de datos / Estilo / Visibilidad) ----------
    // Elementos de la ventana de ajustes de un indicador
    var configuracionSuperposicion = document.getElementById('indicadores-configuracion-superposicion');
    var configuracionCuerpo = document.getElementById('indicadores-configuracion-cuerpo');
    var configuracionPestanas = document.getElementById('indicadores-configuracion-pestanas');
    // cfgUid: instancia en edición; cfgSnap: copia para Cancelar; cfgTab: pestaña visible
    var configuracionUid = null, configuracionSnap = null, configuracionPestana = 'entradas';

    // TITULO CERRAR AJUSTES

    /** Oculta la ventana de ajustes de un indicador y olvida la instancia y la copia de seguridad. */
    function cerrarAjustes(){ configuracionSuperposicion.style.display = 'none'; configuracionUid = null; configuracionSnap = null; }
    // TITULO CERRAR AJUSTES SI ES

    /** Cierra la ventana de ajustes solo si está mostrando la instancia uid (se usa al quitar un indicador). */
    function cerrarAjustesSiEs(uid){ if (configuracionUid === uid) cerrarAjustes(); }
    // TITULO INST AJUSTES

    /** Devuelve la instancia cuyos ajustes están abiertos (cfgUid) o undefined si no hay ninguna. */
    function instAjustes(){ return indicadorActivos.filter(function(i){ return i.uid === configuracionUid; })[0]; }
    // TITULO CANCELAR AJUSTES

    /**
     * Descarta los cambios hechos desde que se abrió la ventana restaurando la copia (cfgSnap), redibuja y cierra.
     */
    function cancelarAjustes(){   // descarta lo cambiado desde que se abrió la ventana
      var inst = instAjustes();
      if (inst && configuracionSnap) { restaurarInstancia(inst, configuracionSnap); reconstruirIndicador(inst); }
      cerrarAjustes();
    }
    // TITULO APLICAR CAMBIO

    /**
     * Aplica un cambio hecho en la ventana de ajustes: reconstruye el indicador y actualiza el título de la ventana.
     */
    function aplicarCambio(inst){
      reconstruirIndicador(inst);
      document.getElementById('indicadores-configuracion-titulo').textContent = tituloInstancia(inst) + '  ·  ' + DEFS[inst.id].nombre;
    }

    // TITULO EL

    /**
     * Crea un elemento HTML de etiqueta tag con clase opcional cls y texto opcional txt. Es el ayudante de creación
     * de DOM que reutiliza también el backtest.
     */
    function el(tag, cls, txt){ var e = document.createElement(tag); if (cls) e.className = cls; if (txt !== undefined) e.textContent = txt; return e; }
    // TITULO FILA

    /** Añade al cuerpo de la ventana de ajustes una fila con la etiqueta y el control indicados. */
    function fila(etiqueta, control){
      var f = el('div', 'configuracion-fila'); f.appendChild(el('span', '', etiqueta)); f.appendChild(control); configuracionCuerpo.appendChild(f);
    }
    // TITULO SECCION

    /** Añade al cuerpo de la ventana de ajustes un título de sección con el texto t. */
    function seccion(t){ configuracionCuerpo.appendChild(el('div', 'configuracion-seccion', t)); }
    // TITULO SELECTOR

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
    // TITULO CASILLA

    /**
     * Crea una casilla de verificación con texto y estado inicial marcada; al cambiar llama a alCambiar con el
     * booleano. Devuelve la etiqueta.
     */
    function casilla(texto, marcada, alCambiar){
      var l = el('label', 'configuracion-revisar'); var c = document.createElement('input'); c.type = 'checkbox'; c.checked = marcada;
      c.addEventListener('change', function(){ alCambiar(c.checked); });
      l.appendChild(c); l.appendChild(el('span', '', texto)); return l;
    }
    // TITULO ASEGURAR LISTA

    /**
     * Garantiza que inst[campo] sea un array de n posiciones (relleno con null) para poder guardar valores por capa.
     */
    function asegurarLista(inst, campo, n){
      if (!inst[campo]) inst[campo] = new Array(n).fill(null);
    }

    // TITULO PESTANA ENTRADAS

    /**
     * Pinta la pestaña Entradas de datos: un selector o campo numérico por cada parámetro del indicador, que valida y
     * aplica el cambio.
     */
    function pestanaEntradas(inst, tablaDatos){
      if (!tablaDatos.params.length) { configuracionCuerpo.appendChild(el('div', 'configuracion-vacio', 'Este indicador no tiene parámetros.')); return; }
      tablaDatos.params.forEach(function(pd){
        var ctl;
        if (pd.t === 'sel') {
          ctl = selector(pd.o, inst.p[pd.k], function(v){ inst.p[pd.k] = valorParametro(pd, v); aplicarCambio(inst); });
        } else {
          ctl = document.createElement('input'); ctl.type = 'number'; ctl.min = pd.min; ctl.max = pd.max; ctl.step = pd.paso; ctl.value = inst.p[pd.k];
          ctl.addEventListener('change', function(){ inst.p[pd.k] = valorParametro(pd, ctl.value); ctl.value = inst.p[pd.k]; aplicarCambio(inst); });
        }
        fila(pd.n, ctl);
      });
    }

    // ESTILOS_LINEA: opciones de tipo de trazo [valor de LightweightCharts, texto]
    var ESTILOS_LINEA = [[0, 'Sólida'], [2, 'Discontinua'], [1, 'Punteada']];
    // TITULO PESTANA ESTILO

    /**
     * Pinta la pestaña Estilo: por cada capa su visibilidad, color, tipo de trazo y grosor, más las opciones de
     * precisión, etiquetas en la escala y valores en la línea de estado.
     */
    function pestanaEstilo(inst, tablaDatos){
      tablaDatos.capas.forEach(function(cp, i){
        var tipo = cp[2] || 'linea';
        var f = el('div', 'configuracion-fila configuracion-estilo');
        f.appendChild(casilla(cp[0], capaVisible(inst, i), function(v){ asegurarLista(inst, 'v', tablaDatos.capas.length); inst.v[i] = v ? null : 0; if (inst.v.every(function(x){ return x === null; })) inst.v = null; aplicarCambio(inst); }));
        var ctl = el('div', 'configuracion-controles');
        var autoColor = (tipo === 'hist') && ['macd', 'osma', 'bulls', 'bears', 'ao', 'ac', 'gator', 'bwmfi', 'volumenes'].indexOf(tablaDatos.id) >= 0;
        if (!autoColor) {
          var c = document.createElement('input'); c.type = 'color'; c.value = colorCapa(inst, i);
          c.addEventListener('input', function(){ asegurarLista(inst, 'c', tablaDatos.capas.length); inst.c[i] = c.value; aplicarCambio(inst); });
          ctl.appendChild(c);
        }
        if (tipo === 'linea') {
          ctl.appendChild(selector(ESTILOS_LINEA, estiloLineaCapa(inst, i), function(v){ asegurarLista(inst, 's', tablaDatos.capas.length); inst.s[i] = Number(v); aplicarCambio(inst); }));
          ctl.appendChild(selector([1, 2, 3, 4, 5].map(function(n){ return [n, n + ' px']; }), anchoCapa(inst, i), function(v){ asegurarLista(inst, 'w', tablaDatos.capas.length); inst.w[i] = Number(v); aplicarCambio(inst); }));
        }
        f.appendChild(ctl); configuracionCuerpo.appendChild(f);
      });
      seccion('Salidas');
      var precisiones = [['', 'Por defecto']].concat([0, 1, 2, 3, 4, 5, 6, 7, 8].map(function(n){ return [n, String(n) + (n === 1 ? ' decimal' : ' decimales')]; }));
      fila('Precisión', selector(precisiones, inst.pr === null ? '' : inst.pr, function(v){ inst.pr = (v === '') ? null : Number(v); aplicarCambio(inst); }));
      configuracionCuerpo.appendChild(casilla('Etiquetas en la escala de precios', inst.et, function(v){ inst.et = v; aplicarCambio(inst); }));
      configuracionCuerpo.appendChild(casilla('Valores en la línea de estado', inst.sl, function(v){ inst.sl = v; aplicarCambio(inst); }));
    }

    // TITULO PESTANA VISIBILIDAD

    /**
     * Pinta la pestaña Visibilidad: para cada grupo de temporalidad una casilla y un rango mínimo-máximo (campos
     * numéricos y deslizadores) que limitan dónde se muestra el indicador.
     */
    function pestanaVisibilidad(inst){
      GRUPOS_TEMPORALIDAD.forEach(function(g){
        var r = inst.vis[g[0]], f = el('div', 'configuracion-visible');
        f.appendChild(casilla(g[1], r[0], function(v){ r[0] = v; aplicarCambio(inst); }));
        var mn = document.createElement('input'), mx = document.createElement('input');
        mn.type = mx.type = 'number'; mn.min = mx.min = g[2]; mn.max = mx.max = g[3]; mn.value = r[1]; mx.value = r[2];
        var doble = el('div', 'configuracion-doble'), rmn = document.createElement('input'), rmx = document.createElement('input');
        rmn.type = rmx.type = 'range'; rmn.min = rmx.min = g[2]; rmn.max = rmx.max = g[3]; rmn.value = r[1]; rmx.value = r[2];
        doble.appendChild(rmn); doble.appendChild(rmx);
        /**
         * Auxiliar de pestanaVisibilidad: colorea la pista del doble deslizador resaltando el tramo entre el mínimo y
         * el máximo.
         */
        function pintaPista(){
          var span = g[3] - g[2] || 1, a = (r[1] - g[2]) / span * 100, b = (r[2] - g[2]) / span * 100;
          doble.style.background = 'linear-gradient(to right,#3a3f47 ' + a + '%,#d1d4dc ' + a + '%,#d1d4dc ' + b + '%,#3a3f47 ' + b + '%)';
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
        f.appendChild(mn); f.appendChild(doble); f.appendChild(mx);
        configuracionCuerpo.appendChild(f);
      });
      configuracionCuerpo.appendChild(el('div', 'configuracion-nota', 'El indicador solo se muestra en las temporalidades marcadas y dentro del rango indicado (p. ej. Minutos 1–15: M1, M5 y M15).'));
    }

    // TITULO PINTAR AJUSTES

    /**
     * Dibuja la ventana de ajustes de la instancia abierta: título, pestañas (Entradas, Estilo, Visibilidad) y el
     * contenido de la pestaña activa.
     */
    function pintarAjustes(){
      var inst = instAjustes();
      if (!inst) return;
      var tablaDatos = DEFS[inst.id];
      document.getElementById('indicadores-configuracion-titulo').textContent = tituloInstancia(inst) + '  ·  ' + tablaDatos.nombre;
      configuracionPestanas.innerHTML = '';
      [['entradas', 'Entradas de datos'], ['estilo', 'Estilo'], ['visibilidad', 'Visibilidad']].forEach(function(tb){
        var b = el('button', 'configuracion-pestana' + (configuracionPestana === tb[0] ? ' on' : ''), tb[1]);
        b.addEventListener('click', function(){ configuracionPestana = tb[0]; pintarAjustes(); });
        configuracionPestanas.appendChild(b);
      });
      configuracionCuerpo.innerHTML = '';
      if (configuracionPestana === 'entradas') pestanaEntradas(inst, tablaDatos);
      else if (configuracionPestana === 'estilo') pestanaEstilo(inst, tablaDatos);
      else pestanaVisibilidad(inst);
    }

    // TITULO ABRIR AJUSTES IND

    /**
     * Abre la ventana de ajustes del indicador uid guardando una copia para poder cancelar y mostrando la pestaña de
     * entradas.
     */
    function abrirAjustesIndicador(uid){
      var inst = indicadorActivos.filter(function(i){ return i.uid === uid; })[0];
      if (!inst) return;
      configuracionUid = uid;
      configuracionSnap = JSON.parse(JSON.stringify(serializarInstancia(inst)));
      configuracionPestana = 'entradas';
      pintarAjustes();
      configuracionSuperposicion.style.display = 'flex';
    }

    // Botones de la ventana de ajustes: cerrar y cancelar descartan, Aceptar guarda y Restablecer vuelve a los valores por defecto
    document.getElementById('indicadores-configuracion-cerrar').addEventListener('click', cancelarAjustes);
    document.getElementById('indicadores-configuracion-cancelar').addEventListener('click', cancelarAjustes);
    document.getElementById('indicadores-configuracion-aceptar').addEventListener('click', function(){ cambioIndicadores(); cerrarAjustes(); });
    document.getElementById('indicadores-configuracion-reiniciar').addEventListener('click', function(){
      var inst = instAjustes();
      if (!inst) return;
      restaurarInstancia(inst, { id: inst.id });
      reconstruirIndicador(inst);
      pintarAjustes();
    });
    configuracionSuperposicion.addEventListener('click', function(e){ if (e.target === configuracionSuperposicion) cancelarAjustes(); });
    // Escape cierra primero la ventana de ajustes y, si no está abierta, la de selección
    document.addEventListener('keydown', function(e){
      if (e.key !== 'Escape') return;
      if (configuracionSuperposicion.style.display !== 'none') cancelarAjustes();
      else if (modalSuperposicion.style.display !== 'none') modalSuperposicion.style.display = 'none';
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
