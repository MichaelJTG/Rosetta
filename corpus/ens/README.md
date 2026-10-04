# Corpus ENS — Esquema Nacional de Seguridad (RD 311/2022)

**Fuente principal**: Real Decreto 311/2022, de 3 de mayo (BOE-A-2022-7191).
Texto del Anexo II transcrito del Boletín Oficial del Estado — legislación española de libre difusión.

**Fuente de los mapeos ISO 27001:2022**: CCN-STIC 825 «Esquema Nacional de Seguridad — Guía de Adecuación»,
publicada por el Centro Criptológico Nacional (CCN). Documento público. Los identificadores de control ISO
que aparecen en la columna `iso_27001_2022` de `ens-2022-anexo-ii.yaml` se derivan de esa guía.
No se reproduce el texto de la CCN-STIC 825 en este repositorio.

**Fuente de los mapeos en el ground truth de evaluación** (`eval/ground_truth/ens_iso.json`):
SoA del caso TechServ, facilitado por el equipo docente de la asignatura como material
del ejercicio práctico. Los controles ISO aparecen como listas de identificadores; el
texto del SoA no se reproduce. Ver `eval/ground_truth/README.md`.

**Licencia del corpus YAML**: Dominio público — legislación española de libre difusión.
**Formato**: YAML compatible con `CorpusLoader._cargar_yaml_intuitem`
**Controles**: 73 medidas del Anexo II (todas las familias ENS)

## Cobertura

| Dimensión | Categoría | Controles incluidos |
|-----------|-----------|---------------------|
| Marco organizativo | org | org.1, org.2, org.3, org.4 |
| Marco operacional | op.pl | op.pl.1, op.pl.4 |
| Marco operacional | op.acc | op.acc.1–2, op.acc.4–6 |
| Marco operacional | op.exp | op.exp.1–4, op.exp.7–10 |
| Marco operacional | op.ext | op.ext.1 |
| Marco operacional | op.mon | op.mon.1, op.mon.2 |
| Medidas de protección | mp.if | mp.if.1 |
| Medidas de protección | mp.per | mp.per.1, mp.per.3 |
| Medidas de protección | mp.com | mp.com.1–3 |
| Medidas de protección | mp.si | mp.si.1, mp.si.2, mp.si.5 |
| Medidas de protección | mp.sw | mp.sw.1, mp.sw.2 |
| Medidas de protección | mp.info | mp.info.3, mp.info.4, mp.info.6 |
| Medidas de protección | mp.s | mp.s.1, mp.s.2, mp.s.4 |
| Medidas de protección | mp.eq | mp.eq.1, mp.eq.3 |

## Mapeo clave ISO 27001:2022 ↔ ENS

| Hallazgo | ISO 27001 | ENS |
|----------|-----------|-----|
| Credencial expuesta | A.8.24 | mp.si.2, mp.info.4 |
| Sin MFA | A.8.5 | op.acc.5 |
| Puerto RDP abierto | A.8.20 | mp.com.1, op.exp.2 |
| Sin logging | A.8.16 | op.exp.8, op.exp.9, op.mon.1 |
| Sin parchear (CVE) | A.8.8 | op.exp.4 |
| Acceso sin proceso formal | A.5.18 | op.acc.4, org.4 |

## Uso

```bash
rosetta load-corpus ens_2022 corpus/ens/
```
