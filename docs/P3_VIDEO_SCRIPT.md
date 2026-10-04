# docs/P3_VIDEO_SCRIPT.md — Guión de demostración P3

> Duración estimada: 7–9 minutos.
> Herramientas: navegador + terminal. Docker corriendo con `docker compose up -d`.
> Caso ficticio: empresa TechServ S.L. (datos generados con `seed_demo.py`).

---

## Antes de grabar

```bash
# Levantar el stack
docker compose up -d

# Esperar a que la app esté healthy
docker compose ps       # rosetta: healthy

# Indexar el corpus (si no está ya)
rosetta load-corpus all corpus/
# → debe mostrar ≥ 166 fragmentos en 7 marcos

# Poblar la demo con hallazgos ficticios
uv run python scripts/seed_demo.py
```

Abrir el navegador en `http://localhost:8000/dashboard`.

---

## Sección 1 · Contexto (0:00 – 0:45)

**[Pantalla: diapositiva / texto]**

> ROSETTA es una plataforma de cumplimiento normativo que toma hallazgos técnicos
> arbitrarios y los traduce, en tiempo real, a evidencia de cumplimiento para
> ISO 27001:2022, ENS 2022, NIS2, DORA y otros marcos.
>
> No es un escáner. No es un SIEM. Es el Traductor Simbiótico entre lo técnico y lo legal.

**[Pantalla: diagrama de tres capas del CLAUDE.md]**

- Capa de sensores → Nmap, Nuclei, Wazuh, PDF
- Capa núcleo (IP) → Traductor + RAG + Neo4j
- Capa de salida → API, CLI, Dashboard, CI gate

---

## Sección 2 · Login y dashboard (0:45 – 1:30)

**[Pantalla: navegador]**

1. Ir a `http://localhost:8000/dashboard`.
2. Introducir credenciales de demo.
3. Mostrar el panel de inicio: métricas de cumplimiento por marco.
4. Mencionar los 16 paneles disponibles (señalar el menú lateral).

> «Desde aquí tenemos una visión continua del estado de cumplimiento de TechServ.»

---

## Sección 3 · Traducción de hallazgo técnico (1:30 – 3:00)  ← RF-01, RF-02

**[Pantalla: panel "Traducir" del dashboard o terminal]**

```bash
rosetta translate \
  "CVE-2024-3400: RCE sin autenticación en PAN-OS. CVSS 10. \
   Explotación activa en el firewall perimetral de TechServ."
```

**O vía panel web:** pegar el texto en el campo y pulsar «Traducir».

**Mostrar la respuesta:**
- `controles_incumplidos`: e.g. `["8.8", "8.19", "5.23"]`
- `cita_normativa`: fragmento literal del corpus
- `justificacion`: por qué aplica ese control
- Marcos cubiertos: ISO 27001:2022 y ENS 2022 simultáneamente

> «El Traductor Simbiótico usa RAG sobre el corpus normativo. Recupera los fragmentos
> más relevantes y fuerza al LLM a responder con IDs de control estructurados.
> Nunca responde fuera de esquema.»

---

## Sección 4 · Pipeline multi-marco (3:00 – 3:45)  ← RF-02, RF-03

**[Pantalla: panel "Controles" o respuesta JSON]**

1. Mostrar que la misma traducción devuelve controles de ISO 27001 **y** ENS 2022.
2. Abrir ChromaDB stats en `GET /health` → 166 fragmentos, 7 marcos indexados.

> «El corpus incluye RD 311/2022 Anexo II completo (73 medidas ENS), ISO 27001:2022,
> NIS2, DORA, RGPD, NIST CSF 2.0 y PCI-DSS 4.0.»

---

## Sección 5 · Generación de dosier (3:45 – 4:30)  ← RF-04

**[Pantalla: panel "Hallazgos" → botón «Generar dosier»]**

