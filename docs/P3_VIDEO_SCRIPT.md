# docs/P3_VIDEO_SCRIPT.md — Guión de demostración P3

> Duración estimada: **12–14 minutos**.
> Herramientas: navegador + terminal. Docker corriendo con `docker compose up -d`.
> Caso ficticio: empresa TechServ S.L. (datos generados con `seed_demo.py`).

---

## Antes de grabar

El `.env` (o un override de compose) necesita `ROSETTA_USER`, `ROSETTA_PASSWORD`,
`ROSETTA_JWT_SECRET`, `ROSETTA_AUDIT_ALLOWLIST=lab-objetivo` y
`OLLAMA_URL=http://host.docker.internal:11434`. Tiempos medidos en el ensayo del
2026-10-14 (GPU de 16 GB, Ollama `qwen2.5:14b`):

```bash
# Levantar el stack con el laboratorio del Modo Auditoría (~3,5 min con --build)
docker compose --profile lab up -d

# Esperar a que la app esté healthy (~20 s)
docker compose ps       # app: healthy, neo4j: healthy

# Cargar el corpus (~25 s) y reiniciar la app
docker compose exec app rosetta load-corpus all corpus
# → ✓ 229 fragmentos indexados en ChromaDB (7 marcos)
docker compose restart app

# Poblar la demo con hallazgos ficticios (~2 min: 12 pasos)
docker compose exec app python scripts/seed_demo.py
```

Abrir el navegador en `http://localhost:8000/dashboard`.

---

## Sección 1 · Contexto y problema que resuelve ROSETTA (0:00 – 1:00)

**[Pantalla: diapositiva o fondo neutro con texto]**

> «Cuando un equipo técnico encuentra una vulnerabilidad — un CVE, una mala configuración,
> un hallazgo de auditoría — sabe que hay un problema. Lo que no sabe es *qué artículo del
> ENS*, *qué control de ISO 27001* ni *qué requisito de NIS2* incumple.
> Esa traducción la hace hoy un consultor de cumplimiento, a mano, en días.
> ROSETTA la hace en segundos.»

**[Pantalla: diagrama de tres capas del CLAUDE.md]**

- Capa de sensores (commodity): Nmap, Nuclei, Wazuh, PDF de auditoría
- Capa núcleo (IP propia): Traductor Simbiótico — LLM + RAG sobre corpus normativo
- Capa de salida: API REST, CLI, Dashboard, Gate CI/CD

> «No es un escáner. No compite con Vanta ni Drata. Es el Traductor Simbiótico
> entre lo técnico y lo legal, con soporte multi-marco simultáneo.»

---

## Sección 2 · Login y dashboard (1:00 – 1:45)

**[Pantalla: navegador → http://localhost:8000/dashboard]**

1. Ir a `http://localhost:8000/dashboard`.
2. Introducir credenciales de demo.
3. Mostrar el panel de inicio: métricas de cumplimiento por marco.
4. Señalar los 16 paneles del menú lateral.

> «ROSETTA tiene 31 endpoints HTTP; 30 están documentados en Swagger. El dashboard da acceso
> visual a los más relevantes. Vamos directamente a lo que importa: la traducción.»

---

## Sección 3 · Traducción de hallazgo técnico (1:45 – 3:30) ← RF-01, RF-02

**[Pantalla: panel «Traducir» del dashboard]**

Panel «Traducir» → «+ Traducir hallazgo». Origen `manual`, dificultad `baja`, activo
`fw-perimetral.techserv.example`, evidencia «CVE-2024-3400: RCE sin
autenticación en PAN-OS (GlobalProtect). CVSS 10. Explotación activa en el
firewall perimetral de TechServ.», vector «Petición HTTP manipulada contra el
portal GlobalProtect expuesto a Internet», marcos ISO 27001:2022 y ENS 2022 →
«Traducir hallazgo» (~12 s). No usar `rosetta translate` en directo: el CLI recibe la
ruta de un JSON, no texto libre.

**Mostrar la respuesta:**
- `controles_incumplidos`: los que devuelva el LLM; no son deterministas (en el ensayo: `A.8.20` y `mp.s.2`, uno de cada marco)
- `cita_normativa`: fragmento literal del corpus
- `justificacion`: por qué aplica ese control

> «El Traductor usa RAG sobre el corpus. Recupera los fragmentos más relevantes
> y fuerza al LLM a responder con IDs de control estructurados mediante tool-use.
> Si el LLM intenta responder fuera del esquema Pydantic, el sistema lo rechaza.
> No hay respuesta de texto libre: solo JSON validado.»

**Mostrar el modo validado** (~30 s; en el ensayo el Validador rechazó la
traducción, `valida: false`):

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"auditor-demo","password":"cambia-esta-clave-de-prueba"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -X POST "http://localhost:8000/translate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hallazgo": {"origen": "manual", "activo_detectado": "vpn.techserv.example",
       "evidencia": "4 cuentas de administración sin MFA",
       "vector_ataque": "Acceso VPN de administradores solo con contraseña",
       "dificultad_explotacion": "media"},
       "marcos": ["ens_2022"], "validar": true}'
