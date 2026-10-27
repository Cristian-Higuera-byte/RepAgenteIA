# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara perfil_copia .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Ajuste del perfil de inversor del seguidor para que se parezca al de la estrategia que copia.

Al copiar, el usuario puede pedir que su perfil de inversor se ajuste a la estrategia: la tolerancia al riesgo pasa a la que corresponde al nivel de riesgo de la estrategia
(bajo, medio o alto) y se agregan a sus instrumentos habituales los tipos de activo que opera. La experiencia y el objetivo no se tocan. Antes de aplicar se muestran los
cambios y se guarda el perfil anterior en la copia (`copias.perfil_previo`) para poder restaurarlo al dejar de copiar. Se lee y se guarda con `perfil/almacen.py`.
Las reglas de riesgo operativas de la plataforma (riesgo por operación, pérdida diaria, etc.) son globales y no dependen del perfil de cada usuario, así que no cambian.
"""
from componentes_plataforma.perfil import almacen

# Tolerancia al riesgo del perfil que corresponde a cada nivel de riesgo de la estrategia
_TOLERANCIA = {"bajo": "conservador", "medio": "moderado", "alto": "agresivo"}
# Instrumento del perfil que corresponde a cada tipo de activo que registra la plataforma
_INSTRUMENTO = {"Forex": "forex", "Índices": "indices", "Materias primas": "materias", "Metales": "materias", "Criptomonedas": "cripto", "Acciones": "acciones", "ETF": "etf"}
# Textos para mostrar
_NOMBRES = {"conservador": "Conservador", "moderado": "Moderado", "agresivo": "Agresivo", "forex": "Divisas (Forex)", "indices": "Índices", "materias": "Materias primas",
            "cripto": "Criptomonedas", "acciones": "Acciones", "etf": "ETF"}


# TITULO NOMBRE

def _nombre(valor) -> str:
    """Texto para mostrar de un valor del perfil: un nombre conocido, la lista de nombres o «Sin definir»."""
    if isinstance(valor, list):
        return ", ".join(_NOMBRES.get(v, str(v)) for v in valor) or "Sin definir"
    return _NOMBRES.get(valor, str(valor)) if valor else "Sin definir"


# TITULO PROPUESTA

def propuesta(usuario_id, riesgo: str, tipos_activo: list) -> dict:
    """Calcula cómo quedaría el perfil del usuario al asemejarse a una estrategia de riesgo `riesgo` que opera los `tipos_activo` (nombres como «Índices»).

    Devuelve {"cambios": [{"campo", "etiqueta", "antes", "despues"}], "nuevos": {campo: valor a guardar}, "previos": {campo: valor actual}} con solo lo que cambiaría; vacío
    si el perfil ya se parece a la estrategia."""
    perfil = almacen.leer(usuario_id) or {}
    cambios, nuevos, previos = [], {}, {}
    tolerancia = _TOLERANCIA.get(riesgo)
    if tolerancia and perfil.get("tolerancia_riesgo") != tolerancia:
        cambios.append({"campo": "tolerancia_riesgo", "etiqueta": "Tolerancia al riesgo", "antes": _nombre(perfil.get("tolerancia_riesgo")), "despues": _nombre(tolerancia)})
        nuevos["tolerancia_riesgo"], previos["tolerancia_riesgo"] = tolerancia, perfil.get("tolerancia_riesgo")
    actuales = list(perfil.get("instrumentos") or [])
    agregar = [i for i in dict.fromkeys(_INSTRUMENTO[t] for t in tipos_activo if t in _INSTRUMENTO) if i not in actuales]
    if agregar:
        cambios.append({"campo": "instrumentos", "etiqueta": "Instrumentos que operas", "antes": _nombre(actuales), "despues": _nombre(actuales + agregar)})
        nuevos["instrumentos"], previos["instrumentos"] = actuales + agregar, actuales
    return {"cambios": cambios, "nuevos": nuevos, "previos": previos}


# TITULO APLICAR

def aplicar(usuario_id, valores: dict) -> bool:
    """Guarda en el perfil del usuario los `valores` (campo: valor). Devuelve True si se pudo guardar."""
    return bool(valores) and bool(almacen.guardar(usuario_id, valores).get("ok"))


# TITULO RESTAURAR

def restaurar(usuario_id, previos: dict | None) -> bool:
    """Devuelve al perfil del usuario los valores que tenía antes de ajustarlo (`copias.perfil_previo`). Un valor vacío se guarda como vacío. True si se pudo guardar."""
    if not previos:
        return False
    return bool(almacen.guardar(usuario_id, {k: (v if v is not None else "") for k, v in previos.items()}).get("ok"))



# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara perfil_copia .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
