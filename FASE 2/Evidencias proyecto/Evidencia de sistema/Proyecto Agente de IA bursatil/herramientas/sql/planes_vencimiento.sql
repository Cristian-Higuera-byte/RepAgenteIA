-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ---------------------------------- INICIO Piña y Jara planes_vencimiento .SQL -------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: agrega a `planes_usuario` la columna `vence_en`, la fecha hasta la que vale un plan de pago. Pasada esa fecha el usuario cuenta como Gratis (lo aplica
-- herramientas/plan_usuario.py sin tocar la fila). El plan Gratis y los planes sin fecha (por ejemplo los asignados a mano sin días) no vencen. La muestran la vista Planes
-- y la barra de uso del chat. Cuando exista el pago con Flow, cada pago fijará aquí la nueva fecha.
-- Motor: PostgreSQL 10 o superior, tanto el de un hosting (phpPgAdmin > pestaña SQL) como Supabase (SQL Editor > New query > Run).
-- Ejecutar DESPUÉS de crear la tabla `planes_usuario`. Es idempotente. Si la columna no existe, la plataforma funciona como antes, sin vencimientos.

-- -------------------------------------------
-- Columna `vence_en` de la tabla `planes_usuario` --
-- -------------------------------------------

ALTER TABLE planes_usuario ADD COLUMN IF NOT EXISTS vence_en TIMESTAMPTZ;

-- Nota para un hosting (cPanel): si el usuario de la base de datos de la plataforma no es el dueño de la tabla, ejecutar este archivo con el usuario dueño.

-- Para ver cuándo vence cada plan (consulta de ejemplo):
--   SELECT u.email, p.plan, p.vence_en FROM planes_usuario p JOIN usuarios u ON u.id = p.usuario_id ORDER BY p.vence_en NULLS LAST;
-- Para fijar un vencimiento a mano (o usar `python asignar_plan.py correo plan dias`):
--   UPDATE planes_usuario SET vence_en = now() + interval '30 days' WHERE usuario_id = (SELECT id FROM usuarios WHERE email = 'persona@ejemplo.cl');
-- Para quitarlo (el plan deja de vencer):
--   UPDATE planes_usuario SET vence_en = NULL WHERE usuario_id = (SELECT id FROM usuarios WHERE email = 'persona@ejemplo.cl');

-- -------------------------------------------------------------------------------------------------------
-- ----------------------------------- FIN Piña y Jara planes_vencimiento .SQL ---------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