```

> «Con `"validar": true` en el cuerpo, el agente Validador actúa como segunda opinión sobre la
> traducción. Añade latencia, pero está disponible para casos críticos.
> El cliente controla el coste-calidad.»

---

## Sección 4 · Pipeline multi-marco y corpus (3:30 – 4:15) ← RF-02, RF-03

**[Pantalla: terminal]**

```bash
docker compose exec app rosetta load-corpus all corpus
```

Mostrar (salida del comando; `GET /health` solo devuelve `status` y `version`):
- 229 fragmentos indexados
- 7 marcos → ISO 27001:2022, ENS 2022, NIS2, DORA, RGPD, NIST CSF 2.0, PCI-DSS 4.0

> «El corpus incluye el Anexo II completo del RD 311/2022 (73 medidas ENS),
> los 93 controles del Anexo A de ISO 27001:2022, y cinco marcos adicionales.
> ChromaDB filtra por `framework_id` para que cada traducción recupere solo
> los fragmentos del marco solicitado.»

---

## Sección 5 · Evaluación del Traductor — Bloque C (4:15 – 7:00)

**[Pantalla: terminal → eval/reports/]**

> «Aquí está el resultado más importante de esta práctica desde el punto de vista
> de la calidad del sistema. El harness mide el Traductor contra un ground truth externo:
> el SoA real del caso TechServ, creado por el equipo docente.
> La regla es estricta: prohibido usar salida de IA como ground truth.
> Si midiéramos el modelo contra sí mismo, estaríamos midiendo coherencia,
> no calidad.»

### 5a · Modo correspondencia (73 medidas ENS → ISO 27001:2022)

```bash
cat eval/reports/2026-10-04T22-14-23_correspondencia_eval_report.md | head -25
```

```
Casos evaluados: 73/73
Precision macro-avg: 0.4078
Recall macro-avg:    0.2164
F1 macro-avg:        0.2648
Tasa alucinación:    0.0000  ←
Tasa discrepancia:   0.6250
```

> «El número clave es la tasa de alucinación: **cero**.
> En los 73 casos, el Traductor nunca citó un control que no existe en ISO 27001:2022.
> Eso es lo que el RAG garantiza: el LLM solo puede recuperar controles del corpus.»

> «La discrepancia es distinta de la alucinación. Un control alucinado es uno inventado,
> inexistente en la norma — eso sería un error grave y no ocurrió ninguna vez.
> Un control discrepante es un control real de ISO 27001, pero distinto al que el
> ground truth asociaba a esa medida ENS. El Traductor se equivoca en *cuál* control
> es el más relevante — eso explica el F1=0.26 —, pero nunca inventa identificadores.
> Esta distinción es la que justifica el diseño RAG: sin corpus, habría alucinaciones.»

> «Mejor familia con más de un caso: "Control de acceso", con F1 = 0,55.
> Peores: "Protección de las comunicaciones" y "Protección de los soportes de
> información", con F1 = 0 en sus 9 casos: el LLM elige controles reales de
> ISO 27001, pero no los que asocia el SoA.»

### 5b · Modo hallazgo (16 hallazgos ficticios → ISO 27001:2022)

```bash
cat eval/reports/2026-10-04T22-23-10_hallazgo_eval_report.md | head -25
```

```
Casos evaluados: 16/16
Precision macro-avg: 0.3125
Recall macro-avg:    0.2812
F1 macro-avg:        0.2813
Tasa alucinación:    0.0000  ←
Tasa discrepancia:   0.7568
```

> «16 hallazgos técnicos ficticios — CVEs, malas configuraciones, PII en logs.
> Mismo resultado: cero alucinación.
> 0 % en 73 + 16 = **89 casos en total**.
> El RAG actúa como barrera. El LLM ve solo fragmentos del corpus;
> si el control no está en el corpus, no puede aparecer en la respuesta.»

### 5c · Comparativa Traductor solo vs Traductor + Validador

```bash
cat eval/reports/2026-10-11T15-28-50_correspondencia_eval_report.md | grep -A 9 "Comparativa"
```

```
Casos con validación:            73
Aprobados por Validador:         39
Rechazados por Validador:        34
F1 medio aprobados:          0.3615
F1 medio rechazados:         0.1706
Precision rechazo @F1<0.5:   0.8235
```

> «El Validador es un agente independiente que recibe la traducción y emite un
> veredicto. La pregunta es: ¿rechaza traducciones que realmente están mal?
> Sobre los 73 casos, las aprobadas tienen un F1 medio de 0,36 y las
> rechazadas de 0,17: discrimina. De cada 100 rechazos, 82 eran traducciones
> malas.»

> «Pero no basta como filtro. Aprueba 23 de las 51 traducciones malas y
> rechaza 6 de las 22 buenas. Quedarse solo con las aprobadas sube el F1 de
> 0,27 a 0,36 a costa de descartar casi la mitad. Es una segunda opinión;
> no sustituye la revisión del auditor.»

---

## Sección 6 · Seguridad del producto — Bloque B (7:00 – 9:00)

> «La seguridad de ROSETTA como producto — no lo que mide, sino lo que protege
> al propio sistema — se documentó en un modelo de amenazas STRIDE con 10 bloques.»

### B-4 · Rate limiting por IP real (no por XFF forjable)

```bash
# Seis logins fallidos seguidos desde el mismo cliente (límite: 5 por minuto)
for i in 1 2 3 4 5 6; do
  curl -s -o /dev/null -w "%{http_code} " \
    -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong"}'
