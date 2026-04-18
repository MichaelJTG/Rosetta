# Próximos pasos — cómo continuar con ROSETTA

> Guía operativa para seguir desde aquí. Todo lo que necesitas para arrancar con Claude Code en tu terminal y empezar el primer sprint funcional.

---

## 1. Prerrequisitos

Asegúrate de tener instalado:

- **Python 3.11 o superior**: `python --version`
- **uv** (gestor de paquetes moderno): https://docs.astral.sh/uv/getting-started/installation/
  - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **git**: https://git-scm.com/downloads
- **Claude Code CLI**: https://docs.claude.com/en/docs/claude-code
- **API key de Anthropic**: https://console.anthropic.com/ (necesaria para el Traductor)
- *(Opcional por ahora)* **Obsidian**: https://obsidian.md/ — para abrir el vault

## 2. Inicializar git y primer commit

Desde PowerShell, en `C:\Users\WorkStation\Desktop\Rosetta`:

```powershell
git init
git branch -M main
git add .
git commit -m "chore(scaffold): ROSETTA initial project structure (MVP-0)"
```

Cuando quieras publicarlo en GitHub (privado o público según decidas):

```powershell
# Asumiendo que creas el repo vacío en GitHub primero
git remote add origin https://github.com/<tu-usuario>/rosetta.git
git push -u origin main
```

## 3. Configurar entorno de desarrollo

```powershell
# Desde C:\Users\WorkStation\Desktop\Rosetta
uv sync --extra dev

# Copiar variables de entorno
copy .env.example .env
# Edita .env y pon tu ANTHROPIC_API_KEY

# Verificar que funciona
uv run rosetta version
# Debería imprimir: ROSETTA v0.1.0

# Ejecutar tests (deben pasar los 4 de test_models.py)
uv run pytest

# Lint y type check
uv run ruff check .
uv run mypy src/

# Arrancar API en modo dev (endpoint /health funciona ya)
uv run uvicorn rosetta.api.main:app --reload
# Abrir http://127.0.0.1:8000/docs para ver Swagger
```

## 4. Instalar pre-commit (recomendado)

```powershell
uv run pre-commit install
```

A partir de aquí, cada commit se revisa con ruff, mypy, gitleaks.

## 5. Abrir el proyecto con Claude Code

Desde tu terminal, en la carpeta del proyecto:

```powershell
cd C:\Users\WorkStation\Desktop\Rosetta
claude
```

Claude Code detectará `CLAUDE.md` automáticamente y tendrá todo el contexto del proyecto: visión, arquitectura, reglas de desarrollo, convenciones del vault, y la lista de tareas del roadmap.

### Primer prompt sugerido para Claude Code

```
Lee CLAUDE.md y docs/ROADMAP.md. Vamos a arrancar MVP-1: Traductor Simbiótico
funcional sobre ISO 27001:2022. Empieza por implementar CorpusLoader para
parsear un PDF de ISO 27001:2022 Anexo A a fragmentos por control, sin
implementar todavía el RAG. Propón primero la estrategia de segmentación y
espera mi aprobación antes de escribir código.
```

## 6. Abrir el vault con Obsidian

1. Abrir Obsidian.
2. Botón "Open folder as vault".
3. Seleccionar `C:\Users\WorkStation\Desktop\Rosetta\vault`.
4. Empezar por `00_Index.md`.

Obsidian detectará automáticamente los YAML frontmatter, los tags (`#sprint/0`, `#mentor/carlos`, etc.) y los backlinks.

## 7. El primer sprint real (MVP-1) en cinco pasos

1. **Conseguir corpus ISO 27001:2022**: PDF oficial (ISO cobra) o texto alternativo. Colocar en `corpus/iso27001/`. *Nota legal*: para pruebas y desarrollo interno es aceptable; para producción se adquiere licencia.
2. **Implementar `CorpusLoader`**: parsear PDF y segmentar por control del Anexo A (`A.5.1`, `A.5.2`…`A.8.34`).
3. **Implementar `NormativaRAG.ingestar_corpus()` y `recuperar()`**: ChromaDB persistente, embeddings con `sentence-transformers` (modelo `intfloat/multilingual-e5-base` para soportar español/inglés).
4. **Implementar `TraductorSimbiotico.traducir()`**: pipeline completo con Claude tool-use forzando schema `DatosCompliance`.
5. **Tests E2E**: los 5 hallazgos canónicos de `examples/` deben devolver el control top-1 correcto sin alucinar.

Criterio de aceptación MVP-1: `uv run rosetta translate examples/finding_aws_leaked_key.json --marco iso_27001_2022` devuelve un JSON `DatosCompliance` válido citando al menos `A.8.24` y/o `A.5.15`.

## 8. Rutinas del vault

- **Al abrir Claude Code cada sesión**: crear nota en `vault/07_Sprints/YYYY-MM-DD_sprint-N.md` con plantilla.
- **Al tomar una decisión de arquitectura**: ADR en `docs/adr/` + resumen en `vault/02_ADR/`.
- **Al descubrir un patrón normativo útil**: nota en `vault/03_Normativa/` o `vault/04_Controles/`.
- **Al tener una reunión con Carlos u otro mentor**: nota en `vault/08_Reuniones/` con la plantilla.
- **Revisión semanal del Inbox**: reubicar notas sueltas a su carpeta final.

## 9. Secuencia sugerida de comandos para la primera sesión con Claude Code

```powershell
# Terminal 1: API en caliente
cd C:\Users\WorkStation\Desktop\Rosetta
uv run uvicorn rosetta.api.main:app --reload

# Terminal 2: Claude Code
cd C:\Users\WorkStation\Desktop\Rosetta
claude
```

Y al terminar el sprint, antes de `git commit`:

```powershell
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/
uv run pytest
```

---

## Checklist rápida antes del primer push a GitHub

- [ ] `.env` **NO** está committeado (el `.gitignore` lo evita).
- [ ] `ANTHROPIC_API_KEY` está solo en `.env`, nunca en código.
- [ ] README refleja el estado real del proyecto.
- [ ] Al menos un ADR registrado.
- [ ] Sprint 0 documentado en `vault/07_Sprints/`.

## Dudas o bloqueos

Si te bloqueas en cualquier paso: vuelve a Cowork, abre esta conversación, y cuéntame el error concreto. Entre Claude Code (en tu terminal) y yo (aquí en Cowork) cubrimos cualquier obstáculo.
