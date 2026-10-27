"""Diagnóstico de la memoria en Supabase, paso a paso.

Ejecutar desde la raíz del proyecto:   python probar_memoria.py

No necesita llamar al modelo ni gasta tokens. Usa un usuario de prueba
("diagnostico") y al final borra todo lo que creó.
"""
import base64
import inspect
import json
import os
from pathlib import Path

import config  # noqa: F401  (carga el .env)
from core.memoria import ErrorMemoria, Memoria, TABLA_CHATS, TABLA_DATOS, TABLA_MENSAJES, _obtener_cliente

OK, FALLO = "  OK   ", "  FALLO"
problemas: list[str] = []


def paso(titulo: str) -> None:
    print(f"\n── {titulo}")


def ok(msg: str) -> None:
    print(f"{OK} {msg}")


def fallo(msg: str, pista: str = "") -> None:
    print(f"{FALLO} {msg}")
    if pista:
        print(f"         → {pista}")
    problemas.append(msg)


def tipo_de_clave(clave: str) -> str:
    """Dice qué tipo de clave de Supabase es, sin mostrarla."""
    if clave.startswith("sb_secret_"):
        return "secret (servidor)"
    if clave.startswith("sb_publishable_"):
        return "publishable (pública)"
    try:
        carga = clave.split(".")[1]
        carga += "=" * (-len(carga) % 4)
        rol = json.loads(base64.urlsafe_b64decode(carga)).get("role", "desconocido")
        return {"service_role": "service_role (servidor)", "anon": "anon (pública)"}.get(rol, rol)
    except Exception:  # noqa: BLE001
        return "formato no reconocido"


# ── 1. Credenciales ───────────────────────────────────────────
paso("1. Credenciales en el .env")
url, clave = os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", "")
if url:
    ok(f"SUPABASE_URL definida ({url.split('//')[-1].split('.')[0]}...)")
else:
    fallo("Falta SUPABASE_URL", f"agrégala al .env que está junto a config.py ({config.RAIZ / '.env'})")
if clave:
    tipo = tipo_de_clave(clave)
    ok(f"SUPABASE_KEY definida, tipo: {tipo}")
    if "pública" in tipo:
        print("  AVISO  La clave es pública: con RLS activado (como deja memoria_supabase.sql) no podrá escribir; "
              "usa la service_role / secret en el .env (solo en el servidor)")
else:
    fallo("Falta SUPABASE_KEY", f"agrégala al .env que está junto a config.py ({config.RAIZ / '.env'})")

# ── 2. Cliente ────────────────────────────────────────────────
paso("2. Conexión con Supabase")
cliente = None
try:
    cliente = _obtener_cliente()
    ok("Cliente de Supabase creado")
except ErrorMemoria as e:
    fallo(str(e), "¿está instalada la librería? pip install supabase")

# ── 3. Tablas ─────────────────────────────────────────────────
paso("3. Tablas")
if cliente:
    for tabla in (TABLA_CHATS, TABLA_MENSAJES, TABLA_DATOS):
        try:
            cliente.table(tabla).select("*").limit(1).execute()
            ok(f"{tabla} accesible")
        except Exception as e:  # noqa: BLE001
            texto = str(e)
            if "row-level security" in texto.lower() or "permission denied" in texto.lower():
                pista = "permisos/RLS: la clave no tiene acceso; usa la service_role"
            elif "does not exist" in texto.lower() or "could not find" in texto.lower() or "PGRST205" in texto:
                pista = "la tabla no existe: ejecuta memoria_supabase.sql en el SQL Editor de Supabase"
            else:
                pista = ""
            fallo(f"{tabla}: {texto[:200]}", pista)

# ── 4. Escritura y lectura ────────────────────────────────────
paso("4. Guardar y leer (usuario de prueba 'diagnostico')")
if cliente and not problemas:
    m = Memoria("diagnostico")
    try:
        m.iniciar_chat()
        ok("Conversación creada")
        turno = [{"role": "user", "content": "pregunta de prueba"}, {"role": "assistant", "content": "respuesta de prueba"}]
        m.guardar_turno(turno)
        ok("Turno guardado")
        if m.cargar_historial() == turno:
            ok("Historial leído idéntico a lo guardado")
        else:
            fallo("El historial leído no coincide con lo guardado")
        m.guardar_resumen("resumen de prueba")
        m.guardar_dato("dato_prueba", "valor")
        if m.datos_usuario().get("dato_prueba") == "valor":
            ok("Resumen y dato duradero guardados")
        else:
            fallo("El dato duradero no se leyó de vuelta")
    except ErrorMemoria as e:
        rls = "row-level security" in str(e).lower()
        fallo(str(e)[:300], "la clave no tiene permiso de escritura (RLS): usa la service_role / secret en el .env" if rls else "")
    finally:
        try:
            m.olvidar_todo()
            ok("Datos de prueba borrados")
        except ErrorMemoria as e:
            print(f"  AVISO  No se pudieron borrar los datos de prueba (usuario 'diagnostico'): {e}")
else:
    print("  (se omite: corrige primero los fallos anteriores)")

# ── 5. Integración con el agente ──────────────────────────────
paso("5. Integración en core/agente.py y main.py")
try:
    from core.agente import Agente

    if "usuario_id" in inspect.signature(Agente.__init__).parameters:
        ok("Agente.__init__ acepta usuario_id")
    else:
        fallo("Agente.__init__ no tiene el parámetro usuario_id", "falta el cambio de las líneas 50 a 59 de agente.py")
    if "_guardar_turno" in inspect.getsource(Agente.responder_stream):
        ok("responder_stream guarda el turno al terminar")
    else:
        fallo("responder_stream no llama a _guardar_turno", "falta el cambio de las líneas 83 a 84 de agente.py")
    if hasattr(Agente, "_prompt") and hasattr(Agente, "_guardar_turno"):
        ok("Métodos _prompt y _guardar_turno presentes")
    else:
        fallo("Faltan los métodos _prompt y/o _guardar_turno", "falta el cambio de las líneas 63 a 65 de agente.py")
except Exception as e:  # noqa: BLE001
    fallo(f"No se pudo importar core.agente: {type(e).__name__}: {e}")

main = Path("main.py")
if main.exists():
    if "usuario_id" in main.read_text(encoding="utf-8"):
        ok("main.py crea el agente con usuario_id")
    else:
        fallo("main.py crea el agente SIN usuario_id (la memoria queda desactivada, sin avisar)",
              'cambia Agente() por Agente(usuario_id="local")')
else:
    print("  AVISO  No encuentro main.py en esta carpeta; ejecuta el script desde la raíz del proyecto.")

# ── Resultado ─────────────────────────────────────────────────
print("\n" + "─" * 50)
if problemas:
    print(f"{len(problemas)} problema(s) encontrado(s). Pégame esta salida completa.")
else:
    print("Todo en orden: la memoria y su integración funcionan.")