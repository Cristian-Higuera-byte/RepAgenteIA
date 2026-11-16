-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.


-- -------------------------------------------------------------------------------------------------------
-- --------------------------------- INICIO Piña y Jara copytrading .SQL ---------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Descripción: base de datos del copy trading de la plataforma. Registra las operaciones de cada usuario y su equity, las estrategias que los gestores
-- publican (con sus métricas ya calculadas), las cuentas de inversor, las copias de los seguidores, las operaciones replicadas y las comisiones de rendimiento.
-- Motor: PostgreSQL (Supabase). Ejecutar en SQL Editor > New query > Run, DESPUÉS de los scripts 01 (usuarios) y 02 (perfiles_usuario, de donde sale el apodo).
-- Es idempotente: se puede volver a ejecutar sin perder datos.
-- Seguridad: RLS activo y SIN políticas; solo el servidor, con la clave service_role, lee y escribe estas tablas. El nombre público del gestor es su apodo
-- (perfiles_usuario.apodo): no se guarda ni se muestra nombre, documento ni correo.

-- -------------------------------------------
-- Estructura de tabla para la tabla `operaciones` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS operaciones (

        -- TITULO IDENTIFICACION

            id BIGSERIAL PRIMARY KEY,
            -- Usuario dueño de la operación y tipo de cuenta donde se ejecutó (demo o real).
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            cuenta_tipo TEXT NOT NULL DEFAULT 'demo' CHECK (cuenta_tipo IN ('demo', 'real')),
            -- Identificador de la posición en el bróker (dealId de Capital.com): evita registrar dos veces la misma operación.
            id_broker TEXT NOT NULL,

        -- TITULO INSTRUMENTO

            simbolo TEXT NOT NULL,
            -- Tipo de activo para la asignación (Índices, Forex, Criptomonedas, Materias primas, Acciones...).
            tipo_activo TEXT,
            lado TEXT NOT NULL CHECK (lado IN ('compra', 'venta')),
            volumen NUMERIC(18, 6) NOT NULL CHECK (volumen > 0),
            tamano_contrato NUMERIC(18, 6) NOT NULL DEFAULT 1,

        -- TITULO APERTURA

            precio_apertura NUMERIC(18, 6) NOT NULL,
            abierta_en TIMESTAMPTZ NOT NULL,
            stop_loss NUMERIC(18, 6),
            take_profit NUMERIC(18, 6),
            -- Foto del momento de abrir: equity de la cuenta y apalancamiento. Sirven para el tamaño relativo y el margen usado.
            equity_apertura NUMERIC(18, 2),
            apalancamiento INTEGER,
            margen_usado_pct NUMERIC(8, 4),

        -- TITULO CIERRE

            estado TEXT NOT NULL DEFAULT 'abierta' CHECK (estado IN ('abierta', 'cerrada')),
            precio_cierre NUMERIC(18, 6),
            cerrada_en TIMESTAMPTZ,
            -- Resultado neto de la operación (ganancia o pérdida) en la moneda de la cuenta, y sus costos.
            resultado NUMERIC(18, 2),
            comision NUMERIC(18, 2) NOT NULL DEFAULT 0,
            swap NUMERIC(18, 2) NOT NULL DEFAULT 0,

        -- TITULO ORIGEN

            -- Quién originó la operación: el usuario a mano, el agente de IA o una copia. Si es una copia, de cuál y de qué operación se copió.
            origen TEXT NOT NULL DEFAULT 'manual' CHECK (origen IN ('manual', 'agente', 'copia')),
            copia_id BIGINT,
            operacion_origen_id BIGINT REFERENCES operaciones(id) ON DELETE SET NULL,

        -- TITULO CONTROL

            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT operaciones_cierre_coherente CHECK (estado = 'abierta' OR (precio_cierre IS NOT NULL AND cerrada_en IS NOT NULL))
    );

    -- Una operación del bróker se registra una sola vez por cuenta.
    CREATE UNIQUE INDEX IF NOT EXISTS operaciones_broker_unico ON operaciones (usuario_id, cuenta_tipo, id_broker);
    -- Para listar la cartera (abiertas y cerradas) de un usuario y calcular sus métricas.
    CREATE INDEX IF NOT EXISTS operaciones_usuario_fecha ON operaciones (usuario_id, abierta_en DESC);
    CREATE INDEX IF NOT EXISTS operaciones_usuario_estado ON operaciones (usuario_id, estado);
    -- Para encontrar las operaciones copiadas de una operación original.
    CREATE INDEX IF NOT EXISTS operaciones_origen ON operaciones (operacion_origen_id) WHERE operacion_origen_id IS NOT NULL;

