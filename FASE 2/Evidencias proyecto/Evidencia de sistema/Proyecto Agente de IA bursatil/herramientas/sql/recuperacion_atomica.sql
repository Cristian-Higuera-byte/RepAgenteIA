-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ------------------------------ INICIO Piña y Jara recuperacion_atomica .SQL ---------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: dos funciones que vuelven atómica la recuperación de contraseña (corrección de la auditoría de seguridad, 13-11-2026) y la tabla que apoya a una de ellas.
--   - `restablecer_contrasena_atomico`: usa el enlace Y guarda la contraseña nueva en una sola transacción. Si algo falla al guardar la contraseña, el enlace NO queda gastado
--     (antes se marcaba como usado primero y, si el guardado fallaba, la persona se quedaba sin contraseña nueva y sin enlace).
--   - `reservar_recuperacion`: reserva el envío de un enlace de recuperación de forma atómica (dos solicitudes simultáneas del mismo correo no pueden enviar dos correos) y aplica
--     la espera y el máximo diario por CORREO, exista o no una cuenta con él, para que la respuesta sea idéntica en ambos casos y no se pueda saber qué cuentas existen.
--   - Tabla `solicitudes_recuperacion`: una fila por solicitud, con el hash SHA-256 del correo (nunca el correo) y el instante. La usa `reservar_recuperacion`.
-- Las usa herramientas/verificacion_correo.py (llamadas con `cliente.rpc(...)`) y herramientas/gestor_autenticacion.py.
-- Motor: PostgreSQL (Supabase o cPanel). Ejecutar DESPUÉS de verificacion_correo.sql (necesita `usuarios` y `enlaces_correo`) y ANTES de actualizar el código en el servidor:
-- sin estas funciones la recuperación de contraseña responde con un error neutro (no se pierde ningún enlace). Es idempotente: se puede volver a ejecutar.

-- -------------------------------------------
-- Estructura de tabla para la tabla `solicitudes_recuperacion` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS solicitudes_recuperacion (

        -- TITULO IDENTIFICACION

            -- Identificador de la solicitud.
            id BIGSERIAL PRIMARY KEY,
            -- Hash SHA-256 (hexadecimal) del correo escrito, ya en minúsculas y sin espacios. No se guarda el correo.
            correo_hash TEXT NOT NULL,

        -- TITULO CONTROL

            -- Instante de la solicitud.
            solicitada_en TIMESTAMPTZ NOT NULL
    );

    -- Para contar rápido las solicitudes recientes de un correo.
    CREATE INDEX IF NOT EXISTS solicitudes_recuperacion_correo ON solicitudes_recuperacion (correo_hash, solicitada_en DESC);

-- -------------------------------------------
-- Función `reservar_recuperacion` --
-- -------------------------------------------

    -- TITULO RESERVAR RECUPERACION

        -- Descripción: reserva el envío de un enlace de recuperación. Un bloqueo por correo hace que las solicitudes simultáneas del mismo correo se atiendan una tras otra.
        -- Devuelve una fila con:
        --   estado = 'limite'    ya se pidió el máximo de enlaces en el último día (`segundos` = 0);
        --   estado = 'espera'    todavía no pasó la espera entre solicitudes (`segundos` = lo que falta);
        --   estado = 'reservado' la solicitud quedó anotada; si hay usuario, se invalidaron sus enlaces de recuperación anteriores y se creó el nuevo (`solicitud_id` = su identificador,
        --                        para poder liberarlo si el correo no se puede enviar). Sin usuario (el correo no tiene cuenta) también responde 'reservado', sin crear ningún enlace.
        -- Parámetros: correo normalizado (hash), usuario (NULL si no existe), hash del enlace nuevo, espera y vigencia en segundos, máximo por día y el instante actual de la aplicación.
        CREATE OR REPLACE FUNCTION reservar_recuperacion(p_correo_hash TEXT, p_usuario BIGINT, p_token_hash TEXT, p_espera_s INTEGER, p_maximo_dia INTEGER,
                                                         p_vigencia_s INTEGER, p_ahora TIMESTAMPTZ DEFAULT now())
        RETURNS TABLE (estado TEXT, segundos INTEGER, solicitud_id BIGINT)
        LANGUAGE plpgsql AS $$
        DECLARE
            v_hoy INTEGER;
            v_ultima TIMESTAMPTZ;
            v_faltan INTEGER;
            v_id BIGINT;
        BEGIN
            PERFORM pg_advisory_xact_lock(hashtext(p_correo_hash));
            DELETE FROM solicitudes_recuperacion s WHERE s.correo_hash = p_correo_hash AND s.solicitada_en < p_ahora - INTERVAL '2 days';
            SELECT count(*), max(s.solicitada_en) INTO v_hoy, v_ultima
              FROM solicitudes_recuperacion s WHERE s.correo_hash = p_correo_hash AND s.solicitada_en > p_ahora - INTERVAL '1 day';
            IF v_hoy >= p_maximo_dia THEN
                RETURN QUERY SELECT 'limite'::TEXT, 0, NULL::BIGINT;
                RETURN;
            END IF;
            IF v_ultima IS NOT NULL AND v_ultima + make_interval(secs => p_espera_s) > p_ahora THEN
                v_faltan := CEIL(EXTRACT(EPOCH FROM (v_ultima + make_interval(secs => p_espera_s) - p_ahora)))::INTEGER;
                RETURN QUERY SELECT 'espera'::TEXT, v_faltan, NULL::BIGINT;
                RETURN;
            END IF;
            INSERT INTO solicitudes_recuperacion (correo_hash, solicitada_en) VALUES (p_correo_hash, p_ahora) RETURNING id INTO v_id;
            IF p_usuario IS NOT NULL THEN
                UPDATE enlaces_correo e SET usado_en = p_ahora WHERE e.usuario_id = p_usuario AND e.tipo = 'recuperacion' AND e.usado_en IS NULL;
                INSERT INTO enlaces_correo (usuario_id, tipo, token_hash, creado_en, expira_en)
                VALUES (p_usuario, 'recuperacion', p_token_hash, p_ahora, p_ahora + make_interval(secs => p_vigencia_s));
            END IF;
            RETURN QUERY SELECT 'reservado'::TEXT, 0, v_id;
        END
        $$;

