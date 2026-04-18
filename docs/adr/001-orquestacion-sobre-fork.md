# ADR-001 · Orquestación de open source sobre fork/reimplementación

- **Estado:** Aprobado
- **Fecha:** 2026-04-18
- **Autor:** Mj
- **Consultado:** asistente Claude (Cowork)

## Contexto

ROSETTA necesita capacidades de Red Team (escaneo, OSINT) y Blue Team (SIEM, honeypots). Existen múltiples herramientas open source maduras para ambas funciones. Se plantea la decisión entre (a) reimplementarlas dentro del producto para tener control total, (b) forkearlas e integrarlas modificadas, o (c) orquestarlas sin tocar su código vía CLI/API.

## Decisión

**Adoptamos la opción (c): orquestación sin fork.**

Cada herramienta externa se consume mediante su interfaz pública (subprocess o API REST) y su salida se normaliza al modelo interno `HallazgoMaestro`. No se modifica el código upstream de ninguna herramienta.

## Consecuencias positivas

1. **Seguridad legal inequívoca**: orquestar no está sujeto a las cláusulas copyleft de GPL/AGPL. Wazuh, theHarvester, OpenVAS u otras herramientas copyleft pueden usarse sin contaminar nuestra licencia.
2. **Mantenimiento más barato**: recibimos las mejoras upstream automáticamente.
3. **Foco claro**: el valor diferencial de ROSETTA es el Traductor Simbiótico, no los sensores.
4. **Swap trivial**: cambiar Nuclei por OpenVAS es cambiar un adaptador, no refactorizar el core.

## Consecuencias negativas aceptadas

1. Dependemos de binarios externos en el host de ejecución.
2. Cambios de formato de salida de una herramienta pueden romper el adaptador — mitigado con tests de integración.
3. No podemos optimizar internamente el rendimiento de las herramientas.

## Alternativas descartadas

- **(a) Reimplementación:** descartada. Un proyecto unipersonal no puede superar a Nuclei o Wazuh en sus propios dominios. Lo hecho sería mediocre.
- **(b) Fork con modificaciones:** descartada para el caso general. Se permite puntualmente si una herramienta MIT/Apache necesita un parche muy localizado, y siempre previo ADR específico.

## Referencias

- Herramientas MIT/Apache seguras para embebido: Nuclei, Subfinder, Amass, Atomic Red Team, Caldera.
- Herramientas GPL/AGPL seguras para orquestación externa: Wazuh, theHarvester, OpenVAS, MISP, TheHive.
