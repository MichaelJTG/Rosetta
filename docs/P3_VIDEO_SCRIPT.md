# docs/P3_VIDEO_SCRIPT.md — Guion del vídeo P3

> Duración prevista: **17:40**, en los 7 bloques de `data/fuentes/estructura_video.md`.
> **Vídeo final: unos 25 minutos** (enlace en la portada de la memoria). Los minutos de cada
> requisito están en la matriz (memoria, apartado 9, y `P3_MATRIZ.md`); RF-11, RF-14, RF-15 y
> RF-18 no aparecen en el vídeo (por tiempo).
> **Parte 2** (errores y seguridad, calidad y cierre): grabada el 16/10 como continuación, con
> diapositivas y comandos en directo, y unida a la parte 1 sin sus últimos 8 segundos. Empieza en
> el 20:40 del vídeo final: errores y seguridad 21:09, calidad 23:23 y cierre 24:21.
> Hoja de una página: `docs/P3_HOJA_GRABACION.md`. Comandos numerados:
> `~/.rosetta/grabacion/comandos.txt` (fuera del repo, junto con el PDF ficticio, el diff del
> Gate y el TOKEN). Caso ficticio: TechServ S.L. Tiempos medidos en el ensayo automático del
> **2026-10-15** contra `9ce6942` (GPU de 16 GB, Ollama `qwen2.5:14b` en caliente). Los
> controles que devuelve el LLM cambian de una ejecución a otra.

---

## Preparación (no se graba)

Override local `~/.rosetta/compose.grabacion.yml` (usuario de demo, secreto JWT,
`ROSETTA_AUDIT_ALLOWLIST=lab-objetivo`, `OLLAMA_URL=http://host.docker.internal:11434`).
En Git Bash, desde la raíz del repo:

```bash
export COMPOSE_FILE="docker-compose.yml;C:/Users/WorkStation/.rosetta/compose.grabacion.yml"
docker compose --profile lab down -v                        # 5 s
docker compose --profile lab up -d --build                  # 20 s con caché; app healthy en ~15 s
docker compose exec -T app rosetta load-corpus all corpus   # 15 s → 229 fragmentos, 7 marcos
docker compose restart app                                  # healthy en ~12 s
docker compose exec -T app python scripts/seed_demo.py      # 95-160 s → 12 pasos correctos
```

Después: bloque 0 de `comandos.txt` (TOKEN), modelo cargado, Plan Director generado en una
ventana de incógnito y el dashboard principal en la pantalla de login (hoja, «Antes de pulsar REC»).

---

## Bloque 1 · Presentación (0:00 – 1:00)

### Quién eres y qué es ROSETTA [—] · 1:00

**[Pantalla: cámara o diagrama]**

> «Soy [nombre] y presento ROSETTA, mi proyecto individual de la Práctica 3, con la autorización
> del equipo docente para hacerlo en solitario.
> El problema es el tiempo que pasa entre un hallazgo técnico y su evidencia normativa. Un
> escáner encuentra un CVE en un firewall; el equipo técnico sabe que hay un problema, pero no
> qué control de ISO 27001 ni qué medida del ENS incumple. Esa traducción la hace hoy un
> consultor, a mano, y tarda días.
> ROSETTA la hace en segundos y con la cita literal de la norma. Está pensado para auditores,
> CISOs y responsables de cumplimiento. No es un escáner ni un SIEM: orquesta herramientas que
> ya existen y traduce lo que encuentran.»

---

## Bloque 2 · Requisitos (1:00 – 2:00)

### Requisitos de la P1 y cambios [—] · 1:00

**[Pantalla: `docs/P3_MATRIZ.md` en GitHub]**

