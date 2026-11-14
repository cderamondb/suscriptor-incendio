# Ficha de Negocio — SuscriptorIA Incendio

## Cliente

Aseguradoras medianas del mercado chileno con cartera de incendio y property comercial, y corredores de reaseguro que precotizan riesgos. El usuario directo es el suscriptor (senior y junior); el comprador es la gerencia técnica.

## Problema

Armar una cotización de incendio exige leer a mano slips, schedules Excel e informes de inspección, transcribir datos a planillas y tarificar sin trazabilidad. Eso significa horas por caso, errores de transcripción y poca evidencia para auditoría (CMF) cuando se pregunta de dónde salió cada dato.

## Solución

Copiloto que extrae la ficha de riesgo con cita verificada por dato, tarifica de forma determinista con el tarifario de la compañía, controla apetito y facultades, y emite la cotización en PDF.

## Rol de la IA

Leer, extraer, clasificar la ocupación y explicar. La IA **no** calcula precios ni aprueba propuestas. Ningún dato extraído entra al cálculo de la prima sin confirmación humana.

## Propuesta de valor medible

| Métrica | Sin copiloto | Con SuscriptorIA |
|---|---|---|
| Tiempo por cotización | ~2-4 horas | ~15-30 minutos |
| Datos sin fuente en la ficha | Frecuentes | Cero (cada campo con origen) |
| Trazabilidad para auditoría | Parcial (planillas) | Completa (documento, página, cita) |

## Modelo de ingresos

**Opción seleccionada: SaaS por suscriptor al mes** con un mínimo de usuarios por compañía.

- Tarifa mensual por suscriptor activo (hipótesis: USD 150-300/mes).
- Implementación inicial cobrada aparte: carga del tarifario y reglas de la compañía.
- Tramos de volumen para compañías con más de 10 suscriptores.

Alternativa evaluada: cobro por caso cotizado con tramos de volumen.

## Costo mensual estimado de operación

Precios consultados en noviembre 2026. Todos los montos en USD.

### Infraestructura Heroku

| Componente | Plan | Costo mensual |
|---|---|---|
| Dyno web | Basic | USD 7 |
| Heroku Postgres | Mini | USD 5 |
| **Subtotal infraestructura** | | **USD 12** |

Fuente: [Heroku Pricing](https://www.heroku.com/pricing), noviembre 2026.

### Costo LLM por caso (Anthropic API directa)

Modelo utilizado: Claude (API directa de Anthropic, plan B activado).

Estimación basada en un caso típico de extracción (1 slip PDF + 1 schedule Excel):

| Concepto | Tokens estimados | Precio/1M tokens | Costo |
|---|---|---|---|
| Entrada (documentos + prompt + herramientas) | ~15.000 | USD 3,00 | USD 0,045 |
| Salida (ficha extraída + llamadas a herramientas) | ~5.000 | USD 15,00 | USD 0,075 |
| **Total por caso** | ~20.000 | | **~USD 0,12** |

Nota: precios de Claude Sonnet 4.6 (modelo configurado actualmente). Los tokens reales se miden en las evals y se actualizan en `docs/MEJORA_PROMPTS.md`.

### Proyección mensual

| Escenario | Casos/mes | Costo LLM | Infraestructura | Total |
|---|---|---|---|---|
| Bajo (1 suscriptor) | 50 | USD 6 | USD 12 | USD 18 |
| Medio (5 suscriptores) | 250 | USD 30 | USD 12 | USD 42 |
| Alto (20 suscriptores) | 1.000 | USD 120 | USD 12 | USD 132 |

### Control de costos

- **Tope en código:** `MAX_TOKENS_POR_CASO` y `MAX_TOKENS_DIA` configurables por variable de entorno.
- **Límite del proveedor:** configurable en console.anthropic.com (plan B activo).
- Heroku Managed Inference no ofrece un hard cap nativo confirmado (documentado en Supuestos del README).
