# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------- INICIO Piña y Jara _prueba_verificacion_correo .PY --------------------------
# -------------------------------------------------------------------------------------------------------

"""
_prueba_verificacion_correo.py
------------------------------
Prueba la confirmación del correo y la recuperación de contraseña sin base de datos real ni servidor de correo: usa una base en memoria y un SMTP falso.
Ejecutar: python _prueba_verificacion_correo.py
"""
import os
import re
import smtplib
import sys
from datetime import datetime, timedelta, timezone

os.environ.setdefault("BASE_DATOS", "supabase")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from herramientas import correo, gestor_autenticacion as gestor, sesion_persistente, verificacion_correo as enlaces

# TITULO BASE EN MEMORIA


def _fecha(texto):
    """Convierte el texto ISO guardado en datetime con zona horaria."""
    return enlaces.leer_fecha(texto)


class Respuesta:
    """Resultado de una consulta: las filas afectadas o leídas."""

    def __init__(self, data):
        self.data = data
        self.count = len(data)


class Consulta:
    """Constructor de consultas mínimo sobre listas de diccionarios, con la misma forma que usa el código real."""

    def __init__(self, filas, accion=None, datos=None):
        self.filas, self.accion, self.datos = filas, accion, datos
        self.filtros, self.orden, self.tope = [], None, None

    def select(self, *_):
        self.accion = "select"
        return self

    def insert(self, datos):
        self.accion, self.datos = "insert", datos
        return self

    def update(self, datos):
        self.accion, self.datos = "update", datos
        return self

    def delete(self):
        self.accion = "delete"
        return self

    def _filtro(self, columna, prueba):
        self.filtros.append((columna, prueba))
        return self

    def eq(self, columna, valor):
        return self._filtro(columna, lambda x: x == valor)

    def is_(self, columna, valor):
        return self._filtro(columna, lambda x: x is None)

    def gt(self, columna, valor):
        return self._filtro(columna, lambda x: _fecha(x) > _fecha(valor))

    def gte(self, columna, valor):
        return self._filtro(columna, lambda x: _fecha(x) >= _fecha(valor))

    def order(self, columna, desc=False):
        self.orden = (columna, desc)
        return self

    def limit(self, cantidad):
        self.tope = cantidad
        return self

    def execute(self):
        if self.accion == "insert":
            fila = dict(self.datos)
            fila["id"] = max([f.get("id", 0) for f in self.filas] + [0]) + 1
            for columna, valor in self.defecto.items():
                fila.setdefault(columna, valor)
            self.filas.append(fila)
            return Respuesta([dict(fila)])
        elegidas = [f for f in self.filas if all(c in f and p(f[c]) for c, p in self.filtros)]
        if self.accion == "update":
            for fila in elegidas:
                fila.update(self.datos)
        elif self.accion == "delete":
            for fila in elegidas:
                self.filas.remove(fila)
        if self.orden:
            elegidas.sort(key=lambda f: f[self.orden[0]], reverse=self.orden[1])
        if self.tope:
            elegidas = elegidas[: self.tope]
        return Respuesta([dict(f) for f in elegidas])


class BaseMemoria:
    """Cliente falso con las tablas `usuarios` y `enlaces_correo` en listas."""

    DEFECTOS = {"usuarios": {"correo_verificado": None}, "enlaces_correo": {"usado_en": None}}

    def __init__(self):
        self.tablas = {"usuarios": [], "enlaces_correo": []}

    def table(self, nombre):
        consulta = Consulta(self.tablas[nombre])
        consulta.defecto = {k: v for k, v in self.DEFECTOS[nombre].items() if v is not None or nombre == "enlaces_correo"}
        return consulta


# TITULO SMTP FALSO

class SmtpFalso:
    """Reemplaza smtplib.SMTP_SSL: guarda los mensajes enviados en vez de enviarlos."""

    enviados = []
    fallar = False

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def login(self, usuario, clave):
        if SmtpFalso.fallar:
            raise smtplib.SMTPAuthenticationError(535, b"rechazado")

    def send_message(self, mensaje):
        SmtpFalso.enviados.append(mensaje)


def texto_de(mensaje):
    """Texto simple del mensaje."""
    return mensaje.get_body(preferencelist=("plain",)).get_content()