> «La matriz de trazabilidad relaciona cada requisito con su commit, sus tests y su evidencia.
> Son 25 funcionales, de RF-01 a RF-19 y de RF-20a a RF-20f, y 12 no funcionales.
> Respecto a la P1 hay cuatro cambios. RF-20 era un único "panel avanzado" y se ha partido en
> seis requisitos para poder trazarlos: catálogo, roadmap, evidencias, gap analysis, plan
> director y análisis de riesgos. Los adaptadores de Shodan y HIBP pasan al roadmap: solo existe
> el tipo de origen, no el adaptador. La evaluación cuantitativa del Traductor es nueva. Y el
> despliegue en servidor propio se ha retirado: la evaluación se hace en local con Docker.
> Según la matriz: 23 funcionales cumplidos y 2 parciales, el Modo Auditoría y el Validador;
> 11 no funcionales cumplidos y 1 parcial, la latencia.»

---

## Bloque 3 · Arquitectura (2:00 – 3:30)

### Diagrama de componentes [—] · 1:30

**[Pantalla: `docs/memoria/diagramas/componentes.svg`]**

> «Tres capas. Abajo, los sensores: Nmap y Nuclei para la parte ofensiva, alertas de Wazuh para
> la defensiva y los informes PDF de auditoría. No los modifico: los orquesto por línea de
> comandos.
> En el centro, el núcleo: una API FastAPI que sirve también el dashboard. El Traductor usa RAG:
> el corpus de 7 marcos está indexado en ChromaDB, se recuperan los fragmentos del marco pedido y
> el LLM solo puede responder llamando a una función con un esquema Pydantic. El LLM es
> intercambiable: Ollama en local, que es lo que vais a ver, o cualquier API compatible con
> OpenAI, como Groq, que también he probado. Neo4j guarda el grafo activo-control, pero es
> opcional: si se cae, la API sigue. El historial de hallazgos va en SQLite.
> Arriba, las salidas: API REST, CLI, dashboard, dosier en PDF y el gate de CI/CD.
> Qué hace la IA: traducir, validar, el Copilot, el drift, el Gate, leer los PDF, el gap
> analysis, el plan director y las amenazas del análisis de riesgos. Qué es determinista: los
> escáneres, la correlación con Wazuh, el dosier, el panel de evidencias, el cumplimiento por
> marco, el catálogo y el grafo.»

---

## Bloque 4 · Demostración (3:30 – 13:10)

### Login y dashboard [RF-15, RF-12] · 0:30 · medido 4 s

**[Pantalla: `localhost:8000/dashboard`, pantalla de login]** Usuario `auditor-demo`, contraseña
`cambia-esta-clave-de-prueba` → «Entrar».

> «El acceso usa JWT: un token de 30 minutos y otro de refresco. El login está limitado a cinco
> intentos por minuto. Estos son los 16 paneles: análisis, inteligencia, asistencia, datos y los
> seis de gestión que salen de RF-20.»

### Traducir un hallazgo [RF-01, RF-02, RF-03] · 1:00 · medido 25 s

**[Pantalla: «Traducir» → «+ Traducir hallazgo»]** Origen `manual`, dificultad `baja`, activo
`fw-perimetral.techserv.example`, evidencia «CVE-2024-3400: RCE sin autenticación en PAN-OS
(GlobalProtect). CVSS 10. Explotación activa en el firewall perimetral de TechServ.», vector
«Petición HTTP manipulada contra el portal GlobalProtect expuesto a Internet», marcos ISO
27001:2022 y ENS 2022 → «Traducir hallazgo».

> «Un hallazgo real de 2024: ejecución remota sin autenticación en el firewall de Palo Alto.
> Pido dos marcos a la vez. Mientras responde: el Traductor recupera del corpus los fragmentos
> de cada marco y obliga al modelo a contestar con controles estructurados. No hay texto libre.»

Al llegar la respuesta (en el ensayo: `mp.s.2`, `mp.s.2.1`, `A.8.20`, `A.8.21`):

> «Controles incumplidos de los dos marcos, la cita literal de cada uno sacada del corpus, la
> justificación y la acción de mitigación. El impacto legal sale como crítico.»

### Dosier [RF-04] · 0:30 · medido 2 s

