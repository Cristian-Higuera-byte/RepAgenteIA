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

### Cierre del Día 19 (16-10-2026)
- **Commiteado y pusheado a `main`.** `main` remoto quedó en `edd73b5` (fast-forward desde `ca65cf0`):
  migración Capital (f5edc95) + merge de Cristian (f4c845b) + WebSocket/rendimiento/vistas (edd73b5).
- Informe del día generado (Día 19) en `OCTUBRE/16-10-2026/`. Guía de creación de cuenta + API del
  usuario corregida (frases + estilo, 32 imágenes conservadas).
- Scripts de prueba (`_prueba_*.py`, `_descubrir_capital.py`) y `data/` no versionados a propósito.

### Pendientes (consolidados al cierre del Día 19)
1. Pulir etiquetas/textos menores que aún nombran "MT5"/"XM" en la UI (badge del gráfico, barra
   superior, buscador, diario, backtest, chat) → provider-aware.
2. Validar las funciones de órdenes (abrir/cerrar/pendientes/SL-TP) con operaciones demo reales en
   Capital; confirmar los campos de `/workingorders` y el P/L del historial con más cierres.
3. Afinar aproximaciones del backend Capital: `especs_posicion.k` y swap (para la Cartera).
4. Multicliente: almacenamiento por usuario (equity, journal, credenciales de API cifradas) en Supabase;
   el depósito reconstruido (balance − P/L) asume sin depósitos/retiros → usar historial real.
5. Cobertura del catálogo del buscador (categorías) y set curado de respaldo.
6. Rotar las credenciales de prueba por unas seguras antes de producción.
7. Opcional: capturas del dashboard con Capital para el informe.


## 19-10-2026 — Día 20: validación de operaciones en Capital.com, rendimiento, estándar de código y merge con Cristian

### Operaciones sobre Capital.com (diferencias frente a MT5)
- **Cancelar/modificar órdenes pendientes:** Capital identifica cada orden con un texto largo (dealId) y la interfaz lo
  convertía a entero. Se creó `herramientas/tickets.py` (acepta ambos formatos) y se ajustó el JS que envía la cancelación.
- **Lotes:** Capital mide en unidades (FX: 1 lote = 100.000). Se agregó el factor de lote por instrumento
  (`factor_lote`, `factor_lote_epic`) y se aplica en cartera, ticket e historial (0,01 lote ya no aparece como 100).
- **SL/TP:** cada PUT reemplaza ambos niveles; `modificar_sltp`/`modificar_orden` leen el nivel vigente y lo reenvían, así se
  puede quitar solo uno. Validación del **stop dinámico** (distancia mínima del bróker) con mensaje claro.
- **Capital/margen y hora:** el `balance` ya incluye el P/L abierto (no se cuenta dos veces); la hora se pasa a hora local.
- **OCO:** se adaptó el identificador del par. **PENDIENTE:** el botón verde de OCO no responde en algunas pruebas.

### Rendimiento y vistas
- Se quitó el candado global de consultas (serializaba REST), caché con refresco en segundo plano (`_cache_con_refresco`),
  caché de proceso (`herramientas/cache_proceso.py`) y **precarga** de todas las pestañas. Modal de cierre instantáneo y
  cifras del modal en vivo; etiqueta de precio alineada con la línea del gráfico.
- **Mercados:** logos de instrumentos (incluye acciones), arranca con el primer activo de la lista. **Diario:** reconstruido con
  `/history/activity` (ventanas de 24 h): lotes, entrada, salida y duración. **DOM nivel 1** (mejor bid/ask, spread y cinta
  de cotizaciones, `profundidad_mercado/nivel1.py`, ruta `/dom/<sym>`). Campo del Diario ya no editable.

### Estándar de código de la empresa (referencia: menu.php + notas de la reunión)
- Cabecera de créditos, banner INICIO/FIN y pie en cada archivo; `# TITULO` por función/clase (Python, JS y CSS); descripción
  (docstring) en cada función; comentarios sobrantes retirados.
- **Fachadas eliminadas** de `componentes_plataforma/` (19 archivos que solo reexportaban); imports reescritos.
- **Nombres en español sin abreviar** (solo trading en inglés), por fases: A (~940 nombres compartidos Python/CSS/JS), B
  (variables y parámetros), B2 (funciones y constantes) y C (JS, ~380 identificadores). Verificado con un banco de pruebas en el
  navegador (reglas CSS, errores de consola, recorrido de vistas). Excepciones: API de MT5 (`capital_mt5_compat.py`),
  herramientas del agente, claves de protocolo servidor↔JS y propiedades JS. Detalle en la memoria `nombres-en-espanol`.
- **Bug por renombrado corregido:** las tarjetas de campo del ticket (volumen, SL, TP, calculadora de riesgo) perdieron su estilo
  porque `ord_bx`/`ord_box` chocaron; el CSS apuntaba a `orden_zona_` en vez de `orden_caja_` (`ticket.css`). Reiniciar Streamlit
  (el CSS se lee una vez con `lru_cache`).

### Merge con los cambios de Cristian (`origin/main` = `05112ad`)
- Su commit toca 22 archivos (noticias con lectura interna, serie de velas en memoria, sesión compartida y limitador de
  peticiones en `capital.py`, `paralelo.py`, `velas.py`). Se guardó lo nuestro en un commit (`0d4568d`) y se fusionó: 28
  conflictos en 9 archivos; en `capital.py`, `rss.py`, `velas.py` y `noticias/secciones.py` se tomó su versión y se le aplicaron
  nuestros nombres (fases A/B/B2). Se unificaron `_ORDEN_CANDADO`, `_CANDADO_SESION` y `_medio`; se agregaron descripciones
  a las funciones nuevas. Verificado: compila, sin nombres indefinidos, módulos principales se importan.
- **Subido a `main`: `ab23724`** (merge). No probado corriendo en pantalla todavía.

### Documentos de la práctica (carpeta `C:\Practica\Informe Practica Profesional\`)
- Informe de práctica (14 páginas) y bitácora Duoc UC rellenados; datos tomados del formulario de validación. Informe del Día 20
  generado en `OCTUBRE/19-10-2026/`.

### Pendientes (al cierre del Día 20)
1. **Probar en pantalla el código fusionado** (reiniciar Streamlit y servidor): Noticias, Mercados, gráfico (W1, backtest hasta
   20.000 velas), cancelación de órdenes, ticket (campos).
2. Botón verde de **OCO** sin respuesta (pedir detalle: ¿no pasa nada o hay error?).
3. Renombrado restante: atributos de clase, propiedades JS, clases CSS de una palabra y JS embebido en cadenas de Python.
4. Avisar a Cristian: al traer `main` recibirá cambios en casi todos los archivos (nombres nuevos).
5. Los pendientes 1 a 6 del Día 19 siguen vigentes (etiquetas MT5, validar órdenes, aproximaciones, multicliente, catálogo,
   credenciales). Idea evaluada: **copytrading** con copiador propio sobre la API de Capital (retraso de 1 a 2 s, tope de
   peticiones, revisión CMF); prototipo con dos cuentas demo.

## 20-10-2026 — Día 21: preparación multiusuario (cuentas Capital.com por usuario, real y demo) y nuevo proyecto Supabase

### Indicador "Mercado" de la barra superior con Capital
- **Hallazgo:** `_mercado_abierto` (herramientas/estadisticas_portafolio.py) decidía por avance del tick entre dos lecturas. Con Capital el tick del shim siempre lleva la hora actual y la primera lectura devuelve "sin dato"; como la barra solo se redibuja con un rerun, quedaba en "—".
- **Solución:** con `PROVEEDOR=capital` se lee el estado de sesión que informa Capital (`marketStatus` → `symbol_info().trade_mode`). Con MT5 queda el método anterior.

### Análisis: qué hay que revisar para lanzar a muchos usuarios (checklist en 6 bloques)
- Arquitectura (cuenta por usuario, estado global, servidor de precios, almacenes locales), seguridad, fiabilidad/rendimiento, despliegue, funcional y legal/negocio. Se decidió cada usuario con SUS cuentas de Capital (real y demo) y elección tipo Capital.com, pensando en dinero real desde el diseño (no versión solo demo).
- **Hallazgo:** el backend `capital.py` asumía una sola cuenta (credenciales del `.env` en constantes del módulo, tokens, cachés y límite de peticiones globales).

### Nuevo proyecto Supabase `pyj-bursatil-plataforma` (separado de los otros proyectos)
- Creado en plan Free, región Americas, con "Automatically expose new tables" desactivado y RLS automático activado. Tablas: `usuarios`, `watchlist_usuario`, `credenciales_bolsa` (SQL con el estándar P&J en `herramientas/sql/esquema_plataforma.sql`).
- **Hallazgo:** al desactivar la exposición automática las tablas nacen sin permisos y el servidor falló con `42501 permission denied`; se agregó `GRANT ... TO service_role` (solo ese rol; `anon` y `authenticated` siguen sin acceso). Quedó en el SQL.
- Los `.sql` siguen ahora el estándar P&J (créditos, banner INICIO/FIN, títulos y descripciones; referencia en `ORDENAMIENTO ARCHIVOS`).

### Paso 1 — Credenciales cifradas (`herramientas/credenciales_bolsa.py`)
- Cada dato (correo, API key y contraseña de la key) se cifra con Fernet antes de salir del servidor; clave maestra en `CREDENCIALES_CLAVES` (una o varias, la primera cifra y todas descifran → rotación con `recifrar_todas()`).
- Una fila por usuario y modo: `PRIMARY KEY (usuario_id, es_demo)`. `estado_credenciales()` devuelve solo `{"demo": bool, "real": bool}`, nunca secretos.

### Paso 2 — Sesión de Capital por usuario (sin reescribir el núcleo)
- `capital.py` pasó a `capital_nucleo.py` (misma lógica; solo se quitaron del log fragmentos de la API key). `sesiones_capital.py` carga una COPIA independiente del núcleo por cada (usuario, modo) con `importlib`; cada copia tiene sus credenciales, tokens, cachés, límite de peticiones y archivo de sesión. `capital.py` es ahora una fachada (`__getattr__` de módulo) que enruta cada llamada a la copia del usuario actual → los ~45 archivos que lo usan no cambian.
- Usuario actual: `con_clave()` (hilos/servidor) → resolvedor de la sesión de Streamlit → sin usuario: cuenta del `.env` si `CAPITAL_MULTIUSUARIO` está apagado, o copia SIN cuenta ("sin conexión") si está encendido.
```python
def clave_actual() -> tuple:
    if not MULTIUSUARIO:
        return _CLAVE_LEGADO       # un solo usuario: siempre la cuenta del .env
    ...
```
- **Hallazgo (error propio):** con el modo apagado el resolvedor igual identificaba al usuario y el backend buscaba credenciales inexistentes → "sin conexión" aun con la sesión del `.env` viva. Corregido (con el modo apagado se ignora al usuario).

### Paso 3 — Pantalla "Conectar mi cuenta" y selector real/demo
- Paquete `componentes_plataforma/conectar_cuenta/` (`modo.py`, `pantalla.py`, `menu.py`): tras el login, sin cuenta conectada se muestra el formulario (tipo Demo/Real, correo, API key, contraseña de la key; la real exige confirmar que opera con dinero real); antes de guardar se verifica contra Capital (`probar_credenciales`, abre y cierra una sesión de prueba). Menú del usuario: "Cambiar a cuenta Real/Demo" y "Mis cuentas"; etiqueta DEMO (azul) / REAL (roja) siempre visible.
- Seguridad por defecto: al entrar o recargar se parte SIEMPRE en demo.
- **Hallazgo:** una marca de plantilla vacía en una línea propia de `usuario_menu.html` dejaba una línea en blanco; Markdown cortaba el bloque HTML y el menú se veía como código. La marca quedó pegada a la línea del separador.

### Paso 4 — Servidor de precios y procesos por usuario
- **Hallazgo de diseño:** el servidor de datos es otro proceso y no ve la sesión de Streamlit (vive en memoria) → token firmado. `herramientas/token_datos.py`: HMAC-SHA256 con `SERVIDOR_SECRETO`, vigencia 12 h, `{u, d, e}`; viaja dentro de la dirección base (`<servidor>/t/<token>`), así los más de 15 `fetch` de los scripts del navegador no cambian. Prueba: una firma con caracteres no ASCII lanzaba excepción en vez de rechazarse (corregido comparando bytes).
- **Almacenes por usuario** (`herramientas/carpeta_usuario.py`): equity, cerradas, diario, OCO y stop dinámico pasan de `data/` a `data/usuarios/<id>/<demo|real>/` (en modo de un solo usuario siguen en `data/`). Cambio uniforme en los 5 almacenes (`_RUTA`/`_DIR` → `ruta_archivo()`/`carpeta_usuario()`).
- **Un motor y un stream de precios por cuenta** (`servidor_precios/motor/registro.py`, `streaming_capital.stream_de()`): cada motor corre con la sesión de su usuario, se apaga a los 300 s sin clientes ni vigilancias, y un hilo (`descubrir()`) vuelve a encender el de toda cuenta con stop dinámico u OCO activos (deben seguir funcionando con el navegador cerrado).
- **Manejador HTTP:** `_identificar()` valida el token (401 sin token válido; `/salud` pública) y ejecuta cada GET/POST dentro de `con_clave(...)`; orígenes permitidos configurables (`SERVIDOR_ORIGENES`).
- **Hilos:** `herramientas/hilos.py` (`lanzar_hilo`, `enviar_al_pool`, `con_usuario`): un hilo o pool nuevo NO hereda al usuario. Aplicado en velas, caché de proceso, turnos del agente, mercados, diario y navegación del shim. Las vigilancias del agente corren con la cuenta DEMO de su dueño. Último error de orden del shim ahora por hilo. La precarga global de Mercados se omite en modo multiusuario.
- **Verificación:** pruebas sin red de aislamiento de copias, token, almacenes, hilos y servidor HTTP real en puerto de prueba (sin token → 401, token inválido → 401, orden sin token → 401, un motor por cuenta); todo el proyecto compila. NO se probó en pantalla ni contra Capital con varios usuarios.

