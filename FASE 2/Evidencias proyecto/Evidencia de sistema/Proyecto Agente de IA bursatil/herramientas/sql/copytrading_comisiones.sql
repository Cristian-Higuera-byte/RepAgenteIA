-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- --------------------------- INICIO Piña y Jara copytrading_comisiones .SQL ----------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: cambios de la etapa 5 del copy trading (comisión de rendimiento y ajuste de perfil). Agrega a la billetera los movimientos `comision_pagada` y
-- `comision_cobrada`, la función `billetera_transferir` (pasa dinero de una billetera a otra en una sola operación) y dos columnas de `copias`: `comision_final_en`
-- (cuándo se liquidó la comisión final de una copia detenida) y `perfil_previo` (el perfil de inversor del seguidor antes de ajustarlo a la estrategia).
-- Motor: PostgreSQL (Supabase). Ejecutar en SQL Editor > New query > Run, DESPUÉS de los scripts 01 a 05.
-- Es idempotente: se puede volver a ejecutar sin perder datos.

-- -------------------------------------------
-- Tipos de movimiento de la billetera --
-- -------------------------------------------

    -- Descripción: reemplaza la restricción de tipos de `billetera_movimientos` por una que incluye los dos tipos nuevos (comisión pagada por el seguidor y comisión
    -- cobrada por el gestor).
    ALTER TABLE billetera_movimientos DROP CONSTRAINT IF EXISTS billetera_movimientos_tipo_check;
    ALTER TABLE billetera_movimientos ADD CONSTRAINT billetera_movimientos_tipo_check
        CHECK (tipo IN ('bono', 'recarga_virtual', 'compra_plan', 'ajuste', 'deposito_real', 'retiro_real', 'resultado_operacion', 'comision_pagada', 'comision_cobrada'));

-- -------------------------------------------
-- Columnas nuevas de `copias` --
-- -------------------------------------------

    ALTER TABLE copias ADD COLUMN IF NOT EXISTS comision_final_en TIMESTAMPTZ;
    ALTER TABLE copias ADD COLUMN IF NOT EXISTS perfil_previo JSONB;

-- -------------------------------------------
-- Función `billetera_transferir` --
-- -------------------------------------------

    -- Descripción: pasa `p_monto` de la billetera de `p_origen` a la de `p_destino` registrando un movimiento en cada una (`comision_pagada` y `comision_cobrada`),
    -- todo en una sola operación. Bloquea las dos filas en orden de id para que dos transferencias cruzadas no se traben. Si `p_clave` ya se usó no repite nada y
    -- devuelve los saldos actuales con `repetido` en verdadero. Si el origen no tiene saldo suficiente falla con el mensaje `saldo_insuficiente`.
    CREATE OR REPLACE FUNCTION billetera_transferir(p_origen BIGINT, p_destino BIGINT, p_monto NUMERIC, p_concepto_origen TEXT, p_concepto_destino TEXT,
                                                    p_referencia TEXT DEFAULT NULL, p_clave TEXT DEFAULT NULL)
    RETURNS TABLE (saldo_origen NUMERIC, saldo_destino NUMERIC, movimiento_origen_id BIGINT, movimiento_destino_id BIGINT, repetido BOOLEAN)
    LANGUAGE plpgsql AS $$
    DECLARE
        v_so NUMERIC;
        v_sd NUMERIC;
        v_mo BIGINT;
        v_md BIGINT;
    BEGIN
        IF p_monto <= 0 THEN
            RAISE EXCEPTION 'monto_invalido';
        END IF;
        IF p_origen = p_destino THEN
            RAISE EXCEPTION 'misma_billetera';
        END IF;
        INSERT INTO billetera_cuentas (usuario_id) VALUES (p_origen) ON CONFLICT (usuario_id) DO NOTHING;
        INSERT INTO billetera_cuentas (usuario_id) VALUES (p_destino) ON CONFLICT (usuario_id) DO NOTHING;
        PERFORM 1 FROM billetera_cuentas WHERE usuario_id IN (p_origen, p_destino) ORDER BY usuario_id FOR UPDATE;
        SELECT c.saldo INTO v_so FROM billetera_cuentas c WHERE c.usuario_id = p_origen;
        SELECT c.saldo INTO v_sd FROM billetera_cuentas c WHERE c.usuario_id = p_destino;
        IF p_clave IS NOT NULL THEN
            SELECT m.id INTO v_mo FROM billetera_movimientos m WHERE m.clave_unica = p_clave || ':pago';
            IF FOUND THEN
                SELECT m.id INTO v_md FROM billetera_movimientos m WHERE m.clave_unica = p_clave || ':cobro';
                RETURN QUERY SELECT v_so, v_sd, v_mo, v_md, TRUE;
                RETURN;
            END IF;
        END IF;
        IF v_so < p_monto THEN
            RAISE EXCEPTION 'saldo_insuficiente';
        END IF;
        UPDATE billetera_cuentas SET saldo = saldo - p_monto, actualizada_en = now() WHERE usuario_id = p_origen;
        UPDATE billetera_cuentas SET saldo = saldo + p_monto, actualizada_en = now() WHERE usuario_id = p_destino;
        INSERT INTO billetera_movimientos (usuario_id, tipo, monto, saldo_despues, concepto, referencia, clave_unica)
        VALUES (p_origen, 'comision_pagada', -p_monto, v_so - p_monto, COALESCE(p_concepto_origen, ''), p_referencia, CASE WHEN p_clave IS NULL THEN NULL ELSE p_clave || ':pago' END)
        RETURNING id INTO v_mo;
        INSERT INTO billetera_movimientos (usuario_id, tipo, monto, saldo_despues, concepto, referencia, clave_unica)
        VALUES (p_destino, 'comision_cobrada', p_monto, v_sd + p_monto, COALESCE(p_concepto_destino, ''), p_referencia, CASE WHEN p_clave IS NULL THEN NULL ELSE p_clave || ':cobro' END)
        RETURNING id INTO v_md;
        RETURN QUERY SELECT v_so - p_monto, v_sd + p_monto, v_mo, v_md, FALSE;
    END;
    $$;

-- -------------------------------------------
-- Seguridad y permisos --
-- -------------------------------------------

    -- TITULO SEGURIDAD

        -- Descripción: la función mueve dinero entre billeteras: solo la puede ejecutar el servidor (service_role).
        REVOKE ALL ON FUNCTION billetera_transferir(BIGINT, BIGINT, NUMERIC, TEXT, TEXT, TEXT, TEXT) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION billetera_transferir(BIGINT, BIGINT, NUMERIC, TEXT, TEXT, TEXT, TEXT) TO service_role;





-- -------------------------------------------------------------------------------------------------------
-- ----------------------------- FIN Piña y Jara copytrading_comisiones .SQL -----------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
