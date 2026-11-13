# Reporte LLM — Fase F0

Fecha de consulta: 2026-11-12

## Heroku Managed Inference and Agents — Hallazgos

### Modelos disponibles
Heroku ofrece múltiples modelos Claude a través del add-on Managed Inference:
- Claude Sonnet 4.6, Claude 4 Sonnet, Claude 4.5 Sonnet
- Claude 4.5 Haiku, Claude Haiku 5.5
- Claude Opus 4.5, Opus 4.7, Opus 4.8, Opus 5.5
- Claude Sonnet 5.5

Fuente: [Heroku Changelog](https://devcenter.heroku.com/changelog-items/3603), [Heroku Inference API](https://devcenter.heroku.com/articles/heroku-inference-api)

### API
- **Chat Completions:** endpoint `/v1/chat/completions` compatible con OpenAI.
- **Messages API (preview):** formato nativo de Anthropic (`/v1/messages`), compatible con el SDK de Anthropic. Se configura con `base_url` apuntando a la URL de Heroku Inference y `x-api-key` con `INFERENCE_KEY`.
- **Herramientas (tools):** soportadas en ambos formatos. En Chat Completions acepta `tool_choice: auto | required`. En Messages API, se espera compatibilidad con el formato nativo de Anthropic (`tool_use`, `tool_choice`).

Fuente: [Heroku Inference API v1 Chat Completions](https://devcenter.heroku.com/articles/heroku-inference-api-v1-chat-completions), [Blog Messages API](https://www.heroku.com/blog/accelerating-ai-dev-new-models-performance-improvements-messages-api/)

### Visión (imágenes)
- **Soportada** desde el 30 de enero de 2026 para modelos Claude, Nova y Cohere.
- Los modelos Claude listan "Supported inputs: text, image".
- Las imágenes se envían como parte del array `content` mezclando texto e imagen.

Fuente: [Heroku Changelog — Multimodal](https://devcenter.heroku.com/changelog-items/3581)

### Facturación
- **Modelo de cobro:** por tokens consumidos (metered billing). Ejemplo: Claude 4 Sonnet a $3.00/1M tokens entrada, $15.00/1M tokens salida (verificar precios vigentes al momento del despliegue).
- **Límite de gasto configurable:** No encontré evidencia de un hard cap o budget alert nativo en Heroku para Managed Inference. La facturación es retroactiva (el cobro del mes actual llega en el mes siguiente).

Fuente: [Heroku Usage & Billing](https://devcenter.heroku.com/articles/usage-and-billing), [Heroku Elements — Inference Add-on](https://elements.heroku.com/addons/heroku-inference)

### Rate limits (por modelo)
- Opus 4.7: 50 req/min, 300.000 tokens/min
- Haiku 5.5: 200 req/min, 800.000 tokens/min

## Decisión: Plan A vs Plan B

### Evaluación

| Criterio | Plan A (Heroku Managed Inference) | Plan B (API directa Anthropic) |
|---|---|---|
| Herramientas (tools) | Sí, en ambos formatos de API | Sí, nativo |
| Visión (imágenes) | Sí, desde ene-2026 | Sí |
| Límite de gasto en consola | **No confirmado** — no hay hard cap nativo | **Sí** — configurable en console.anthropic.com |
| Datos ficticios solamente | Aplica a ambos en esta edición | Aplica a ambos en esta edición |
| Integración con Heroku | Nativa (add-on, config vars automáticas) | Manual (ANTHROPIC_API_KEY como config var) |
| SDK compatible | Sí, con Messages API preview + SDK Anthropic | Sí, SDK Anthropic directo |

### Decisión recomendada: **Plan A con control de presupuesto en código**

**Justificación:**
1. Heroku Managed Inference soporta los tres requisitos críticos: herramientas, visión e imágenes.
2. La Messages API preview permite usar el SDK nativo de Anthropic, lo que hace que el cambio a plan B sea trivial (solo cambiar `base_url`).
3. La ausencia de un hard cap en Heroku se mitiga con el control de presupuesto en código (`MAX_TOKENS_POR_CASO` y `MAX_TOKENS_DIA` en §7.1), que es obligatorio independientemente del proveedor.
4. Como respaldo adicional, se documentará en "Supuestos" que Heroku no ofrece un límite de gasto nativo confirmado y que el tope en código es el control principal.

### Verificación pendiente en el despliegue
- [ ] Confirmar que el add-on provee `INFERENCE_URL`, `INFERENCE_KEY` e `INFERENCE_MODEL_ID` como config vars.
- [ ] Probar una llamada con herramientas y una con imagen al modelo real.
- [ ] Verificar si la Messages API acepta `tool_choice: auto` y extended thinking.
- [ ] Consultar los precios vigentes por token del modelo elegido y actualizar `PRECIO_TOKEN_*`.
- [ ] Buscar si existe alguna opción de alertas de billing en el dashboard de Heroku.
- [ ] Captura de la configuración en `docs/evidencia/` si existe algún control de gasto.

### Plan B: cuándo activar
Activar plan B solo si en el despliegue se confirma que:
- La Messages API no soporta `tool_use` o `tool_choice` en Heroku, o
- La visión no funciona correctamente, o
- No es posible seleccionar un modelo con capacidad de herramientas.

En ese caso, se cambia `PROVEEDOR_LLM=anthropic` y se configura `ANTHROPIC_API_KEY` y el límite de gasto en console.anthropic.com. Solo se usan datos ficticios (§0.3).
