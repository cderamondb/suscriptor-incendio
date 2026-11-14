# Changelog de System Prompts

## v2 (2026-11-14)

Cambios respecto a v1, basados en los resultados de evals v1 (0/51 campos, 0/2 alertas):

### Problema detectado
El modelo no usaba las herramientas disponibles. Con v1, el agente respondía en texto plano sin llamar a `listar_documentos` ni `leer_documento`, resultando en fichas completamente vacías.

### Cambios aplicados
1. **Procedimiento obligatorio paso a paso**: se agregó una sección "Procedimiento obligatorio" con 5 pasos numerados que el modelo debe seguir EN ORDEN (listar → leer → registrar → alertas → clasificar).
2. **Nombres de campos explícitos**: se listaron todos los nombres de campo que el modelo debe usar con `registrar_dato` (razon_social, rut, ubicaciones[N].direccion, etc.).
3. **Regla "SIEMPRE usa las herramientas"**: se agregó como regla #1 la instrucción explícita de no responder sin haber llamado primero a las herramientas de lectura.
4. **Tipos de alerta enumerados**: se listaron los 4 tipos de alerta esperados (CONTRADICCION, DATO_FALTANTE, PROMPT_INJECTION, CONTENIDO_SOSPECHOSO) con descripción de cuándo usarlos.
5. **Niveles de confianza definidos**: se especificó cuándo usar ALTA, MEDIA o BAJA en el campo confianza de `registrar_dato`.

### Resultado esperado
Con estos cambios, el modelo debería:
- Usar herramientas en cada caso (no responder en texto plano)
- Extraer datos de los documentos y registrarlos con `registrar_dato`
- Detectar contradicciones entre documentos
- Detectar y alertar intentos de prompt injection

## v1 (2026-10-15)

Versión inicial. Prompt conciso de 9 reglas generales sin procedimiento paso a paso.

### Debilidades identificadas en evals
- No forzaba el uso de herramientas
- El modelo respondía sin leer documentos
- Nombres de campos y tipos de alerta no estaban documentados explícitamente
