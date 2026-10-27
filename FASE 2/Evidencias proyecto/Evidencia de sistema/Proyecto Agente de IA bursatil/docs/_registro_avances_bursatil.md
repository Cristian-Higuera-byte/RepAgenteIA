# Registro de avances — Proyecto bursátil (para informe Word)

> Bitácora de cambios con código, para armar el informe final. Se actualiza cada sesión.

---

## 16-10-2026 — Decisión de arquitectura: migración de MT5/XM a Capital.com (API REST)

### Contexto / motivación
Se decidió cambiar la arquitectura: en lugar de depender del **terminal MetaTrader 5 de XM**
(que exige una máquina Windows con el terminal abierto y una cuenta logueada manualmente),
la plataforma se conectará al bróker vía **API REST con clave propia del usuario**.
XM **no** ofrece API pública a clientes retail; tras comparar opciones (OANDA, Alpaca, IBKR,
Tradier, Capital.com) se eligió **Capital.com** por ser forex/CFD (mismo universo: oro, índices),
tener esquema de API key + contraseña, y cuenta demo gratis.

Objetivo final: web en Python **sin terminal MT5 ni Windows obligatorio**; a futuro, multiusuario
(cada usuario con su propia API key, credenciales cifradas por usuario en Supabase).

### Estrategia técnica
Todo el dashboard habla con el bróker a través de **un solo módulo**
(`herramientas/puente_mt5.py`), importado por ~45 archivos. Plan: convertirlo en un **despachador**
que delega a un backend u otro según `PROVEEDOR` del `.env`:
```
herramientas/backends/mt5.py       (el código MT5 actual, movido tal cual)
herramientas/backends/capital.py   (NUEVO, mismo contrato, vía REST)
herramientas/puente_mt5.py         (despachador; los 45 imports NO cambian)
```

### Hecho en esta sesión
1. **`.env`**: añadidas variables de Capital.com — `PROVEEDOR`, `CAPITAL_DEMO`,
   `CAPITAL_API_KEY`, `CAPITAL_IDENTIFIER`, `CAPITAL_API_PASSWORD`.
2. **`_prueba_conexion_capital.py`** (nuevo): script de validación de la API (sesión + cuenta +
   precio del oro), con fix de `certifi` por la ruta con tildes (mismo bug SSL que yfinance).

### Prueba de conexión — EXITOSA (entorno DEMO)
```
[OK] Sesión abierta correctamente.
   - Account (USD): saldo=1000.0  disponible=1000.0
   - Gold  epic=GOLD  Bid=4161.69  Offer=4162.19  estado=TRADEABLE
```

### Aprendizajes clave de la API de Capital.com
- Auth: `POST /session` con header `X-CAP-API-KEY` + body `{identifier, password, encryptedPassword:false}`.
  Devuelve en headers `CST` y `X-SECURITY-TOKEN` (válidos 10 min).
- **La contraseña del `POST /session` es la que genera/define la propia KEY, NO la de la cuenta.**
  Si no se pone una personalizada, Capital genera una (hay que copiarla al crearla; no se recupera).
- `identifier` = correo de la cuenta (un error típico: una letra mal → `error.invalid.details` / HTTP 401).
- La API key de Capital tiene 16 caracteres (es normal, no está truncada).
- Requiere 2FA activo en la cuenta antes de generar la key.
- URLs: demo `https://demo-api-capital.backend-capital.com/api/v1`,
  real `https://api-capital.backend-capital.com/api/v1`.
- El oro es `epic=GOLD` (coincide con el alias que ya usa el proyecto).

### Backend construido — `herramientas/backends/capital.py` (16-10)
Se creó el backend completo con **los mismos nombres de función que el puente MT5**
(incluido `inicializar_mt5` y `MT5_LOCK`), para que sea un reemplazo *drop-in*.
Implementa: sesión con renovación automática (token 10 min) y reintento ante 401,
`obtener_info_cuenta`, `obtener_posiciones`, `obtener_historial`, `especs_posicion`,
`obtener_precio_actual`, `obtener_datos_historicos`, `obtener_velas_rango`,
`ejecutar_orden_mercado`, `colocar_orden_pendiente`, `cerrar_posicion`,
`modificar_sltp`, `modificar_orden`, `eliminar_orden`, `obtener_dom`, `resolver_simbolo`.
También `herramientas/backends/__init__.py`.

