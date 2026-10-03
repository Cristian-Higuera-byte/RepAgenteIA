"""Extrae HTML, CSS y JavaScript desde central_panel.py.

Este script debe ejecutarse antes de reemplazar el archivo
components/central_panel.py original.

Uso:

    python scripts/extract_central_chart.py
"""

from __future__ import annotations

import ast
from html import unescape
from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_FILE = (
    PROJECT_ROOT
    / "components"
    / "central_panel.py"
)

ASSETS_DIR = (
    PROJECT_ROOT
    / "components"
    / "trading_chart"
    / "assets"
)


def cargar_template_desde_ast(
    source_file: Path,
) -> str:
    """Obtiene _CHART_TEMPLATE sin importar el módulo."""

    source = source_file.read_text(
        encoding="utf-8",
    )

    module = ast.parse(
        source,
        filename=str(source_file),
    )

    for node in module.body:
        if not isinstance(
            node,
            (ast.Assign, ast.AnnAssign),
        ):
            continue

        value_node: ast.expr | None

        if isinstance(node, ast.Assign):
            targets = node.targets
            value_node = node.value
        else:
            targets = [node.target]
            value_node = node.value

        if value_node is None:
            continue

        for target in targets:
            if (
                isinstance(target, ast.Name)
                and target.id == "_CHART_TEMPLATE"
            ):
                value = ast.literal_eval(value_node)

                if not isinstance(value, str):
                    raise TypeError(
                        "_CHART_TEMPLATE no es una cadena."
                    )

                return value

    raise RuntimeError(
        "No se encontró _CHART_TEMPLATE en "
        f"{source_file}."
    )


def normalizar_template(template: str) -> str:
    """Normaliza entidades HTML de copias provenientes del chat."""

    normalized = template

    if (
        "&lt;style" in normalized
        or "&lt;div" in normalized
        or "&lt;script" in normalized
    ):
        normalized = unescape(normalized)

    return normalized


def extraer_bloques(
    template: str,
    tag: str,
) -> list[str]:
    """Extrae el contenido interno de una etiqueta."""

    pattern = re.compile(
        rf"<{tag}\b[^>]*>(.*?)</{tag}>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    return [
        match.group(1).strip()
        for match in pattern.finditer(template)
    ]


def encontrar_script_externo(
    template: str,
) -> str:
    """Encuentra el script externo de Lightweight Charts."""

    pattern = re.compile(
        (
            r"<script\b[^>]*\bsrc=(['\"]?)"
            r"(?P<url>[^\"'>]*lightweight-charts[^\"'>]*)"
            r"\1[^>]*>\s*</script>"
        ),
        flags=re.IGNORECASE | re.DOTALL,
    )

    match = pattern.search(template)

    if not match:
        return (
            "https://cdn.jsdelivr.net/npm/"
            "lightweight-charts@4.1.3/dist/"
            "lightweight-charts.standalone."
            "production.js"
        )

    return match.group("url")


def eliminar_styles_y_scripts(
    template: str,
) -> str:
    """Deja solamente la estructura HTML del componente."""

    without_styles = re.sub(
        r"<style\b[^>]*>.*?</style>",
        "",
        template,
        flags=re.IGNORECASE | re.DOTALL,
    )

    without_scripts = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        without_styles,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return without_scripts.strip()


def aplicar_configuracion_global(
    main_script: str,
) -> str:
    """
    Hace que chart.js acepte tanto los placeholders antiguos
    como window.TRADING_CHART_CONFIG.

    La sustitución conserva compatibilidad con el código actual.
    """

    old_block = """  var API = __API_URL_JS__;
  var SIMBOLO = __SIMBOLO_JS__;
  var DIGITS = __DIGITS__;
  var PIP = __PIP__;"""

    new_block = """  var CONFIG = window.TRADING_CHART_CONFIG || {};
  var API = CONFIG.apiUrl || __API_URL_JS__;
  var SIMBOLO = CONFIG.symbol || __SIMBOLO_JS__;
  var DIGITS = Number.isFinite(CONFIG.digits)
    ? CONFIG.digits
    : __DIGITS__;
  var PIP = Number.isFinite(CONFIG.pipSize)
    ? CONFIG.pipSize
    : __PIP__;
  var TICK_SIZE = Number.isFinite(CONFIG.tickSize)
    ? CONFIG.tickSize
    : Math.pow(10, -DIGITS);"""

    if old_block not in main_script:
        print(
            "[AVISO] No se encontró el bloque inicial "
            "esperado en chart.js."
        )
        print(
            "[AVISO] El archivo seguirá utilizando los "
            "placeholders originales."
        )
        return main_script

    result = main_script.replace(
        old_block,
        new_block,
        1,
    )

    old_pf = (
        "var PF = { type: 'price', precision: DIGITS, "
        "minMove: Math.pow(10, -DIGITS) };"
    )

    new_pf = (
        "var PF = { type: 'price', precision: DIGITS, "
        "minMove: TICK_SIZE };"
    )

    return result.replace(
        old_pf,
        new_pf,
        1,
    )


def construir_chart_html(
    body_html: str,
    external_script_url: str,
) -> str:
    """Construye el HTML que será utilizado por template.py."""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <style>
__CHART_CSS__
    </style>
</head>
<body>
{body_html}

<script>
window.TRADING_CHART_CONFIG = __CHART_CONFIG_JS__;
</script>

<script>
__PREFLIGHT_JS__
</script>

{external_script_url}script>

<script>
__CHART_JS__
</script>
</body>
</html>
"""


def escribir_archivo(
    path: Path,
    content: str,
) -> None:
    """Escribe el archivo y muestra su ruta."""

    path.write_text(
        content.rstrip() + "\n",
        encoding="utf-8",
    )

    relative_path = path.relative_to(
        PROJECT_ROOT
    )

    print(f"[OK] {relative_path}")


def main() -> int:
    """Ejecuta la extracción completa."""

    if not SOURCE_FILE.exists():
        print(
            "[ERROR] No existe el archivo origen:"
        )
        print(SOURCE_FILE)
        return 1

    ASSETS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        template = cargar_template_desde_ast(
            SOURCE_FILE
        )

        template = normalizar_template(template)

        styles = extraer_bloques(
            template,
            "style",
        )

        scripts = extraer_bloques(
            template,
            "script",
        )

        if not styles:
            raise RuntimeError(
                "No se encontró ningún bloque <style>."
            )

        if len(scripts) < 2:
            raise RuntimeError(
                "Se esperaban al menos dos scripts inline."
            )

        css = "\n\n".join(styles)
        preflight_js = scripts[0]
        main_js = scripts[-1]

        main_js = aplicar_configuracion_global(
            main_js
        )

        external_script_url = encontrar_script_externo(
            template
        )

        body_html = eliminar_styles_y_scripts(
            template
        )

        chart_html = construir_chart_html(
            body_html=body_html,
            external_script_url=external_script_url,
        )

        escribir_archivo(
            ASSETS_DIR / "chart.css",
            css,
        )

        escribir_archivo(
            ASSETS_DIR / "preflight.js",
            preflight_js,
        )

        escribir_archivo(
            ASSETS_DIR / "chart.js",
            main_js,
        )

        escribir_archivo(
            ASSETS_DIR / "chart.html",
            chart_html,
        )

    except Exception as error:
        print(
            f"[ERROR] No fue posible extraer los recursos: "
            f"{error}"
        )
        return 1

    print()
    print("Extracción completada.")
    print()
    print(
        "Comprueba los recursos antes de reemplazar "
        "components/central_panel.py."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())