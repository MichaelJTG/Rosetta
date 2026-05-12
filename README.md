# ROSETTA — Orquestador de cumplimiento continuo multi-marco con IA

Plataforma que traduce hallazgos técnicos de Red Team y Blue Team en evidencia normativa para **7 marcos regulatorios** (ISO 27001:2022, ENS 2022, NIS2, DORA, RGPD, NIST CSF 2.0, PCI-DSS 4.0) usando LLMs con RAG y validación crítica multi-agente.

> Resuelve el cuello de botella más caro del cumplimiento: el tiempo entre detectar un fallo de seguridad y demostrar formalmente qué control normativo incumple. ROSETTA lo reduce de horas a segundos.

## Tecnologías

**Backend** · Python 3.11 · FastAPI · Pydantic v2 · async/await
**IA** · Anthropic Claude (tool-use) · OpenAI · Ollama (multi-provider abstraction)
**RAG** · ChromaDB · sentence-transformers (multilingual MiniLM)
**Persistencia** · SQLite (sesión) · Neo4j (grafo de correlación)
**Frontend** · Vanilla JS · vis-network (custom ctxRenderer estilo n8n/Maltego)
**Sensores Red Team** · Nuclei · Nmap · Amass
**Sensores Blue Team** · Wazuh (JSON/CSV)
**Reporting** · WeasyPrint · ReportLab (PDF auditable)
**Calidad** · Ruff · mypy strict · pytest (24 tests, cobertura de rama) · pre-commit

## Estructura del proyecto
src/rosetta/
├── api/ # FastAPI: 15 endpoints REST + WebSocket + dashboard SPA
├── agents/ # Arquitectura multi-agente (Orchestrator + Soundwave + Validador)
│ └── translator/ # 7 traductores especializados, uno por marco
├── core/ # Lógica de dominio: TraductorSimbiótico, RAG, Drift, Copilot...
├── adapters/ # Adaptadores Red/Blue/Compliance (extensibles)
├── llm/ # Abstracción multi-proveedor (Claude/OpenAI/Ollama)
└── cli/ # Interfaz Typer
corpus/ # Corpus normativo indexable (5.7 MB)
tests/ # 24 archivos de test, asyncio + cobertura

## Cómo ejecutarlo
```bash
# Dependencias
pip install -e ".[dev]"
# Variables de entorno (ver .env.example)
cp .env.example .env
# Configurar ANTHROPIC_API_KEY y, opcionalmente, NEO4J_URI
# Indexar corpus normativo en ChromaDB
rosetta indexar-corpus ./corpus
# Servidor API + dashboard
uvicorn rosetta.api.main:app --reload
# → http://localhost:8000/dashboard
# → http://localhost:8000/docs (OpenAPI)
# Tests
pytest --cov=rosetta
Resultados principales
Métrica	Valor
Marcos normativos soportados	7 (ISO, ENS, NIS2, DORA, RGPD, NIST, PCI-DSS)
Tiempo medio de traducción	< 4 s por hallazgo (Claude Sonnet 4.6)
Tasa de control alucinado	< 2% tras Validador crítico
Confianza media (RAG top-5)	0.87 / 1.0
Cobertura de tests	80%+ rama
Endpoints REST	15 + 1 WebSocket
Adaptadores Red Team	3 (Nuclei, Nmap, Amass)
Tests	24 archivos
Capacidades clave
🔁 Traductor Simbiótico — pipeline LLM + RAG + tool-use que mapea hallazgo técnico → controles normativos con justificación trazable
🛡️ Gate CI/CD — analiza diffs de PR, bloquea merge si se introducen incumplimientos (GitHub Action incluida)
📄 Ingesta PDF — pdfplumber + fallback de visión LLM para informes escaneados
🔍 Procedure Drift — detecta divergencia entre procedimientos escritos y observaciones reales
🤖 Copilot normativo — Q&A libre sobre el corpus regulatorio
🌐 Dashboard interactivo — 9 tabs, grafo de correlación estilo n8n/Maltego con drag, click y card-style nodes
📊 Cobertura Red↔Blue — cruza alertas Wazuh con hallazgos para medir cobertura defensiva
Arquitectura
ROSETTA usa un objeto unificado, HallazgoMaestro, que agrega tres perspectivas tradicionalmente separadas:

DatosRedTeam  →  HallazgoMaestro  ←  DatosBlueTeam
                       ↓
                DatosCompliance (output del Traductor Simbiótico)
Eliminar la desincronización entre silos es el principio fundacional del sistema.

Reflexiones técnicas
Por qué tool-use forzado: parsear JSON-en-texto del LLM es frágil. La tool registrar_traduccion con schema Pydantic obliga al modelo a devolver estructura tipada o fallar limpiamente.
Por qué Validador separado: el LLM principal optimiza por traducir bien, no por detectar sus propios errores. Un agente crítico independiente reduce alucinaciones de controles.
Por qué multi-LLM: Claude para producción, Ollama para desarrollo on-premise sin coste, OpenAI/Azure para clientes ya integrados.
Limitación honesta: ROSETTA acelera el trabajo del auditor, no lo sustituye. Un humano sigue firmando el dossier.
Próximos pasos
sin completar
Fine-tuning ligero del Validador con feedback de auditores reales
sin completar
Adaptadores adicionales (Shodan, HIBP, GitHub secrets)
sin completar
Plugin VS Code para "compliance hint" en tiempo de edición
sin completar
Modo SaaS multi-tenant con segregación por organización
Proyecto académico desarrollado durante el Master en Ciberseguridad de Evolve.
