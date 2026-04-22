ROSETTA — Flujo de trabajo completo y estado real del proyecto

> Documento creado el 2026-04-21 para que el usuario pueda comparar
> **lo que está construido hoy** con **la visión que tiene del proyecto**.
> Lee este archivo antes de hablar con Claude Code.

---

## 1. La idea central en una frase

**ROSETTA toma un hallazgo técnico de seguridad (ej. "encontré una clave AWS expuesta en GitHub")
y lo convierte automáticamente en evidencia normativa lista para una auditoría
(ej. "incumple ISO 27001 A.8.24, ENS op.acc.5, con la cita textual del control y la acción de remediación concreta").**

No es un escáner. No es un SIEM. No compite con Vanta ni Drata.
Es el **traductor** entre el lenguaje técnico del Red/Blue Team y el lenguaje legal del compliance.

---

## 2. Los tres problemas reales que resuelve

| Problema real en empresas | Cómo lo resuelve ROSETTA |
|---------------------------|--------------------------|
| El técnico encuentra vulnerabilidades pero no sabe qué norma incumple | Traductor Simbiótico: LLM + RAG sobre corpus normativo |
| Los procedimientos escritos no reflejan lo que pasa en producción | Procedure Drift: compara procedimiento ↔ realidad observada |
| El cumplimiento se evalúa una vez al año, no de forma continua | Grafo Neo4j + Dashboard: acumulación y visión en tiempo real |

---

## 3. Arquitectura en tres capas

```
┌─────────────────────────────────────────────────────────┐
│  CAPA 1 — SENSORES (herramientas open source externas)  │
│                                                         │
│  Nuclei · Amass · Shodan · HIBP · theHarvester · Nmap  │
│  Wazuh (Blue Team) · Logs · Alertas EDR                 │
│                                                         │
│  ROSETTA NO los reimplementa. Solo los orquesta         │
│  vía CLI/API y normaliza su salida.                     │
└────────────────────┬────────────────────────────────────┘
                     │  DatosRedTeam (Pydantic)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  CAPA 2 — NÚCLEO (IP propia de ROSETTA)                 │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  HallazgoMaestro                                 │   │
│  │  (objeto Pydantic central que une todo)          │   │
│  │  = DatosRedTeam + DatosBlueTeam + DatosCompliance│   │
│  └───────────────────────┬──────────────────────────┘   │
│                          │                              │
│  ┌───────────────────────▼──────────────────────────┐   │
│  │  Traductor Simbiótico                            │   │
│  │  1. Construye query semántica del hallazgo       │   │
│  │  2. RAG: recupera top-5 fragmentos del corpus    │   │
│  │  3. LLM (Claude/Ollama/OpenAI): razona sobre     │   │
│  │     hallazgo + contexto normativo                │   │
│  │  4. Devuelve DatosCompliance (schema forzado     │   │
│  │     con tool-use, nunca texto libre)             │   │
│  └───────────┬───────────────────────────┬──────────┘   │
│              │                           │              │
│  ┌───────────▼──────────┐   ┌────────────▼───────────┐  │
│  │  ChromaDB            │   │  Neo4j                 │  │
│  │  Corpus normativo    │   │  Grafo de correlación  │  │
│  │  ISO 27001, ENS,     │   │  Activo → Hallazgo →   │  │
│  │  NIS2, DORA, NIST…   │   │  Control → Marco       │  │
│  │  (vectores embeddings│   │  (persistencia de      │  │
│  │   por control)       │   │   toda la trazabilidad)│  │
│  └──────────────────────┘   └────────────────────────┘  │
└──────────────────────────────┬──────────────────────────┘
                               │  HallazgoMaestro completo
                               ▼
┌─────────────────────────────────────────────────────────┐
│  CAPA 3 — SALIDA                                        │
│                                                         │
│  FastAPI REST  ·  Dashboard web  ·  CLI Typer           │
│  Gate CI/CD (GitHub Actions)  ·  Dossier Markdown       │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Flujo de datos paso a paso (el camino canónico)

```
① Sensor detecta algo
   Ej: Nuclei encuentra puerto RDP 3389 expuesto a internet en servidor.example.com

