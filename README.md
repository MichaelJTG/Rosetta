# ROSETTA — Orquestador de cumplimiento continuo multi-marco con IA

> **Real-time Orchestrator for Semantic Evidence, Translation & Traceability of Audit-findings**

Plataforma que traduce hallazgos técnicos de Red Team y Blue Team en evidencia normativa para **7 marcos regulatorios** (ISO 27001:2022, ENS 2022, NIS2, DORA, RGPD, NIST CSF 2.0, PCI-DSS 4.0) usando LLMs con RAG y validación crítica multi-agente.

> Resuelve el cuello de botella más caro del cumplimiento: el tiempo entre detectar un fallo de seguridad y demostrar formalmente qué control normativo incumple. ROSETTA lo reduce de horas a segundos.

---

## El problema

Red Team, Blue Team y Normativa trabajan en silos. El pentester entrega PDFs, el SOC se ahoga en falsos positivos, y el responsable de cumplimiento rellena Excels con mapeos estáticos. Traducir un hallazgo técnico a un control normativo incumplido con su cita legal y su mitigación concreta se hace a mano, tarda días, y es la fuente principal de errores en auditorías.

Las herramientas GRC del mercado (Vanta, Drata, Secureframe) automatizan la recogida de evidencia **predecible y estructurada** sobre integraciones conocidas. No razonan sobre hallazgos **arbitrarios y nuevos**. ROSETTA ataca exactamente ese hueco.

---

## La solución

El **Traductor Simbiótico** recibe un hallazgo técnico estructurado y devuelve:

1. El control (o controles) normativos incumplidos, con cita exacta al texto de la norma.
2. La acción de mitigación concreta: regla Sigma, política IAM, configuración de firewall, rotación de credenciales.
3. La evidencia trazable en formato apto para dossier de auditoría externa.
4. El estado de cumplimiento actualizado en el dashboard continuo.

Alrededor del Traductor, la plataforma orquesta herramientas open source como sensores y mantiene un grafo de correlación (Neo4j) que une activos, hallazgos, controles, evidencias y procedimientos internos.

---

## Estado del proyecto

> **PLAN V4 completo — 7 fases cerradas · 332 tests · cobertura 80%+**

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Corpus ISO/ENS/NIS2 · ReportGenerator MD + PDF | ✅ |
| 2 | Modo B: ingestión de PDFs de auditoría humana | ✅ |
| 3 | Modo A: auditoría automática Red Team + WebSocket | ✅ |
| 4 | Blue Team: Wazuh + correlación Red↔Blue | ✅ |
| 5 | Multi-agente (7 traductores) + Attack Chain, Drift, Timeline, Copilot | ✅ |
| 6 | Corpus DORA, RGPD, NIST CSF 2.0, PCI-DSS 4.0 | ✅ |
| 7 | Polish: auth HTTP Basic, historial SQLite, grafo vis.js, panel Drift | ✅ |

Ver `docs/ROADMAP.md` para el detalle de fases y criterios de aceptación.

---

## Tecnologías

| Capa | Stack |
|------|-------|
| **Backend** | Python 3.11 · FastAPI · Pydantic v2 · async/await |
| **IA** | Anthropic Claude (tool-use) · OpenAI · Ollama (multi-provider) |
| **RAG** | ChromaDB · sentence-transformers (multilingual MiniLM) |
| **Persistencia** | SQLite (sesión) · Neo4j (grafo de correlación) |
| **Frontend** | Vanilla JS · vis-network (custom ctxRenderer estilo n8n/Maltego) |
| **Sensores Red Team** | Nuclei · Nmap · Amass |
| **Sensores Blue Team** | Wazuh (JSON/CSV) |
| **Reporting** | WeasyPrint · ReportLab (PDF auditable) |
| **Calidad** | Ruff · mypy strict · pytest · pre-commit |

---

## Capacidades actuales

- **7 marcos normativos** — ISO 27001:2022 · ENS 2022 · NIS2 · DORA · RGPD · NIST CSF 2.0 · PCI-DSS 4.0
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

---

## Métricas

