# Eval Report — ENS → ISO 27001:2022 (correspondencia)

**Run ID:** `2026-10-11T15-28-50`
**Modo:** `correspondencia`
**Timestamp:** 2026-10-11T15:49:57.836861+00:00
**Marco:** ens
**Casos evaluados:** 73/73
**Errores:** 0

## Métricas globales

| Métrica | Valor |
|---------|-------|
| Precision (macro avg) | 0.4068 |
| Recall (macro avg) | 0.2205 |
| F1 (macro avg) | 0.2726 |
| Tasa FP total | 0.6349 |
| — Tasa **alucinación** (control inventado) | 0.0000 |
| — Tasa **discrepancia** (control real, mapeo distinto) | 0.6349 |

> **Nota metodológica:** ground truth del SoA del profesor (SoA_TechServ.xlsx) para modo correspondencia; casos ficticios pendientes de revisión del autor para modo hallazgo.
> **Prohibido usar salida IA como ground truth.**
> Alucinación ≠ Discrepancia: un control inventado es cualitativamente peor que un control real con mapeo diferente.

## Comparativa Traductor solo vs Traductor + Validador

| Métrica | Valor |
|---------|-------|
| Casos con validación | 73 |
| Aprobados por Validador | 39 |
| Rechazados por Validador | 34 |
| F1 medio (aprobados) | 0.3615 |
| F1 medio (rechazados) | 0.1706 |
| Precision rechazo @F1<0.5 | 0.8235 |

> Si F1(rechazados) < F1(aprobados), el Validador discrimina correctamente.
> Precision rechazo @F1<0.5: fracción de rechazos donde el Traductor efectivamente se equivocaba (F1 < 0.5).

## Resultados por familia

| Familia | N | Precision | Recall | F1 | FP total | Aluc. | Discr. |
|---------|---|-----------|--------|----|---------:|------:|-------:|
| Continuidad del servicio | 4 | 0.2500 | 0.1250 | 0.1667 | 0.8750 | 0.0000 | 0.8750 |
| Control de acceso | 6 | 0.7500 | 0.4861 | 0.5778 | 0.1818 | 0.0000 | 0.1818 |
| Explotación | 10 | 0.5833 | 0.3000 | 0.3867 | 0.5000 | 0.0000 | 0.5000 |
| Gestión del personal | 4 | 0.1250 | 0.0833 | 0.1000 | 0.8571 | 0.0000 | 0.8571 |
| Marco organizativo | 4 | 0.3750 | 0.1250 | 0.1833 | 0.6667 | 0.0000 | 0.6667 |
| Monitorización del sistema | 3 | 0.6667 | 0.2222 | 0.3333 | 0.3333 | 0.0000 | 0.3333 |
| Planificación | 5 | 0.4400 | 0.2067 | 0.2500 | 0.7000 | 0.0000 | 0.7000 |
| Protección de la información | 6 | 0.2500 | 0.2222 | 0.2333 | 0.7000 | 0.0000 | 0.7000 |
| Protección de las aplicaciones informáticas | 2 | 0.7500 | 0.2083 | 0.3250 | 0.3333 | 0.0000 | 0.3333 |
| Protección de las comunicaciones | 4 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Protección de las instalaciones e infraestructuras | 7 | 0.4524 | 0.4143 | 0.4286 | 0.5000 | 0.0000 | 0.5000 |
| Protección de los equipos | 4 | 0.2500 | 0.1458 | 0.1833 | 0.7143 | 0.0000 | 0.7143 |
| Protección de los servicios | 4 | 0.5000 | 0.1458 | 0.2250 | 0.5000 | 0.0000 | 0.5000 |
| Protección de los soportes de información | 5 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Recursos externos | 4 | 0.5000 | 0.2083 | 0.2917 | 0.6250 | 0.0000 | 0.6250 |
| Servicios en la nube | 1 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 0.0000 | 0.0000 |

## Casos detallados

