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
   ---------------------------------- INICIO Piña y Jara 99_en_vivo .JS ----------------------------------
   ------------------------------------------------------------------------------------------------------- */

      // En vivo: Bid/Ask (ticks) y altas/bajas/SL/TP/P-G (mensaje de cuenta del feed)
      // Suscripción al canal que reparte los ticks y el mensaje de cuenta del feed (solo si el navegador lo soporta).
      if ('BroadcastChannel' in window){
        /**
         * Recibe cada mensaje del feed. d.t trae los precios por símbolo y d.acc el estado de la cuenta.
         * Actualiza BID/ASK y el desfase horario, el editor abierto, y reconstruye POS y ORD cuando cambian
         * (acc.pi posiciones, acc.ord órdenes, acc.pos P/G, acc.pc precio actual).
         */
        new BroadcastChannel('pj-ticks').addEventListener('message', function(ev){
          var d = ev.data || {};
          // Tick del símbolo del gráfico (por nombre mostrado o por nombre real).
          var t = d.t && (d.t[SIMBOLO] || d.t[REAL]);
          if (t && t.b){
            BID = t.b; ASK = t.a;
            if (t.t) OFF = Math.round((t.t - Date.now() / 1000) / 900) * 900;
            if (ed && ed._revisar && document.activeElement && !ed.contains(document.activeElement)) ed._revisar();
          }
          // Mensaje de cuenta: si no viene, no hay nada más que hacer.
          var acc = d.acc;
          if (!acc) return;
          if (acc.pi){
            // Lista completa de posiciones: se reconstruye solo con las del símbolo y se les adjunta P/G (p) y precio actual (pc).
            var np = {};
            for (var tk in acc.pi){
              var x = acc.pi[tk];
              if (x.s !== REAL) continue;
              np[tk] = {s: x.s, t: x.t, v: x.v, po: x.po, sl: x.sl, tp: x.tp, k: x.k, sm: x.sm,
                        tr: x.tr, p: (acc.pos || {})[tk], pc: (acc.pc || {})[tk]};
            }
            POSICION = np;
          } else {
            // Sin lista nueva: solo se actualizan P/G y precio actual de las posiciones existentes.
            for (var tk2 in POSICION){
              if (acc.pos && tk2 in acc.pos) POSICION[tk2].p = acc.pos[tk2];
              if (acc.pc && tk2 in acc.pc) POSICION[tk2].pc = acc.pc[tk2];
            }
          }
          if (acc.ord){
            // Lista completa de órdenes pendientes del símbolo.
            var no = {};
            for (var tk3 in acc.ord){ var o = acc.ord[tk3]; if (o.s === REAL) no[tk3] = o; }
            ORDEN = no;
          }
          // Si cambió alguna lista se recrean o borran las líneas.
          if (acc.pi || acc.ord) unir();
        });
      }
      // ¿El servidor de datos en ejecución es la versión que espera este código?
      // Versión mínima de la API del servidor que espera este código.
      var V_API = 6;
      fetch(API + '/salud').then(function(r){ return r.json(); }).then(function(r){
        if (!r.v || r.v < V_API){
          avisar('El servidor de datos está desactualizado: reinicia servidor_datos.py', true);
          var el = document.getElementById('pj-posicion-aviso'); clearTimeout(tAviso);
          if (el) el.style.whiteSpace = 'normal';
        }
      }).catch(function(){});
      unir();
      // Arranque: primer armado de líneas con los datos iniciales y comienzo del bucle de dibujo.
      // Aquí termina la función autoejecutable abierta en 00_inicio.js.
      ubicar();
    })();

/* -------------------------------------------------------------------------------------------------------
   ------------------------------------ FIN Piña y Jara 99_en_vivo .JS -----------------------------------
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
