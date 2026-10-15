# Hoja de grabación · vídeo P3 (17:40)

Orden e identificadores de `data/fuentes/estructura_video.md` (7 bloques). Narración completa:
`docs/P3_VIDEO_SCRIPT.md`. Comandos numerados: `~/.rosetta/grabacion/comandos.txt` (fuera del
repo). Tiempos medidos en el ensayo automático del **2026-10-15** contra `9ce6942` (GPU de 16 GB,
Ollama `qwen2.5:14b` en caliente). Las respuestas del LLM cambian de una ejecución a otra: los
controles concretos pueden no coincidir con los del ensayo.

> **Recuento.** La estructura habla de 26 RF y 12 RNF (38). La matriz (`P3_MATRIZ.md`) y
> `P3_REQUISITOS.md` tienen **25 RF** (RF-01 a RF-19 y RF-20a a RF-20f) y 12 RNF: **37**. El
> guion usa 25 + 12; la estructura cubre los 37.

## Antes de pulsar REC

1. **Entorno**: ya está en limpio (down -v, laboratorio, corpus de 229 fragmentos, restart y seed
   12/12). `docker compose --profile lab ps` → app y neo4j `healthy`, lab-objetivo `Up`.
2. **Git Bash** en la raíz del repo: bloque 0 de `comandos.txt` (`COMPOSE_FILE` con el override de
   grabación y `TOKEN=$(bash ~/.rosetta/grabacion/token.sh)`). `token.sh` usa el refresh token: no
   cuenta como login. Repetirlo si han pasado más de 30 min.
3. **Modelo**: cargado sin caducidad. `curl -s localhost:11434/api/ps` debe listar `qwen2.5:14b`.
   Si no, una traducción cualquiera: la primera en frío tarda ~60 s.
4. **Plan director pregenerado** (48 s en el ensayo, más de 40): ventana de incógnito →
   `localhost:8000/dashboard` → login → «Plan Director» → «Generar Plan Director» (~40-50 s). Dejarla
   abierta. Respaldo: `~/.rosetta/grabacion/pregenerado/plan_director.png`.
5. **Dashboard principal en la pantalla de login.** Si entra sin pedir credenciales, pulsar «Cerrar
   sesión» (abajo a la izquierda).
6. **Para pegar** (en `~/.rosetta/grabacion/`): `alertas_wazuh.json`, `copilot_pregunta.txt`,
   `copilot_contexto.txt`, `drift_procedimiento.txt`, `drift_observaciones.txt`. El PDF de RF-05 es
   `auditoria_techserv_ficticia.pdf`.
7. **pytest** ya ejecutado: `pytest_cov.txt` (556 passed, 1 skipped, 85 %).
8. **Límites de la API** (contador en memoria): 5 logins por minuto y 5 `/audit/start` por hora. La
   grabación usa 2 auditorías (laboratorio e IP privada). Para repetir tomas: `docker compose restart
   app` pone los contadores a cero sin perder corpus ni hallazgos (healthy en ~12 s).

## Pestañas y ventanas

1. Diagrama: `docs/memoria/diagramas/componentes.svg` (en el navegador)
2. Matriz: `github.com/MichaelJTG/Rosetta/blob/main/docs/P3_MATRIZ.md`
3. `http://localhost:8000/dashboard` (login)
4. `http://localhost:8000/docs`
5. `github.com/MichaelJTG/Rosetta/actions` (último run en verde)
6. `github.com/MichaelJTG/Rosetta` (README, apartado de instalación)
7. Ventana de incógnito con el Plan Director ya generado

## 1. Presentación · 0:00 (1:00)

| Momento | Punto [ID] | Pantalla | Qué hacer | Espera |
|---|---|---|---|---|
| 0:00 | Quién eres y qué es ROSETTA [—] | Cámara o pestaña 1 | Nombre, proyecto individual autorizado. Problema: tiempo entre hallazgo y evidencia normativa | — |

## 2. Requisitos · 1:00 (1:00)

| Momento | Punto [ID] | Pantalla | Qué hacer | Espera |
|---|---|---|---|---|
| 1:00 | Requisitos de la P1 y cambios [—] | Pestaña 2 | 25 RF + 12 RNF. RF-20 partido en seis, Shodan/HIBP a roadmap, evaluación del Traductor nueva, despliegue retirado | — |

## 3. Arquitectura · 2:00 (1:30)

| Momento | Punto [ID] | Pantalla | Qué hacer | Espera |
|---|---|---|---|---|
| 2:00 | Diagrama de componentes [—] | Pestaña 1 | FastAPI + dashboard, RAG ChromaDB, LLM intercambiable (Ollama local, Groq probado), Neo4j opcional, SQLite. IA frente a determinista | — |

