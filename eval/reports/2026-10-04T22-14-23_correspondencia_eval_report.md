# Eval Report — ENS → ISO 27001:2022 (correspondencia)

**Run ID:** `2026-10-04T22-14-23`
**Modo:** `correspondencia`
**Timestamp:** 2026-10-04T22:22:54.856308+00:00
**Marco:** ens
**Casos evaluados:** 73/73
**Errores:** 0

## Métricas globales

| Métrica | Valor |
|---------|-------|
| Precision (macro avg) | 0.4078 |
| Recall (macro avg) | 0.2164 |
| F1 (macro avg) | 0.2648 |
| Tasa FP total | 0.6250 |
| — Tasa **alucinación** (control inventado) | 0.0000 |
| — Tasa **discrepancia** (control real, mapeo distinto) | 0.6250 |

> **Nota metodológica:** ground truth del SoA del profesor (SoA_TechServ.xlsx) para modo correspondencia; casos ficticios pendientes de revisión del autor para modo hallazgo.
> **Prohibido usar salida IA como ground truth.**
> Alucinación ≠ Discrepancia: un control inventado es cualitativamente peor que un control real con mapeo diferente.

## Resultados por familia

| Familia | N | Precision | Recall | F1 | FP total | Aluc. | Discr. |
|---------|---|-----------|--------|----|---------:|------:|-------:|
| Continuidad del servicio | 4 | 0.0833 | 0.1250 | 0.1000 | 0.8333 | 0.0000 | 0.8333 |
| Control de acceso | 6 | 0.6667 | 0.4861 | 0.5500 | 0.3077 | 0.0000 | 0.3077 |
| Explotación | 10 | 0.5833 | 0.2666 | 0.3567 | 0.5556 | 0.0000 | 0.5556 |
| Gestión del personal | 4 | 0.2500 | 0.0833 | 0.1250 | 0.8000 | 0.0000 | 0.8000 |
| Marco organizativo | 4 | 0.5000 | 0.1250 | 0.2000 | 0.5000 | 0.0000 | 0.5000 |
| Monitorización del sistema | 3 | 0.6667 | 0.2222 | 0.3333 | 0.3333 | 0.0000 | 0.3333 |
| Planificación | 5 | 0.4400 | 0.2067 | 0.2500 | 0.7273 | 0.0000 | 0.7273 |
| Protección de la información | 6 | 0.2500 | 0.1389 | 0.1667 | 0.7143 | 0.0000 | 0.7143 |
| Protección de las aplicaciones informáticas | 2 | 0.7500 | 0.2083 | 0.3250 | 0.3333 | 0.0000 | 0.3333 |
| Protección de las comunicaciones | 4 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Protección de las instalaciones e infraestructuras | 7 | 0.6000 | 0.4905 | 0.5238 | 0.4615 | 0.0000 | 0.4615 |
| Protección de los equipos | 4 | 0.1333 | 0.1458 | 0.1389 | 0.8182 | 0.0000 | 0.8182 |
| Protección de los servicios | 4 | 0.5000 | 0.1458 | 0.2250 | 0.5000 | 0.0000 | 0.5000 |
| Protección de los soportes de información | 5 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Recursos externos | 4 | 0.4167 | 0.2083 | 0.2679 | 0.6250 | 0.0000 | 0.6250 |
| Servicios en la nube | 1 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 0.0000 | 0.0000 |

## Casos detallados

