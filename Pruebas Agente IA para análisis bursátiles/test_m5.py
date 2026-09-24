import MetaTrader5 as mt5  # type: ignore[import-untyped]
import pandas as pd  # type: ignore[import-untyped]

print("1. Intentando inicializar MetaTrader 5...")
if not mt5.initialize():
    print(f"❌ Error al inicializar MT5: {mt5.last_error()}")
    quit()

print("¡Conexión exitosa con MT5!")

# 1. Obtener información de la cuenta demo
cuenta = mt5.account_info()
if cuenta is not None:
    print(f"\n--- INFORMACIÓN DE LA CUENTA ---")
    print(f"Login: {cuenta.login}")
    print(f"Servidor: {cuenta.server}")
    print(f"Balance: {cuenta.balance} {cuenta.currency}")
    print(f"Equity: {cuenta.equity} {cuenta.currency}")
else:
    print("❌ No se pudo obtener la información de la cuenta.")

# 2. Probar extracción de datos para un símbolo común (por ejemplo, EURUSD o el que tengas visible)
simbolo = "EURUSD"
print(f"\n2. Probando extracción de datos para {simbolo}...")

# Asegurar que el símbolo esté visible
if mt5.symbol_select(simbolo, True):
    tick = mt5.symbol_info_tick(simbolo)
    if tick:
        print(f"Precio actual {simbolo} -> Bid: {tick.bid} | Ask: {tick.ask}")
    else:
        print(f"⚠️ No se pudo obtener el tick para {simbolo}. Probando con otro activo...")
else:
    print(f"⚠️ El símbolo {simbolo} no está disponible. Revisa los activos de tu Market Watch.")

# 3. Descargar algunas velas históricas
tasas = mt5.copy_rates_from_pos(simbolo, mt5.TIMEFRAME_H1, 0, 5)
if tasas is not None and len(tasas) > 0:
    df_tasas = pd.DataFrame(tasas)
    df_tasas['time'] = pd.to_datetime(df_tasas['time'], unit='s')
    print(f"\n--- ÚLTIMAS 5 VELAS H1 DE {simbolo} ---")
    print(df_tasas[['time', 'open', 'high', 'low', 'close', 'tick_volume']])
else:
    print("❌ No se pudieron descargar las velas históricas.")

# Cerrar conexión al terminar
mt5.shutdown()
print("\nPrueba finalizada y conexión cerrada correctamente.")