## 4. Demostración · 3:30 (9:40)

| Momento | Punto [ID] | Pantalla | Qué escribir / pulsar | Medido |
|---|---|---|---|---|
| 3:30 | Login y dashboard [RF-15, RF-12] | Pestaña 3 | `auditor-demo` / `cambia-esta-clave-de-prueba` → señalar los 16 paneles del menú | 4 s · ✅ 16 |
| 4:00 | Traducir un hallazgo [RF-01, RF-02, RF-03] | «Traducir» → «+ Traducir hallazgo» | Origen `manual` · dificultad `baja` · activo `fw-perimetral.techserv.example` · evidencia «CVE-2024-3400: RCE sin autenticación en PAN-OS (GlobalProtect). CVSS 10. Explotación activa en el firewall perimetral de TechServ.» · vector «Petición HTTP manipulada contra el portal GlobalProtect expuesto a Internet» · marcos ISO 27001:2022 + ENS 2022 → «Traducir hallazgo». Señalar controles, cita y justificación | 25 s · ✅ |
| 5:00 | Dosier [RF-04] | «Hallazgos» | Organización «TechServ (caso ficticio)» → «Generar dosier» → **«↓ Descargar PDF»** (el primer botón es el Markdown) | 2 s · ✅ |
| 5:30 | Ingesta de PDF [RF-05] | «Ingesta PDF» | Seleccionar `auditoria_techserv_ficticia.pdf` → «Extraer hallazgos» | 16 s · ✅ 4 hallazgos |
| 6:10 | Modo Auditoría [RF-06] | «Modo Auditoría» | Objetivos `http://lab-objetivo` · marcar nuclei y nmap · alcance «Laboratorio propio local, contenedor lab-objetivo, autorizado por el autor para la demo de la P3» → «Iniciar auditoría». Narrar mientras llega el progreso | 43 s · ✅ 18 hallazgos |
| 7:10 | Blue Team y correlación [RF-07, RF-08] | «Blue Team» | Pegar `alertas_wazuh.json` → «Ingestar alertas». Señalar cobertura Red↔Blue | 2 s · ✅ 3 alertas, 3 % |
| 7:40 | Validador [RF-09] | Git Bash | Comando **1** (`validar.json` + curl). Narrar mientras responde | 33 s · ✅ |
| 8:20 | Copilot normativo [RF-10] | «Copilot» | Pegar `copilot_pregunta.txt` y `copilot_contexto.txt` → «Preguntar al Copilot». Señalar citas y confianza | 11 s · ✅ |
| 9:00 | Procedure drift [RF-11] | «Procedure Drift» | Pegar `drift_procedimiento.txt` y `drift_observaciones.txt` → «Detectar drift» | 14 s · ✅ |
| 9:30 | Swagger [RF-13] | Pestaña 4 | Desplazar la lista | 1 s · ✅ 30 operaciones |
| 9:40 | Gate CI/CD [RF-14] | Git Bash | Comando **2** (`cat` del diff + curl) → `bloquear: true` | 7 s · ✅ |
| 10:10 | Historial [RF-16] | «Hallazgos» | Botón «en progreso» de un hallazgo activo | 2 s · ✅ |
| 10:30 | Grafo [RF-17] | «Grafo» | Se carga solo; clic en un nodo | 4 s · ✅ 57 nodos |
| 10:50 | CLI [RF-18] | Git Bash | Comando **3** | 2 s · ✅ |
| 11:05 | Cumplimiento por marco [RF-19] | «Cumplimiento» | Chip «ISO 27001:2022» | 2 s · ✅ |
| 11:25 | Catálogo de controles [RF-20a] | «Catálogo de Controles» | Clic en una fila (p. ej. A.8.20) → modal; «Cancelar» | 1 s · ✅ 18 controles |
| 11:40 | Roadmap de vulnerabilidades [RF-20b] | «Roadmap Vuln.» | Plazo, propietario y estado de cada hallazgo (corregido en `81e76fa`). Comando **3b**: ya no necesario | 0,2 s · ✅ |
| 11:55 | Evidencias [RF-20c] | «Panel de Evidencias» | Decir que es mapeo determinista, sin IA | 1 s · ✅ |
| 12:10 | Gap analysis [RF-20d] | «Pre-Gap Análisis» | ISO 27001 → «Analizar con mis datos» | 23 s · ✅ |
| 12:40 | Plan director [RF-20e] | Ventana de incógnito | **Pregenerado antes de grabar; decirlo** | 48 s en directo |
| 12:55 | Análisis de riesgos [RF-20f] | «Análisis de Riesgos» | «Generar análisis» **nada más acabar el gap**, y enseñar el plan mientras corre | 35 s · ✅ |

