# CLAUDE.md — SuscriptorIA Incendio

## Proyecto
Copiloto de suscripción y tarificación de seguros de incendio para el mercado chileno.
Especificación completa en `PROMPT_MAESTRO.md` (§0 manda sobre el resto).

## Comandos
```bash
# Backend
cd backend && pip install -e ".[dev]"
pytest -q                          # tests unitarios + integración (sin LLM real)
pytest -m eval                     # evals con LLM real (requiere confirmación, tiene costo)
ruff check backend/
mypy backend/app/dominio/

# Frontend
cd frontend && npm install
npm test                           # Vitest
npm run lint                       # eslint
npm run build                      # build de producción

# Docker local
docker compose up                  # api + db
# GET http://localhost:8000/salud

# Despliegue (requiere confirmación del usuario)
# heroku container:push web -a <app>
# heroku container:release web -a <app>
```

## Convenciones
- Idioma: español de Chile (es-CL). Código (variables, funciones): español.
- Montos: `decimal.Decimal`, nunca `float`. Redondeo con `ROUND_HALF_UP`.
- Tasas y factores en archivos de datos (`RUTA_TARIFARIO`), nunca en el código.
- System prompts en `/prompts/suscriptor_v{N}.md`, nunca como texto inline.
- Capa `dominio/`: solo stdlib + Pydantic, sin IO, sin LLM, sin BD. Es la única que calcula.
- Capa `agente/`: llama a `dominio/` mediante herramientas, nunca calcula.
- Capa `api/`: sin lógica de negocio.
- Frontend: no calcula montos, solo muestra lo que entrega la API.
- Archivos subidos en Postgres (`bytea`), nunca en disco del dyno.

## Reglas (§11)
1. Solo datos ficticios en el repo, fixtures, prompts y logs.
2. Secretos solo en variables de entorno.
3. Tasas y primas solo en `dominio/tarifa.py`.
4. No escribir tasas en el código; viven en el tarifario.
5. No rellenar datos faltantes con valores por defecto.
6. No modificar tests ni valores de control para que pasen.
7. No llamar al LLM real en `pytest -q`.
8. No mostrar información interna en la cotización externa.
9. No agregar funciones postergadas por §0 ni nuevas tras F3.
10. No ofrecer "modo demo" sin modelo real.

## Alcance de la edición (§0)
- Coberturas: solo incendio y sismo.
- IVA: uniforme sobre prima neta total (simplificación ficticia).
- Concurrencia: máximo 1 trabajo de IA por dyno, 1 por caso.
- Trabajos largos en hilo del proceso web (sin worker separado).
- Archivos en Postgres bytea (sin S3).
- Sin PWA, sin HEIC, sin Playwright, sin despliegue automático.
