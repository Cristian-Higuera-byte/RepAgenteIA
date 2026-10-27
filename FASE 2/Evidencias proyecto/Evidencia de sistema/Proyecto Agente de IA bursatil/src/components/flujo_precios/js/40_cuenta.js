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
   ----------------------------------- INICIO Piña y Jara 40_cuenta .JS ----------------------------------
   ------------------------------------------------------------------------------------------------------- */

  /**
   * Pinta todos los elementos que dependen de los datos de la cuenta (último mensaje `cuenta`).
   * Cubre: data-pj-acc (equity, profit y formatos genéricos usd/pct/signed), barras data-pj-bar,
   * precio actual por ticket (data-pj-posc), P/G por ticket (data-pj-pos) y los textos de los botones de
   * cierre de posiciones. Modifica texto, color y ancho en el DOM; no devuelve nada.
   */
  function pintarCuenta(){
    // Sin datos de cuenta todavía no hay nada que pintar.
    if (!cuenta) return;
    // Valores de cuenta (equity, profit, balance, margen, etc.).
    D.querySelectorAll('[data-pj-acc]').forEach(function(el){
      var f = el.getAttribute('data-pj-acc');
      var formato = el.getAttribute('data-pj-fmt');
      if (formato){                                   // formato genérico (Inicio)
        var val = cuenta[f];
        if (val === undefined || val === null) return;
        var txt;
        if (formato === 'pct') txt = val ? fmt(val, 2) + '%' : '—';
        else if (formato === 'signed') txt = (val >= 0 ? '+' : '') + fmt(val, 2) + (el.getAttribute('data-pj-suf') || '');
        else txt = '$' + fmt(val, 2);
        poner(el, txt);
        if (el.getAttribute('data-pj-color') === '1') color(el, val >= 0 ? '#3fb950' : '#f85149');
        return;
      }
      // Formatos específicos antiguos: equity con divisa y profit con signo.
      if (f === 'equity'){
        poner(el, '$' + fmt(cuenta.equity, 2) + ' ' + (cuenta.currency || ''));
      } else if (f === 'profit'){
        var p = cuenta.profit || 0;
        var vacio = Math.abs(p) < 0.005 && el.getAttribute('data-pj-zero') !== '1';
        poner(el, vacio ? '' : (p >= 0 ? '+' : '') + fmt(p, 2) + (el.getAttribute('data-pj-suf') || ''));
        color(el, p >= 0 ? (el.getAttribute('data-pj-up') || '#3fb950')
                         : (el.getAttribute('data-pj-dn') || '#f85149'));
      }
    });
    // Barras de porcentaje (0-100) cuyo ancho sigue un campo de la cuenta.
    D.querySelectorAll('[data-pj-bar]').forEach(function(el){
      var v = cuenta[el.getAttribute('data-pj-bar')];
      if (v === undefined || v === null) return;
      var w = Math.max(0, Math.min(100, v)).toFixed(1) + '%';
      if (el.style.width !== w) el.style.width = w;
    });
    // Precio actual por ticket de posición.
    var pc = cuenta.pc || {};
    D.querySelectorAll('[data-pj-posc]').forEach(function(el){
      var v = pc[el.getAttribute('data-pj-posc')];
      if (v === undefined) return;
      var d = el.getAttribute('data-pj-d');
      poner(el, fmt(v, (d !== null && d !== '') ? +d : 5));
    });
    // P/G neto (profit + swap) por ticket de posición.
    var pos = cuenta.pos || {};
    D.querySelectorAll('[data-pj-pos]').forEach(function(el){
      var v = pos[el.getAttribute('data-pj-pos')];
      if (v === undefined) return;          // posición recién cerrada: la quita el refresco
      poner(el, (v >= 0 ? '+' : '') + fmt(v, 2));
      color(el, v >= 0 ? (el.getAttribute('data-pj-up') || '#3fb950')
                       : (el.getAttribute('data-pj-dn') || '#f85149'));
    });
    // Botón del modal "¿Quiere cerrar su posición?" (cartera_panel.py): su
    // contenedor se llama st-key-ca_btncerrar_<ticket>; el texto sigue el P/G vivo.
    D.querySelectorAll('[class*="st-key-ca_btncerrar_"]').forEach(function(el){
      var m = el.className.match(/st-key-ca_btncerrar_(\d+)/);
      var v = m ? pos[m[1]] : undefined;
      if (v === undefined) return;
      var txt = el.querySelector('button p') || el.querySelector('button');
      // Formato XM (igual que texto_cerrar() en Python): "-$220.00" / "$280.00"
      if (txt) poner(txt, 'Cerrar con ' + (v >= 0 ? 'ganancia' : 'pérdida') + ' de ' +
                          (v < 0 ? '-' : '') + '$' + fmt(Math.abs(v), 2));
    });
    // Botón "Cerrar operación: $X" del drawer de detalle (cartera_panel.py):
    // contenedor st-key-cadet_cerrar_<ticket>; el monto sigue el P/G vivo.
    D.querySelectorAll('[class*="st-key-cadet_cerrar_"]').forEach(function(el){
      var m = el.className.match(/st-key-cadet_cerrar_(\d+)/);
      var v = m ? pos[m[1]] : undefined;
      if (v === undefined) return;
      var txt = el.querySelector('button p') || el.querySelector('button');
      if (txt) poner(txt, 'Cerrar operación: ' + (v < 0 ? '-' : '') + '$' + fmt(Math.abs(v), 2));
    });
  }


/* -------------------------------------------------------------------------------------------------------
   ------------------------------------ FIN Piña y Jara 40_cuenta .JS ------------------------------------
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