Riesgos tarda 35 s y su hueco es de 15 s. Lanzado al acabar el gap (≈12:37), el resultado llega
hacia 13:12, mientras se cuenta el plan. Si se lanza a las 12:55, el bloque se alarga unos 20 s.

## 5. Errores y seguridad · 13:10 (2:05)

| Momento | Punto [ID] | Pantalla | Comando | Medido |
|---|---|---|---|---|
| 13:10 | Fuerza bruta [RNF-07] | Git Bash | **4** → `401 401 401 401 401 429` (≥ 1 min tras el último login) | 2 s · ✅ |
| 13:35 | PDF falso y de 21 MB [B-9] | Git Bash | **5** → 400 y 413 | 1 s · ✅ |
| 13:55 | Path traversal [B-1] | Git Bash | **6** → `..\` da 400; `../` da 404 | 1 s · ✅ (ver nota) |
| 14:10 | IP privada [RNF-08] | Git Bash | **7** → 400 «dirección privada/reservada» | 1 s · ✅ |
| 14:30 | Cabeceras [RNF-11] | Git Bash | **8** → 200 con CSP, X-Frame-Options, nosniff, Referrer-Policy | 1 s · ✅ |
| 14:45 | Neo4j parado [RNF-01] | Git Bash + «Cumplimiento» | **9a**; en el dashboard, chip «ENS 2022» (responde en ~5 s); **9b** | 7 s + 5 s + 1 s · ✅ |

## 6. Calidad y evaluación · 15:15 (1:25)

| Momento | Punto [ID] | Pantalla | Qué enseñar | Medido |
|---|---|---|---|---|
| 15:15 | CI en verde [RNF-03, RNF-04, RNF-06, RNF-10, RNF-12] | Pestaña 5 | Jobs «Lint, type-check, test (3.11 y 3.12)» (ruff, mypy strict, pytest), «Scan for leaked secrets» (gitleaks), «Dependency CVE audit (pip-audit)» | — |
| 15:40 | Tests y cobertura [RNF-02] | Git Bash | `tail -8 ~/.rosetta/grabacion/pytest_cov.txt` → 556 passed, 85 % | 85 s antes de grabar · ✅ |
| 15:55 | Evaluación del Traductor [—] | Git Bash | Comando **11** | 0 s · ✅ |
| 16:20 | Latencia [RNF-09] | Git Bash | Comando **12** → p50 6,95 s, p95 11,02 s, máx. 59,88 s | 0 s · ✅ |
| 16:30 | Instalación desde cero [RNF-05] | Pestaña 6 | README: requisitos de memoria y alternativa con Groq | — |

## 7. Cierre · 16:40 (1:00)

Limitaciones: Modo Auditoría solo contra laboratorio, Validador opcional, latencia máxima en frío,
sin roles, Shodan/HIBP pendiente, 5 marcos con corpus base, despliegue retirado y Groq con límite
gratuito.

## No funciona (código congelado: se cuenta como limitación)

- ~~**Panel «Roadmap Vuln.» (RF-20b) siempre vacío.**~~ **Corregido en `81e76fa` (G-9)**: el
  endpoint acepta `estado=all` y el panel lista todos los hallazgos. El comando 3b (plan B por
  API) ya no es necesario.
- **Path traversal con `../`** responde 404 y no 400: la ruta con `/` no llega al endpoint (la
  rechaza el router). El 400 de la lista blanca se ve con `..\`. Las dos peticiones se rechazan.
- **`curl -I`** responde 405 porque `/health` no admite HEAD (las cabeceras de seguridad salen
  igual). Por eso el comando 8 usa `curl -s -D - -o /dev/null`.

## Ojo al grabar

- **Validador por curl**: con `-d '...'` y tildes, Git Bash envía el cuerpo en cp1252 y la API
  responde 400 «There was an error parsing the body». El comando 1 usa `validar.json` (UTF-8).
  Alternativa: casilla «Activar Validador» del modal de Traducir. En el ensayo aprobó
  (`valida: true`); el 14/10 rechazó: el veredicto varía.
- **Drift**: en el ensayo propuso «60 días» y citó `A.12.1`, que es un identificador de ISO 27001:2013,
  no de 2022. Si vuelve a salir, no apoyarse en esa cita.
- **Traducción**: los controles de ENS aparecen aunque «Marcos aplicables» solo muestre ISO 27001.
- **Plan y riesgos** con el estado recién sembrado: 38 s y 21 s. Con los hallazgos de la grabación
  (PDF, auditoría, Gate) suben a 48 s y 35 s, como en el ensayo.
