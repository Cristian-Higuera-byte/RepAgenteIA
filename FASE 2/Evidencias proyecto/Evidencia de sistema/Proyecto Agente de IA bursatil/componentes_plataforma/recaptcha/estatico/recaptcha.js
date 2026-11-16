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
   ------------------------------------ INICIO Piña y Jara recaptcha .JS ---------------------------------
   ------------------------------------------------------------------------------------------------------- */

// [recaptcha] Componente de reCAPTCHA de Google para un formulario de la plataforma (Streamlit CCv2).
// Recibe en `data`: v3 (clave del sitio de v3), v2 (clave del sitio de v2), accion (nombre del formulario), pedirV2 (si hay que mostrar el casillero), conservarV2 (si el casillero
// marcado no se reinicia tras un envío) y nonce (sube cada vez que el servidor ya usó el token, para pedir uno nuevo). Devuelve a Python, con setStateValue, `v3` (token invisible) y `v2` (token del casillero).

/** Carga una sola vez por página la librería de Google con la clave de v3 y devuelve una promesa con el objeto grecaptcha, ya listo para usarse. */
function cargarLibreria(claveV3) {
  if (window.__pjRecaptchaPromesa) return window.__pjRecaptchaPromesa
  window.__pjRecaptchaPromesa = new Promise(function (resolver, rechazar) {
    const etiqueta = document.createElement('script')
    etiqueta.src = 'https://www.google.com/recaptcha/api.js?render=' + encodeURIComponent(claveV3)
    etiqueta.async = true
    etiqueta.onload = function () { window.grecaptcha.ready(function () { resolver(window.grecaptcha) }) }
    etiqueta.onerror = function () { window.__pjRecaptchaPromesa = null; rechazar(new Error('No se pudo cargar reCAPTCHA')) }
    document.head.appendChild(etiqueta)
  })
  return window.__pjRecaptchaPromesa
}

export default function (component) {
  const { data, parentElement, setStateValue } = component
  const cfg = data || {}
  const raiz = parentElement
  // Si el casillero debe quedar marcado (por ejemplo, mientras el botón de envío está bloqueado). Se guarda en el elemento y se lee AL MOMENTO de reiniciar, porque un clic
  // programa el reinicio antes de que el servidor repita la página con este dato ya actualizado.
  raiz.__pjConservar = !!cfg.conservarV2
  const contenedorV2 = raiz.querySelector('.pj-rc-v2')

  /** Pide a Google un token de v3 para la acción de este formulario y se lo entrega a Python; si falla entrega vacío, y el servidor pide entonces el casillero. */
  async function renovarV3() {
    try {
      const g = await cargarLibreria(cfg.v3)
      const token = await g.execute(cfg.v3, { action: cfg.accion })
      setStateValue('v3', token)
    } catch (error) {
      setStateValue('v3', '')
    }
  }

  /** Tras un envío, el token del casillero ya se usó (vale una sola vez): se reinicia el casillero y se vacía su token. Si no hay casillero a la vista, no hace nada. */
  async function reiniciarV2() {
    if (!cfg.pedirV2 || raiz.__pjConservar || raiz.__pjV2 === undefined) return
    try {
      const g = await cargarLibreria(cfg.v3)
      g.reset(raiz.__pjV2)
      setStateValue('v2', '')
    } catch (error) { /* sin casillero que reiniciar */ }
  }

  /** Muestra (o esconde) el casillero «No soy un robot» de v2; lo dibuja una sola vez y, si el servidor ya usó el token, lo reinicia. */
  async function actualizarV2() {
    if (!contenedorV2) return
    contenedorV2.style.display = cfg.pedirV2 ? 'flex' : 'none'
    if (!cfg.pedirV2) return
    try {
      const g = await cargarLibreria(cfg.v3)
      if (raiz.__pjV2 === undefined) {
        raiz.__pjV2 = g.render(contenedorV2, {
          sitekey: cfg.v2,
          theme: 'dark',
          callback: function (token) { setStateValue('v2', token) },
          'expired-callback': function () { setStateValue('v2', '') },
          'error-callback': function () { setStateValue('v2', '') }
        })
      } else if (!cfg.conservarV2 && raiz.__pjNonceV2 !== cfg.nonce) {
        g.reset(raiz.__pjV2)
        setStateValue('v2', '')
      }
      raiz.__pjNonceV2 = cfg.nonce
    } catch (error) {
      contenedorV2.textContent = 'No se pudo cargar la verificación. Recarga la página e inténtalo de nuevo.'
    }
  }

  // Token nuevo al montar, cuando el servidor ya usó el anterior (cambia el nonce) y cada 100 s (un token vale 2 minutos y se usa una sola vez).
  if (raiz.__pjNonceV3 !== cfg.nonce) {
    raiz.__pjNonceV3 = cfg.nonce
    renovarV3()
  }
  actualizarV2()
  // Hora del último botón pulsado: la renovación periódica espera 30 s tras un clic, porque entregar un token nuevo en una pantalla sin formulario hace que Streamlit
  // repita la página y CORTARÍA una acción larga en curso (por ejemplo «Probar conexión», que tarda varios segundos).
  let ultimoClic = 0
  const temporizador = setInterval(function () { if (Date.now() - ultimoClic > 30000) renovarV3() }, 100000)
  // Tras pulsar un botón se pide otro token: el envío ya gastó el actual y la persona puede intentarlo de nuevo sin recargar. Con `conservarV2` (pantallas con varios botones seguidos,
  // donde la verificación sigue valiendo) no se pide ni se reinicia nada: el token nuevo repetiría la página en pleno envío y cortaría la acción.
  function alPulsar(evento) {
    // Solo los botones de Streamlit (enviar, probar...), no el ojito de «mostrar contraseña»: ese no debe reiniciar el casillero.
    if (evento.target && evento.target.closest && evento.target.closest('button[data-testid^="stBaseButton"]')) {
      ultimoClic = Date.now()
      if (!cfg.conservarV2) { setTimeout(renovarV3, 2500); setTimeout(reiniciarV2, 2500) }
    }
  }
  document.addEventListener('click', alPulsar, true)

  return function limpiar() {
    clearInterval(temporizador)
    document.removeEventListener('click', alPulsar, true)
  }
}

/* -------------------------------------------------------------------------------------------------------
   ------------------------------------- FIN Piña y Jara recaptcha .JS -----------------------------------
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
