# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------- INICIO Piña y Jara _prueba_backend_capital .PY ---------------------------
# -------------------------------------------------------------------------------------------------------

"""Prueba de LECTURA del backend herramientas/backends/capital.py (sin órdenes)."""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from herramientas.backends import capital as cap

print("inicializar:", cap.inicializar_mt5())
print("\nresolver XAUUSD ->", cap.resolver_simbolo("XAUUSD"))
print("resolver US30 ->", cap.resolver_simbolo("US30"))

print("\n--- info cuenta ---")
print(cap.obtener_info_cuenta())

print("\n--- precio oro ---")
print(cap.obtener_precio_actual("GOLD"))

print("\n--- posiciones ---")
print(cap.obtener_posiciones())

print("\n--- historial (7 dias) ---")
print(cap.obtener_historial(dias=7))

print("\n--- datos historicos GOLD H1 x5 ---")
df = cap.obtener_datos_historicos("GOLD", 16385, 5)
print(df)

print("\n--- DOM ---")
print(cap.obtener_dom("GOLD"))

print("\n[OK] Prueba de lectura del backend completada.")


# -------------------------------------------------------------------------------------------------------
# ----------------------------- FIN Piña y Jara _prueba_backend_capital .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
