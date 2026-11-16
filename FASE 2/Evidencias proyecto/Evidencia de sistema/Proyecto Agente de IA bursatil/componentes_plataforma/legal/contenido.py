# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara contenido .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Textos de los documentos legales de la plataforma: términos de uso, privacidad y cookies, y aviso de riesgo.

Cada documento es un diccionario con su título, un resumen y una lista de secciones; una sección es (título, [bloques]) y cada bloque es un texto o una lista de
textos (viñetas). Son un BORRADOR redactado a partir de lo que la plataforma hace hoy: mientras `EN_REVISION` sea True, cada página lo avisa. Cuando la empresa los
revise y apruebe, se pone `EN_REVISION = False`; y cada vez que cambie su contenido se sube `VERSION`, para saber qué versión aceptó cada usuario.
"""

# Versión de los tres documentos (se guarda junto con la aceptación del usuario) y fecha desde la que rigen.
VERSION = "1.0"
VIGENTE_DESDE = "3 de noviembre de 2026"

# True mientras los textos no hayan sido revisados por el área legal de la empresa; las páginas muestran entonces un aviso.
EN_REVISION = True

# Datos de la empresa responsable, tomados del convenio de práctica y del sitio de la empresa.
EMPRESA = "Piña y Jara Transportes y Servicios Ltda."
RUT = "76.186.223-5"
DIRECCION = "José Joaquín Prieto 5373, San Miguel, Santiago, Chile"
CORREO = "contacto.pinayjara@gmail.com"

# Frase corta que se repite en el pie de la plataforma y junto al agente.
FRASE_RIESGO = ("P&J no entrega asesoría financiera. El agente puede ejecutar órdenes por ti si lo autorizas; en una cuenta real usa tu dinero y puedes perder capital. "
                "Operar con CFD conlleva un alto riesgo de pérdida.")


TERMINOS = {
    "titulo": "Términos de uso",
    "resumen": "Reglas para usar P&J Finance: qué es la plataforma, qué no es y qué se espera de ti.",
    "secciones": [
        ("1. Quiénes somos", [
            f"P&J Finance es una plataforma web de análisis y práctica de trading operada por {EMPRESA}, RUT {RUT}, con domicilio en {DIRECCION}. "
            f"Puedes escribirnos a {CORREO}.",
        ]),
        ("2. Qué es y qué no es la plataforma", [
            "La plataforma ofrece herramientas para ver precios, gráficos y noticias, preparar órdenes, llevar un diario de operaciones y consultar a un agente de "
            "inteligencia artificial. Está en etapa de pruebas: puede tener errores, interrupciones o cambios sin aviso previo.",
            ["No somos una corredora de bolsa ni un bróker: las órdenes se envían al bróker donde tienes tu cuenta (hoy, Capital.com) y tu contrato es con él.",
             "No entregamos asesoría financiera ni recomendaciones de inversión personalizadas.",
             "No recibimos ni administramos dinero tuyo para operar. La billetera y los planes que ves en la plataforma son de demostración y no mueven dinero real."],
        ]),
        ("3. Tu cuenta", [
            ["Debes ser mayor de 18 años y entregar datos verdaderos.",
             "Debes confirmar tu correo electrónico para activar la cuenta.",
             "Eres responsable de mantener en reserva tu contraseña y de lo que se haga con tu cuenta. Si crees que alguien la usó, cambia la contraseña y avísanos.",
             "Una cuenta es de una sola persona."],
        ]),
        ("4. Conexión con tu bróker", [
            "Para operar conectas tu cuenta del bróker con tus credenciales de la API. Las guardamos cifradas y solo se usan para ejecutar lo que tú pides o confirmas. "
            "Puedes desconectar tu cuenta cuando quieras. Mientras la cuenta conectada sea demo, las operaciones no usan dinero real; si conectas una cuenta real, "
            "las operaciones usan tu dinero y son de tu exclusiva responsabilidad.",
        ]),
        ("5. Agente de inteligencia artificial", [
            "El agente responde de forma automática con datos de mercado y de tu cuenta. Puede equivocarse, estar incompleto o basarse en datos con retraso. "
            "Sus respuestas son informativas y no son asesoría financiera.",
            "El agente propone órdenes. Una orden propuesta no se envía al bróker hasta que tú la confirmas, y vence a los pocos minutos. Antes de confirmar, revisa el "
            "instrumento, el lado, el volumen y los niveles de stop loss y take profit.",
            "Además puedes autorizar «vigilancias»: reglas con las que el agente analiza el mercado por su cuenta y abre y cierra posiciones sin pedirte confirmación en cada orden, "
            "aunque no estés mirando la pantalla, dentro de los límites de riesgo que definas. Mientras una vigilancia esté activa, eres responsable de lo que opere; puedes detenerla "
            "cuando quieras. Con una cuenta real, esas operaciones usan tu dinero.",
        ]),
        ("6. Uso permitido", [
            ["No uses la plataforma para fines ilegales ni para operar en nombre de otras personas sin su autorización.",
             "No intentes acceder a cuentas ni a datos de otros usuarios, ni sobrecargar o vulnerar el servicio.",
             "No copies ni revendas la plataforma, su diseño ni su código."],
        ]),
        ("7. Planes y pagos", [
            "Hoy no se cobra por el uso de la plataforma. Si en el futuro hubiera planes de pago, se informarán sus precios y condiciones antes de cobrar cualquier monto.",
        ]),
        ("8. Disponibilidad y datos de terceros", [
            "No garantizamos que la plataforma funcione sin interrupciones. Los precios, noticias y demás datos vienen de terceros (el bróker, Yahoo Finance, Investing.com y otros) "
            "y pueden tener retraso, errores o no estar disponibles.",
        ]),
        ("9. Limitación de responsabilidad", [
            "En la medida que la ley lo permita, no respondemos por pérdidas de dinero ni por daños derivados de operaciones, de decisiones que tomes con la información de la "
            "plataforma, de fallas de internet o de terceros, ni de interrupciones del servicio. Operar es una decisión y un riesgo tuyos.",
        ]),
        ("10. Propiedad intelectual", [
            f"La plataforma, su diseño, textos y código pertenecen a {EMPRESA} Tus datos siguen siendo tuyos.",
        ]),
        ("11. Cambios y ley aplicable", [
            "Podemos actualizar estos términos; la versión vigente y su fecha se muestran siempre en esta página, y te pediremos aceptarlos de nuevo si el cambio es importante. "
            "Se rigen por las leyes de Chile.",
        ]),
    ],
}


PRIVACIDAD = {
    "titulo": "Privacidad y cookies",
    "resumen": "Qué datos guardamos, para qué, con quién los compartimos y qué cookies usa la plataforma.",
    "secciones": [
        ("1. Responsable", [
            f"El responsable del tratamiento de tus datos es {EMPRESA}, RUT {RUT}, {DIRECCION}. Contacto: {CORREO}.",
        ]),
        ("2. Qué datos guardamos", [
            ["Cuenta: tu nombre, tu correo y un resumen irreversible (hash) de tu contraseña; nunca la contraseña misma.",
             "Verificación y recuperación: enlaces de un solo uso, de los que guardamos solo su hash.",
             "Perfil (opcional): datos personales, de contacto y de inversor que decidas completar en «Mi perfil».",
             "Conexión con el bróker: el correo, la clave y la contraseña de la API de tu cuenta, guardados cifrados.",
             "Actividad: órdenes, posiciones, historial y diario de operaciones, límites de riesgo, favoritos y listas de activos.",
             "Conversaciones con el agente y las propuestas de órdenes que genera.",
             "Sesiones abiertas: un identificador aleatorio (guardamos solo su hash), el resumen del navegador y las fechas de uso.",
             "Registros técnicos: el servidor y el proveedor de hosting registran datos como la dirección IP y la hora de cada visita, por seguridad y funcionamiento."],
        ]),
        ("3. Para qué los usamos", [
            ["Darte acceso a la plataforma y ejecutar lo que pides o confirmas.",
             "Enviarte correos del servicio: confirmación de correo y recuperación de contraseña.",
             "Cuidar la seguridad del servicio y resolver fallas.",
             "Mejorar la plataforma, por ejemplo midiendo su rendimiento. No usamos tus datos para publicidad ni los vendemos."],
        ]),
        ("4. Con quién los compartimos", [
            ["Tu bróker (hoy, Capital.com): recibe las órdenes y consultas que se hacen con las credenciales de tu cuenta.",
             "DeepSeek, proveedor del modelo de inteligencia artificial: recibe los mensajes que escribes al agente y los datos de mercado y de tu cuenta que el agente consulta "
             "para responderte. Es un proveedor externo, que puede procesar la información fuera de Chile.",
             "El proveedor de hosting y de correo de la empresa, que aloja la plataforma, la base de datos y envía los correos.",
             "Fuentes de datos de mercado (Yahoo Finance, Investing.com, entre otras): reciben consultas de instrumentos, no tus datos personales."],
            "Fuera de esos casos solo entregaremos tus datos si una autoridad competente lo exige conforme a la ley.",
        ]),
        ("5. Cookies y datos en tu navegador", [
            "La plataforma usa solo lo necesario para funcionar. No usa cookies de publicidad ni de seguimiento de terceros, y desactivamos la telemetría de uso del programa con que está hecha.",
            ["Cookie «pj_sesion» (propia, necesaria): mantiene tu sesión abierta hasta 30 días, aunque cierres el navegador, y en hasta 5 dispositivos a la vez. Contiene un identificador "
             "aleatorio. Se borra al cerrar sesión; también puedes borrarla desde tu navegador.",
             "Identificador de sesión en la dirección (parámetro «s»): identifica la pestaña abierta. No compartas ni publiques enlaces de la plataforma que lo contengan.",
             "Preferencias de la interfaz: el navegador puede guardar ajustes como el tema o la disposición de los paneles."],
        ]),
        ("6. Cuánto tiempo los guardamos", [
            "Guardamos tus datos mientras tu cuenta esté activa. Las sesiones persistentes vencen a los 30 días. Si quieres que eliminemos tu cuenta y tus datos, escríbenos "
            f"a {CORREO}.",
        ]),
        ("7. Seguridad", [
            "Las contraseñas se guardan con un hash irreversible y las claves de tu bróker, cifradas. Aun así, ninguna medida es absoluta: elige una contraseña fuerte, "
            "no la repitas en otros sitios y cierra sesión en los equipos que no sean tuyos.",
        ]),
        ("8. Tus derechos", [
            f"Puedes pedirnos acceder a tus datos, corregirlos, eliminarlos u oponerte a su uso, conforme a la legislación chilena de protección de datos personales, escribiendo a {CORREO}.",
        ]),
        ("9. Cambios", [
            "Si cambiamos esta política, publicaremos aquí la nueva versión con su fecha.",
        ]),
    ],
}


RIESGO = {
    "titulo": "Aviso de riesgo",
    "resumen": "Operar con CFD tiene un alto riesgo de pérdida; la plataforma y su agente no son asesoría financiera.",
    "secciones": [
        ("1. Riesgo de pérdida", [
            ["Operar con derivados como los CFD y con apalancamiento conlleva un alto riesgo de perder dinero con rapidez. Puedes perder parte o todo el capital que uses.",
             "No es adecuado para todas las personas. Opera solo con dinero que puedas permitirte perder y entiende cómo funciona cada producto antes de usarlo."],
        ]),
        ("2. La plataforma no es asesoría financiera", [
            "La información, los gráficos, los análisis y las respuestas del agente son herramientas de apoyo, de carácter informativo. No consideran tu situación financiera ni tus "
            "objetivos, y no constituyen asesoría ni una recomendación de comprar o vender. La decisión de operar es siempre tuya. Si tienes dudas, consulta a un asesor autorizado.",
        ]),
        ("3. El agente de inteligencia artificial puede equivocarse", [
            "El agente puede dar información incorrecta, incompleta o desactualizada. Verifica los datos y revisa con cuidado cada orden que te proponga antes de confirmarla. "
            "Si autorizas una vigilancia automática, el agente abre y cierra posiciones por su cuenta sin pedirte confirmación en cada orden: puede equivocarse, operar en un mal momento "
            "o fallar por problemas técnicos, y las pérdidas son tuyas. Revisa sus operaciones y detenla si no se comporta como esperas.",
        ]),
        ("4. Cuenta demo y cuenta real", [
            "Si operas en una cuenta real, las órdenes que se ejecuten, tanto las que confirmes como las de una vigilancia automática que hayas autorizado, usan tu dinero y las pérdidas son reales.",
            "El resultado en una cuenta demo no garantiza el mismo resultado en una cuenta real: en la realidad influyen el deslizamiento de precios, la liquidez y la velocidad de ejecución. "
            "Los resultados pasados no aseguran resultados futuros.",
        ]),
        ("5. Límites de las protecciones", [
            "Un stop loss no garantiza que la orden se cierre al precio indicado: en mercados con saltos o poca liquidez puede ejecutarse a un precio peor. "
            "Los límites de riesgo de la plataforma ayudan a controlar el riesgo, pero no lo eliminan.",
        ]),
        ("6. Datos de terceros", [
            "Los precios y las noticias vienen de terceros y pueden tener retraso o errores. Antes de operar, comprueba el precio en tu bróker.",
        ]),
    ],
}


# Documentos por la clave que se usa en la dirección (?legal=terminos|privacidad|riesgo).
DOCUMENTOS = {"terminos": TERMINOS, "privacidad": PRIVACIDAD, "riesgo": RIESGO}


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara contenido .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
