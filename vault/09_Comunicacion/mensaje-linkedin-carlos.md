---
title: Mensaje LinkedIn · Carlos Gómez Pintado
tags: [comunicacion, mentor/carlos, rosetta]
created: 2026-04-18
estado: entregado
destinatario: Carlos Gómez Pintado · CEO Cyberxia
---

# Mensaje LinkedIn · Carlos Gómez Pintado

> Objetivo: presentar ROSETTA ("Ecosistema Total / Traductor Simbiótico") y pedir 20–30 min de feedback.
> Tono: alumno a mentor, respetuoso pero directo, sin rellenos.
> Enlace pendiente: [[08_Reuniones/pendiente-carlos-gomez]].

---

## Versión 1 · Mensaje largo (primer contacto en frío)

Hola Carlos,

Te escribo como alumno tuyo porque llevo unas semanas dándole forma a un proyecto en el que me gustaría muchísimo tener tu criterio antes de seguir invirtiendo horas. Prefiero que me digas pronto si voy por buen camino o si estoy reinventando una rueda que ya existe.

La idea, que estoy llamando internamente **"Ecosistema Total"** con un **"Traductor Simbiótico"** en su núcleo, parte de una observación que seguro te resulta familiar: Red Team, Blue Team y Normativa siguen trabajando en silos. El auditor rellena Excels, el pentester entrega PDFs, el SOC se ahoga en falsos positivos, y el SGSI (ISO 27001, ENS, NIS2, DORA, RGPD…) se queda como un documento muerto entre auditorías.

Mi propuesta es un orquestador autónomo tipo ASOC ligero donde una capa de IA actúa de "Traductor Simbiótico": toma un hallazgo técnico (una credencial filtrada, un puerto expuesto, un activo de Shadow IT) y lo convierte automáticamente en tres cosas: el control normativo incumplido, la configuración de defensa concreta para mitigarlo, y la evidencia trazable lista para auditoría. El resultado es cumplimiento continuo en vez de fotos anuales, y reducción real de fatiga de alertas porque solo escala al analista lo que viola un control activo.

Arquitectónicamente lo estoy montando modular: FastAPI para la API interna, Neo4j para correlacionar activos–hallazgos–controles, RAG sobre corpus normativo en ChromaDB, y un selector de marco por auditoría (ISO 27001:2022, ENS, NIS2, DORA, PCI-DSS, NIST CSF…). Es un proyecto paralelo a mis estudios, así que estoy priorizando agresivamente: primero el Traductor y el mapeo normativo, después la capa de OSINT/ASM, y al final el honeypot adaptativo.

Me encantaría tener **20–30 minutos contigo**, virtuales o presenciales, para enseñarte el diseño y que me digas sin filtros qué te chirría, qué descartarías, y si ves un caso de uso real en Cyberxia o en sus clientes. Tu perspectiva me ahorraría meses de ir por el camino equivocado.

Gracias de antemano por el tiempo,
Mj

---

## Versión 2 · Mensaje corto (si ya hay confianza)

Hola Carlos,

Llevo semanas dándole forma a un proyecto y me gustaría mucho tu opinión antes de seguir. Lo estoy llamando "Ecosistema Total": un orquestador autónomo con una capa de IA ("Traductor Simbiótico") que toma un hallazgo técnico (credencial filtrada, Shadow IT, puerto expuesto) y lo convierte automáticamente en control normativo incumplido + configuración de defensa + evidencia de auditoría.

Soporta selector de marco (ISO 27001, ENS, NIS2, DORA, PCI-DSS, NIST CSF…) y la tesis es cumplimiento continuo en vez de fotos anuales.

¿Tendrías 20–30 min para que te lo enseñe y me digas sin filtros qué ves mal? Tu feedback me ahorraría meses.

Gracias,
Mj

---

## Versión 3 · Hook corto (nota de conexión LinkedIn, 300 caracteres)

Hola Carlos, soy alumno tuyo. Estoy montando un proyecto de orquestación SecOps + compliance continuo con IA ("Traductor Simbiótico" entre hallazgo técnico y control normativo). Me encantaría enseñártelo 20 min y que me lo destroces con sinceridad antes de invertir más meses. Gracias.

---

## Respuesta de Carlos (clave para el roadmap)

Carlos respondió con entusiasmo y señaló el **procedure drift** como killer feature: *"ooooh MUY potente, es importante la revisión de procedimientos y mantenimiento de los mismos que es el gran problema de las empresas pero me mola muchisimo!"*

Ese insight entró al roadmap como [[MOC_Roadmap#MVP-5|MVP-5]] y tiene nota dedicada en [[06_Procedimientos/insight-carlos-procedure-drift]].

## Notas operativas

- No adjuntar diagramas ni documentos en el primer mensaje. El objetivo es conseguir la reunión, no explicar todo.
- Si pide más info, mandarle un doc de 1 página con arquitectura y el escenario maestro.
- Si no contesta en 7-10 días, un reenvío corto ("sé que andas liado, te dejo esto por aquí por si te interesa") es aceptable. Una sola vez.

## Enlaces

- [[08_Reuniones/pendiente-carlos-gomez]] · [[09_Comunicacion/presentacion-proyecto-clase]] · [[00_Dashboard]]
