---
title: MOC · Hallazgos canónicos
tags: [moc, hallazgo, rosetta]
created: 2026-04-18
---

# MOC · Hallazgos canónicos

> Hallazgos arquetípicos que ROSETTA debe traducir correctamente. Sirven como tests E2E del Traductor.
> Cada hallazgo es una nota con: descripción técnica, fuente esperada, controles incumplidos esperados, ejemplo JSON.

## Set canónico para MVP-1 (ISO 27001:2022)

Los 5 hallazgos que validan el MVP-1. Si los 5 devuelven el control correcto top-1 o top-3, el MVP se da por aceptado.

1. [[05_Hallazgos/aws-key-leak|AWS access key filtrada en GitHub público]]
   - Fuente esperada: `GITHUB_SECRETS` o `MANUAL`
   - Controles esperados: ISO 27001 A.8.24 (criptografía y gestión de claves) · A.5.15 (control de acceso)
   - Ejemplo JSON: `examples/finding_aws_leaked_key.json`

2. [[05_Hallazgos/puerto-rdp-expuesto|RDP (3389) expuesto a internet]]
   - Fuente esperada: `SHODAN` o `NMAP`
   - Controles esperados: ISO 27001 A.8.20 (seguridad de redes) · A.8.22 (segregación de redes)

3. [[05_Hallazgos/sin-mfa|Cuenta administrativa sin MFA]]
   - Fuente esperada: `MANUAL` (auditoría IAM) o adaptador AWS/Azure futuro
   - Controles esperados: ISO 27001 A.5.16 (autenticación) · A.5.15

4. [[05_Hallazgos/sin-logs|Sistema crítico sin logs centralizados]]
   - Fuente esperada: `WAZUH` (ausencia de eventos)
   - Controles esperados: ISO 27001 A.8.15 (registro de eventos) · A.8.16 (monitorización)

5. [[05_Hallazgos/cifrado-debil|Certificado TLS con cifrado débil]]
   - Fuente esperada: `NUCLEI`
   - Controles esperados: ISO 27001 A.8.24 · A.8.20

## Categorías futuras

- **OSINT**: subdominios olvidados, paneles admin expuestos, repos GitHub con secretos.
- **Postura cloud**: buckets públicos, IAM excesiva, sin encryption at rest.
- **Logs**: ausencia de logs, retención corta, sin SIEM.
- **Identidad**: sin MFA, contraseñas débiles, cuentas inactivas.
- **Procedure drift**: procedimiento dice una cosa, sensores observan otra ([[06_Procedimientos/insight-carlos-procedure-drift|Carlos's killer feature]]).

## Plantilla de hallazgo canónico

Ver [[99_Templates/Hallazgo_template]].
