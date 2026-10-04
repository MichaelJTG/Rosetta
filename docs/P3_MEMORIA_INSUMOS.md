# docs/P3_MEMORIA_INSUMOS.md — Memoria de insumos de la Práctica 3

> Registra las fuentes, datos y herramientas utilizadas durante el desarrollo
> de la Práctica 3, con especial atención a la trazabilidad de los datos de
> evaluación y al cumplimiento del principio «prohibido generar el ground
> truth con IA».

---

## 1. Fuentes normativas

| Fuente | Uso en P3 | Cómo se obtuvo |
|--------|-----------|----------------|
| **RD 311/2022 (ENS) — Anexo II** | Texto de las 73 medidas ENS en `corpus/ens/ens-2022-anexo-ii.yaml` | Descarga pública del BOE (BOE-A-2022-7191). Transcripción manual al formato YAML del proyecto. |
| **CCN-STIC 825 (guía de adecuación ENS)** | Referencia para la columna `iso_27001_2022` del corpus; inspira el mapeo ENS→ISO | Guía pública del CCN. No se reproduce el texto íntegro: solo se usan los identificadores de control que mapea. |
| **ISO/IEC 27001:2022 — Anexo A** | `VALID_ISO_27001_2022_IDS` (93 controles 5.1–8.34) en `eval/run_eval.py` | La estructura del Anexo A (secciones 5–8 y rangos de controles) es conocida públicamente. Los identificadores exactos se construyeron manualmente a partir de la numeración pública (sin reproducir texto con copyright). |
| **SoA del caso TechServ (equipo docente)** | Ground truth de los 73 casos en `eval/ground_truth/ens_iso.json` | Proporcionado por el equipo docente como material de la asignatura. No se publica en abierto: los controles ISO aparecen como listas de IDs, sin reproducir el SoA textual. |

---

## 2. Datos de evaluación

### 2.1 Ground truth `ens_iso.json` (73 casos)

- **Origen**: SoA del caso TechServ facilitado por el equipo docente.
- **Proceso**: los identificadores de control ISO 27001:2022 para cada medida ENS se extrajeron del SoA y se volcaron manualmente al JSON.
- **Garantía de independencia**: el mapeo NO se generó con IA. Generarlo con el propio modelo sería medir el modelo contra sí mismo.
- **Licencia de uso**: material docente; no redistribuir fuera del contexto de la asignatura.

### 2.2 Ground truth `ens_hallazgos_tecnicos.json` (16 casos)

- **Origen**: casos ficticios creados para P3. Empresa imaginaria «TechServ S.A.», 16 hallazgos técnicos (uno por familia ENS).
- **Proceso**: hallazgos redactados manualmente; controles ISO asignados también manualmente como estimación provisional.
- **Advertencia**: todos los casos llevan `"revision": "pendiente"`. Las asignaciones de control NO han sido validadas contra CCN-STIC 825. Las métricas del modo `hallazgo` son indicativas.
- **Datos sensibles**: ninguno. Dominios `.example`, IPs de documentación (RFC 5737), nombres genéricos.

---

## 3. Herramientas y modelos de IA

| Herramienta | Versión / parámetros | Uso |
|-------------|---------------------|-----|
| **Ollama** | v0.4.x (runtime local) | Proveedor LLM en entorno de desarrollo; no requiere API key |
| **qwen2.5:14b** | 14B parámetros (Q4_K_M) | Modelo LLM para el Traductor Simbiótico y el Validador en todos los benchmarks de P3 |
| **ChromaDB** | 1.5.9 | Vector store para el RAG del Traductor |
| **Anthropic SDK** | ≥0.25.0 | Abstracción multi-proveedor LLM; en P3 solo se usa Ollama (sin ANTHROPIC_API_KEY) |

**Nota sobre el uso de IA en el desarrollo**: Claude (claude-sonnet-4-6) se usó como asistente de programación durante la Práctica 3 (Claude Code). Todo el código generado fue revisado y aprobado por el autor. Las docstrings extensas y la documentación están en español por convención del proyecto.

---

## 4. Corpus de normativa indexado

Los siguientes marcos están indexados en ChromaDB (cargados con `rosetta load-corpus all corpus/`):

| Marco | Ficheros fuente en `corpus/` | Estado |
|-------|------------------------------|--------|
| ISO 27001:2022 | `iso27001/` | Indexado |
| ENS RD 311/2022 | `ens/ens-2022-anexo-ii.yaml` | Indexado (enriquecido en C-1) |
| NIS2 | `nis2/` | Indexado |
| DORA | `dora/` | Indexado |
| NIST CSF | `nist/` | Indexado |
| PCI DSS | `pcidss/` | Indexado |
| GDPR | `gdpr/` | Indexado |

El corpus completo se carga en el arranque del contenedor. La ruta de indexación es idempotente: reindexar no duplica documentos.

---

## 5. Datos ficticios usados en demos y tests

Toda demostración y todo test usa datos ficticios para evitar exponer información real de auditorías:

- **Empresa**: TechServ S.A. (ficticia)
- **Dominios**: `*.techserv.local`, `*.example.com`
- **IPs**: rangos de documentación RFC 5737 (192.0.2.x, 198.51.100.x, 203.0.113.x)
- **CVEs**: identificadores con formato válido pero sin vulnerabilidad real asociada (ej. CVE-2024-1234)
- **Credenciales en tests**: variables de entorno (`TEST_EXTRA_USER_PASS`) con valor ficticio en CI

---

## 6. Decisiones de privacidad y publicación

| Elemento | Decisión | Motivo |
|----------|----------|--------|
| SoA del docente | No se publica el texto; solo IDs de control | Material docente, no redistribuible |
| `corpus/ens/*.yaml` | Publicado | Texto del BOE (dominio público) |
| `eval/ground_truth/ens_iso.json` | Publicado (solo IDs ISO, sin texto SoA) | No reproduce el SoA textual |
| Historial git con contraseña antigua | No reescrito aún | Decisión pendiente del autor (ver INC-01) |
| `.env` con credenciales de producción | Nunca versionado | `.gitignore` + pre-commit hook |
