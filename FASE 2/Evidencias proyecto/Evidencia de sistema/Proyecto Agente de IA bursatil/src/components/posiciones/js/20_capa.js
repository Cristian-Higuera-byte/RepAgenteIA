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
   ------------------------------------ INICIO Piña y Jara 20_capa .JS -----------------------------------
   ------------------------------------------------------------------------------------------------------- */

      // Capa HTML superpuesta al gráfico: contiene todas las líneas, etiquetas, menús y avisos de este módulo.
      var capa = document.createElement('div'); capa.id = 'pj-pos';
      containerEl.parentNode.appendChild(capa);
      // ITEMS: elementos dibujados por id; nodos: nodos DOM por id; drag: arrastre en curso; tAviso: temporizador del aviso;
      // menu y conf: menú contextual y tarjeta de confirmación abiertos (o null).
      var ITEMS = {}, nodos = {}, drag = null, tAviso = null, menu = null, conf = null;
      // Etiqueta del precio en vivo (la nativa del gráfico se apagó en central_panel):
      // la dibujamos nosotros para que mida igual que las demás, llegue al borde y mande en el apilado.
      // Elemento de la etiqueta del precio en vivo, oculto hasta el primer tick.
      var liveEl = document.createElement('div'); liveEl.className = 'ej ejlive';
      liveEl.style.display = 'none'; capa.appendChild(liveEl);


/* -------------------------------------------------------------------------------------------------------
   ------------------------------------- FIN Piña y Jara 20_capa .JS -------------------------------------
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