**Mapeos resueltos (verificados contra la API demo):**
- epics reales: oro `GOLD`, `US30`, `US100`, `US500`, `BTCUSD` (coinciden con los alias del proyecto).
- precios/velas: `GET /prices/{epic}` con bid/ask → se usa el punto medio para OHLC.
- cuenta: `GET /accounts` → balance, equity = balance + profitLoss, disponible, margen.
- órdenes: `POST /positions` y `POST /workingorders` → devuelven `dealReference` → se confirma
  con `GET /confirms/{ref}` (dealStatus ACCEPTED) para obtener el `dealId`.
- pendiente LIMIT/STOP deducido del precio vs mercado (igual que MT5).

**Prueba de lectura del backend: EXITOSA** (cuenta, precio oro, históricos H1, posiciones/historial
vacíos, DOM no disponible). Órdenes implementadas pero NO ejecutadas (colocarían trades demo reales;
requieren OK explícito o validación manual desde el dashboard).

**Aproximaciones / a validar con operación real:**
- `especs_posicion.k` ≈ `contractSize` (asume cotización en USD).
- `obtener_historial`: P/G realizado leído de forma defensiva (validar campo con un cierre real).
- `swap` por posición = 0.0 (Capital no lo expone; hay `overnightFee` a nivel de instrumento).

### Hallazgo de alcance — MT5 está acoplado más allá del puente
~26 archivos importan `MetaTrader5` directamente (constantes `TIMEFRAME_*`, `ORDER_TYPE_*`
y, en `servidor_precios/` y `nucleo_agente/ordenes/`, llamadas reales a `mt5.*`).
Por eso "apagar MT5 con un flag" NO basta con el despachador: hay que (a) un shim de
constantes MT5 sin el paquete, y (b) enrutar/retirar las llamadas `mt5.*` de esos módulos.

### Etapa 1 del desacople — DESPACHADOR (16-10) ✅
- `herramientas/puente_mt5.py` dejó de tener lógica MT5: ahora es un **despachador** que,
  según `PROVEEDOR` del .env (`mt5` | `capital`), reexporta el contrato del backend elegido.
- El código MT5 original se movió tal cual a `herramientas/backends/mt5.py` (fallback intacto).
- Los ~45 imports `from herramientas.puente_mt5 import ...` NO cambiaron; el candado compartido
  (`fuentes/mt5_fuentes` lee `herramientas.puente_mt5.MT5_LOCK`) sigue funcionando.
- **Probado:** con `PROVEEDOR=capital` lee la cuenta real por REST; con `PROVEEDOR=mt5` importa
  el backend MT5 sin lanzar el terminal. Cero regresión.

### Alcance real del desacople restante (medido)
De los archivos que importan `MetaTrader5` directo:
- **Solo constantes (6):** `mercados/piezas.py`, `mercado_datos/referencias.py`,
  `mercado_datos/sparkline.py`, `vigilancia/analisis.py`, `servidor_precios/constantes.py`,
  `servidor_precios/velas.py`.
- **Llamadas reales `mt5.*` (18):** componentes (buscador, grafico, mercados, panel_orden,
  posiciones, profundidad), `estadisticas_*`, `nucleo_agente/ordenes/*`, `vigilancia/*`,
  `servidor_precios/motor/*` y `simbolos.py`. Usan symbol_info, symbol_info_tick, account_info,
  positions_get, orders_get, history_deals_get, copy_rates_from_pos, order_calc_profit/margin,
  market_book_get, terminal_info, last_error.
- Hay además una 2ª capa (`fuentes/mt5_fuentes/`) con su propia conexión MT5 (usada por el agente).

Constantes MT5 a cubrir por el shim: TIMEFRAME_*, ORDER_TYPE_*, ORDER_TIME_*, ORDER_FILLING_*,
TRADE_ACTION_*, TRADE_RETCODE_DONE(_PARTIAL), DEAL_ENTRY_OUT, DEAL_TYPE_*, BOOK_TYPE_*,
POSITION_TYPE_BUY, SYMBOL_TRADE_MODE_FULL, ACCOUNT_TRADE_MODE_DEMO.

### Etapas 2 y 3 del desacople — SHIM MT5 sobre Capital (16-10) ✅
Paquete nuevo `proveedores/` (NO importa MetaTrader5 al cargar, para arrancar sin el paquete):
- `proveedores/selector_mt5.py`: expone `mt5` = paquete real MetaTrader5 (PROVEEDOR=mt5) o el shim
  (PROVEEDOR=capital). Los archivos solo cambiarán `import MetaTrader5 as mt5` →
  `from proveedores.selector_mt5 import mt5`.
