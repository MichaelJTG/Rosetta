---
title: Presentación del proyecto de clase · ROSETTA
tags: [comunicacion, presentacion, rosetta]
created: 2026-04-18
estado: entregado
publico: Clase · itinerario Normativa
---

# ROSETTA · Orquestador de cumplimiento continuo

> Documento usado como presentación del proyecto de clase. Itinerario: Normativa.
> Autor: Mj · Mentor informal: Carlos Gómez Pintado (CEO Cyberxia).

---

## Elevator pitch (30 segundos)

Un orquestador de cumplimiento continuo que convierte el SGSI en un sistema vivo. Toma hallazgos técnicos reales de herramientas open source de Red Team y Blue Team (Nuclei, Amass, Wazuh, Caldera), y una capa de IA los traduce en tiempo real a evidencia normativa multi-marco (ISO 27001, ENS, NIS2, DORA). El resultado es una auditoría que se ejecuta sola 24/7 en vez de una foto anual.

## El problema

En la práctica real, Red Team, Blue Team y Normativa trabajan en silos. El pentester entrega un PDF, el SOC se ahoga en alertas, y el responsable de cumplimiento rellena Excels con mapeos estáticos a la ISO 27001. Nadie traduce automáticamente un hallazgo técnico a un control normativo incumplido ni a la evidencia que un auditor pediría. Esa traducción es manual, cara, lenta y propensa a errores — y es exactamente el gap que la mayoría de las empresas pagan por resolver.

## La solución

El núcleo del proyecto es el **Traductor Simbiótico**: una capa de IA con RAG sobre el corpus normativo que recibe un hallazgo técnico estructurado y devuelve cuatro cosas:

1. El control (o controles) normativos incumplidos, con cita exacta al texto de la norma.
2. La acción de mitigación concreta (regla Sigma, política IAM, configuración de firewall, rotación de credenciales, etc.).
3. La evidencia trazable en formato apto para auditoría.
4. El estado de cumplimiento actualizado en el dashboard continuo.

Alrededor de ese núcleo, la plataforma integra herramientas open source como sensores — sin reinventar la rueda — y genera un grafo de correlación (Neo4j) que une activos, hallazgos, controles y evidencias.

## Qué NO es

No es un escáner de vulnerabilidades propio. No es un SIEM propio. No es una herramienta ofensiva. Es **el tejido conectivo** que hoy falta entre lo técnico y lo normativo.

## Arquitectura en tres capas

**Capa de sensores (commodity, vía adaptadores):** Nuclei, Amass, Subfinder, theHarvester, Caldera, Atomic Red Team del lado Red Team; Wazuh, OpenSearch, Velociraptor del lado Blue Team. Se consumen vía API/CLI, sin modificar su código (ver [[02_ADR/001-orquestacion-sobre-fork]]).

**Capa núcleo (IP propietaria):** Traductor Simbiótico (RAG sobre ChromaDB), grafo de correlación Neo4j, motor de inferencia normativa multi-marco, generador de dossier de auditoría, orquestador FastAPI.

**Capa de salida:** Dashboard de cumplimiento continuo, informes ejecutivos y técnicos, evidencias exportables en formato compatible con auditoría ISO/ENS.

## Stack tecnológico

Python + FastAPI para el orquestador, Neo4j para el grafo de correlación, ChromaDB para la base vectorial del RAG normativo, Docker para contenerización de sensores y honeypots, API de Claude o modelo local (Llama 3.1 / Mistral vía Ollama) para el razonamiento normativo (ver [[02_ADR/002-abstraccion-llm]]).

## Marcos normativos soportados

Ver [[MOC_Normativas]] para el mapa completo.

- [[03_Normativa/ISO_27001_2022]] · pieza central MVP-1
- [[03_Normativa/ENS_2022]] · MVP-3, diferenciador ibérico
- [[03_Normativa/NIS2]] · MVP-8+
- [[03_Normativa/DORA]] · MVP-8+
- [[03_Normativa/RGPD]] · MVP-8+
- [[03_Normativa/NIST_CSF_2]] · MVP-8+
- [[03_Normativa/PCI_DSS_4]] · MVP-8+

## Alcance realista para la entrega de clase

**MVP objetivo:** Traductor Simbiótico funcional sobre ISO 27001:2022 y ENS, alimentado por Nuclei + Amass como sensores Red Team, generando dossier de cumplimiento a partir de una auditoría real sobre un entorno de pruebas propio.

**Fuera del alcance del MVP:** módulos de BAS completo, integración con SIEM del cliente, multi-tenant, UI pulida para usuario final.

## Punto fuerte del proyecto

La **correlación semántica automatizada entre hallazgo técnico y control normativo multi-marco**. Es el único componente que herramientas existentes (Vanta, Drata, Tenable, Qualys) no resuelven bien, y es donde la IA aporta valor real e insustituible.

## Punto débil asumido conscientemente

Los módulos de Red Team y Blue Team nunca serán mejores que las herramientas open source maduras a las que orquestan — y no lo pretenden. El valor del proyecto no vive ahí.

## Por qué resuelve los problemas reales del sector

Resuelve el gap técnico-legal (hallazgos que hoy nadie mapea a controles en tiempo real). Reduce fatiga de alertas filtrando por impacto normativo real. Convierte la auditoría de una foto anual a un estado continuo. Detecta Shadow IT cruzando OSINT con inventario oficial. Da trazabilidad forense lista para auditoría externa desde el día uno.

## Por qué tiene sentido comercial (enfoque Cyberxia)

Multiplica la velocidad de entrega de informes de cumplimiento de una consultora por un factor de 5 a 10. Permite ofrecer "cumplimiento continuo como servicio" en vez de auditorías puntuales. Diferencia frente a competidores que siguen entregando PDFs estáticos.

## Pregunta a Carlos en la reunión

¿Qué parte del flujo le parece más valiosa desde Cyberxia — la automatización del mapeo normativo, la generación automática de evidencia de auditoría, o la correlación entre Shadow IT y controles incumplidos? Su respuesta define por dónde profundizo en los próximos meses.

## Enlaces

- [[09_Comunicacion/mensaje-linkedin-carlos]] · [[08_Reuniones/pendiente-carlos-gomez]] · [[00_Dashboard]] · [[MOC_Roadmap]]