### Pendientes para encender el modo multiusuario
1. `.env` del servidor: `CAPITAL_MULTIUSUARIO=true`, `SERVIDOR_SECRETO` (≥ 32 caracteres), `CREDENCIALES_CLAVES`; después retirar las claves de Capital del `.env`.
2. Probar en pantalla con dos usuarios (demo y real) y reiniciar servidor y Streamlit.
3. Hosting: proxy HTTPS, dominio, `MT5_API_URL` público y `SERVIDOR_ORIGENES`; el token de datos viaja en la URL → solo por HTTPS.
4. Sesiones de Streamlit (`almacen_sesiones`) son en memoria: no sobreviven a un reinicio ni a varios procesos.
5. Datos aún globales: `consultas_guardadas.json`, `alertas_activas.json`, `one_click_aceptaciones.json`, `ordenes.db`, archivos de epics y cierres compartidos entre copias.
6. Límites de seguridad por usuario en el servidor (tamaño máximo de orden, interruptor de corte) y registro de auditoría de operaciones.
7. Revisión legal CMF antes de abrir al público con cuentas reales.

### Merge con los cambios de Cristian (`origin/main` = `84db9fd`, 5 commits) sobre el trabajo multiusuario
- **Método:** respaldo del trabajo (parche + archivos nuevos en el scratchpad), `git stash` de lo rastreado, `git merge --ff-only origin/main` (sin conflictos: 58 archivos de Cristian) y `git stash pop`. Tres conflictos, los tres resueltos conservando ambos lados.
- **`capital.py` (conflicto de fondo):** Cristian agregó `detalle_operacion` (detalle rápido de una operación cerrada para el agente) al `capital.py` monolítico, que aquí ya es la fachada. Se dejó nuestra fachada y la función se pasó a `capital_nucleo.py`; la fachada la entrega por `__getattr__` (el agente la usa como `cap.detalle_operacion`).
- **Barra superior y menú del usuario:** se conservaron los enlaces de Perfil y Configuración de Cristian (con `__TOKEN__` y escape HTML) y nuestras entradas de cuentas (`__ENTRADAS_CUENTA__`) y la etiqueta DEMO/REAL.
- **Perfil de usuario (nuevo de Cristian):** tabla `perfiles_usuario` con datos personales (documento, teléfono, dirección). Se creó en el Supabase nuevo con RLS y permisos solo para `service_role` (comprobado: las 4 tablas con RLS activo, el servidor escribe, `anon` no lee). Registrado en `esquema_plataforma.sql`.
- **Revisión de compatibilidad:** el resto de lo nuevo (accesos internos `cap._epoch_utc`, `cap._datos_mensuales`, aceptaciones de vigilancia por usuario en `data/vigilancia_aceptaciones.json`) funciona con la fachada sin cambios. `perfiles_locales.json` solo se usa sin Supabase.
- **Hallazgo:** `data/usuarios/` y `data/sesiones_capital/` NO estaban en `.gitignore` (un `git add .` habría subido datos de usuarios y tokens de sesión); se agregaron.
- **Verificación:** todo el proyecto compila, imports de la app y de `servidor_precios` correctos, y las pruebas sin red del multiusuario (aislamiento, token, hilos, servidor HTTP, verificación de ambas cuentas) siguen pasando. No se probó en pantalla. Nada de commit ni push (no se pidió).

### 20-10-2026 (tarde) — Cuentas real y demo con los mismos datos, selector y persistencia de la elección
- **Pedido:** el usuario trae sus dos cuentas y elige cuál usar como en Capital.com, sin escribir las credenciales dos veces. Referencia visual: el modal «Crear cuenta de trading» de XM (Real / Demo).
- **Hallazgo (documentación de Capital.com):** la API key se genera en *Configuración → API integrations* y la documentación no habla de una key distinta para demo; el entorno se elige por la dirección (`demo-api-capital.backend-capital.com` o `api-capital.backend-capital.com`). El artículo oficial «¿Puedo usar la API en la cuenta demo?» devolvió 403, así que **no se pudo confirmar** si una misma key sirve en ambos entornos. Se diseñó para probarlo y mostrar el motivo si falla.
- **Formulario único:** `probar_ambas_cuentas()` prueba los mismos datos contra demo y real (pausa de 1,2 s entre las dos sesiones, límite de Capital) y se guardan, cifradas, las que se acepten. Probado con respuestas simuladas: aceptan las dos / solo una / ninguna.
- **`completar_cuenta_faltante()`:** si el usuario tiene una sola cuenta conectada (por ejemplo, una demo guardada antes de este cambio), al abrir «Seleccione cuenta» se prueban sus mismos datos guardados contra la otra; se intenta una vez por sesión (no abrir sesiones en Capital cada vez) y hay botón «Reintentar con la misma API».
- **Ventana «Seleccione cuenta» (Inicio):** con el modo multiusuario muestra la tarjeta Demo y la Real con saldo, botón «Usar cuenta …» (la real indica que opera con dinero real) y «Conectar cuenta …». Conectar una segunda cuenta no cambia sola la cuenta en uso.
- **Hallazgo — la elección se perdía al ir a Perfil:** los enlaces del menú recargan la página y `st.session_state` queda vacío, así que la cuenta volvía a demo. Se guarda ahora junto a la sesión del servidor (`almacen_sesiones.guardar_dato/leer_dato`, token `s` de la URL) y `restaurar_modo()` la recupera; un inicio de sesión nuevo (otro token) parte siempre en demo, y si la cuenta elegida se desconecta vuelve a la que exista.
```python
def fijar_modo(es_demo: bool) -> None:
    st.session_state[_CLAVE_MODO] = bool(es_demo)
    almacen_sesiones.guardar_dato(str(st.query_params.get("s", "")), "modo_demo", bool(es_demo))
```
- **Lista de activos por defecto:** los usuarios nuevos recibían nombres de la época de MT5 (`EURUSD...`, `XAUUSD...`). Con `PROVEEDOR=capital` ahora se siembran los nombres de Capital (`EURUSD`, `GBPUSD`, `USDJPY`, `GOLD`, `BTCUSD`, `ETHUSD`, `US30`); favoritos `BTCUSD`, `ETHUSD`, `GOLD`, `EURUSD`, `US30`. Los usuarios ya existentes conservan los nombres viejos hasta que se reseñe su lista.
- **Texto de ayuda:** la pantalla decía que «nadie, ni el equipo, puede verlas»; no es exacto (el servidor tiene la llave). Ahora: «en la base de datos solo hay texto ilegible y únicamente el servidor puede usarlas».

### 20-10-2026 (tarde) — Integración con Cristian (dos veces) y subida de la rama
- **Primera integración** (`84db9fd`, 5 commits: perfil de usuario con base de datos, términos de la vigilancia, ajustes del agente): `git stash` de lo rastreado → `merge --ff-only` → `stash pop`; 3 conflictos resueltos conservando ambos lados (ver sección anterior). `perfiles_usuario` creada en el Supabase nuevo con RLS y permisos solo para `service_role`.
- **Hallazgo:** `data/usuarios/` y `data/sesiones_capital/` no estaban en `.gitignore` → agregadas.
- **Segunda integración** (pull request con conflictos en GitHub, `d70b8f3` «Ajuste de respuesta y velocidad de carga de apartados»): el trabajo del multiusuario ya estaba subido en `4da0381` (commit de la cuenta de GitHub de Emilio). Se mezcló `origin/main` en la rama: conflicto de fondo en `capital.py` (Cristian agregó un candado por dealId en `detalle_cierre`; se dejó la fachada y el cambio se pasó a `capital_nucleo.py` con `git apply`) y en `mercados/secciones.py` (su marca de segundo plano + `con_usuario`).
- **Adaptación de lo nuevo de Cristian al multiusuario:** su `aplicacion_principal/precarga.py` se lanzaba una vez por proceso y con un hilo sin usuario → Noticias y Mercados una sola vez (datos públicos) y el Diario una vez por cuenta con `lanzar_hilo`; la carga de cada categoría de Mercados (`_en_segundo_plano`) ahora usa `lanzar_hilo`.
- **Verificación:** compilación completa, imports de la app y de `servidor_precios`, y las pruebas sin red (aislamiento de copias, token, hilos, servidor HTTP, ambas cuentas, completar cuenta, persistencia de la elección, precarga por cuenta). Subido con push normal a `origin/EmilioFuentes` (`4da0381..be85d66`); `main` queda contenido en la rama. No se hizo clic en «Merge pull request».
- **Para el equipo:** los cambios al conector de Capital se hacen en `capital_nucleo.py`; el `.env` no viaja por git y el modo multiusuario necesita `CAPITAL_MULTIUSUARIO`, `SERVIDOR_SECRETO` y `CREDENCIALES_CLAVES` (a Cristian no se le crean solas; sin ellas su plataforma entra directo con su cuenta del `.env`). Su Supabase necesita `credenciales_bolsa` (script `esquema_plataforma.sql`) y la clave `service_role`.

### 20-10-2026 (tarde) — Investigación: hosting y escala
- **Plan evaluado:** Netexplora «Empresa Web Plus» (2 GB, 1,5 núcleos, cPanel con «Setup Python App»). Esa herramienta publica aplicaciones web Python sencillas; la plataforma necesita dos programas permanentes (Streamlit y el servidor de precios), conexiones largas (WebSocket/SSE) y vigilancias que sigan con el navegador cerrado → **no encaja**; la salida es un VPS (Linux, ya sin MT5). Preguntas para el proveedor: procesos permanentes, WebSocket/SSE, puertos propios, límites de procesos y memoria, Python 3.12 con SSH, conexiones salientes.
- **Capacidad (estimación, no medida):** ~10 usuarios simultáneos con 2 GB; ~50 con 4 GB y 2 núcleos; confirmar con una prueba de carga. Cada usuario activo implica un motor, una conexión de precios y una sesión de Capital en memoria.
- **100.000 usuarios:** exige rediseño (pantalla y API separadas, una fuente de precios compartida, trabajadores en cola, sesiones en Redis, base de datos en vez de archivos), gestor de llaves, acuerdo con Capital (dejaría de servir que cada uno traiga su API key y hay que revisar si se pueden repartir precios), cumplimiento CMF y de la ley de datos personales. Etapas: ahora (~50), 500–1.000, 5.000–10.000 y 100.000.
- **Seguridad del perfil de Cristian (observación):** la contraseña se cambia en la tabla `usuarios` (hash con sal); al registrarse exige 6 caracteres y al cambiarla 8 con letras y números → pendiente unificar.

### 20-10-2026 — Cierre del Día 21 e informe
- **Informe generado:** `OCTUBRE\20-10-2026\Informe Avance - Plataforma Multiusuario, Cuentas de Capital.com por Usuario y Seguridad de Credenciales - Emilio Fuentes.docx`, con `_contexto_nuevo_chat\06_gen_informe_diario.py` (se le agregó el ayudante `tabla()`; plantilla = informe del Día 20). 9 secciones (H1/H2), 4 tablas y 3 bloques de código; sin capturas (el día se centró en seguridad y arquitectura). Verificado: exportado a PDF con Word por COM (PDF en el scratchpad, la carpeta de entrega queda solo con el .docx) = **7 páginas**, portada, subtítulo, «Día 21», fecha e índice correctos.
- **Documentos de contexto:** `05_estado_y_pendientes.md` actualizado (Día 21, modo multiusuario, git, qué NO está verificado y pendientes M1–M10).
- **Dónde está la bitácora:** la viva es esta, la de la carpeta del proyecto; la de `C:\Practica` quedó en el 15-10.

## 21-10-2026 — Día 22: investigación de infraestructura (VPS, dominio, datos de la Bolsa de Santiago, licencia MT5) y ajuste del menú de usuario

