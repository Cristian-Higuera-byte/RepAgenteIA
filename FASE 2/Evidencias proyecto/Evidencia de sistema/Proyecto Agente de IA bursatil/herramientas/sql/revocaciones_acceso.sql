-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ------------------------------ INICIO Piña y Jara revocaciones_acceso .SQL ----------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: registro de los cierres de sesión que deben alcanzar al servidor de datos. El navegador habla directo con ese servidor (otro proceso, sin acceso a la memoria de
-- Streamlit) usando un token firmado que dura hasta 12 horas. Para que cerrar sesión, cerrar todas las sesiones o cambiar la contraseña invaliden también ese token y sus conexiones
-- abiertas, cada cierre deja aquí una fila que el servidor de datos consulta. Lo usan herramientas/token_datos.py y servidor_precios/manejador.py.
--   - `sesion` vacía (NULL): el usuario cerró TODAS sus sesiones o cambió su contraseña; vale para todo token emitido antes de `desde`.
--   - `sesion` con valor: se cerró esa sesión (huella de su token de la URL); vale solo para los tokens emitidos desde ella.
-- Motor: PostgreSQL (Supabase o cPanel). Ejecutar DESPUÉS de crear la tabla `usuarios`. Es idempotente: se puede volver a ejecutar sin perder datos.
-- Las filas con más de 13 horas ya no tienen efecto (ningún token dura tanto) y el propio programa las borra al registrar un cierre nuevo.
-- Seguridad: no guarda tokens ni contraseñas; solo el usuario, la huella de la sesión y el instante del cierre.

-- -------------------------------------------
-- Estructura de tabla para la tabla `revocaciones_acceso` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS revocaciones_acceso (

        -- TITULO IDENTIFICACION

            -- Identificador de la revocación.
            id BIGSERIAL PRIMARY KEY,
            -- Usuario al que afecta; al borrar el usuario se borran sus revocaciones.
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            -- Huella (16 caracteres hexadecimales) de la sesión cerrada, o NULL cuando el cierre alcanza a todas las sesiones del usuario.
            sesion TEXT,

        -- TITULO CONTROL

            -- Instante del cierre, en segundos desde 1970 (la misma escala que la hora de emisión del token).
            desde DOUBLE PRECISION NOT NULL
    );

    -- Para que el servidor de datos encuentre rápido las revocaciones de un usuario.
    CREATE INDEX IF NOT EXISTS revocaciones_acceso_usuario ON revocaciones_acceso (usuario_id, desde);

-- -------------------------------------------
-- Seguridad y permisos --
-- -------------------------------------------

    -- TITULO SEGURIDAD

        -- Descripción: RLS activo y sin políticas (la clave pública anon no puede leer ni escribir nada). El servidor usa service_role (o el usuario de la base en PostgreSQL de cPanel),
        -- que necesita permisos explícitos porque las tablas se crean sin permisos (sin ellos aparece "permission denied", código 42501).
        ALTER TABLE revocaciones_acceso ENABLE ROW LEVEL SECURITY;
        GRANT USAGE ON SCHEMA public TO service_role;
        GRANT ALL ON TABLE public.revocaciones_acceso TO service_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

    -- TITULO CONSULTAS DE EJEMPLO

        -- Revocaciones vigentes de un usuario:
        --   SELECT sesion, to_timestamp(desde) FROM revocaciones_acceso WHERE usuario_id = 1 ORDER BY desde DESC;
        -- Limpiar las que ya no tienen efecto (más de 13 horas):
        --   DELETE FROM revocaciones_acceso WHERE desde < extract(epoch FROM now()) - 13 * 3600;


-- -------------------------------------------------------------------------------------------------------
-- ------------------------------- FIN Piña y Jara revocaciones_acceso .SQL ------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