② Adaptador normaliza la salida
   nuclei.py → DatosRedTeam {
     origen: "nuclei",
     activo_detectado: "servidor.example.com:3389",
     evidencia: "Nuclei template rdp-open-port.yaml, CVSS 7.5",
     vector_ataque: "Puerto RDP expuesto a internet sin restricción de IP",
     dificultad_explotacion: "media"
   }

③ Se crea el HallazgoMaestro
   HallazgoMaestro {
     id_hallazgo: "SEC-A1B2C3D4",
     timestamp: "2026-04-21T10:30:00Z",
     red_team_data: <DatosRedTeam del paso ②>,
     blue_team_data: null,      ← pendiente
     compliance_data: null      ← se llena en el paso siguiente
   }

④ Traductor Simbiótico recibe el hallazgo
   a. Construye query: "Puerto RDP expuesto a internet. Activo: servidor.example.com:3389"
   b. RAG consulta ChromaDB: devuelve fragmentos de ISO 27001 A.8.20, A.8.22, ENS mp.com.1
   c. LLM recibe: hallazgo + fragmentos normativos + schema de respuesta obligatorio
   d. LLM devuelve (via tool-use, no texto libre):
      DatosCompliance {
        marcos_aplicables: ["iso_27001_2022", "ens_2022"],
        controles_incumplidos: ["A.8.20", "A.8.22"],
        cita_normativa: "A.8.20: Seguridad en redes - Las redes deben ser gestionadas...",
        justificacion: "El puerto RDP sin restricción de IP...",
        impacto_legal: "alta",
        accion_mitigacion: "Aplicar regla de firewall: deny tcp any 3389; allow tcp 10.0.0.0/8 3389",
        evidencia_auditoria: "Hallazgo SEC-A1B2C3D4: servidor.example.com expone..."
      }

⑤ HallazgoMaestro se completa y persiste en Neo4j
   Nodos creados:
     (Activo: servidor.example.com)
     (Hallazgo: SEC-A1B2C3D4)
     (Control: A.8.20, marco: iso_27001_2022)
     (Control: A.8.22, marco: iso_27001_2022)
     (Marco: iso_27001_2022)
   Relaciones:
     (Activo)-[:AFECTADO_POR]->(Hallazgo)
     (Hallazgo)-[:INCUMPLE]->(Control A.8.20)
     (Control A.8.20)-[:PERTENECE_A]->(Marco)

⑥ Dashboard y salidas se actualizan
   - Panel "Estado de cumplimiento" muestra A.8.20 con +1 hallazgo
   - Grafo Neo4j muestra la red de relaciones
   - Dossier Markdown listo para adjuntar a informe de auditoría
```

---

## 5. El objeto central: HallazgoMaestro

Todo en ROSETTA gira en torno a este objeto. Es el "contrato" entre capas.

```python
HallazgoMaestro {
  id_hallazgo:     "SEC-A1B2C3D4"           # generado automáticamente
  timestamp:       datetime                  # cuándo se detectó

  red_team_data:   DatosRedTeam {           # QUÉ se encontró
    origen:                  FuenteRedTeam  # nuclei | amass | shodan | hibp | github_secrets | nmap | manual | otro
    activo_detectado:        str            # URL, IP, dominio, nombre del secreto…
    evidencia:               str            # link o snapshot a la prueba
    vector_ataque:           str            # descripción del riesgo técnico
    dificultad_explotacion:  Severidad      # informativa | baja | media | alta | critica
    cve_relacionado:         str | None     # CVE si aplica
  }

  blue_team_data:  DatosBlueTeam | None {   # CÓMO está protegido (opcional)
    shadow_it:        bool                  # ¿está en inventario?
    estado_defensa:   str                   # "Sin EDR", "WAF configurado"…
  }

  compliance_data: DatosCompliance | None { # QUÉ NORMA incumple (output del Traductor)
    marcos_aplicables:    [MarcoNormativo]  # iso_27001_2022 | ens_2022 | nis2 | dora | nist_csf_2 | pci_dss_4
    controles_incumplidos: [str]            # ["A.8.20", "A.8.22"]
    cita_normativa:        str              # texto exacto del control
    justificacion:         str              # razonamiento LLM
    impacto_legal:         Severidad        # gravedad normativa
    accion_mitigacion:     str              # qué hacer exactamente
    evidencia_auditoria:   str              # texto listo para dossier
  }
}
```

---

## 6. El Traductor Simbiótico (el corazón del proyecto)

Es el componente que **diferencia ROSETTA de un Excel con controles**.

### ¿Por qué no es solo "preguntar al LLM"?

Sin RAG, el LLM inventa controles que no existen o cita artículos incorrectos.
ROSETTA usa **Retrieval-Augmented Generation**:

```
Hallazgo → Query semántica → ChromaDB (corpus normativo vectorizado)
                                  ↓
                    Top-5 fragmentos reales del corpus
                                  ↓
                    LLM razona SOLO sobre esos fragmentos
                    (regla dura: no inventes controles)
                                  ↓
                    Tool-use fuerza schema DatosCompliance
                    (nunca texto libre, siempre JSON validado)