done
# → 401 401 401 401 401 429
# Cuentan todos los logins del último minuto, también el del TOKEN:
# lanzar el bucle al menos 1 minuto después del último login.
```

> «El cliente que supera el límite ve 429. El segundo cliente, con otra IP,
> empieza su contador desde cero. Antes de este fix, la app usaba X-Forwarded-For,
> que un atacante puede forjar. Ahora usa X-Real-IP, que nginx pone y el cliente
> no puede sobrescribir.»

### B-9 · Protección de `POST /ingest/pdf`

```bash
# 1. Fichero sin magic bytes PDF → 400
printf "esto no es un pdf" > /tmp/fake.pdf
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8000/ingest/pdf \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/fake.pdf"
# → 400

# 2. PDF que supera el límite de 20 MB → 413
python -c "open('/tmp/large_test.pdf','wb').write(b'%PDF-1.4\n' + b'0' * 21 * 1024 * 1024)"
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8000/ingest/pdf \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/large_test.pdf"
# → 413
```

> «Tres defensas en capas. Primero: magic bytes. Se leen los primeros 4 bytes
> del stream — si no empiezan por `%PDF`, el servidor devuelve 400 antes de leer
> el fichero completo. Segundo: límite de tamaño configurable — 20 MB por defecto,
> rechaza con 413 sin cargar el fichero entero en memoria.
> Tercero: límite de páginas — 500 por defecto, rechazo 422 con pdfplumber
> antes de procesarlo. Cuatro tests cubren los tres casos.»

### B-1 y B-2 (breve)

> «B-1 corrige path traversal en la generación de dosiers: el nombre del fichero
> pasa por validador Pydantic con regex `[A-Za-z0-9_-]` máximo 64 chars.
> B-2 corrige XSS almacenado: toda salida del LLM que va a innerHTML en el
> dashboard pasa por la función `esc()`.»

---

## Sección 7 · Dosier y otras funcionalidades (9:00 – 10:30) ← RF-04, RF-06, RF-11

### Generación de dosier (RF-04)

**[Pantalla: panel «Hallazgos» → botón «Generar dosier»]**

1. Escribir la organización: «TechServ (caso ficticio)».
2. Clicar «Generar dosier» (~1 s). El dosier incluye todos los hallazgos de la
   sesión (31 en el ensayo, con los de la auditoría); no se elige uno.
3. Clicar «↓ Descargar PDF» → abre el PDF: portada, resumen ejecutivo, tabla de controles.

> «El dosier está en formato de auditoría. Entregable directo al auditor externo.»

### Modo Auditoría Red Team (RF-06)

**[Pantalla: panel «Auditoría»]** Objetivo `http://lab-objetivo`, marcar Nuclei
y Nmap, declaración de alcance «Laboratorio propio local, contenedor
lab-objetivo, autorizado por el autor para la demo de la P3» → iniciar (~45 s;
en el ensayo, 18 hallazgos: 17 de Nuclei y 1 de Nmap). Requiere
`ROSETTA_AUDIT_ALLOWLIST=lab-objetivo` y el perfil `lab` levantado.

