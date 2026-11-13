## --- Etapa 1: build del frontend ---
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

## --- Etapa 2: backend + frontend compilado ---
FROM python:3.12-slim AS final

# Dependencias de sistema para WeasyPrint y PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Usuario sin privilegios
RUN groupadd -g 10001 appuser && useradd -u 10001 -g appuser -m appuser

WORKDIR /app

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir .

COPY backend/app/ ./app/
COPY prompts/ ./prompts/
COPY datos/ ./datos/
COPY --from=frontend-build /frontend/dist ./static/

RUN chown -R appuser:appuser /app
USER 10001

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
