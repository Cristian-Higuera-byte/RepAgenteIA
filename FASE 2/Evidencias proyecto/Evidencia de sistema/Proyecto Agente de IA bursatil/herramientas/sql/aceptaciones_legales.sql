-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ----------------------------- INICIO Piña y Jara aceptaciones_legales .SQL ----------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: constancia de qué documentos legales aceptó cada usuario (términos de uso, privacidad y cookies, aviso de riesgo), con su versión y la fecha. Una fila por
-- documento aceptado; se escribe cuando el usuario marca la casilla al crear su cuenta. Lo usa herramientas/aceptaciones_legales.py.
-- Motor: PostgreSQL 10 o superior, tanto el de un hosting (phpPgAdmin > pestaña SQL) como Supabase (SQL Editor > New query > Run).
-- Ejecutar DESPUÉS de crear la tabla `usuarios`. Es idempotente: se puede volver a ejecutar sin perder datos.
-- Si esta tabla no existe, la plataforma sigue funcionando: solo que no queda registrada la aceptación.

-- -------------------------------------------
-- Estructura de tabla para la tabla `aceptaciones_legales` --
-- -------------------------------------------

CREATE TABLE IF NOT EXISTS aceptaciones_legales (
    id BIGSERIAL PRIMARY KEY,
    -- Usuario que aceptó; si se borra el usuario se borran sus aceptaciones.
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    -- Documento aceptado: terminos, privacidad o riesgo (claves de componentes_plataforma/legal/contenido.py).
    documento TEXT NOT NULL,
    -- Versión del documento que se aceptó (VERSION de contenido.py) y cuándo.
    version TEXT NOT NULL,
    aceptada_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS aceptaciones_legales_usuario ON aceptaciones_legales (usuario_id, documento, aceptada_en DESC);

-- -------------------------------------------
-- Permisos en Supabase (no hace nada en otro PostgreSQL) --
-- -------------------------------------------

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
        ALTER TABLE aceptaciones_legales ENABLE ROW LEVEL SECURITY;
        GRANT ALL ON TABLE public.aceptaciones_legales TO service_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
    END IF;
END $$;

-- Nota para un hosting (cPanel): las tablas nuevas no heredan permisos. Después de ejecutar este archivo, dar permisos al usuario de la base de datos de la
-- plataforma, cambiando <usuario> por su nombre (la variable POSTGRES_USUARIO del .env):
--   GRANT ALL ON ALL TABLES IN SCHEMA public TO "<usuario>";
--   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "<usuario>";

-- Para ver quién aceptó qué (consulta de ejemplo):
--   SELECT u.email, a.documento, a.version, a.aceptada_en FROM aceptaciones_legales a JOIN usuarios u ON u.id = a.usuario_id ORDER BY a.aceptada_en DESC;

-- -------------------------------------------------------------------------------------------------------
-- ------------------------------ FIN Piña y Jara aceptaciones_legales .SQL ------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