> «Nmap y Nuclei corren dentro del contenedor. La validación de alcance bloquea
> IPs privadas fuera de la allowlist. El progreso llega por WebSocket.»

### Detección de procedure drift (RF-11)

**[Pantalla: panel «Drift»]**

> «ROSETTA compara el procedimiento escrito contra el comportamiento observado
> por los sensores. Si el procedimiento dice "todos los sistemas se parchean
> mensualmente" pero Wazuh detecta un servidor sin parches desde hace 90 días,
> eso es drift — el insight central del mentor Carlos Gómez Pintado.»

---

## Sección 8 · CI, cobertura y calidad (10:30 – 11:45) ← Bloque A

**[Pantalla: GitHub → Actions tab]**

> «CI en GitHub Actions: matriz Python 3.11 y 3.12. Cada push ejecuta ruff,
> mypy strict sobre src/ sin errores, pytest con cobertura, gitleaks,
> y pip-audit sobre el uv.lock.»

```bash
# ~75 s: lanzarlo antes y mostrar el final, o cortar la espera
uv run pytest --cov=rosetta --cov-branch --cov-report=term-missing -q 2>&1 | tail -5
# 556 passed, 1 skipped · TOTAL 85 % (core/ 92 %)
```

mypy, en el log del job de CI, no en local: con el Python 3.13 del `.venv` local
falla al leer los stubs de numpy (sintaxis `type` de Python 3.12).

> «556 tests, cobertura global del 85 % y del 92 % en core/, por encima del
> 80 % que pide RNF-02. pdf_ingestion.py sigue en 76 %, documentado en
> P3_REQUISITOS.md. La honestidad sobre los límites del sistema es parte
> de la calidad de la entrega.»

**[Pantalla: incidente INC-01]**

> «Tuvimos un incidente real: una contraseña de prueba se escribió como literal
> en un test y se publicó. Se detectó, se rotaron las credenciales en producción
> y se documentó como INC-01 en P3_SEGURIDAD.md. Después se limpió el historial
> con git filter-repo, pero el incidente sigue documentado: es más honesto
> contarlo que ocultarlo.»

---

## Sección 9 · Cierre (11:45 – 13:00)

**[Pantalla: repo GitHub con badge CI verde]**

> «Resumen:
> - 26 RF: 24 ✅, 2 🟡.
> - 12 RNF: 11 ✅, 1 🟡 (RNF-09: de 20 traducciones, solo la primera, con el modelo en frío, supera 30 s; p95 = 11 s).
> - Bloque B: 10/11 bloques. B-9 implementado en esta entrega.
> - Eval: 0% de controles inventados en 89 casos. El Validador discrimina
>   (F1 0,36 en aprobadas frente a 0,17 en rechazadas; precisión de rechazo
>   0,82), pero aprueba 23 de las 51 traducciones malas.
> - El código está en GitHub, la CI está en verde, el corpus tiene 7 marcos.»

---

## Notas técnicas para la grabación

| Punto | Detalle |
|-------|---------|
| Token de demo | `docker compose exec app python -c "import httpx; r=httpx.post('http://localhost:8000/auth/login',json={'username':'auditor-demo','password':'cambia-esta-clave-de-prueba'}); print(r.json()['access_token'][:40]+'...')"` |
| LLM en demo | Usar Ollama local (`LLM_PROVIDER=ollama`) para evitar costes y latencia de red |
| Corpus pre-cargado | Verificar con `rosetta load-corpus all corpus` antes de grabar → 229 fragmentos, y reiniciar la app |
| Caso TechServ | `scripts/seed_demo.py` crea hallazgos ficticios listos para mostrar |
| Duración LLM | Ensayo del 2026-10-14: traducción ~12 s, con Validador ~30 s, Drift ~14 s, auditoría del laboratorio ~45 s. No acelerar el vídeo en esas partes |
| Hoja de grabación | `docs/P3_HOJA_GRABACION.md`: orden de pestañas, textos de cada formulario y duración de cada bloque |
| Validador | Mostrar primero sin `"validar": true`, luego con él, para contrastar latencia y veredicto |
| B-9 demo | Preparar fichero no-PDF (`printf "fake" > /tmp/fake.pdf`) y PDF grande para el 413 |
| Eval reports | Tener terminales con los MD ya abiertos en `less`, no leerlos en directo |
