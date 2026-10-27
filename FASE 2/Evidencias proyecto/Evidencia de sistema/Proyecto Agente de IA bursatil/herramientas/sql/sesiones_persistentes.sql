-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ---------------------------- INICIO Piña y Jara sesiones_persistentes .SQL ----------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: sesiones que se mantienen abiertas al cerrar el navegador («mantener sesión iniciada»). Cada fila es un dispositivo: el navegador guarda en una cookie
-- un token aleatorio y aquí se guarda solo su hash SHA-256 (nunca el token), el usuario y cuándo vence. Lo usa herramientas/sesion_persistente.py.
-- Motor: PostgreSQL (Supabase). Ejecutar en SQL Editor > New query > Run, DESPUÉS de crear la tabla `usuarios`.
-- Es idempotente: se puede volver a ejecutar sin perder datos.
-- Seguridad: RLS activo y SIN políticas; solo el servidor, con la clave service_role, lee y escribe esta tabla.

-- -------------------------------------------
-- Estructura de tabla para la tabla `sesiones_persistentes` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS sesiones_persistentes (

        -- TITULO IDENTIFICACION

            -- Identificador de la sesión (uno por dispositivo y por inicio de sesión).
            id BIGSERIAL PRIMARY KEY,
            -- Usuario dueño de la sesión; al borrar el usuario se borran sus sesiones.
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            -- Hash SHA-256 (hexadecimal) del token que vive en la cookie del navegador. Único: así se busca la sesión sin guardar el token.
            token_hash TEXT NOT NULL UNIQUE,

        -- TITULO CONTROL

            -- Cuándo se creó, cuándo vence (30 días después, definido en sesion_persistente.py) y la última vez que se usó para volver a entrar.
            creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            expira_en TIMESTAMPTZ NOT NULL,
            ultimo_uso TIMESTAMPTZ NOT NULL DEFAULT now(),
            -- Navegador o dispositivo (resumen del User-Agent), solo para reconocer la sesión al revisar la tabla.
            dispositivo TEXT
    );

    -- Para encontrar rápido las sesiones de un usuario y borrar las vencidas.
    CREATE INDEX IF NOT EXISTS sesiones_persistentes_usuario ON sesiones_persistentes (usuario_id, expira_en);

-- -------------------------------------------
-- Seguridad y permisos --
-- -------------------------------------------

    -- TITULO SEGURIDAD

        -- Descripción: RLS activo y sin políticas (la clave pública anon no puede leer ni escribir nada). El servidor usa service_role, que
        -- necesita permisos explícitos porque el proyecto crea las tablas sin permisos (sin ellos aparece "permission denied", código 42501).
        ALTER TABLE sesiones_persistentes ENABLE ROW LEVEL SECURITY;
        GRANT USAGE ON SCHEMA public TO service_role;
        GRANT ALL ON TABLE public.sesiones_persistentes TO service_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

        -- Para ver las sesiones abiertas de cada usuario (consulta de ejemplo):
        --   SELECT u.email, s.dispositivo, s.creada_en, s.expira_en, s.ultimo_uso
        --   FROM sesiones_persistentes s JOIN usuarios u ON u.id = s.usuario_id ORDER BY s.ultimo_uso DESC;
        -- Para cerrar todas las sesiones de un usuario desde Supabase:
        --   DELETE FROM sesiones_persistentes WHERE usuario_id = 1;


-- -------------------------------------------------------------------------------------------------------
-- ----------------------------- FIN Piña y Jara sesiones_persistentes .SQL ------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
