// Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
// Dirección: José Joaquín Prieto #5373 -
// San Miguel - Santiago - Chile
// contacto.pinayjara@gmail.com
// https://www.pinayjara.cl
// Creado, Programado y Diseñado por Piña y Jara
// Transportes y Servicios Ltda.


// -------------------------------------------------------------------------------------------------------
// ---------------------------------------- INICIO Piña y Jara medidor .JS -------------------------------
// -------------------------------------------------------------------------------------------------------

/*
medidor.js
----------
Actualiza en vivo, mientras se escribe, el medidor de fuerza de la contraseña (4 barras y lista de requisitos). Streamlit solo avisa al servidor cuando el
campo pierde el foco o se pulsa Enter, así que el medidor se calcula aquí, en el navegador, con la misma regla que herramientas/contrasenas.py.

Python antepone `var CFG = {...}` con la regla (requisitos, claves comunes, colores y texto de ayuda). El medidor de cada campo es un elemento con
`data-pj-medidor="<etiqueta del campo>"` que llega VACÍO desde Python; el campo se reconoce por su `aria-label`, que Streamlit toma de la etiqueta.

El medidor se dibuja dentro de un Shadow DOM del elemento: el árbol de la página es de React y, si aquí se reescribiera su contenido, al recargar Streamlit
fallaría con «NotFoundError: Failed to execute 'removeChild'». Un observador vuelve a dibujar el medidor cuando React crea el elemento de nuevo.
*/
(function () {
  var P;
  try { P = window.parent; } catch (e) { return; }
  var D = P.document;

  var DISFRAZ = { '@': 'a', '4': 'a', '3': 'e', '1': 'i', '!': 'i', '0': 'o', '$': 's', '5': 's', '7': 't' };
  var COMUNES = {};
  CFG.comunes.forEach(function (c) { COMUNES[c] = true; });
  var BORDES = /^[0-9!?#$%&*._\-+= ]+|[0-9!?#$%&*._\-+= ]+$/g;


  // TITULO SOLO LETRAS
  function soloLetras(texto) {
    return Array.from(texto).filter(function (c) { return /\p{L}/u.test(c); }).join('');
  }


  // TITULO ES COMUN
  function esComun(clave) {
    var minuscula = clave.toLowerCase();
    var nucleo = minuscula.replace(BORDES, '');
    var disfrazada = Array.from(nucleo).map(function (c) { return DISFRAZ[c] || c; }).join('');
    return !!COMUNES[soloLetras(disfrazada)] || !!COMUNES[soloLetras(minuscula)] || !!COMUNES[minuscula] || (minuscula.length > 0 && new Set(Array.from(minuscula)).size === 1);
  }


  // TITULO CUMPLIMIENTO
  function cumplimiento(clave) {
    var letras = Array.from(clave);
    return [
      letras.length >= 8,
      letras.some(function (c) { return c !== c.toLowerCase(); }),
      letras.some(function (c) { return c !== c.toUpperCase(); }),
      letras.some(function (c) { return /\p{Nd}/u.test(c); }),
      letras.some(function (c) { return /[^\p{L}\p{N}\s]/u.test(c); })
    ];
  }


  // TITULO DIBUJAR
  function dibujar(medidor, clave) {
    var cumple = cumplimiento(clave);
    var cumplidos = cumple.filter(Boolean).length;
    var llenas = [0, 1, 1, 2, 3, 4][cumplidos];
    var comun = clave !== '' && esComun(clave);
    if (!clave) llenas = 0;
    else if (comun) llenas = Math.min(llenas, 1);

    var barras = '';
    for (var i = 0; i < 4; i++) {
      var color = i < llenas ? CFG.colores[String(llenas)] : '#30363d';
      barras += "<span style='flex:1; height:4px; border-radius:2px; background:" + color + ";'></span>";
    }
    var detalle;
    if (!clave) {
      detalle = "<p style='color:#8b949e; font-size:12px; margin:4px 0 0;'>" + CFG.ayuda + "</p>";
    } else {
      var puntos = CFG.requisitos.map(function (texto, i) {
        return "<span style='color:" + (cumple[i] ? '#3fb950' : '#8b949e') + "; font-size:12px; margin-right:12px; white-space:nowrap;'>" +
               (cumple[i] ? '✓' : '○') + ' ' + texto + '</span>';
      }).join('');
      var aviso = comun ? "<p style='color:#f85149; font-size:12px; margin:4px 0 0;'>Esa contraseña es demasiado común.</p>" : '';
      detalle = "<div style='margin-top:4px; line-height:1.7;'>" + puntos + '</div>' + aviso;
    }
    var raiz = medidor.shadowRoot || medidor.attachShadow({ mode: 'open' });
    raiz.innerHTML = "<div style='display:flex; gap:4px; margin-top:2px;'>" + barras + '</div>' + detalle;
  }


  // TITULO CAMPO DE
  function campoDe(medidor) {
    var etiqueta = medidor.getAttribute('data-pj-medidor');
    var campos = D.querySelectorAll('input[aria-label]');
    for (var i = 0; i < campos.length; i++) {
      if (campos[i].getAttribute('aria-label') === etiqueta) return campos[i];
    }
    return null;
  }


  // TITULO BARRER
  // Dibuja los medidores que React acaba de crear (todavía sin contenido) con el valor actual de su campo.
  function barrer() {
    var medidores = D.querySelectorAll('[data-pj-medidor]');
    for (var i = 0; i < medidores.length; i++) {
      if (medidores[i].shadowRoot) continue;
      var campo = campoDe(medidores[i]);
      dibujar(medidores[i], campo ? campo.value || '' : '');
    }
  }


  // TITULO AL ESCRIBIR
  function alEscribir(evento) {
    var campo = evento.target;
    if (!campo || !campo.getAttribute) return;
    var etiqueta = campo.getAttribute('aria-label');
    if (!etiqueta) return;
    var medidores = D.querySelectorAll('[data-pj-medidor]');
    for (var i = 0; i < medidores.length; i++) {
      if (medidores[i].getAttribute('data-pj-medidor') === etiqueta) dibujar(medidores[i], campo.value || '');
    }
  }

  // Cada ejecución de la página crea un componente nuevo: se quita el oyente anterior para no acumularlos.
  if (P.__pjMedidorOyente) D.removeEventListener('input', P.__pjMedidorOyente, true);
  P.__pjMedidorOyente = alEscribir;
  D.addEventListener('input', alEscribir, true);

  // Observador: cuando Streamlit recarga y React crea un medidor nuevo (vacío), se dibuja en el siguiente cuadro de animación.
  if (P.__pjMedidorObservador) P.__pjMedidorObservador.disconnect();
  var pendiente = false;
  P.__pjMedidorObservador = new P.MutationObserver(function () {
    if (pendiente) return;
    pendiente = true;
    P.requestAnimationFrame(function () { pendiente = false; barrer(); });
  });
  P.__pjMedidorObservador.observe(D.body, { childList: true, subtree: true });
  barrer();
})();

// -------------------------------------------------------------------------------------------------------
// ----------------------------------------- FIN Piña y Jara medidor .JS ---------------------------------
// -------------------------------------------------------------------------------------------------------

// Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
// Dirección: José Joaquín Prieto #5373 -
// San Miguel - Santiago - Chile
// contacto.pinayjara@gmail.com
// https://www.pinayjara.cl
// Creado, Programado y Diseñado por Piña y Jara
// Transportes y Servicios Ltda.
