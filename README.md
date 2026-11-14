# SuscriptorIA Incendio

Copiloto de suscripción y tarificación de seguros de incendio para el mercado chileno.

## Idea de negocio

**Cliente:** aseguradoras medianas del mercado chileno con cartera de incendio y property comercial, y corredores de reaseguro que precotizan riesgos. El usuario es el suscriptor (senior y junior); el comprador es la gerencia técnica.

**Problema:** armar una cotización de incendio exige leer a mano slips, schedules Excel e informes de inspección, transcribir datos a planillas y tarificar sin trazabilidad. Eso significa horas por caso, errores de transcripción y poca evidencia para auditoría (CMF) cuando se pregunta de dónde salió cada dato.

**Solución:** copiloto que extrae la ficha de riesgo con cita verificada por dato, tarifica de forma determinista con el tarifario de la compañía, controla apetito y facultades, y emite la cotización en PDF.

**Rol de la IA:** leer, extraer, clasificar la ocupación y explicar. La IA **no** calcula precios ni aprueba propuestas.

**Propuesta de valor:** menos tiempo por cotización, cero datos sin fuente en la ficha y trazabilidad completa para auditoría.

## Cómo usar la app

1. Abrir la URL pública en modo incógnito.
2. Iniciar sesión con las credenciales del usuario de evaluación (proporcionadas en la plataforma del curso, no en este repositorio).
3. Abrir el caso demo precargado desde la bandeja.
4. En la pestaña **Documentos**, verificar los archivos cargados y presionar **Extraer con IA**.
5. Una vez completada la extracción, revisar la **Ficha** de riesgo: cada campo muestra su valor, estado de confianza y origen (documento, página/celda, cita textual). Corregir si es necesario y confirmar.
6. En la pestaña **Propuesta**, revisar el análisis de apetito, ajustar el porcentaje comercial si corresponde, y aprobar o rechazar la propuesta.
7. Generar la cotización en PDF.

### Roles y facultades

| Rol | Suma asegurada máx. | Ajuste comercial | Aprueba REFERIR |
|---|---|---|---|
| SUSCRIPTOR | 200.000 UF | ±15 % | No |
| SUSCRIPTOR_SENIOR | 1.000.000 UF | ±25 % | Sí |
| Fuera de ambos | — | — | COMITE |

## Arquitectura

```
┌─────────────┐     ┌──────────────────────────────────────────────┐
│  Frontend   │     │  Backend (FastAPI)                           │
│  React 18   │────▶│  ┌────────┐  ┌──────────┐  ┌────────────┐  │
│  Vite 5     │     │  │ api/   │──│ dominio/ │  │  agente/   │  │
│  Tailwind 3 │     │  │        │  │ (tarifa, │  │ (LLM +     │  │
│             │     │  │        │  │  apetito, │  │  tools)    │  │
│             │     │  │        │  │  estados) │  │            │  │
│             │◀────│  │        │  └──────────┘  └────────────┘  │
└─────────────┘     │  │        │  ┌──────────┐  ┌────────────┐  │
                    │  │        │──│ ingesta/ │  │persistencia│  │
                    │  └────────┘  │ (PDF,    │  │ (Postgres) │  │
                    │              │  Excel,  │  └────────────┘  │
                    │              │  imagen) │                   │
                    │              └──────────┘                   │
                    └──────────────────────────────────────────────┘
```

### Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (psycopg v3)
- **Frontend:** React 18, TypeScript, Vite 5, Tailwind CSS 3
- **Base de datos:** PostgreSQL 16
- **IA:** Anthropic Claude (API directa) con herramientas y visión
- **Infraestructura:** Docker, Heroku (dyno web + Heroku Postgres)
- **CI:** GitHub Actions (ruff, mypy, pytest, eslint, vitest, docker build)

### Principio rector

> El modelo lee, extrae y explica; el código calcula y valida; el suscriptor decide.

Ningún dato extraído por la IA entra al cálculo de la prima sin confirmación humana, y ninguna prima la calcula el LLM.

### Capas del backend

| Capa | Responsabilidad | Restricciones |
|---|---|---|
| `dominio/` | Tarifa, apetito, facultades, estados, modelos | Solo stdlib + Pydantic. Sin IO, sin LLM, sin BD |
| `ingesta/` | Lectura de PDF (texto y escaneado), Excel, imágenes | Sin LLM |
| `agente/` | Orquesta el LLM con herramientas; llama a `dominio/` | Nunca calcula |
| `api/` | Endpoints REST, autenticación, trabajos | Sin lógica de negocio |
| `persistencia/` | Modelos DB, CRUD, sesión SQLAlchemy | |
| `cotizacion/` | Generación del PDF de cotización | |

