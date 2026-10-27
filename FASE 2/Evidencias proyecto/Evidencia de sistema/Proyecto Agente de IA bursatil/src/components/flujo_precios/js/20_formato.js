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
   ---------------------------------- INICIO Piña y Jara 20_formato .JS ----------------------------------
   ------------------------------------------------------------------------------------------------------- */

  /** Formatea el número `v` con exactamente `d` decimales y separador de miles (estilo en-US). Devuelve texto. */
  function fmt(v, d){
    return Number(v).toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});
  }
  /**
   * Decide cuántos decimales usar para el elemento `el`: el valor de data-pj-d si existe;
   * si no, 2 cuando |v| supera 100 y 5 en caso contrario. Devuelve un entero.
   */
  function dec(el, v){
    var d = el.getAttribute('data-pj-d');
    return (d !== null && d !== '') ? +d : (Math.abs(v) > 100 ? 2 : 5);
  }
  /** Escribe `txt` en el elemento solo si difiere del actual (evita mutaciones y repintados inútiles). */
  function poner(el, txt){ if (el.textContent !== txt) el.textContent = txt; }
  /** Aplica el color `c` al texto del elemento solo si hay color y es distinto del actual. */
  function color(el, c){ if (c && el.style.color !== c) el.style.color = c; }


/* -------------------------------------------------------------------------------------------------------
   ------------------------------------ FIN Piña y Jara 20_formato .JS -----------------------------------
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
