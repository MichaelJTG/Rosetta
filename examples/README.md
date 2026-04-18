# Ejemplos de hallazgos para ROSETTA

Cada archivo JSON de este directorio representa un `DatosRedTeam` canónico listo para ser procesado por el Traductor Simbiótico. Se usan como entrada en tests E2E y demos en vivo.

## Catálogo

- `finding_aws_leaked_key.json` · AWS access key expuesta en repositorio público. Esperado: ISO 27001 A.8.24 (gestión de claves), A.5.15 (control de acceso), ENS op.acc.1.

Próximos (ver MVP-1):
- Puerto RDP 3389 expuesto a internet.
- Servicio web sin MFA en panel admin.
- Servidor de desarrollo sin logs habilitados.
- Credenciales filtradas en pastebin.
