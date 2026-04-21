"""Generador de informes de auditoría ROSETTA.

Genera informes en dos formatos:
  - Markdown (.md): informe estructurado listo para versionado en git
  - PDF (.pdf): documento formal con marca ROSETTA + opción de marca cliente

El PDF se genera con reportlab (MIT License, puro Python, sin dependencias nativas).
WeasyPrint requiere GTK+ (no disponible en todos los sistemas); reportlab es el backend
por defecto al ser portable y de solo Python.

Uso típico:
    from rosetta.core.report_generator import ReportGenerator, ReportConfig
    config = ReportConfig(nombre_cliente="Acme Corp")
    gen = ReportGenerator(config)
    md_path, pdf_path = gen.generar(hallazgos, ruta_salida=Path("reports/"))
"""

from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from rosetta.core.models import HallazgoMaestro, Severidad

logger = structlog.get_logger(__name__)

# Colores corporativos ROSETTA (RGB 0-1)
_COLOR_PRIMARIO = (0.05, 0.27, 0.52)  # azul oscuro #0D4585
_COLOR_ACENTO = (0.82, 0.18, 0.13)  # rojo alerta #D12E21
_COLOR_GRIS = (0.4, 0.4, 0.4)

_SEV_COLOR: dict[Severidad, tuple[float, float, float]] = {
    Severidad.CRITICA: (0.82, 0.18, 0.13),
    Severidad.ALTA: (0.9, 0.45, 0.0),
    Severidad.MEDIA: (0.85, 0.7, 0.0),
    Severidad.BAJA: (0.0, 0.55, 0.27),
    Severidad.INFORMATIVA: (0.4, 0.4, 0.4),
}


class ReportConfig:
    """Configuración de marca para el informe generado.

    Atributos:
        nombre_cliente: Nombre de la organización auditada. Si None, solo aparece ROSETTA.
        logo_cliente: Ruta a imagen PNG/JPG del logotipo del cliente (opcional).
        autor: Nombre del auditor o equipo que firma el informe.
        confidencialidad: Nivel de confidencialidad impreso en cabecera/pie.
    """

    __slots__ = ("nombre_cliente", "logo_cliente", "autor", "confidencialidad")

    def __init__(
        self,
        nombre_cliente: str | None = None,
        logo_cliente: str | Path | None = None,
        autor: str = "ROSETTA Audit Platform",
        confidencialidad: str = "CONFIDENCIAL",
    ) -> None:
        self.nombre_cliente = nombre_cliente
        self.logo_cliente = Path(logo_cliente) if logo_cliente else None
        self.autor = autor
        self.confidencialidad = confidencialidad


