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
   --------------------------------- INICIO Piña y Jara 30_utilidades .JS --------------------------------
   ------------------------------------------------------------------------------------------------------- */

      // TITULO FMT

      /**
       * Formatea un número con separador de miles y exactamente d decimales (formato en-US).
       * Recibe v (número) y d (decimales); devuelve el texto.
       */
      function fmt(v, d){ return Number(v).toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d}); }
      // TITULO TXT

      /**
       * Cambia el texto de un elemento solo si es distinto (evita repintados innecesarios en cada tick).
       * Recibe el elemento el y el texto t.
       */
      function txt(el, t){ if (el.textContent !== t) el.textContent = t; }
      // TITULO REDONDEAR

      /**
       * Redondea un precio a los decimales del símbolo (DIGITS). Recibe px y devuelve el número redondeado.
       */
      function redondear(px){ var f = Math.pow(10, DIGITS); return Math.round(px * f) / f; }
      // TITULO ES COMPRA

      /**
       * Indica si el elemento it es de compra (tipos 0 Buy, 2 Buy Limit y 4 Buy Stop). Devuelve un booleano.
       */
      function esCompra(it){ return it.t === 0 || it.t === 2 || it.t === 4; }
      // TITULO PRECIO ENTRADA

      /**
       * Precio de entrada vigente de it: el que se está arrastrando (pendiente en el nodo n) o el original.
       */
      function precioEntrada(it, n){ return (n && n.pend.po !== undefined) ? n.pend.po : it.po; }
      // TITULO PG EN

      /**
       * Proyecta la ganancia o pérdida si el precio llega a px.
       * Recibe it (elemento), entrada (precio de entrada) y px; devuelve dinero con signo (compra gana al subir, venta al bajar).
       */
      // P/G si el precio llega a `px` (k = valor de 1 unidad de precio por lote)
      function gananciaPerdidaEn(it, entrada, px){ return (esCompra(it) ? 1 : -1) * (px - entrada) * (it.k || K) * it.v; }
      // TITULO ETIQUETA

      /**
       * Texto corto del elemento, por ejemplo 'Buy Limit 0.10' (tipo y volumen con 2 decimales).
       */
      function etiqueta(it){ return TIPO[it.t] + ' ' + fmt(it.v, 2); }

      // TITULO VALIDAR

      /**
       * Valida un nivel antes de enviarlo al servidor.
       * Recibe it (elemento), f (campo: 'po', 'sl' o 'tp'), px (precio propuesto) y entrada (precio de entrada de la orden).
       * Devuelve '' si es válido o el motivo del rechazo (lado incorrecto respecto al precio actual o a la entrada).
       */
      // '' si es válido; si no, el motivo
      function validar(it, f, px, entrada){
        // Distancia mínima de stops del bróker para este elemento.
        var m = it.sm || SM;
        // Precio de entrada de una orden pendiente: debe quedar del lado correcto del mercado actual.
        if (f === 'po'){
          if (!BID || !ASK) return '';
          if (it.t === 2 && !(px < ASK - m)) return 'un Buy Limit debe quedar bajo el precio actual (Ask)';
          if (it.t === 4 && !(px > ASK + m)) return 'un Buy Stop debe quedar sobre el precio actual (Ask)';
          if (it.t === 3 && !(px > BID + m)) return 'un Sell Limit debe quedar sobre el precio actual (Bid)';
          if (it.t === 5 && !(px < BID - m)) return 'un Sell Stop debe quedar bajo el precio actual (Bid)';
          return '';
        }
        // SL y TP: se comparan con el precio de referencia (actual para posiciones, entrada para órdenes).
        // posición: contra el precio actual; orden pendiente: contra su precio de entrada
        var ref = it.kind === 'ord' ? entrada : (it.pc || it.po), c = esCompra(it);
        var donde = it.kind === 'ord' ? 'el precio de entrada' : 'el precio actual';
        if (f === 'sl' && c && !(px < ref - m)) return 'en una compra el Stop Loss debe quedar bajo ' + donde;
        if (f === 'sl' && !c && !(px > ref + m)) return 'en una venta el Stop Loss debe quedar sobre ' + donde;
        if (f === 'tp' && c && !(px > ref + m)) return 'en una compra el Take Profit debe quedar sobre ' + donde;
        if (f === 'tp' && !c && !(px < ref - m)) return 'en una venta el Take Profit debe quedar bajo ' + donde;
        return '';
      }

      // TITULO AVISAR

      /**
       * Muestra un aviso temporal en la capa (verde si fue bien, rojo si es un error) y lo apaga a los 3,8 segundos.
       * Recibe el texto t y malo (true para error).
       */
      function avisar(t, malo){
        var el = document.getElementById('pj-posicion-aviso');
        if (!el){ el = document.createElement('div'); el.id = 'pj-posicion-aviso'; capa.appendChild(el); }
        el.textContent = t;
        el.style.borderColor = malo ? '#da3633' : '#2ea043';
        el.style.opacity = '1';
        clearTimeout(tAviso);
        tAviso = setTimeout(function(){ el.style.opacity = '0'; }, 3800);
      }


/* -------------------------------------------------------------------------------------------------------
   ---------------------------------- FIN Piña y Jara 30_utilidades .JS ----------------------------------
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
