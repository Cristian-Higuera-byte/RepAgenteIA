-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- ----------------------------------- INICIO Piña y Jara esquema .SQL -----------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Tabla del perfil de usuario (una fila por usuario). Ejecutar UNA vez en Supabase: SQL Editor > New query > pegar > Run.
-- Es idempotente: se puede volver a ejecutar sin perder datos (crea lo que falta y no toca lo que ya existe).
-- Requiere la tabla `usuarios` (ver herramientas/gestor_autenticacion.py), cuyo id es bigserial.

create table if not exists perfiles_usuario (
    usuario_id bigint primary key references usuarios(id) on delete cascade,
    -- Datos personales
    nombres text,
    apellidos text,
    apodo text,                              -- opcional; único sin distinguir mayúsculas (índice más abajo)
    fecha_nacimiento date,
    nacionalidad text,                       -- código de país (CL, AR...)
    genero text,
    -- Documento de identidad
    tipo_documento text,                     -- rut | cedula | pasaporte | extranjeria
    numero_documento text,
    pais_documento text,
    vencimiento_documento date,
    -- Contacto y dirección
    telefono_prefijo text,
    telefono_movil text,
    telefono_alterno text,
    pais text,
    region text,
    ciudad text,
    direccion text,
    codigo_postal text,
    -- Perfil de inversor
    situacion_laboral text,
    ocupacion text,
    fuente_fondos text,
    rango_ingresos text,
    rango_patrimonio text,
    experiencia text,
    objetivo text,
    tolerancia_riesgo text,
    instrumentos jsonb not null default '[]'::jsonb,
    es_pep boolean not null default false,
    -- Preferencias
    idioma text not null default 'es',
    zona_horaria text,
    moneda_visualizacion text not null default 'USD',
    notificaciones jsonb not null default '{}'::jsonb,
    -- Control del sistema (el formulario no escribe `verificacion`)
    verificacion text not null default 'sin_verificar',   -- sin_verificar | verificado
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

-- Apodo (para bases creadas antes de agregarlo) y su unicidad: dos usuarios no pueden tener el mismo apodo (sin distinguir mayúsculas).
-- Los apodos vacíos se guardan como NULL y no cuentan.
alter table perfiles_usuario add column if not exists apodo text;
create unique index if not exists perfiles_usuario_apodo_unico
    on perfiles_usuario (lower(apodo))
    where apodo is not null;

-- Un mismo documento no puede estar en dos cuentas distintas.
create unique index if not exists perfiles_usuario_documento_unico
    on perfiles_usuario (tipo_documento, numero_documento)
    where numero_documento is not null;

-- Seguridad: estos datos son personales. Con la clave `anon` y RLS desactivado cualquiera con la clave puede leerlos.
-- Para producción activa RLS y usa la clave de servicio (service_role) solo en el servidor:
--   alter table perfiles_usuario enable row level security;
-- (sin políticas, solo la clave de servicio puede leer y escribir).

-- Seguridad en el proyecto: RLS sin políticas y permisos solo para el rol del servidor (igual que las demás tablas; es idempotente).
DO $$
BEGIN
    IF to_regclass('public.perfiles_usuario') IS NOT NULL THEN
        ALTER TABLE perfiles_usuario ENABLE ROW LEVEL SECURITY;
        GRANT ALL ON TABLE public.perfiles_usuario TO service_role;
    END IF;
END $$;


-- -------------------------------------------------------------------------------------------------------
-- ------------------------------------- FIN Piña y Jara esquema .SQL ------------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
