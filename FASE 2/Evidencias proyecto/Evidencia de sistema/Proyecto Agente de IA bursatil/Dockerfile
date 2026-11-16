# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.

# Imagen del sistema: dashboard (Streamlit, puerto 8501) y servidor de precios (puerto 8000) en un solo contenedor.
# Construir:  docker compose build        Levantar:  docker compose up -d
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Santiago \
    SERVIDOR_HOST=0.0.0.0

WORKDIR /app

# Las dependencias se instalan antes de copiar el código para aprovechar la caché de capas de Docker.
COPY requirements.txt .
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

COPY . .

# El sistema no corre como administrador dentro del contenedor.
RUN useradd --create-home --uid 10001 pyj && mkdir -p /app/data && chown -R pyj:pyj /app
USER pyj

EXPOSE 8501 8000

HEALTHCHECK --interval=30s --timeout=6s --start-period=45s --retries=3 CMD ["python", "despliegue/salud.py"]

CMD ["python", "despliegue/arranque_docker.py"]
