---
title: Patrón · Aislamiento dual de red (management vs operations)
tags: [hallazgo, patron, seguridad, deployment, rosetta]
categoria: patron-seguridad
created: 2026-04-20
origen: [[05_Hallazgos/referencia-decepticon]]
---

# Patrón · Aislamiento dual de red (management vs operations)

## Qué es

Diseño de deployment con **dos redes Docker (o VPC) separadas**:

- **Red de management** (`rosetta-core`): servicios de inteligencia — FastAPI, ChromaDB, Neo4j, LLM local, dashboard. Sin exposición al exterior salvo API gateway.
- **Red de operations** (`rosetta-sensors`): contenedores que interactúan con el mundo exterior — adapters Red Team que escanean targets, adapters Blue Team que consumen logs del cliente.

La comunicación sensor→core es unidireccional y estricta: solo a través de una **cola de mensajes** (Redis Streams o NATS) con un único topic por tipo de mensaje, transportando únicamente estructuras `DatosRedTeam` / `DatosBlueTeam` normalizadas y validadas por Pydantic en la frontera.

Los sensores **no conocen** credenciales de Neo4j, ChromaDB, LLM ni dashboard. Si un sensor se compromete, el atacante llega a una cola de mensajes — nada más.

## Origen

Observado en [[referencia-decepticon]]: `decepticon-net` (orquestador + Neo4j + LLM) aislada de `sandbox-net` (Kali + targets). Si un target compromete el Kali, el atacante queda atrapado en sandbox-net.

## Por qué importa a ROSETTA aunque no hagamos ofensa

No somos ofensivos, pero:

1. **Nuclei (MVP-2)** escanea targets reales — infraestructura no controlada, que puede devolver payloads maliciosos al parser.
2. **Wazuh (MVP-4/5)** consume logs del cliente — pueden contener cadenas construidas para escape de parsing.
3. **Futuros adapters** pueden conectarse a APIs de terceros (Shodan, HIBP) con respuestas no confiables.

Si un parser de un sensor tiene un CVE (pasa en cualquier librería), lo mejor es que la explotación no alcance los datos del núcleo.

## Cómo lo aplicamos a ROSETTA

### Hoy (desarrollo local)
No aplicable. Todo corre en `localhost`. Costo/beneficio negativo.

### Cuando llegue el primer deployment (MVP-8 o primer cliente)

`docker-compose.yml` con dos redes:

```yaml
networks:
  rosetta-core:
    driver: bridge
    internal: false   # API gateway sale a internet/red corporativa
  rosetta-sensors:
    driver: bridge
    internal: true    # sensores NO tienen salida a red de management

services:
  api:
    networks: [rosetta-core]
  chromadb:
    networks: [rosetta-core]
  neo4j:
    networks: [rosetta-core]
  redis-bus:
    networks: [rosetta-core, rosetta-sensors]   # única pasarela
  nuclei-adapter:
    networks: [rosetta-sensors]
  wazuh-adapter:
    networks: [rosetta-sensors]
```

Con Redis actuando como única frontera, y los sensores publicando mensajes `DatosRedTeam` validados con Pydantic antes de cruzar.

## Bonus: dogfooding y talking point

ROSETTA cumpliría sobre sí misma **ISO 27001 A.8.22 (Segregación de redes)** y **ENS op.red.2 (Protección del perímetro interno)**. Para un producto de compliance esto es marketing puro — *"venimos con segregación de red por defecto y podemos enseñar el mapeo de controles de nuestra propia infraestructura"*.

## Cuándo introducirlo

**No ahora**. Overhead innecesario en dev.

**Planificar en MVP-8** como requisito del deployment de referencia. Debe ir en un ADR de deployment (no existe aún — propuesta: **ADR-006 · Arquitectura de despliegue segura por defecto**).

## Riesgos y mitigación

- **Complejidad operativa**: compose con dos redes es más difícil de debuggear. Mitigación: diagrama ASCII en el ADR + runbook.
- **Latencia añadida por la cola**: negligible con Redis Streams (<1ms local).
- **Single point of failure en Redis**: compensar con persistencia AOF y replicación en producción.

## Enlaces

- [[05_Hallazgos/referencia-decepticon]] · [[MOC_Hallazgos]]
- Controles relacionados: [[03_Normativa/ISO_27001_2022]] (A.8.22) · [[03_Normativa/ENS_2022]] (op.red.2)
- Pendiente: ADR-006 de deployment
