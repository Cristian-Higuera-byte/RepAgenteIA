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
   ----------------------------- INICIO Piña y Jara 55_pantalla_completa .JS -----------------------------
   ------------------------------------------------------------------------------------------------------- */

// [grafico] Pantalla completa: botón, modo "pj-fs" y selector de activo (cambiar de símbolo sin salir)
    // Se pone en pantalla completa el IFRAME entero (window.frameElement), no solo el gráfico: así sigue en pantalla
    // completa aunque Streamlit recargue el contenido (p. ej. al cambiar de activo). Si no se puede, se usa el
    // contenedor del gráfico como antes. En pantalla completa se ven los botones VENDER/COMPRAR (posiciones/)
    // y el nombre del activo abre la lista de activos de la watchlist.
    // ACTIVOS: lista de activos de la watchlist inyectada por Python (símbolo b, nombre n, icono i y marca a de activo actual)
    var ACTIVOS = __ACTIVOS_JSON__;
    // wrapFs / btnFullEl: contenedor del gráfico y botón de pantalla completa; docPadre: documento de Streamlit si es accesible
    var contenedorFs = document.getElementById('tradingview-contenedor');
    var botonCompletoEl = document.getElementById('boton-completo');
    var docPadre = null;
    try { docPadre = window.parent.document; } catch (e) {}

    // TITULO PANTALLA COMPLETA SIMULADA (pantallas tactiles)
    // fsFalso: el iframe esta ampliado con position:fixed sobre toda la ventana. Se recuerda en el propio iframe (data-pj-fs) porque Streamlit puede
    // recargar el contenido sin cambiar el elemento iframe y este script arrancaria de nuevo sin saber que ya esta ampliado.
    var fsFalso = false;
    var marcoFs = window.frameElement;
    /** Indica si la ventana padre es de celular o tablet (hasta 1024 px, el mismo corte que el CSS de la plataforma). */
    function esTactil(){ try { return window.parent.innerWidth <= 1024; } catch (e) { return false; } }
    /** Amplia el iframe a toda la ventana (position:fixed con !important para ganar a la regla de alto de la plataforma). Devuelve false si no se puede. */
    function entrarFsFalso(){
      if (!marcoFs || !docPadre) return false;
      marcoFs.setAttribute('data-pj-estilo', marcoFs.getAttribute('style') || '');
      marcoFs.setAttribute('data-pj-fs', '1');
      /* Boton Atras del telefono: se agrega una entrada al historial al ampliar; Atras la consume y cierra la ampliacion (en vez de salir de la pagina). */
      try {
        var P = window.parent;
        P.history.pushState({ pjFs: 1 }, '');
        if (P.__pjFsAtras) P.removeEventListener('popstate', P.__pjFsAtras);
        P.__pjFsAtras = function(){ if (fsFalso) salirFsFalso(true); };
        P.addEventListener('popstate', P.__pjFsAtras);
      } catch (e) {}
      aplicarFsFalso(true);
      return true;
    }
    /** Quita la ampliacion y devuelve al iframe su estilo anterior. */
    function salirFsFalso(desdeAtras){
      aplicarFsFalso(false);
      // Se retira la entrada de historial que se agrego al ampliar (si el cierre no vino ya del boton Atras).
      if (!desdeAtras) { try { var P = window.parent; if (P.history.state && P.history.state.pjFs) P.history.back(); } catch (e) {} }
    }
    /** Pone o quita los estilos de la ampliacion y la clase del documento padre (que la CSS usa para fijar el desplazamiento de la pagina). */
    function aplicarFsFalso(on){
      fsFalso = on;
      if (on) {
        /* La tarjeta de precio de la pagina (simbolo, precio, Bid/Ask) se queda fija sobre el grafico para abrir la lista de activos sin salir; el
           iframe se baja lo que mide la tarjeta (CSS de riel/estilos.css: html.pj-grafico-expandido .pj-cab-precio). */
        var cab = docPadre.querySelector('.pj-cab-precio');
        var desplazo = cab ? Math.round(cab.getBoundingClientRect().height) + 14 : 0;
        [['position','fixed'],['top',desplazo + 'px'],['left','0'],['width','100%'],['height','calc(100% - ' + desplazo + 'px)'],['max-width','none'],['min-height','0'],['z-index','100010'],['border','0'],['background','#0d1117']]
          .forEach(function(p){ marcoFs.style.setProperty(p[0], p[1], 'important'); });
      } else {
        var previo = marcoFs.getAttribute('data-pj-estilo') || '';
        if (previo) marcoFs.setAttribute('style', previo); else marcoFs.removeAttribute('style');
        marcoFs.removeAttribute('data-pj-fs'); marcoFs.removeAttribute('data-pj-estilo');
      }
      docPadre.documentElement.classList.toggle('pj-grafico-expandido', on);
    }
    // Si el iframe ya estaba ampliado antes de cargar este script, se retoma ese estado.
    if (marcoFs && marcoFs.getAttribute('data-pj-fs') === '1') { fsFalso = true; }
    // TITULO EN PANTALLA COMPLETA

    /**
     * Indica si la pantalla completa está activa sobre este iframe o sobre el contenedor del gráfico, consultando
     * también el documento padre de Streamlit.
     */
    function enPantallaCompleta(){
      if (fsFalso) return true;
      var fe = docPadre ? docPadre.fullscreenElement : document.fullscreenElement;
      if (!fe && document.fullscreenElement) fe = document.fullscreenElement;
      return !!fe && (fe === window.frameElement || fe === contenedorFs);
    }
    // TITULO ALTERNAR PANTALLA COMPLETA

    /**
     * Entra o sale de pantalla completa: pide pantalla completa del iframe entero (o del contenedor si no es posible)
     * y sale usando el documento que la tiene.
     */
    function alternarPantallaCompleta(){
      if (fsFalso) { salirFsFalso(false); return; }
      /* Pantallas tactiles: la API de pantalla completa no existe en el iPhone y en Android quita las barras propias; se amplia el iframe a toda la ventana. */
      if (esTactil() && entrarFsFalso()) return;
      if (enPantallaCompleta()) {
        var d = (docPadre && docPadre.fullscreenElement) ? docPadre : document;
        if (d.exitFullscreen) d.exitFullscreen();
        return;
      }
      /** Alternativa de alternarPantallaCompleta: pone en pantalla completa solo el contenedor del gráfico. */
      var respaldo = function(){ if (contenedorFs.requestFullscreen) contenedorFs.requestFullscreen(); };
      var fe = window.frameElement;
      if (fe && fe.requestFullscreen) {
        var p = null;
        try { p = fe.requestFullscreen(); } catch (e) { respaldo(); return; }
        if (p && p.catch) p.catch(respaldo);
      } else { respaldo(); }
    }
    if (botonCompletoEl) botonCompletoEl.addEventListener('click', alternarPantallaCompleta);
    /* Con el grafico ampliado en pantalla tactil, VENDER/COMPRAR del grafico abren el panel Operar (con el lado elegido) en vez de operar a mercado:
       se pulsa el boton de la barra Vender/Comprar de la pagina (riel.js), cuyas hojas se muestran sobre el grafico. Devuelve true si lo atendio. */
    window.__pjOperarDesdeGrafico = function(lado){
      if (!fsFalso || !docPadre) return false;
      var b = docPadre.querySelector(lado === 'SELL' ? '.pj-op-vender' : '.pj-op-comprar');
      if (!b) return false;
      b.click();
      return true;
    };
    // TITULO MENUS DE LA BARRA SUPERIOR EN PANTALLAS TACTILES
    /* En pantallas tactiles la barra superior se desplaza de lado (css/10_base_y_barra_superior.css) y un contenedor con desplazamiento recorta a sus hijos absolutos,
       asi que al abrirse cada menu desplegable (clase show) se coloca con position:fixed bajo su boton, alineado a la derecha y sin salirse de la ventana; al
       cerrarse o salir de pantalla tactil se restauran sus estilos, y desplazar la barra lo cierra. */
    function colocarMenuFijo(m){
      if (!esTactil() || !m.classList.contains('show')) { m.style.position = m.style.top = m.style.right = m.style.left = m.style.maxHeight = m.style.overflowY = ''; return; }
      var boton = m.parentNode.querySelector('button'), r = (boton || m.parentNode).getBoundingClientRect();
      m.style.position = 'fixed'; m.style.top = Math.round(r.bottom) + 'px'; m.style.left = 'auto';
      m.style.right = Math.max(4, Math.round(window.innerWidth - r.right)) + 'px';
      m.style.maxHeight = Math.max(120, window.innerHeight - Math.round(r.bottom) - 8) + 'px'; m.style.overflowY = 'auto';
    }
    var menusBarraSuperior = document.querySelectorAll('.tradingview-desplegable-contenido');
    var observadorMenus = new MutationObserver(function(cambios){ cambios.forEach(function(c){ colocarMenuFijo(c.target); }); });
    Array.prototype.forEach.call(menusBarraSuperior, function(m){ observadorMenus.observe(m, { attributes: true, attributeFilter: ['class'] }); });
    var barraSuperiorEl = document.getElementById('tradingview-barra-superior');
    if (barraSuperiorEl) barraSuperiorEl.addEventListener('scroll', function(){ Array.prototype.forEach.call(menusBarraSuperior, function(m){ m.classList.remove('show'); }); }, { passive: true });

    var botonExpandirMovil = document.getElementById('boton-expandir-movil');
    if (botonExpandirMovil) botonExpandirMovil.addEventListener('click', alternarPantallaCompleta);

    // --- Selector de activo ---
    // Elementos del selector de activo
    var panelSeleccion = document.getElementById('seleccion-activo');
    var listaSeleccion = document.getElementById('seleccion-activo-lista');
    var mensajeSeleccion = document.getElementById('seleccion-activo-mensaje');
    var simboloEl = document.getElementById('leyenda-simbolo');

    // TITULO CONSTRUIR SELECTOR

    /**
     * Dibuja la lista de activos de la watchlist (icono, nombre, descripción y marca del activo actual) y asocia el
     * clic a elegirActivo.
     */
    function construirSelector(){
      listaSeleccion.innerHTML = '';
      ACTIVOS.forEach(function(a, i){
        var fila = document.createElement('div'); fila.className = 'seleccion-fila';
        var ico = document.createElement('div'); ico.className = 'seleccion-icono'; ico.innerHTML = a.i || '';
        var txt = document.createElement('div'); txt.className = 'seleccion-texto';
        var nom = document.createElement('span'); nom.className = 'seleccion-nombre'; nom.textContent = a.b;
        txt.appendChild(nom);
        if (a.n) { var de = document.createElement('span'); de.className = 'seleccion-descripcion'; de.textContent = a.n; txt.appendChild(de); }
        fila.appendChild(ico); fila.appendChild(txt);
        if (a.a) { var ok = document.createElement('span'); ok.className = 'seleccion-aceptar'; ok.textContent = String.fromCharCode(10003); fila.appendChild(ok); }
        fila.addEventListener('click', function(){ elegirActivo(i); });
        listaSeleccion.appendChild(fila);
      });
    }
    // TITULO ABRIR SELECTOR ACTIVO

    /** Muestra el panel selector de activo; solo funciona en pantalla completa y si hay activos. */
    function abrirSelectorActivo(){
      if (!enPantallaCompleta() || !ACTIVOS.length) return;
      mensajeSeleccion.textContent = '';
      construirSelector();
      panelSeleccion.classList.add('abierto');
    }
    // TITULO CERRAR SELECTOR ACTIVO

    /** Oculta el panel selector de activo. */
    function cerrarSelectorActivo(){ panelSeleccion.classList.remove('abierto'); }
    // TITULO ELEGIR ACTIVO

    /**
     * Cambia al activo número i pulsando el botón oculto de Streamlit correspondiente; si no se puede, muestra un
     * mensaje.
     */
    function elegirActivo(i){
      var a = ACTIVOS[i];
      if (!a) return;
      if (a.a) { cerrarSelectorActivo(); return; }
      // Streamlit tiene un botón oculto por activo (posiciones_grafico.gatillos_cierre): se pulsa el nº i
      var b = null;
      try { b = docPadre.querySelector('.st-key-grafico_cerrar_sel_' + i + ' button'); } catch (e) {}
      if (!b) { mensajeSeleccion.textContent = 'No se pudo cambiar de activo desde aquí. Sal de la pantalla completa y elígelo en la lista.'; return; }
      mensajeSeleccion.textContent = 'Cambiando a ' + a.b + '…';
      b.click();
    }
    // Eventos del selector: el nombre del activo lo abre o cierra; la X, un clic fuera o Escape lo cierran
    if (simboloEl) simboloEl.addEventListener('click', function(e){
      e.stopPropagation();
      if (panelSeleccion.classList.contains('abierto')) cerrarSelectorActivo(); else abrirSelectorActivo();
    });
    document.getElementById('seleccion-activo-x').addEventListener('click', cerrarSelectorActivo);
    document.addEventListener('mousedown', function(e){
      if (panelSeleccion.classList.contains('abierto') && !panelSeleccion.contains(e.target) && e.target !== simboloEl) cerrarSelectorActivo();
    });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape') { cerrarSelectorActivo(); if (fsFalso) salirFsFalso(false); } });

    // --- Modo pantalla completa (clase pj-fs): se revisa a menudo porque el evento llega al documento padre ---
    // fsPrevio: último estado de pantalla completa visto, para detectar cambios
    var fsPrevio = null;
    // TITULO SINCRONIZAR PANTALLA

    /**
     * Revisa si cambió el estado de pantalla completa: actualiza la clase pj-fs, cierra el selector al salir y
     * redibuja los dibujos.
     */
    function sincronizarPantalla(){
      document.documentElement.classList.toggle('pj-tactil', esTactil());
      var fs = enPantallaCompleta();
      if (fs === fsPrevio) return;
      fsPrevio = fs;
      contenedorFs.classList.toggle('pj-fs', fs);
      if (!fs) cerrarSelectorActivo();
      redibujarTodo();
    }
    // Se revisa cada 200 ms porque el evento de pantalla completa llega al documento padre
    setInterval(sincronizarPantalla, 200);
    sincronizarPantalla();

/* -------------------------------------------------------------------------------------------------------
   ------------------------------- FIN Piña y Jara 55_pantalla_completa .JS ------------------------------
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
