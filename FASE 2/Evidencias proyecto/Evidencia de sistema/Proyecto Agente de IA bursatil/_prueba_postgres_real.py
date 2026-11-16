# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara _prueba_postgres_real .PY --------------------------
# -------------------------------------------------------------------------------------------------------

"""
_prueba_postgres_real.py
------------------------
Prueba el adaptador `herramientas/base_datos_postgres.py` contra un PostgreSQL de verdad (el del hosting).

Qué hace: crea un usuario de prueba, ejercita cada operación (insert, select con count, update, upsert, in_, order, limit, columnas JSONB,
las funciones billetera_mover y rpc) y al terminar BORRA todo lo que creó (el usuario de prueba y, en cascada, sus datos).
No toca ningún dato existente: el correo de prueba es prueba-adaptador@example.invalid.

Requisitos: las 23 tablas creadas, `psycopg2-binary` instalado y las 5 variables POSTGRES_* en el .env.
Uso (desde la carpeta del proyecto, con el entorno activo):  python _prueba_postgres_real.py
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)
os.environ["BASE_DATOS"] = "postgres"

from herramientas import base_datos

CORREO_PRUEBA = "prueba-adaptador@example.invalid"
fallos: list = []


# TITULO COMPROBAR

def comprobar(nombre: str, obtenido, esperado) -> None:
    """Compara lo obtenido con lo esperado y lo informa; anota el fallo si no coinciden."""
    estado = "ok" if obtenido == esperado else "FALLA"
    if estado == "FALLA":
        fallos.append(nombre)
    print(f"  [{estado}] {nombre}" + ("" if estado == "ok" else f"  (esperado {esperado!r}, obtenido {obtenido!r})"))


# TITULO LIMPIAR

def limpiar(cliente) -> None:
    """Borra el usuario de prueba; sus datos relacionados se borran en cascada."""
    cliente.table("usuarios").delete().eq("email", CORREO_PRUEBA).execute()


# TITULO PRUEBAS

def probar(cliente) -> None:
    """Ejercita cada operación del adaptador contra la base de datos real y comprueba los resultados."""
    limpiar(cliente)
    print("usuarios")
    creado = cliente.table("usuarios").insert({"nombre": "Prueba adaptador", "email": CORREO_PRUEBA, "password_hash": "x"}).execute().data[0]
    usuario_id = creado["id"]
    comprobar("insert devuelve la fila con id numérico", isinstance(usuario_id, int), True)
    comprobar("la fecha llega como texto ISO", isinstance(creado["creado_en"], str) and "T" in creado["creado_en"], True)

    respuesta = cliente.table("usuarios").select("id, nombre", count="exact").eq("email", CORREO_PRUEBA).execute()
    comprobar("select con count exacto", (len(respuesta.data), respuesta.count), (1, 1))
    comprobar("select de columnas elegidas", sorted(respuesta.data[0].keys()), ["id", "nombre"])

    modificado = cliente.table("usuarios").update({"nombre": "Nombre nuevo"}).eq("id", usuario_id).execute().data
    comprobar("update devuelve la fila modificada", modificado[0]["nombre"], "Nombre nuevo")

    try:
        cliente.table("usuarios").insert({"nombre": "Otra", "email": CORREO_PRUEBA, "password_hash": "y"}).execute()
        comprobar("correo repetido debe fallar", "no fallo", "duplicate")
    except Exception as error:  # noqa: BLE001 - se revisa el texto del error, igual que hace el resto del código
        comprobar("el error de correo repetido contiene 'duplicate'", "duplicate" in str(error).lower(), True)

    sin_resultado = cliente.table("usuarios").select("id").in_("id", [-1, -2]).execute().data
    comprobar("in_ sin coincidencias", sin_resultado, [])
    con_resultado = cliente.table("usuarios").select("id").in_("id", [usuario_id, -1]).execute().data
    comprobar("in_ con coincidencia", [fila["id"] for fila in con_resultado], [usuario_id])
    comprobar("order y limit", len(cliente.table("usuarios").select("id").order("id", desc=True).limit(1).execute().data), 1)

    print("upsert")
    cliente.table("planes_usuario").upsert({"usuario_id": usuario_id, "plan": "pro"}).execute()
    cliente.table("planes_usuario").upsert({"usuario_id": usuario_id, "plan": "gratis"}).execute()
    planes = cliente.table("planes_usuario").select("plan").eq("usuario_id", usuario_id).execute().data
    comprobar("upsert por clave primaria no duplica y actualiza", planes, [{"plan": "gratis"}])
    cliente.table("agente_memoria_usuario").upsert({"usuario_id": usuario_id, "clave": "k", "valor": "uno"}, on_conflict="usuario_id,clave").execute()
    cliente.table("agente_memoria_usuario").upsert({"usuario_id": usuario_id, "clave": "k", "valor": "dos"}, on_conflict="usuario_id,clave").execute()
    memoria = cliente.table("agente_memoria_usuario").select("valor").eq("usuario_id", usuario_id).execute().data
    comprobar("upsert con on_conflict", memoria, [{"valor": "dos"}])

    print("JSONB")
    chat = cliente.table("agente_chats").insert({"usuario_id": usuario_id}).execute().data[0]
    cliente.table("agente_mensajes").insert([{"chat_id": chat["id"], "turno": 1, "orden": 1, "mensaje": {"role": "user", "content": "hola"}},
                                             {"chat_id": chat["id"], "turno": 1, "orden": 2, "mensaje": {"role": "assistant", "content": "qué tal"}}]).execute()
    mensajes = cliente.table("agente_mensajes").select("mensaje").eq("chat_id", chat["id"]).gte("turno", 1).order("orden").execute().data
    comprobar("los mensajes JSON vuelven como diccionarios y en orden", [m["mensaje"]["content"] for m in mensajes], ["hola", "qué tal"])

    print("funciones (rpc)")
    abono = cliente.rpc("billetera_mover", {"p_usuario": usuario_id, "p_tipo": "bono", "p_monto": 10, "p_clave": "prueba-adaptador-1"}).execute().data
    comprobar("billetera_mover abona y devuelve el saldo como número", round(float(abono[0]["saldo_nuevo"]), 2), 10.0)
    repetido = cliente.rpc("billetera_mover", {"p_usuario": usuario_id, "p_tipo": "bono", "p_monto": 10, "p_clave": "prueba-adaptador-1"}).execute().data
    comprobar("la misma clave no abona dos veces", (round(float(repetido[0]["saldo_nuevo"]), 2), repetido[0]["repetido"]), (10.0, True))
    try:
        cliente.rpc("billetera_mover", {"p_usuario": usuario_id, "p_tipo": "ajuste", "p_monto": -50}).execute()
        comprobar("saldo insuficiente debe fallar", "no fallo", "saldo_insuficiente")
    except Exception as error:  # noqa: BLE001 - el código real busca este texto en el error
        comprobar("el error contiene 'saldo_insuficiente'", "saldo_insuficiente" in str(error), True)

    print("borrado en cascada")
    limpiar(cliente)
    comprobar("no queda el usuario", cliente.table("usuarios").select("id").eq("email", CORREO_PRUEBA).execute().data, [])
    comprobar("no queda su billetera", cliente.table("billetera_cuentas").select("usuario_id").eq("usuario_id", usuario_id).execute().data, [])
    comprobar("no queda su chat", cliente.table("agente_chats").select("id").eq("usuario_id", usuario_id).execute().data, [])


# TITULO PRINCIPAL

def principal() -> int:
    """Crea el cliente, corre las pruebas y borra siempre los datos de prueba; devuelve 0 si todo pasó o 1 si algo falló."""
    cliente = base_datos.crear_cliente()
    try:
        probar(cliente)
    finally:
        try:
            limpiar(cliente)
        except Exception as error:  # noqa: BLE001
            print("No se pudo limpiar el usuario de prueba:", error)
    print("\nTODO OK" if not fallos else f"\nFALLARON {len(fallos)}: {fallos}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(principal())


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara _prueba_postgres_real .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