-- -------------------------------------------
-- Estructura de tabla para la tabla `equity_historial` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS equity_historial (

        id BIGSERIAL PRIMARY KEY,
        usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        cuenta_tipo TEXT NOT NULL DEFAULT 'demo' CHECK (cuenta_tipo IN ('demo', 'real')),
        -- Foto del balance y del equity (balance más resultado de las abiertas) y su momento. Con esto se arma la curva, la rentabilidad y el drawdown.
        balance NUMERIC(18, 2) NOT NULL,
        equity NUMERIC(18, 2) NOT NULL,
        -- Depósitos y retiros netos desde la foto anterior: se descuentan para que no cuenten como rentabilidad.
        flujo_neto NUMERIC(18, 2) NOT NULL DEFAULT 0,
        registrado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS equity_historial_usuario ON equity_historial (usuario_id, cuenta_tipo, registrado_en DESC);

-- -------------------------------------------
-- Estructura de tabla para la tabla `cuentas_inversor` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS cuentas_inversor (

        -- Una cuenta de inversor por usuario (como en XM: hay que abrirla antes de copiar). Guarda cuándo aceptó los términos y su estado.
        usuario_id BIGINT PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
        acepto_terminos_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        version_terminos TEXT NOT NULL DEFAULT '1',
        estado TEXT NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'suspendida')),
        creada_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

-- -------------------------------------------
-- Estructura de tabla para la tabla `estrategias` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS estrategias (

        -- TITULO IDENTIFICACION

            id BIGSERIAL PRIMARY KEY,
            -- Gestor dueño de la estrategia. Su nombre público es el apodo de su perfil.
            gestor_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            nombre TEXT NOT NULL CHECK (char_length(nombre) BETWEEN 3 AND 40),

        -- TITULO PRESENTACION

            -- Biografía del gestor y descripción de la estrategia (se muestran en la ficha). Tipo: manual o algorítmica.
            biografia TEXT NOT NULL DEFAULT '' CHECK (char_length(biografia) <= 500),
            descripcion TEXT NOT NULL DEFAULT '' CHECK (char_length(descripcion) <= 1000),
            tipo TEXT NOT NULL DEFAULT 'manual' CHECK (tipo IN ('manual', 'algoritmico')),
            categoria TEXT,

        -- TITULO CONDICIONES

            -- Inversión mínima para copiar (USD) y comisión de rendimiento: porcentaje de la ganancia que el seguidor paga al gestor (entre 0 y 30).
            inversion_minima NUMERIC(14, 2) NOT NULL DEFAULT 50 CHECK (inversion_minima >= 50),
            comision_pct NUMERIC(5, 2) NOT NULL DEFAULT 20 CHECK (comision_pct BETWEEN 0 AND 30),

        -- TITULO ESTADO

            -- borrador: solo la ve el gestor; publicada: aparece en el listado; pausada: no admite nuevas copias; cerrada: terminó.
            estado TEXT NOT NULL DEFAULT 'borrador' CHECK (estado IN ('borrador', 'publicada', 'pausada', 'cerrada')),
            -- Cuenta de la que salen las operaciones de la estrategia y consentimiento del gestor para compartir su historial.
            cuenta_tipo TEXT NOT NULL DEFAULT 'demo' CHECK (cuenta_tipo IN ('demo', 'real')),
            acepto_compartir_en TIMESTAMPTZ,
            creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            publicada_en TIMESTAMPTZ,
            actualizada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            -- No se puede publicar sin el consentimiento del gestor.
            CONSTRAINT estrategias_publicada_con_consentimiento CHECK (estado = 'borrador' OR acepto_compartir_en IS NOT NULL)
    );

    -- Un gestor no repite el nombre de sus estrategias.
    CREATE UNIQUE INDEX IF NOT EXISTS estrategias_gestor_nombre ON estrategias (gestor_id, lower(nombre));
    CREATE INDEX IF NOT EXISTS estrategias_estado ON estrategias (estado, publicada_en DESC);

