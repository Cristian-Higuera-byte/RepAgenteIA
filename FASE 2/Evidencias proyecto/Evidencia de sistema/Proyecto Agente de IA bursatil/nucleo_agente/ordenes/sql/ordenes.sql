-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ----------------------------------- INICIO Piña y Jara ordenes .SQL -----------------------------------
-- -------------------------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ordenes (
    id TEXT PRIMARY KEY,
    creada TEXT NOT NULL,
    expira TEXT NOT NULL,
    estado TEXT NOT NULL,        -- PENDIENTE | EJECUTANDO | EJECUTADA | RECHAZADA_USUARIO |
                                 -- RECHAZADA_RIESGO | EXPIRADA | ERROR
    accion TEXT NOT NULL,        -- abrir | cerrar
    simbolo TEXT,
    lado TEXT,                   -- compra | venta  (en 'cerrar': el lado de la posición)
    volumen REAL,
    precio_ref REAL,
    sl REAL,
    tp REAL,
    riesgo_dinero REAL,          -- en 'abrir': pérdida si salta el SL; en 'cerrar': P&L flotante
    riesgo_pct REAL,
    ticket_objetivo INTEGER,     -- en 'cerrar': ticket de la posición
    justificacion TEXT,
    detalle TEXT,                -- motivo del rechazo / resultado de la ejecución
    ticket_resultado INTEGER,
    origen TEXT DEFAULT 'agente',  -- agente (propone y el usuario confirma) | automatica (vigilancia autorizada)
    vigilancia_id TEXT             -- si origen = 'automatica': la vigilancia que la generó
)


-- -------------------------------------------------------------------------------------------------------
-- ------------------------------------- FIN Piña y Jara ordenes .SQL ------------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
