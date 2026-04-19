# ROSETTA

**Real-time Orchestrator for Semantic Evidence, Translation & Traceability of Audit-findings**

Orquestador de cumplimiento continuo. Toma hallazgos técnicos reales de herramientas open source (Red Team y Blue Team), y una capa de IA los traduce en tiempo real a evidencia normativa multi-marco: ISO 27001:2022, ENS, NIS2, DORA, RGPD, NIST CSF 2.0, PCI-DSS v4.0.

El resultado es que el SGSI deja de ser un documento muerto y se convierte en un sistema vivo que audita sus propios controles 24/7.

---

## El problema

Red Team, Blue Team y Normativa trabajan en silos. El pentester entrega PDFs, el SOC se ahoga en falsos positivos, y el responsable de cumplimiento rellena Excels con mapeos estáticos. Traducir un hallazgo técnico a un control normativo incumplido con su cita legal y su mitigación concreta se hace a mano, tarda días, y es la fuente principal de errores en auditorías.

Las herramientas GRC del mercado (Vanta, Drata, Secureframe) automatizan la recogida de evidencia **predecible y estructurada** sobre integraciones conocidas. No razonan sobre hallazgos **arbitrarios y nuevos**. ROSETTA ataca exactamente ese hueco.

## La solución

El **Traductor Simbiótico** recibe un hallazgo técnico estructurado y devuelve:

1. El control (o controles) normativos incumplidos, con cita exacta al texto de la norma.
2. La acción de mitigación concreta: regla Sigma, política IAM, configuración de firewall, rotación de credenciales.
3. La evidencia trazable en formato apto para dossier de auditoría externa.
4. El estado de cumplimiento actualizado en el dashboard continuo.

Alrededor del Traductor, la plataforma orquesta herramientas open source como sensores y mantiene un grafo de correlación (Neo4j) que une activos, hallazgos, controles, evidencias y procedimientos internos.

## Estado del proyecto

> Fase: **MVP-7 completado · Gate CI/CD activo**. Ver `docs/ROADMAP.md` para el detalle de fases.

## Arquitectura rápida

```
┌──────────────────────────────────────────────────────────────┐
│           CAPA SENSORES (commodity, orquestado)              │
│   Nuclei · Amass · Subfinder · Shodan · HIBP (Red Team)      │
│   Wazuh · OpenSearch · Velociraptor · syslog (Blue Team)     │
└──────────────────────────┬───────────────────────────────────┘
                           │  Hallazgo Maestro (Pydantic)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│            CAPA NÚCLEO · Traductor Simbiótico                │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ LLM Claude │──│ RAG ChromaDB │──│ Grafo Neo4j          │  │
│  │            │  │ Corpus ISO/  │  │ Activos-Hallazgos-   │  │
│  │            │  │ ENS/NIS2/... │  │ Controles-Evidencias │  │
│  └────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │  DatosCompliance
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    CAPA SALIDA                               │
│  FastAPI · CLI · Dashboard continuo · Dossier auditoría      │
│  Gate CI/CD (PR-level compliance check)                      │
└──────────────────────────────────────────────────────────────┘
```

## Cómo empezar

ROSETTA soporta tres proveedores LLM intercambiables: **Claude** (Anthropic, por defecto), **OpenAI** y **Ollama** (modelos locales, sin coste). Puedes empezar sin clave de API usando Ollama — ver [NEXT_STEPS.md §10](./NEXT_STEPS.md#10-desarrollo-sin-clave-de-anthropic--ollama-local).

Requisitos: Python 3.11+, [uv](https://docs.astral.sh/uv/). Para Claude: API key de Anthropic. Para Ollama: ninguna.

```bash
# Clonar (cuando haya remoto) o entrar en el directorio del proyecto
cd Rosetta

# Crear entorno e instalar dependencias
uv sync --extra dev

# Configurar variables de entorno
cp .env.example .env
# Edita .env y pon tu ANTHROPIC_API_KEY

# Activar entorno
uv run rosetta version

# Ejecutar tests
uv run pytest

# Lint + types
uv run ruff check .
uv run mypy src/

# Arrancar la API (modo dev)
uv run uvicorn rosetta.api.main:app --reload
```

## Estructura del repositorio

```
Rosetta/
├── src/rosetta/          # Código fuente
│   ├── core/             # Traductor, RAG, grafo, modelos
│   ├── adapters/         # Sensores Red/Blue + cargador de corpus
│   ├── llm/              # Cliente Claude
│   ├── api/              # FastAPI
│   └── cli/              # Typer CLI
├── tests/                # Pytest
├── docs/                 # Arquitectura, roadmap, ADRs
│   └── adr/              # Architecture Decision Records
├── corpus/               # Corpus normativo (PDFs/MDs en .gitignore)
├── examples/             # Casos de uso de ejemplo
├── vault/                # Obsidian vault — segundo cerebro
├── CLAUDE.md             # Contexto para Claude Code
├── pyproject.toml
└── README.md
```

## Licencia

Proprietary provisional · ver [LICENSE](./LICENSE). Sujeta a revisión a licencia abierta o modelo open-core en fases posteriores.

## Autor

Mj · michael.jt.pro@gmail.com

Proyecto desarrollado bajo la mentoría informal de Carlos Gómez Pintado (CEO, Cyberxia).
