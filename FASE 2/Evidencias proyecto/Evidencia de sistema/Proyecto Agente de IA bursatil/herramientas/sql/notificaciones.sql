-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- --------------------------------- INICIO Piña y Jara notificaciones .SQL ------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: historial de los avisos de la campana (respuestas y órdenes del agente, cierres de posiciones, alertas de precio). Una fila por aviso. Con esta tabla los avisos
-- sobreviven a los reinicios del servidor y se ven iguales desde cualquier dispositivo. La campana sigue funcionando desde la memoria; la tabla se escribe en segundo plano.
-- Lo usa nucleo_agente/notificaciones.py. Los avisos de más de 90 días se borran solos (una vez al día, desde la propia plataforma).
-- Motor: PostgreSQL 10 o superior, tanto el de un hosting (phpPgAdmin > pestaña SQL) como Supabase (SQL Editor > New query > Run).
-- Ejecutar DESPUÉS de crear la tabla `usuarios`. Es idempotente: se puede volver a ejecutar sin perder datos.
-- Si esta tabla no existe, la plataforma sigue funcionando: los avisos viven solo en la memoria, como antes.

-- -------------------------------------------
-- Estructura de tabla para la tabla `notificaciones` --
-- -------------------------------------------

CREATE TABLE IF NOT EXISTS notificaciones (
    -- Identificador del aviso (texto aleatorio generado por la plataforma).
    id TEXT PRIMARY KEY,
    -- Usuario dueño del aviso; si se borra el usuario se borran sus avisos.
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    -- Tipo: agente, orden, auto, error, posicion o alerta (decide el ícono en la campana).
    tipo TEXT NOT NULL DEFAULT 'agente',
    titulo TEXT NOT NULL,
    texto TEXT NOT NULL DEFAULT '',
    -- Referencia a lo que lo originó (id del turno del agente o de la vigilancia); puede quedar vacía.
    ref TEXT,
    -- leida: el usuario ya lo vio. oculta: lo quitó de la campana con «Marcar como leídas» (sigue en el historial).
    leida BOOLEAN NOT NULL DEFAULT FALSE,
    oculta BOOLEAN NOT NULL DEFAULT FALSE,
    creada TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Los avisos de un usuario, del más nuevo al más antiguo (campana e historial).
CREATE INDEX IF NOT EXISTS notificaciones_usuario ON notificaciones (usuario_id, creada DESC);
-- Para la limpieza diaria por antigüedad.
CREATE INDEX IF NOT EXISTS notificaciones_creada ON notificaciones (creada);

-- -------------------------------------------
-- Permisos en Supabase (no hace nada en otro PostgreSQL) --
-- -------------------------------------------

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
        ALTER TABLE notificaciones ENABLE ROW LEVEL SECURITY;
        GRANT ALL ON TABLE public.notificaciones TO service_role;
    END IF;
END $$;

-- Nota para un hosting (cPanel): las tablas nuevas no heredan permisos. Después de ejecutar este archivo, dar permisos al usuario de la base de datos de la
-- plataforma, cambiando <usuario> por su nombre (la variable POSTGRES_USUARIO del .env):
--   GRANT ALL ON ALL TABLES IN SCHEMA public TO "<usuario>";
--   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "<usuario>";

-- Limpieza manual (la plataforma ya lo hace sola cada día): borrar avisos de más de 90 días.
--   DELETE FROM notificaciones WHERE creada < now() - interval '90 days';
-- Para ver cuántos avisos guarda cada usuario:
--   SELECT usuario_id, count(*) FROM notificaciones GROUP BY usuario_id ORDER BY 2 DESC;

-- -------------------------------------------------------------------------------------------------------
-- ---------------------------------- FIN Piña y Jara notificaciones .SQL --------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