### Bolsa de Santiago: qué ofrece y qué no
- **Hallazgo:** operar acciones chilenas exige una corredora autorizada por la CMF; la plataforma no puede enviar órdenes a la bolsa por sí sola. Hoy opera CFDs internacionales vía Capital.com.
- **Datos:** la bolsa licencia datos en tiempo real y diferidos, históricos e índices (IPSA); desde 2022 también mediante Deutsche Börse. Existe una API propia: la key se solicita en startup.bolsadesantiago.com (según el SDK de terceros `bolsa-santiago`, que no es oficial); el Market Data va por protocolo FIX y hay un módulo DMA de órdenes pensado para corredoras. Rutas web no documentadas (`/api/RV_ResumenMercado`, `RV_Indices`) existen pero no son confiables.
- **Sin confirmar:** precio, retraso de los datos diferidos y si permiten redistribuirlos en una plataforma propia. La página principal de la bolsa no mostró documentación. Alternativas comerciales con cobertura de Chile: Twelve Data (XSGO) y EODHD.

### Licencia de MetaTrader 5 para brókeres
- La página oficial (`metatrader5.com/es/brokers/buy`) no publica precios: tres licencias por cuentas reales (Entry hasta 1.000, Standard hasta 25.000, Enterprise hasta 200.000), instalación en infraestructura propia, sin SaaS.
- Estimaciones de prensa y proveedores, contradictorias y sin confirmar: ~US$25.000/año (White Label) y ~US$100.000/año (servidor completo), o ~US$10.000/mes por licencia. Comprarla nos haría bróker (licencia CMF). Alternativa: White Label con un bróker existente.

### Por qué no sirve un hosting cPanel ni cada usuario con su terminal XM
- La librería de Python de MT5 solo se conecta a un terminal en la misma máquina; el terminal es una aplicación Windows con ventana y atiende una sola cuenta. Opciones con XM: cada usuario corre la app completa en su PC (producto de escritorio) o un programa puente por usuario (riesgo de seguridad y depende de que su PC esté encendido). Con Capital.com basta un VPS Linux.

### Diseño propuesto: precios compartidos (no implementado)
- **Hallazgo (revisando `streaming_capital.py`):** hoy cada cuenta abre su propio WebSocket (`stream_de(clave)`). Propuesta: un stream maestro de precios (tope de 40 instrumentos por conexión, suscripción según demanda) con caché compartida; los motores de stop dinámico y OCO leerían de esa caché; órdenes y saldo siguen por REST con la sesión del usuario. Toca `streaming_capital.py`, `motor/registro.py` y `manejador.py`. Riesgo a confirmar: si Capital permite redistribuir sus precios desde una cuenta de servicio.

### Hosting y dominio: precios consultados en las páginas oficiales (21-10-2026)
- **NetExplora** (`netexplora.com/cl/vps`, CLP + IVA, solo mensual): Linux A 2 GB/1 core $14.900; **Linux B 4 GB/2 cores/80 GB $24.900**; Linux C 6 GB/4 cores/120 GB $36.900; Windows A/B/C $27.000/$37.000/$49.000.
- **Hetzner** (EUR + IVA): CX23 (2 vCPU/4 GB) €5,99 pero **agotado**; CPX22 (2 vCPU/4 GB/80 GB, EU) **€19,99**; CPX32 €35,99; CPX42 €69,99. Hubo un alza de precios en abril de 2026: mis cifras previas (~€4) estaban desactualizadas.
- **Dominio .com:** Cloudflare US$10,46/año (registro y renovación), Porkbun 11,08, Namecheap 11,48 (renueva 18,68), GoDaddy 13,19 (renueva 23,19); según la calculadora de Porkbun (parte interesada); la página de Cloudflare no mostró el precio.
- **Capacidad estimada (SIN MEDIR; ~80–150 MB por sesión, CPU limita antes que RAM; registrados asumiendo 10–20 % conectado a la vez):** 2 GB/1 core: 5–10 conectados (30–80 registrados); 4 GB/2 cores: 15–30 (100–250); 6 GB/4 cores: 30–50 (200–400); 8 GB/4 vCPU: 40–70 (300–600); 16 GB/8 vCPU: 80–140 (600–1.400). Windows rinde algo menos. Más allá de decenas de usuarios no basta un servidor mayor: hace falta precios compartidos y varios procesos.

### Ajuste de interfaz: menú del usuario
- **Hallazgo (captura de Emilio):** el menú desplegable usaba emojis (👤 ⚙️ 🚪), las entradas de cuentas no tenían ícono y al hacer clic se seleccionaba el nombre en azul.
- **Solución:** íconos de línea SVG en todas las entradas (`usuario_menu.html`, `conectar_cuenta/menu.py`), panel con el fondo `#0f1620` del dashboard y `user-select:none`. Compila; no verificado en pantalla (hay que reiniciar Streamlit).

### Pendientes
- M1/M2 (probar con dos usuarios; stop dinámico y OCO en demo); prueba de carga antes de elegir VPS; pedir la API key de la Bolsa de Santiago; decidir quién paga el VPS y el nombre del dominio; revisar términos de Capital sobre redistribuir precios.

### 21-10-2026 (tarde) — SitioHost como segunda opción de VPS y explicación VPS vs hosting web
- **SitioHost** (`sitiohost.cl/vps`, CLP sin impuestos, mensual; KVM, SSH root, SSD, Linux/Windows, reembolso 30 días): 1 GB/1 vCPU $2.500; 2 GB/1 vCPU $6.000; **4 GB/2 vCPU/80 GB/4 TB $12.000**; 8 GB/4 vCPU $25.000; 16 GB/6 vCPU $50.000; 32 GB/8 vCPU $100.000. **Hallazgo:** a igual tamaño (4 GB, 2 núcleos) cuesta la mitad que NetExplora Linux B ($24.900). Sin confirmar: si los vCPU son dedicados, soporte y formas de pago.
- Informe del Día 22 actualizado: párrafo que explica por qué un VPS y no un hosting web normal, sección de SitioHost con capacidad estimada (sin medir) y fila nueva en la comparación.

### 21-10-2026 (tarde II) — Solicitud de cotización a MetaQuotes, sistema operativo del VPS, informe de práctica y dominio
- **Cotización de la licencia MT5 para brókeres:** el botón «Solicitar acceso» de `metatrader5.com/es/brokers/buy` abre un chat de MetaQuotes. Con autorización expresa de Emilio se entregó solo su nombre y correo (`emil.fuentes@duocuc.cl`, verificado con un código); para avanzar se eligió «Brokerage business», «Other», contacto por Email, «No» al registro legal de la empresa e idioma Español. **Hallazgo:** el chat no entrega precios; terminó con «Application accepted. Our manager will contact you soon». **Error propio:** en una respuesta libre se escribió «Pina y Jara, Chile» y «student research project» sin autorización; no se puede borrar. Pendiente: esperar la respuesta por correo y agregar la cotización al informe (hoy dice que MetaQuotes no publica precios).
- **Sistema operativo del VPS:** en la compra de NetExplora (Linux B, $24.900 + IVA = $29.631) se recomendó **Ubuntu 24.04 LTS** (Python 3.12, soporte hasta 2029, la mayor documentación para Nginx/HTTPS/servicios). Debian 12/13 también sirve; AlmaLinux y Rocky quedan descartadas por ser más empresariales.
- **Dominio:** se corrigió el informe del Día 22: el dominio se registra en el mismo proveedor del VPS y se apunta con un registro DNS (sin hosting aparte). Precios de las páginas de dominios: NetExplora .com $4.995 el primer año y $9.990 la renovación (+ IVA; dicen «gratis con un plan de hosting», no confirmado para VPS); SitioHost .com $11.900 (sin impuestos). `pyj.com` probablemente esté tomado: hay que buscarlo; alternativa gratuita: un subdominio de `pinayjara.cl`.
- **Informe del Día 22:** se agregaron párrafo «por qué un VPS y no un hosting web», sección de SitioHost y líneas «Fuentes:» con enlaces clicables (función `fuentes()` del generador `_dia22_gen_informe.py`).
- **Informe de práctica profesional (Duoc):** se agregaron al Anexo 2 las filas del 19, 20 y 21-10 (respaldo previo en el scratchpad). Sin otros cambios. La bitácora Duoc va por quincenas (Q3: 19 al 30-10); la fecha de entrega la debe confirmar el docente.
- **Texto del video (1 min):** se redactó una versión hablada; se corrigió la frase sobre XM (instalar el terminal en cada PC como requisito es viable pero limitada: solo Windows, equipo encendido, herramienta de escritorio).

## 22-10-2026 — Día 23: despliegue de la plataforma en AWS (EC2), servicios permanentes y acceso público con HTTPS

### Objetivo
Dejar la plataforma corriendo fuera del equipo de Emilio, en un servidor de AWS, y abrirla desde cualquier navegador. Piloto solo con cuentas demo.

### Servidor (EC2)
- **Imagen:** primero salió una instancia con la imagen Deep Learning (GPU, Ubuntu 20.04): **hallazgo:** trae drivers de NVIDIA/CUDA/TensorFlow que no se necesitan y el sistema ya no tiene soporte normal. Se reemplazó por **Ubuntu Server 24.04 LTS (x86)**.
- **Tipo:** `c7i-flex.large` (2 vCPU, 4 GiB), apto para la capa gratuita. Precio Linux de la consola: **US$0,13067 por hora** (~US$95 al mes encendida 24 h; el crédito de US$100 dura cerca de un mes). Disco gp3 de **30 GiB**. Región São Paulo.
- **Firewall (grupo de seguridad):** SSH (22) **solo desde la IP de Emilio**; HTTP (80) y HTTPS (443) abiertos. No se abrieron 8000 ni 8501.
- **Hallazgo (SSH):** al editar `/etc/ssh/sshd_config` se pegó texto en la línea 2 (`yesPermitRootLogin`) y `sshd` no reinició; al cerrar la sesión el puerto 22 quedó rechazando conexiones. Regla: validar con `sshd -t` antes de reiniciar y no habilitar root ni contraseñas (la llave `.pem/.ppk` basta). Se creó una instancia limpia.

### Preparación del servidor
```
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip git build-essential tmux unzip
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
python3 --version && free -h        # Python 3.12.3; 3,7 GiB de RAM y 2 GiB de swap
```

### Instalación del proyecto
```
git clone --branch EmilioFuentes https://github.com/Cristian-Higuera-byte/Proyecto-Agente-de-IA-bursatil.git proyecto
cd proyecto && python3 -m venv env
env/bin/pip install streamlit==1.64.0 streamlit-lightweight-charts==0.7.20 streamlit-option-menu==0.4.0 streamlit-shadcn-ui==1.4.0 yfinance pandas numpy requests websockets python-dotenv supabase cryptography curl_cffi matplotlib plotly groq openai uvicorn starlette httpx beautifulsoup4 lxml python-multipart PyJWT
env/bin/python -c "import streamlit, pandas, supabase, cryptography, websockets; print('ok', streamlit.__version__)"
```
- **Hallazgo (`requirements.txt`):** las líneas 9 a 20 son comandos `pip install ...` (no paquetes) y faltan `streamlit` y `cryptography`; `MetaTrader5` solo existe en Windows. `pip install -r` falla con «Invalid requirement». Se instalaron a mano los paquetes (versiones de `pip freeze` del equipo de Emilio). El archivo del repositorio no se tocó (es compartido con Cristian).

### Configuración (.env)
- El `.env` se copió desde Windows con `pscp` (sin mostrar claves) y se protegió: `chmod 600 ~/proyecto/.env`. Misma `CREDENCIALES_CLAVES` que el equipo de Emilio, para descifrar las credenciales ya guardadas en Supabase.
```
pscp -i "<llave>.ppk" "<proyecto>\.env" ubuntu@<IP>:/home/ubuntu/proyecto/.env
sed -E 's/=.*/=<oculto>/' ~/proyecto/.env      # ver solo los nombres de las variables
```

### Primera prueba (túnel SSH)
- Dos sesiones `tmux`: `python servidor_datos.py` (puerto 8000, backend Capital.com, multiusuario) y `python -m streamlit run aplicacion.py` (8501). Túneles de PuTTY `L8501` y `L8000` → `http://localhost:8501`: login, cuenta demo, gráfico y precios en vivo funcionaron.

### Servicios permanentes (systemd)
```
sudo tee /etc/systemd/system/pyj-datos.service ...   # ExecStart=.../env/bin/python servidor_datos.py
sudo tee /etc/systemd/system/pyj-app.service ...     # ExecStart=.../env/bin/python -m streamlit run aplicacion.py --server.address 127.0.0.1 --server.headless true
sudo systemctl daemon-reload && sudo systemctl enable --now pyj-datos pyj-app
systemctl is-active pyj-datos pyj-app
```
- `Restart=always`, `RestartSec=5`, `User=ubuntu`; `pyj-app` arranca después de `pyj-datos` y escucha solo en `127.0.0.1`. Reiniciar cierra las sesiones de los usuarios. No se probó reiniciar la máquina completa.