| Código | Nombre | F1 | P | R | TP | FP | FN | Alucinados | Discrepancias | Perdidos |
|--------|--------|----|---|---|----|----|----|------------|---------------|----------|
| org.2 | Normativa de seguridad (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 6 | — | 5.37 | 5.1, 5.10, 5.36 |
| org.3 | Procedimientos de seguridad (KO) | 0.4000 | 1.0000 | 0.2500 | 1 | 0 | 3 | — | — | 5.14, 5.24, 5.5 |
| org.4 | Proceso de autorización (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 5 | — | 5.31, 5.37 | 5.10, 5.2, 8.19 |
| op.pl.3 | Adquisición de nuevos compon (OK) | 0.2500 | 0.2000 | 0.3333 | 1 | 4 | 2 | — | 5.22, 5.35, 5.37 | 5.19, 5.8 |
| op.acc.3 | Segregación de funciones y t (OK) | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 8.2 |
| op.acc.4 | Proceso de gestión de derech (OK) | 1.0000 | 1.0000 | 1.0000 | 3 | 0 | 0 | — | — | — |
| op.exp.1 | Inventario de activos (OK) | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 5.12 |
| op.exp.2 | Configuración de seguridad (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 5 | 3 | — | 5.35, 5.37, 8.16 | 8.12, 8.19, 8.9 |
| op.exp.5 | Gestión de cambios (KO) | 0.4000 | 0.5000 | 0.3333 | 1 | 1 | 2 | — | 5.37 | 8.29, 8.31 |
| op.exp.9 | Registro de la gestión de in (KO) | 0.3333 | 0.3333 | 0.3333 | 1 | 2 | 2 | — | 5.24, 5.25 | 5.27, 5.28 |
| op.ext.1 | Contratación y acuerdos de n (OK) | 0.6667 | 1.0000 | 0.5000 | 2 | 0 | 2 | — | — | 5.14, 6.6 |
| op.ext.2 | Gestión diaria (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 1 | — | 5.37, 8.16 | 5.22 |
| op.cont.2 | Plan de continuidad (KO) | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 5.30 |
| op.cont.3 | Pruebas periódicas (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 2 | — | 5.36, 8.16 | 5.30, 8.14 |
| op.cont.4 | Medios alternativos (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 4 | 2 | — | 5.22, 5.35, 5.36 | 5.30, 8.14 |
| mp.if.1 | Áreas separadas y con contro (OK) | 0.5000 | 0.6667 | 0.4000 | 2 | 1 | 3 | — | 5.15 | 7.2, 7.3, 7.4 |
| mp.if.2 | Identificación de las person (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.16 | 7.2, 7.4 |
| mp.if.3 | Acondicionamiento de los loc (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 7.6 | 7.12, 7.5, 7.8 |
| mp.if.5 | Protección frente a incendio (KO) | 1.0000 | 1.0000 | 1.0000 | 1 | 0 | 0 | — | — | — |
| mp.if.7 | Registro de entrada y salida (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 8.16 | 7.10, 7.2, 7.9 |
| mp.per.1 | Caracterización del puesto d (OK) | 0.4000 | 0.5000 | 0.3333 | 1 | 1 | 2 | — | 5.37 | 5.2, 6.1 |
| mp.per.3 | Concienciación (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 1 | — | 5.36 | 6.3 |
| mp.per.4 | Formación (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 1 | — | 5.36 | 6.3 |
| mp.com.1 | Perímetro seguro (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 3 | — | 7.1, 7.4 | 8.20, 8.21, 8.22 |
| mp.si.3 | Custodia (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 5.36 | 5.10, 5.9, 7.10 |
| mp.si.4 | Transporte (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 3 | — | 5.36, 5.37 | 5.14, 7.10, 7.9 |
| mp.info.1 | Datos personales (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 3 | — | 5.13, 8.15 | 5.31, 5.34, 8.11 |
| mp.s.1 | Protección del correo electr (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 4 | — | 8.12 | 5.14, 8.23, 8.24 |
| op.acc.5 | Mecanismo de autenticación ( (OK) | 0.8000 | 1.0000 | 0.6667 | 2 | 0 | 1 | — | — | 5.16 |
| mp.com.4 | Separación de flujos de info (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 2 | — | 5.14, 5.37 | 8.20, 8.22 |
| op.acc.6 | Mecanismo de autenticación ( (OK) | 0.6667 | 1.0000 | 0.5000 | 2 | 0 | 2 | — | — | 6.7, 8.1 |
| op.ext.3 | Protección de la cadena de s (OK) | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 5.29, 5.30 |
| mp.eq.2 | Bloqueo de puesto de trabajo (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 2 | — | 6.2, 8.16 | 7.7, 8.1 |
| mp.si.1 | Marcado de soportes (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.35 | 5.13, 7.10 |
| mp.info.2 | Calificación de la informaci (OK) | 1.0000 | 1.0000 | 1.0000 | 2 | 0 | 0 | — | — | — |
| mp.info.5 | Limpieza de documentos (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.31 | 5.14, 8.10 |
| mp.eq.4 | Otros dispositivos conectado (OK) | 0.4000 | 0.5000 | 0.3333 | 1 | 1 | 2 | — | 5.15 | 5.9, 8.20 |
| mp.si.5 | Borrado y destrucción (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 3 | — | 5.37, 8.32 | 7.10, 7.14, 8.10 |
| op.cont.1 | Análisis de impacto (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 8.29 | 5.29, 5.30 |
| op.pl.4 | Dimensionamiento/gestión de  (OK) | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 8.14 |
| mp.if.4 | Energía eléctrica (OK) | 0.5000 | 0.5000 | 0.5000 | 1 | 1 | 1 | — | 7.4 | 7.11 |
| mp.s.4 | Protección frente a denegaci (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 4 | — | 8.21 | 5.30, 8.14, 8.16 |
| mp.info.6 | Copias de seguridad (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 2 | — | 5.35, 8.26 | 8.13, 8.14 |
| op.exp.8 | Registro de la actividad (OK) | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 8.16, 8.17 |
| mp.info.3 | Firma electrónica (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 5.35 | 5.31, 8.24, 8.26 |
| op.acc.1 | Identificación (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 5.37 | 5.16, 5.17, 8.15 |
| mp.info.4 | Sellos de tiempo (OK) | 0.4000 | 0.5000 | 0.3333 | 1 | 1 | 2 | — | 5.37 | 8.24, 8.26 |
| op.exp.10 | Protección de claves criptog (KO) | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 5.17 |
| op.ext.4 | Interconexión de sistemas (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 3 | 4 | — | 5.19, 5.22, 5.36 | 5.14, 8.20, 8.21 |
| mp.per.2 | Deberes y obligaciones (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 3 | 5 | — | 5.31, 5.36, 5.37 | 5.11, 6.2, 6.4 |
| mp.eq.1 | Puesto de trabajo despejado (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 1 | — | 5.37 | 7.7 |
| mp.sw.2 | Aceptación y puesta en servi (OK) | 0.4000 | 1.0000 | 0.2500 | 1 | 0 | 3 | — | — | 8.11, 8.31, 8.33 |
| mp.s.3 | Protección de la navegación  (KO) | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 8.16, 8.7 |
| op.acc.2 | Requisitos de acceso (OK) | 0.3333 | 0.5000 | 0.2500 | 1 | 1 | 3 | — | 5.18 | 8.18, 8.3, 8.4 |
| mp.si.2 | Criptografía (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 8.29 | 7.10, 8.12, 8.24 |
| op.exp.4 | Mantenimiento y actualizacio (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 8.32 | 7.13, 8.31, 8.8 |
| op.nub.1 | Protección de servicios en l (KO) | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 5.19 |
| op.mon.1 | Detección de intrusión (KO) | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 8.15, 8.20 |
| op.mon.2 | Sistema de métricas (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 1 | — | 5.37 | 5.36 |
| mp.eq.3 | Protección de dispositivos p (OK) | 0.3333 | 0.5000 | 0.2500 | 1 | 1 | 3 | — | 5.37 | 6.7, 7.9, 8.24 |
| op.exp.3 | Gestión de la configuración  (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 5.37 | 8.13, 8.32, 8.9 |
| op.exp.7 | Gestión de incidentes (OK) | 0.8000 | 1.0000 | 0.6667 | 4 | 0 | 2 | — | — | 5.27, 5.28 |
| mp.com.2 | Protección de la confidencia (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 3 | — | 5.34, 8.3 | 5.14, 8.20, 8.24 |
| op.pl.2 | Arquitectura de Seguridad (KO) | 0.3333 | 1.0000 | 0.2000 | 1 | 0 | 4 | — | — | 5.9, 8.20, 8.22 |
| op.exp.6 | Protección frente a código d (OK) | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 8.16, 8.19 |
| mp.sw.1 | Desarrollo de aplicaciones (OK) | 0.2500 | 0.5000 | 0.1667 | 1 | 1 | 5 | — | 8.29 | 8.25, 8.27, 8.28 |
| op.pl.1 | Análisis de riesgos (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 1 | — | 5.25, 5.35 | 5.7 |
| mp.s.2 | Protección de servicios y ap (OK) | 0.4000 | 1.0000 | 0.2500 | 1 | 0 | 3 | — | — | 8.25, 8.29, 8.8 |
| mp.com.3 | Protección de la integridad  (OK) | 0.0000 | 0.0000 | 0.0000 | 0 | 5 | 3 | — | 5.35, 5.37, 8.26 | 6.7, 8.20, 8.24 |
| op.mon.3 | Vigilancia (OK) | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 5.7, 8.8 |
| org.1 | Política de seguridad (KO) | 0.3333 | 0.5000 | 0.2500 | 1 | 1 | 3 | — | 5.36 | 5.2, 5.31, 5.4 |
| op.pl.5 | Componentes certificados (KO) | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.36 | 5.21, 8.9 |
| mp.if.6 | Protección frente a inundaci (OK) | 1.0000 | 1.0000 | 1.0000 | 1 | 0 | 0 | — | — | — |
