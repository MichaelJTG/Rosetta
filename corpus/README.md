# Corpus normativo

Ubicación de los textos oficiales de cada marco normativo para ingesta al RAG.

## Estructura esperada

```
corpus/
├── iso27001/        # ISO/IEC 27001:2022 (descarga oficial o Markdown preparado)
├── ens/             # ENS — Real Decreto 311/2022 (BOE)
├── nis2/            # Directiva NIS2
└── dora/            # DORA Regulation
```

## Formato admitido

- PDF (se parsea con pypdf).
- Markdown estructurado por control/artículo.
- Texto plano segmentado.

## Importante

Los PDFs oficiales suelen estar sujetos a derechos de distribución (ISO cobra por el texto de la norma). Este directorio está en `.gitignore` para los `*.pdf` y `*.docx` — cada usuario debe obtener los textos por los canales legítimos.

Para ENS (español) el BOE es público: https://www.boe.es/buscar/act.php?id=BOE-A-2022-7191

## Cargar un corpus

```bash
uv run rosetta load-corpus iso_27001_2022 corpus/iso27001/
```
