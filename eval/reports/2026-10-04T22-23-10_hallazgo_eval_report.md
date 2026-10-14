# Eval Report — Hallazgos técnicos → ISO 27001:2022

**Run ID:** `2026-10-04T22-23-10`
**Modo:** `hallazgo`
**Timestamp:** 2026-10-04T22:25:24.712914+00:00
**Marco:** ens
**Casos evaluados:** 16/16
**Errores:** 0

## Métricas globales

| Métrica | Valor |
|---------|-------|
| Precision (macro avg) | 0.3125 |
| Recall (macro avg) | 0.2812 |
| F1 (macro avg) | 0.2813 |
| Tasa FP total | 0.7568 |
| — Tasa **alucinación** (control inventado) | 0.0000 |
| — Tasa **discrepancia** (control real, mapeo distinto) | 0.7568 |

> **Nota metodológica:** ground truth del SoA del profesor (SoA_TechServ.xlsx) para modo correspondencia; casos ficticios pendientes de revisión del autor para modo hallazgo.
> **Prohibido usar salida IA como ground truth.**
> Alucinación ≠ Discrepancia: un control inventado es cualitativamente peor que un control real con mapeo diferente.

## Resultados por familia

| Familia | N | Precision | Recall | F1 | FP total | Aluc. | Discr. |
|---------|---|-----------|--------|----|---------:|------:|-------:|
| Continuidad del servicio | 1 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 0.0000 | 0.0000 |
| Control de acceso | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Explotación | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Gestión del personal | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Marco organizativo | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Monitorización del sistema | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Planificación | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Protección de la información | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Protección de las aplicaciones informáticas | 1 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 0.0000 | 0.0000 |
| Protección de las comunicaciones | 1 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.0000 | 0.5000 |
| Protección de las instalaciones e infraestructuras | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Protección de los equipos | 1 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| Protección de los servicios | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Protección de los soportes de información | 1 | 0.5000 | 1.0000 | 0.6667 | 0.5000 | 0.0000 | 0.5000 |
| Recursos externos | 1 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| Servicios en la nube | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |

## Casos detallados

| Código | Nombre | F1 | P | R | TP | FP | FN | Alucinados | Discrepancias | Perdidos |
|--------|--------|----|---|---|----|----|----|------------|---------------|----------|
| HT-01 | Sin prueba de restauración d | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 5.30 |
| HT-02 | Cuenta de administrador sin  | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 8.5 | 5.17, 8.2 |
| HT-03 | Servidor web con CVE-2024-21 | 0.0000 | 0.0000 | 0.0000 | 0 | 3 | 1 | — | 5.15, 8.2, 8.21 | 8.8 |
| HT-04 | Cuenta de empleado dado de b | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 2 | — | 5.21, 8.10 | 5.11, 6.5 |
| HT-05 | Sin política de seguridad de | 0.0000 | 0.0000 | 0.0000 | 0 | 4 | 2 | — | 5.19, 5.20, 5.35 | 5.1, 5.36 |
| HT-06 | Sin sistema de logs centrali | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 6.8 | 8.15, 8.16 |
| HT-07 | Sin registro de riesgos actu | 0.0000 | 0.0000 | 0.0000 | 0 | 3 | 2 | — | 5.21, 5.25, 5.35 | 5.7, 5.8 |
| HT-08 | PII de clientes visible en l | 0.0000 | 0.0000 | 0.0000 | 0 | 3 | 2 | — | 5.33, 8.10, 8.12 | 5.34, 8.11 |
| HT-09 | Inyección SQL confirmada en  | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 8.25 |
| HT-10 | Telnet habilitado en switch  | 0.5000 | 0.5000 | 0.5000 | 1 | 1 | 1 | — | 8.21 | 8.26 |
| HT-11 | Acceso a sala de servidores  | 0.0000 | 0.0000 | 0.0000 | 0 | 4 | 2 | — | 5.15, 7.10, 8.2 | 7.2, 7.4 |
| HT-12 | Portátil corporativo sin cif | 1.0000 | 1.0000 | 1.0000 | 2 | 0 | 0 | — | — | — |
| HT-13 | API REST pública sin control | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 2 | — | 5.26, 8.5 | 5.14, 8.21 |
| HT-14 | Pen drive con datos de clien | 0.6667 | 0.5000 | 1.0000 | 2 | 2 | 0 | — | 5.21, 8.12 | — |
| HT-15 | Proveedor externo con acceso | 1.0000 | 1.0000 | 1.0000 | 2 | 0 | 0 | — | — | — |
| HT-16 | Bucket S3 de AWS con datos d | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 1 | — | 5.20, 6.6 | 5.23 |
