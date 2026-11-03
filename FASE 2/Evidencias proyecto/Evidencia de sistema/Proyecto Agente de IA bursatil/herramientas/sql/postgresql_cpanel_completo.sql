-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.

-- -------------------------------------------------------------------------------------------------------
-- ------------------------- INICIO Piña y Jara postgresql_cpanel_completo .SQL --------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: crea las 23 tablas de la plataforma y sus funciones en un PostgreSQL común (por ejemplo, el del hosting cPanel).
-- Motor: PostgreSQL 10 o superior. Ejecutar en phpPgAdmin > pestaña SQL, con la base de datos elegida, en el orden en que está escrito:
-- las tablas que dependen de otras (claves foráneas hacia `usuarios`, `estrategias`, `copias`) van después de ellas.
-- Es idempotente: se puede volver a ejecutar sin perder datos.
-- Diferencias con los scripts de Supabase (herramientas/sql/): no activa RLS ni da permisos a `service_role`, porque ese rol solo existe en
-- Supabase; el acceso lo controla el usuario de la base de datos. El disparador usa EXECUTE PROCEDURE (PostgreSQL 10 no admite EXECUTE FUNCTION).
-- Las tablas `ordenes` y `vigilancias` no están aquí: viven en una base SQLite local del agente (data/ordenes.db).
-- Las tablas `agente_chats`, `agente_mensajes`, `agente_memoria_usuario` y `documentos_rag` no tenían script en el proyecto: sus columnas se
-- dedujeron de los campos que lee y escribe el código (nucleo_agente/memoria y herramientas/gestor_rag.py); conviene validarlas.
-- Si las funciones con «$$» dan error en el cuadro SQL, ejecutar cada bloque `CREATE OR REPLACE FUNCTION ... $$;` por separado.

-- -------------------------------------------
-- Tablas de la plataforma (19) --
-- -------------------------------------------