-- -------------------------------------------
-- Estructura de tabla para la tabla `estrategias_metricas` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS estrategias_metricas (

        -- Valores ya calculados de cada estrategia (los recalcula un proceso periódico; así el listado no recorre todas las operaciones).
        estrategia_id BIGINT PRIMARY KEY REFERENCES estrategias(id) ON DELETE CASCADE,
        -- Rentabilidad en porcentaje: último mes, 3 meses, 12 meses y total.
        rent_1m NUMERIC(10, 2), rent_3m NUMERIC(10, 2), rent_12m NUMERIC(10, 2), rent_total NUMERIC(10, 2),
        -- Riesgo: drawdown máximo (%), nivel (bajo, medio, alto) y apalancamiento medio.
        drawdown_max NUMERIC(6, 2),
        riesgo TEXT CHECK (riesgo IN ('bajo', 'medio', 'alto')),
        apalancamiento INTEGER,
        -- Operaciones: totales, ganadoras, perdedoras, mejor y peor resultado, y factor de beneficio.
        operaciones_total INTEGER NOT NULL DEFAULT 0,
        operaciones_ganadoras INTEGER NOT NULL DEFAULT 0,
        operaciones_perdedoras INTEGER NOT NULL DEFAULT 0,
        mejor_operacion NUMERIC(18, 2),
        peor_operacion NUMERIC(18, 2),
        factor_beneficio NUMERIC(10, 2),
        -- Dinero: fondos propios del gestor, total invertido por los seguidores, cantidad de inversores y margen usado (%).
        fondos_propios NUMERIC(18, 2),
        invertido NUMERIC(18, 2) NOT NULL DEFAULT 0,
        inversores INTEGER NOT NULL DEFAULT 0,
        margen_usado_pct NUMERIC(8, 4),
        -- Reparto por tipo de activo, por ejemplo {"Índices": 100} (abiertas y cerradas se calculan aparte).
        asignacion_abiertas JSONB NOT NULL DEFAULT '{}'::jsonb,
        asignacion_cerradas JSONB NOT NULL DEFAULT '{}'::jsonb,
        actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

-- -------------------------------------------
-- Estructura de tabla para la tabla `estrategias_diario` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS estrategias_diario (

        -- Una fila por estrategia y día: alimenta la curva de rendimiento y las barras mensuales de Rentabilidades, Inversores e Invertido.
        estrategia_id BIGINT NOT NULL REFERENCES estrategias(id) ON DELETE CASCADE,
        dia DATE NOT NULL,
        rent_acumulada NUMERIC(10, 2) NOT NULL,
        equity NUMERIC(18, 2),
        drawdown NUMERIC(6, 2),
        inversores INTEGER NOT NULL DEFAULT 0,
        invertido NUMERIC(18, 2) NOT NULL DEFAULT 0,
        PRIMARY KEY (estrategia_id, dia)
    );

-- -------------------------------------------
-- Estructura de tabla para la tabla `estrategias_favoritas` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS estrategias_favoritas (

        -- La estrella de la ficha: estrategias que el usuario marcó para seguir de cerca.
        usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        estrategia_id BIGINT NOT NULL REFERENCES estrategias(id) ON DELETE CASCADE,
        creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (usuario_id, estrategia_id)
    );

-- -------------------------------------------
-- Estructura de tabla para la tabla `copias` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS copias (

        -- TITULO IDENTIFICACION

            id BIGSERIAL PRIMARY KEY,
            inversor_id BIGINT NOT NULL REFERENCES cuentas_inversor(usuario_id) ON DELETE CASCADE,
            estrategia_id BIGINT NOT NULL REFERENCES estrategias(id) ON DELETE RESTRICT,

        -- TITULO ASIGNACION

            -- Cómo se calcula el tamaño de lo copiado: por importe invertido (se reparte según los fondos propios del gestor) o por multiplicador fijo.
            modo TEXT NOT NULL DEFAULT 'importe' CHECK (modo IN ('importe', 'multiplicador')),
            importe NUMERIC(14, 2) CHECK (importe > 0),
            multiplicador NUMERIC(8, 4) CHECK (multiplicador > 0),
            -- «Copiar operaciones abiertas»: al empezar, replicar también las posiciones que el gestor ya tiene abiertas.
            copiar_abiertas BOOLEAN NOT NULL DEFAULT FALSE,

        -- TITULO PROTECCIONES

            -- Take profit y stop loss de la copia, como porcentaje del importe invertido (vacío = desactivado). Al llegar, la copia se cierra.
            take_profit_pct NUMERIC(6, 2) CHECK (take_profit_pct > 0),
            stop_loss_pct NUMERIC(6, 2) CHECK (stop_loss_pct > 0 AND stop_loss_pct <= 100),

        -- TITULO ESTADO

            estado TEXT NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'pausada', 'cerrada')),
            motivo_cierre TEXT,
            -- Marca de agua: la mayor ganancia sobre la que ya se cobró comisión; solo se cobra lo que la supere.
            marca_agua NUMERIC(14, 2) NOT NULL DEFAULT 0,
            creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            cerrada_en TIMESTAMPTZ,
            CONSTRAINT copias_asignacion_coherente CHECK ((modo = 'importe' AND importe IS NOT NULL) OR (modo = 'multiplicador' AND multiplicador IS NOT NULL))
    );

    -- Un inversor solo puede tener una copia activa o pausada por estrategia.
    CREATE UNIQUE INDEX IF NOT EXISTS copias_inversor_estrategia_vigente ON copias (inversor_id, estrategia_id) WHERE estado <> 'cerrada';
    CREATE INDEX IF NOT EXISTS copias_estrategia ON copias (estrategia_id, estado);

    -- Ahora que existe `copias`, las operaciones copiadas pueden apuntar a su copia.
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'operaciones_copia_fk') THEN
            ALTER TABLE operaciones ADD CONSTRAINT operaciones_copia_fk FOREIGN KEY (copia_id) REFERENCES copias(id) ON DELETE SET NULL;
        END IF;
    END $$;

