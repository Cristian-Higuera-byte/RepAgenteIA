-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- --------------------- INICIO Piña y Jara Base de Datos pyj-bursatil-plataforma .SQL -------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: esquema de la plataforma bursátil multiusuario (proyecto Supabase `pyj-bursatil-plataforma`).
-- Motor: PostgreSQL. Ejecutar una vez en el editor SQL de Supabase.
-- Seguridad: todas las tablas tienen RLS activo y SIN políticas; la aplicación accede solo desde el servidor
-- con la clave service_role (que ignora RLS), así la clave pública (anon) no puede leer ni escribir nada.

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

    ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------
-- Estructura de tabla para la tabla `watchlist_usuario` --
-- ----------------------------------------------------

    CREATE TABLE IF NOT EXISTS watchlist_usuario (

        -- TITULO IDENTIFICACION

            -- Identificador de la fila.
            id BIGSERIAL PRIMARY KEY,
            -- Usuario dueño de la lista; al borrar el usuario se borra su lista.
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,

        -- TITULO ACTIVO

            -- Símbolo del activo (por ejemplo GOLD o EURUSD).
            simbolo TEXT NOT NULL,
            -- TRUE si está en favoritos (los que se muestran en la barra de favoritos).
            favorito BOOLEAN NOT NULL DEFAULT FALSE,

        -- TITULO CONTROL

            -- Fecha en que se agregó el activo.
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),

        -- Un mismo símbolo no puede repetirse en la lista de un usuario.
        UNIQUE (usuario_id, simbolo)
    );

    ALTER TABLE watchlist_usuario ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------
-- Estructura de tabla para la tabla `credenciales_bolsa` --
-- ---------------------------------------------------------

    -- Descripción: credenciales de la API de Capital.com de cada usuario, SIEMPRE cifradas por la aplicación
    -- (ver herramientas/credenciales_bolsa.py). Un usuario puede tener una cuenta real y una demo.

    CREATE TABLE IF NOT EXISTS credenciales_bolsa (

        -- TITULO IDENTIFICACION DE LA CUENTA

            -- Usuario dueño de las credenciales; al borrar el usuario se borran también.
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            -- Modo de la cuenta: TRUE = demo, FALSE = real.
            es_demo BOOLEAN NOT NULL,

        -- TITULO DATOS CIFRADOS (Fernet; la clave maestra vive solo en el .env del servidor)

            -- Correo de la cuenta de Capital.com.
            identificador_cifrado TEXT NOT NULL,
            -- API key generada en Capital.com (con permiso de operar y sin retiro).
            api_key_cifrada TEXT NOT NULL,
            -- Contraseña de la API key (la que define la propia key, no la de la cuenta).
            api_contrasena_cifrada TEXT NOT NULL,

        -- TITULO CONTROL

            -- Versión del formato guardado, por si cambian los campos en el futuro.
            version SMALLINT NOT NULL DEFAULT 1,
            -- Fecha de la última modificación (la actualiza el disparador de más abajo).
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),

        -- Una cuenta real y una demo por usuario.
        PRIMARY KEY (usuario_id, es_demo)
    );

    ALTER TABLE credenciales_bolsa ENABLE ROW LEVEL SECURITY;

    -- TITULO ACTUALIZAR FECHA DE MODIFICACION

        -- Descripción: antes de cada UPDATE refresca `actualizado_en` con la hora actual.
        CREATE OR REPLACE FUNCTION credenciales_bolsa_actualizado() RETURNS TRIGGER
        SET search_path = public AS $$
        BEGIN
            NEW.actualizado_en = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS credenciales_bolsa_fecha ON credenciales_bolsa;
        CREATE TRIGGER credenciales_bolsa_fecha BEFORE UPDATE ON credenciales_bolsa
            FOR EACH ROW EXECUTE FUNCTION credenciales_bolsa_actualizado();


-- ----------------------------------------------------
-- Permisos del rol del servidor (`service_role`) --
-- ----------------------------------------------------

    -- TITULO PERMISOS DEL SERVIDOR

        -- Descripción: el proyecto se creó con "Automatically expose new tables" DESACTIVADO, así que las tablas
        -- nacen sin permisos y el servidor falla con "permission denied" (código 42501). Solo se le dan permisos a
        -- service_role; anon y authenticated siguen sin acceso a nada.
        GRANT USAGE ON SCHEMA public TO service_role;
        GRANT ALL ON TABLE public.usuarios, public.watchlist_usuario, public.credenciales_bolsa TO service_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- --------------------------------------------------------
-- Tabla `perfiles_usuario` (la crea componentes_plataforma/perfil/esquema.sql) --
-- --------------------------------------------------------

    -- TITULO PERFIL DE USUARIO: SEGURIDAD

        -- Descripción: la tabla del perfil (datos personales: documento, teléfono, dirección) se crea ejecutando
        -- componentes_plataforma/perfil/esquema.sql y, en este proyecto, se le agrega lo mismo que a las demás:
        -- RLS sin políticas y permisos solo para el rol del servidor.
        -- Si la tabla todavía no existe (primera vez), este paso se omite: el script del perfil lo repite al terminar.
        DO $$
        BEGIN
            IF to_regclass('public.perfiles_usuario') IS NOT NULL THEN
                ALTER TABLE perfiles_usuario ENABLE ROW LEVEL SECURITY;
                GRANT ALL ON TABLE public.perfiles_usuario TO service_role;
            END IF;
        END $$;


-- -------------------------------------------------------------------------------------------------------
-- --------------------- FIN Piña y Jara Base de Datos pyj-bursatil-plataforma .SQL ----------------------
-- -------------------------------------------------------------------------------------------------------


-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
