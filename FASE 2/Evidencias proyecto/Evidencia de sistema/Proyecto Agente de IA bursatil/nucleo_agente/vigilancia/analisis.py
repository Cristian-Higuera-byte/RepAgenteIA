# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara analisis .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Agente del análisis (sin herramientas de ejecución) y mensaje que se le envía en cada chequeo.

`fabrica_agente` se puede sustituir (las pruebas inyectan un agente falso): se lee desde este módulo en cada chequeo."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from nucleo_agente.vigilancia import configuracion
from nucleo_agente.vigilancia.configuracion import HERRAMIENTAS_EXCLUIDAS


# TITULO REGISTRO SIN EJECUCION

class _RegistroSinEjecucion:
    """Registro de herramientas para el análisis automático: el de siempre MENOS las que proponen o
    programan órdenes. Así el modelo no puede ejecutar nada por su cuenta; solo analiza y decide.

    Imita la interfaz del registro real (nombres, esquemas, ejecutar) para poder pasarse al Agente."""

    # TITULO INIT

    def __init__(self, base: Any, excluidas: frozenset = HERRAMIENTAS_EXCLUIDAS) -> None:
        """Guarda el registro base y el conjunto de nombres de herramientas que deben ocultarse."""
        self._base, self._excluidas = base, excluidas

    # TITULO NOMBRES

    def nombres(self) -> list[str]:
        """Devuelve los nombres de herramientas del registro base sin las excluidas."""
        return [n for n in self._base.nombres() if n not in self._excluidas]

    # TITULO ESQUEMAS

    def esquemas(self) -> list[dict[str, Any]]:
        """Devuelve los esquemas de herramientas que se envían al modelo, sin los de las excluidas."""
        return [e for e in self._base.esquemas() if e.get("function", {}).get("name") not in self._excluidas]

    # TITULO EJECUTAR

    def ejecutar(self, nombre: str, argumentos: dict[str, Any]) -> str:
        """Ejecuta una herramienta del registro base; si está excluida devuelve un JSON de error sin ejecutarla
        (defensa extra por si el modelo la invoca aunque no la vea)."""
        if nombre in self._excluidas:
            return json.dumps({"error": "Esa herramienta no está disponible en el análisis automático."}, ensure_ascii=False)
        return self._base.ejecutar(nombre, argumentos)


# TITULO FABRICA AGENTE REAL

def _fabrica_agente_real() -> Any:
    """Crea el agente real del análisis: perfil de vigilancia, registro sin herramientas de ejecución y sin usuario.

    Los imports son tardíos para evitar ciclos y no cargar el modelo hasta que haga falta."""
    from nucleo_agente.agente import Agente  # import tardío: evita ciclos y no carga el modelo si no hace falta
    from herramientas_agente.base import REGISTRO
    # usuario_id=None: sin memoria persistente; cada chequeo es una conversación nueva y barata.
    return Agente(perfil=configuracion.PERFIL_VIGILANCIA, registro=_RegistroSinEjecucion(REGISTRO), usuario_id=None)


# Se puede sustituir (las pruebas inyectan un agente falso).
fabrica_agente: Callable[[], Any] = _fabrica_agente_real


# TITULO MENSAJE ANALISIS

def _mensaje_analisis(v: dict[str, Any], posiciones: list[Any]) -> str:
    """Construye el mensaje que se envía al agente en cada chequeo.

    Recibe la vigilancia y sus posiciones abiertas. Incluye activo, instrucción del usuario, avance de
    operaciones, riesgo fijado, posiciones con su resultado, permiso de cierre, el último resumen y las
    instrucciones para responder con el bloque ```decision``` que lee parsear_decision."""
    # Lista de posiciones propias abiertas, una línea por ticket.
    if posiciones:
        filas = []
        for p in posiciones:
            tipo = "compra" if p.type == mt5.POSITION_TYPE_BUY else "venta"
            filas.append(
                f"- ticket {p.ticket}: {tipo} {p.volume:g} lotes, abierta a {p.price_open}, ahora {p.price_current}, "
                f"SL {p.sl or 'sin SL'}, TP {p.tp or 'sin TP'}, resultado {p.profit:+.2f}"
            )
        abiertas = "\n".join(filas)
    else:
        abiertas = "- ninguna"
    puede_cerrar = "SÍ, solo las listadas arriba" if v.get("permite_cerrar") else "NO"
    return f"""MODO VIGILANCIA AUTOMÁTICA (el usuario te autorizó a operar solo este activo).

Activo: {v['simbolo']}
Lo que pidió el usuario: {v.get('instruccion') or '(vigilar el activo y operar en el mejor momento)'}
Hora local: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Chequeo número {int(v.get('chequeos') or 0)} (cada {v['intervalo_min']} min). Aperturas hechas: {v.get('operaciones') or 0} de {v['max_operaciones']}.
Riesgo por operación fijado por el sistema: {v['riesgo_pct']}% del equity (el lote lo calcula el sistema).
Posiciones abiertas por esta vigilancia:
{abiertas}
¿Puedes cerrarlas por tu análisis?: {puede_cerrar}
Último resumen tuyo: {v.get('ultimo_resumen') or '(primer chequeo)'}

Qué hacer:
1. Analiza {v['simbolo']} con las herramientas de datos (precio actual, velas en varios marcos de tiempo, niveles clave, tendencia, noticias próximas de alto impacto, etc.).
2. Decide UNA acción: esperar, abrir o cerrar. Esperar es una decisión válida y a menudo la mejor: abre solo si hay una oportunidad clara, con un stop loss lógico (obligatorio) y una relación beneficio/riesgo razonable. No abras si ya hay una posición abierta.
3. No existen herramientas para ejecutar: el sistema ejecutará tu decisión por ti, dentro de sus límites de riesgo.
4. Explica tu análisis en pocas líneas y termina SIEMPRE con este bloque (JSON válido, nada después):
```decision
{{"accion": "esperar", "resumen": "una frase para el historial"}}
```
Para abrir: {{"accion": "abrir", "lado": "compra" o "venta", "stop_loss": precio, "take_profit": precio, "resumen": "..."}}
Para cerrar una de las posiciones listadas: {{"accion": "cerrar", "ticket": el ticket tal como aparece en la lista (entre comillas si es texto), "resumen": "..."}}"""


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara analisis .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