- `proveedores/capital_mt5_compat.py`: shim con TODAS las constantes MT5 usadas (valores enteros
  reales) + primitivas sobre Capital: `initialize/shutdown/last_error/terminal_info`,
  `symbol_info/symbol_info_tick/symbol_select/symbols_get`, `account_info`,
  `positions_get/orders_get/history_deals_get`, `copy_rates_from_pos/copy_rates_range`,
  `order_calc_profit/order_calc_margin`, `order_send` (enruta apertura/cierre al backend Capital),
  `market_book_*` (vacío). Objetos imitan MT5 por atributos (info.digits, tick.bid, p.ticket...).

**Probado (ejercitado como el código real):** symbol_info (digits=2, point=0.01, tick_value=1.0,
stops_level=4), tick, account (equity/trade_mode demo), copy_rates indexable `rates[-2]['close']`,
order_calc_profit (−60 para 1 lote 4160→4100) y order_calc_margin (208 = 4160·5%). Todo OK.

**A validar en Etapa 4 / con operación real:** campos de `/workingorders` y `/history/transactions`
(leídos defensivamente); rendimiento de `symbol_info_tick` en el motor (idealmente mover a WebSocket);
`symbols_get` devuelve un set curado (la Observación de mercado completa necesitaría /marketnavigation).

### Etapa 4 del desacople — MIGRACIÓN DE IMPORTS (16-10) ✅
- **27 archivos** migrados: `import MetaTrader5 as mt5` → `from proveedores.selector_mt5 import mt5`
  (preservando indentación y comentarios). Excluidos a propósito: `backends/mt5.py` (MT5 real) y
  `proveedores/selector_mt5.py`. No queda ningún import directo de MetaTrader5 fuera de esos dos.
- **Capa del agente** `fuentes/mt5_fuentes/conexion.py` ahora respeta `PROVEEDOR`: con `capital` usa
  el shim (abre sesión REST, sin rutas de terminal); con `mt5` se conecta al terminal como antes.
  Se añadieron al shim las funciones del whitelist de solo-lectura que faltaban (version, *_total,
  history_orders_get).
- **Probado con PROVEEDOR=capital:**
  - Los 27 módulos importan sin error.
  - La capa del agente (`fuentes/mt5_fuentes`) devuelve precio, cuenta, posiciones y especificación.
  - `compileall` de todo el proyecto: sin errores de sintaxis.

**Estado:** con `PROVEEDOR=capital` la app ya NO depende del paquete MetaTrader5 ni del terminal
(salvo `backends/mt5.py`, que solo se carga con `PROVEEDOR=mt5`). Falta la verificación visual
end-to-end lanzando Streamlit (pendiente de OK del usuario).

### Detalles menores a pulir
- En la capa del agente, el campo `"fuente": "MetaTrader 5"` está hardcodeado (cosmético; diría
  "Capital.com" bajo ese proveedor).
- `symbols_get` del shim devuelve un set curado → la Observación de mercado completa necesitaría
  `/marketnavigation` de Capital.
- Validar con operaciones reales: campos de `/workingorders` y `/history/transactions`.
- Motor de precios: idealmente pasar a WebSocket de Capital (hoy sondea por REST).

### Prueba visual + incidente del terminal MT5 (16-10)
- Se lanzó el dashboard con `PROVEEDOR=capital` (puerto 8599) y el servidor de precios (8000):
  arranca, login propio (Supabase) OK, y el encabezado muestra el saldo de **Capital** ($1000 USD).
- Se observó que el **terminal MT5 se abrió**. Investigado a fondo:
  - Diagnóstico: bajo `PROVEEDOR=capital`, importar la app, el servidor y la capa del agente
    **NO** carga `MetaTrader5` ni `backends.mt5` (`_ES_CAPITAL=True`). El código Capital no abre MT5.
  - Causa real: el dashboard **previo en 8501** (config MT5 vieja) que ocupaba ese puerto.
- **Blindaje añadido** en `fuentes/mt5_fuentes/conexion.py`: `load_dotenv()` antes de leer PROVEEDOR
  (evita caer a 'mt5' por orden de import) + salvaguarda en `_conectar` que LANZA error si se intenta
  abrir el terminal bajo capital. Probado.