```

### Los marcos soportados actualmente

| Marco | Estado en corpus | Notas |
|-------|-----------------|-------|
| ISO 27001:2022 | ⚠️ Corpus pendiente de cargar | Requiere texto; ISO cobra por PDF oficial |
| ENS 2022 | ⚠️ Corpus pendiente | BOE público, gratuito |
| NIS2 | ⚠️ Corpus pendiente | EUR-Lex público |
| DORA | ⚠️ Corpus pendiente | EUR-Lex público |
| NIST CSF 2.0 | ⚠️ Corpus pendiente | NIST.gov público |
| PCI-DSS 4.0 | ⚠️ Corpus pendiente | Requiere registro gratuito |
| RGPD | ⚠️ Corpus pendiente | EUR-Lex público |

> ⚠️ **Punto crítico**: Sin corpus cargado, el RAG no devuelve fragmentos y el Traductor
> trabaja sin contexto real. Esto reduce la calidad de la traducción.
> El comando para cargar corpus es: `uv run rosetta load-corpus <marco> corpus/<marco>/`

---

## 7. Lo que existe HOY en el código (estado real)

### ✅ Implementado y funcional

| Módulo | Archivo | Qué hace |
|--------|---------|----------|
| Modelos Pydantic | `core/models.py` | Todos los tipos del sistema definidos |
| Traductor Simbiótico | `core/traductor.py` | Pipeline RAG + LLM completo, anti-alucinación |
| RAG | `core/rag.py` | ChromaDB con búsqueda por marco y filtrado |
| Grafo Neo4j | `core/graph.py` | Nodos/relaciones, consultas Cypher, dossier Markdown |
| Procedure Drift | `core/drift.py` | Detector de desviación procedimiento ↔ realidad |
| Diff Analyzer | `core/diff_analyzer.py` | Analiza diffs de PR para CI/CD gate |
| LLM Claude | `llm/claude.py` | Cliente Anthropic con tool-use y async |
| LLM Ollama | `llm/ollama.py` | Cliente Ollama para desarrollo sin coste |
| LLM OpenAI | `llm/openai.py` | Cliente OpenAI compatible |
| LLM Factory | `llm/factory.py` | Selección automática por variable de entorno |
| API REST | `api/main.py` | FastAPI con 5 endpoints |
| Dashboard | `api/dashboard.py` | Panel web embebido (HTML/JS vanilla) |
| Adaptador Nuclei | `adapters/red/nuclei.py` | Orquestación de Nuclei vía subprocess |
| Adaptador Amass | `adapters/red/amass.py` | Esqueleto (pendiente implementación completa) |
| CLI | `cli/main.py` | Comandos translate, load-corpus, version |

### ⚠️ Implementado pero incompleto

| Elemento | Problema |
|----------|----------|
| Corpus normativo | Los archivos de corpus no están cargados en ChromaDB todavía |
| Grafo Neo4j en dashboard | Existe el grafo pero el dashboard no lo visualiza |
| Adaptador Amass | Solo esqueleto, sin implementación real |
| Blue Team adapters | Solo interfaces, sin implementación |

### ❌ No implementado aún

| Elemento | MVP objetivo |
|----------|-------------|
| Adaptador Wazuh | MVP-4 |
| GitHub Action para CI/CD gate | MVP-7 |
| Panel Procedure Drift en dashboard | MVP-8 |
| Autenticación en la API | MVP-8+ |
| Persistencia de sesión (SQLite) | MVP-8+ |
| Multi-tenant | MVP-8+ |

---

## 8. Los endpoints de la API hoy

| Método | Ruta | Qué hace |
|--------|------|----------|
| GET | `/health` | Estado de la API y versión |
| GET | `/dashboard` | Dashboard web (Panel 1, 2 y 3) |
| POST | `/translate` | **Traduce un hallazgo** a evidencia normativa |
| GET | `/findings` | Lista hallazgos de la sesión (paginado) |
| GET | `/compliance/state/{marco}` | Estado de cumplimiento por marco |
| POST | `/analyze-diff` | Analiza diff de PR para CI/CD gate |

**Nota importante**: los endpoints existen y funcionan. El dashboard (Panel visual) es la
interfaz web sobre estos endpoints. Los problemas actuales del dashboard están documentados
en el plan de mejora.

---

## 9. El Dashboard hoy — 3 paneles

```
┌────────────────────────────┬────────────────────────────┐
│  Panel 1                   │  Panel 2                   │
│  Traducir hallazgo         │  Estado de cumplimiento    │
│  ─────────────────         │  ─────────────────────     │
│  Textarea JSON             │  Selector de marco         │
│  Selector de marcos        │  Barras de controles más   │
│  Botón "Traducir"          │  incumplidos               │
│  Resultado con tabla       │  Distribución severidad    │
│  (controles, cita,         │                            │
│   mitigación)              │                            │
│                            │                            │
│  ⚠️ BUG: errores de        │  ✅ Funciona               │
│  validación poco claros    │                            │
└────────────────────────────┴────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│  Panel 3 — Hallazgos de sesión (ancho completo)          │
│  ──────────────────────────────────────────────          │
│  Tabla con: ID · Activo · Origen · Controles · Impacto   │
│  Badges de severidad coloreados                          │
│  Botón "Refrescar"                                       │
│                                                          │
│  ⚠️ BUG: grafo Neo4j no visible aquí                     │
│  ⚠️ BUG: Gate CI/CD no tiene panel propio                │
└──────────────────────────────────────────────────────────┘
```

---

## 10. Procedure Drift — la "killer feature" según el mentor

**Problema real que resuelve:**

Las empresas escriben procedimientos de seguridad para pasar auditorías.
Luego la realidad operativa evoluciona y nadie actualiza los procedimientos.
El auditor llega, ve el procedimiento escrito, ve la realidad... y hay un GAP.
Ese GAP es una no-conformidad. Nadie lo detecta hasta que llega la auditoría.

**Cómo lo resuelve ROSETTA:**

```
Procedimiento escrito (PDF/MD):
  "Las cuentas inactivas >90 días se desactivan automáticamente."

