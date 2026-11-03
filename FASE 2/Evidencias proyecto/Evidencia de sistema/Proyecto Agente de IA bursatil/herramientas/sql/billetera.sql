-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ------------------------------------ INICIO Piña y Jara billetera .SQL --------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: billetera virtual de cada usuario (saldo de prueba sin valor monetario) y su libro de movimientos. Sirve para pagar planes
-- dentro de la plataforma y queda preparada para cuentas reales (columna `tipo` y movimientos de depósito y retiro reales).
-- Motor: PostgreSQL (Supabase). Ejecutar en SQL Editor > New query > Run, DESPUÉS de crear la tabla `usuarios`.
-- Es idempotente: se puede volver a ejecutar sin perder datos.
-- Seguridad: RLS activo y SIN políticas; solo el servidor, con la clave service_role, lee y escribe estas tablas y ejecuta la función.

-- -------------------------------------------
-- Estructura de tabla para la tabla `billetera_cuentas` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS billetera_cuentas (

        -- TITULO IDENTIFICACION

            -- Usuario dueño de la billetera (una por usuario); al borrar el usuario se borra su billetera.
            usuario_id BIGINT PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,

        -- TITULO SALDO

            -- Moneda del saldo y tipo de billetera: virtual (de prueba) o real (futuro, con dinero de verdad).
            moneda TEXT NOT NULL DEFAULT 'USD',
            tipo TEXT NOT NULL DEFAULT 'virtual' CHECK (tipo IN ('virtual', 'real')),
            -- Saldo actual; nunca puede quedar negativo.
            saldo NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (saldo >= 0),

        -- TITULO CONTROL

            creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizada_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

-- -------------------------------------------
-- Estructura de tabla para la tabla `billetera_movimientos` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS billetera_movimientos (

        -- Identificador de la fila y usuario dueño del movimiento.
        id BIGSERIAL PRIMARY KEY,
        usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,

        -- Tipo de movimiento: bono (saldo inicial), recarga_virtual, compra_plan, ajuste (correcciones y reembolsos) y, para el futuro,
        -- deposito_real, retiro_real y resultado_operacion (ganancia o pérdida de una operación cerrada).
        tipo TEXT NOT NULL CHECK (tipo IN ('bono', 'recarga_virtual', 'compra_plan', 'ajuste', 'deposito_real', 'retiro_real', 'resultado_operacion')),
        -- Monto con signo: positivo abona y negativo cobra. Saldo que quedó después del movimiento.
        monto NUMERIC(14, 2) NOT NULL CHECK (monto <> 0),
        saldo_despues NUMERIC(14, 2) NOT NULL CHECK (saldo_despues >= 0),
        -- Texto para mostrar al usuario y referencia opcional (por ejemplo la clave del plan comprado).
        concepto TEXT NOT NULL DEFAULT '',
        referencia TEXT,
        -- Clave que evita registrar dos veces el mismo movimiento (por ejemplo el bono inicial); puede quedar vacía.
        clave_unica TEXT UNIQUE,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    -- Para listar rápido los últimos movimientos de un usuario.
    CREATE INDEX IF NOT EXISTS billetera_movimientos_usuario ON billetera_movimientos (usuario_id, creado_en DESC);

-- -------------------------------------------
-- Función `billetera_mover` --
-- -------------------------------------------

    -- Descripción: registra un movimiento y actualiza el saldo en una sola operación, bloqueando la fila del usuario para que dos movimientos
    -- simultáneos no se pisen. Crea la billetera si no existe. Si `p_clave` ya se usó, no repite el movimiento y devuelve el saldo actual.
    -- Si el movimiento dejaría el saldo negativo, falla con el mensaje `saldo_insuficiente`.
    CREATE OR REPLACE FUNCTION billetera_mover(p_usuario BIGINT, p_tipo TEXT, p_monto NUMERIC, p_concepto TEXT DEFAULT '',
                                               p_referencia TEXT DEFAULT NULL, p_clave TEXT DEFAULT NULL)
    RETURNS TABLE (saldo_nuevo NUMERIC, movimiento_id BIGINT, repetido BOOLEAN)
    LANGUAGE plpgsql AS $$
    DECLARE
        v_saldo NUMERIC;
        v_nuevo NUMERIC;
        v_id BIGINT;
    BEGIN
        INSERT INTO billetera_cuentas (usuario_id) VALUES (p_usuario) ON CONFLICT (usuario_id) DO NOTHING;
        SELECT c.saldo INTO v_saldo FROM billetera_cuentas c WHERE c.usuario_id = p_usuario FOR UPDATE;
        IF p_clave IS NOT NULL THEN
            SELECT m.id INTO v_id FROM billetera_movimientos m WHERE m.clave_unica = p_clave;
            IF FOUND THEN
                RETURN QUERY SELECT v_saldo, v_id, TRUE;
                RETURN;
            END IF;
        END IF;
        v_nuevo := v_saldo + p_monto;
        IF v_nuevo < 0 THEN
            RAISE EXCEPTION 'saldo_insuficiente';
        END IF;
        UPDATE billetera_cuentas SET saldo = v_nuevo, actualizada_en = now() WHERE usuario_id = p_usuario;
        INSERT INTO billetera_movimientos (usuario_id, tipo, monto, saldo_despues, concepto, referencia, clave_unica)
        VALUES (p_usuario, p_tipo, p_monto, v_nuevo, COALESCE(p_concepto, ''), p_referencia, p_clave) RETURNING id INTO v_id;
        RETURN QUERY SELECT v_nuevo, v_id, FALSE;
    END;
    $$;

-- -------------------------------------------
-- Seguridad y permisos --
-- -------------------------------------------

    -- TITULO SEGURIDAD

        -- Descripción: RLS activo y sin políticas (la clave pública anon no puede leer ni escribir nada). El servidor usa service_role, que
        -- necesita permisos explícitos porque el proyecto crea las tablas sin permisos (sin ellos aparece "permission denied", código 42501).
        ALTER TABLE billetera_cuentas ENABLE ROW LEVEL SECURITY;
        ALTER TABLE billetera_movimientos ENABLE ROW LEVEL SECURITY;
        GRANT USAGE ON SCHEMA public TO service_role;
        GRANT ALL ON TABLE public.billetera_cuentas, public.billetera_movimientos TO service_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
        -- La función mueve dinero: solo la puede ejecutar el servidor.
        REVOKE ALL ON FUNCTION billetera_mover(BIGINT, TEXT, NUMERIC, TEXT, TEXT, TEXT) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION billetera_mover(BIGINT, TEXT, NUMERIC, TEXT, TEXT, TEXT) TO service_role;

        -- Para ver el saldo total y los movimientos por tipo (consultas de ejemplo):
        --   SELECT SUM(saldo) FROM billetera_cuentas;
        --   SELECT tipo, COUNT(*), SUM(monto) FROM billetera_movimientos GROUP BY tipo;


-- -------------------------------------------------------------------------------------------------------
-- --------------------------------- FIN Piña y Jara billetera .SQL ------------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