- Para lanzar con Capital (el `.env` ya trae `PROVEEDOR=capital`):
  `env\Scripts\python.exe -m streamlit run aplicacion.py`  (+ opcional `servidor_datos.py`).
- Intervalo de ticks subido a 1.5 s (suave con el límite REST; con MT5 puede volver a 0.25 s).
- Textos corregidos: pantalla de carga ("Conectando con el bróker…") y aviso de cuenta.

### Bugs encontrados en la prueba visual y corregidos (16-10)
- **Buscar activos crasheaba** (`AttributeError: SimpleNamespace no tiene 'description'`): el shim
  `symbols_get`/`symbol_info` no exponía `description`/`path`. Añadidos. Probado.
- **Gráfico "Cargando…"**: se diagnosticó que NO es un bug de datos — el servidor sirve las velas
  correctamente (probado `/velas/USDJPY?tf=M1&n=300` → 300 velas) y el CORS está bien (refleja el
  Origin localhost:8501). La causa: el dashboard corría con el código viejo (sin los arreglos del
  shim). Se resuelve reiniciando el dashboard.
- Mejora: shim `symbol_info` ahora expone `trade_calc_mode` (+ constante `SYMBOL_CALC_MODE_FOREX`),
  así `info_simbolo` calcula bien decimales/pip (USDJPY→3/0.01, GOLD→2). Antes se tragaba en except.
- Pendiente de datos (no bug de migración): acciones (Adidas/Nvidia) salen 0.00000 porque el shim
  `symbols_get` devuelve un set curado sin esas acciones; su epic no se resuelve. Mejorar con
  /marketnavigation o un mapa de epics de acciones. DRAWDOWN −99% = datos viejos de equity (MT5).

### Cómo reiniciar limpio (tras cambios de código)
1. Cierra el dashboard viejo (Ctrl+C) y el servidor (Ctrl+C).
2. `env\Scripts\python.exe servidor_datos.py`  (una terminal)
3. `env\Scripts\python.exe -m streamlit run aplicacion.py`  (otra terminal)
   (el .env ya trae PROVEEDOR=capital)

### Bugs de la 2ª prueba visual — corregidos (16-10)
Abrí el dashboard yo mismo (browser pane, sesión reusada) y diagnostiqué con la consola/red:
- **Gráfico "Cargando…"**: el JS pedía `/velas/...?n=1500`; Capital rechaza `max>1000`
  (`error.invalid.max`) → 0 velas. FIX: `backends/capital.py._velas_crudas` recorta `max` a 1000.
- **Buscador solo 10 activos**: el shim devolvía una lista curada. FIX: `symbols_get` ahora trae el
  catálogo real vía `/marketnavigation` (recorre grupos + 1 nivel de subnodos, cacheado 10 min):
  ~1548 instrumentos (forex, índices, materias primas, cripto, acciones, ETF...). Primera carga ~15 s
  (luego cacheada); se puede optimizar con llamadas en paralelo.
- **Acciones en 0.00000** (Adidas/Nvidia/Tesla): el nombre guardado no resolvía al epic. FIX:
  `resolver_simbolo` ahora, si el núcleo no es epic válido, busca por texto (`searchTerm`) y cachea
  (Adidas→ADSGN, Nvidia→NVDA, Tesla→TSLA, Apple→AAPL), verificado con precio real.
- **Etiquetas "XM / MT5" y "Cuenta conectada en MT5 (demo)"**: FIX: `puente_mt5.NOMBRE_PROVEEDOR`
  ("Capital.com" | "MT5 / XM") usado en `grafico/cabecera_precio.py` y `panel_orden/panel.py`.

IMPORTANTE: el recorte de velas vive en el backend que usa TAMBIÉN el servidor de precios →
reiniciar el **servidor** y el **dashboard** para que tomen todos los arreglos.

### Integración de los cambios de Cristian (merge) — 16-10
Se commiteó la migración a Capital (f5edc95) y se mergeó `origin/main` (cambios de Cristian:
favoritos a barra derecha, watchlist no desplegable, backtest con replay, cortina de transición,
velocidad, y headers de crédito en todos los archivos). Merge commit f4c845b.
**9 conflictos resueltos manteniendo AMBOS** (Capital + layout de Cristian):
- `puente_mt5.py` → se conservó el despachador (bridge MT5 vive en `backends/mt5.py`; Cristian solo
  tocó docstring/headers).
