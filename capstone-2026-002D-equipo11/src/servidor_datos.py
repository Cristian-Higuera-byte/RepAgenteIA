"""
servidor_datos.py
-----------------
Mini-servidor de datos de MetaTrader 5 para alimentar el gráfico en tiempo real.
Expone los precios de MT5 como JSON para que el gráfico (Lightweight Charts) haga
polling y avance solo, SIN recargar Streamlit (igual que las plataformas de trading).

Cómo ejecutarlo (en una terminal APARTE, además del 'streamlit run app.py'):
    env\\Scripts\\python servidor_datos.py

Endpoints:
    GET /velas/<símbolo>?tf=H1&n=150   -> lista de velas OHLC (carga inicial del gráfico)
    GET /ultima/<símbolo>?tf=H1        -> última vela (para actualizar el gráfico en vivo)

Nota: usa solo la librería estándar de Python (http.server), no requiere instalar nada.
El terminal de MetaTrader 5 debe estar abierto y logueado.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

import MetaTrader5 as mt5  # type: ignore[import-untyped]
from tools.mt5_bridge import inicializar_mt5, obtener_datos_historicos

PUERTO = 8000

# Temporalidades soportadas (igual que el selector del dashboard)
TF_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}


def obtener_velas(simbolo: str, tf: str, n: int) -> list:
    """Devuelve una lista de velas OHLC de MT5 en formato JSON para Lightweight Charts."""
    inicializar_mt5()
    df = obtener_datos_historicos(simbolo, timeframe=TF_MAP.get(tf, mt5.TIMEFRAME_H1), n_velas=n)
    if df.empty:
        return []
    velas = []
    for tiempo, fila in df.iterrows():
        velas.append({
            "time": int(tiempo.timestamp()),
            "open": round(float(fila["open"]), 5),
            "high": round(float(fila["high"]), 5),
            "low": round(float(fila["low"]), 5),
            "close": round(float(fila["close"]), 5),
            "volume": float(fila["tick_volume"]),
        })
    return velas


class Manejador(BaseHTTPRequestHandler):
    def _responder(self, obj):
        cuerpo = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")  # permite el fetch desde el iframe del gráfico
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        parsed = urlparse(self.path)
        partes = [unquote(p) for p in parsed.path.strip("/").split("/")]
        qs = parse_qs(parsed.query)
        tf = qs.get("tf", ["H1"])[0]
        try:
            if len(partes) >= 2 and partes[0] == "velas":
                n = int(qs.get("n", ["150"])[0])
                self._responder(obtener_velas(partes[1], tf, n))
            elif len(partes) >= 2 and partes[0] == "ultima":
                velas = obtener_velas(partes[1], tf, 2)
                self._responder(velas[-1] if velas else {})
            else:
                self._responder({"error": "ruta no reconocida"})
        except Exception as e:
            self._responder({"error": str(e)})

    def log_message(self, *args):
        pass  # silencia los logs de acceso en consola


if __name__ == "__main__":
    inicializar_mt5()
    print(f"Servidor de datos MT5 activo en http://localhost:{PUERTO}  (Ctrl+C para detener)")
    ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador).serve_forever()