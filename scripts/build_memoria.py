"""Build script: docs/memoria/memoria.md -> dist/P3_MichaelTelleria_Memoria.pdf"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_MD = ROOT / "docs" / "memoria" / "memoria.md"
SRC_CSS = ROOT / "docs" / "memoria" / "estilos.css"
DIST = ROOT / "dist"
OUT_PDF = DIST / "P3_MichaelTelleria_Memoria.pdf"
OUT_HTML = DIST / "P3_MichaelTelleria_Memoria.html"

STATUS_GLYPHS = {
    "✅": '<span class="st st-ok">✔</span>',
    "🟡": '<span class="st st-parcial">◐</span>',
}

# Cover: the h1 and the subtitle of memoria.md become a full-width band and the
# rest of section 1 (heading, table and note) a card below it
COVER_RE = re.compile(
    r'(<section class="portada">)\s*'
    r"<h1>ROSETTA — Memoria técnica de la Práctica 3</h1>\s*"
    r'(<h2 id="sec-1">.*?</h2>)\s*'
    r"<p><strong>ROSETTA — (Orquestador de cumplimiento continuo)</strong></p>"
    r"(.*?)(</section>)",
    re.S,
)
COVER_BAND = (
    r"\1"
    '<header class="banda">'
    '<h1 class="marca">ROSETTA</h1>'
    r'<p class="subtitulo">\3</p>'
    '<p class="tipo">Memoria técnica · Práctica 3</p>'
    "</header>"
    r'<div class="tarjeta">\2\4</div>'
    r"\5"
)


def cover_band(body: str) -> str:
    new_body, count = COVER_RE.subn(COVER_BAND, body, count=1)
    if count != 1:
        print("WARNING: cover not found; the cover keeps the plain layout.", file=sys.stderr)
    return new_body


def md_to_html(md_text: str, css_path: Path) -> str:
    try:
        import markdown_it  # type: ignore[import]

        mdi = markdown_it.MarkdownIt("commonmark", {"html": True}).enable("table")
        body = mdi.render(md_text)
    except (ImportError, Exception):
        try:
            import markdown  # type: ignore[import]

            body = markdown.markdown(
                md_text,
                extensions=["tables", "fenced_code"],
            )
        except ImportError:
            print(
                "WARNING: neither markdown-it-py nor Markdown installed. "
                "Using plain pre-wrap fallback.",
                file=sys.stderr,
            )
            escaped = md_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            body = f"<pre style='white-space:pre-wrap'>{escaped}</pre>"

    # Anchor ids for the table of contents (nav.indice -> target-counter);
    # the section number goes in its own span so the CSS can colour it
    body = re.sub(r"<h2>(\d+)\. ", r'<h2 id="sec-\1"><span class="num">\1.</span> ', body)
    body = re.sub(r'(<a href="#sec-\d+">)(\d+)\. ', r'\1<span class="num">\2.</span> ', body)
    body = cover_band(body)

    # The app image has no emoji font: map status emoji to DejaVu glyphs
    for emoji, html in STATUS_GLYPHS.items():
        body = body.replace(emoji, html)

    css = css_path.read_text(encoding="utf-8")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>ROSETTA — Memoria técnica P3</title>
  <style>{css}</style>
</head>
<body>
{body}
</body>
</html>"""


def build() -> None:
    if not SRC_MD.exists():
        print(f"ERROR: source not found: {SRC_MD}", file=sys.stderr)
        sys.exit(1)

    DIST.mkdir(parents=True, exist_ok=True)

    md_text = SRC_MD.read_text(encoding="utf-8")
    html = md_to_html(md_text, SRC_CSS)

    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML written -> {OUT_HTML}")

    try:
        from weasyprint import HTML as WP  # type: ignore[import]

        WP(string=html, base_url=str(ROOT / "docs" / "memoria")).write_pdf(str(OUT_PDF))
        size_kb = OUT_PDF.stat().st_size // 1024
        print(f"PDF written  -> {OUT_PDF}  ({size_kb} KB)")
    except ImportError:
        print(
            "WeasyPrint not installed. HTML saved; install and rerun:\n"
            "  uv pip install weasyprint markdown-it-py\n"
            "  python scripts/build_memoria.py",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"WeasyPrint error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    build()