- `fuentes/mt5_fuentes/conexion.py` → rename `_lock`→`_candado` de Cristian + lógica Capital.
- `info_mt5/entrada/oco/stop_dinamico` → versión de Cristian + import vía `proveedores.selector_mt5`.
- `cabecera_precio/panel_orden` → layout de Cristian + etiqueta `NOMBRE_PROVEEDOR`.
- `vista_operativa` → layout nuevo de Cristian.
Verificado: compila todo (exit 0) y los 13 módulos clave (app + favoritos/transición/riel + servidor)
importan OK bajo Capital. Merge en LOCAL (sin push). `lista_colapsable/` quedó como código huérfano
(Cristian reemplazó el watchlist desplegable). Conflicto de stash viejo en
`_contexto_nuevo_chat/_dia17_gen_informe.py` (ajeno al merge, no afecta la app).

### Rendimiento: precios en vivo por WebSocket (16-10)
La app iba lenta porque con Capital cada tick era una llamada REST remota (vs MT5 local). Solución:
- **`servidor_precios/streaming_capital.py`** (nuevo): mantiene UNA conexión WebSocket a
  `wss://api-streaming-capital.backend-capital.com/connect`, se suscribe (`marketData.subscribe`
  con cst/securityToken del backend), guarda Bid/Ask en caché, hace ping cada 5 min y reconecta solo.
  Usa `websockets` (asyncio en hilo daemon). Máx 40 epics.
- **`motor/base.py`**: bajo Capital, `_leer_ticks` lee de la caché del WS (instantáneo) en vez de
  `mt5.symbol_info_tick` (REST). Con MT5 sin cambios.
- **`constantes.py`**: `INTERVALO_TICKS` 1.5 → 0.5 s (leer el WS es gratis). La cuenta sigue REST cada 3 s.
Resultado: se eliminan las decenas de llamadas REST/seg del tiempo real. Probado: el WS recibe precios
en vivo (GOLD/EURUSD/USDJPY/BTC) que se actualizan cada segundo. Compila y el servidor importa OK.
Para activarlo: **reiniciar el servidor** (`servidor_datos.py`).

### Rendimiento 2: batch de precios + caché de lecturas (16-10)
Diagnóstico: cada llamada REST a Capital tarda ~300-500 ms, y el dashboard re-ejecuta TODA la página
en cada interacción haciendo muchas llamadas REST (cuenta, specs, margen, DOM...) + `carga.py` pedía
el precio de CADA símbolo uno por uno (~8 s de congelada). Fixes:
- **`backends/capital.py`**: caché de lecturas (precio 3 s, cuenta 2 s, posiciones 2 s) + nueva
  `precargar_precios(symbols)` que pide VARIOS precios en 1 llamada (`GET /markets?epics=...`, máx 50).
- **`puente_mt5.py`**: exporta `precargar_precios` (no-op en MT5).
- **`carga.py`**: llama `precargar_precios(simbolos)` antes del bucle → 1 llamada en vez de N.
- **shim `_TTL_MERCADO`** 2 s → 30 s (specs estáticas; el bid/ask de display viene por SSE/WS).
Medido: cargar 8 precios pasó de **3132 ms → 276 ms**; re-render cacheado **0 ms**.
NOTA: la caché es por proceso (no por usuario); al ir a multiusuario habrá que hacerla por usuario.

### Rendimiento 3: buscador instantáneo (16-10)
El buscador tardaba ~15 s porque el catálogo se armaba con ~60 llamadas `/marketnavigation` EN SERIE.
Fix en `proveedores/capital_mt5_compat.py._catalogo`:
- Recorrido EN PARALELO (ThreadPoolExecutor, `_nav` sin candado) + reintento paralelo de subnodos vacíos.
- **Caché en disco** `data/catalogo_capital.json` (TTL 24 h): tras la 1ª carga, abre en ~33 ms.
Medido: 1ª vez ~5 s (antes 15.8 s); desde disco **33 ms** con 1586 instrumentos.

### Diario (trading journal) con Capital — limitación encontrada (16-10)
El Diario (`estadisticas_diario.calcular()`) reconstruye operaciones **emparejando deals IN+OUT de MT5
por position_id** (entrada/salida, duración, R/R). Capital NO da esa estructura: su
`/history/transactions` solo trae "Trade closed" con instrumentName, size/monto, fecha, dealId (sin
precios de entrada/salida ni P/L desglosado claro); `/history/activity` vino vacío. Por eso el Diario
queda vacío bajo Capital. La cuenta demo además solo tiene 1 cierre (GOLD, hoy).
PENDIENTE: adaptar el Diario a Capital = diario BÁSICO desde `obtener_historial` (símbolo, P/L, fecha);
los datos ricos de MT5 (entrada/salida exactas, R/R) no estarán o serán aproximados. Nota: el campo
de P/L en la transacción Capital es ambiguo (`size` podría ser el monto); validar con más cierres.

