# Eval Report — ENS → ISO 27001:2022 (correspondencia)

**Run ID:** `2026-10-04T22-25-31`
**Modo:** `correspondencia`
**Timestamp:** 2026-10-04T22:28:41.381461+00:00
**Marco:** ens
**Casos evaluados:** 10/10
**Errores:** 0

## Métricas globales

| Métrica | Valor |
|---------|-------|
| Precision (macro avg) | 0.4400 |
| Recall (macro avg) | 0.2917 |
| F1 (macro avg) | 0.3267 |
| Tasa FP total | 0.6522 |
| — Tasa **alucinación** (control inventado) | 0.0000 |
| — Tasa **discrepancia** (control real, mapeo distinto) | 0.6522 |

> **Nota metodológica:** ground truth del SoA del profesor (SoA_TechServ.xlsx) para modo correspondencia; casos ficticios pendientes de revisión del autor para modo hallazgo.
> **Prohibido usar salida IA como ground truth.**
> Alucinación ≠ Discrepancia: un control inventado es cualitativamente peor que un control real con mapeo diferente.

## Comparativa Traductor solo vs Traductor + Validador

| Métrica | Valor |
|---------|-------|
| Casos con validación | 10 |
| Aprobados por Validador | 7 |
| Rechazados por Validador | 3 |
| F1 medio (aprobados) | 0.3524 |
| F1 medio (rechazados) | 0.2667 |
| Precision rechazo @F1<0.5 | 1.0 |

> Si F1(rechazados) < F1(aprobados), el Validador discrimina correctamente.
> Precision rechazo @F1<0.5: fracción de rechazos donde el Traductor efectivamente se equivocaba (F1 < 0.5).

## Resultados por familia

| Familia | N | Precision | Recall | F1 | FP total | Aluc. | Discr. |
|---------|---|-----------|--------|----|---------:|------:|-------:|
| Control de acceso | 2 | 1.0000 | 0.5834 | 0.7333 | 0.0000 | 0.0000 | 0.0000 |
| Explotación | 4 | 0.3000 | 0.2916 | 0.2875 | 0.7000 | 0.0000 | 0.7000 |
| Marco organizativo | 3 | 0.3333 | 0.0833 | 0.1333 | 0.8000 | 0.0000 | 0.8000 |
| Planificación | 1 | 0.2000 | 0.3333 | 0.2500 | 0.8000 | 0.0000 | 0.8000 |

## Casos detallados

| Código | Nombre | F1 | P | R | TP | FP | FN | Alucinados | Discrepancias | Perdidos |
|--------|--------|----|---|---|----|----|----|------------|---------------|----------|
| org.2 | Normativa de seguridad (✓) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 6 | — | 5.35, 5.37 | 5.1, 5.10, 5.36 |
| org.3 | Procedimientos de seguridad (✗) | 0.4000 | 1.0000 | 0.2500 | 1 | 0 | 3 | — | — | 5.14, 5.24, 5.5 |
| org.4 | Proceso de autorización (✓) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 5 | — | 5.31, 5.37 | 5.10, 5.2, 8.19 |
| op.pl.3 | Adquisición de nuevos compon (✓) | 0.2500 | 0.2000 | 0.3333 | 1 | 4 | 2 | — | 5.22, 5.35, 5.37 | 5.19, 5.8 |
| op.acc.3 | Segregación de funciones y t (✓) | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 8.2 |
| op.acc.4 | Proceso de gestión de derech (✓) | 0.8000 | 1.0000 | 0.6667 | 2 | 0 | 1 | — | — | 8.2 |
| op.exp.1 | Inventario de activos (✓) | 0.5000 | 0.5000 | 0.5000 | 1 | 1 | 1 | — | 5.37 | 5.12 |
| op.exp.2 | Configuración de seguridad (✗) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 5.37 | 8.12, 8.19, 8.9 |
| op.exp.5 | Gestión de cambios (✗) | 0.4000 | 0.5000 | 0.3333 | 1 | 1 | 2 | — | 5.37 | 8.29, 8.31 |
| op.exp.9 | Registro de la gestión de in (✓) | 0.2500 | 0.2000 | 0.3333 | 1 | 4 | 2 | — | 5.24, 5.25, 5.37 | 5.27, 5.28 |
