# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------- INICIO Piña y Jara correos_temporales .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
correos_temporales.py
---------------------
Rechazo de correos desechables (temporales) al crear una cuenta.

Los servicios de correo temporal (10minutemail, Guerrilla Mail, Mailinator, etc.) entregan un buzón público que dura minutos: quien se registra
con uno puede confirmar el enlace, pero la cuenta queda sin un correo real para recuperar la contraseña, enviar avisos o aplicar los límites por
persona. La plataforma compara el dominio del correo contra una lista de dominios desechables conocidos (incluidos los subdominios).

- Lista blanca (activa por defecto): solo se aceptan correos de proveedores conocidos (Gmail, Outlook, Hotmail, Yahoo, iCloud, Proton, los de cada país de Latinoamérica,
  universidades y organismos públicos de la región) más los dominios de CORREOS_DOMINIOS_PERMITIDOS_EXTRA. Es la defensa que de verdad funciona contra el correo temporal: los servicios
  cambian de dominio todos los días y una lista de bloqueo siempre llega tarde. CORREOS_SOLO_CONOCIDOS=false la apaga y deja solo la lista de bloqueo. Quien entra
  con Google no pasa por la lista blanca (Google ya verificó su identidad), pero sí por la de bloqueo.
- La lista integrada cubre los servicios más usados y se suma la lista pública de herramientas/listas/dominios_temporales.txt (se actualiza con actualizar_dominios_temporales.py); se puede ampliar sin tocar el código con CORREOS_TEMPORALES_EXTRA en el .env (dominios separados por coma).
- CORREOS_TEMPORALES_PERMITIDOS (también en el .env) saca dominios de la lista, por si alguno se bloquea por error.
- Un dominio que no esté en la lista no se detecta: la lista hay que mantenerla al día.
"""
import os
import re

# Formato mínimo de un correo: algo@dominio.tld, sin espacios
_FORMATO = re.compile(r"^[^@\s]+@([^@\s]+\.[^@\s.]{2,})$")

# Dominios desechables conocidos (en minúsculas, sin "@")
_DOMINIOS_TEMPORALES = frozenset("""
10minutemail.com 10minutemail.net 10minutemail.org 10minemail.com 10mail.org 20minutemail.com 20minutemail.it 30minutemail.com
temp-mail.org temp-mail.io temp-mail.ru tempmail.com tempmail.net tempmail.org tempmail.dev tempmail.email tempmailo.com tempmail.plus
tempmailaddress.com temp-mail.com tempail.com tempr.email tempinbox.com tempemail.net tempemail.com tempmailer.com tempmailer.de
guerrillamail.com guerrillamail.net guerrillamail.org guerrillamail.biz guerrillamail.de guerrillamail.info guerrillamailblock.com
grr.la sharklasers.com pokemail.net spam4.me guerrillamail.es
mailinator.com mailinator.net mailinator.org mailinator2.com mailinater.com notmailinator.com reallymymail.com
yopmail.com yopmail.net yopmail.fr cool.fr.nf jetable.fr.nf nospam.ze.tc nomail.xl.cx mega.zik.dj speed.1s.fr courriel.fr.nf moncourrier.fr.nf monemail.fr.nf monmail.fr.nf
throwawaymail.com throwam.com trashmail.com trashmail.net trashmail.org trashmail.de trashmail.me trashmail.io trashmail.at trash-mail.com trash-mail.de
trashmail.ws wegwerfmail.de wegwerfmail.net wegwerfmail.org wegwerfemail.de
getnada.com nada.email nada.ltd getairmail.com airmail.cc
maildrop.cc mailnesia.com mailcatch.com mailnull.com mailtemp.info mail-temporaire.fr mailtothis.com mailzilla.com mailforspam.com
dispostable.com discard.email discardmail.com discardmail.de spambox.us spambog.com spambog.de spambog.ru spamgourmet.com spamgourmet.net spamex.com
fakeinbox.com fakemail.fr fakemailgenerator.com fake-mail.net mailmetrash.com mytrashmail.com
anonbox.net anonymbox.com anonmails.de
burnermail.io burner.kiwi
emailondeck.com email-fake.com emailfake.com fakemail.net emailtemporanea.com emailtemporanea.net emailtemporal.org correotemporal.org
temporarymail.com temporary-mail.net temporaryemail.net temporaryemail.us
moakt.com moakt.cc moakt.ws bccto.me
mohmal.com mohmal.im mohmal.in mohmal.tech
minuteinbox.com minutemail.com
mintemail.com mt2014.com mt2015.com
33mail.com mailsac.com inboxbear.com inboxkitten.com
tmail.ws tmailor.com tmpmail.net tmpmail.org tmpeml.com
harakirimail.com incognitomail.com incognitomail.net incognitomail.org
dropmail.me 10mail.xyz emlhub.com emltmp.com
mailpoof.com mail7.io mail.tm mail.gw
dcctb.com dayrep.com einrot.com fleckens.hu gustr.com jourrapide.com rhyta.com superrito.com teleworm.us armyspy.com cuvox.de
kurzepost.de lroid.com luxusmail.org meltmail.com mvrht.net nepwk.com nurfuerspam.de objectmail.com ownmail.net proxymail.eu rcpt.at
sofort-mail.de sogetthis.com soodonims.com spoofmail.de stuffmail.de supergreatmail.com suremail.info tafmail.com thankyou2010.com
trbvm.com trbvn.com turual.com twinmail.de tyldd.com uggsrock.com upliftnow.com uplipht.com venompen.com veryrealemail.com viditag.com
viralplays.com vpn.st vsimcard.com webemail.me wh4f.org whyspam.me willhackforfood.biz winemaven.info wronghead.com wuzup.net wuzupmail.net
xagloo.com xemaps.com xents.com xmaily.com xoxy.net yapped.net yogamaven.com yomail.info yuurok.com zehnminutenmail.de
zippymail.info zoaxe.com zoemail.org
gmailnator.com emailnator.com smailpro.com artegin.com bwingmedia.com
chacuo.net eyepaste.com filzmail.com get2mail.fr gishpuppy.com great-host.in grr.la guerillamail.com haltospam.com hidemail.de hulapla.de
ieatspam.eu ieatspam.info imails.info inboxalias.com incognitomail.org instant-mail.de jnxjn.com junk1e.com kasmail.com klzlk.com
koszmail.pl kulturbetrieb.info lifebyfood.com link2mail.net listomail.com lopl.co.cz mailbidon.com mailblocks.com mailchop.com
maileater.com mailexpire.com mailfreeonline.com mailguard.me mailimate.com mailin8r.com mailismagic.com mailme.lv mailmoat.com
mailscrap.com mailshell.com mailsiphon.com mailslite.com mailtome.de mailtrash.net mailzilla.org nobulk.com noclickemail.com
nomail.pw nospamfor.us nowmymail.com oneoffemail.com onewaymail.com pjjkp.com plexolan.de pookmail.com 
privatdemail.net punkass.com putthisinyourspamdatabase.com quickinbox.com rmqkr.net rppkn.com s0ny.net safersignup.de
safetymail.info sendspamhere.com shiftmail.com shitmail.me skeefmail.com slopsbox.com smellfear.com snakemail.com sneakemail.com
spamavert.com spambox.info spamcero.com spamcorptastic.com spamday.com spamfree24.com spamhereplease.com spamhole.com spamify.com
spaml.com spammotel.com spamobox.com spamspot.com spamthis.co.uk spamtroll.net
""".split())


# Códigos de país de Latinoamérica (más España y Portugal, de donde vienen muchos proveedores que se usan en la región)
_PAISES = ("ar", "bo", "br", "cl", "co", "cr", "cu", "do", "ec", "sv", "gt", "hn", "mx", "ni", "pa", "py", "pe", "pr", "uy", "ve", "es", "pt")

# Proveedores que existen con la misma marca en muchos países (hotmail.com, hotmail.com.mx, hotmail.cl, outlook.com.ar…): se aceptan con «.com», «.es»,
# «.<país>», «.com.<país>» y «.co.<país>». Un servicio temporal no se registra con estos nombres.
_MARCAS_CON_PAIS = frozenset("hotmail outlook live msn yahoo ymail".split())

# Proveedores y dominios conocidos que SÍ se aceptan (en minúsculas, sin "@"); los subdominios también valen
_PROVEEDORES_CONOCIDOS = frozenset("""
gmail.com googlemail.com icloud.com me.com mac.com proton.me protonmail.com pm.me aol.com gmx.com gmx.net gmx.es zoho.com fastmail.com yandex.com mail.com
vtr.net entel.cl movistar.cl tie.cl manquehue.net terra.cl
telmexmail.com prodigy.net.mx prodigy.net.mx megacable.com.mx totalplay.net.mx
fibertel.com.ar speedy.com.ar arnet.com.ar ciudad.com.ar telecentro.com.ar
uol.com.br bol.com.br terra.com.br globo.com ig.com.br r7.com oi.com.br zipmail.com.br globomail.com
une.net.co etb.net.co telecom.com.co
terra.com.pe telefonica.net.pe
adinet.com.uy vera.com.uy movistar.com.uy
cantv.net movistar.com.ve
ice.co.cr racsa.co.cr
cwpanama.net
claro.com.co claro.com.pe claro.com.ar
terra.es telefonica.net movistar.es orange.es ono.com
duocuc.cl duoc.cl uc.cl puc.cl uchile.cl usach.cl udec.cl inacap.cl santotomas.cl uai.cl udd.cl utem.cl
unam.mx itesm.mx tec.mx ipn.mx uba.ar usp.br unicamp.br unal.edu.co uniandes.edu.co
pinayjara.cl rmcabogados.cl
""".split())

# Terminaciones de dominio aceptadas: instituciones educativas y públicas de la región (.edu.mx, .gob.pe, .gov.br, .gub.uy, .ac.cr…)
_SUFIJOS_CONOCIDOS = tuple(sorted({".edu", ".gov", ".mil"} | {f".{tipo}.{pais}" for tipo in ("edu", "gob", "gov", "gub", "mil", "ac", "jus", "leg") for pais in _PAISES}))


# TITULO ES MARCA CON PAIS

def _es_marca_con_pais(dominio: str) -> bool:
    """True si el dominio es de una marca multinacional con terminación de país: hotmail/outlook/live/msn/yahoo/ymail con `.com`, `.es`, `.<país>`, `.com.<país>` o `.co.<país>`."""
    partes = dominio.split(".")
    for i in range(len(partes) - 1):
        if partes[i] not in _MARCAS_CON_PAIS:
            continue
        resto = partes[i + 1:]
        if resto == ["com"] or (len(resto) == 1 and resto[0] in _PAISES) or (len(resto) == 2 and resto[0] in ("com", "co") and resto[1] in _PAISES):
            return True
    return False


# TITULO DOMINIOS DEL ARCHIVO

_ARCHIVO_LISTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listas", "dominios_temporales.txt")
_cache_archivo: tuple[float, frozenset] = (-1.0, frozenset())


def _desde_archivo() -> frozenset:
    """Dominios de herramientas/listas/dominios_temporales.txt (lista pública descargada con actualizar_dominios_temporales.py); se relee solo cuando el archivo cambia."""
    global _cache_archivo
    try:
        modificado = os.path.getmtime(_ARCHIVO_LISTA)
        if modificado != _cache_archivo[0]:
            with open(_ARCHIVO_LISTA, encoding="utf-8") as f:
                dominios = frozenset(l.strip().lower() for l in f if l.strip() and not l.lstrip().startswith("#"))
            _cache_archivo = (modificado, dominios)
    except OSError:
        return frozenset()
    return _cache_archivo[1]


# TITULO DOMINIOS EXTRA Y PERMITIDOS

def _desde_entorno(nombre: str) -> set[str]:
    """Lee del .env una lista de dominios separados por coma, espacio o punto y coma; devuelve un conjunto vacío si la variable no existe."""
    texto = os.environ.get(nombre, "")
    return {d.strip().lower().lstrip("@") for d in re.split(r"[,;\s]+", texto) if d.strip()}


# TITULO DOMINIO DE UN CORREO

def dominio_de(correo: str) -> str:
    """Devuelve el dominio del correo en minúsculas ('' si el correo no tiene un formato válido)."""
    coincide = _FORMATO.match((correo or "").strip().lower())
    return coincide.group(1) if coincide else ""


# TITULO FORMATO VALIDO

def formato_valido(correo: str) -> bool:
    """True si el texto tiene la forma usuario@dominio.tld (sin comprobar que el buzón exista)."""
    return bool(dominio_de(correo))


# TITULO ES TEMPORAL

def es_temporal(correo: str) -> bool:
    """True si el dominio del correo (o uno de sus dominios padre, p. ej. 'x.mailinator.com') figura como servicio de correo desechable."""
    dominio = dominio_de(correo)
    if not dominio:
        return False
    bloqueados = _DOMINIOS_TEMPORALES | _desde_archivo() | _desde_entorno("CORREOS_TEMPORALES_EXTRA")
    permitidos = _desde_entorno("CORREOS_TEMPORALES_PERMITIDOS")
    partes = dominio.split(".")
    for i in range(len(partes) - 1):
        candidato = ".".join(partes[i:])
        if candidato in permitidos:
            return False
        if candidato in bloqueados:
            return True
    return False


# TITULO SOLO CONOCIDOS

def solo_conocidos() -> bool:
    """True si la lista blanca está activa (por defecto sí; CORREOS_SOLO_CONOCIDOS=false la apaga)."""
    return os.environ.get("CORREOS_SOLO_CONOCIDOS", "true").strip().lower() not in ("0", "false", "no", "apagado")


# TITULO ES CONOCIDO

def es_conocido(correo: str) -> bool:
    """True si el dominio del correo es de un proveedor conocido, termina en un sufijo aceptado (.edu, .gob.cl…) o figura en CORREOS_DOMINIOS_PERMITIDOS_EXTRA (también sus subdominios)."""
    dominio = dominio_de(correo)
    if not dominio:
        return False
    if dominio.endswith(_SUFIJOS_CONOCIDOS) or _es_marca_con_pais(dominio):
        return True
    permitidos = _PROVEEDORES_CONOCIDOS | _desde_entorno("CORREOS_DOMINIOS_PERMITIDOS_EXTRA")
    partes = dominio.split(".")
    return any(".".join(partes[i:]) in permitidos for i in range(len(partes) - 1))


# TITULO VALIDAR

def validar(correo: str, verificado_por_google: bool = False) -> str | None:
    """Devuelve el aviso a mostrar si el correo no sirve para crear una cuenta, o None si es aceptable.

    Rechaza el formato inválido, los servicios de correo temporal (lista de bloqueo) y, con la lista blanca activa, los dominios que no son de un proveedor conocido.
    Con `verificado_por_google=True` (el correo viene de «Continuar con Google») no se exige la lista blanca: Google ya comprobó que la persona es dueña del correo."""
    if not formato_valido(correo):
        return "Escribe un correo válido (por ejemplo, nombre@dominio.com)."
    if es_temporal(correo):
        return "No se aceptan correos temporales. Usa un correo personal o de tu empresa."
    if solo_conocidos() and not verificado_por_google and not es_conocido(correo):
        return ("Usa un correo de un proveedor conocido (Gmail, Outlook, Hotmail, Yahoo, iCloud…) o de tu institución. "
                "Si quieres registrarte con el correo de tu empresa, escríbenos desde Soporte.")
    return None


# -------------------------------------------------------------------------------------------------------
# ----------------------------- FIN Piña y Jara correos_temporales .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