class ReportGenerator:
    """Genera informes de auditoría de cumplimiento normativo en MD y PDF.

    El informe incluye:
      - Portada con marca ROSETTA (+ cliente si se configura)
      - Resumen ejecutivo con métricas clave
      - Tabla de hallazgos por severidad
      - Detalle control-por-control con citas normativas
      - Pie de página con nivel de confidencialidad

    Args:
        config: Configuración de marca. Si None, se usa configuración por defecto ROSETTA.
    """

    def __init__(self, config: ReportConfig | None = None) -> None:
        self.config = config or ReportConfig()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generar(
        self,
        hallazgos: list[HallazgoMaestro],
        ruta_salida: Path | str,
        nombre_base: str | None = None,
    ) -> tuple[Path, Path]:
        """Genera el informe completo en MD y PDF.

        Args:
            hallazgos: Lista de HallazgoMaestro con datos Red Team + compliance.
            ruta_salida: Directorio donde se guardarán los archivos generados.
            nombre_base: Nombre base para los archivos (sin extensión).
                         Por defecto: rosetta_report_YYYYMMDD_HHMMSS.

        Returns:
            Tupla (path_markdown, path_pdf) con las rutas de los archivos generados.
        """
        ruta = Path(ruta_salida)
        ruta.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = nombre_base or f"rosetta_report_{ts}"

        md_path = ruta / f"{base}.md"
        pdf_path = ruta / f"{base}.pdf"

        md_content = self._generar_markdown(hallazgos, ts)
        md_path.write_text(md_content, encoding="utf-8")

        self._generar_pdf(hallazgos, pdf_path, ts)

        logger.info(
            "informe_generado",
            md=str(md_path),
            pdf=str(pdf_path),
            hallazgos=len(hallazgos),
        )
        return md_path, pdf_path

    def generar_markdown(
        self,
        hallazgos: list[HallazgoMaestro],
        ruta_salida: Path | str,
        nombre_base: str | None = None,
    ) -> Path:
        """Genera solo el informe Markdown."""
        ruta = Path(ruta_salida)
        ruta.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = nombre_base or f"rosetta_report_{ts}"
        md_path = ruta / f"{base}.md"
        md_path.write_text(self._generar_markdown(hallazgos, ts), encoding="utf-8")
        logger.info("markdown_generado", path=str(md_path))
        return md_path

    # ------------------------------------------------------------------
    # Generación Markdown
    # ------------------------------------------------------------------

    def _generar_markdown(self, hallazgos: list[HallazgoMaestro], ts: str) -> str:
        """Construye el contenido completo del informe en Markdown."""
        cfg = self.config
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        cliente_str = f" — {cfg.nombre_cliente}" if cfg.nombre_cliente else ""
        metricas = self._calcular_metricas(hallazgos)

        partes: list[str] = [
            f"# Informe de Auditoría de Cumplimiento{cliente_str}\n",
            "**Plataforma:** ROSETTA Audit Platform  ",
            f"**Autor:** {cfg.autor}  ",
            f"**Fecha:** {fecha}  ",
            f"**Clasificación:** {cfg.confidencialidad}\n",
            "---\n",
            "## Resumen Ejecutivo\n",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| Total hallazgos | **{metricas['total']}** |",
            f"| Críticos | **{metricas.get('critica', 0)}** |",
            f"| Altos | **{metricas.get('alta', 0)}** |",
            f"| Medios | **{metricas.get('media', 0)}** |",
            f"| Marcos afectados | **{metricas['marcos']}** |\n",
            "---\n",
            "## Hallazgos por Severidad\n",
            "| ID | Activo | Severidad | Controles | Marcos |",
            "|----|--------|-----------|-----------|--------|",
        ]

        for h in hallazgos:
            compliance = h.compliance_data
            if compliance is None:
                continue
            marcos_str = ", ".join(m.value for m in compliance.marcos_aplicables)
            controles_str = ", ".join(compliance.controles_incumplidos[:3])
            if len(compliance.controles_incumplidos) > 3:
                controles_str += f" (+{len(compliance.controles_incumplidos) - 3})"
            activo = h.red_team_data.activo_detectado[:40]
            partes.append(
                f"| `{h.id_hallazgo}` | {activo} "
                f"| **{compliance.impacto_legal.value.upper()}** "
                f"| {controles_str} | {marcos_str} |"
            )

        partes.extend(["\n---\n", "## Detalle de Hallazgos\n"])

        for i, h in enumerate(hallazgos, 1):
            compliance = h.compliance_data
            if compliance is None:
                continue
            partes.extend(
                [
                    f"### {i}. `{h.id_hallazgo}` — {h.red_team_data.activo_detectado}\n",
                    f"- **Severidad:** {compliance.impacto_legal.value.upper()}",
                    f"- **Origen:** {h.red_team_data.origen.value}",
                    f"- **Vector:** {h.red_team_data.vector_ataque}",
                    f"- **Marcos:** {', '.join(m.value for m in compliance.marcos_aplicables)}",
                    f"- **Controles incumplidos:** {', '.join(compliance.controles_incumplidos)}",
                    f"\n**Cita normativa:**\n> {compliance.cita_normativa}\n",
                    f"**Justificación:**\n{compliance.justificacion}\n",
                    f"**Acción de mitigación:**\n{compliance.accion_mitigacion}\n",
                    "---\n",
                ]
            )

        partes.extend(
            [
                f"\n*Informe generado por ROSETTA Audit Platform · {fecha}*  ",
                f"*Ref: {ts} · {cfg.confidencialidad}*",
            ]
        )

        return "\n".join(partes)

    # ------------------------------------------------------------------
    # Generación PDF con reportlab
    # ------------------------------------------------------------------

    def _generar_pdf(self, hallazgos: list[HallazgoMaestro], path: Path, ts: str) -> None:
        """Genera el informe PDF usando reportlab (fallback a stub si no disponible)."""
        try:
            self._generar_pdf_reportlab(hallazgos, path, ts)
        except ImportError:
            logger.warning("reportlab_no_disponible_pdf_stub", path=str(path))
            # Stub mínimo de PDF para que el archivo exista
            path.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n")

    def _generar_pdf_reportlab(self, hallazgos: list[HallazgoMaestro], path: Path, ts: str) -> None:
        """Implementación real con reportlab."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import (
            ParagraphStyle,
            getSampleStyleSheet,
        )
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            HRFlowable,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        cfg = self.config
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        cliente_str = f" — {cfg.nombre_cliente}" if cfg.nombre_cliente else ""
        metricas = self._calcular_metricas(hallazgos)

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
        )

        styles = getSampleStyleSheet()
        azul = colors.Color(*_COLOR_PRIMARIO)

        estilo_titulo = ParagraphStyle(
            "RosettaTitulo",
            parent=styles["Heading1"],
            textColor=azul,
            fontSize=20,
            spaceAfter=6,
        )
        estilo_subtitulo = ParagraphStyle(
            "RosettaSubtitulo",
            parent=styles["Normal"],
            textColor=colors.Color(*_COLOR_GRIS),
            fontSize=10,
            spaceAfter=4,
        )
        estilo_h2 = ParagraphStyle(
            "RosettaH2",
            parent=styles["Heading2"],
            textColor=azul,
            fontSize=14,
            spaceBefore=16,
            spaceAfter=6,
        )
        estilo_h3 = ParagraphStyle(
            "RosettaH3",
            parent=styles["Heading3"],
            textColor=azul,
            fontSize=11,
            spaceBefore=10,
            spaceAfter=4,
        )
        estilo_body = ParagraphStyle(
            "RosettaBody",
            parent=styles["Normal"],
            fontSize=9,
            spaceAfter=4,
            leading=13,
        )
        estilo_cita = ParagraphStyle(
            "RosettaCita",
            parent=styles["Normal"],
            fontSize=8,
            leftIndent=20,
            textColor=colors.Color(*_COLOR_GRIS),
            spaceAfter=4,
            leading=12,
        )

        story: list[Any] = []

        # Portada
        story.append(Paragraph("ROSETTA", estilo_titulo))
        story.append(Paragraph(f"Informe de Auditoría de Cumplimiento{cliente_str}", estilo_titulo))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"Autor: {cfg.autor}", estilo_subtitulo))
        story.append(Paragraph(f"Fecha: {fecha}", estilo_subtitulo))
        story.append(Paragraph(f"Clasificación: {cfg.confidencialidad}", estilo_subtitulo))
        story.append(HRFlowable(width="100%", thickness=2, color=azul))
        story.append(Spacer(1, 0.5 * cm))

        # Resumen ejecutivo
        story.append(Paragraph("Resumen Ejecutivo", estilo_h2))
        datos_resumen = [
            ["Métrica", "Valor"],
            ["Total hallazgos", str(metricas["total"])],
            ["Críticos", str(metricas.get("critica", 0))],
            ["Altos", str(metricas.get("alta", 0))],
            ["Medios", str(metricas.get("media", 0))],
            ["Marcos afectados", str(metricas["marcos"])],
        ]
        tabla_resumen = Table(datos_resumen, colWidths=[10 * cm, 5 * cm])
        tabla_resumen.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), azul),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.Color(0.95, 0.97, 1.0)],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ]
            )
        )
        story.append(tabla_resumen)
        story.append(Spacer(1, 0.5 * cm))

        # Tabla hallazgos
        hallazgos_con_compliance = [h for h in hallazgos if h.compliance_data is not None]
        if hallazgos_con_compliance:
            story.append(Paragraph("Hallazgos por Severidad", estilo_h2))
            filas: list[list[str]] = [["ID", "Activo", "Severidad", "Controles"]]
            for h in hallazgos_con_compliance:
                compliance = h.compliance_data
                assert compliance is not None  # narrowing
                controles_str = ", ".join(compliance.controles_incumplidos[:2])
                if len(compliance.controles_incumplidos) > 2:
                    controles_str += f" +{len(compliance.controles_incumplidos) - 2}"
                activo = h.red_team_data.activo_detectado
                if len(activo) > 35:
                    activo = activo[:32] + "…"
                filas.append(
                    [
                        h.id_hallazgo,
                        activo,
                        compliance.impacto_legal.value.upper(),
                        controles_str,
                    ]
                )

            tabla = Table(filas, colWidths=[2.5 * cm, 6 * cm, 2.5 * cm, 5 * cm])
            sev_styles: list[tuple[Any, ...]] = [
                ("BACKGROUND", (0, 0), (-1, 0), azul),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.Color(0.97, 0.97, 0.97)],
                ),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
            ]
            for idx, h in enumerate(hallazgos_con_compliance, 1):
                compliance = h.compliance_data
                assert compliance is not None
                rgb = _SEV_COLOR.get(compliance.impacto_legal, _COLOR_GRIS)
                sev_styles.append(("TEXTCOLOR", (2, idx), (2, idx), colors.Color(*rgb)))
            tabla.setStyle(TableStyle(sev_styles))
            story.append(tabla)
            story.append(Spacer(1, 0.5 * cm))

        # Detalle
        if hallazgos_con_compliance:
            story.append(Paragraph("Detalle de Hallazgos", estilo_h2))
            hr_color = colors.Color(0.85, 0.85, 0.85)
            for i, h in enumerate(hallazgos_con_compliance, 1):
                compliance = h.compliance_data
                assert compliance is not None
                story.append(
                    Paragraph(
                        f"{i}. {h.id_hallazgo} — {h.red_team_data.activo_detectado}",
                        estilo_h3,
                    )
                )
                rgb = _SEV_COLOR.get(compliance.impacto_legal, _COLOR_GRIS)
                sev_hex = f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"
                story.append(
                    Paragraph(
                        f"<b>Severidad:</b> <font color='{sev_hex}'>"
                        f"{compliance.impacto_legal.value.upper()}</font> &nbsp;|&nbsp; "
                        f"<b>Origen:</b> {h.red_team_data.origen.value} &nbsp;|&nbsp; "
                        f"<b>Marcos:</b> "
                        f"{', '.join(m.value for m in compliance.marcos_aplicables)}",
                        estilo_body,
                    )
                )
                story.append(
                    Paragraph(
                        f"<b>Controles:</b> {', '.join(compliance.controles_incumplidos)}",
                        estilo_body,
                    )
                )
                cita = textwrap.shorten(compliance.cita_normativa, width=300, placeholder="…")
                story.append(Paragraph(f"<i>«{cita}»</i>", estilo_cita))
                just = textwrap.shorten(compliance.justificacion, width=400, placeholder="…")
                story.append(Paragraph(f"<b>Justificación:</b> {just}", estilo_body))
                mit = textwrap.shorten(compliance.accion_mitigacion, width=400, placeholder="…")
                story.append(Paragraph(f"<b>Mitigación:</b> {mit}", estilo_body))
                story.append(HRFlowable(width="100%", thickness=0.5, color=hr_color))

        # Pie
        story.append(Spacer(1, 1 * cm))
        story.append(
            Paragraph(
                f"Generado por ROSETTA Audit Platform · {fecha} · "
                f"Ref: {ts} · {cfg.confidencialidad}",
                estilo_subtitulo,
            )
        )

        doc.build(story)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _calcular_metricas(self, hallazgos: list[HallazgoMaestro]) -> dict[str, Any]:
        """Calcula métricas de resumen del conjunto de hallazgos."""
        sev_dist: dict[str, int] = {}
        marcos_set: set[str] = set()

        for h in hallazgos:
            compliance = h.compliance_data
            if compliance is None:
                continue
            sev = compliance.impacto_legal.value
            sev_dist[sev] = sev_dist.get(sev, 0) + 1
            for m in compliance.marcos_aplicables:
                marcos_set.add(m.value)

        return {
            "total": len(hallazgos),
            "marcos": len(marcos_set),
            **sev_dist,
        }
