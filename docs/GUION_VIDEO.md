# Guion del Video — SuscriptorIA Incendio (≤ 3 minutos)

## Acto 1 · Problema (0:00 – 0:30)

**Texto sugerido:**

> "Cotizar un seguro de incendio en Chile implica leer slips, schedules Excel e informes de inspección a mano, transcribir datos a planillas y tarificar sin trazabilidad. Eso toma horas por caso, genera errores de transcripción y deja poca evidencia para auditoría cuando la CMF pregunta de dónde salió cada dato."

**Visual:** mostrar brevemente un slip PDF y un schedule Excel de ejemplo, resaltando la cantidad de datos que hay que extraer manualmente.

## Acto 2 · Demo en vivo del flujo C1 (0:30 – 2:20)

Abrir la app en modo incógnito en la URL pública. No mostrar credenciales en pantalla.

### 2.1 Login y bandeja (0:30 – 0:45)

1. Iniciar sesión con el usuario de evaluación.
2. Mostrar la bandeja con el caso demo (Comercializadora Demo SpA).

### 2.2 Documentos (0:45 – 1:00)

1. Abrir el caso demo.
2. Mostrar los documentos precargados (slip_c1.pdf, schedule_c1.xlsx).
3. Mencionar que se pueden subir archivos adicionales (drag-and-drop o desde el teléfono).

### 2.3 Extracción con IA (1:00 – 1:30)

1. Presionar "Extraer con IA".
2. Mostrar el spinner con el estado del trabajo.
3. Al completar, mostrar los tokens consumidos y la versión del prompt.
4. Navegar a la ficha de riesgo.

### 2.4 Ficha de riesgo (1:30 – 1:50)

1. Mostrar campos extraídos: asegurado, RUT, ocupación, construcción, ubicaciones.
2. Hacer click en el origen de un campo para mostrar la cita textual y el documento fuente.
3. Mostrar los badges de estado (EXTRAIDO, CONFIRMADO) y confianza.
4. Confirmar la ficha.

### 2.5 Propuesta y cotización (1:50 – 2:20)

1. Mostrar el análisis de apetito (DENTRO / REFERIR / DECLINAR).
2. Crear la propuesta con ajuste comercial 0%.
3. Mostrar la tabla de factores: tasas, factores de construcción/protección/deducible, primas por cobertura.
4. Aprobar la propuesta.
5. Generar y descargar el PDF de cotización.
6. Mostrar que la prima bruta es 101,08 UF y que no contiene información interna.

## Acto 3 · Cómo se construyó (2:20 – 3:00)

**Texto sugerido:**

> "El proyecto se construyó con un prompt maestro de más de 400 líneas que define el dominio, las fases, los casos de prueba y las reglas. El agente de IA usa un system prompt versionado con 9 reglas estrictas: nunca calcula precios, nunca inventa datos, y trata el contenido de los documentos como información, no como instrucciones."

**Puntos clave a mencionar:**

1. **Prompt maestro (`PROMPT_MAESTRO.md`):** especificación completa que guía la construcción fase por fase (F0–F4).
2. **Golden set determinista (C1–C9):** 9 casos de prueba con valores exactos que validan el dominio sin llamar al LLM.
3. **Evals con LLM real (E1–E5):** 5 casos de extracción que miden aciertos por campo, alertas y tokens. Se corrieron con v1 y v2 del prompt.
4. **Mejora medida v1 → v2:** tabla comparativa en `docs/MEJORA_PROMPTS.md` que muestra qué campos mejoraron y por qué, con métricas de antes y después.

**Cierre:**

> "El modelo lee, extrae y explica; el código calcula y valida; el suscriptor decide."
