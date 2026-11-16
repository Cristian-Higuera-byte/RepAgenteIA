"""Descarga la lista pública de dominios de correo temporal (proyecto disposable-email-domains) a herramientas/listas/dominios_temporales.txt.

Uso (en el servidor, con el entorno activado):  python actualizar_dominios_temporales.py
No hace falta reiniciar: el registro relee el archivo cuando cambia. Repetir cada cierto tiempo (por ejemplo, una vez al mes).
"""
import os
import sys
import urllib.request

URL = "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf"
DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "herramientas", "listas", "dominios_temporales.txt")


def main() -> int:
    """Descarga la lista, comprueba que tenga un tamaño razonable y reemplaza el archivo; devuelve 0 si salió bien."""
    with urllib.request.urlopen(URL, timeout=30) as respuesta:
        texto = respuesta.read().decode("utf-8")
    dominios = sorted({l.strip().lower() for l in texto.splitlines() if l.strip() and not l.startswith("#") and "." in l})
    if len(dominios) < 1000:
        print(f"La lista descargada tiene solo {len(dominios)} dominios; no se reemplaza el archivo.", file=sys.stderr)
        return 1
    with open(DESTINO, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Dominios de correo temporal (fuente: disposable-email-domains). Lo genera actualizar_dominios_temporales.py\n")
        f.write("\n".join(dominios) + "\n")
    print(f"{len(dominios)} dominios guardados en {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
