"""CLI de ROSETTA usando Typer."""

from __future__ import annotations

import typer
from rich.console import Console

from rosetta import __version__

app = typer.Typer(
    name="rosetta",
    help="Orquestador de cumplimiento continuo — ROSETTA CLI.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Muestra la versión instalada de ROSETTA."""
    console.print(f"[bold cyan]ROSETTA[/] v{__version__}")


@app.command()
def translate(
    hallazgo_path: str = typer.Argument(
        ..., help="Ruta a un JSON con un DatosRedTeam."
    ),
    marco: str = typer.Option(
        "iso_27001_2022", help="Marco normativo a aplicar."
    ),
) -> None:
    """Traduce un hallazgo en JSON a su representación normativa."""
    console.print(f"[yellow]TODO[/] traducir {hallazgo_path} contra {marco}")
    console.print("Ver docs/ROADMAP.md#mvp-1")


@app.command(name="load-corpus")
def load_corpus(
    marco: str = typer.Argument(..., help="Marco a cargar, ej: iso_27001_2022."),
    ruta: str = typer.Argument(..., help="Carpeta con PDFs/MDs del marco."),
) -> None:
    """Carga un marco normativo al RAG."""
    console.print(f"[yellow]TODO[/] cargar corpus {marco} desde {ruta}")
    console.print("Ver docs/ROADMAP.md#mvp-1")


if __name__ == "__main__":
    app()