-- -------------------------------------------
-- Función `restablecer_contrasena_atomico` --
-- -------------------------------------------

    -- TITULO RESTABLECER CONTRASENA ATOMICO

        -- Descripción: marca como usado el enlace de recuperación (solo si existe, es de recuperación, no se usó y no venció) y guarda la contraseña nueva, todo en una transacción:
        -- si el segundo paso falla, se deshace el primero y el enlace sigue sirviendo. Si `p_verificar` es verdadero deja además el correo como verificado (quien recibió el enlace
        -- demostró que controla ese correo). Devuelve una fila con el usuario (`id_usuario`), o ninguna fila si el enlace no sirve. La contraseña llega ya cifrada.
        CREATE OR REPLACE FUNCTION restablecer_contrasena_atomico(p_token_hash TEXT, p_password_hash TEXT, p_verificar BOOLEAN DEFAULT FALSE, p_ahora TIMESTAMPTZ DEFAULT now())
        RETURNS TABLE (id_usuario BIGINT)
        LANGUAGE plpgsql AS $$
        DECLARE
            v_usuario BIGINT;
        BEGIN
            UPDATE enlaces_correo e SET usado_en = p_ahora
             WHERE e.token_hash = p_token_hash AND e.tipo = 'recuperacion' AND e.usado_en IS NULL AND e.expira_en > p_ahora
            RETURNING e.usuario_id INTO v_usuario;
            IF v_usuario IS NULL THEN
                RETURN;
            END IF;
            UPDATE usuarios u SET password_hash = p_password_hash WHERE u.id = v_usuario;
            IF p_verificar THEN
                UPDATE usuarios u SET correo_verificado = TRUE, correo_verificado_en = p_ahora WHERE u.id = v_usuario;
            END IF;
            RETURN QUERY SELECT v_usuario;
        END
        $$;

-- -------------------------------------------
-- Seguridad y permisos --
-- -------------------------------------------

    -- TITULO SEGURIDAD

        -- Descripción: en Supabase, RLS activo y sin políticas en la tabla nueva (la clave pública anon no puede leer ni escribir nada). El servidor usa service_role (o el usuario de la base en
        -- PostgreSQL de cPanel), que necesita permisos explícitos porque las tablas se crean sin permisos (sin ellos aparece "permission denied", código 42501).
        -- Solo si existe el rol `service_role` (Supabase) se activa RLS y se le dan permisos. En el PostgreSQL de cPanel NO se activa RLS: el usuario de la base no es el dueño de la tabla y, sin
        -- una política, RLS le impediría escribir ("new row violates row-level security policy"); allí los permisos se dan al usuario de la base (ver la nota de abajo).
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
                ALTER TABLE solicitudes_recuperacion ENABLE ROW LEVEL SECURITY;
                GRANT USAGE ON SCHEMA public TO service_role;
                GRANT ALL ON TABLE public.solicitudes_recuperacion TO service_role;
                GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
            END IF;
        END $$;

        -- PostgreSQL de cPanel: dar los permisos al usuario de la base (el mismo de los demás GRANT del proyecto):
        --   GRANT ALL ON TABLE solicitudes_recuperacion TO vptzmybcspqcmxjgjakx;
        --   GRANT USAGE, SELECT ON SEQUENCE solicitudes_recuperacion_id_seq TO vptzmybcspqcmxjgjakx;

    -- TITULO COMPROBACION

        -- Un enlace que no existe no cambia nada y devuelve cero filas (se puede ejecutar sin riesgo):
        --   SELECT * FROM restablecer_contrasena_atomico('hash-que-no-existe', 'x');
        -- Solicitudes recientes de recuperación (sin correos, solo hashes):
        --   SELECT id, left(correo_hash, 8), solicitada_en FROM solicitudes_recuperacion ORDER BY solicitada_en DESC LIMIT 10;


-- -------------------------------------------------------------------------------------------------------
-- ------------------------------- FIN Piña y Jara recuperacion_atomica .SQL -----------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
