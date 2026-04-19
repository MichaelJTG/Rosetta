---
title: PCI-DSS v4.0
tags: [normativa, normativa/pci, rosetta]
marco_id: pci_dss_4
created: 2026-04-18
estado_corpus: no_cargado
prioridad: media
mvp: MVP-8
---

# PCI-DSS v4.0 · Payment Card Industry Data Security Standard

> Estándar del consorcio PCI Security Standards Council. Obligatorio para cualquier entidad que procese, almacene o transmita datos de tarjetas de pago.

## Datos rápidos

- **Publicador**: PCI Security Standards Council
- **Versión**: 4.0 (marzo 2022) · v3.2.1 deprecada en marzo 2024
- **Acceso al corpus**: registro gratuito en pcisecuritystandards.org
- **Ámbito**: comercios, procesadores, adquirentes, emisores

## Los 12 requisitos PCI-DSS v4.0

1. Instalar y mantener controles de seguridad de red
2. Aplicar configuraciones seguras a todos los componentes
3. Proteger datos de cuenta almacenados
4. Proteger datos de cuenta en tránsito con cifrado fuerte
5. Proteger frente a software malicioso
6. Desarrollar y mantener sistemas y software seguros
7. Restringir acceso a componentes y datos por necesidad
8. Identificar usuarios y autenticar acceso
9. Restringir acceso físico
10. Registrar y monitorizar todo acceso
11. Probar regularmente seguridad de sistemas y redes
12. Apoyar la seguridad con políticas y programas organizacionales

## Por qué incluirlo (más adelante)

- Cualquier ecommerce o pasarela de pagos lo necesita.
- Es muy prescriptivo (a diferencia de ISO 27001 que es más flexible) → fácil de auditar automáticamente.
- Encaja perfecto con el gate CI/CD del [[MOC_Roadmap#MVP-7|MVP-7]] (verificar que no se introducen incumplimientos PCI en cada deploy).

## Mapeos clave

- PCI Req 3 ↔ ISO 27001 A.8.24 (cifrado at-rest)
- PCI Req 4 ↔ ISO 27001 A.8.24 (cifrado en tránsito)
- PCI Req 8 ↔ ISO 27001 A.5.16 + A.5.17 (autenticación)
- PCI Req 10 ↔ ISO 27001 A.8.15 + A.8.16 (logging y monitorización)

## Enlaces

- [[MOC_Normativas]] · [[03_Normativa/ISO_27001_2022]]
- PCI Council: https://www.pcisecuritystandards.org/
