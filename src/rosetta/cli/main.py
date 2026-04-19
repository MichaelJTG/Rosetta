"""CLI de ROSETTA usando Typer."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

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
    hallazgo_path: str = typer.Argument(..., help="Ruta a un JSON con un DatosRedTeam."),
    marco: str = typer.Option("iso_27001_2022", "--marco", "-m", help="Marco normativo."),
    chromadb_path: str = typer.Option(
        None, "--chroma", help="Ruta a ChromaDB. Por defecto usa CHROMADB_PATH del .env."
    ),
) -> None:
    """Traduce un hallazgo en JSON a su representación normativa.

    El hallazgo debe ser un JSON con la estructura DatosRedTeam.
    Requiere que el corpus del marco esté cargado (usa load-corpus primero).
    """
    from rosetta.core.models import DatosRedTeam, MarcoNormativo
    from rosetta.core.rag import NormativaRAG
    from rosetta.core.traductor import TraductorSimbiotico
    from rosetta.llm.factory import get_llm_client

    ruta = Path(hallazgo_path)
    if not ruta.exists():
        console.print(f"[red]Error:[/] No se encontró el archivo {hallazgo_path}")
        raise typer.Exit(1)

    try:
        hallazgo_data = json.loads(ruta.read_text(encoding="utf-8"))
        hallazgo = DatosRedTeam(**hallazgo_data)
    except Exception as exc:
        console.print(f"[red]Error al parsear el hallazgo:[/] {exc}")
        raise typer.Exit(1) from exc

    try:
        marco_enum = MarcoNormativo(marco)
    except ValueError:
        valores = ", ".join(m.value for m in MarcoNormativo)
        console.print(f"[red]Marco desconocido:[/] {marco}. Opciones: {valores}")
        raise typer.Exit(1) from None

    chroma_path = chromadb_path or os.getenv("CHROMADB_PATH", ".chroma")
    rag = NormativaRAG(chromadb_path=chroma_path)

    if rag.contar(marco_enum) == 0:
        console.print(
            f"[yellow]Aviso:[/] El corpus de {marco} no está cargado. "
            f"Ejecuta: [bold]rosetta load-corpus {marco} corpus/{marco.replace('_', '')}/[/]"
        )

    llm = get_llm_client()
    traductor = TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=[marco_enum])

    console.print(f"[cyan]Traduciendo[/] {ruta.name} contra {marco}…")

    try:
        resultado = asyncio.run(traductor.traducir(hallazgo))
    except Exception as exc:
        console.print(f"[red]Error en la traducción:[/] {exc}")
        raise typer.Exit(1) from exc

    resultado_json = resultado.model_dump_json(indent=2)
    syntax = Syntax(resultado_json, "json", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="[bold green]DatosCompliance[/]", expand=False))


@app.command(name="load-corpus")
def load_corpus(
    marco: str = typer.Argument(..., help="Marco normativo, ej: iso_27001_2022."),
    ruta: str = typer.Argument(..., help="Carpeta con el corpus del marco."),
    chromadb_path: str = typer.Option(
        None, "--chroma", help="Ruta a ChromaDB. Por defecto usa CHROMADB_PATH del .env."
    ),
) -> None:
    """Carga un marco normativo al RAG (ChromaDB).

    Parsea todos los archivos (.yaml, .pdf, .md) en la carpeta indicada,
    genera embeddings y los indexa en ChromaDB para que el Traductor pueda
    hacer búsqueda semántica.
    """
    from rosetta.adapters.compliance.loader import CorpusLoader
    from rosetta.core.models import MarcoNormativo
    from rosetta.core.rag import NormativaRAG

    try:
        marco_enum = MarcoNormativo(marco)
    except ValueError:
        valores = ", ".join(m.value for m in MarcoNormativo)
        console.print(f"[red]Marco desconocido:[/] {marco}. Opciones: {valores}")
        raise typer.Exit(1) from None

    ruta_path = Path(ruta)
    if not ruta_path.exists():
        console.print(f"[red]Error:[/] No existe la carpeta {ruta}")
        raise typer.Exit(1)

    chroma_path = chromadb_path or os.getenv("CHROMADB_PATH", ".chroma")

    console.print(f"[cyan]Cargando corpus[/] {marco} desde {ruta}…")

    loader = CorpusLoader()
    fragmentos = loader.cargar(marco_enum, ruta_path)

    if not fragmentos:
        console.print("[yellow]No se encontraron fragmentos en la carpeta indicada.[/]")
        raise typer.Exit(1)

    rag = NormativaRAG(chromadb_path=chroma_path)
    n = rag.ingestar_corpus(fragmentos)

    console.print(
        f"[green]✓[/] {n} fragmentos de [bold]{marco}[/] indexados en ChromaDB ({chroma_path})"
    )


@app.command()
def dossier(
    marco: str = typer.Option("iso_27001_2022", "--marco", "-m", help="Marco normativo."),
    salida: str = typer.Option(None, "--salida", "-o", help="Ruta del archivo Markdown de salida."),
    neo4j_uri: str = typer.Option(
        None, "--neo4j-uri", help="URI Neo4j. Por defecto NEO4J_URI del .env."
    ),
    neo4j_user: str = typer.Option(None, "--neo4j-user", help="Usuario Neo4j."),
    neo4j_password: str = typer.Option(None, "--neo4j-password", help="Contraseña Neo4j."),
) -> None:
    """Exporta un dossier de auditoría en Markdown desde el grafo Neo4j.

    Requiere Neo4j corriendo (docker compose up neo4j).
    """
    from rosetta.core.graph import GrafoCorrelacion

    uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
    password = neo4j_password or os.getenv("NEO4J_PASSWORD", "rosetta_dev")

    try:
        grafo = GrafoCorrelacion.desde_uri(uri, user, password)
    except Exception as exc:
        console.print(f"[red]No se pudo conectar a Neo4j ({uri}):[/] {exc}")
        console.print("[dim]Asegúrate de que Neo4j está corriendo: docker compose up neo4j[/]")
        raise typer.Exit(1) from exc

    try:
        markdown = grafo.exportar_dossier(marco)
    finally:
        grafo.cerrar()

    if salida:
        Path(salida).write_text(markdown, encoding="utf-8")
        console.print(f"[green]✓[/] Dossier exportado a [bold]{salida}[/]")
    else:
        console.print(markdown)


if __name__ == "__main__":
    app()
