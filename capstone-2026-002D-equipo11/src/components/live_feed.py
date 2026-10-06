"""
live_feed.py
------------
Feed de precios EN VIVO del navegador (streaming por SSE desde servidor_datos.py).

Cómo funciona:
  - Los componentes marcan sus números con atributos `data-pj-*`
    (p. ej. <span data-pj-s="EURUSD..." data-pj-f="px">1.12010</span>).
  - `inyectar_feed()` mete un iframe invisible con un script que:
      1) junta todos los símbolos marcados en la página,
      2) abre UNA conexión SSE a `/stream?s=...` del servidor de datos,
      3) en cada tick reescribe SOLO el texto/color de esos elementos en el DOM
         (sin reejecutar Streamlit → sin parpadeo ni colisiones de deltas),
      4) reenvía el tick por BroadcastChannel('pj-ticks') para que el gráfico
         mueva la vela actual al instante.
  - Si Streamlit redibuja un bloque (rerun de un fragmento), un MutationObserver
    repinta enseguida con el último tick conocido.

Atributos soportados:
  data-pj-s     símbolo tal como se pide al servidor (con o sin '...')
  data-pj-f     campo: px | bid | ask | side | var | spr
  data-pj-d     decimales (por defecto: 2 si el precio > 100, si no 5)
  data-pj-pre   prefijo (p. ej. "$")
  data-pj-side  BUY | SELL  (para data-pj-f="side": ask o bid)
  data-pj-pip   tamaño del pip (para data-pj-f="spr")
  data-pj-flash "1" → colorea verde/rojo según suba/baje el último tick
  data-pj-up / data-pj-dn  colores de variación positiva/negativa
  data-pj-acc   equity | profit   (datos de la cuenta, sin data-pj-s)
                con data-pj-suf (sufijo) y data-pj-zero="1" (mostrar +0.00 en vez de vacío)
  data-pj-pos   ticket de una posición → su P/G neto (profit + swap)
  data-pj-spark símbolo de un mini-gráfico (<img> dentro); data-pj-vals = semilla
                "v1,v2,..." → se redibuja en el navegador con cada tick

Si el servidor de datos NO está corriendo, no se inyecta nada y los fragmentos
`run_every` siguen refrescando como antes (intervalo rápido).
"""
import json
import os
import urllib.request

import streamlit as st
import streamlit.components.v1 as components

API_URL = os.environ.get("MT5_API_URL", "http://localhost:8000")


@st.cache_data(ttl=15, show_spinner=False)
def feed_activo() -> bool:
    """True si servidor_datos.py responde (se revisa como máximo cada 15 s)."""
    try:
        with urllib.request.urlopen(API_URL + "/salud", timeout=0.4) as r:
            return r.status == 200
    except Exception:
        return False


def intervalo(rapido: str = "2s", lento: str | None = None) -> str | None:
    """Intervalo de los fragmentos `run_every`. Con feed en vivo, por defecto
    NINGUNO (None): el feed ya pinta todo y cada recarga de Streamlit atenúa el
    bloque un instante (parpadeo). Los fragmentos se siguen recargando al
    interactuar (✕, +, botones). Sin feed, el refresco rápido de siempre."""
    return lento if feed_activo() else rapido