-- -------------------------------------------
-- Estructura de tabla para la tabla `copias_operaciones` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS copias_operaciones (

        -- Una fila por cada operación del gestor que se intentó replicar en una copia: qué se copió, a qué tamaño y cómo salió.
        id BIGSERIAL PRIMARY KEY,
        copia_id BIGINT NOT NULL REFERENCES copias(id) ON DELETE CASCADE,
        operacion_origen_id BIGINT NOT NULL REFERENCES operaciones(id) ON DELETE CASCADE,
        operacion_copia_id BIGINT REFERENCES operaciones(id) ON DELETE SET NULL,
        volumen_origen NUMERIC(18, 6) NOT NULL,
        volumen_copia NUMERIC(18, 6),
        precio_origen NUMERIC(18, 6) NOT NULL,
        precio_copia NUMERIC(18, 6),
        -- pendiente: esperando mercado abierto; copiada: replicada; cerrada: ya se cerró junto con la original; fallida: el bróker la rechazó (ver `error`).
        estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'copiada', 'cerrada', 'fallida')),
        error TEXT,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    -- Cada operación original se replica una sola vez por copia.
    CREATE UNIQUE INDEX IF NOT EXISTS copias_operaciones_unica ON copias_operaciones (copia_id, operacion_origen_id);
    CREATE INDEX IF NOT EXISTS copias_operaciones_estado ON copias_operaciones (estado) WHERE estado IN ('pendiente', 'fallida');