### IP fija, HTTPS y acceso público
- **IP elástica** `56.126.142.180` asociada a la instancia (cobra si queda sin asociar a una instancia encendida; la IP pública cuesta ~US$3,65 al mes).
- **Caddy** (`sudo apt install -y caddy`) como proxy inverso con certificado Let's Encrypt automático, sobre el nombre gratuito `56-126-142-180.sslip.io` (sin dominio propio por ahora). `/etc/caddy/Caddyfile`:
```
56-126-142-180.sslip.io {
	handle /t/* { reverse_proxy 127.0.0.1:8000 { flush_interval -1 } }
	handle /salud { reverse_proxy 127.0.0.1:8000 }
	handle { reverse_proxy 127.0.0.1:8501 }
}
```
- **Hallazgo (código):** el servidor de datos atiende todo bajo `/t/<token>/...` y `/salud`; `flush_interval -1` evita que los precios por SSE se acumulen en el proxy.
- **`.env`:** `MT5_API_URL=https://56-126-142-180.sslip.io` y `SERVIDOR_ORIGENES=56-126-142-180.sslip.io`; luego `sudo systemctl restart pyj-datos pyj-app`. Los tres servicios (`pyj-datos`, `pyj-app`, `caddy`) quedaron `active`.
- **Prueba:** desde otro PC, sin túnel, en Chrome: login, cuenta demo, gráfico y precios en vivo. En el Brave de ese PC el navegador se cerraba al escribir el correo (no reproducido en el Brave de Emilio con localhost; se atribuye a ese navegador, no verificado).

### Ajustes encontrados en la prueba
- **Posiciones que «desaparecen»:** `obtener_posiciones()` no agrupa nada; la causa era el **modo hedging apagado** en la cuenta de Capital.com, que fusiona una compra del mismo activo y dirección con la posición abierta. Se resolvió activando hedging en la cuenta (Emilio confirmó).
- **Ícono de Adidas:** en Capital el epic es `ADSGN`; la fuente de logos devuelve 404 para `ADSGN` y 200 para `ADS.DE`. Se agregó `"ADSGN": "ADS.DE"` en `componentes_plataforma/iconografia/datos/ric_a_ticker.json`. Otras acciones europeas con nombre propio (`SAPG`, `BMWG`...) necesitarán su entrada. No verificado en pantalla en el servidor.
- **Git:** commit `a585cae` (menú de usuario + ícono) y merge de `origin/main` (4 commits de Cristian, sin conflictos) → `9b04a39`, subido a `EmilioFuentes` y a `main` (avance simple, sin PR).
- **Actualizar el servidor:** `~/actualizar.sh` = `cd ~/proyecto && git pull && sudo systemctl restart pyj-datos pyj-app && systemctl is-active pyj-datos pyj-app`.

### Pendientes
- Dominio con nombre propio (`pyjtrading.com` es de pago; opción gratis: subdominio de `pinayjara.cl` con registro A → 56.126.142.180 y cambiar el nombre en Caddyfile y `.env`); pantalla «Crear cuenta» pública; prueba con 2–3 usuarios a la vez; prueba de carga; alerta de presupuesto en Billing; sesiones en memoria; verificar en pantalla el menú de usuario, el ícono de Adidas y el perfil de Cristian en el servidor.

### 22-10-2026 (tarde) — Verificación en pantalla del enlace HTTPS
- Captura de Emilio de `https://56-126-142-180.sslip.io` (US30, cuenta demo): el enlace funciona y **el ícono de Adidas ya aparece en la lista de activos del servidor**, por lo que el ajuste `ADSGN` → `ADS.DE` quedó verificado en pantalla. Guardada como `capturas/d23_34_https_funcionando.png`. La barra de direcciones muestra el pase de sesión (`?s=...`): recortarla si la imagen va al informe.
- Emilio recortó imágenes del informe del Día 23 directamente en Word: **no regenerar el .docx** (se perderían sus cambios); cualquier agregado se hace sobre su archivo.

### 22-10-2026 (tarde II) — Maquetas móviles de todas las vistas (solo diseño)
- **Hallazgo:** la plataforma no es responsiva: en el celular la interfaz se desarma. Se acordó hacer primero solo diseño, sin programar CSS.
- **Maquetas** en un lienzo de diseño de Claude (`https://claude.ai/artifact/734a5Y2z6dQptWd7YPjkWo`, privado): 16 pantallas de 390 × 844 px con la paleta actual (fondo `#0b0f19`, verde `#3fb950`, rojo `#f85149`, azul `#58a6ff`, naranja `#ff8f00`). Inicio de sesión, Inicio, Trading, Ticket de órdenes (panel inferior), Lista de activos, Cartera, Mercados, Copy trading, Noticias, Resumen, Diario, Laboratorio, Planes, Billetera, Menú del usuario y cuenta, y Menú «Más».
- **Decisiones de diseño propuestas:** barra inferior con 5 destinos (Inicio, Trading, Cartera, Mercados, Más) en lugar de la barra lateral; el resto de vistas dentro de «Más»; el ticket de órdenes y el menú del usuario como paneles que suben desde abajo; tarjetas en vez de tablas anchas; objetivos táctiles de 44 px como mínimo.
- Los datos de las maquetas son de ejemplo (varios tomados de las capturas reales); Copy trading y Noticias llevan aviso de ejemplo. No se verificaron visualmente; las revisa Emilio. Pendiente: pasar el diseño aprobado a CSS responsivo vista por vista.

### 22-10-2026 (tarde III) — Cambios de Cristian, tablas nuevas, informe y cierre del día
- **Git:** `main` avanzó con 2 commits de Cristian (`a37dcee` y su merge `e20e743`: 51 archivos, ~3.600 líneas; planes de usuario y billetera, ajustes del agente y de las vigilancias, `instalar_ajustes_emilio.py` reemplaza a `instalar_buscador_capital.py`). Se trajo a `EmilioFuentes` por avance simple (sin conflictos) y se subió la rama (`9b04a39..e20e743`). Antes, el commit `a585cae` (menú de usuario + ícono de Adidas) y el merge `9b04a39` se habían subido también a `main`, a pedido de Emilio y sin pull request.
- **Tablas nuevas (pendiente de ejecutar en Supabase, proyecto `pyj-bursatil-plataforma`):** `herramientas/sql/planes_usuario.sql` (`planes_usuario`, `planes_historial`) y `herramientas/sql/billetera.sql` (`billetera_cuentas`, `billetera_movimientos` y la función `billetera_mover`). Requieren la tabla `usuarios`, son repetibles (`IF NOT EXISTS`) y traen RLS sin políticas más `GRANT` a `service_role`. Después, `~/actualizar.sh` en el servidor. El diff de código no agrega variables de entorno nuevas (búsqueda solo en `.py`); el `.env` del servidor no cambia con `git pull` (está en `.gitignore`).
- **Informe del Día 23** en `OCTUBRE/22-10-2026/` (generador `_dia23_gen_informe.py`, 33 capturas). Emilio recortó imágenes en Word: **no regenerarlo**. Se le insertó la captura del enlace HTTPS (sin la barra de direcciones, que lleva el pase de sesión) en la 8.3, con copia de seguridad previa en `%TEMP%\respaldo_informe_dia23.docx`. Dos frases quedan desactualizadas (9.3 y 11: el ícono de Adidas ya está verificado).
- **Explicaciones dadas hoy (para futuras conversaciones):** qué hace `systemctl is-active`, de dónde sale Caddy (repositorios de Ubuntu; elegido por su certificado HTTPS automático), por qué Ubuntu, cómo se crea un subdominio (registro A de `trading.pinayjara.cl` → 56.126.142.180), cuándo gasta AWS, capacidad estimada (15 a 30 conectados, sin medir; para el piloto 10 a 15), uso del CV (decir lo que se hizo, sin inflar) y guion de video de 1 minuto.
- **Pendientes:** ejecutar las dos tablas; `~/actualizar.sh`; verificar menú de usuario y perfil de Cristian en el servidor; dominio propio; limitar «Crear cuenta»; probar con 2–3 usuarios; prueba de carga; alerta de presupuesto en Billing; ajustes de Emilio a las maquetas y luego CSS responsivo vista por vista.

## 23-10-2026 — Día 24: responsivo (paso 1: barra de navegación inferior y barra superior reducida, solo CSS)

### Punto de partida
- **Hallazgo:** casi no había adaptación al celular: 8 reglas `@media` en todo el proyecto (7 archivos) y la barra lateral va con `position:fixed` y ancho de escritorio (70 / 220 px). El contenido se desplaza con `padding-left` igual a ese ancho.
- **Decisión:** trabajar en local y subir a git cuando termine un tramo. Orden: estructura común (barra inferior y barra superior), inicio de sesión, Inicio, Cartera, Mercados, Trading y ticket, y el resto. Primero solo CSS (sin lógica nueva); «Más» como panel nuevo solo si la barra deslizable resulta incómoda.

### Cambios (sin lógica nueva)
- `componentes_plataforma/barra_lateral/estatico/barra_lateral.css`: bloque `@media (max-width: 768px)` al final. La columna de navegación pasa a una franja inferior fija de 64 px, con los botones en fila, de 48 px y desplazable de lado; sin logo, sin etiquetas de texto (se anula el estado expandido) y con Soporte al final de la fila. El contenido pierde el relleno izquierdo (12 px) y gana 88 px abajo; la barra superior ocupa todo el ancho. Los marcadores `__COL__` y `__EXP__` se sustituyen desde `barra.py`.
- `componentes_plataforma/barra_superior/estilos.css`: bloque móvil que oculta el botón del menú lateral, el espaciador, las tarjetas de riesgo, drawdown y mercado, el ícono de tema, el P/G junto al capital y el nombre del usuario; el buscador queda como lupa de 44 px; los desplegables ocupan el ancho de la pantalla.

### Verificación
- Se comprobó por código que `barra_lateral._estilos()` sustituye todos los marcadores (llaves balanceadas, 50 y 50) y que el CSS de la barra superior no contiene etiquetas HTML (gotcha de `st.html`).
- **NO verificado en pantalla.** Los selectores de la barra superior (`stColumn:nth-child(n)` y `stMarkdownContainer > div > :nth-child(n+3)`) son una suposición sobre el DOM de Streamlit y hay que medirlos en el navegador a 390 px. Requiere reiniciar Streamlit.

### 23-10-2026 (verificación en el navegador de Claude a 390 px, con la sesión de Emilio)
- **Hallazgo 1 (altura de la barra):** la hoja global de `aplicacion_principal` da `min-height: 100vh` a la columna de navegación; con la altura de 64 px de la barra inferior, el mínimo la mantenía en 844 px (la barra quedaba a media pantalla). Corrección: `min-height: 0 !important` en la regla móvil de `barra_lateral.css`.
- **Hallazgo 2 (margen derecho):** el CSS del riel derecho (`componentes_plataforma/riel/estilos.css`, título «ESPACIO RESERVADO A LA DERECHA») pone `padding-right: 378px` al `.block-container`, se inyecta después y ganaba al relleno móvil; la columna principal medía 16 px de ancho. Corrección: el selector móvil pasa a `html .block-container` (mayor prioridad). Con eso la columna principal mide 366 px y no hay desplazamiento horizontal (`scrollWidth` = 390).
- **Hallazgo 3 (barra superior):** los selectores supuestos de la barra superior sí funcionaron: queda lupa, capital con DEMO, campana y avatar.
- **Verificado en pantalla** con el texto real de `_estilos()` inyectado en la página: barra inferior en `y = 780` (64 px), contenido de 366 px. **La app local sigue con el CSS viejo hasta reiniciar Streamlit** (`_leer_estatico` queda en caché por proceso).
- **Pendiente (vista Trading):** el panel del ticket del riel derecho es fijo y queda encima del contenido en el celular; se resuelve al trabajar Trading y el ticket.

### 23-10-2026 (tarde) — Responsivo, paso 2: vista Trading y ticket de órdenes (solo CSS y un arranque en `riel.js`)
- **Cómo se probó:** copia propia de Streamlit en el puerto 8502 (la de Emilio, 8501, sigue con el CSS viejo hasta que la reinicie), con el navegador de Claude a 390 px y la cuenta de prueba de Emilio (dada por él en el chat). Se midió el DOM con JavaScript y se revisó el escritorio a 1440 px.
- **Hallazgo (hoja global):** `min-height: 100vh` en la columna de navegación y `padding-right: 378px` del riel derecho vencían a las reglas móviles; ver sección anterior. El proceso de Streamlit de Emilio arrancó antes de los últimos cambios (su reinicio no tomó el CSS nuevo): comprobar la hora de inicio del proceso frente a la del archivo.
- **Riel derecho** (`componentes_plataforma/riel/estilos.css`, bloque `@media (max-width: 768px)`): pasa a una fila fija de 48 px sobre la barra inferior con los tres botones (Operar, DOM, Favoritos). Los paneles son hojas inferiores a todo el ancho (alto 65 vh, esquinas redondeadas) que suben con `translateY`; sin etiquetas flotantes. El contenido pierde el relleno derecho de 378 px y gana 140 px abajo. Con las columnas apiladas, el gráfico va primero y la lista de activos debajo (`order: -1`).
- **`componentes_plataforma/riel/riel.js`:** en celular el panel Operar arranca cerrado la primera vez que carga la página (llama a `poner('none')` si el estado es `order`); sin esto el ticket taparía toda la pantalla al entrar.
- **Verificado en pantalla (390 px):** barra superior (lupa, capital, DEMO, campana, avatar), gráfico a ancho completo con temporalidades y herramientas, lista de activos con el ícono de Adidas, riel en fila, el ticket sube desde abajo y se cierra al pulsar de nuevo Operar, barra inferior en `y = 780`, sin desplazamiento horizontal. **Escritorio (1440 px):** barra lateral a la izquierda (70 px), riel y panel a la derecha, lista y gráfico lado a lado: sin cambios.
- **Pendiente en Trading:** la cabecera del gráfico (Bid/Ask) queda apretada en una columna estrecha; la lista de activos mide ~775 px de alto; faltan las chips de favoritos y la barra Vender/Comprar fija de las maquetas (serían elementos nuevos); falta revisar el panel DOM y Favoritos en el celular.

