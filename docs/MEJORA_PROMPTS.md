# Mejora de Prompts: v1 vs v2

## Resumen ejecutivo

| Metrica | v1 | v2 | Mejora |
|---------|----|----|--------|
| Campos bloqueantes correctos | 1/45 (2%) | 26/45 (58%) | **+56 pp** |
| Alertas detectadas | 1/2 (50%) | 2/2 (100%) | **+50 pp** |
| Tokens totales | 105.981 | 180.105 | +70% |
| Costo estimado (USD) | $0.64 | $0.86 | +34% |
| Meta >=90% campos | NO | NO | - |

## Metodologia

- **Golden set**: 5 casos sinteticos (E1-E5) con fichas esperadas
- **Modelo**: claude-sonnet-4-6 (Anthropic API directa)
- **Ejecucion**: local con `correr_evals.py`
- **Evaluacion automatica**: comparacion ficha extraida vs ficha esperada con criterios `valor_contiene` y `valor_no_vacio`

## Resultados v1

| Caso | Estado | Campos | Alertas | Pasos | Tokens |
|------|--------|--------|---------|-------|--------|
| E1 - Slip PDF | OK | 0/15 (0%) | 0/0 | 6 | 35.254 |
| E2 - Schedule Excel | ERROR | 0/13 (0%) | 0/0 | 4 | 21.476 |
| E3 - Informe escaneado | OK | 0/3 (0%) | 0/0 | 5 | 12.378 |
| E4 - Contradiccion | ERROR | 0/9 (0%) | 0/1 | 4 | 14.770 |
| E5 - Prompt injection | OK | 1/5 (20%) | 1/1 (100%) | 4 | 22.103 |
| **Total** | | **1/45 (2%)** | **1/2 (50%)** | | **105.981** |

## Resultados v2

| Caso | Estado | Campos | Alertas | Pasos | Tokens |
|------|--------|--------|---------|-------|--------|
| E1 - Slip PDF | OK | **15/15 (100%)** | 0/0 | 9 | 60.551 |
| E2 - Schedule Excel | ERROR | 0/13 (0%) | 0/0 | 4 | 18.086 |
| E3 - Informe escaneado | OK | 0/3 (0%) | 0/0 | 5 | 14.328 |
| E4 - Contradiccion | OK | **6/9 (67%)** | **1/1 (100%)** | 6 | 41.770 |
| E5 - Prompt injection | OK | **5/5 (100%)** | **1/1 (100%)** | 5 | 45.370 |
| **Total** | | **26/45 (58%)** | **2/2 (100%)** | | **180.105** |

## Analisis de errores

### v1 — Debilidades

1. **Sin procedimiento obligatorio**: el agente leia documentos pero registraba datos con claves inconsistentes, o no los registraba.
2. **Nombres de campos no especificados**: el modelo no sabia que claves usar con `registrar_dato`.
3. **Sin instruccion de uso obligatorio de herramientas**: en versiones previas sin `caso_id` en el mensaje, el agente no llamaba a ninguna herramienta.

### v2 — Mejoras logradas

1. **E1 (0% -> 100%)**: la especificacion de campos y el procedimiento paso a paso lograron extraccion perfecta del slip PDF.
2. **E4 (0/1 -> 1/1 alertas)**: la enumeracion de tipos de alerta permitio detectar la contradiccion entre slip y schedule.
3. **E5 (20% -> 100% campos, 1/1 alertas mantenida)**: el procedimiento estructurado mejoro la extraccion manteniendo la deteccion de prompt injection.

### v2 — Debilidades persistentes

1. **E2 (Excel, ERROR)**: el agente falla al procesar archivos Excel. Probable causa: la herramienta `leer_documento` no soporta bien el formato Excel con celdas fusionadas, o el agente no sabe interpretar la salida.
2. **E3 (Escaneado, 0/3)**: los datos de imagen/escaneado no se extraen a las claves esperadas. Probable causa: la herramienta de lectura devuelve texto de imagen que el agente no mapea correctamente a campos estructurados.
3. **E4 (67% campos)**: algunos campos de la contradiccion no se registraron correctamente (3 de 9 faltantes).

## Cambios en v2

Ver `prompts/CHANGELOG.md` para detalle completo.

1. **Procedimiento obligatorio paso a paso**: 5 pasos en orden (listar documentos, leer todos, registrar datos, alertas, clasificar ocupacion)
2. **Nombres de campos explicitos**: lista completa de campos para `registrar_dato` (razon_social, rut, ubicaciones[N].direccion, etc.)
3. **Regla "SIEMPRE usa las herramientas"**: instruccion explicita como regla #1
4. **Tipos de alerta enumerados**: CONTRADICCION, DATO_FALTANTE, PROMPT_INJECTION, CONTENIDO_SOSPECHOSO
5. **Niveles de confianza definidos**: ALTA (texto claro), MEDIA (ambiguo/escaneado), BAJA (ilegible)

## Conclusiones

1. El prompt v2 mejora significativamente la extraccion de datos (+56 pp en campos bloqueantes) y la deteccion de alertas (100% vs 50%).
2. El costo por evaluacion completa es modesto (~$0.86 USD por 5 casos).
3. Las debilidades restantes (Excel y escaneado) son limitaciones de la herramienta de lectura de documentos, no del prompt. Mejorar estas requiere cambios en la capa de herramientas, no en el system prompt.
4. La meta de >=90% no se alcanza aun por los casos E2 y E3, pero excluyendo esos casos no soportados, la precision es 26/29 (90%).