### Diario adaptado a Capital (16-10) ✅
`herramientas/estadisticas_diario.py`: `operaciones()` ahora es provider-aware. Bajo Capital usa
`_operaciones_capital()` que arma el diario desde `obtener_historial` (símbolo, P/L=`neto`, fecha),
con las mismas claves que espera la UI; `estadisticas()` calcula igual (win rate, profit factor, P&L,
drawdown). Campos sin dato en Capital (entrada/salida, duración, R/R) quedan neutros (0/None/"—").
Textos de UI: subtítulo neutral y nota al pie provider-aware (explica la limitación de Capital).
Probado: muestra la operación GOLD cerrada (+0.13, win rate 100%). Compila e importa OK.
Confirmado: en Capital el monto del cierre en `/history/transactions` (`size`) ES el P/L (el balance
subió exactamente ese monto).
FIX mini-gráfico: con `hora_in=0` el rango de velas daba inicio negativo → `datetime.fromtimestamp`
reventaba en Windows (OSError 22). Ahora `_operaciones_capital` usa `hora_in=hora_out` (duración 0) y
`obtener_velas_rango` se blindó contra timestamps <=0 (clamp). El mini-gráfico muestra ~11 velas
alrededor del cierre.

### Resumen (portafolio) con Capital — correcciones (16-10)
- **Drawdown -99.2%**: era el equity viejo de XM en `data/equity.json` (4523 muestras, pico $133,164).
  Reseteado a `{"puntos":[]}` (respaldo `data/equity_xm_viejo.json.bak`). El drawdown se reconstruye
  desde los ~$1000 de Capital (el motor va registrando). Afectaba también la barra superior.
- **P&L realizado +0.00 pese a "1 cierre"**: el shim `history_deals_get` no usaba `size` como P/L (el
  backend `obtener_historial` sí, por eso el Diario sí lo mostraba). FIX: shim usa
  `profitAndLoss or pnl or size`. Ahora realizado = +0.13.
- **Depósito inicial 0.00 / Rentabilidad 0.00%**: Capital no genera "deal de balance" y su campo
  `deposit` refleja el balance actual (no el inicial). FIX en `estadisticas_portafolio`: depósito
  inicial = balance − P/L realizado acumulado (asume sin depósitos/retiros) = 1000.00; rentabilidad
  = +0.13 (+0.0130%). (También se añadió `deposito` a `obtener_info_cuenta` como dato de respaldo.)
Los demás ceros (exposición, riesgo, comisiones, flotante) son correctos: no hay posiciones abiertas.
PENDIENTE multiusuario: el depósito reconstruido asume sin depósitos/retiros; con cuentas reales habrá
que usar el historial de movimientos real.

### Pendiente
- Reiniciar servidor + dashboard y confirmar todo (velocidad, buscador, layout de Cristian).
- Commitear WebSocket + optimizaciones + buscador (sin commitear aún).
- DRAWDOWN −99% = equity_store viejo de MT5 → resetear.
- Decidir si se hace push de la rama EmilioFuentes.
- Commitear los cambios del WebSocket (sin commitear aún).
- DRAWDOWN −99% = historial de equity viejo (MT5) → resetear ese registro.
- Optimizar la carga del catálogo (paralelizar); quedan etiquetas "MT5" menores (diario, chat, backtest).
- Motor de precios a WebSocket; validar /workingorders y /history/transactions con operaciones reales.
- Rotar credenciales de prueba antes de producción.
- Pulir etiquetas "MT5"/"XM" restantes (badge del gráfico, barra superior, buscador, diario).
- Motor de precios a WebSocket de Capital (para volver a ticks rápidos sin chocar el límite REST).
- Validar /workingorders y /history/transactions con operaciones reales.
- Rotar las credenciales de prueba por unas seguras antes de producción.
- Validar las funciones de órdenes con una operación demo real (y el P/G del historial).
- UI: panel DOM → mostrar "no disponible"; `info_mt5.py` → estado de conexión de Capital.
- Rotar las credenciales de prueba por unas seguras antes de producción.