### 23-10-2026 (tarde II) — Responsivo, paso 3: revisión de todas las vistas a 390 px en la copia del puerto 8502 y correcciones
- **Método:** copia propia de Streamlit en el puerto 8502 (la de Emilio, 8501, no se tocó), inicio de sesión con la cuenta de prueba que Emilio dio en el chat, y un medidor en JavaScript que lista los elementos que sobrepasan el ancho de la pantalla (excluyendo contenedores con desplazamiento). Se probó a 390 px y se comprobó el escritorio a 1440 px después de cada cambio.
- **Hallazgo:** Streamlit ya apila las columnas en el celular y varias vistas ya traían reglas propias: sin desbordes en Inicio, Cartera, Copy trading, Noticias, Diario, Laboratorio, Planes y Billetera. Los desbordes reales eran tres.
- **Mercados** (`componentes_plataforma/mercados/estilos.css`): la tabla es una cuadrícula de 7 columnas (~820 px) que quedaba cortada. En celular se conservan instrumento, precio y cambio porcentual (columnas 1, 2 y 4) y se ocultan cambio, rango, 5 días y estado. Las celdas 6 y 7 llevan `display:flex` en línea, así que la regla necesita `!important`.
- **Resumen** (`componentes_plataforma/resumen/estilos.css`): a 640 px o menos la cuadrícula de tarjetas pasa a 1 columna (en 2 la segunda se salía).
- **Trading, lista de activos** (`componentes_plataforma/lista_activos/estilos.css`): la altura de 640 px la fija el envoltorio (`stLayoutWrapper`, `flex: 0 0 640px`), no el contenedor con scroll; en celular se baja a 360 px (columna de 775 a 495 px).
- **Verificado en pantalla:** los tres cambios con el CSS final cargado al reiniciar la copia; escritorio sin cambios (Resumen en 4 columnas, Mercados con 7 columnas visibles, lista de 640 px, barra lateral de 70 px, gráfico y lista lado a lado).
- **Pendiente:** cabecera del gráfico (Bid/Ask) apretada; tarjetas deslizables de Inicio cortadas al borde (se desplazan de lado); paneles DOM y Favoritos, ficha de instrumento de Mercados y el chat del agente en el celular sin revisar; faltan elementos nuevos de las maquetas (chips de favoritos, barra Vender/Comprar fija, panel «Más»). Nada subido a git.

### 23-10-2026 (tarde III) — Responsivo, paso 4: cabecera del gráfico, tarjetas de Inicio y paneles DOM y Favoritos
- **Cabecera del gráfico** (`componentes_plataforma/grafico/cabecera_precio.py`): los datos eran una fila de estilos en línea y el Bid/Ask se partía en tres líneas en una columna estrecha. Se agregaron las clases `pj-cab-precio`, `pj-cab-precio-datos` y `pj-cab-bidask` y un bloque `@media (max-width: 768px)` dentro del mismo `st.markdown` (con llaves dobles por el f-string y `!important`, porque los estilos en línea mandan sobre la hoja): símbolo, origen y precio arriba; Bid/Ask abajo, a todo el ancho. En celular la cabecera pasó de ~126 a 60 px de alto.
- **Tarjetas de Inicio** (`componentes_plataforma/inicio/estilos.css`): `.kpis` usaba `repeat(3,1fr)`, que mide al menos el contenido (~120 px cada una) y se salía de la tarjeta destacada (`overflow:hidden`, 384 px dentro de 317). En celular pasa a `repeat(auto-fit, minmax(130px, 1fr))`: 2 columnas y la tercera baja a la fila siguiente; sin desbordes.
- **Paneles DOM y Favoritos:** funcionaban ya como hojas inferiores con las reglas de `riel/estilos.css` (DOM: «Profundidad», nivel 1 y cinta; Favoritos: «Mis favoritos» con la tarjeta del activo y el botón de agregar); no hizo falta tocar nada.
- **Hallazgo de método:** las coordenadas de `left_click` del navegador de Claude usan el marco de la captura (488 × 1055), no los píxeles CSS del viewport emulado (390 × 844): factor ~1,25. Un clic dado en píxeles CSS cae en otro lugar. Para probar el riel conviene `find` o JavaScript. Inyectar CSS de prueba con `<style>` no sirve cuando la hoja real se vuelve a inyectar después (gana por orden): hay que reiniciar la copia.
- **Verificado en pantalla** (copia del puerto 8502, reiniciada con el código final): Inicio y cabecera a 390 px; **escritorio a 1440 px sin cambios** (tarjetas de Inicio en 3 columnas; cabecera en una fila de 35 px con Bid/Ask de 14 px).
- **Pendiente:** elementos nuevos de las maquetas (chips de favoritos, barra Vender/Comprar fija y panel «Más»); la ficha de instrumento de Mercados, el chat del agente y otras ventanas (diálogos, buscador) en el celular sin revisar. Nada subido a git.

### 23-10-2026 (tarde IV) — Responsivo, paso 5: ficha de Mercados, chat del agente y diálogos a 390 px
- **Método:** copia propia en el puerto 8502 con la cuenta de prueba de Emilio; se midió el desborde dentro de cada diálogo (elementos cuyo borde derecho pasa de 382 px).
- **Ficha del instrumento (Mercados):** el diálogo de Streamlit ocupa toda la pantalla y se desplaza; el único desborde era `.ficha-rendimiento` (6 columnas de ~71 px = 480 px dentro de 309). En celular va en 3 columnas (2 filas), regla en `componentes_plataforma/mercados/estilos.css` dentro del bloque móvil; 0 desbordes tras el cambio (probado con la regla inyectada; el orden en el archivo garantiza que gane a la regla base, pero no se recargó la copia después).
- **Chat del agente (vista Trading):** sin desbordes. Las tres columnas se apilan (historial 675 px, chat 924 px, tercer bloque 288 px) y el campo de escritura queda dentro del panel (no está fijado al borde de la pantalla, así que la barra inferior no lo tapa). El chat queda lejos (y ≈ 2.200 px): mejora posible, no urgente.
- **Diálogos:** buscador (358 × 716 px, sin desbordes; categorías en varias filas, resultados con «Abrir» y «+» apilados), confirmación de cierre de posición («¿Quiere cerrar su posición?» con botón ancho y «Cancelar»; solo se abrió y se canceló, no se cerró ninguna posición), menú del usuario (panel de 210 px dentro de la pantalla) y pantalla «Mis cuentas» (a pantalla completa, sin barras, con «Volver al panel»): todos caben sin cambios.
- **Hallazgos de método:** el buscador no se cierra con Escape (sí la ficha de Mercados); se cierra con la ✕ del diálogo. La primera carga tras reiniciar puede quedar un rato en «Cargando terminal…» sin la barra inferior; recargar la página lo resuelve.
- **Pendiente:** diálogo «Seleccione cuenta» (tarjetas Demo y Real), chips de favoritos, barra Vender/Comprar fija y panel «Más» (elementos nuevos de las maquetas); subir todo a git. Escritorio: no se modificó nada fuera de bloques `@media (max-width: 768px)`.

### 23-10-2026 (tarde V) — Responsivo, paso 6: elementos nuevos de las maquetas (chips de favoritos, barra Vender/Comprar y hoja «Más»)
- **Chips de favoritos** (`componentes_plataforma/riel/movil.py`, `renderizar_chips_favoritos`): fila deslizable de botones redondeados con los favoritos (`st.session_state.favoritos`); el activo mostrado va en naranja (botón `primary`); al tocar uno cambia `activo_seleccionado` con un `on_click`. Se dibuja en `aplicacion_principal/vista_operativa.py` antes de las columnas. En escritorio el contenedor y su envoltorio se ocultan (`display: none`) para no sumar separación.
- **Barra fija Vender/Comprar** (`movil.py`, `renderizar_barra_operar`): HTML con atributos `data-pj-*` que el feed del navegador rellena en vivo (Bid y Ask del activo mostrado), fija a 112 px del borde (sobre el rail de 48 px y la barra de 64 px) y bajo los paneles. **Solo abre el ticket**: `riel.js` captura el toque y llama a `poner('order')`; la orden se confirma en el ticket, nunca desde la barra. El contenido gana relleno inferior de 210 px. Estilos en `componentes_plataforma/riel/estilos.css` (bloque base + bloque móvil).
- **Hoja «Más»:** `barra.py` agrega el botón `navegacion_mas` (oculto en escritorio) y genera las etiquetas de la hoja (`html.pj-mas-abierto`); `barra_lateral.js` alterna esa clase al tocarlo y la quita al tocar cualquier otro botón de la barra (que navega con normalidad). En celular la barra muestra solo Inicio, Trading, Cartera, Mercados y «Más»; abierta, la barra crece hacia arriba en una cuadrícula de 4 columnas con las 13 entradas (11 secciones, Soporte y «Cerrar»). Hallazgos de CSS: los contenedores sin botón (estilo y logo) y el envoltorio del script `pj_sbjs` ocupaban celdas vacías de la cuadrícula y hubo que ocultarlos o sacarlos del flujo; el margen automático de Soporte lo encogía.
- **Verificado en pantalla** (copia 8502 con el código final): los tres elementos a 390 px (chip US30 resaltado; barra con VENDER 52,430.4 y COMPRAR 52,432.4 en vivo; tocar Vender abre el panel Operar; «Más» abre la hoja de 4 filas × 4 columnas y «Noticias» navega y cierra la hoja). **Escritorio a 1440 px sin cambios:** chips, barra y «Más» ocultos; barra lateral de 70 px, rail a la derecha, lista y gráfico lado a lado con las mismas medidas de antes (12 botones de navegación visibles).
- **Observación:** durante la prueba la barra superior mostró «— sin conexión Capital.com» mientras el gráfico tenía precio; es el estado de la cuenta de la copia 8502 (otra sesión de Capital), no del CSS. No se probaron órdenes.
- **Pendiente:** diálogo «Seleccione cuenta»; revisar los cambios con calma en un celular real; subir todo a git y actualizar el servidor.

### 23-10-2026 (noche) — Responsivo, paso 7: pantalla de Trading a alto completo, como las apps de brokers (XM)
- **Problema (captura de Emilio):** en el celular el gráfico quedaba cortado y había que bajar para ver Vender/Comprar. **Causas medidas:** (1) el contenedor del gráfico (`stElementContainer` del iframe) tenía 750 px propios; (2) la fila del riel (48 px) y la barra Vender/Comprar sumaban 160 px sobre la barra de navegación; (3) la barra Vender/Comprar medía 49 px en vez de 64 (el `stMarkdownContainer` de Streamlit trae `margin-bottom: -16px`) y el riel tapaba los botones; (4) la barra de dibujo de la izquierda (43 px) y la cabecera de precio (68 px) se comían espacio.
- **Cambios** (todo dentro de `@media (max-width: 768px)`):
  - `componentes_plataforma/riel/estilos.css`: el riel derecho se oculta en celular (el ticket se abre desde Vender/Comprar y los favoritos son las chips; **el panel DOM queda sin acceso en celular**); paneles como hojas inferiores sobre la barra de navegación (`bottom: 64px`); barra Vender/Comprar fija a 64 px del borde con `height: 64px` y margen del markdown anulado; el iframe del gráfico y su contenedor miden `100dvh - 362px` (alto de pantalla menos barra superior, chips, cabecera, barra Vender/Comprar y barra de navegación); relleno inferior de 150 px.
  - `componentes_plataforma/grafico/estatico/css/30_cuerpo_y_herramientas.css`: dentro del iframe se oculta `#tradingview-barra-herramientas-izquierda` en celular (va tras la regla base para ganar por orden; en `10_...` no ganaba).
  - `componentes_plataforma/grafico/cabecera_precio.py`: cabecera compacta (relleno 6 px, Bid/Ask de 12 px) y el estado «Conectado» pasa a un punto en la esquina (clase `pj-cab-estado`).
- **Verificado en la copia 8502 a 390 px:** chips 90–136, cabecera 152–220, gráfico 226–708 (482 px, ancho 365 y lienzo 384 px sin barra de dibujo), barra Vender/Comprar 716–780 con botones completos, barra de navegación 780–844: todo en una sola pantalla, sin desplazamiento. **Escritorio a 1440 px sin cambios** (iframe de 750 px, barra de dibujo visible, riel a la derecha, cabecera de 57 px, barra lateral de 70 px).
- **Hallazgo de método:** la captura del navegador de Claude sale reducida cuando el panel es más ancho que el viewport emulado; la medición con JavaScript y `zoom` sobre la esquina sirven para revisar.
- **Pendiente:** etiquetas de texto bajo los íconos de la barra inferior y el logo P&J en la barra superior (acordado como siguiente paso), ritmo común de títulos y tarjetas, diálogo «Seleccione cuenta», y revisar en un celular real. Nada subido a git.

