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
   ---------------------------------- INICIO Piña y Jara 10_estilos .JS ----------------------------------
   ------------------------------------------------------------------------------------------------------- */

      // Hoja de estilos del trading desde el gráfico. Se arma como una sola cadena CSS (concatenada) y se agrega al
      // documento del iframe; no se usa un archivo aparte porque el gráfico vive en un iframe aislado.
      var est = document.createElement('style');
      est.textContent =
        // Capa de superposición que cubre el gráfico (pj-posicion): no captura el ratón salvo en sus controles.
        '#pj-posicion{position:absolute;pointer-events:none;z-index:6;overflow:hidden;}' +
        // Línea de nivel (pl) y su trazo (ln); las órdenes pendientes (po) usan trazo discontinuo.
        '#pj-posicion .pl{position:absolute;left:0;height:0;}' +
        '#pj-posicion .ln{position:absolute;left:0;top:0;height:0;border-top:1px solid;}' +
        '#pj-posicion .po .ln{border-top-style:dashed;}' +
        // Etiqueta (tg) con tres partes: lotes (vo), P/G (pg) y botón de cierre (x).
        '#pj-posicion .tg{position:absolute;top:-11px;height:22px;display:flex;align-items:stretch;pointer-events:auto;' +
        'font:600 12px "Source Sans Pro",system-ui,sans-serif;border-radius:4px;overflow:hidden;' +
        'box-shadow:0 2px 8px rgba(0,0,0,.45);cursor:default;white-space:nowrap;}' +
        '#pj-posicion .lv .tg,#pj-posicion .po .tg{cursor:ns-resize;}' +
        '#pj-posicion .vo{display:flex;align-items:center;padding:0 8px;color:#fff;border:1px solid transparent;border-right:none;}' +
        '#pj-posicion .pg{display:flex;align-items:center;padding:0 9px;background:#161b22;border:1px solid;border-left:none;border-right:none;' +
        'font-family:ui-monospace,Consolas,monospace;font-variant-numeric:tabular-nums;}' +
        '#pj-posicion .x{display:flex;align-items:center;justify-content:center;width:22px;background:#161b22;border:1px solid;' +
        'border-left:1px solid #30363d;color:#8b949e;cursor:pointer;font-size:13px;}' +
        '#pj-posicion .x:hover{background:#da3633;color:#fff;}' +
        // Etiquetas del eje de precios (ej) y del precio en vivo (ejlive).
        '#pj-posicion .ej{position:absolute;right:0;top:-10px;height:20px;display:flex;align-items:center;justify-content:center;' +
        'box-sizing:border-box;color:#fff;font:600 11.5px ui-monospace,Consolas,monospace;}' +   // todos iguales, rectángulo completo
        '#pj-posicion .ejlive{position:absolute;right:0;z-index:7;background:#e6edf3;color:#0d1117;}' +   // precio en vivo (blanco), lo dibujamos nosotros
        // Estados de la línea: pendiente de confirmación (pend, semitransparente) y valor inválido (mal, punteada).
        '#pj-posicion .pl.pend{opacity:.5;}' +
        '#pj-posicion .pl.mal .ln{border-top-style:dotted;border-top-width:2px;}' +
        // Insignias TP/SL arrastrables (bds, bd) y conectores de nivel (cn).
        '#pj-posicion .bds{position:absolute;top:-11px;height:22px;display:flex;gap:4px;pointer-events:auto;}' +
        '#pj-posicion .bd{display:flex;align-items:center;padding:0 7px;border:1px dashed;border-radius:4px;background:#0d1117;' +
        'font:700 11.5px "Source Sans Pro",system-ui,sans-serif;cursor:ns-resize;user-select:none;}' +
        '#pj-posicion .bd:hover{background:#161b22;}' +
        '#pj-posicion .cn{position:absolute;width:0;border-left:1px solid;}' +
        '#pj-posicion .cn:before,#pj-posicion .cn:after{content:"";position:absolute;left:-4px;width:7px;height:7px;border-radius:50%;background:inherit;}' +
        '#pj-posicion .cn:before{top:-3px;}#pj-posicion .cn:after{bottom:-3px;}' +
        // Aviso temporal de resultado, centrado arriba.
        '#pj-posicion-aviso{position:absolute;left:50%;top:40px;transform:translateX(-50%);padding:7px 14px;border-radius:8px;' +
        'background:#161b22;border:1px solid #30363d;color:#e6edf3;font:600 12.5px "Source Sans Pro",system-ui,sans-serif;' +
        'box-shadow:0 6px 20px rgba(0,0,0,.5);transition:opacity .25s;white-space:nowrap;z-index:3;}' +
        // Menú del clic derecho (pj-menu): elementos (it), íconos (ic), separadores (sep) y título (tit).
        '#pj-menu{position:absolute;min-width:230px;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:5px 0;' +
        'pointer-events:auto;box-shadow:0 10px 30px rgba(0,0,0,.6);font:13px "Source Sans Pro",system-ui,sans-serif;z-index:4;}' +
        '#pj-menu .it{display:flex;align-items:center;gap:10px;padding:7px 14px;color:#e6edf3;cursor:pointer;white-space:nowrap;}' +
        '#pj-menu .it:hover{background:#1f6feb;}' +
        '#pj-menu .it .px{margin-left:auto;padding-left:18px;color:#8b949e;font-family:ui-monospace,Consolas,monospace;}' +
        '#pj-menu .it:hover .px{color:#e6edf3;}' +
        '#pj-menu .ic{width:14px;text-align:center;font-weight:700;}' +
        '#pj-menu .sep{height:1px;background:#30363d;margin:5px 0;}' +
        '#pj-menu .dis{color:#6e7681;cursor:default;}#pj-menu .dis:hover{background:none;}' +
        '#pj-menu .tit{color:#8b949e;font-size:11.5px;padding:4px 14px 6px;}' +
        // Tarjeta de confirmación (pj-configuracion) que se muestra cuando One-Click Trading está apagado.
        '#pj-configuracion{position:absolute;left:50%;top:45%;transform:translate(-50%,-50%);min-width:300px;background:#0d1117;' +
        'border:1px solid #30363d;border-radius:12px;padding:14px 16px;pointer-events:auto;z-index:5;' +
        'box-shadow:0 14px 40px rgba(0,0,0,.65);font:13px "Source Sans Pro",system-ui,sans-serif;color:#c9d1d9;}' +
        '#pj-configuracion .t{color:#e6edf3;font-weight:700;font-size:14px;margin-bottom:6px;}' +
        '#pj-configuracion .d{margin-bottom:12px;line-height:1.45;}' +
        '#pj-configuracion .d b{color:#e6edf3;}' +
        '#pj-configuracion .bs{display:flex;gap:8px;}' +
        '#pj-configuracion button{flex:1;height:32px;border-radius:7px;border:1px solid #30363d;background:#161b22;color:#e6edf3;' +
        'font:600 13px "Source Sans Pro",system-ui,sans-serif;cursor:pointer;}' +
        '#pj-configuracion button.ok{background:linear-gradient(90deg,#ff4b4b,#ff8f00);border:none;color:#fff;}' +
        '#pj-configuracion .h{color:#8b949e;font-size:11.5px;margin-top:9px;}' +
        '#pj-configuracion .h a{color:#ff8f00;cursor:pointer;font-weight:600;}#pj-configuracion .h a:hover{text-decoration:underline;}' +
        // Editor de orden (pj-ed): cabecera, campos, cotización, proyección de P/G, mensajes y botones.
        '#pj-ed{position:absolute;left:50%;top:46%;transform:translate(-50%,-50%);width:540px;max-width:94%;background:#0d1117;' +
        'border:1px solid #30363d;border-radius:12px;pointer-events:auto;z-index:7;box-shadow:0 18px 50px rgba(0,0,0,.7);' +
        'font:13px "Source Sans Pro",system-ui,sans-serif;color:#c9d1d9;overflow:hidden;}' +
        '#pj-ed .hd{display:flex;align-items:center;justify-content:space-between;padding:11px 16px;background:#161b22;' +
        'border-bottom:1px solid #30363d;color:#e6edf3;font-weight:700;font-size:14px;}' +
        '#pj-ed .cx{cursor:pointer;color:#8b949e;font-size:15px;}#pj-ed .cx:hover{color:#fff;}' +
        '#pj-ed .cuerpo{display:flex;gap:18px;padding:16px;}' +
        '#pj-ed .campos{display:grid;grid-template-columns:auto 190px;gap:9px 12px;align-items:center;}' +
        '#pj-ed label{color:#8b949e;text-align:right;}' +
        '#pj-ed input,#pj-ed select{height:30px;background:#161b22;border:1px solid #30363d;border-radius:6px;color:#e6edf3;' +
        'padding:0 8px;font:13px ui-monospace,Consolas,monospace;outline:none;color-scheme:dark;box-sizing:border-box;width:100%;}' +
        '#pj-ed select{font-family:"Source Sans Pro",system-ui,sans-serif;}' +
        '#pj-ed input:focus,#pj-ed select:focus{border-color:#ff8f00;}' +
        '#pj-ed input:disabled{opacity:.45;}' +
        '#pj-ed .cot{flex:1;min-width:0;display:flex;flex-direction:column;align-items:stretch;justify-content:center;gap:8px;' +
        'background:#0f1620;border:1px solid #202a37;border-radius:10px;padding:10px;}' +
        '#pj-ed .fila{display:flex;align-items:baseline;justify-content:space-between;gap:10px;}' +
        '#pj-ed .fila .k{color:#8b949e;font-size:12px;}' +
        '#pj-ed .fila .v{font:700 19px ui-monospace,Consolas,monospace;white-space:nowrap;}' +
        '#pj-ed .proy{display:flex;flex-direction:column;gap:3px;border-top:1px solid #202a37;padding-top:8px;' +
        'font:12px ui-monospace,Consolas,monospace;}' +
        '#pj-ed .proy:empty{display:none;}' +
        '#pj-ed .msg{min-height:18px;padding:0 16px;color:#f85149;font-size:12.5px;}' +
        '#pj-ed .bs{display:flex;gap:10px;padding:8px 16px 4px;}' +
        '#pj-ed button{flex:1;height:34px;border-radius:7px;border:none;font:600 13.5px "Source Sans Pro",system-ui,sans-serif;cursor:pointer;color:#fff;}' +
        '#pj-ed button.ok{background:linear-gradient(90deg,#ff4b4b,#ff8f00);}' +
        '#pj-ed button.del{background:#da3633;}' +
        '#pj-ed button:disabled{opacity:.4;cursor:default;}' +
        '#pj-ed .nt{color:#8b949e;font-size:11.5px;text-align:center;padding:6px 16px 14px;}' +
        // Botones VENDER / COMPRAR a mercado (pj-mercado), visibles solo en pantalla completa (clase pj-fs de tradingview-contenedor).
        '#pj-mercado{display:none;align-items:stretch;gap:0;margin:5px 0 3px;pointer-events:auto;border-radius:5px;overflow:hidden;' +
        'box-shadow:0 2px 8px rgba(0,0,0,.45);font-family:"Source Sans Pro",system-ui,sans-serif;width:max-content;}' +
        '#tradingview-contenedor.pj-fs #pj-mercado{display:flex;}' +
        '#pj-mercado button{display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:92px;padding:5px 12px 4px;' +
        'border:none;color:#fff;cursor:pointer;line-height:1.1;}' +
        '#pj-mercado button b{font:700 14px ui-monospace,Consolas,monospace;}' +
        '#pj-mercado button span{font:700 10px "Source Sans Pro",system-ui,sans-serif;letter-spacing:.4px;margin-top:2px;}' +
        '#pj-mercado .vend{background:#e5484d;}#pj-mercado .vend:hover{background:#f2575c;}' +
        '#pj-mercado .comp{background:#1fa463;}#pj-mercado .comp:hover{background:#27b872;}' +
        '#pj-mercado .spr{display:flex;align-items:center;justify-content:center;min-width:34px;padding:0 6px;background:#0d1117;' +
        'color:#c9d1d9;font:600 12px ui-monospace,Consolas,monospace;text-shadow:none;}';
      // Inserta la hoja de estilos en el head del iframe.
      document.head.appendChild(est);

/* -------------------------------------------------------------------------------------------------------
   ------------------------------------ FIN Piña y Jara 10_estilos .JS -----------------------------------
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
