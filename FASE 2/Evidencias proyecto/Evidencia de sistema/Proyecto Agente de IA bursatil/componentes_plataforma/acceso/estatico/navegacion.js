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
   ------------------------------------ INICIO Piña y Jara navegacion .JS --------------------------------
   ------------------------------------------------------------------------------------------------------- */

// [acceso] Navegación sin recargar entre la portada, el inicio de sesión, el registro y «Olvidé mi contraseña», y entre las opciones del menú del usuario (Perfil,
// Configuración, cuentas) una vez iniciada la sesión (Streamlit CCv2). Python le dice qué enlaces atender (`data.prefijos`, y `data.portada` para el enlace `./`).
// Esas pantallas se enlazaban con enlaces normales (`?acceso=entrar`), que recargan toda la página y dejan ver el esqueleto gris de Streamlit mientras vuelve a arrancar.
// Este componente intercepta el clic en esos enlaces, evita la recarga y le avisa a Python (setTriggerValue «destino») a dónde ir; Python cambia la dirección y dibuja la
// pantalla nueva en la misma sesión. Un clic con Ctrl, Mayús o botón medio sigue funcionando como siempre (abre en otra pestaña).

// Mientras se pasa de una pantalla a otra, el contenido se oculta (clase en <html>) y se muestra de una vez cuando la pantalla nueva está completa. Sin esto se veía la portada
// atenuada, luego el formulario a medio dibujar (campos vacíos, esqueletos) y los planes apareciendo de a uno: el «pestañeo».
const CLASE_CAMBIANDO = 'pj-acceso-cambiando'
const CLASE_REVELANDO = 'pj-acceso-revelando'
// Tiempo sin cambios en la pantalla (ms) que se exige antes de mostrarla; tiempo máximo (ms) que puede quedar oculta si algo falla; y tiempo (ms) tras el cual, si Streamlit
// no llegó a ejecutar nada (por ejemplo, un enlace a la misma pantalla), se vuelve a mostrar.
const QUIETUD_MS = 250
const MAXIMO_MS = 6000
const SIN_EJECUCION_MS = 1500

/** Agrega una sola vez las reglas que ocultan y vuelven a mostrar el contenido. */
function instalarEstilo() {
  if (document.getElementById('pj-acceso-estilo')) return
  const estilo = document.createElement('style')
  estilo.id = 'pj-acceso-estilo'
  estilo.textContent = 'html.' + CLASE_CAMBIANDO + ' [data-testid="stMain"] { visibility: hidden !important; }\n' +
    'html.' + CLASE_REVELANDO + ' [data-testid="stMain"] { animation: pj-acceso-aparece .16s ease-out; }\n' +
    '@keyframes pj-acceso-aparece { from { opacity: 0; } to { opacity: 1; } }'
  document.head.appendChild(estilo)
}

/** ¿Está la pantalla nueva realmente lista? Streamlit terminó de ejecutar, no quedan elementos de la pantalla anterior ni esqueletos, y los campos ya tienen su `input`
 *  (se cargan por separado y, mientras llegan, se ve solo la etiqueta). */
function pantallaLista(app) {
  if (app && app.getAttribute('data-test-script-state') === 'running') return false
  if (document.querySelector('[data-stale="true"], [data-testid="stSkeleton"], [class*="Skeleton"]')) return false
  const campos = document.querySelectorAll('[data-testid="stTextInput"], [data-testid="stSelectbox"], [data-testid="stTextArea"]')
  for (let i = 0; i < campos.length; i++) {
    if (!campos[i].querySelector('input, textarea')) return false
  }
  return true
}

/** Oculta el contenido y lo vuelve a mostrar cuando la pantalla nueva está lista y quieta (o a los 6 s, por si algo falla). */
function ocultarHastaTerminar() {
  const raiz = document.documentElement
  const app = document.querySelector('[data-testid="stApp"]')
  const direccionInicial = location.search
  const inicio = Date.now()
  let ultimoCambio = Date.now()
  let corrio = false
  instalarEstilo()
  raiz.classList.remove(CLASE_REVELANDO)
  raiz.classList.add(CLASE_CAMBIANDO)
  if (raiz.__pjCambiando) { clearInterval(raiz.__pjCambiando.reloj); raiz.__pjCambiando.observador.disconnect() }
  // Cada vez que cambia algo en la pantalla se reinicia la cuenta de «quietud».
  const observador = new MutationObserver(function () { ultimoCambio = Date.now() })
  observador.observe(document.body, { childList: true, subtree: true, attributes: true })
  function terminar() {
    clearInterval(reloj)
    observador.disconnect()
    raiz.__pjCambiando = null
    raiz.classList.add(CLASE_REVELANDO)
    raiz.classList.remove(CLASE_CAMBIANDO)
    setTimeout(function () { raiz.classList.remove(CLASE_REVELANDO) }, 400)
  }
  const reloj = setInterval(function () {
    if (app && app.getAttribute('data-test-script-state') === 'running') corrio = true
    const cambio = corrio || location.search !== direccionInicial
    const quieta = Date.now() - ultimoCambio >= QUIETUD_MS
    const transcurrido = Date.now() - inicio
    if ((cambio && transcurrido > 150 && quieta && pantallaLista(app)) || (!cambio && transcurrido > SIN_EJECUCION_MS) || transcurrido > MAXIMO_MS) terminar()
  }, 40)
  raiz.__pjCambiando = { reloj: reloj, observador: observador }
}

/** ¿Es un enlace interno que se abre en la misma pestaña y empieza con alguno de los prefijos indicados (o es la portada `./`, si se permite)? */
function esEnlaceInterno(enlace, prefijos, portada) {
  const destino = enlace.getAttribute('href') || ''
  if (enlace.target && enlace.target !== '_self') return false
  if (portada && destino === './') return true
  return prefijos.some(function (prefijo) { return destino.indexOf(prefijo) === 0 })
}

export default function (component) {
  const { setTriggerValue, data } = component
  const prefijos = (data && data.prefijos) || ['?acceso=']
  const portada = !data || data.portada !== false
  const ocultar = portada

  /** Al pulsar un enlace de acceso: cancela la recarga y entrega a Python la dirección de destino. */
  function alPulsar(evento) {
    if (evento.defaultPrevented || evento.button !== 0 || evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) return
    const enlace = evento.target && evento.target.closest ? evento.target.closest('a') : null
    if (!enlace || !esEnlaceInterno(enlace, prefijos, portada)) return
    evento.preventDefault()
    if (ocultar) ocultarHastaTerminar()   // solo en las pantallas de acceso; el menú de la aplicación ya tiene su propio aviso de carga
    setTriggerValue('destino', enlace.getAttribute('href'))
  }

  document.addEventListener('click', alPulsar, true)
  return function limpiar() {
    document.removeEventListener('click', alPulsar, true)
  }
}

/* -------------------------------------------------------------------------------------------------------
   ------------------------------------- FIN Piña y Jara navegacion .JS ----------------------------------
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
