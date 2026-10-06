"""Build script: docs/memoria/memoria.md -> dist/P3_Memoria.pdf"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_MD = ROOT / "docs" / "memoria" / "memoria.md"
SRC_CSS = ROOT / "docs" / "memoria" / "estilos.css"
DIST = ROOT / "dist"
OUT_PDF = DIST / "P3_Memoria.pdf"
OUT_HTML = DIST / "P3_Memoria.html"


def md_to_html(md_text: str, css_path: Path) -> str:
    try:
        import markdown_it  # type: ignore[import]

        mdi = markdown_it.MarkdownIt("commonmark", {"breaks": False})
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

        WP(string=html, base_url=str(DIST)).write_pdf(str(OUT_PDF))
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