-- -------------------------------------------
-- Estructura de tabla para la tabla `comisiones_rendimiento` --
-- -------------------------------------------

    CREATE TABLE IF NOT EXISTS comisiones_rendimiento (

        -- Cálculo periódico de lo que el seguidor paga al gestor por una copia: sobre la ganancia que supera la marca de agua.
        id BIGSERIAL PRIMARY KEY,
        copia_id BIGINT NOT NULL REFERENCES copias(id) ON DELETE CASCADE,
        periodo_desde TIMESTAMPTZ NOT NULL,
        periodo_hasta TIMESTAMPTZ NOT NULL,
        ganancia_acumulada NUMERIC(14, 2) NOT NULL,
        marca_agua_antes NUMERIC(14, 2) NOT NULL,
        marca_agua_despues NUMERIC(14, 2) NOT NULL,
        comision_pct NUMERIC(5, 2) NOT NULL,
        comision NUMERIC(14, 2) NOT NULL CHECK (comision >= 0),
        -- Movimiento de la billetera virtual con el que se pagó (billetera_movimientos.id); vacío si todavía no se cobró.
        movimiento_billetera_id BIGINT REFERENCES billetera_movimientos(id) ON DELETE SET NULL,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT comisiones_periodo_valido CHECK (periodo_hasta > periodo_desde)
    );

    CREATE UNIQUE INDEX IF NOT EXISTS comisiones_copia_periodo ON comisiones_rendimiento (copia_id, periodo_hasta);

-- -------------------------------------------
-- Seguridad y permisos --
-- -------------------------------------------

    -- TITULO SEGURIDAD

        -- Descripción: RLS activo y sin políticas (la clave pública anon no puede leer ni escribir nada). El servidor usa service_role, que
        -- necesita permisos explícitos porque el proyecto crea las tablas sin permisos (sin ellos aparece "permission denied", código 42501).
        ALTER TABLE operaciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE equity_historial ENABLE ROW LEVEL SECURITY;
        ALTER TABLE cuentas_inversor ENABLE ROW LEVEL SECURITY;
        ALTER TABLE estrategias ENABLE ROW LEVEL SECURITY;
        ALTER TABLE estrategias_metricas ENABLE ROW LEVEL SECURITY;
        ALTER TABLE estrategias_diario ENABLE ROW LEVEL SECURITY;
        ALTER TABLE estrategias_favoritas ENABLE ROW LEVEL SECURITY;
        ALTER TABLE copias ENABLE ROW LEVEL SECURITY;
        ALTER TABLE copias_operaciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE comisiones_rendimiento ENABLE ROW LEVEL SECURITY;
        GRANT USAGE ON SCHEMA public TO service_role;
        GRANT ALL ON TABLE public.operaciones, public.equity_historial, public.cuentas_inversor, public.estrategias, public.estrategias_metricas,
            public.estrategias_diario, public.estrategias_favoritas, public.copias, public.copias_operaciones, public.comisiones_rendimiento TO service_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

        -- Para ver las estrategias publicadas con el apodo de su gestor (consulta de ejemplo):
        --   SELECT e.nombre, p.apodo, m.rent_1m, m.drawdown_max FROM estrategias e
        --   JOIN perfiles_usuario p ON p.usuario_id = e.gestor_id JOIN estrategias_metricas m ON m.estrategia_id = e.id WHERE e.estado = 'publicada';


-- -------------------------------------------------------------------------------------------------------
-- ---------------------------------- FIN Piña y Jara copytrading .SQL -----------------------------------
-- -------------------------------------------------------------------------------------------------------

-- Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
-- Dirección: José Joaquín Prieto #5373 -
-- San Miguel - Santiago - Chile
-- contacto.pinayjara@gmail.com
-- https://www.pinayjara.cl
-- Creado, Programado y Diseñado por Piña y Jara
-- Transportes y Servicios Ltda.