| Código | Nombre | F1 | P | R | TP | FP | FN | Alucinados | Discrepancias | Perdidos |
|--------|--------|----|---|---|----|----|----|------------|---------------|----------|
| org.2 | Normativa de seguridad | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 6 | — | 5.37 | 5.1, 5.10, 5.36 |
| org.3 | Procedimientos de seguridad | 0.4000 | 1.0000 | 0.2500 | 1 | 0 | 3 | — | — | 5.14, 5.24, 5.5 |
| org.4 | Proceso de autorización | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 5 | — | 5.37 | 5.10, 5.2, 8.19 |
| op.pl.3 | Adquisición de nuevos compon | 0.2500 | 0.2000 | 0.3333 | 1 | 4 | 2 | — | 5.22, 5.35, 5.37 | 5.19, 5.8 |
| op.acc.3 | Segregación de funciones y t | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 8.2 |
| op.acc.4 | Proceso de gestión de derech | 1.0000 | 1.0000 | 1.0000 | 3 | 0 | 0 | — | — | — |
| op.exp.1 | Inventario de activos | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 5.12 |
| op.exp.2 | Configuración de seguridad | 0.0000 | 0.0000 | 0.0000 | 0 | 5 | 3 | — | 5.35, 5.37, 8.16 | 8.12, 8.19, 8.9 |
| op.exp.5 | Gestión de cambios | 0.4000 | 0.5000 | 0.3333 | 1 | 1 | 2 | — | 5.37 | 8.29, 8.31 |
| op.exp.9 | Registro de la gestión de in | 0.3333 | 0.3333 | 0.3333 | 1 | 2 | 2 | — | 5.24, 5.25 | 5.27, 5.28 |
| op.ext.1 | Contratación y acuerdos de n | 0.5714 | 0.6667 | 0.5000 | 2 | 1 | 2 | — | 5.22 | 5.14, 6.6 |
| op.ext.2 | Gestión diaria | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 1 | — | 5.37, 8.16 | 5.22 |
| op.cont.2 | Plan de continuidad | 0.4000 | 0.3333 | 0.5000 | 1 | 2 | 1 | — | 5.36, 5.37 | 5.30 |
| op.cont.3 | Pruebas periódicas | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.36 | 5.30, 8.14 |
| op.cont.4 | Medios alternativos | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.37 | 5.30, 8.14 |
| mp.if.1 | Áreas separadas y con contro | 0.7500 | 1.0000 | 0.6000 | 3 | 0 | 2 | — | — | 7.3, 7.4 |
| mp.if.2 | Identificación de las person | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.16 | 7.2, 7.4 |
| mp.if.3 | Acondicionamiento de los loc | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 7.6 | 7.12, 7.5, 7.8 |
| mp.if.5 | Protección frente a incendio | 1.0000 | 1.0000 | 1.0000 | 1 | 0 | 0 | — | — | — |
| mp.if.7 | Registro de entrada y salida | 0.2500 | 0.2000 | 0.3333 | 1 | 4 | 2 | — | 5.37, 7.13, 7.8 | 7.10, 7.9 |
| mp.per.1 | Caracterización del puesto d | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 5.2, 6.1 |
| mp.per.3 | Concienciación | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 1 | — | 5.36 | 6.3 |
| mp.per.4 | Formación | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 1 | — | 5.36 | 6.3 |
| mp.com.1 | Perímetro seguro | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 7.1 | 8.20, 8.21, 8.22 |
| mp.si.3 | Custodia | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 5.36 | 5.10, 5.9, 7.10 |
| mp.si.4 | Transporte | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 5.36 | 5.14, 7.10, 7.9 |
| mp.info.1 | Datos personales | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 8.15 | 5.31, 5.34, 8.11 |
| mp.s.1 | Protección del correo electr | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 4 | — | 8.12 | 5.14, 8.23, 8.24 |
| op.acc.5 | Mecanismo de autenticación ( | 0.8000 | 1.0000 | 0.6667 | 2 | 0 | 1 | — | — | 5.16 |
| mp.com.4 | Separación de flujos de info | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.14 | 8.20, 8.22 |
| op.acc.6 | Mecanismo de autenticación ( | 0.5000 | 0.5000 | 0.5000 | 2 | 2 | 2 | — | 5.15, 5.18 | 6.7, 8.1 |
| op.ext.3 | Protección de la cadena de s | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 5.29, 5.30 |
| mp.eq.2 | Bloqueo de puesto de trabajo | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 2 | — | 5.37, 6.2 | 7.7, 8.1 |
| mp.si.1 | Marcado de soportes | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.35 | 5.13, 7.10 |
| mp.info.2 | Calificación de la informaci | 0.5000 | 0.5000 | 0.5000 | 1 | 1 | 1 | — | 5.36 | 5.13 |
| mp.info.5 | Limpieza de documentos | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.31 | 5.14, 8.10 |
| mp.eq.4 | Otros dispositivos conectado | 0.3333 | 0.3333 | 0.3333 | 1 | 2 | 2 | — | 5.15, 5.37 | 5.9, 8.20 |
| mp.si.5 | Borrado y destrucción | 0.0000 | 0.0000 | 0.0000 | 0 | 3 | 3 | — | 5.28, 5.35, 5.37 | 7.10, 7.14, 8.10 |
| op.cont.1 | Análisis de impacto | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 8.16 | 5.29, 5.30 |
| op.pl.4 | Dimensionamiento/gestión de  | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 8.14 |
| mp.if.4 | Energía eléctrica | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 7.11 |
| mp.s.4 | Protección frente a denegaci | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 4 | — | 8.21 | 5.30, 8.14, 8.16 |
| mp.info.6 | Copias de seguridad | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.35 | 8.13, 8.14 |
| op.exp.8 | Registro de la actividad | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 8.16, 8.17 |
| mp.info.3 | Firma electrónica | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 5.35 | 5.31, 8.24, 8.26 |
| op.acc.1 | Identificación | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 5.37 | 5.16, 5.17, 8.15 |
| mp.info.4 | Sellos de tiempo | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 8.24, 8.26 |
| op.exp.10 | Protección de claves criptog | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 5.17 |
| op.ext.4 | Interconexión de sistemas | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 4 | — | 5.19, 5.36 | 5.14, 8.20, 8.21 |
| mp.per.2 | Deberes y obligaciones | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 5 | — | 5.31, 5.36 | 5.11, 6.2, 6.4 |
| mp.eq.1 | Puesto de trabajo despejado | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 1 | — | 5.37 | 7.7 |
| mp.sw.2 | Aceptación y puesta en servi | 0.4000 | 1.0000 | 0.2500 | 1 | 0 | 3 | — | — | 8.11, 8.31, 8.33 |
| mp.s.3 | Protección de la navegación  | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 8.16, 8.7 |
| op.acc.2 | Requisitos de acceso | 0.3333 | 0.5000 | 0.2500 | 1 | 1 | 3 | — | 5.18 | 8.18, 8.3, 8.4 |
| mp.si.2 | Criptografía | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 8.29 | 7.10, 8.12, 8.24 |
| op.exp.4 | Mantenimiento y actualizacio | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 8.32 | 7.13, 8.31, 8.8 |
| op.nub.1 | Protección de servicios en l | 0.6667 | 1.0000 | 0.5000 | 1 | 0 | 1 | — | — | 5.19 |
| op.mon.1 | Detección de intrusión | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 8.15, 8.20 |
| op.mon.2 | Sistema de métricas | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 1 | — | 5.37 | 5.36 |
| mp.eq.3 | Protección de dispositivos p | 0.2222 | 0.2000 | 0.2500 | 1 | 4 | 3 | — | 5.37, 7.1, 7.6 | 6.7, 7.9, 8.24 |
| op.exp.3 | Gestión de la configuración  | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 3 | — | 8.26 | 8.13, 8.32, 8.9 |
| op.exp.7 | Gestión de incidentes | 0.5000 | 1.0000 | 0.3333 | 2 | 0 | 4 | — | — | 5.25, 5.27, 5.28 |
| mp.com.2 | Protección de la confidencia | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 3 | — | 5.34, 8.3 | 5.14, 8.20, 8.24 |
| op.pl.2 | Arquitectura de Seguridad | 0.3333 | 1.0000 | 0.2000 | 1 | 0 | 4 | — | — | 5.9, 8.20, 8.22 |
| op.exp.6 | Protección frente a código d | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 8.16, 8.19 |
| mp.sw.1 | Desarrollo de aplicaciones | 0.2500 | 0.5000 | 0.1667 | 1 | 1 | 5 | — | 8.29 | 8.25, 8.27, 8.28 |
| op.pl.1 | Análisis de riesgos | 0.0000 | 0.0000 | 0.0000 | 0 | 3 | 1 | — | 5.21, 5.25, 5.35 | 5.7 |
| mp.s.2 | Protección de servicios y ap | 0.4000 | 1.0000 | 0.2500 | 1 | 0 | 3 | — | — | 8.25, 8.29, 8.8 |
| mp.com.3 | Protección de la integridad  | 0.0000 | 0.0000 | 0.0000 | 0 | 2 | 3 | — | 8.26, 8.5 | 6.7, 8.20, 8.24 |
| op.mon.3 | Vigilancia | 0.5000 | 1.0000 | 0.3333 | 1 | 0 | 2 | — | — | 5.7, 8.8 |
| org.1 | Política de seguridad | 0.4000 | 1.0000 | 0.2500 | 1 | 0 | 3 | — | — | 5.2, 5.31, 5.4 |
| op.pl.5 | Componentes certificados | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2 | — | 5.36 | 5.21, 8.9 |
| mp.if.6 | Protección frente a inundaci | 1.0000 | 1.0000 | 1.0000 | 1 | 0 | 0 | — | — | — |
