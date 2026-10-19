(function(){
  var P = window.parent, D, H;
  try { D = P.document; H = D.documentElement; } catch(e) { return; }
  // Un solo oyente (en fase de captura): el clic en la pestaña alterna la clase
  // en <html> y NO llega a Streamlit, así la lista se oculta/muestra sin recargar.
  if (P.__pjWlFn) D.removeEventListener('click', P.__pjWlFn, true);
  P.__pjWlFn = function(e){
    if (!(e.target && e.target.closest)) return;
    if (!e.target.closest('.st-key-wl_toggle button')) return;
    e.stopPropagation(); e.preventDefault();
    H.classList.toggle('pj-wl-oculto');
  };
  D.addEventListener('click', P.__pjWlFn, true);
})();
