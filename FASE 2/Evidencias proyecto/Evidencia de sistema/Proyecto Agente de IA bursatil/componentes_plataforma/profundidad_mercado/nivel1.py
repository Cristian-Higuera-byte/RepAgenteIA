# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara nivel1 .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""DOM de nivel 1 para Capital.com: mejor Bid/Ask con su cantidad disponible + cinta de cotizaciones.

Capital.com no publica un libro de órdenes con varios niveles (ni por REST ni por WebSocket); lo único real que
entrega es el mejor precio de compra y de venta con la cantidad disponible en cada uno (`bidQty` / `ofrQty`).
Este módulo arma un componente HTML con su propio script que consulta `GET /dom/<símbolo>` del servidor de datos
cada segundo (el servidor lo alimenta del WebSocket) y pinta:
  - los dos lados (Ask arriba, Bid abajo) con precio y cantidad, y una barra que compara ambas cantidades;
  - el spread;
  - la cinta con las últimas variaciones de precio (hora, bid, ask y flecha de dirección).
Todo es real: no hay volúmenes de muestra."""
from __future__ import annotations

import json

_PLANTILLA = r"""
<style>
  html,body { margin:0; background:transparent; color:#e6edf3;
              font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }
  .n1 { font-size:12px; }
  .cab { display:flex; justify-content:space-between; color:#8b949e; font-size:11px; padding:0 2px 5px; }
  .lado { display:flex; align-items:center; gap:8px; margin-bottom:4px; }
  .barra { flex:1; height:22px; border-radius:4px; position:relative; }
  .barra.ask { background:#1b1420; } .barra.bid { background:#111d17; }
  .barra > i { position:absolute; right:0; top:0; height:22px; border-radius:4px; opacity:.6; }
  .barra.ask > i { background:#da3633; } .barra.bid > i { background:#2ea043; }
  .barra span { position:absolute; left:7px; top:4px; font-family:ui-monospace,Consolas,monospace; font-size:11.5px; }
  .px { min-width:82px; text-align:right; font-family:ui-monospace,Consolas,monospace; font-weight:700; font-size:13px; }
  .px.ask { color:#f85149; } .px.bid { color:#3fb950; }
  .spread { display:flex; justify-content:space-between; align-items:center; background:#151c27;
            border:1px solid #202a37; border-radius:6px; padding:4px 8px; margin:4px 0; color:#8b949e; }
  .spread b { color:#e6edf3; font-family:ui-monospace,Consolas,monospace; }
  .bal { display:flex; height:6px; border-radius:3px; overflow:hidden; margin:6px 0 2px; background:#202a37; }
  .bal i { display:block; height:6px; }
  .balt { display:flex; justify-content:space-between; color:#8b949e; font-size:10.5px; margin-bottom:8px; }
  .tit { color:#8b949e; font-size:11px; margin:6px 2px 4px; }
  table { width:100%; border-collapse:collapse; font-family:ui-monospace,Consolas,monospace; font-size:11.5px; }
  td { padding:2px 4px; border-top:1px solid #1b2431; } td.r { text-align:right; }
  .sube { color:#3fb950; } .baja { color:#f85149; } .nota { color:#8b949e; padding:10px 2px; }
</style>
<div class="n1" id="n1"><div class="nota">Esperando datos…</div></div>
<script>
(function(){
  var API = __API__, SYM = __SYM__, DIG = __DIG__;
  var el = document.getElementById('n1');
  function f(v, d){ return Number(v).toLocaleString('en-US', {minimumFractionDigits:d, maximumFractionDigits:d}); }
  function q(v){ v = Number(v) || 0; return v >= 100 ? f(v, 0) : f(v, 2); }
  function hora(ms){ var d = new Date(ms); return d.toLocaleTimeString('es-CL', {hour12:false}); }
  function pintar(d){
    if (!d || !d.disponible){
      el.innerHTML = '<div class="nota">' + ((d && d.motivo) || 'Sin datos del servidor (¿está servidor_datos.py en marcha?)') + '</div>';
      return;
    }
    var tot = (d.bq || 0) + (d.aq || 0), pa = tot ? (d.aq / tot * 100) : 50, pb = 100 - pa;
    var spr = d.ask - d.bid;
    var h = '<div class="cab"><span>Cantidad</span><span>Precio</span></div>' +
      '<div class="lado"><div class="barra ask"><i style="width:' + pa.toFixed(0) + '%"></i><span>' + q(d.aq) + '</span></div>' +
      '<div class="px ask">' + f(d.ask, DIG) + '</div></div>' +
      '<div class="spread"><span>Spread</span><b>' + f(spr, DIG) + '</b></div>' +
      '<div class="lado"><div class="barra bid"><i style="width:' + pb.toFixed(0) + '%"></i><span>' + q(d.bq) + '</span></div>' +
      '<div class="px bid">' + f(d.bid, DIG) + '</div></div>' +
      '<div class="bal"><i style="width:' + pb.toFixed(1) + '%;background:#2ea043"></i><i style="width:' + pa.toFixed(1) + '%;background:#da3633"></i></div>' +
      '<div class="balt"><span>Compra ' + pb.toFixed(0) + '%</span><span>Venta ' + pa.toFixed(0) + '%</span></div>' +
      '<div class="tit">Cinta (últimas cotizaciones)</div><table>';
    var c = (d.cinta || []).slice(-14).reverse();
    for (var i = 0; i < c.length; i++){
      var prev = c[i + 1], dir = '', cls = '';
      if (prev){ var m = (c[i].b + c[i].a) / 2, mp = (prev.b + prev.a) / 2;
        if (m > mp){ dir = '▲'; cls = 'sube'; } else if (m < mp){ dir = '▼'; cls = 'baja'; } }
      h += '<tr><td>' + hora(c[i].t) + '</td><td class="r ' + cls + '">' + f(c[i].b, DIG) + '</td>' +
           '<td class="r ' + cls + '">' + f(c[i].a, DIG) + '</td><td class="r ' + cls + '">' + dir + '</td></tr>';
    }
    el.innerHTML = h + '</table>';
  }
  function ciclo(){
    fetch(API + '/dom/' + encodeURIComponent(SYM)).then(function(r){ return r.json(); })
      .then(pintar).catch(function(){ pintar(null); });
  }
  ciclo(); setInterval(ciclo, 1000);
})();
</script>
"""


# TITULO HTML NIVEL1

def html_nivel1(api_url: str, simbolo: str, digitos: int) -> str:
    """HTML (con CSS y script) del panel de nivel 1 para `simbolo`, que consulta `api_url` cada segundo."""
    return (_PLANTILLA.replace("__API__", json.dumps(api_url))
            .replace("__SYM__", json.dumps(simbolo))
            .replace("__DIG__", str(int(digitos))))


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara nivel1 .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
