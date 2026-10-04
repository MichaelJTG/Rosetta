# eval/ground_truth — Ground truth de evaluación

Este directorio contiene las referencias de «respuesta correcta» usadas por
`eval/run_eval.py` para medir la calidad del Traductor Simbiótico.

---

## Ficheros

### `ens_iso.json` — 73 casos de correspondencia ENS → ISO 27001:2022

| Campo | Descripción |
|-------|-------------|
| `ens_id` | Identificador de la medida ENS (ej. `op.acc.1`) |
| `ens_nombre` | Nombre corto de la medida |
| `iso_27001_2022_control_ids` | Lista de controles ISO 27001:2022 que el SoA asocia a esa medida ENS |

**Fuente**: SoA del caso TechServ, facilitado por el equipo docente de la asignatura
como material del ejercicio práctico (Práctica 3 de Ciberseguridad Avanzada).
El texto del SoA no se reproduce. Solo se incluyen los identificadores de control ISO.

**Fuente secundaria (inspección)**: CCN-STIC 825 «Guía de Adecuación al ENS»,
publicada por el Centro Criptológico Nacional (CCN). Documento público.
Algunos mapeos se verificaron contra esta guía.

**Garantía de independencia**: el mapeo NO se generó con IA. Generarlo con el
propio modelo evaluado sería medir el modelo contra sí mismo.

**Licencia**: material docente; no redistribuir fuera del contexto de la asignatura.

---

### `ens_hallazgos_tecnicos.json` — 16 casos de hallazgo técnico → ISO 27001:2022

| Campo | Descripción |
|-------|-------------|
| `hallazgo_id` | Identificador del hallazgo (ej. `HT-01`) |
| `familia` | Familia ENS del hallazgo |
| `descripcion` | Descripción del hallazgo técnico ficticio |
| `revision` | `"pendiente"` — los controles ISO son provisionales |
| `hallazgo` | Objeto con `origen`, `activo_detectado`, `evidencia`, `vector_ataque`, `dificultad_explotacion` |
| `iso_27001_2022_control_ids` | Lista de controles ISO asignados manualmente (provisional) |
| `notas` | Razonamiento del mapeo |

**Fuente**: casos ficticios creados para P3. Empresa imaginaria «TechServ S.A.»,
uno por familia ENS, con datos sintéticos (dominios `.example`, IPs RFC 5737).

**Advertencia**: todos los casos llevan `"revision": "pendiente"`. Las asignaciones
de control ISO no han sido validadas contra CCN-STIC 825. Las métricas del modo
`--mode hallazgo` son indicativas hasta que se complete la revisión.

**Garantía de independencia**: los controles ISO se asignaron manualmente,
no mediante el LLM evaluado.

---

## Principio de construcción del ground truth

> **Prohibido generar el ground truth con IA.**
> El ground truth es la referencia con la que se mide el modelo.
> Si la misma IA genera la referencia, el eval mide la consistencia
> interna del modelo, no su alineación con el criterio normativo humano.
>
> Fuentes válidas: SoA facilitado por el docente, CCN-STIC 825,
> revisión manual por el autor.
