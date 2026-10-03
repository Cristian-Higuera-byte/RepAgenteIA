window.onerror = function(msg, src, line){
  var e = document.getElementById('tv-ohlc-vals');
  if (e) e.innerText = 'Error JS: ' + msg + ' (línea ' + line + ')';
};
setTimeout(function(){
  var e = document.getElementById('tv-ohlc-vals');
  if (!window.LightweightCharts && e) e.innerText = 'No cargó lightweight-charts (CDN bloqueado o sin internet)';
}, 4000);