def token_de(mensaje, parametro):
    """Extrae el token del enlace que viaja en el correo."""
    return re.search(parametro + r"=([\w-]+)", texto_de(mensaje)).group(1)


# TITULO PREPARACION

smtplib.SMTP_SSL = SmtpFalso
for variable, valor in {"CORREO_SERVIDOR": "smtp.prueba.cl", "CORREO_PUERTO": "465", "CORREO_USUARIO": "no-responder@prueba.cl",
                        "CORREO_CLAVE": "clave-secreta", "PLATAFORMA_URL": "https://plataforma.prueba.cl/"}.items():
    os.environ[variable] = valor

revocadas = []
sesion_persistente.revocar_todas = lambda usuario_id: revocadas.append(usuario_id)

aciertos, fallos = 0, []


def comprobar(condicion, descripcion):
    """Cuenta un acierto o registra el fallo."""
    global aciertos
    if condicion:
        aciertos += 1
    else:
        fallos.append(descripcion)
        print(f"  FALLA: {descripcion}")


def nueva_base():
    """Deja una base vacía, sin correos enviados y con el SMTP funcionando."""
    base = BaseMemoria()
    gestor._supabase = base
    SmtpFalso.enviados.clear()
    SmtpFalso.fallar = False
    revocadas.clear()
    return base


def retroceder(base, minutos):
    """Hace que los enlaces existentes parezcan creados hace `minutos` minutos."""
    for fila in base.tablas["enlaces_correo"]:
        fila["creado_en"] = (_fecha(fila["creado_en"]) - timedelta(minutes=minutos)).isoformat()


# TITULO CASOS

print("Sin verificación activa (modo anterior)")
os.environ.pop("VERIFICACION_CORREO", None)
base = nueva_base()
r = gestor.registrar_usuario("Ana", "Ana@Prueba.cl", "Zorro#Azul42")
comprobar(r["ok"] and not r.get("requiere_verificacion"), "el registro sin verificación inicia como antes")
comprobar("correo_verificado" not in base.tablas["usuarios"][0], "sin verificación no se escribe la columna correo_verificado")
comprobar(not SmtpFalso.enviados, "sin verificación no se envía correo")
comprobar(gestor.autenticar_usuario("ana@prueba.cl", "Zorro#Azul42")["ok"], "el acceso funciona sin verificación")

print("Contraseña")
for clave, motivo in (("Co1!", "menos de 8 caracteres"), ("Sololetras#", "sin número"), ("12345678", "solo números"), ("zorro#azul42", "sin mayúscula"),
                      ("ZORRO#AZUL42", "sin minúscula"), ("ZorroAzul42", "sin símbolo"), ("123456", "123456"), ("Password1!", "clave común"),
                      ("P@ssw0rd!", "clave común disfrazada"), ("Qwerty123!", "clave común"), ("Clave1234!", "clave común")):
    comprobar(gestor.validar_contrasena(clave) is not None, f"se rechaza: {motivo} ({clave})")
comprobar(gestor.validar_contrasena("Zorro#Azul42") is None, "con los cinco requisitos y no común se acepta")
comprobar(not gestor.registrar_usuario("Zoe", "zoe@prueba.cl", "abc123")["ok"], "el registro rechaza una contraseña débil")
comprobar(not gestor.registrar_usuario("Zoe", "zoe@prueba.cl", "123456")["ok"], "el registro rechaza 123456")
comprobar(not gestor.cambiar_contrasena(1, "Zorro#Azul42", "123456")["ok"], "el cambio desde el perfil rechaza 123456")