Observaciones reales (logs de Wazuh):
  - "Cuenta admin_backup sin actividad desde hace 180 días — activa"
  - "15 cuentas de empleados que salieron hace >90 días — activas"

Resultado del DriftDetector:
  drift_detectado: true
  descripcion: "El procedimiento indica desactivación automática en 90 días
               pero los logs muestran 15 cuentas activas con >90 días de inactividad"
  fragmento_afectado: "Las cuentas inactivas >90 días se desactivan automáticamente"
  redaccion_propuesta: "Las cuentas inactivas >90 días deben desactivarse.
                        Actualmente el proceso es manual — se recomienda implementar
                        script automático o habilitar política en Active Directory."
  controles_afectados: ["A.5.18", "A.9.2.6"]
  impacto: "alta"
```

**Estado actual:** El módulo `core/drift.py` está implementado. No tiene panel en el dashboard todavía.

---

## 11. El Grafo Neo4j — la memoria del sistema

```
Modelo de datos en Neo4j:

(:Activo {nombre: "servidor.example.com"})
    │
    └─[:AFECTADO_POR]─►(:Hallazgo {
            id: "SEC-A1B2C3D4",
            severidad: "alta",
            timestamp: "2026-04-21T10:30:00Z"
          })
              │
              └─[:INCUMPLE]─►(:Control {
                      id: "A.8.20",
                      nombre: "Seguridad en redes"
                    })
                        │
                        └─[:PERTENECE_A]─►(:Marco {nombre: "iso_27001_2022"})