### Montos y aritmética

Todos los montos usan `decimal.Decimal` con redondeo `ROUND_HALF_UP`. Nunca `float`. El frontend no calcula: solo muestra lo que entrega la API, formateado en es-CL (1.234,56).

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
```

## Supuestos

1. **IVA simplificado:** el IVA de 19 % se aplica sobre la prima neta total (incendio + sismo) como simplificación del modelo ficticio. Esta no es una validación tributaria para uso real.
2. **Datos ficticios:** todos los datos del repositorio (tarifario, cartera, fixtures, documentos de prueba) son sintéticos. No hay datos reales de asegurados, corredores ni pólizas.
3. **Concurrencia:** máximo 1 trabajo de IA por dyno, 1 por caso. Los trabajos largos corren en un hilo del proceso web (sin worker separado).
4. **Archivos:** almacenados en PostgreSQL (`bytea`), sin S3 ni almacenamiento externo.
5. **Límite de gasto del proveedor:** Heroku Managed Inference no ofrece un hard cap nativo confirmado. El control principal de costos es el tope en código (`MAX_TOKENS_POR_CASO` y `MAX_TOKENS_DIA`). Al usar Anthropic directamente, se puede configurar un límite en console.anthropic.com.
6. **Autenticación:** sesión con cookie HttpOnly + SameSite=Lax. Sin proveedor de inicio de sesión corporativo.

## Fase posterior

Funcionalidades postergadas que no se construyen en esta edición:

- **Playwright:** tests end-to-end automatizados con Playwright.
- **PWA:** Progressive Web App instalable con caché offline.
- **HEIC:** soporte para imágenes HEIC (actualmente retorna `ArchivoNoSoportado` 415).
- **S3/MinIO:** almacenamiento externo de archivos (actualmente en Postgres `bytea`).
- **Worker separado:** proceso dedicado para trabajos en segundo plano.
- **Apps staging/producción separadas:** actualmente una sola app Heroku.
- **Despliegue automático desde CI:** actualmente se despliega manualmente con `git push heroku main`.
- **Administración de usuarios desde la UI:** actualmente los usuarios se crean por seed.
- **Evals de 10 casos:** ampliación del golden set de 5 a 10 casos de evaluación.
- **Reintentos avanzados y comparables con UI propia.**

## Estructura del repositorio

```
suscriptor-incendio/
├── PROMPT_MAESTRO.md              # especificación completa del proyecto
├── CLAUDE.md                      # contexto para Claude Code
├── README.md                      # este archivo
├── .env.example                   # variables de entorno (sin secretos)
├── docker-compose.yml
├── heroku.yml
├── Dockerfile
├── prompts/                       # system prompts versionados
│   ├── suscriptor_v1.md
│   ├── suscriptor_v2.md
│   └── CHANGELOG.md
├── docs/
│   ├── MEJORA_PROMPTS.md          # comparación medida v1 → v2
│   ├── FICHA_NEGOCIO.md           # modelo de negocio y costos
│   ├── GUION_VIDEO.md             # guion del video de presentación
│   └── evidencia/                 # capturas y evidencia
├── datos/ejemplo/                 # tarifario y cartera ficticios
├── backend/
│   ├── app/
│   │   ├── dominio/               # lógica pura: tarifa, apetito, facultades
│   │   ├── ingesta/               # lectura de PDF, Excel, imágenes
│   │   ├── agente/                # orquestación LLM con herramientas
│   │   ├── api/                   # endpoints FastAPI
│   │   ├── persistencia/          # modelos DB y CRUD
│   │   ├── cotizacion/            # generador de PDF
│   │   └── trabajos/              # cola de trabajos en segundo plano
│   └── tests/
│       ├── fixtures/              # documentos sintéticos
│       └── evals/                 # golden set con LLM real
└── frontend/
    └── src/
        ├── paginas/               # 5 pantallas React
        ├── componentes/           # componentes reutilizables
        └── api/                   # cliente HTTP tipado
```

## Licencia

Proyecto académico — Curso de Prompt Engineering.