print("Registro con verificación activa")
os.environ["VERIFICACION_CORREO"] = "true"
base = nueva_base()
r = gestor.registrar_usuario("Beto", "beto@prueba.cl", "Zorro#Azul42")
comprobar(r["ok"] and r.get("requiere_verificacion") is True, "el registro pide verificar")
comprobar(base.tablas["usuarios"][0].get("correo_verificado") is False, "la cuenta nueva queda sin verificar")
comprobar(len(SmtpFalso.enviados) == 1 and SmtpFalso.enviados[0]["To"] == "beto@prueba.cl", "se envió un correo al destinatario")
correo_1 = SmtpFalso.enviados[0]
comprobar("https://plataforma.prueba.cl/?verificar=" in texto_de(correo_1), "el enlace usa PLATAFORMA_URL sin barra doble")
token = token_de(correo_1, "verificar")
guardado = base.tablas["enlaces_correo"][0]
comprobar(token not in str(guardado) and guardado["token_hash"] == enlaces.hash_de(token), "en la base solo se guarda el hash del token")
comprobar("clave-secreta" not in str(correo_1), "la clave del buzón no aparece en el mensaje")
a = gestor.autenticar_usuario("beto@prueba.cl", "Zorro#Azul42")
comprobar(not a["ok"] and a.get("codigo") == "sin_verificar" and a["usuario"] is None, "sin verificar no puede entrar")
comprobar(a.get("pendiente", {}).get("email") == "beto@prueba.cl", "el rechazo trae los datos para reenviar el enlace")
comprobar(not gestor.autenticar_usuario("beto@prueba.cl", "mala")["ok"] and "codigo" not in gestor.autenticar_usuario("beto@prueba.cl", "mala"),
          "con contraseña errónea no se revela el estado de verificación")

print("Confirmar el correo")
comprobar(not gestor.verificar_correo("token-inventado")["ok"], "un token inventado no sirve")
comprobar(not gestor.verificar_correo("")["ok"], "un token vacío no sirve")
comprobar(not gestor.restablecer_contrasena(token, "Nube#Roja77x")["ok"], "un enlace de verificación no sirve para recuperar")
comprobar(base.tablas["enlaces_correo"][0]["usado_en"] is None, "el intento con tipo equivocado no gasta el enlace")
comprobar(gestor.verificar_correo(token)["ok"], "el enlace correcto confirma")
comprobar(base.tablas["usuarios"][0]["correo_verificado"] is True, "la cuenta queda verificada")
comprobar(not gestor.verificar_correo(token)["ok"], "el enlace solo sirve una vez")
comprobar(gestor.autenticar_usuario("beto@prueba.cl", "Zorro#Azul42")["ok"], "verificada, puede entrar")

print("Enlace vencido")
base = nueva_base()
gestor.registrar_usuario("Caro", "caro@prueba.cl", "Zorro#Azul42")
token = token_de(SmtpFalso.enviados[0], "verificar")
base.tablas["enlaces_correo"][0]["expira_en"] = (enlaces.ahora_utc() - timedelta(seconds=1)).isoformat()
comprobar(not gestor.verificar_correo(token)["ok"], "un enlace vencido no sirve")
comprobar(base.tablas["usuarios"][0]["correo_verificado"] is False, "un enlace vencido no verifica la cuenta")
dur = enlaces.duracion_de
comprobar(dur("verificacion") == timedelta(hours=24) and dur("recuperacion") == timedelta(minutes=60), "duraciones: 24 h y 60 min")

print("Reenvío y límites")
usuario = base.tablas["usuarios"][0]
r = gestor.reenviar_verificacion(usuario["id"], "Caro", usuario["email"])
comprobar(not r["ok"] and "minuto" in r["mensaje"], "pedir otro enlace al instante se frena")
retroceder(base, 2)
viejo = token
r = gestor.reenviar_verificacion(usuario["id"], "Caro", usuario["email"])
comprobar(r["ok"] and len(SmtpFalso.enviados) == 2, "pasado el minuto se reenvía")
nuevo = token_de(SmtpFalso.enviados[1], "verificar")
comprobar(not gestor.verificar_correo(viejo)["ok"], "al pedir uno nuevo el anterior queda invalidado")
comprobar(gestor.verificar_correo(nuevo)["ok"], "el enlace nuevo funciona")
base = nueva_base()
gestor.registrar_usuario("Dani", "dani@prueba.cl", "Zorro#Azul42")
usuario = base.tablas["usuarios"][0]
for _ in range(enlaces.MAXIMO_ENVIOS_POR_DIA - 1):
    retroceder(base, 2)
    comprobar(gestor.reenviar_verificacion(usuario["id"], "Dani", usuario["email"])["ok"], "envíos dentro del límite diario")
retroceder(base, 2)
r = gestor.reenviar_verificacion(usuario["id"], "Dani", usuario["email"])
comprobar(not r["ok"] and "mañana" in r["mensaje"], "el sexto envío del día se rechaza")