```

**Para qué sirve:**

- "¿Qué controles de ISO 27001 tienen más hallazgos este mes?" → `controles_mas_incumplidos()`
- "¿Qué activos tienen hallazgos críticos abiertos?" → `hallazgos_por_activo()`
- "Genera el dossier de auditoría para ISO 27001" → `exportar_dossier()`
- Visualización de la red de relaciones en el dashboard (pendiente)

**Estado actual:** Neo4j funciona. Se conecta si `NEO4J_URI` está en `.env`.
Sin Neo4j, el sistema usa los hallazgos de sesión en memoria (fallback automático).

---

## 12. El Gate de CI/CD — protección en el pipeline de desarrollo

**Problema que resuelve:**

Con IA generando código (vibe coding), es fácil que un desarrollador acepte un
PR que tiene una clave hardcodeada, logs excesivos de datos personales, o cifrado
débil. Eso es un incumplimiento normativo. ROSETTA lo detecta antes del merge.

**Cómo funciona:**

```
PR en GitHub
    │
    ▼
GitHub Action llama a POST /analyze-diff
con el diff del PR
    │
    ▼
DiffAnalyzer divide el diff en hunks
    │
    ▼
Para cada hunk: Traductor Simbiótico analiza
si introduce incumplimientos
    │
    ▼
Si severidad >= umbral configurado:
    bloquear: true → PR bloqueado con comentario Markdown
    (tabla con archivo, línea, control incumplido, acción)

Si todo OK:
    bloquear: false → PR puede continuar
```

**Estado actual:** El endpoint `POST /analyze-diff` funciona. No tiene panel en el dashboard.
La GitHub Action no está creada todavía (MVP-7).

---

## 13. Los LLMs soportados

ROSETTA no está atado a un proveedor:

| Proveedor | Config `.env` | Cuándo usarlo |
|-----------|--------------|---------------|
| **Claude (Anthropic)** | `LLM_PROVIDER=claude` + `ANTHROPIC_API_KEY=...` | Producción, mejor calidad |
| **Ollama (local)** | `LLM_PROVIDER=ollama` + `OLLAMA_MODEL=llama3.1:8b` | Desarrollo sin coste |
| **OpenAI** | `LLM_PROVIDER=openai` + `OPENAI_API_KEY=...` | Alternativa |

---

## 14. El roadmap de MVPs

```
MVP-0 · Scaffold                    ✅ Completado
MVP-1 · Traductor sobre ISO 27001   ⚠️  Implementado, falta cargar corpus
MVP-2 · Grafo Neo4j                 ⚠️  Implementado, falta conectar al dashboard
MVP-3 · Segundo marco: ENS          ⚠️  Código listo, falta corpus ENS
MVP-4 · Adaptador Nuclei real       ⚠️  Esqueleto implementado
MVP-5 · Procedure Drift             ⚠️  Implementado, sin UI en dashboard
MVP-6 · API REST + Dashboard        ✅  Funcional (con los 3 bugs conocidos)
MVP-7 · Gate CI/CD                  🔲  Endpoint existe, Action no creada
MVP-8+ · NIS2, DORA, multi-tenant   🔲  Pendiente
```

---

## 15. Cómo arrancar el sistema

```powershell
# 1. Asegúrate de tener el .env configurado
#    Mínimo necesario: ANTHROPIC_API_KEY o LLM_PROVIDER=ollama

# 2. Arrancar el servidor
cd C:\Users\WorkStation\Desktop\Rosetta
uv run uvicorn rosetta.api.main:app --reload

# 3. Abrir el dashboard en el navegador
start http://localhost:8000/dashboard

# 4. (Opcional) Ver la documentación Swagger automática
start http://localhost:8000/docs

