-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ---------------------------------- INICIO Piña y Jara perfil_apellidos .SQL ---------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: agrega a `perfiles_usuario` las columnas `apellido_paterno` y `apellido_materno`. El registro y el perfil piden ambos apellidos por separado;
-- la columna `apellidos` se sigue llenando con los dos juntos (la usan la cabecera del perfil y el nombre visible).
-- Motor: PostgreSQL 10 o superior, tanto el de un hosting (phpPgAdmin > pestaña SQL) como Supabase (SQL Editor > New query > Run).
-- Ejecutar DESPUÉS de crear la tabla `perfiles_usuario`. Es idempotente. Hay que ejecutarlo ANTES de subir el código nuevo: sin las columnas el guardado del perfil falla.

-- -------------------------------------------
-- Columnas nuevas de la tabla `perfiles_usuario` --
-- -------------------------------------------

ALTER TABLE perfiles_usuario ADD COLUMN IF NOT EXISTS apellido_paterno TEXT;
ALTER TABLE perfiles_usuario ADD COLUMN IF NOT EXISTS apellido_materno TEXT;

-- Nota para un hosting (cPanel): si el usuario de la base de datos de la plataforma no es el dueño de la tabla, ejecutar este archivo con el usuario dueño.
-- Las cuentas existentes quedan con las columnas vacías: al abrir su perfil el formulario sugiere el reparto a partir de `apellidos` y se guarda al pulsar «Guardar cambios».

-- -------------------------------------------------------------------------------------------------------
-- ----------------------------------- FIN Piña y Jara perfil_apellidos .SQL -----------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
