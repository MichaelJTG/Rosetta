"""
Benchmark de latencia del Traductor Simbiótico (RNF-09: < 30 s por traducción).

Traduce 20 hallazgos técnicos distintos contra 1 marco (ISO 27001:2022, el
valor por defecto de POST /translate y del dashboard) y mide el tiempo de
TraductorSimbiotico.traducir(): recuperación RAG + llamada al LLM + parseo.

Entradas (todas ficticias, ninguna generada por IA):
  - los 16 hallazgos de eval/ground_truth/ens_hallazgos_tecnicos.json
  - los 4 primeros hallazgos de scripts/seed_demo.py (caso TechServ)

Con Ollama, antes de empezar se descarga el modelo de memoria (keep_alive=0)
para que la primera llamada sea en frío, como la primera petición tras más de
5 minutos sin uso. De cada llamada se guardan las métricas que devuelve Ollama
(carga del modelo, tokens de entrada y de salida, tiempo de generación) y los
valores de marcos_aplicables que no son un MarcoNormativo (aviso
marco_desconocido del Traductor).

p95 por rango más cercano: el valor en la posición ceil(0,95 · n) de la lista
ordenada (con n = 20, el 19.º).

Uso:
    uv run python eval/bench_latency.py [--n 20] [--out eval/reports/]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import httpx  # noqa: E402
from seed_demo import HALLAZGOS as SEED_HALLAZGOS  # noqa: E402

from rosetta.core.models import DatosRedTeam, MarcoNormativo  # noqa: E402
from rosetta.core.rag import NormativaRAG  # noqa: E402
from rosetta.core.traductor import TraductorSimbiotico  # noqa: E402
from rosetta.llm.base import CompletionResult  # noqa: E402
from rosetta.llm.factory import get_llm_client  # noqa: E402

GT_HALLAZGO = Path(__file__).parent / "ground_truth" / "ens_hallazgos_tecnicos.json"
REPORTS_DIR = Path(__file__).parent / "reports"
RNF09_THRESHOLD_S = 30.0
NS_PER_S = 1e9
_MARCOS_VALIDOS = {m.value for m in MarcoNormativo}


def load_hallazgos(n: int) -> list[tuple[str, dict[str, Any]]]:
    """Devuelve n hallazgos (id, datos): primero los 16 técnicos, luego los del seed."""
    with open(GT_HALLAZGO, encoding="utf-8") as f:
        gt_cases = json.load(f)["cases"]
    pool = [(c["hallazgo_id"], c["hallazgo"]) for c in gt_cases]
    pool += [(f"SEED-{i:02d}", h["hallazgo"]) for i, h in enumerate(SEED_HALLAZGOS, 1)]
    if n > len(pool):
        raise ValueError(f"Solo hay {len(pool)} hallazgos distintos; pedidos {n}.")
    return pool[:n]


def p95_nearest_rank(values: list[float]) -> float:
    """Percentil 95 por rango más cercano (sin interpolar)."""
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


async def unload_ollama_model(base_url: str, model: str) -> None:
    """Saca el modelo de memoria para que la primera llamada sea en frío."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        await client.post(f"{base_url}/api/generate", json={"model": model, "keep_alive": 0})


def _ollama_metrics(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "load_s": round(raw.get("load_duration", 0) / NS_PER_S, 2),
        "prompt_tokens": raw.get("prompt_eval_count"),
        "prompt_eval_s": round(raw.get("prompt_eval_duration", 0) / NS_PER_S, 2),
        "output_tokens": raw.get("eval_count"),
        "eval_s": round(raw.get("eval_duration", 0) / NS_PER_S, 2),
        "llm_total_s": round(raw.get("total_duration", 0) / NS_PER_S, 2),
    }


async def run(n: int) -> dict[str, Any]:
    llm = get_llm_client()
    proveedor = getattr(llm, "proveedor", type(llm).__name__)
    modelo = getattr(llm, "model", None)
    rag = NormativaRAG(chromadb_path=os.getenv("CHROMADB_PATH", ".chroma"))
    traductor = TraductorSimbiotico(
        llm=llm, rag=rag, marcos_activos=[MarcoNormativo.ISO_27001_2022]
    )

    last: dict[str, CompletionResult] = {}
    original = llm.completar

    async def spy(*args: Any, **kwargs: Any) -> CompletionResult:
        result = await original(*args, **kwargs)
        last["result"] = result
        return result

    llm.completar = spy  # type: ignore[method-assign]

    if proveedor == "ollama":
        await unload_ollama_model(llm.base_url, llm.model)  # type: ignore[attr-defined]

    calls: list[dict[str, Any]] = []
    for i, (hid, datos) in enumerate(load_hallazgos(n), 1):
        last.clear()
        call: dict[str, Any] = {"i": i, "hallazgo_id": hid, "error": None}
        t0 = time.monotonic()
        try:
            await traductor.traducir(DatosRedTeam(**datos))
        except Exception as exc:  # noqa: BLE001 — se registra y se sigue midiendo
            call["error"] = str(exc)[:200]
        call["latency_s"] = round(time.monotonic() - t0, 2)

        result = last.get("result")
        if result is not None:
            if proveedor == "ollama" and isinstance(result.raw, dict):
                call.update(_ollama_metrics(result.raw))
            marcos_raw: list[str] = []
            if result.tool_calls:
                marcos_raw = list(result.tool_calls[0].tool_input.get("marcos_aplicables", []))
            call["marcos_aplicables_raw"] = marcos_raw
            call["marco_desconocido"] = [m for m in marcos_raw if m not in _MARCOS_VALIDOS]
        calls.append(call)
        print(
            f"  [{i:2d}/{n}] {hid:8s} {call['latency_s']:6.2f}s "
            f"load={call.get('load_s', '-')} in={call.get('prompt_tokens', '-')} "
            f"out={call.get('output_tokens', '-')} "
            f"marco_desconocido={call.get('marco_desconocido', [])}"
            + (f" ERROR {call['error']}" if call["error"] else ""),
            flush=True,
        )

    latencias = [c["latency_s"] for c in calls]
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "proveedor": proveedor,
        "modelo": modelo,
        "num_ctx": getattr(llm, "num_ctx", None),
        "marcos": [MarcoNormativo.ISO_27001_2022.value],
        "n": n,
        "errores": sum(1 for c in calls if c["error"]),
        "p50_s": round(statistics.median(latencias), 2),
        "p95_s": p95_nearest_rank(latencias),
        "max_s": max(latencias),
        "media_s": round(statistics.mean(latencias), 2),
        "sobre_umbral": sum(1 for x in latencias if x >= RNF09_THRESHOLD_S),
        "umbral_s": RNF09_THRESHOLD_S,
        "calls": calls,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark RNF-09 del Traductor.")
    parser.add_argument("--n", type=int, default=20, help="Número de llamadas (máx. 23)")
    parser.add_argument("--out", default=str(REPORTS_DIR))
    args = parser.parse_args()

    report = asyncio.run(run(args.n))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    path = out_dir / f"{stamp}_bench_latency_{report['proveedor']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"\n{report['proveedor']} {report['modelo']} · n={report['n']} · "
        f"p50={report['p50_s']}s p95={report['p95_s']}s max={report['max_s']}s "
        f"media={report['media_s']}s · >= {RNF09_THRESHOLD_S:.0f}s: {report['sobre_umbral']} "
        f"· errores: {report['errores']}\n{path}"
    )


if __name__ == "__main__":
    main()
