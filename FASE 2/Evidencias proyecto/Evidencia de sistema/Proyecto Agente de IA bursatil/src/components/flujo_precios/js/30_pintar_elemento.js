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
   ------------------------------ INICIO Piña y Jara 30_pintar_elemento .JS ------------------------------
   ------------------------------------------------------------------------------------------------------- */

  /**
   * Pinta un elemento marcado con data-pj-s a partir de un tick `t`.
   * Campos del tick: l = último precio, b = bid, a = ask, ch = cambio del día, pct = cambio en %.
   * Según data-pj-f escribe variación (var), cambio o porcentaje (ch/pct), spread (spr) o precio
   * (px/bid/ask/side), y opcionalmente colorea el destello verde/rojo. Modifica texto y estilo del DOM.
   */
  function pintarElem(el, t){
    // Campo a mostrar (por defecto el último precio), prefijo opcional y valor numérico a pintar.
    var f = el.getAttribute('data-pj-f') || 'px';
    var pre = el.getAttribute('data-pj-pre') || '';
    var v;
    // Variación completa: "+cambio (+pct%)" con colores configurables.
    if (f === 'var'){
      // Decimales según el precio actual.
      var d = dec(el, t.l);
      var up = el.getAttribute('data-pj-up') || '#3fb950';
      var dn = el.getAttribute('data-pj-dn') || '#f85149';
      // Texto: signo + cambio y porcentaje entre paréntesis.
      poner(el, (t.ch >= 0 ? '+' : '') + fmt(t.ch, d) + ' (' + (t.pct >= 0 ? '+' : '') + t.pct.toFixed(2) + '%)');
      color(el, t.ch >= 0 ? up : dn);
      return;
    }
    if (f === 'ch' || f === 'pct'){
      // cambio del día por separado (tablas): 'ch' en precio, 'pct' en % con flecha;
      // data-pj-pill="1" también pinta el fondo (pastilla verde/roja)
      var sube = t.ch >= 0;
      var txt = (f === 'ch') ? (sube ? '+' : '') + fmt(t.ch, dec(el, t.l))
                             : (sube ? '▲ +' : '▼ ') + t.pct.toFixed(2) + '%';
      poner(el, txt);
      color(el, sube ? (el.getAttribute('data-pj-up') || '#3fb950')
                     : (el.getAttribute('data-pj-dn') || '#f85149'));
      if (el.getAttribute('data-pj-pill') === '1'){
        var bg = sube ? 'rgba(63,185,80,.12)' : 'rgba(248,81,73,.12)';
        if (el.style.background !== bg) el.style.background = bg;
      }
      return;
    }
    // Spread en pips: (ask - bid) dividido por el tamaño del pip.
    if (f === 'spr'){
      var pip = parseFloat(el.getAttribute('data-pj-pip')) || 0;
      if (!pip) return;
      var s = (t.a - t.b) / pip;
      poner(el, s < 100 ? fmt(s, 1) : fmt(s, 0));
      return;
    }
    // Selección del valor según el campo; "side" usa bid para SELL y ask para BUY.
    if (f === 'bid') v = t.b;
    else if (f === 'ask') v = t.a;
    else if (f === 'side') v = (el.getAttribute('data-pj-side') === 'SELL') ? t.b : t.a;
    else v = t.l;
    if (!v) return;
    // Escribe el precio formateado con su prefijo.
    poner(el, pre + fmt(v, dec(el, v)));
    // Destello: verde si el precio subió respecto al tick anterior, rojo si bajó.
    if (el.getAttribute('data-pj-flash') === '1'){
      var prev = parseFloat(el.getAttribute('data-pj-prev'));
      if (!isNaN(prev) && v !== prev) color(el, v > prev ? '#3fb950' : '#f85149');
      el.setAttribute('data-pj-prev', String(v));
    }
  }


/* -------------------------------------------------------------------------------------------------------
   -------------------------------- FIN Piña y Jara 30_pintar_elemento .JS -------------------------------
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
