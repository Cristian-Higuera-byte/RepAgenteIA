-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- --------------------------- INICIO Piña y Jara Tabla usuarios (acceso) .SQL ---------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: crea la tabla `usuarios` (nombre, correo y contraseña de acceso a la plataforma) que usa
-- herramientas/gestor_autenticacion.py. Motor: PostgreSQL (Supabase). Ejecutar en SQL Editor > New query > Run.
-- Es idempotente: se puede ejecutar de nuevo sin perder datos. La contraseña nunca se guarda en claro, solo su hash.
-- Debe ejecutarse ANTES de las tablas que dependen de ella (perfiles_usuario, watchlist_usuario, credenciales_bolsa).

-- -------------------------------------------
-- Estructura de tabla para la tabla `usuarios` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS usuarios (

        -- TITULO IDENTIFICACION

            -- Identificador interno del usuario.
            id BIGSERIAL PRIMARY KEY,
            -- Nombre visible en la barra superior.
            nombre TEXT NOT NULL,
            -- Correo de acceso (único, guardado en minúsculas por la aplicación).
            email TEXT NOT NULL UNIQUE,

        -- TITULO ACCESO

            -- Hash PBKDF2-HMAC-SHA256 con sal, formato 'sal$hash'. La contraseña nunca se guarda en claro.
            password_hash TEXT NOT NULL,

        -- TITULO CONTROL

            -- Fecha de creación de la cuenta.
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

-- -------------------------------------------
-- Seguridad y permisos --
-- -------------------------------------------

    -- TITULO SEGURIDAD

        -- Descripción: RLS activo y SIN políticas: la clave pública (anon) no puede leer ni escribir nada. La aplicación
        -- accede solo desde el servidor con la clave service_role, a la que se le dan permisos explícitos (el proyecto
        -- crea las tablas sin permisos y, sin esto, el servidor falla con "permission denied", código 42501).
        ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
        GRANT USAGE ON SCHEMA public TO service_role;
        GRANT ALL ON TABLE public.usuarios TO service_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- -------------------------------------------------------------------------------------------------------
-- ---------------------------- FIN Piña y Jara Tabla usuarios (acceso) .SQL -----------------------------
-- -------------------------------------------------------------------------------------------------------


-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