**[Pantalla: «Hallazgos»]** Organización «TechServ (caso ficticio)» → «Generar dosier» →
«↓ Descargar PDF» (el segundo botón; el primero es el Markdown).

> «El dosier reúne todos los hallazgos de la sesión en formato de auditoría: portada, resumen
> ejecutivo y tabla de controles. Lo genera ReportLab, sin IA. Es el entregable para el auditor.»

### Ingesta de PDF de auditoría [RF-05] · 0:40 · medido 16 s

**[Pantalla: «Ingesta PDF»]** Seleccionar `~/.rosetta/grabacion/auditoria_techserv_ficticia.pdf`
→ «Extraer hallazgos».

> «Esto es un informe de auditoría ficticio de TechServ, de una página, con cuatro hallazgos:
> un Struts vulnerable en el portal de proveedores, copias del ERP sin cifrar, una cuenta
> compartida de administrador y logs de base de datos que no se centralizan. pdfplumber saca el
> texto y el LLM extrae cada hallazgo con su activo y su evidencia.»

Resultado del ensayo: 4 hallazgos, 1 página, modo `texto`.

> «Los cuatro quedan registrados como hallazgos de la sesión, igual que los de los escáneres.»

### Modo Auditoría contra el laboratorio [RF-06] · 1:00 · medido 43 s

**[Pantalla: «Modo Auditoría»]** Objetivos `http://lab-objetivo`, marcar nuclei y nmap, alcance
«Laboratorio propio local, contenedor lab-objetivo, autorizado por el autor para la demo de la
P3» → «Iniciar auditoría».

> «Solo escaneo un laboratorio propio: un contenedor nginx sin puertos publicados, en la red
> interna de Docker. La declaración de alcance es obligatoria, y la API rechaza IPs privadas que
> no estén en una lista de permitidos; lo veremos en el bloque de seguridad.
> El progreso llega por WebSocket mientras corren Nuclei y Nmap, y cada hallazgo se registra.»

Resultado del ensayo: «Auditoría completada: 18 hallazgo(s), 0 error(es)».

### Blue Team y correlación [RF-07, RF-08] · 0:30 · medido 2 s

**[Pantalla: «Blue Team»]** Pegar `alertas_wazuh.json` → «Ingestar alertas».

> «Tres alertas de Wazuh en su formato JSON: fuerza bruta por RDP y un intento por SSH. ROSETTA
> las normaliza y las cruza con los hallazgos ofensivos por activo. La cobertura dice qué
> hallazgos tienen además una alerta defensiva: aquí, 1 de 33. Es determinista, sin IA.»

### Validador [RF-09] · 0:40 · medido 33 s

**[Pantalla: Git Bash]** Comando 1: `cat` de `validar.json` y el curl a `/translate`.

> «Otra traducción, ahora con validar a true: cuatro cuentas de administración de la VPN sin
> doble factor, contra el ENS. Un segundo agente, el Validador, revisa la traducción y da un
> veredicto con su confianza y su razonamiento. Tarda más, por eso es opcional.»

Al llegar (en el ensayo `valida: true`, confianza 1,0; el 14/10 rechazó una traducción
parecida):

> «Aquí la aprueba. No siempre lo hace: en la evaluación lo veremos con números.»

### Copilot normativo [RF-10] · 0:40 · medido 11 s

**[Pantalla: «Copilot»]** Pregunta de `copilot_pregunta.txt`: «¿Qué exige el ENS para el acceso
remoto de los administradores? ¿Es obligatorio el doble factor?». Contexto de
`copilot_contexto.txt`: «Organismo público, sistema de categoría MEDIA, administración por VPN.»
→ «Preguntar al Copilot».

> «Pregunta libre sobre el corpus. La respuesta cita las medidas de las que sale y da un nivel
> de confianza calculado según cuánto del corpus ha recuperado.»

### Procedure drift [RF-11] · 0:30 · medido 14 s

**[Pantalla: «Procedure Drift»]** Pegar `drift_procedimiento.txt` (PRO-IAM-001) y
`drift_observaciones.txt` → «Detectar drift».

