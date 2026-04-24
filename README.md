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

> **PLAN V4 completo — 7 fases cerradas · 332 tests · cobertura 80%**
>
> | Fase | Descripción | Estado |
> |------|-------------|--------|
> | 1 | Corpus ISO/ENS/NIS2 · ReportGenerator MD + PDF | ✅ |
> | 2 | Modo B: ingestión de PDFs de auditoría humana | ✅ |
> | 3 | Modo A: auditoría automática Red Team + WebSocket | ✅ |
> | 4 | Blue Team: Wazuh + correlación Red↔Blue | ✅ |
> | 5 | Multi-agente (7 traductores) + Attack Chain, Drift, Timeline, Copilot | ✅ |
> | 6 | Corpus DORA, RGPD, NIST CSF 2.0, PCI-DSS 4.0 | ✅ |
> | 7 | Polish: auth HTTP Basic, historial SQLite, grafo vis.js, panel Drift | ✅ |
>
> Ver `docs/ROADMAP.md` para el detalle de fases y criterios de aceptación.

## Capacidades actuales

- **7 marcos normativos**: ISO 27001:2022 · ENS 2022 · NIS2 · DORA · RGPD · NIST CSF 2.0 · PCI-DSS 4.0
- **Modo A** — auditoría automática Red Team (Nuclei, Nmap) con WebSocket de progreso en tiempo real
- **Modo B** — ingestión de informes PDF de auditoría humana con extracción LLM
- **Blue Team** — correlación de alertas Wazuh con hallazgos Red Team
- **Multi-agente** — 7 traductores especializados por marco + orquestador + validador
- **Attack Chain** — encadenamiento MITRE ATT&CK sobre hallazgos correlacionados
- **Compliance Timeline** — snapshots históricos de cumplimiento
- **Procedure Drift** — detecta divergencias entre procedimientos escritos y realidad observada
- **Copilot normativo** — preguntas en lenguaje natural sobre controles
- **Gate CI/CD** — endpoint `POST /analyze-diff` para bloquear PRs con incumplimientos normativos
- **Grafo vis.js** — visualización interactiva activo → control en el dashboard
- **Historial persistente** — hallazgos de sesión almacenados en SQLite (sobrevive a reinicios)
- **Autenticación básica** — HTTP Basic Auth opcional vía variables de entorno

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

# Habilitar autenticación básica (opcional — sin estas vars no se requiere auth)
export ROSETTA_USER=admin
export ROSETTA_PASSWORD=changeme

# Dashboard visual
open http://localhost:8000/dashboard
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