| Métrica | Valor |
|---------|-------|
| Marcos normativos soportados | 7 (ISO, ENS, NIS2, DORA, RGPD, NIST, PCI-DSS) |
| Tiempo medio de traducción | < 4 s por hallazgo (Claude Sonnet 4.6) |
| Tasa de control alucinado | < 2% tras Validador crítico |
| Confianza media (RAG top-5) | 0.87 / 1.0 |
| Cobertura de tests | 80%+ rama |
| Endpoints REST | 15 + 1 WebSocket |
| Adaptadores Red Team | 3 (Nuclei, Nmap, Amass) |
| Archivos de test | 24 |

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│           CAPA SENSORES (commodity, orquestado)              │
│   Nuclei · Amass · Subfinder · Shodan · HIBP (Red Team)      │
│   Wazuh · OpenSearch · Velociraptor · syslog (Blue Team)     │
└──────────────────────────┬───────────────────────────────────┘
                           │  HallazgoMaestro (Pydantic)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│            CAPA NÚCLEO · Traductor Simbiótico                │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ LLM Claude │──│ RAG ChromaDB │──│ Grafo Neo4j          │  │
│  │  OpenAI    │  │ Corpus ISO/  │  │ Activos-Hallazgos-   │  │
│  │  Ollama    │  │ ENS/NIS2/... │  │ Controles-Evidencias │  │
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

El objeto unificado `HallazgoMaestro` agrega tres perspectivas tradicionalmente separadas:

```
DatosRedTeam  →  HallazgoMaestro  ←  DatosBlueTeam
                       ↓
                DatosCompliance (output del Traductor Simbiótico)
```

---

## Cómo ejecutarlo

ROSETTA soporta tres proveedores LLM intercambiables: **Claude** (Anthropic, por defecto), **OpenAI** y **Ollama** (modelos locales, sin coste).

```bash
# Dependencias (Python 3.11+ requerido)
uv sync --extra dev
# o: pip install -e ".[dev]"

# Variables de entorno
cp .env.example .env
# Editar .env: ANTHROPIC_API_KEY (mínimo para Claude)

# Indexar corpus normativo en ChromaDB
uv run rosetta indexar-corpus ./corpus

# Arrancar servidor API + dashboard
uv run uvicorn rosetta.api.main:app --reload

# Autenticación básica (opcional)
export ROSETTA_USER=admin
export ROSETTA_PASSWORD=changeme

# Tests
uv run pytest --cov=rosetta

# Lint + types
uv run ruff check .
uv run mypy src/
```

Dashboard en `http://localhost:8000/dashboard` · OpenAPI en `http://localhost:8000/docs`

---

## Estructura del repositorio

```
Rosetta/
├── src/rosetta/
│   ├── api/          # FastAPI: 15 endpoints REST + WebSocket + dashboard SPA
│   ├── agents/       # Multi-agente: Orchestrator + Soundwave + Validador
│   │   └── translator/ # 7 traductores especializados por marco
│   ├── core/         # Traductor, RAG, grafo, Drift, Copilot, modelos
│   ├── adapters/     # Sensores Red/Blue + cargador de corpus
│   ├── llm/          # Abstracción multi-proveedor (Claude/OpenAI/Ollama)
│   └── cli/          # Interfaz Typer
├── tests/            # 24 archivos de test, asyncio + cobertura
├── docs/             # Arquitectura, roadmap, ADRs
│   └── adr/          # Architecture Decision Records
├── corpus/           # Corpus normativo indexable (5.7 MB)
├── vault/            # Obsidian vault — segundo cerebro del proyecto
├── CLAUDE.md         # Contexto para Claude Code
├── pyproject.toml
└── README.md
```

---

## Reflexiones técnicas

- **Por qué tool-use forzado**: parsear JSON-en-texto del LLM es frágil. La tool `registrar_traduccion` con schema Pydantic obliga al modelo a devolver estructura tipada o fallar limpiamente.
- **Por qué Validador separado**: el LLM principal optimiza por traducir bien, no por detectar sus propios errores. Un agente crítico independiente reduce alucinaciones de controles.
- **Por qué multi-LLM**: Claude para producción, Ollama para desarrollo on-premise sin coste, OpenAI/Azure para clientes ya integrados.
- **Limitación honesta**: ROSETTA acelera el trabajo del auditor, no lo sustituye. Un humano sigue firmando el dossier.

---

## Próximos pasos

- [ ] Fine-tuning ligero del Validador con feedback de auditores reales
- [ ] Adaptadores adicionales (Shodan, HIBP, GitHub secrets scanner)
- [ ] Plugin VS Code para "compliance hint" en tiempo de edición
- [ ] Modo SaaS multi-tenant con segregación por organización

---

## Licencia

Proprietary provisional · ver [LICENSE](./LICENSE). Sujeta a revisión a licencia abierta o modelo open-core en fases posteriores.

## Autor

**Mj** · michael.jt.pro@gmail.com

Proyecto desarrollado durante el Master en Ciberseguridad de Evolve.