CREATE TABLE IF NOT EXISTS usuarios (
            id BIGSERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

CREATE TABLE IF NOT EXISTS watchlist_usuario (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            simbolo TEXT NOT NULL,
            favorito BOOLEAN NOT NULL DEFAULT FALSE,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (usuario_id, simbolo)
    );

CREATE TABLE IF NOT EXISTS credenciales_bolsa (
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            es_demo BOOLEAN NOT NULL,
            identificador_cifrado TEXT NOT NULL,
            api_key_cifrada TEXT NOT NULL,
            api_contrasena_cifrada TEXT NOT NULL,
            version SMALLINT NOT NULL DEFAULT 1,
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (usuario_id, es_demo)
    );

CREATE OR REPLACE FUNCTION credenciales_bolsa_actualizado() RETURNS TRIGGER
        SET search_path = public AS $$
        BEGIN
            NEW.actualizado_en = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS credenciales_bolsa_fecha ON credenciales_bolsa;

CREATE TRIGGER credenciales_bolsa_fecha BEFORE UPDATE ON credenciales_bolsa
            FOR EACH ROW EXECUTE PROCEDURE credenciales_bolsa_actualizado();

create table if not exists perfiles_usuario (
    usuario_id bigint primary key references usuarios(id) on delete cascade,
    nombres text,
    apellidos text,
    apodo text,
    fecha_nacimiento date,
    nacionalidad text,
    genero text,
    tipo_documento text,
    numero_documento text,
    pais_documento text,
    vencimiento_documento date,
    telefono_prefijo text,
    telefono_movil text,
    telefono_alterno text,
    pais text,
    region text,
    ciudad text,
    direccion text,
    codigo_postal text,
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
    idioma text not null default 'es',
    zona_horaria text,
    moneda_visualizacion text not null default 'USD',
    notificaciones jsonb not null default '{}'::jsonb,
    verificacion text not null default 'sin_verificar',
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

alter table perfiles_usuario add column if not exists apodo text;

create unique index if not exists perfiles_usuario_apodo_unico
    on perfiles_usuario (lower(apodo))
    where apodo is not null;

create unique index if not exists perfiles_usuario_documento_unico
    on perfiles_usuario (tipo_documento, numero_documento)
    where numero_documento is not null;

CREATE TABLE IF NOT EXISTS planes_usuario (
            usuario_id BIGINT PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
            plan TEXT NOT NULL CHECK (plan IN ('gratis', 'basico', 'pro', 'avanzado')),
            origen TEXT NOT NULL DEFAULT 'prueba' CHECK (origen IN ('prueba', 'pago', 'admin')),
            desde TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

CREATE TABLE IF NOT EXISTS planes_historial (
        id BIGSERIAL PRIMARY KEY,
        usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        plan_anterior TEXT,
        plan_nuevo TEXT NOT NULL,
        origen TEXT NOT NULL DEFAULT 'prueba',
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

CREATE INDEX IF NOT EXISTS planes_historial_usuario ON planes_historial (usuario_id, creado_en DESC);

CREATE TABLE IF NOT EXISTS sesiones_persistentes (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            expira_en TIMESTAMPTZ NOT NULL,
            ultimo_uso TIMESTAMPTZ NOT NULL DEFAULT now(),
            dispositivo TEXT
    );

CREATE INDEX IF NOT EXISTS sesiones_persistentes_usuario ON sesiones_persistentes (usuario_id, expira_en);

CREATE TABLE IF NOT EXISTS billetera_cuentas (
            usuario_id BIGINT PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
            moneda TEXT NOT NULL DEFAULT 'USD',
            tipo TEXT NOT NULL DEFAULT 'virtual' CHECK (tipo IN ('virtual', 'real')),
            saldo NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (saldo >= 0),
            creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizada_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

CREATE TABLE IF NOT EXISTS billetera_movimientos (
        id BIGSERIAL PRIMARY KEY,
        usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        tipo TEXT NOT NULL CHECK (tipo IN ('bono', 'recarga_virtual', 'compra_plan', 'ajuste', 'deposito_real', 'retiro_real', 'resultado_operacion')),
        monto NUMERIC(14, 2) NOT NULL CHECK (monto <> 0),
        saldo_despues NUMERIC(14, 2) NOT NULL CHECK (saldo_despues >= 0),
        concepto TEXT NOT NULL DEFAULT '',
        referencia TEXT,
        clave_unica TEXT UNIQUE,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

CREATE INDEX IF NOT EXISTS billetera_movimientos_usuario ON billetera_movimientos (usuario_id, creado_en DESC);

CREATE OR REPLACE FUNCTION billetera_mover(p_usuario BIGINT, p_tipo TEXT, p_monto NUMERIC, p_concepto TEXT DEFAULT '',
                                               p_referencia TEXT DEFAULT NULL, p_clave TEXT DEFAULT NULL)
    RETURNS TABLE (saldo_nuevo NUMERIC, movimiento_id BIGINT, repetido BOOLEAN)
    LANGUAGE plpgsql AS $$
    DECLARE
        v_saldo NUMERIC;
        v_nuevo NUMERIC;
        v_id BIGINT;
    BEGIN
        INSERT INTO billetera_cuentas (usuario_id) VALUES (p_usuario) ON CONFLICT (usuario_id) DO NOTHING;
        SELECT c.saldo INTO v_saldo FROM billetera_cuentas c WHERE c.usuario_id = p_usuario FOR UPDATE;
        IF p_clave IS NOT NULL THEN
            SELECT m.id INTO v_id FROM billetera_movimientos m WHERE m.clave_unica = p_clave;
            IF FOUND THEN
                RETURN QUERY SELECT v_saldo, v_id, TRUE;
                RETURN;
            END IF;
        END IF;
        v_nuevo := v_saldo + p_monto;
        IF v_nuevo < 0 THEN
            RAISE EXCEPTION 'saldo_insuficiente';
        END IF;
        UPDATE billetera_cuentas SET saldo = v_nuevo, actualizada_en = now() WHERE usuario_id = p_usuario;
        INSERT INTO billetera_movimientos (usuario_id, tipo, monto, saldo_despues, concepto, referencia, clave_unica)
        VALUES (p_usuario, p_tipo, p_monto, v_nuevo, COALESCE(p_concepto, ''), p_referencia, p_clave) RETURNING id INTO v_id;
        RETURN QUERY SELECT v_nuevo, v_id, FALSE;
    END;
    $$;


CREATE TABLE IF NOT EXISTS operaciones (
            id BIGSERIAL PRIMARY KEY,
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            cuenta_tipo TEXT NOT NULL DEFAULT 'demo' CHECK (cuenta_tipo IN ('demo', 'real')),
            id_broker TEXT NOT NULL,
            simbolo TEXT NOT NULL,
            tipo_activo TEXT,
            lado TEXT NOT NULL CHECK (lado IN ('compra', 'venta')),
            volumen NUMERIC(18, 6) NOT NULL CHECK (volumen > 0),
            tamano_contrato NUMERIC(18, 6) NOT NULL DEFAULT 1,
            precio_apertura NUMERIC(18, 6) NOT NULL,
            abierta_en TIMESTAMPTZ NOT NULL,
            stop_loss NUMERIC(18, 6),
            take_profit NUMERIC(18, 6),
            equity_apertura NUMERIC(18, 2),
            apalancamiento INTEGER,
            margen_usado_pct NUMERIC(8, 4),
            estado TEXT NOT NULL DEFAULT 'abierta' CHECK (estado IN ('abierta', 'cerrada')),
            precio_cierre NUMERIC(18, 6),
            cerrada_en TIMESTAMPTZ,
            resultado NUMERIC(18, 2),
            comision NUMERIC(18, 2) NOT NULL DEFAULT 0,
            swap NUMERIC(18, 2) NOT NULL DEFAULT 0,
            origen TEXT NOT NULL DEFAULT 'manual' CHECK (origen IN ('manual', 'agente', 'copia')),
            copia_id BIGINT,
            operacion_origen_id BIGINT REFERENCES operaciones(id) ON DELETE SET NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT operaciones_cierre_coherente CHECK (estado = 'abierta' OR (precio_cierre IS NOT NULL AND cerrada_en IS NOT NULL))
    );

CREATE UNIQUE INDEX IF NOT EXISTS operaciones_broker_unico ON operaciones (usuario_id, cuenta_tipo, id_broker);

CREATE INDEX IF NOT EXISTS operaciones_usuario_fecha ON operaciones (usuario_id, abierta_en DESC);

CREATE INDEX IF NOT EXISTS operaciones_usuario_estado ON operaciones (usuario_id, estado);

CREATE INDEX IF NOT EXISTS operaciones_origen ON operaciones (operacion_origen_id) WHERE operacion_origen_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS equity_historial (
        id BIGSERIAL PRIMARY KEY,
        usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        cuenta_tipo TEXT NOT NULL DEFAULT 'demo' CHECK (cuenta_tipo IN ('demo', 'real')),
        balance NUMERIC(18, 2) NOT NULL,
        equity NUMERIC(18, 2) NOT NULL,
        flujo_neto NUMERIC(18, 2) NOT NULL DEFAULT 0,
        registrado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

CREATE INDEX IF NOT EXISTS equity_historial_usuario ON equity_historial (usuario_id, cuenta_tipo, registrado_en DESC);

CREATE TABLE IF NOT EXISTS cuentas_inversor (
        usuario_id BIGINT PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
        acepto_terminos_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        version_terminos TEXT NOT NULL DEFAULT '1',
        estado TEXT NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'suspendida')),
        creada_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

CREATE TABLE IF NOT EXISTS estrategias (
            id BIGSERIAL PRIMARY KEY,
            gestor_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            nombre TEXT NOT NULL CHECK (char_length(nombre) BETWEEN 3 AND 40),
            biografia TEXT NOT NULL DEFAULT '' CHECK (char_length(biografia) <= 500),
            descripcion TEXT NOT NULL DEFAULT '' CHECK (char_length(descripcion) <= 1000),
            tipo TEXT NOT NULL DEFAULT 'manual' CHECK (tipo IN ('manual', 'algoritmico')),
            categoria TEXT,
            inversion_minima NUMERIC(14, 2) NOT NULL DEFAULT 50 CHECK (inversion_minima >= 50),
            comision_pct NUMERIC(5, 2) NOT NULL DEFAULT 20 CHECK (comision_pct BETWEEN 0 AND 30),
            estado TEXT NOT NULL DEFAULT 'borrador' CHECK (estado IN ('borrador', 'publicada', 'pausada', 'cerrada')),
            cuenta_tipo TEXT NOT NULL DEFAULT 'demo' CHECK (cuenta_tipo IN ('demo', 'real')),
            acepto_compartir_en TIMESTAMPTZ,
            creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            publicada_en TIMESTAMPTZ,
            actualizada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT estrategias_publicada_con_consentimiento CHECK (estado = 'borrador' OR acepto_compartir_en IS NOT NULL)
    );

CREATE UNIQUE INDEX IF NOT EXISTS estrategias_gestor_nombre ON estrategias (gestor_id, lower(nombre));

CREATE INDEX IF NOT EXISTS estrategias_estado ON estrategias (estado, publicada_en DESC);

CREATE TABLE IF NOT EXISTS estrategias_metricas (
        estrategia_id BIGINT PRIMARY KEY REFERENCES estrategias(id) ON DELETE CASCADE,
        rent_1m NUMERIC(10, 2), rent_3m NUMERIC(10, 2), rent_12m NUMERIC(10, 2), rent_total NUMERIC(10, 2),
        drawdown_max NUMERIC(6, 2),
        riesgo TEXT CHECK (riesgo IN ('bajo', 'medio', 'alto')),
        apalancamiento INTEGER,
        operaciones_total INTEGER NOT NULL DEFAULT 0,
        operaciones_ganadoras INTEGER NOT NULL DEFAULT 0,
        operaciones_perdedoras INTEGER NOT NULL DEFAULT 0,
        mejor_operacion NUMERIC(18, 2),
        peor_operacion NUMERIC(18, 2),
        factor_beneficio NUMERIC(10, 2),
        fondos_propios NUMERIC(18, 2),
        invertido NUMERIC(18, 2) NOT NULL DEFAULT 0,
        inversores INTEGER NOT NULL DEFAULT 0,
        margen_usado_pct NUMERIC(8, 4),
        asignacion_abiertas JSONB NOT NULL DEFAULT '{}'::jsonb,
        asignacion_cerradas JSONB NOT NULL DEFAULT '{}'::jsonb,
        actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

CREATE TABLE IF NOT EXISTS estrategias_diario (
        estrategia_id BIGINT NOT NULL REFERENCES estrategias(id) ON DELETE CASCADE,
        dia DATE NOT NULL,
        rent_acumulada NUMERIC(10, 2) NOT NULL,
        equity NUMERIC(18, 2),
        drawdown NUMERIC(6, 2),
        inversores INTEGER NOT NULL DEFAULT 0,
        invertido NUMERIC(18, 2) NOT NULL DEFAULT 0,
        PRIMARY KEY (estrategia_id, dia)
    );

CREATE TABLE IF NOT EXISTS estrategias_favoritas (
        usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        estrategia_id BIGINT NOT NULL REFERENCES estrategias(id) ON DELETE CASCADE,
        creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (usuario_id, estrategia_id)
    );

CREATE TABLE IF NOT EXISTS copias (
            id BIGSERIAL PRIMARY KEY,
            inversor_id BIGINT NOT NULL REFERENCES cuentas_inversor(usuario_id) ON DELETE CASCADE,
            estrategia_id BIGINT NOT NULL REFERENCES estrategias(id) ON DELETE RESTRICT,
            modo TEXT NOT NULL DEFAULT 'importe' CHECK (modo IN ('importe', 'multiplicador')),
            importe NUMERIC(14, 2) CHECK (importe > 0),
            multiplicador NUMERIC(8, 4) CHECK (multiplicador > 0),
            copiar_abiertas BOOLEAN NOT NULL DEFAULT FALSE,
            take_profit_pct NUMERIC(6, 2) CHECK (take_profit_pct > 0),
            stop_loss_pct NUMERIC(6, 2) CHECK (stop_loss_pct > 0 AND stop_loss_pct <= 100),
            estado TEXT NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'pausada', 'cerrada')),
            motivo_cierre TEXT,
            marca_agua NUMERIC(14, 2) NOT NULL DEFAULT 0,
            creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            cerrada_en TIMESTAMPTZ,
            CONSTRAINT copias_asignacion_coherente CHECK ((modo = 'importe' AND importe IS NOT NULL) OR (modo = 'multiplicador' AND multiplicador IS NOT NULL))
    );

CREATE UNIQUE INDEX IF NOT EXISTS copias_inversor_estrategia_vigente ON copias (inversor_id, estrategia_id) WHERE estado <> 'cerrada';

CREATE INDEX IF NOT EXISTS copias_estrategia ON copias (estrategia_id, estado);

DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'operaciones_copia_fk') THEN
            ALTER TABLE operaciones ADD CONSTRAINT operaciones_copia_fk FOREIGN KEY (copia_id) REFERENCES copias(id) ON DELETE SET NULL;
        END IF;
    END $$;

CREATE TABLE IF NOT EXISTS copias_operaciones (
        id BIGSERIAL PRIMARY KEY,
        copia_id BIGINT NOT NULL REFERENCES copias(id) ON DELETE CASCADE,
        operacion_origen_id BIGINT NOT NULL REFERENCES operaciones(id) ON DELETE CASCADE,
        operacion_copia_id BIGINT REFERENCES operaciones(id) ON DELETE SET NULL,
        volumen_origen NUMERIC(18, 6) NOT NULL,
        volumen_copia NUMERIC(18, 6),
        precio_origen NUMERIC(18, 6) NOT NULL,
        precio_copia NUMERIC(18, 6),
        estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'copiada', 'cerrada', 'fallida')),
        error TEXT,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

CREATE UNIQUE INDEX IF NOT EXISTS copias_operaciones_unica ON copias_operaciones (copia_id, operacion_origen_id);

CREATE INDEX IF NOT EXISTS copias_operaciones_estado ON copias_operaciones (estado) WHERE estado IN ('pendiente', 'fallida');

CREATE TABLE IF NOT EXISTS comisiones_rendimiento (
        id BIGSERIAL PRIMARY KEY,
        copia_id BIGINT NOT NULL REFERENCES copias(id) ON DELETE CASCADE,
        periodo_desde TIMESTAMPTZ NOT NULL,
        periodo_hasta TIMESTAMPTZ NOT NULL,
        ganancia_acumulada NUMERIC(14, 2) NOT NULL,
        marca_agua_antes NUMERIC(14, 2) NOT NULL,
        marca_agua_despues NUMERIC(14, 2) NOT NULL,
        comision_pct NUMERIC(5, 2) NOT NULL,
        comision NUMERIC(14, 2) NOT NULL CHECK (comision >= 0),
        movimiento_billetera_id BIGINT REFERENCES billetera_movimientos(id) ON DELETE SET NULL,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT comisiones_periodo_valido CHECK (periodo_hasta > periodo_desde)
    );

CREATE UNIQUE INDEX IF NOT EXISTS comisiones_copia_periodo ON comisiones_rendimiento (copia_id, periodo_hasta);

ALTER TABLE billetera_movimientos DROP CONSTRAINT IF EXISTS billetera_movimientos_tipo_check;

ALTER TABLE billetera_movimientos ADD CONSTRAINT billetera_movimientos_tipo_check
        CHECK (tipo IN ('bono', 'recarga_virtual', 'compra_plan', 'ajuste', 'deposito_real', 'retiro_real', 'resultado_operacion', 'comision_pagada', 'comision_cobrada'));

ALTER TABLE copias ADD COLUMN IF NOT EXISTS comision_final_en TIMESTAMPTZ;

ALTER TABLE copias ADD COLUMN IF NOT EXISTS perfil_previo JSONB;

CREATE OR REPLACE FUNCTION billetera_transferir(p_origen BIGINT, p_destino BIGINT, p_monto NUMERIC, p_concepto_origen TEXT, p_concepto_destino TEXT,
                                                    p_referencia TEXT DEFAULT NULL, p_clave TEXT DEFAULT NULL)
    RETURNS TABLE (saldo_origen NUMERIC, saldo_destino NUMERIC, movimiento_origen_id BIGINT, movimiento_destino_id BIGINT, repetido BOOLEAN)
    LANGUAGE plpgsql AS $$
    DECLARE
        v_so NUMERIC;
        v_sd NUMERIC;
        v_mo BIGINT;
        v_md BIGINT;
    BEGIN
        IF p_monto <= 0 THEN
            RAISE EXCEPTION 'monto_invalido';
        END IF;
        IF p_origen = p_destino THEN
            RAISE EXCEPTION 'misma_billetera';
        END IF;
        INSERT INTO billetera_cuentas (usuario_id) VALUES (p_origen) ON CONFLICT (usuario_id) DO NOTHING;
        INSERT INTO billetera_cuentas (usuario_id) VALUES (p_destino) ON CONFLICT (usuario_id) DO NOTHING;
        PERFORM 1 FROM billetera_cuentas WHERE usuario_id IN (p_origen, p_destino) ORDER BY usuario_id FOR UPDATE;
        SELECT c.saldo INTO v_so FROM billetera_cuentas c WHERE c.usuario_id = p_origen;
        SELECT c.saldo INTO v_sd FROM billetera_cuentas c WHERE c.usuario_id = p_destino;
        IF p_clave IS NOT NULL THEN
            SELECT m.id INTO v_mo FROM billetera_movimientos m WHERE m.clave_unica = p_clave || ':pago';
            IF FOUND THEN
                SELECT m.id INTO v_md FROM billetera_movimientos m WHERE m.clave_unica = p_clave || ':cobro';
                RETURN QUERY SELECT v_so, v_sd, v_mo, v_md, TRUE;
                RETURN;
            END IF;
        END IF;
        IF v_so < p_monto THEN
            RAISE EXCEPTION 'saldo_insuficiente';
        END IF;
        UPDATE billetera_cuentas SET saldo = saldo - p_monto, actualizada_en = now() WHERE usuario_id = p_origen;
        UPDATE billetera_cuentas SET saldo = saldo + p_monto, actualizada_en = now() WHERE usuario_id = p_destino;
        INSERT INTO billetera_movimientos (usuario_id, tipo, monto, saldo_despues, concepto, referencia, clave_unica)
        VALUES (p_origen, 'comision_pagada', -p_monto, v_so - p_monto, COALESCE(p_concepto_origen, ''), p_referencia, CASE WHEN p_clave IS NULL THEN NULL ELSE p_clave || ':pago' END)
        RETURNING id INTO v_mo;
        INSERT INTO billetera_movimientos (usuario_id, tipo, monto, saldo_despues, concepto, referencia, clave_unica)
        VALUES (p_destino, 'comision_cobrada', p_monto, v_sd + p_monto, COALESCE(p_concepto_destino, ''), p_referencia, CASE WHEN p_clave IS NULL THEN NULL ELSE p_clave || ':cobro' END)
        RETURNING id INTO v_md;
        RETURN QUERY SELECT v_so - p_monto, v_sd + p_monto, v_mo, v_md, FALSE;
    END;
    $$;

-- -------------------------------------------
-- Memoria del agente de IA y conocimiento interno (4) --
-- -------------------------------------------

CREATE TABLE IF NOT EXISTS agente_chats (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo TEXT,
    resumen TEXT,
    creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizada_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS agente_chats_usuario ON agente_chats (usuario_id, actualizada_en DESC);

CREATE TABLE IF NOT EXISTS agente_mensajes (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES agente_chats(id) ON DELETE CASCADE,
    turno INTEGER NOT NULL,
    orden INTEGER NOT NULL,
    mensaje JSONB NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (chat_id, orden)
);

CREATE TABLE IF NOT EXISTS agente_memoria_usuario (
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    clave TEXT NOT NULL,
    valor TEXT NOT NULL,
    actualizada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (usuario_id, clave)
);

CREATE TABLE IF NOT EXISTS documentos_rag (
    id BIGSERIAL PRIMARY KEY,
    contenido TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -------------------------------------------------------------------------------------------------------
-- -------------------------- FIN Piña y Jara postgresql_cpanel_completo .SQL ----------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