### 24-10-2026 (madrugada) — Responsivo, paso 8: etiquetas de la barra inferior, logo P&J arriba y ritmo común de títulos
- **Etiquetas bajo los íconos** (`componentes_plataforma/barra_lateral/barra.py` + `estatico/barra_lateral.css`): los botones de la barra inferior pasan de 48 × 48 a 64 × 56 px con el ícono arriba y el texto debajo (Inicio, Trading, Cartera, Mercados y Más, 11 px). `barra.py` genera las reglas `::after` desde `ITEMS` con un marcador nuevo en el CSS (`__ETIQUETAS_MOVIL__`). Hallazgo: con `justify-content: space-around` los botones quedaban pegados a la derecha porque los contenedores sin botón (estilos y logo) y el envoltorio del script `pj_sbjs` también recibían espacio; al ocultarlos o sacarlos del flujo los cinco botones se reparten el ancho (13–77, 88–152, 163–227, 238–302 y 314–378 px).
- **Logo P&J en la barra superior** (`componentes_plataforma/barra_superior/estilos.css`): en celular la primera columna deja de ocultarse; se esconde el botón ☰ y se muestra el texto P&J con el degradado de marca mediante `::before` (`content: "P\26 J"`). Medido a 390 px: logo, lupa, capital con DEMO, campana y avatar caben sin desbordar (avatar termina en 386 px).
- **Ritmo común:** se midieron los títulos de página: Resumen, Diario, Laboratorio, Planes, Billetera y Copy trading ya medían 22 px; Inicio 26 px, Mercados 24 px y Noticias 24 px (este último en línea, sin clase). Una regla única en `barra_lateral.css` (bloque móvil) los lleva a 22 px; `noticias/secciones.py` recibe la clase `noticias-titulo`. Las tarjetas y los espacios no se tocaron: la revisión no mostró desbordes ni diferencias que justifiquen cambiarlos.
- **Verificado en la copia 8502:** etiquetas, logo y títulos a 390 px; **escritorio a 1440 px sin cambios** (títulos de 26/24/24 px, 12 botones de 44 × 44 px, ☰ visible, sin logo de columna, sin etiquetas, sin «Más»).
- **Pendiente:** diálogo «Seleccione cuenta», pruebas en un celular real y subir todo a git (Emilio pidió no subir nada hasta que lo diga).

### 24-10-2026 (madrugada II) — Responsivo, paso 9: diálogo «Seleccione cuenta» a 390 px
- El diálogo se abre desde Inicio con el botón de la cuenta (`inicio_seleccion`, `componentes_plataforma/inicio/modal_cuentas.py`). A 390 px mide 358 × 471 px con las tarjetas Demo y Real apiladas (saldo, número de cuenta, tipo) y el botón «Usar cuenta Real (opera con dinero real)»; **sin desbordes**, no hizo falta ningún cambio de CSS. Solo se abrió y se cerró con la ✕; **no se pulsó el botón de la cuenta Real** (cambiaría de cuenta).
- El recorte ampliado de la esquina también confirmó, ya con el código final, el logo P&J arriba y las etiquetas de la barra inferior.
- **Con esto quedan revisadas a 390 px todas las vistas y diálogos del responsivo.** Pendiente: probar en un celular real y subir a git cuando Emilio lo diga (actualizar luego el servidor con `~/actualizar.sh`).

### 24-10-2026 (mañana) — Responsivo, paso 10: leyenda del gráfico, capital con ganancia/pérdida y avatar siempre visible (captura de Emilio en su celular)
- **Capital sin ganancia/pérdida:** el paso 5 había ocultado `[data-pj-acc="profit"]` para ganar ancho. Ahora se muestra en dos líneas dentro del mismo recuadro: equity arriba y P/G flotante debajo (11 px, verde o rojo), y se oculta la etiqueta «CAPITAL» (`componentes_plataforma/barra_superior/estilos.css`: `span:has(> [data-pj-acc="profit"]) { flex-direction: column }`). El recuadro de capital mide ~120 px en vez de ~185.
- **Avatar cortado a la derecha:** en el celular de Emilio la suma de logo, lupa, capital con DEMO, campana y avatar superaba el ancho (en mi emulación a 390 px llegaba a 382 px, sin margen). Con el capital más angosto y la lupa de 40 px, el avatar termina en 366 px a 390; un bloque `@media (max-width: 400px)` aprieta la lupa (36 px), el logo (20 px), la etiqueta DEMO (9 px, selector `[title^="Cuenta con la que"]`) y los espacios; a 340 px o menos se oculta la campana. Medido: avatar termina en 351 px a 360 y en 314 px a 320; `scrollWidth` = ancho en los tres. El avatar se queda arriba a la derecha (la alternativa de moverlo a la hoja «Más» queda como opción).
- **Leyenda OHLC del gráfico demasiado grande** (`componentes_plataforma/grafico/estatico/css/10_base_y_barra_superior.css`, dentro del iframe): en celular se reduce a una sola línea de 10 px (O, H, L, C y variación; 262 × 29 px) y se ocultan símbolo, temporalidad y origen de datos (ya están en la cabecera de precio y en la barra de temporalidades; además el origen decía «XM», un resto de la época de MetaTrader). Los 12 px de escritorio tapaban las velas.
- **Escritorio a 1440 px sin cambios:** leyenda con símbolo y OHLC de 12 px, P/G de 13 px en la misma fila, etiqueta CAPITAL visible, sin logo de columna y con el ☰.
- **Pendiente:** que Emilio lo vea en su celular y diga si quiere el avatar en otro sitio; nada subido a git.

### 24-10-2026 (mañana) — Responsivo, paso 11: se quitan los chips de favoritos y la barra Vender/Comprar se angosta
- **Chip «US30» sobre el gráfico (no se entendía y quitaba espacio):** eliminado (`riel/movil.py`, `riel/__init__.py`, `vista_operativa.py` y su CSS). Ahora el **símbolo de la cabecera de precio lleva una flecha ▾** y al tocarlo se abre la hoja de Favoritos (`riel.js` + `grafico/cabecera_precio.py`); al elegir un favorito la hoja se cierra y se cambia el activo. Solo celular.
- **Barra Vender/Comprar:** de ~90 px a 52 px; cada botón es una sola línea (etiqueta + precio en vivo), 40 px de alto. Sigue abriendo el ticket de órdenes.
- **Gráfico:** el iframe pasa a `calc(100dvh - 290px)`; a 390×844 mide 554 px (antes 482), con la barra y la navegación inferiores visibles sin bajar.
- **Verificado en 8502:** símbolo → clase `pj-panel-favorito`, elegir tarjeta → `pj-panel-none`; sin desborde horizontal. **Escritorio a 1440×900 sin cambios** (barra oculta, sin ▾, riel visible, gráfico 750 px).
- **Pendiente:** ver en celular real; nada subido a git.

### 24-10-2026 (mañana) — Responsivo, paso 12: cabecera de precio compacta, hueco superior eliminado y botones Vender/Comprar como antes
- **Aclaración de Emilio:** el «recuadro» que quitaba espacio era la tarjeta de precio (US30 / Capital.com / Bid-Ask), no la barra Vender/Comprar. La barra **vuelve a su tamaño anterior** (64 px, botones de dos líneas de 48 px; `riel/estilos.css`).
- **Cabecera de precio** (`grafico/cabecera_precio.py`, solo celular): se oculta la etiqueta «Capital.com» (clase `pj-cab-origen`), relleno 4×10 px, símbolo 17 px, precio 18 px, Bid/Ask 11 px.
- **Hueco perdido bajo la barra superior (~32 px):** el contenedor del CSS inyectado y el envoltorio de `pj_panel_favorito` medían 0 px pero eran hijos de `pj_vista` (separación de 16 px), sumando 32 px vacíos. Ahora salen del flujo en celular (`position:absolute`).
- **Medido a 390×844:** cabecera y=64 (56 px), gráfico y=124 con 586 px (`calc(100dvh - 258px)`; antes 554), barra y=716–780, sin desborde horizontal. Escritorio: reglas solo dentro de `@media (max-width:768px)`; no se re-midió en esta pasada.
- Nada subido a git.

### 24-10-2026 (mañana) — Responsivo, paso 13: la Lista de activos también sale como hoja al tocar el símbolo
- **Pedido de Emilio:** al tocar «US30 ▾» se abría solo Favoritos; quería que la Lista de activos apareciera de la misma forma.
- **Ahora** (`riel/estilos.css`, solo celular): al tocar el símbolo se abren **dos hojas apiladas** sobre la navegación: Favoritos arriba (máx. 30vh, con scroll) y Lista de activos debajo (42vh; zona con scroll `calc(42vh - 150px)`). La lista ya no queda bajo el gráfico, así que la página es más corta. Al elegir una tarjeta (`favsel_*`) o una fila (`wlsel_*`) las hojas se cierran (`riel.js`).
- **Gotcha:** el panel Favoritos vive dentro de la columna de la lista; si esa columna lleva `transform`, el panel `position:fixed` queda atrapado en ella (se vio desplazado ~65 px). Por eso la columna se oculta con `visibility`, no con `transform`.
- **Medido a 390×844:** Favoritos y=200–425, lista y=426–780, sin desborde; elegir una fila vuelve a `pj-panel-none`. Solo Trading tiene Lista de activos (Cartera muestra solo Favoritos). Escritorio sin reglas nuevas fuera de la media query; no re-medido.
- Se vuelve a mostrar la etiqueta «Capital.com» en la cabecera (a pedido). Nada subido a git.

### 24-10-2026 (mañana) — Responsivo, paso 14: corrección de la hoja Lista de activos (el gráfico desaparecía)
- **Fallo reportado por Emilio:** tras el paso 13 el gráfico y la cabecera no se veían y la lista asomaba sobre ellos (con textos sueltos «One-Click Trading» y «Pending order»).
- **Causa:** `div[data-testid="stColumn"]:has(.st-key-lista_activos_panel)` coincidía con DOS columnas: la de la lista y la columna exterior que también contiene el gráfico; la regla fija/ocultaba ambas. Además `visibility:hidden` no ocultaba todo (hijos con `visibility:visible`).
- **Arreglo** (`riel/estilos.css`): selector con `:not(:has(.st-key-grafico_cerrar_wrap))` para tomar solo la columna de la lista, y ocultarla con `display:none` (abierta: `display:block`).
- **Medido a 390×844:** cerrada → cabecera y=64, gráfico y=124 con 586 px, lista oculta; abierta → Favoritos 200–425, lista 426–780; elegir fila vuelve a `pj-panel-none`; sin desborde. Escritorio no re-medido. Nada subido a git.
- **Lección:** verificar siempre cuántos elementos coincide un selector con `:has()` (`querySelectorAll(...).length`) y revisar el gráfico, no solo la hoja nueva.

### 24-10-2026 (mañana) — Responsivo, paso 15: Lista de activos sola, con botón para pasar a Favoritos y volver
- **Pedido de Emilio:** no mostrar Favoritos y Lista juntas; la lista sale sola y desde ella se accede a Favoritos y viceversa.
- **Ahora** (solo celular): tocar el símbolo abre **solo la hoja «Lista de activos»** (65vh; nuevo estado `pj-panel-activos` en `riel.js`). Su cabecera lleva el botón «★ Favoritos» (`pj-ir-fav`, en `lista_activos/panel.py`) que cambia a la hoja Favoritos; esta lleva «‹ Lista de activos» (`pj-ir-lista`, en `favoritos/barra.py`) para volver. En Cartera (sin lista) el símbolo abre Favoritos y el botón de volver se oculta. Tocar el símbolo de nuevo cierra; elegir una fila/tarjeta también.
- **CSS** (`riel/estilos.css`): columna de la lista `fixed` 65vh con `display:none` salvo `html.pj-panel-activos`; zona con scroll `calc(65vh - 150px)`; clase `.pj-nav-hoja` (oculta en escritorio).
- **Medido a 390×844:** símbolo → solo lista (y=231, 549 px); «★ Favoritos» → solo favoritos; «‹ Lista de activos» → solo lista; símbolo → cerrado; sin desborde. Escritorio no re-medido. Nada subido a git.

### 24-10-2026 (mañana) — Responsivo, paso 16: el panel Operar asomaba al abrir la Lista de activos
- **Fallo reportado:** al tocar el símbolo salía el panel de órdenes (Operar) en vez de la lista.
- **Causa:** la regla que muestra Operar «por defecto» era `html:not(.pj-panel-dom):not(.pj-panel-favorito):not(.pj-panel-none)`; con el nuevo estado `pj-panel-activos` también se cumplía y Operar se mostraba. Se añadió `:not(.pj-panel-activos)` en las dos reglas (`riel/estilos.css`: botón del rail y `pj_panel_orden`).
- **Verificado a 390×844** (qué hoja queda visible por estado): inicio ninguna; símbolo → solo lista; «★ Favoritos» → solo favoritos; «‹ Lista de activos» → solo lista; símbolo → cerrado; Vender → solo Operar. Nada subido a git.
- **Lección:** al añadir un estado nuevo a los paneles, revisar todas las reglas `:not(...)` en cadena.