print("Fallo del servidor de correo")
base = nueva_base()
SmtpFalso.fallar = True
r = gestor.registrar_usuario("Eli", "eli@prueba.cl", "Zorro#Azul42")
comprobar(r["ok"] and "no pudimos enviar" in r["mensaje"], "si el correo falla, la cuenta se crea y se avisa")
comprobar(not base.tablas["enlaces_correo"], "el enlace de un envío fallido se borra (no cuenta para el límite)")
comprobar("clave-secreta" not in r["mensaje"] and "smtp" not in r["mensaje"].lower(), "el aviso no muestra detalles técnicos")
SmtpFalso.fallar = False
usuario = base.tablas["usuarios"][0]
comprobar(gestor.reenviar_verificacion(usuario["id"], "Eli", usuario["email"])["ok"], "se puede reenviar enseguida tras un fallo")

print("Recuperar contraseña")
base = nueva_base()
gestor.registrar_usuario("Fer", "fer@prueba.cl", "Zorro#Azul42")
SmtpFalso.enviados.clear()
generico = gestor.solicitar_recuperacion("nadie@prueba.cl")
comprobar(generico["ok"] and not SmtpFalso.enviados, "correo desconocido: mismo mensaje y no se envía nada")
conocido = gestor.solicitar_recuperacion("  FER@prueba.cl ")
comprobar(conocido["mensaje"] == generico["mensaje"] and len(SmtpFalso.enviados) == 1, "correo conocido: mismo mensaje y sí se envía")
comprobar(SmtpFalso.enviados[0]["To"] == "fer@prueba.cl", "se envía a la dirección guardada")
tok = token_de(SmtpFalso.enviados[0], "recuperar")
comprobar(not gestor.verificar_correo(tok)["ok"], "un enlace de recuperación no confirma el correo")
comprobar(not gestor.restablecer_contrasena(tok, "corta1")["ok"], "una contraseña débil se rechaza")
comprobar(base.tablas["enlaces_correo"][0]["usado_en"] is None, "la contraseña débil no gasta el enlace")
r = gestor.restablecer_contrasena(tok, "Luna#Verde58")
comprobar(r["ok"], "con contraseña válida se restablece")
comprobar(revocadas == [base.tablas["usuarios"][0]["id"]], "se cierran las sesiones guardadas")
comprobar(base.tablas["usuarios"][0]["correo_verificado"] is True, "recuperar también deja el correo verificado")
comprobar(not gestor.restablecer_contrasena(tok, "Luna#Verde58")["ok"], "el enlace de recuperación solo sirve una vez")
comprobar(gestor.autenticar_usuario("fer@prueba.cl", "Luna#Verde58")["ok"], "entra con la contraseña nueva")
comprobar(not gestor.autenticar_usuario("fer@prueba.cl", "Zorro#Azul42")["ok"], "la contraseña anterior ya no sirve")
comprobar(gestor.solicitar_recuperacion("")["ok"] is False, "correo vacío se rechaza")
for variable in ("CORREO_CLAVE",):
    guardada = os.environ.pop(variable)
    comprobar(not gestor.solicitar_recuperacion("fer@prueba.cl")["ok"], "sin correo configurado la recuperación avisa que no está disponible")
    os.environ[variable] = guardada

print("Correo y plantillas")
comprobar(correo.configurado(), "configurado() detecta las variables")
asunto, texto, cuerpo = correo.plantilla_verificacion("<b>Ana</b>", "https://x.cl/?verificar=a&b=1", 24)
comprobar("<b>Ana</b>" not in cuerpo and "&lt;b&gt;" in cuerpo, "el nombre se escapa en el HTML")
try:
    correo.enviar("a@b.cl\nBcc: otro@x.cl", "asunto", "texto")
    comprobar(False, "una dirección con salto de línea debe rechazarse")
except correo.ErrorCorreo:
    comprobar(True, "")

print(f"\n{aciertos} comprobaciones correctas, {len(fallos)} fallas")
if fallos:
    sys.exit(1)

# -------------------------------------------------------------------------------------------------------
# -------------------------- FIN Piña y Jara _prueba_verificacion_correo .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