> «Esta es la idea de mi mentor, Carlos Gómez Pintado: los procedimientos escritos se separan de
> la realidad y nadie los actualiza. El procedimiento dice que las cuentas sin uso se deshabilitan
> a los 90 días; Wazuh ve 37 cuentas sin login desde hace más de 180. ROSETTA marca el drift, el
> fragmento afectado, una redacción propuesta y los controles.»

En el ensayo: «Drift detectado · ALTA». Ojo: propuso «60 días» y citó `A.12.1` (ISO 27001:2013);
si vuelve a salir, no apoyarse en esa cita.

### Swagger [RF-13] · 0:10 · medido 1 s

**[Pantalla: `localhost:8000/docs`]**

> «Toda la API está documentada con OpenAPI: 30 operaciones en Swagger.»

### Gate CI/CD [RF-14] · 0:30 · medido 7 s

**[Pantalla: Git Bash]** Comando 2: `cat` de `pr_gate.diff` y el curl a `/analyze-diff`.

> «Un pull request ficticio en el cliente de pagos: añade una clave en claro, registra el número
> de tarjeta en el log y desactiva la verificación TLS. El Gate analiza cada bloque del diff
> contra PCI-DSS e ISO 27001 y responde si hay que bloquear el PR, con un comentario en Markdown
> listo para publicar.»

En el ensayo: `bloquear: true` por `verify=False` (PCI-DSS Req. 3.5, cifrado del PAN en tránsito).

### Historial de hallazgos [RF-16] · 0:20 · medido 2 s

**[Pantalla: «Hallazgos»]** Botón «en progreso» en un hallazgo activo.

> «Cada hallazgo tiene un ciclo de vida: activo, en progreso, solucionado. El historial se guarda
> en SQLite y no se borra: los resueltos se archivan.»

### Grafo [RF-17] · 0:20 · medido 4 s

**[Pantalla: «Grafo»]** Se carga al abrirlo (57 nodos y 53 aristas en el ensayo). Clic en un nodo.

> «Cada activo afectado, unido a los controles que incumple. Sale de Neo4j; si no está, de
> memoria.»

### CLI [RF-18] · 0:15 · medido 2 s

**[Pantalla: Git Bash]** Comando 3: `rosetta version` y `rosetta --help`.

> «Lo mismo desde la terminal: traducir, cargar el corpus, generar el dosier, escanear o detectar
> drift.»

### Cumplimiento por marco [RF-19] · 0:20 · medido 2 s

**[Pantalla: «Cumplimiento»]** Chip «ISO 27001:2022».

> «Estado agregado por marco: hallazgos, distribución de severidad y los controles más
> incumplidos.»

### Catálogo de controles [RF-20a] · 0:15 · medido 1 s

**[Pantalla: «Catálogo de Controles»]** Clic en una fila (p. ej. A.8.20) → modal → «Cancelar».

> «El catálogo de controles: estado, responsable, comentarios y evidencias de cada uno.»

### Roadmap de vulnerabilidades [RF-20b] · 0:15 · ✅

**[Pantalla: «Roadmap Vuln.»]**

> «Cada vulnerabilidad con su plazo, su propietario y su estado. Al ensayar el vídeo este panel
> salía vacío: pedía los hallazgos con el filtro "all" y el endpoint no lo reconocía. Lo corregí y
> añadí un test para ese caso.»

### Evidencias [RF-20c] · 0:15 · medido 1 s

**[Pantalla: «Panel de Evidencias»]**

> «Cada herramienta, ligada a los controles para los que aporta evidencia. Es un mapeo
> determinista, sin IA: verde con dos fuentes o más, amarillo con una, rojo sin ninguna.»

### Gap analysis [RF-20d] · 0:30 · medido 23 s

**[Pantalla: «Pre-Gap Análisis»]** ISO 27001:2022 → «Analizar con mis datos».