# 5. (Opcional) Conectar Neo4j con Docker
docker-compose up -d
# Añadir al .env:
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=rosetta_dev
```

---

## 16. Comparación visión ↔ realidad

| Lo que describes que quieres | Estado actual |
|------------------------------|---------------|
| Pegar cualquier JSON de hallazgo y traducirlo | ✅ Funciona, pero errores de validación poco claros |
| Ver qué controles se incumplen más (por marco) | ✅ Panel 2 funciona |
| Ver historial de hallazgos traducidos | ✅ Panel 3 funciona |
| Ver el grafo Neo4j en el dashboard | ❌ No existe todavía (plan de mejora lo incluye) |
| Usar el Gate de CI/CD desde el dashboard | ❌ El endpoint existe pero no tiene panel |
| Hacer todo desde el dashboard (sin CLI) | ⚠️ Parcial — falta panel grafo y panel CI/CD |
| Procedure Drift visible en el dashboard | ❌ El motor existe pero sin UI |
| Exportar dossier de auditoría | ✅ Via `grafo.exportar_dossier()`, sin botón en dashboard |

---

## 17. Los tres problemas concretos del dashboard que hay que arreglar

### Bug 1 — No puedo pegar otros JSON para probar
**Causa:** El textarea tiene un ejemplo fijo. Si pegas un JSON con valores de enum incorrectos
(ej. `"origen": "scanner"` en vez de `"origen": "nuclei"`), el servidor devuelve un error 422
pero el mensaje no te dice qué campo falló ni qué valores son válidos.

**Solución planeada:** Dropdown con 5 plantillas de ejemplo + validación client-side
que muestra qué valores son válidos antes de enviar al servidor.

### Bug 2 — El grafo Neo4j no se ve
**Causa:** No existe ningún endpoint `GET /graph/data` ni código frontend que renderice
nodos/aristas. Solo hay datos tabulares.

**Solución planeada:** Nuevo endpoint + panel con vis.js para renderizar la red de
Activos → Hallazgos → Controles → Marcos.

### Bug 3 — El Gate CI/CD no tiene interfaz
**Causa:** El endpoint `POST /analyze-diff` existe pero el dashboard no lo expone.

**Solución planeada:** Panel 5 colapsable con textarea para diff, resultado en tabla
y botón para copiar el comentario Markdown de PR.

---

## 18. Flujo completo en un diagrama

```
ENTRADA                   NÚCLEO                        SALIDA
─────────                 ──────                        ──────

Nuclei JSON  ──────────►  NucleiAdapter
                              │ DatosRedTeam
Shodan data  ──────────►  ShodanAdapter ──────────────► HallazgoMaestro
                                                              │
HIBP breach  ──────────►  HIBPAdapter                        │
                                                              ▼
Manual JSON  ──────────────────────────────────────►  TraductorSimbiótico
(dashboard Panel 1)                                         │  ▲
                                                            │  │ Top-5 fragmentos
                                                            ▼  │
                                                       ChromaDB (RAG)
                                                       ISO27001/ENS/NIS2
                                                            │
                                                            ▼
                                                         LLM (Claude/Ollama)
                                                         Tool-use → DatosCompliance
                                                            │
                                                            ▼
                                                       Neo4j Graph ──────────► Dashboard Panel 4
                                                            │                  (grafo visual)
                                                            │
                              ┌─────────────────────────────┤
                              │                             │
                              ▼                             ▼
                         API REST                    Dossier Markdown
                              │                      (auditoría externa)
                    ┌─────────┴──────────┐
                    │                    │
                    ▼                    ▼
              Dashboard web        GitHub Action
              Panel 1,2,3          CI/CD Gate
              (+ 4,5 planeados)    (POST /analyze-diff)

Procedimiento
interno (MD) ──────────────────────────────────────► DriftDetector ──► Dashboard Panel 6 (planeado)
+ Logs Wazuh                                         LLM compara y
                                                     propone update
```

---

*Generado automáticamente leyendo todo el código fuente del proyecto el 2026-04-21.*
*Para el plan de mejora del dashboard ver: `.gemini/antigravity/brain/.../implementation_plan.md`*