_JS = r"""
<script>
(function(){
  var API = __API__;
  var P = window.parent, D;
  try { D = P.document; } catch(e) { return; }   // sin acceso al DOM padre: no hay feed

  var bc = ('BroadcastChannel' in window) ? new BroadcastChannel('pj-ticks') : null;
  var es = null, actuales = '', ultimo = {}, cuenta = null, pendiente = false;
  var spark = {}, sparkT = {}, sembrado = {};
  // Un punto nuevo por cada tick (el motor lee cada 250 ms y solo envía si el
  // precio cambió). 120 puntos ≈ 30 s de ticks en un símbolo muy activo.
  var SPARK_MAX = 120, SPARK_PASO = 250;

  // --- Mini-gráficos (sparklines) -----------------------------------------
  function sembrarSparks(){
    D.querySelectorAll('[data-pj-spark]').forEach(function(el){
      var s = el.getAttribute('data-pj-spark');
      var v = (el.getAttribute('data-pj-vals') || '').split(',').map(parseFloat)
                .filter(function(x){ return isFinite(x); });
      // La semilla del servidor (histórico M1) se usa UNA vez por símbolo: los
      // ticks ya recibidos se agregan detrás. Si aún no trae histórico real
      // (< 5 puntos, símbolo recién agregado) se reintenta en el próximo refresco.
      if (sembrado[s] || !v.length) return;
      if (v.length >= 5){
        spark[s] = v.concat(spark[s] || []).slice(-SPARK_MAX);
        sembrado[s] = true;
      } else if (!spark[s]) {
        spark[s] = v.slice();
      }
      sparkT[s] = Date.now();
    });
  }
  function empujarSpark(s, precio){
    if (!precio) return;
    var buf = spark[s] || (spark[s] = []);
    var ahora = Date.now();
    if (!buf.length || ahora - (sparkT[s] || 0) >= SPARK_PASO){
      buf.push(precio); sparkT[s] = ahora;
      if (buf.length > SPARK_MAX) buf.splice(0, buf.length - SPARK_MAX);
    } else {
      buf[buf.length - 1] = precio;          // dentro del paso: mueve el último punto
    }
  }
  function svgSpark(s, vals, col){
    var w = 92, h = 40, pad = 3;
    if (vals.length < 2) vals = [vals[0], vals[0]];
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), rng = (hi - lo) || 1;
    var n = vals.length, pts = [];
    for (var i = 0; i < n; i++){
      var x = i * (w / (n - 1)), y = h - pad - ((vals[i] - lo) / rng) * (h - 2 * pad);
      pts.push(x.toFixed(1) + ',' + y.toFixed(1));
    }
    var linea = pts.join(' '), gid = 'pjs' + s.replace(/\W/g, '');
    return "<svg xmlns='http://www.w3.org/2000/svg' width='" + w + "' height='" + h +
      "' viewBox='0 0 " + w + " " + h + "' preserveAspectRatio='none'>" +
      "<defs><linearGradient id='" + gid + "' x1='0' y1='0' x2='0' y2='1'>" +
      "<stop offset='0' stop-color='" + col + "' stop-opacity='0.30'/>" +
      "<stop offset='1' stop-color='" + col + "' stop-opacity='0'/></linearGradient></defs>" +
      "<polygon points='0," + h + " " + linea + " " + w + "," + h + "' fill='url(#" + gid + ")'/>" +
      "<polyline points='" + linea + "' fill='none' stroke='" + col + "' stroke-width='1.6' " +
      "stroke-linejoin='round' stroke-linecap='round'/></svg>";
  }
  function pintarSpark(el, s){
    // SVG EN LÍNEA (no <img> data-URI): se dibuja en el mismo frame, sin
    // decodificar imagen → al reemplazar el dibujo del servidor no hay parpadeo.
    var buf = spark[s];
    if (!buf || !buf.length) return;
    var t = ultimo[s];
    var col = (t && t.ch < 0) ? '#f85149' : '#3fb950';
    var clave = buf.length + '|' + buf[buf.length - 1] + '|' + buf[0] + '|' + col;
    if (el.getAttribute('data-pj-k') === clave) return;
    el.setAttribute('data-pj-k', clave);
    el.innerHTML = svgSpark(s, buf, col);
  }

  function fmt(v, d){
    return Number(v).toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});
  }
  function dec(el, v){
    var d = el.getAttribute('data-pj-d');
    return (d !== null && d !== '') ? +d : (Math.abs(v) > 100 ? 2 : 5);
  }
  function poner(el, txt){ if (el.textContent !== txt) el.textContent = txt; }
  function color(el, c){ if (c && el.style.color !== c) el.style.color = c; }

  function pintarElem(el, t){
    var f = el.getAttribute('data-pj-f') || 'px';
    var pre = el.getAttribute('data-pj-pre') || '';
    var v;
    if (f === 'var'){
      var d = dec(el, t.l);
      var up = el.getAttribute('data-pj-up') || '#3fb950';
      var dn = el.getAttribute('data-pj-dn') || '#f85149';
      poner(el, (t.ch >= 0 ? '+' : '') + fmt(t.ch, d) + ' (' + (t.pct >= 0 ? '+' : '') + t.pct.toFixed(2) + '%)');
      color(el, t.ch >= 0 ? up : dn);
      return;
    }
    if (f === 'spr'){
      var pip = parseFloat(el.getAttribute('data-pj-pip')) || 0;
      if (!pip) return;
      var s = (t.a - t.b) / pip;
      poner(el, s < 100 ? fmt(s, 1) : fmt(s, 0));
      return;
    }
    if (f === 'bid') v = t.b;
    else if (f === 'ask') v = t.a;
    else if (f === 'side') v = (el.getAttribute('data-pj-side') === 'SELL') ? t.b : t.a;
    else v = t.l;
    if (!v) return;
    poner(el, pre + fmt(v, dec(el, v)));
    if (el.getAttribute('data-pj-flash') === '1'){
      var prev = parseFloat(el.getAttribute('data-pj-prev'));
      if (!isNaN(prev) && v !== prev) color(el, v > prev ? '#3fb950' : '#f85149');
      el.setAttribute('data-pj-prev', String(v));
    }
  }

  function pintarCuenta(){
    if (!cuenta) return;
    D.querySelectorAll('[data-pj-acc]').forEach(function(el){
      var f = el.getAttribute('data-pj-acc');
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
  }

  function pintar(solo){
    D.querySelectorAll('[data-pj-s]').forEach(function(el){
      var s = el.getAttribute('data-pj-s');
      if (solo && !(s in solo)) return;
      var t = ultimo[s];
      if (t) pintarElem(el, t);
    });
    D.querySelectorAll('[data-pj-spark]').forEach(function(el){
      var s = el.getAttribute('data-pj-spark');
      if (!solo || (s in solo)) pintarSpark(el, s);
    });
    pintarCuenta();
  }

  function simbolos(){
    var set = {};
    D.querySelectorAll('[data-pj-s]').forEach(function(el){ set[el.getAttribute('data-pj-s')] = 1; });
    return Object.keys(set).sort().join(',');
  }

  function conectar(lista){
    if (es) es.close();
    actuales = lista;
    es = new EventSource(API + '/stream?s=' + encodeURIComponent(lista));
    es.onmessage = function(ev){
      var m;
      try { m = JSON.parse(ev.data); } catch(e) { return; }
      sembrarSparks();
      for (var k in m.t){ ultimo[k] = m.t[k]; empujarSpark(k, m.t[k].l); }
      if (m.acc) cuenta = m.acc;
      pintar(m.t);
      if (bc) bc.postMessage(m);
    };
  }

  // Revisa si cambió el conjunto de símbolos (cambio de vista/activo) y repinta
  // lo que Streamlit acaba de redibujar con valores viejos.
  function revisar(){
    pendiente = false;
    sembrarSparks();                   // la tarjeta redibujada puede traer semilla nueva
    var lista = simbolos();
    if (lista && lista !== actuales) conectar(lista);
    pintar(null);
  }
  // El callback del MutationObserver corre ANTES de que el navegador pinte el
  // cambio: repintar aquí mismo hace que nunca se vea el valor/mini-gráfico viejo
  // que trae el refresco de respaldo de Streamlit (antes se veía ~120 ms → parpadeo).
  // La reconexión por cambio de símbolos sí va con retardo (no es urgente).
  new MutationObserver(function(){
    sembrarSparks();
    pintar(null);
    if (pendiente) return;
    pendiente = true;
    setTimeout(revisar, 120);
  }).observe(D.body, {childList: true, subtree: true});

  revisar();
  window.addEventListener('unload', function(){ if (es) es.close(); });
})();
</script>
"""

def inyectar_feed():
    """Inserta (una vez por página) el script del feed en vivo. No ocupa espacio."""
    if not feed_activo():
        return
    # OJO: el CSS que oculta este contenedor (.st-key-pj_feed) va en el bloque de
    # estilos global de app.py. Un st.markdown(_CSS) propio aquí agregaba un
    # elemento más al flujo y Streamlit le sumaba ~1rem de separación (hueco
    # visible bajo la barra superior).
    with st.container(key="pj_feed"):
        components.html(_JS.replace("__API__", json.dumps(API_URL)), height=0)


def attrs(simbolo: str, campo: str = "px", **extra) -> str:
    """Atributos data-pj-* listos para meter en una etiqueta HTML."""
    partes = [f'data-pj-s="{simbolo}"', f'data-pj-f="{campo}"']
    for k, v in extra.items():
        partes.append(f'data-pj-{k}="{v}"')
    return " ".join(partes)