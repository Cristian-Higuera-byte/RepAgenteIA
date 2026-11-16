-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ---------------------------- INICIO Piña y Jara verificacion_correo .SQL ------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: verificación del correo al registrarse y recuperación de contraseña. Agrega a `usuarios` el estado «correo verificado» y crea la tabla
-- `enlaces_correo`, donde cada fila es un enlace de un solo uso que se envía por correo (de verificación o de recuperación). Solo se guarda el hash
-- SHA-256 del enlace, nunca el enlace, igual que en las sesiones persistentes. Lo usa herramientas/verificacion_correo.py.
-- Motor: PostgreSQL 10 o superior, tanto el de un hosting (phpPgAdmin > pestaña SQL) como Supabase (SQL Editor > New query > Run).
-- Ejecutar DESPUÉS de crear la tabla `usuarios`. Es idempotente: se puede volver a ejecutar sin perder datos.
-- Cuentas existentes: la primera vez que se ejecuta, las cuentas que ya existen pasan a «verificadas» para que nadie quede fuera. Las siguientes veces ese
-- paso NO se repite, de modo que una cuenta nueva sin verificar nunca se marca como verificada por volver a ejecutar este archivo.
-- Seguridad: en Supabase (donde existe el rol `service_role`) se activa RLS sin políticas y se dan permisos solo a ese rol; en otro PostgreSQL ese bloque no
-- hace nada. En un hosting hay que dar además permisos al usuario de la base de datos que usa la plataforma (ver la nota del final).

-- -------------------------------------------
-- Estructura de tabla para la tabla `usuarios` (estado del correo) --
-- -------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'usuarios' AND column_name = 'correo_verificado') THEN
        ALTER TABLE usuarios ADD COLUMN correo_verificado BOOLEAN NOT NULL DEFAULT FALSE;
        ALTER TABLE usuarios ADD COLUMN correo_verificado_en TIMESTAMPTZ;
        UPDATE usuarios SET correo_verificado = TRUE, correo_verificado_en = now();
    END IF;
END $$;

-- -------------------------------------------
-- Estructura de tabla para la tabla `enlaces_correo` --
-- -------------------------------------------

CREATE TABLE IF NOT EXISTS enlaces_correo (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('verificacion', 'recuperacion')),
    token_hash TEXT NOT NULL UNIQUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_en TIMESTAMPTZ NOT NULL,
    usado_en TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS enlaces_correo_usuario ON enlaces_correo (usuario_id, tipo, creado_en DESC);

-- -------------------------------------------
-- Permisos en Supabase (no hace nada en otro PostgreSQL) --
-- -------------------------------------------

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
        ALTER TABLE enlaces_correo ENABLE ROW LEVEL SECURITY;
        GRANT ALL ON TABLE public.usuarios, public.enlaces_correo TO service_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
    END IF;
END $$;

-- Nota para un hosting (cPanel): las tablas nuevas no heredan permisos. Después de ejecutar este archivo, volver a dar permisos al usuario de la base de
-- datos de la plataforma, cambiando <usuario> por su nombre (la variable POSTGRES_USUARIO del .env):
--   GRANT ALL ON ALL TABLES IN SCHEMA public TO "<usuario>";
--   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "<usuario>";

-- -------------------------------------------------------------------------------------------------------
-- ----------------------------- FIN Piña y Jara verificacion_correo .SQL --------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
