"""CLI de ROSETTA usando Typer."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from rosetta import __version__

load_dotenv()

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


@app.command()
def scan(
    objetivo: str = typer.Argument(..., help="URL, IP o dominio del activo autorizado a escanear."),
    sensor: str = typer.Option("nuclei", "--sensor", "-s", help="Sensor Red Team: nuclei."),
    marco: str = typer.Option(
        "iso_27001_2022", "--marco", "-m", help="Marco(s) normativo(s), separados por coma."
    ),
    salida: str = typer.Option(None, "--salida", "-o", help="Ruta del dossier Markdown de salida."),
    chromadb_path: str = typer.Option(None, "--chroma", help="Ruta a ChromaDB."),
    neo4j_uri: str = typer.Option(None, "--neo4j-uri", help="URI Neo4j."),
    neo4j_user: str = typer.Option(None, "--neo4j-user", help="Usuario Neo4j."),
    neo4j_password: str = typer.Option(None, "--neo4j-password", help="Contraseña Neo4j."),
    nuclei_bin: str = typer.Option("nuclei", "--nuclei-bin", help="Ruta al binario nuclei."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Parsea hallazgos sin llamar al LLM."),
) -> None:
    """Pipeline completo: escanea con Nuclei, traduce a normativa y genera dossier.

    Flujo: nuclei → DatosRedTeam → TraductorSimbiótico → Neo4j → Markdown.

    Requiere nuclei en PATH y, para persistencia, Neo4j corriendo.
    """
    import uuid

    from rosetta.adapters.red.nuclei import NucleiAdapter
    from rosetta.core.graph import GrafoCorrelacion
    from rosetta.core.models import DatosRedTeam, HallazgoMaestro, MarcoNormativo
    from rosetta.core.rag import NormativaRAG
    from rosetta.core.traductor import TraductorSimbiotico
    from rosetta.llm.factory import get_llm_client

    # Parsear marcos
    marcos_raw = [m.strip() for m in marco.split(",")]
    marcos: list[MarcoNormativo] = []
    for m in marcos_raw:
        try:
            marcos.append(MarcoNormativo(m))
        except ValueError:
            valores = ", ".join(x.value for x in MarcoNormativo)
            console.print(f"[red]Marco desconocido:[/] {m}. Opciones: {valores}")
            raise typer.Exit(1) from None

    console.print(f"[cyan]Escaneando[/] {objetivo} con {sensor}…")

    # 1. Escaneo
    if sensor == "nuclei":
        adapter = NucleiAdapter(binario=nuclei_bin)
    else:
        console.print(f"[red]Sensor desconocido:[/] {sensor}. Disponibles: nuclei")
        raise typer.Exit(1)

    try:
        hallazgos_red: list[DatosRedTeam] = asyncio.run(adapter.escanear(objetivo))
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1) from exc
    except Exception as exc:
        console.print(f"[red]Error en escaneo:[/] {exc}")
        raise typer.Exit(1) from exc

    if not hallazgos_red:
        console.print("[yellow]No se encontraron hallazgos.[/]")
        raise typer.Exit(0)

    console.print(f"[green]✓[/] {len(hallazgos_red)} hallazgos encontrados.")

    if dry_run:
        for h in hallazgos_red:
            console.print(f"  · {h.activo_detectado} — {h.vector_ataque[:80]}")
        raise typer.Exit(0)

    # 2. Traducir + persistir en grafo
    chroma_path = chromadb_path or os.getenv("CHROMADB_PATH", ".chroma")
    rag = NormativaRAG(chromadb_path=chroma_path)
    llm = get_llm_client()
    traductor = TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=marcos)

    neo_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
    neo_pass = neo4j_password or os.getenv("NEO4J_PASSWORD", "rosetta_dev")

    grafo: GrafoCorrelacion | None = None
    try:
        grafo = GrafoCorrelacion.desde_uri(neo_uri, neo_user, neo_pass)
    except Exception as exc:
        console.print(f"[yellow]Neo4j no disponible ({exc}) — los hallazgos no se persistirán.[/]")

    errores = 0
    for rt_data in hallazgos_red:
        try:
            compliance = asyncio.run(traductor.traducir(rt_data))
        except Exception as exc:
            console.print(f"[yellow]Error traduciendo {rt_data.activo_detectado}:[/] {exc}")
            errores += 1
            continue

        if grafo is not None:
            hallazgo_id = f"SEC-{uuid.uuid4().hex[:8].upper()}"
            for ctrl in compliance.controles_incumplidos:
                for marco_obj in compliance.marcos_aplicables:
                    grafo.registrar_hallazgo(
                        hallazgo_id=hallazgo_id,
                        activo=rt_data.activo_detectado,
                        marco=marco_obj.value,
                        control_id=ctrl,
                        control_nombre=ctrl,
                        severidad=compliance.impacto_legal.value,
                        origen=rt_data.origen.value,
                        evidencia=rt_data.evidencia,
                        justificacion=compliance.justificacion,
                        mitigacion=compliance.accion_mitigacion,
                        timestamp=str(
                            HallazgoMaestro(
                                id_hallazgo=hallazgo_id,
                                red_team_data=rt_data,
                                compliance_data=compliance,
                            ).timestamp
                        ),
                    )

    console.print(
        f"[green]✓[/] {len(hallazgos_red) - errores}/{len(hallazgos_red)} hallazgos traducidos."
    )

    # 3. Dossier
    if grafo is not None:
        markdown = grafo.exportar_dossier(marcos[0].value, titulo=f"Scan {objetivo}")
        grafo.cerrar()

        if salida:
            Path(salida).write_text(markdown, encoding="utf-8")
            console.print(f"[green]✓[/] Dossier exportado a [bold]{salida}[/]")
        else:
            console.print(markdown)


@app.command(name="detect-drift")
def detect_drift(
    procedimiento: str = typer.Argument(
        ..., help="Ruta al archivo del procedimiento (.md, .txt, .pdf)."
    ),
    observaciones: str = typer.Option(
        ...,
        "--observaciones",
        "-o",
        help="Observaciones separadas por '|' o ruta a archivo .txt/.json.",
    ),
    procedimiento_id: str = typer.Option(
        None, "--id", help="ID del procedimiento. Por defecto: nombre del archivo."
    ),
) -> None:
    """Detecta desviación (drift) entre un procedimiento interno y la realidad observada.

    Ejemplo:
        rosetta detect-drift examples/procedures/PRO-IAM-001.md \\
          --observaciones "12 cuentas con >90 días inactivas sin desactivar|3 admins sin rotación de clave"
    """
    from rosetta.core.drift import DriftDetector
    from rosetta.llm.factory import get_llm_client

    proc_path = Path(procedimiento)
    if not proc_path.exists():
        console.print(f"[red]No se encontró el procedimiento:[/] {procedimiento}")
        raise typer.Exit(1)

    texto_proc = proc_path.read_text(encoding="utf-8")
    pid = procedimiento_id or proc_path.stem

    # Parsear observaciones: '|' separadas, o fichero
    obs_path = Path(observaciones)
    if obs_path.exists():
        if obs_path.suffix.lower() == ".json":
            import json as _json

            obs_lista: list[str] = _json.loads(obs_path.read_text(encoding="utf-8"))
        else:
            obs_lista = [
                line.strip()
                for line in obs_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
    else:
        obs_lista = [o.strip() for o in observaciones.split("|") if o.strip()]

    if not obs_lista:
        console.print("[red]No se proporcionaron observaciones.[/]")
        raise typer.Exit(1)

    llm = get_llm_client()
    detector = DriftDetector(llm=llm)

    console.print(f"[cyan]Analizando drift[/] en {pid} con {len(obs_lista)} observaciones…")

    try:
        resultado = asyncio.run(detector.detectar_drift(pid, texto_proc, obs_lista))
    except Exception as exc:
        console.print(f"[red]Error en análisis de drift:[/] {exc}")
        raise typer.Exit(1) from exc

    if resultado.drift_detectado:
        console.print(f"\n[bold red]⚠ DRIFT DETECTADO[/] — Impacto: {resultado.impacto.value}")
        console.print(f"\n{resultado.descripcion_drift}")
        if resultado.fragmento_afectado:
            console.print(f"\n[dim]Fragmento afectado:[/]\n{resultado.fragmento_afectado}")
        if resultado.redaccion_propuesta:
            console.print(f"\n[green]Redacción propuesta:[/]\n{resultado.redaccion_propuesta}")
        if resultado.controles_afectados:
            console.print(
                f"\n[yellow]Controles normativos afectados:[/] {', '.join(resultado.controles_afectados)}"
            )
    else:
        console.print(
            "[green]✓ Sin drift detectado.[/] El procedimiento refleja la realidad observada."
        )


if __name__ == "__main__":
    app()
