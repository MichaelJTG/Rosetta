---
title: Insight de Carlos — procedure drift como pilar del proyecto
tags: [mentor/carlos, decision/aprobada, procedimiento, idea]
created: 2026-04-18
---

# Insight de Carlos — procedure drift

## Cita textual del mentor

> "Ojo eeeeeeeeeeeeeeeh MUY potente, es importante la revisión de procedimientos y mantenimiento de los mismos que es el gran problema de las empresas pero me mola muchisimo!"

— Carlos Gómez Pintado, CEO de Cyberxia, en respuesta al pitch inicial de ROSETTA.

## Interpretación

Carlos está señalando un dolor real que él ve todos los días en sus clientes: los procedimientos se escriben una vez para pasar la auditoría y luego se quedan estáticos mientras la realidad operativa evoluciona. El resultado es **procedure drift**: la documentación deja de reflejar cómo se opera. Es la causa número uno de no-conformidades en auditorías de ISO 27001 en España.

## Implicación para ROSETTA

El Traductor Simbiótico, tal como está diseñado, traduce **hallazgo técnico → control normativo**. Lo que Carlos sugiere es extender el Traductor para que también traduzca **comportamiento observado ↔ procedimiento escrito** y detecte desviación.

Ejemplo canónico:
- Procedimiento `PRO-IAM-001` dice: "Las cuentas inactivas se desactivan en 30 días."
- Sensor Blue Team (Wazuh) observa: 12 cuentas con más de 90 días sin actividad y sin desactivar.
- Salida ROSETTA: "Drift detectado. Procedimiento no se cumple en la práctica. Opciones: (a) desactivar las cuentas, (b) actualizar el procedimiento si la práctica real es intencionada. Propuesta de redacción actualizada: ..."

## Estado

Incorporado al roadmap como **MVP-5**. Ver `docs/ROADMAP.md`.

## Relacionado con

- [[00_Index]] · [[00_Dashboard]] · [[MOC_Roadmap#MVP-5]]
- [[08_Reuniones/pendiente-carlos-gomez]]
- [[05_Hallazgos/sin-logs]] (ejemplo canónico relacionado)