> «El gap analysis lo hace el LLM en directo: para cada control del catálogo decide, con los
> hallazgos de la sesión, si se cumple, se cumple en parte, no se cumple o no hay datos.»

En el ensayo: 18 controles, 0 cumplen, 1 parcial, 6 no cumplen, 11 sin datos. Al terminar, abrir
«Análisis de Riesgos» y pulsar «Generar análisis» antes de ir al plan.

### Plan director [RF-20e] · 0:15 · pregenerado (48 s en directo)

**[Pantalla: ventana de incógnito con el Plan Director ya generado]**

> «El plan director tarda cerca de un minuto, así que lo he generado antes de grabar: acciones
> priorizadas con esfuerzo en personas-día y coste a 450 euros el día.»

En el ensayo: 13 acciones, 26,5 personas-día, 11.925 €. Respaldo:
`~/.rosetta/grabacion/pregenerado/plan_director.png`.

### Análisis de riesgos [RF-20f] · 0:15 · medido 35 s

**[Pantalla: «Análisis de Riesgos»]** Lanzado al acabar el gap.

> «Y el análisis de riesgos, en directo: cada activo de la sesión, sus amenazas, probabilidad
> por impacto en una escala de 1 a 25 y un tratamiento.»

En el ensayo: 15 activos, riesgo medio 14,5.

---

## Bloque 5 · Errores y seguridad (13:10 – 15:15)

### Fuerza bruta: 401 ×5 y 429 [RNF-07] · 0:25 · medido 2 s

**[Pantalla: Git Bash]** Comando 4 (al menos 1 minuto después del último login).

> «Seis logins fallidos seguidos. Los cinco primeros, 401; el sexto, 429. El límite se aplica
> por IP real: la cabecera X-Forwarded-For, que el cliente puede falsificar, no cuenta.»

### PDF falso (400) y PDF de 21 MB (413) [B-9] · 0:20 · medido 1 s

**[Pantalla: Git Bash]** Comando 5.

> «La ingesta mira los primeros bytes: un texto con extensión .pdf da 400. Y un PDF de 21 MB
> da 413: el límite es de 20 MB y se deja de leer en cuanto se pasa.»

### Path traversal en la descarga (400) [B-1] · 0:15 · medido 1 s

**[Pantalla: Git Bash]** Comando 6.

