-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- -------------------------------- INICIO Piña y Jara planes_usuario .SQL -------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: planes de los usuarios de la plataforma (Gratis, Básico, Pro y Avanzado) y el historial de cambios de plan.
-- Motor: PostgreSQL (Supabase). Ejecutar en SQL Editor > New query > Run, DESPUÉS de crear la tabla `usuarios`.
-- Es idempotente: se puede volver a ejecutar sin perder datos.
-- Seguridad: RLS activo y SIN políticas; solo el servidor, con la clave service_role, lee y escribe estas tablas.

-- -------------------------------------------
-- Estructura de tabla para la tabla `planes_usuario` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS planes_usuario (

        -- TITULO IDENTIFICACION

            -- Usuario dueño del plan (uno por usuario); al borrar el usuario se borra su plan.
            usuario_id BIGINT PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,

        -- TITULO PLAN

            -- Clave del plan: gratis, basico, pro o avanzado (las mismas de PLANES_IA en configuracion.py).
            plan TEXT NOT NULL CHECK (plan IN ('gratis', 'basico', 'pro', 'avanzado')),
            -- De dónde viene el plan: prueba (elegido en la vista de Planes mientras no se cobra), pago o admin.
            origen TEXT NOT NULL DEFAULT 'prueba' CHECK (origen IN ('prueba', 'pago', 'admin')),

        -- TITULO CONTROL

            -- Cuándo se asignó el plan por primera vez y cuándo se cambió por última vez.
            desde TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

-- -------------------------------------------
-- Estructura de tabla para la tabla `planes_historial` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS planes_historial (

        -- Identificador de la fila.
        id BIGSERIAL PRIMARY KEY,
        -- Usuario que cambió de plan.
        usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        -- Plan anterior (vacío la primera vez) y plan nuevo.
        plan_anterior TEXT,
        plan_nuevo TEXT NOT NULL,
        -- De dónde viene el cambio y cuándo ocurrió.
        origen TEXT NOT NULL DEFAULT 'prueba',
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    -- Para consultar rápido los cambios de un usuario.
    CREATE INDEX IF NOT EXISTS planes_historial_usuario ON planes_historial (usuario_id, creado_en DESC);

-- -------------------------------------------
-- Seguridad y permisos --
-- -------------------------------------------

    -- TITULO SEGURIDAD

        -- Descripción: RLS activo y sin políticas (la clave pública anon no puede leer ni escribir nada). El servidor usa service_role, que
        -- necesita permisos explícitos porque el proyecto crea las tablas sin permisos (sin ellos aparece "permission denied", código 42501).
        ALTER TABLE planes_usuario ENABLE ROW LEVEL SECURITY;
        ALTER TABLE planes_historial ENABLE ROW LEVEL SECURITY;
        GRANT USAGE ON SCHEMA public TO service_role;
        GRANT ALL ON TABLE public.planes_usuario, public.planes_historial TO service_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

        -- Para ver el plan de cada usuario y cuántos hay por plan (consulta de ejemplo):
        --   SELECT plan, COUNT(*) FROM planes_usuario GROUP BY plan;


-- -------------------------------------------------------------------------------------------------------
-- --------------------------------- FIN Piña y Jara planes_usuario .SQL ---------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