### 24-10-2026 (mañana) — Responsivo, paso 17: asa y toque fuera para cerrar las hojas
- **Pedido de Emilio:** el panel Operar no se podía cerrar; quería la «rayita» de las apps de celular o poder tocar fuera.
- **Hecho** (todas las hojas: Operar, DOM, Favoritos y Lista de activos; solo celular):
  - **Asa:** `::before` de 44×5 px gris (`#6e7681`) centrada arriba de cada hoja (`riel/estilos.css`; `position:sticky`, `flex:0 0 5px` — sin el `flex` medía 0 px). `riel.js`: un toque en los primeros 30 px de la hoja la cierra (`pj-panel-none`).
  - **Tocar fuera:** mientras haya una hoja abierta, `html:not(.pj-panel-none)::after` pone un velo oscuro (`z-index:99990`, 55 %) sobre la página; el clic cae en `html` y `riel.js` cierra la hoja.
- **Medido a 390×844** (clics simulados con `elementFromPoint`): asa de Operar y de Lista cierran; clic fuera cierra; Vender reabre Operar; asa de 5 px visible.
- **Pendiente:** probar con el dedo en un celular real (el arrastre hacia abajo no está implementado, solo toque). Escritorio no re-medido. Nada subido a git.

### 24-10-2026 (mañana) — Responsivo, paso 18: se quita la rayita (asa) de las hojas
- Emilio la vio muy gruesa y encima del contenido: se eliminó el `::before` y el cierre por toque en los primeros 30 px. Las hojas se cierran **tocando fuera** (velo oscuro, `riel.js`), con el botón del símbolo o con Vender/Comprar. No probado en pantalla tras el cambio (solo se quitó código). Nada subido a git.

### 24-10-2026 (mañana) — Responsivo, paso 19: «tocar fuera» más robusto
- Emilio dijo que tocar fuera no cerraba en su navegador. En mi copia (390×844) el velo ya cerraba con clic real, así que se reforzó sin depender solo del velo: `riel.js` cierra la hoja abierta ante cualquier clic que no caiga dentro de ella, la barra de navegación (superior e inferior), la barra Vender/Comprar, el símbolo, diálogos o popovers.
- **Verificado con clic real** (herramienta de clic del navegador) fuera de la hoja Operar a 390×844: pasa a `pj-panel-none`.
- **Posibles causas en su navegador (sin confirmar):** `riel.js` se lee al arrancar Streamlit (hay que reiniciarlo y recargar con Ctrl+F5) o la ventana mide más de 768 px (las reglas son solo de celular). Nada subido a git.

### 24-10-2026 (tarde) — Responsivo, paso 20: Cartera sin gráfico en celular
- **Pedido de Emilio:** en Cartera (celular) mostrar solo la lista de posiciones, sin el gráfico ni la cabecera de precio.
- **Hecho** (`riel/estilos.css`, solo ≤768 px): se oculta la columna interior del gráfico en la vista sin Lista de activos (`html:not(:has(.st-key-lista_activos_panel))`; esa lista solo existe en Trading). La columna exterior (contiene toda la vista) no se toca: `:not(:has([data-testid="stColumn"]))`. La barra Vender/Comprar sigue visible.
- **Medido a 391 px:** en Cartera, cabecera de precio y gráfico ocultos (iframe con ancho 0), «Cartera» arranca en y=76 y aparece «P/G TOTAL»; en Trading el gráfico y la cabecera siguen. Sin desborde. Escritorio no re-medido. Nada subido a git.
- **Efecto colateral:** sin la cabecera de precio, en Cartera no existe el símbolo ▾ que abre la Lista de activos/Favoritos.

### 24-10-2026 (tarde) — Responsivo, paso 21: iPhone 13 Pro Max (navegador de WhatsApp): recorte a la derecha y barras fijas desplazadas
- **Reporte de Emilio (capturas desde su iPhone):** el lado derecho se recorta (avatar, botón Comprar, precios del gráfico), la barra superior desaparece al hacer scroll y, arriba del todo, desaparece la inferior.
- **Causa 1 — ancho:** a 428 px (iPhone Pro Max) la barra superior sobraba 8 px (la campana terminaba en 436): las reglas que aprietan la barra eran solo para ≤400 px. Ahora son para ≤440 px (`barra_superior/estilos.css`). A 428 px: sin elementos fuera de pantalla (`scrollWidth` 428), avatar termina en 369.
- **Causa 2 — barras fijas:** en el navegador integrado de WhatsApp los elementos `position:fixed` se pegan a la ventana de maquetación y no a la visible (las dos barras se movían 103 px con el scroll, igual que el contenido). `barra_lateral.js` publica el desfase de `visualViewport` en `--pj-vv-top` y `--pj-vv-bottom` (0 en escritorio); las usan la barra superior, la de navegación, la Vender/Comprar, las hojas y la columna de la lista (`bottom: calc(64px + var(--pj-vv-bottom))`).
- **Causa 3 — texto:** en el iPhone la leyenda OHLC (10 px) se veía a ~13 px (ampliación automática de texto en iOS): `-webkit-text-size-adjust: 100%` en la página y en el iframe del gráfico.
- **No verificado en iPhone** (no hay dispositivo aquí): en mi emulación las variables valen 0 y todo queda como antes. La corrección de las barras fijas es la técnica estándar, pero hay que probarla en el teléfono. Sin commit todavía.

### 24-10-2026 (tarde) — Responsivo, paso 22: barrido por anchos de celular (320 a 430 px)
- **Pedido de Emilio:** que se adapte a todos los celulares actuales. Se midió en el navegador integrado (emulación) con la cuenta de prueba en el puerto 8502.
- **Trading** en 320×568, 360×740, 375×667, 390×844, 393×852, 412×915, 430×932 y tablet 768×1024: `scrollWidth` = ancho en todos (sin desborde horizontal); los 5 botones de la barra inferior y los dos de Vender/Comprar caben (a 320 px: Vender 12–156, Comprar 164–308). Barra superior completa (avatar termina en 314 a 320, 351 a 360 y 406 a 430).
- **Las 11 vistas a 320 px** (Inicio, Trading, Cartera, Mercados, Copy trading, Noticias, Resumen, Diario, Laboratorio, Planes, Billetera): `scrollWidth` = 320 en todas. Hay contenido más ancho dentro de contenedores con scroll propio (tabla de Diario, comparativa de Planes), que se desplaza dentro de su tarjeta y no ensancha la página.
- **768 px (tablet):** el panel del agente sobrepasa el ancho (793 px); no es un celular, queda como pendiente opcional.
- **No cubierto:** el navegador real de iPhone (barras fijas desplazadas: ver paso 21), Android real, modo horizontal y teclado en pantalla. Sin commit.

### 24-10-2026 (tarde) — Responsivo, paso 23: tarjeta «Confirmar orden» recortada en celular
- **Reporte de Emilio (captura):** al pulsar «Colocar orden» en el ticket, la tarjeta de confirmación (Colocar orden / Cancelar) salía cortada por arriba.
- **Causa:** la tarjeta (`.st-key-orden_confirmacion_tarjeta`, `panel_orden/confirmacion.py`) es `position:fixed` pero vive dentro de la hoja Operar; la hoja abierta tenía `transform: translateY(0)` y un `transform`, aunque sea la identidad, la convierte en bloque contenedor de sus hijos fijos: la tarjeta se colocaba y recortaba dentro de la hoja.
- **Arreglo** (`riel/estilos.css`, solo ≤768 px): hojas abiertas con `transform: none` en vez de `translateY(0)`; y la tarjeta ocupa el ancho (12 px de margen) y se coloca sobre las barras (`bottom: calc(148px + var(--pj-vv-bottom))`).
- **Medido a 390×844** con una tarjeta de prueba inyectada (no se colocó ninguna orden): hoja con `transform: none`; tarjeta en x 12–378, y 526–696, dentro de la pantalla y sobre la barra Vender/Comprar. No se vio el flujo real de confirmación (habría que pulsar «Colocar orden»); escritorio sin cambios (regla solo en la media query). Sin commit.

### 24-10-2026 (tarde) — Responsivo, paso 24: tablets (el corte de celular sube de 768 a 1024 px)
- **Aviso de Emilio:** en su tablet se veía como escritorio y la idea es que sea responsivo, no a un tamaño fijo. El diseño de celular (barra inferior, hojas, Vender/Comprar) solo se activaba hasta 768 px; una tablet vertical (810–834 px) caía en escritorio.
- **Hecho:** el corte pasa a **1024 px** en las reglas de la estructura: `barra_lateral.css`/`.js`, `barra_superior/estilos.css`, `riel/estilos.css` y `riel.js`, `cabecera_precio.py`, `inicio`, `mercados` y `lista_activos`. Quedan igual los escalones finos de la barra superior (≤440 y ≤340) y las reglas del interior del gráfico (≤768 sobre el ancho del iframe).
- **Medido:** 820×1180 y 1024×768 → barra inferior, hojas y Vender/Comprar, sin desborde (`scrollWidth` = ancho; gráfico 922 px de alto en la vertical); 1100×800 y 1440×900 → escritorio (barra lateral de 70 px, riel, sin barra Vender/Comprar).
- **Límite:** en 769–1024 px se usa la misma estructura que en celular, con contenido estirado; no hay aún un diseño propio de dos columnas para tablet. Corte único a revisar si algún dispositivo cae justo en 1024. No probado en tablet real. Sin commit.

### 24-10-2026 (tarde) — Responsivo, paso 25: Vender/Comprar fijan el lado en el ticket y la barra se oculta en Cartera
- **Reporte de Emilio:** (1) en Cartera no deberían salir los botones de compra/venta; (2) en Trading los dos botones de abajo llevaban a lo mismo: Comprar abría BUY (verde) pero Vender también abría con BUY seleccionado.
- **Causa de (2):** la barra solo abría el panel (`poner('order')`); el lado lo guarda `st.session_state.orden_lado` (por defecto BUY) y solo cambia con los botones invisibles del ticket (`orden_superposicion_sell` / `_buy`, `panel_orden/panel.py`).
- **Arreglo** (`riel/riel.js`): al tocar Vender o Comprar se abre el panel y se pulsa por código el botón invisible del lado correspondiente (el rerun del fragmento fija el lado). **Cartera** (`riel/estilos.css`, ≤1024 px): barra Vender/Comprar oculta en la vista sin Lista de activos, y el relleno inferior baja a 88 px.
- **Medido a 390×844** (sin colocar órdenes): inicio → BUY; Vender → `orden-sell.sel`; Comprar → `orden-buy.sel`; Cartera → barra `display:none`. Sin commit.

### 24-10-2026 (tarde) — Responsivo, paso 26: el panel Operar se abre ya con el lado correcto
- **Reporte de Emilio:** al tocar el lado contrario, el panel se abría antes de cambiar y se veía el cambio de BUY a SELL.
- **Arreglo** (`riel/riel.js`): si el ticket ya muestra el lado pedido se abre de inmediato; si no, se pulsa el botón invisible del lado y el panel se abre cuando el ticket pinta ese lado (sondeo cada 50 ms, tope 2 s por si el servidor tarda).
- **Medido a 390×844** muestreando cada 20 ms: Vender → al abrirse ya es SELL (cambio de lado a los 414 ms, panel a los 447 ms); Comprar → BUY (450/516 ms); Vender de nuevo → SELL. En el servidor puede tardar algo más (hasta 2 s). Sin commit.

### 24-10-2026 (tarde) — Responsivo, paso 27: botón para ampliar el gráfico (como XM)
- **Pedido de Emilio (capturas de XM):** botón de ampliar el gráfico que lo lleva a pantalla completa y deja ver sus herramientas de dibujo.
- **Qué había:** ya existía `#boton-completo` (barra superior del gráfico), pero en celular queda fuera de la vista (la barra se desplaza) y en iPhone la API de pantalla completa no existe para un iframe.
- **Hecho** (`grafico/estatico/`): botón `#boton-expandir-movil` al final de la barra de rangos (`html/40_barra_rangos.html`; `css/60_barra_rangos.css`: `position:sticky; right:0`, solo con la clase `pj-tactil`, que `55_pantalla_completa.js` pone en el html del iframe cuando la ventana padre mide ≤1024 px). Al pulsarlo en pantallas táctiles se usa una **pantalla completa simulada**: el iframe pasa a `position:fixed` sobre toda la ventana (estilos con `!important`, estado guardado en `data-pj-fs` del iframe por si Streamlit recarga el contenido; Escape o el mismo botón, con icono de contraer, la cierran). En ese modo vuelve la barra de dibujo (`css/30_cuerpo_y_herramientas.css`, solo `pj-tactil` + `pj-fs`) y siguen los botones VENDER/COMPRAR de posiciones. La página padre bloquea su scroll (`html.pj-grafico-expandido`, `riel/estilos.css`). En escritorio sigue la pantalla completa real.
- **Medido a 390×844:** botón visible en la barra de rangos (x 319–354); al pulsar: iframe 390×844 en (0,0), `pj-fs` activo, barra de dibujo visible (43 px de ancho), icono de contraer; al volver a pulsar: iframe 366×586 en su sitio, sin estilo en línea. No probado: iPhone/Android reales, rotación de pantalla en modo ampliado, dibujar con el dedo. Sin commit.

