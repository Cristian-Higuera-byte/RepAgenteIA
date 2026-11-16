-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ------------------------------------- INICIO Piña y Jara roles .SQL -----------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: agrega a la tabla `usuarios` la columna `rol` para distinguir a los usuarios normales de los administradores («root»). Solo los root ven las secciones
-- internas de la plataforma (hoy, el Laboratorio). Lo lee herramientas/roles.py. Todos los usuarios existentes quedan como «usuario».
-- Motor: PostgreSQL 10 o superior, tanto el de un hosting (phpPgAdmin > pestaña SQL) como Supabase (SQL Editor > New query > Run).
-- Es idempotente: se puede volver a ejecutar sin perder datos. Si la columna no existe, nadie es root por esta vía (sigue valiendo la variable ROOT_CORREOS del .env).

-- -------------------------------------------
-- Estructura de la columna `rol` en la tabla `usuarios` --
-- -------------------------------------------

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol TEXT NOT NULL DEFAULT 'usuario';

-- Solo se admiten dos valores.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'usuarios_rol_valido') THEN
        ALTER TABLE usuarios ADD CONSTRAINT usuarios_rol_valido CHECK (rol IN ('usuario', 'root'));
    END IF;
END $$;

-- -------------------------------------------
-- Cómo crear un usuario root --
-- -------------------------------------------

-- El usuario primero se registra y confirma su correo de forma normal. Después, desde phpPgAdmin o el SQL Editor (nunca desde la plataforma), cambiar su rol
-- cambiando el correo del ejemplo. El cambio rige en menos de un minuto (si no, reiniciar Streamlit):
--   UPDATE usuarios SET rol = 'root' WHERE email = 'persona@ejemplo.cl';
-- Para quitar el permiso:
--   UPDATE usuarios SET rol = 'usuario' WHERE email = 'persona@ejemplo.cl';
-- Para ver quiénes son root:
--   SELECT id, nombre, email FROM usuarios WHERE rol = 'root';

-- Nota para un hosting (cPanel): si el usuario de la base de datos de la plataforma no es el dueño de la tabla, ejecutar este archivo con el usuario dueño y repetir
-- los permisos (GRANT ALL ON ALL TABLES IN SCHEMA public TO "<usuario>").

-- -------------------------------------------------------------------------------------------------------
-- -------------------------------------- FIN Piña y Jara roles .SQL -------------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
