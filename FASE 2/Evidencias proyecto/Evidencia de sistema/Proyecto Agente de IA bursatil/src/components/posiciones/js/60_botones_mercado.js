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
   ------------------------------ INICIO Piña y Jara 60_botones_mercado .JS ------------------------------
   ------------------------------------------------------------------------------------------------------- */

      // ---------- Botones VENDER / COMPRAR a mercado (solo en pantalla completa) ----------
      // Misma lógica que el ticket: One-Click Trading activo -> al instante; apagado -> se confirma en el propio gráfico.
      // Volumen = el del ticket (o el mínimo del símbolo si el ticket no está a la vista). Ejecuta por POST /mercado.
      /* La barra de mercado se arma una vez: botón de venta (Bid), spread y botón de compra (Ask). */
      var mercado = document.createElement('div'); mercado.id = 'pj-mercado';
      mercado.innerHTML = '<button class="vend" type="button" title="Vender a mercado"><b>—</b><span>VENDER</span></button>' +
        '<span class="spr" title="Spread">—</span>' +
        '<button class="comp" type="button" title="Comprar a mercado"><b>—</b><span>COMPRAR</span></button>';
      // Se inserta en la leyenda del gráfico, antes de la leyenda de comparación.
      var legendEl = document.getElementById('tv-legend');
      if (legendEl) legendEl.insertBefore(mercado, document.getElementById('tv-cmp-legend'));
      // Referencias a los textos de Bid, Ask y spread para actualizarlos sin recrear el DOM.
      var mBid = mercado.querySelector('.vend b'), mAsk = mercado.querySelector('.comp b'), mSpr = mercado.querySelector('.spr');
      /**
       * Refresca los precios Bid y Ask de los botones y el spread en pips (o en puntos si PIP no está definido).
       * Muestra un guion largo mientras no haya precio.
       */
      function actualizarMercado(){
        txt(mBid, BID ? fmt(BID, DIGITS) : '—');
        txt(mAsk, ASK ? fmt(ASK, DIGITS) : '—');
        var sp = (BID && ASK) ? (ASK - BID) / (PIP > 0 ? PIP : Math.pow(10, -DIGITS)) : null;
        txt(mSpr, sp === null ? '—' : sp.toFixed(1));
      }
      /**
       * Envía una orden a mercado (POST /mercado) tras confirmar, o al instante con One-Click.
       * Recibe lado ('BUY' o 'SELL'); usa el volumen del ticket y avisa el resultado. Sin precio en vivo no opera.
       */
      function ordenMercado(lado){
        if (!BID || !ASK){ avisar('Sin precio en vivo: no se puede operar ahora', true); return; }
        var vol = volumenTicket(), compra = lado === 'BUY', precio = compra ? ASK : BID;
        accion(compra ? 'Comprar a mercado' : 'Vender a mercado',
               '<b>' + (compra ? 'Compra' : 'Venta') + ' ' + fmt(vol, 2) + '</b> ' + REAL +
               ' al precio de mercado (~<b>' + fmt(precio, DIGITS) + '</b>)', function(){
          post('/mercado', {symbol: REAL, lado: lado, volumen: vol}).then(function(res){
            if (res.error){ avisar(res.error, true); return; }
            avisar((compra ? 'Comprados ' : 'Vendidos ') + fmt(res.volume || vol, 2) + ' lote(s) de ' + REAL +
                   ' a ' + fmt(res.price || precio, DIGITS), false);
          });
        });
      }
      // Evita que el clic en los botones llegue al gráfico; luego se conecta cada botón con su lado.
      mercado.addEventListener('mousedown', function(e){ e.stopPropagation(); });
      mercado.querySelector('.vend').onclick = function(){ ordenMercado('SELL'); };
      mercado.querySelector('.comp').onclick = function(){ ordenMercado('BUY'); };


/* -------------------------------------------------------------------------------------------------------
   -------------------------------- FIN Piña y Jara 60_botones_mercado .JS -------------------------------
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