### 24-10-2026 (tarde) — Responsivo, paso 28: gráfico ampliado con botón Atrás, tarjeta de precio y panel Operar
- **Reporte de Emilio:** (1) el botón Atrás del teléfono no sacaba del modo ampliado; (2) VENDER/COMPRAR del gráfico ampliado debían abrir el panel de órdenes; (3) sobre el gráfico ampliado debía verse la tarjeta de precio (símbolo ▾, origen, precio, Bid/Ask) para abrir la lista de activos sin salir.
- **Hecho:**
  - **Atrás:** al ampliar se agrega una entrada de historial (`history.pushState({pjFs:1})`) y un `popstate` cierra la ampliación; al cerrarla con el botón se retira esa entrada con `history.back()` (`55_pantalla_completa.js`).
  - **Operar:** en pantalla táctil ampliada, los botones VENDER/COMPRAR del gráfico (`posiciones/js/60_botones_mercado.js`) llaman a `window.__pjOperarDesdeGrafico`, que pulsa el botón correspondiente de la barra Vender/Comprar de la página: se abre el panel Operar con el lado elegido **sin salir de la ampliación**. Fuera de ese modo siguen operando a mercado como antes.
  - **Tarjeta de precio:** ampliado, `.pj-cab-precio` queda `position:fixed` arriba (z-index 100015) y el iframe se baja su alto; al tocar el símbolo se abre la Lista de activos encima del gráfico (hojas z-index 100030, velo 100020, tarjeta de confirmación 100040; `riel/estilos.css`, `html.pj-grafico-expandido`).
- **Medido a 390×844:** ampliado → iframe en y=70 (774 px de alto), tarjeta fija arriba, historial +1 entrada; símbolo → lista visible sobre el iframe; tocar fuera → cerrada; VENDER del gráfico → hoja Operar con SELL y el gráfico sigue ampliado; `history.back()` → sale de la ampliación y el iframe vuelve a su sitio (366×586, sin estilo en línea). No probado en teléfono real (botón Atrás físico/gestos, rotación). Sin commit.

### 24-10-2026 (tarde) — Responsivo, paso 29: dibujar en el gráfico con el dedo
- **Reporte de Emilio:** en el gráfico ampliado las herramientas se podían elegir pero no colocar.
- **Causa:** el dibujo (`grafico/estatico/js/22_dibujo_interaccion.js`) solo escucha `mousedown/mousemove/mouseup`; al arrastrar un dedo el navegador no genera eventos de ratón (solo tras un toque corto) y el gráfico hacía scroll.
- **Arreglo:** puente táctil al final del mismo archivo: `touchstart/move/end/cancel` (en captura, `passive:false`) se traducen a eventos de ratón sintéticos, solo cuando el toque es del dibujo (herramienta activa, dibujo en curso, segundo punto pendiente o dedo sobre un dibujo existente) y no cae en botones, menús ni fuera del área de trazado; si no, el gráfico se desplaza como siempre. Un dedo = un gesto; con dos dedos no interviene (zoom/desplazamiento normales).
- **Medido a 390×844** con eventos táctiles simulados en el gráfico ampliado: elegir «Línea de tendencia» y arrastrar de (150,300) a (280,420) → el lienzo de dibujos pasa de 0 a 36 484 píxeles, la herramienta vuelve al cursor, `preventDefault` aplicado. No probado con dedo real (precisión, arrastre de puntos de dibujos existentes, herramientas de tres puntos o texto). Sin commit.

### 24-10-2026 (tarde) — Responsivo, paso 30: poder borrar los dibujos en el celular
- **Reporte de Emilio (captura con Fibonacci y línea de tendencia):** no podía quitarlos.
- **Causas:** (1) la barra flotante de estilos (`#tradingview-stylebar`, `grafico/estatico/js/23_dibujo_barra_estilos.js`) va centrada y más ancha que el gráfico en celular; los botones **Duplicar / Eliminar** (al final de la barra) quedaban fuera de la pantalla; (2) «Limpiar elementos» usa `confirm()`, que muchos navegadores integrados bloquean dentro de un iframe (el botón no hacía nada).
- **Arreglo:** (1) con la clase `pj-tactil` (ventana ≤1024 px) la barra se ajusta al ancho del gráfico (`left:46px; right:6px`), se desplaza si no cabe y las acciones (Ajustes, Duplicar, Eliminar) pasan al principio (`order:-1`); botones de 36×34 px. (2) En pantallas táctiles «Limpiar elementos» pide un segundo toque en 3 s (el icono se pone rojo y aparece el aviso «Toca de nuevo para limpiar todos los dibujos»; `22_dibujo_interaccion.js`); en escritorio sigue el `confirm()`.
- **Medido a 390×844** (eventos táctiles simulados): barra x 46–384 con Eliminar en x 133–169 (visible); dibujo creado → Eliminar → el dibujo desaparece (lienzo 36 484 → 1 877 px, barra oculta); «Limpiar»: primer toque arma y no borra, segundo borra todo (lienzo 0).
- **Observación:** tocar la etiqueta «+ Añadir texto» de una línea seleccionada abre la ventana de Ajustes (comportamiento original); esa ventana tapa el gráfico hasta cerrarla. No probado con dedo real. Sin commit.

### 24-10-2026 (tarde) — Sesión persistente («mantener sesión iniciada» con cookie, 30 días)
- **Problema (Emilio):** al cerrar el navegador (celular o PC) la sesión se cerraba. Causa: la sesión vivía en el token `?s=` de la URL (se pierde al cerrar y abrir la web limpia) y en un almacén **en memoria** del servidor (se vacía al reiniciar la app, p. ej. con `~/actualizar.sh`).
- **Diseño:** cookie `pj_sesion` con un token aleatorio (`secrets.token_urlsafe(32)`), `Max-Age` 30 días, `Path=/`, `SameSite=Lax`, `Secure` si es HTTPS; en Supabase solo se guarda el **hash SHA-256** del token, el usuario, el vencimiento y el dispositivo.
- **Archivos nuevos:** `herramientas/sql/sesiones_persistentes.sql` (tabla `sesiones_persistentes`, RLS sin políticas + GRANT a `service_role`, índice por usuario), `herramientas/sesion_persistente.py` (`crear`, `validar`, `revocar`, `revocar_todas`; purga las vencidas al crear) y `componentes_plataforma/acceso/cookie.py` (escribe/borra la cookie con un script de altura 0 y lee `st.context.cookies`; la acción queda pendiente en `st.session_state` y se emite en la siguiente pasada).
- **Cambios:** `acceso/sesion.py` (`iniciar_sesion` crea el token y programa la cookie; `usuario_en_sesion` prueba la cookie si no hay `?s=` y crea un `?s=` nuevo; `cerrar_sesion` revoca la fila y programa borrar la cookie) y `acceso/pantalla.py` (`aplicar_pendiente()` tras `usuario_en_sesion()`).
- **Probado:** lógica completa con un cliente Supabase simulado (crear, solo se guarda el hash, validar, vencida rechazada y purgada, revocar, revocar_todas, sin Supabase/tabla no rompe); en el navegador (8502): el inicio de sesión sigue funcionando sin la tabla (sin excepciones, sin cookie) y el script escribe y borra la cookie. **No probado:** el ciclo completo con Supabase real (falta ejecutar el SQL), cierre y reapertura del navegador en celular/PC, y Safari/iPhone (cookies con ITP). Sin commit.
- **Pendiente:** ejecutar `sesiones_persistentes.sql` en Supabase; luego probar: iniciar sesión → cerrar el navegador → abrir la web (debe entrar) → «Cerrar sesión» → abrir (debe pedir login). Idea futura: llamar a `revocar_todas` al cambiar la contraseña.

### 24-10-2026 (tarde) — Sesión persistente: máximo 5 dispositivos por cuenta
- **Pedido de Emilio:** máximo 5 dispositivos y que se reemplace el que menos se usa.
- **Hecho** (`herramientas/sesion_persistente.py`): `MAX_DISPOSITIVOS = 5`; al crear una sesión nueva se ordenan las del usuario por `ultimo_uso` (descendente) y se borran las que pasen de 5, es decir, las de uso más antiguo. Además `crear(..., reemplaza_token=...)` borra la fila de la cookie que ya traía ese navegador (`acceso/sesion.py` le pasa `cookie.leer()`), para que iniciar sesión varias veces en el mismo navegador no ocupe cupos.
- **Matiz:** `ultimo_uso` se actualiza cuando la sesión se restaura desde la cookie (al abrir la web de nuevo), no en cada clic.
- **Probado con Supabase simulado:** 5 dispositivos caben; el 6.º cierra el de `ultimo_uso` más antiguo (no el más antiguo en creación: si uno se vuelve a usar, se salva); mismo navegador reemplaza su fila; otro usuario no se afecta; sin Supabase no rompe. No probado contra Supabase real. Sin commit.

### 24-10-2026 (tarde) — Gráfico en celular: Deshacer/Rehacer visibles y poder ocultar la barra de estilos
- **Reporte de Emilio (capturas):** Deshacer y Rehacer quedaban escondidos a la derecha de la barra superior del gráfico (que se desplaza de lado) y la barra de estilos del dibujo (engranaje, duplicar, eliminar, colores) no se podía ocultar.
- **Deshacer/Rehacer:** en pantalla táctil (`pj-tactil`, ≤1024 px) se pasan a la barra de rangos, fijos a la derecha junto al botón de ampliar (`js/23_dibujo_barra_estilos.js`, función `ubicarDeshacerRehacer`; `css/60_barra_rangos.css`: `position:sticky`, `right:78/39/0`); en escritorio vuelven a la barra de acciones. Mantienen su estado habilitado/deshabilitado.
- **Ocultar la barra de estilos:** (1) botón «✕ Ocultar barra» en la propia barra (solo táctil) que quita la selección; (2) un toque corto en un hueco del gráfico, sin herramienta ni dibujo bajo el dedo, también la quita (`js/22_dibujo_interaccion.js`, mismo puente táctil). Antes en táctil solo un clic de ratón deseleccionaba.
- **Medido a 390×844** (eventos simulados): rangos 1–366; Deshacer 241–276, Rehacer 280–315, Ampliar 319–354 (todos visibles); dibujo creado → barra visible; ✕ (x 172–208) → barra oculta; volver a seleccionar y tocar un hueco → oculta; Deshacer quita el dibujo. No probado con un indicador añadido ni con dedo real. Sin commit.

### 24-10-2026 (tarde) — Barra superior del gráfico desplazable en celular
- **Pedido de Emilio:** que la barra de temporalidades/acciones se desplace de lado como la de rangos, porque quedaban botones fuera de la vista.
- **Hecho:** con `pj-tactil` la barra `#tradingview-barra-superior` tiene `overflow-x:auto` (sin barra visible), `justify-content:flex-start` y sus dos grupos no se encogen (`css/10_base_y_barra_superior.css`). Como un contenedor con desplazamiento recorta a los menús desplegables absolutos, `js/55_pantalla_completa.js` los pasa a `position:fixed` al abrirse (bajo su botón, alineados a la derecha, dentro de la ventana, con alto máximo) y los cierra al desplazar la barra; en escritorio no cambia nada.
- **Medido a 390×844:** ancho visible 365 px, contenido 731 px; al desplazar, «Captura» pasa de x=641 a x=275; el menú «Tipo de gráfico» abre en x 151–362 (dentro de la ventana) y se cierra al desplazar. No probado con dedo real ni con los otros menús ni en escritorio. Sin commit.

### 23-10-2026 (cierre) — Subida a git, corrección de solape en tablet e informe del Día 24
- **Git:** todo el día subido a `EmilioFuentes` y a `main` (commit `7b4922d`, tras traer los 2 commits de Cristian con merge sin conflictos). Sesión persistente: commit `7879563`.
- **Hallazgo al hacer las capturas de tablet:** la fila de paneles del agente se montaba sobre el gráfico (y en celular dejaba un hueco): el contenedor del iframe trae `flex: 0 0 750px` dentro de una columna flex, y la altura calculada no bastaba. Arreglo: `flex: 0 0 calc(100dvh - 258px)` en el contenedor (`riel/estilos.css`). Medido: 390 → gráfico 124–710 y separador a 742; 820 → gráfico 124–1046 y separador a 1078; 1100 sin cambios. **Este arreglo aún no está subido a git.**
- **Informe del Día 24** generado: `OCTUBRE\23-10-2026\Informe Avance - Plataforma Adaptable a Celulares y Tablets, Grafico Tactil y Sesion que se Mantiene Abierta - Emilio Fuentes.docx` (14 páginas, 8 capturas reales `capturas/d24_*`; generador `_contexto_nuevo_chat/_dia24_gen_informe.py`). Exportado a PDF con Word (14 páginas, títulos y capturas en su sitio); no se pudo revisar visualmente página a página (no hay renderizador de PDF).
- Nota de fecha: varias secciones anteriores de hoy están rotuladas «24-10-2026» por error; la fecha real es 23-10-2026.
