# Corpus ISO/IEC 27001:2022

## Fuente

- **Archivo**: `iso27001-2022-intuitem.yaml`
- **Proveedor original**: intuitem (CISO Assistant Community)
- **Repositorio**: https://github.com/intuitem/ciso-assistant-community
- **Licencia del repo**: AGPL-3.0 (aplica al software, no a los datos del corpus)
- **Nota de copyright del archivo**: *"This is the outline of the ISO27001-2022 standard.
  You can purchase the full standard from https://www.iso.org/standard/27001"*

## Contenido

93 controles ISO/IEC 27001:2022 (Tercera edición, octubre 2022):
- **A.5** Controles organizacionales (37 controles)
- **A.6** Controles de personas (8 controles)
- **A.7** Controles físicos (14 controles)
- **A.8** Controles tecnológicos (34 controles)

Las descripciones son resúmenes propios de intuitem, no texto verbatim de la norma ISO.
Traducciones disponibles: en, es, fr, de, cs, sv, zh.

## Uso en ROSETTA

Este corpus alimenta `NormativaRAG` a través de `CorpusLoader`.
No commitear este directorio al repositorio — está cubierto por `.gitignore`.

## Cómo actualizar

```bash
curl -sL https://raw.githubusercontent.com/intuitem/ciso-assistant-community/main/backend/library/libraries/iso27001-2022.yaml \
  -o corpus/iso27001/iso27001-2022-intuitem.yaml
```