1. Clicar «Generar dosier» para el hallazgo del CVE.
2. Mostrar `POST /reports/generate` → nombre del fichero.
3. Clicar «Descargar» → abre el PDF en el navegador.
4. Mostrar: portada, resumen ejecutivo, tabla de controles, recomendaciones.

> «El dosier está en formato de auditoría. Se puede entregar directamente al equipo legal
> o al auditor externo. No hay trabajo manual de mapeo.»

---

## Sección 6 · Modo Auditoría Red Team (4:30 – 5:30)  ← RF-06, RNF-08

**[Pantalla: panel "Auditoría" o terminal]**

```bash
# POST /audit/start con laboratorio local (permitido por la allowlist)
curl -s -X POST http://localhost:8000/audit/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target": "127.0.0.1", "scope": ["127.0.0.1"]}'
```

**O panel web:** introducir IP de laboratorio y pulsar «Iniciar auditoría».

1. Mostrar WebSocket con progreso en tiempo real.
2. Mostrar que IPs privadas fuera de allowlist → `403 Forbidden` (RNF-08).

> «Nmap y Nuclei corren dentro del contenedor. La validación de alcance
> bloquea IPs privadas para evitar auditorías accidentales de producción.»

---

## Sección 7 · Métricas de evaluación — Bloque C (5:30 – 6:30)

**[Pantalla: terminal]**

```bash
# Mostrar resultado del eval ya ejecutado (de eval/reports/)
cat eval/reports/2026-10-04T21-18-39_eval_report.md
```

**Destacar:**
- Ground truth: 73 medidas ENS del SoA del profesor (no generado con IA)
- Precision macro-avg: 0.5625 · Recall: 0.2812 · F1: 0.3667
- Tasa de alucinación: 0.50 (Ollama qwen2.5:14b, 8 casos)
- Mejor familia: «Control de acceso» F1=0.73

> «Este harness mide la calidad del Traductor con un ground truth externo — el SoA
> real del profesor. Prohibido usar salida IA como ground truth: sería medir el modelo
> contra sí mismo.»

---

## Sección 8 · Panel de Cumplimiento y Copilot (6:30 – 7:30)  ← RF-10, RF-19

**[Pantalla: panel "Cumplimiento"]**

1. Mostrar estado agregado por marco (ISO 27001 / ENS).
2. Cambiar al panel "Copilot".
3. Escribir: `«¿Qué controles ENS aplican a la gestión de parches?»`
4. Mostrar respuesta con cita literal y nivel de confianza.

> «El Copilot responde con citas directas del corpus, no parafrasea.
> El campo confianza indica cuántos fragmentos relevantes respaldaban la respuesta.»

---

## Sección 9 · Cierre (7:30 – 8:00)

**[Pantalla: diagrama de arquitectura o repo en GitHub]**

> ROSETTA cumple los 26 RF y 12 RNF del enunciado, más los requisitos de seguridad
> del Bloque B. El código está en GitHub, la CI está en verde, y el corpus incluye
> los 7 marcos normativos del alcance.
>
> Los dos módulos en 🟡 (RNF-02 cobertura 77 %, RNF-09 tail latency) están
> documentados con sus razones y su estado real.

**Mostrar:**
- Repositorio GitHub → CI verde (badge)
- `docs/P3_REQUISITOS.md` en el repo

---

## Notas técnicas para la grabación

| Punto | Detalle |
|-------|---------|
| Token de demo | `docker compose exec rosetta uv run python -c "import httpx; r=httpx.post('http://localhost:8000/auth/login',json={'username':'admin','password':'<contraseña_nueva>'}); print(r.json()['access_token'][:40]+'...')"` |
| LLM en demo | Usar Ollama local (`LLM_PROVIDER=ollama`) para evitar costes y latencia de red |
| Corpus pre-cargado | Verificar con `GET /health` antes de grabar |
| Caso TechServ | `scripts/seed_demo.py` crea hallazgos ficticios listos para mostrar |
| Duración real | Las llamadas al LLM toman 5–20 s. No acelerar el vídeo en esas partes. |
