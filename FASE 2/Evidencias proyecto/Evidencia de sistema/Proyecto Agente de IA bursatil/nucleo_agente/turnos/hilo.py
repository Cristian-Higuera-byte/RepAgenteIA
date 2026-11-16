# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara hilo .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Hilo que corre al agente: traduce sus eventos al estado del turno (fase, texto, herramientas, imágenes…)."""
from __future__ import annotations

import time
from typing import Any

from herramientas import cuota_ia, permisos_plan
from nucleo_agente import contexto
from nucleo_agente.turnos.avisos import _avisar
from nucleo_agente.turnos.imagenes import imagenes_de_resultado
from nucleo_agente.turnos.turno import Turno


# TITULO CORRER

def _correr(turno: Turno, agente: Any) -> None:
    """Cuerpo del hilo de un turno: ejecuta al agente y vuelca sus eventos en el objeto `turno`.

    Recibe el Turno (estado compartido con la interfaz) y el Agente. Fija el usuario en contexto, recorre
    responder_stream() actualizando fase, texto, herramientas, imágenes, banderas de orden/vigilancia y
    tokens; atiende la solicitud de cancelación entre eventos; registra cualquier error en `turno.error`.
    Al final cierra el generador, anota la hora de fin, deja el aviso en la campana (salvo si el usuario
    canceló) y por último marca `terminado` para que la interfaz ya encuentre el aviso.
    """
    # Las herramientas que lo necesiten sabrán a qué usuario pertenece esta consulta.
    contexto.fijar_usuario(turno.usuario_id)   # las herramientas que lo necesiten saben quién pregunta
    gen = agente.responder_stream(turno.prompt)
    try:
        for evento in gen:
            # Cancelación cooperativa: se atiende al llegar el siguiente evento.
            if turno.cancelar_solicitado:
                turno.cancelado = True
                break
            # Cada tipo de evento actualiza la fase visible y el estado del turno.
            if evento.tipo == "razonamiento":
                turno.fase = "Analizando…"
            elif evento.tipo == "texto":
                turno.fase = "Redactando la respuesta…"
                turno.texto += evento.texto
            elif evento.tipo == "herramienta":
                # El usuario no ve qué herramienta se usa: solo una fase genérica (el nombre queda en
                # turno.herramientas por si hace falta depurar, pero la interfaz no lo muestra).
                turno.fase = ("Preparando la propuesta…" if str(evento.texto).startswith("proponer_")
                              else "Consultando los datos…")
                turno.herramientas.append(str(evento.texto))
            elif evento.tipo == "resultado":
                turno.fase = "Procesando los datos…"
                # Se detecta si el agente propuso una orden o una vigilancia para avisar al usuario.
                if evento.texto in ("proponer_orden", "proponer_cierre_posicion"):
                    turno.hubo_orden = True
                elif evento.texto == "proponer_vigilancia" and "VIGILANCIA_PENDIENTE" in str((evento.datos or {}).get("resultado", "")):
                    turno.hubo_vigilancia = True
                # Las imágenes guardadas en disco por la herramienta se acumulan sin repetir.
                for ruta in imagenes_de_resultado((evento.datos or {}).get("resultado")):
                    if ruta not in turno.imagenes:
                        turno.imagenes.append(ruta)
            elif evento.tipo == "fin":
                # Al terminar se guardan los tokens consumidos y el perfil usado (para el pie del turno).
                d = evento.datos or {}
                turno.tokens_entrada = d.get("tokens_entrada", "?")
                turno.tokens_salida = d.get("tokens_salida", "?")
                turno.perfil = d.get("perfil", "?")
    except Exception as e:  # noqa: BLE001 - el error se muestra en el chat, no se pierde en el hilo
        if not turno.cancelar_solicitado:   # si el usuario ya lo había detenido, el fallo no importa
            if isinstance(e, (cuota_ia.ErrorCuota, permisos_plan.ErrorPlan)):   # cuota agotada o función fuera del plan: el mensaje ya explica qué pasó
                turno.error = str(e)
            else:
                motivo = "Error del modelo" if type(e).__name__ == "ErrorLLM" else "Error al ejecutar el agente"
                turno.error = f"{motivo}: {e}"
    finally:
        try:
            gen.close()   # si se detuvo a medias, el agente descarta ese turno incompleto de su historial
        except Exception:  # noqa: BLE001
            pass
        turno.t_fin = time.time()
        try:
            turno.cuota = cuota_ia.texto_uso()     # cuánto lleva gastado el usuario este mes, para el pie del mensaje
        except Exception:  # noqa: BLE001
            pass
        try:
            if not turno.cancelado:   # lo detuvo el propio usuario: no hace falta avisarle
                _avisar(turno)
        finally:
            turno.terminado = True   # al final: así la interfaz ya encuentra el aviso creado


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- FIN Piña y Jara hilo .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