> «Pedir un informe con `..\` para salir del directorio: 400, nombre no válido. La descarga
> solo acepta nombres de una lista blanca y comprueba que la ruta no sale de la carpeta. Con
> `../` ni siquiera llega al endpoint: el router devuelve 404.»

### Escaneo a IP privada rechazado [RNF-08] · 0:20 · medido 1 s

**[Pantalla: Git Bash]** Comando 7.

> «Una auditoría contra 192.168.1.10: 400. Las IPs privadas y reservadas se bloquean salvo que
> el administrador las añada a la lista de permitidos, como el laboratorio de antes.»

### Cabeceras de seguridad [RNF-11] · 0:15 · medido 1 s

**[Pantalla: Git Bash]** Comando 8.

> «Content-Security-Policy, X-Frame-Options a DENY, nosniff y Referrer-Policy en todas las
> respuestas.»

### Neo4j parado: la app sigue [RNF-01] · 0:30 · medido 7 s + 5 s + 1 s

**[Pantalla: Git Bash y dashboard]** Comando 9a (`docker compose stop neo4j` y el curl a
`/compliance/state`) → en el dashboard, «Cumplimiento» → chip «ENS 2022» (responde en ~5 s) →
comando 9b (`docker compose start neo4j`).

> «Paro Neo4j. El panel de cumplimiento sigue respondiendo, con los datos en memoria de la sesión:
> la API detecta que el grafo no está y sigue sin él. Lo vuelvo a arrancar.»

Neo4j vuelve a estar *healthy* a los ~17 s.

---

## Bloque 6 · Calidad y evaluación (15:15 – 16:40)

### CI en verde [RNF-03, RNF-04, RNF-06, RNF-10, RNF-12] · 0:25

**[Pantalla: GitHub Actions, último run]**

> «Cada push pasa por cuatro jobs. Lint, tipos y tests en Python 3.11 y 3.12: ruff, mypy en modo
> estricto y pytest. gitleaks sobre todo el historial. Y pip-audit sobre las dependencias exactas
> del lockfile.»

### Tests y cobertura [RNF-02] · 0:15 · ejecutado antes (85 s)

**[Pantalla: Git Bash]** `tail -8 ~/.rosetta/grabacion/pytest_cov.txt`.

> «556 tests, 1 omitido, y un 85 % de cobertura global; el núcleo está en el 92 %.»

### Evaluación del Traductor [—] · 0:25

**[Pantalla: Git Bash]** Comando 11.

> «Medí el Traductor contra un ground truth externo, no contra otra IA: 73 medidas del ENS con su
> correspondencia en ISO 27001 y 16 hallazgos técnicos. En los 89 casos, cero controles
> inventados. Ojo: alucinación no es lo mismo que discrepancia. Una discrepancia es un control
> que existe pero no es el que esperaba la referencia, y ahí el F1 se queda en 0,26. El Validador
> acierta el 82 % de sus rechazos, pero aprueba 23 de las 51 traducciones malas: es una segunda
> opinión, no sustituye al auditor.»

### Latencia [RNF-09] · 0:10

**[Pantalla: Git Bash]** Comando 12.

> «Con Ollama, en 20 llamadas: mediana de 7 segundos, p95 de 11 y un máximo de 60, el de la
> primera llamada con el modelo en frío. Una de 20 pasa de 30 segundos.»

### Instalación desde cero [RNF-05] · 0:10

**[Pantalla: README en GitHub]**

> «El README se ha probado en un clon limpio. Indica cuánta memoria hace falta para el modelo
> local y, si no la hay, cómo usar Groq.»

---

## Bloque 7 · Cierre (16:40 – 17:40)

### Limitaciones y mejoras [—] · 1:00

**[Pantalla: repo en GitHub]**

> «Limitaciones. El Modo Auditoría solo lo he probado contra el laboratorio; un objetivo real
> necesita una autorización escrita. El Validador es opcional y no sustituye la revisión humana.
> La latencia máxima, en frío, pasa de 30 segundos. No hay roles: todos los usuarios tienen los
> mismos permisos. Shodan y HIBP siguen en el roadmap. De los 7 marcos, 5 tienen solo un corpus
> base. El despliegue en servidor propio está retirado. Groq funciona, pero su plan gratuito no
> aguanta el seed entero.
> Como mejoras: roles, los adaptadores pendientes, evaluar los otros cinco marcos y escanear la
> imagen Docker. Gracias.»

---

## Notas técnicas

| Punto | Detalle |
|-------|---------|
| Hoja de grabación | `docs/P3_HOJA_GRABACION.md`: momento de cada punto, textos de formulario, esperas medidas y lo que no funciona |
| Comandos | `~/.rosetta/grabacion/comandos.txt`, del 0 (TOKEN) al 12 (latencia), en el orden del vídeo |
| TOKEN | `TOKEN=$(bash ~/.rosetta/grabacion/token.sh)`: usa el refresh token (7 días) y no cuenta en el límite de logins |
| Límites | 5 logins/min y 5 `/audit/start`/hora, en memoria; `docker compose restart app` los pone a cero |
| Validador | Cuerpo en `validar.json`: con `-d` y tildes, Git Bash rompe la codificación (400). Alternativa: casilla «Activar Validador» del modal de Traducir |
| Pregenerado | Plan director (48 s en el ensayo): ventana de incógnito antes de REC; respaldo en `~/.rosetta/grabacion/pregenerado/` |
| No usar | `curl -I` (405: `/health` no admite HEAD); `rosetta translate "texto"` (el CLI espera un JSON); `mypy` en local (falla con el Python 3.13 del `.venv`; enseñarlo en la CI) |
