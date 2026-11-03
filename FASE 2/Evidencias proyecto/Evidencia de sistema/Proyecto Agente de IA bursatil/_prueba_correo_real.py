# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------- INICIO Piña y Jara _prueba_correo_real .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
_prueba_correo_real.py
----------------------
Envía UN correo de prueba de verdad con la configuración del .env (CORREO_*), sin tocar la base de datos ni crear enlaces.
Sirve para comprobar, antes de activar la verificación, que el servidor SMTP acepta la conexión, el usuario y la contraseña, y que el mensaje llega.
Uso:  python _prueba_correo_real.py destinatario@dominio.cl
"""
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from herramientas import correo


def main() -> int:
    """Envía el correo de prueba y devuelve 0 si salió bien o 1 si hubo un error (que se imprime sin mostrar la contraseña)."""
    if len(sys.argv) != 2:
        print("Uso: python _prueba_correo_real.py destinatario@dominio.cl")
        return 1
    destinatario = sys.argv[1]
    if not correo.configurado():
        print("Faltan variables CORREO_* en el .env (CORREO_SERVIDOR, CORREO_PUERTO, CORREO_USUARIO, CORREO_CLAVE).")
        return 1
    configuracion = correo.leer_configuracion()
    print(f"Enviando desde {configuracion['usuario']} por {configuracion['servidor']}:{configuracion['puerto']} ({configuracion['seguridad']}) a {destinatario}...")
    enlace = os.environ.get("PLATAFORMA_URL", "https://ejemplo.cl").rstrip("/") + "/?verificar=ENLACE-DE-PRUEBA"
    asunto, texto, cuerpo = correo.plantilla_verificacion("equipo", enlace, 24)
    try:
        correo.enviar(destinatario, "[Prueba] " + asunto, texto, cuerpo)
    except correo.ErrorCorreo as error:
        print(f"ERROR: {error}")
        return 1
    print("Enviado. Revisa la bandeja de entrada y también la carpeta de spam.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -------------------------------------------------------------------------------------------------------
# ---------------------------- FIN Piña y Jara _prueba_correo_real .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
