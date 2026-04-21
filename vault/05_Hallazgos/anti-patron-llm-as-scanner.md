---
title: Anti-patrón · LLM-as-scanner vs LLM-as-translator
tags: [hallazgo, anti-patron, narrativa, pitch, rosetta]
categoria: anti-patron
created: 2026-04-20
referencia_externa: https://github.com/zakirkun/deep-eye
licencia_referencia: MIT
---

# Anti-patrón · LLM-as-scanner vs LLM-as-translator

> Nota de contraste narrativo. Clarifica dónde ROSETTA coloca la IA frente a otros proyectos que también usan LLMs en seguridad.

## El anti-patrón: LLM-as-scanner

Ejemplo canónico: [zakirkun/deep-eye](https://github.com/zakirkun/deep-eye) (MIT, ~1k stars, 0 releases formales).

Descripción textual del README: *"An advanced AI-driven vulnerability scanner and penetration testing tool that integrates multiple AI providers (OpenAI, Grok, OLLAMA, Claude) with comprehensive security testing modules for automated bug hunting, intelligent payload generation, and professional reporting."*

**Qué hace**: mete el LLM **dentro del escáner** — genera payloads context-sensitive para SQLi/XSS/SSRF/XXE/etc., hace OSINT, reporta. ~45 vectores ofensivos.

**Por qué es un anti-patrón para el caso de ROSETTA**:
1. El LLM hace lo que herramientas deterministas (Nuclei, ZAP, Burp) ya hacen mejor, más barato y más rápido — solo que añade no-determinismo y coste.
2. No resuelve el dolor real que ve Carlos Gómez Pintado: **el hallazgo técnico existe; lo que falta es traducirlo a evidencia de control**.
3. Incrementa la superficie de ataque al proyecto (prompt injection desde target hostil → LLM que genera payload manipulado).

## El patrón de ROSETTA: LLM-as-translator

ROSETTA coloca la IA **después** del hallazgo técnico, no dentro del escáner:

```
[Nuclei / Wazuh / Amass / Shodan / ...]        (sensores deterministas, open-source)
            ↓  HallazgoMaestro
[LLM Translator + RAG multi-marco]              ← AQUÍ vive la IA de ROSETTA
            ↓  Traducciones
[Dossier multi-marco / Gate CI-CD / Dashboard]
```

Los sensores son commodity y se orquestan, no se reinventan (CLAUDE.md §4). La IA entra únicamente donde hay un problema no resuelto: convertir un hallazgo técnico arbitrario en controles de ISO/ENS/NIS2/DORA/RGPD con justificación auditable.

## Tabla de contraste (para pitch)

| Eje | LLM-as-scanner (deep-eye y similares) | LLM-as-translator (ROSETTA) |
|-----|--------------------------------------|-----------------------------|
| Dónde vive la IA | dentro del escáner | después del hallazgo |
| Qué resuelve | generar payloads | producir evidencia de cumplimiento |
| Herramientas sustituye | Nuclei, ZAP, Burp | nada — llena hueco vacío |
| Aporta valor cuando… | el escáner es malo | el escáner ya encontró el hallazgo |
| Riesgo por prompt injection | alto (target hostil manipula) | bajo (fragmentos RAG curados) |
| Coste por hallazgo | alto (LLM por cada payload) | bajo (LLM por cada traducción) |
| Audibilidad | opaca (LLM decide atacar) | trazable (citas a fragmentos normativos) |

## Talking points con Carlos / clientes / profesores

- *"Hay muchos proyectos que meten IA dentro del escáner. Nosotros la metemos después, donde realmente falta automatización: entre el hallazgo y la evidencia."*
- *"Nuestra IA no decide cómo atacar. Decide qué control del Anexo A se ha incumplido y por qué. Eso es auditable. Lo otro no."*
- *"Carlos lo dijo claro: el dolor no está en escanear, está en que los procedimientos divergen de la realidad. ROSETTA lo ataca ahí — ver [[05_Hallazgos/insight-carlos-procedure-drift]]."*

## Consecuencias prácticas para el diseño

1. **No meter generación de payloads** como feature del Traductor, ni siquiera como "nice-to-have".
2. **Adapters Red Team siempre orquestan herramientas deterministas** — nunca inyectan LLM en la capa de sensor.
3. Si alguna vez se añadiera deep-eye (u otro scanner-IA) como adaptador, sería **puramente vía CLI/API**, consumiendo su output como `DatosRedTeam` normalizado, sin acoplarnos a su estilo arquitectónico.

## Por qué esta nota existe

Porque un día alguien (mentor, profesor, inversor, contratante futuro) preguntará: *"¿y en qué os diferenciáis de \[deep-eye / PentestGPT / HackingBuddyGPT\]?"*. La respuesta debe ser inmediata y articulada. Esta nota es el guion.

## Enlaces

- [[MOC_Hallazgos]] · [[05_Hallazgos/referencia-decepticon]] (otra referencia externa, ofensiva)
- [[05_Hallazgos/insight-carlos-procedure-drift]] (dónde sí está el dolor)
- [[10_Agentes/MOC_Agentes]] · [[CLAUDE]] §2 (lo que ROSETTA NO es)
- URL referencia: https://github.com/zakirkun/deep-eye
