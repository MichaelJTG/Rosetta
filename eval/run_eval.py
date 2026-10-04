"""
C-2: Eval harness for ROSETTA Traductor Simbiótico.

Measures accuracy and hallucination rate of ENS->ISO 27001:2022 mapping
against ground truth extracted from professor's SoA (ens_iso.json).

Usage:
    python eval/run_eval.py [--marco ens] [--limit N] [--out eval/reports/]

Output:
    eval/reports/YYYY-MM-DDTHH-MM-SS_eval_report.json   (machine-readable)
    eval/reports/YYYY-MM-DDTHH-MM-SS_eval_report.md     (human-readable)

Ground truth source: SoA_TechServ.xlsx (professor's SoA) -- NOT AI-generated.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rosetta.core.models import DatosRedTeam, FuenteRedTeam, Severidad  # noqa: E402
from rosetta.core.rag import NormativaRAG  # noqa: E402
from rosetta.core.traductor import TraductorSimbiotico  # noqa: E402
from rosetta.llm.factory import get_llm_client  # noqa: E402

GT_PATH = Path(__file__).parent / "ground_truth" / "ens_iso.json"
REPORTS_DIR = Path(__file__).parent / "reports"


@dataclass
class CaseResult:
    ens_code: str
    ens_name: str
    familia: str
    nivel_exigido: str
    gt_iso_ids: list[str]
    predicted_iso_ids: list[str]
    predicted_iso_raw: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    hallucinated_ids: list[str] = field(default_factory=list)
    missed_ids: list[str] = field(default_factory=list)
    error: str | None = None
    latency_s: float = 0.0


@dataclass
class FamilyReport:
    familia: str
    n_cases: int
    avg_precision: float
    avg_recall: float
    avg_f1: float
    hallucination_rate: float


@dataclass
class EvalReport:
    run_id: str
    timestamp: str
    marco: str
    total_cases: int
    evaluated: int
    errors: int
    overall_precision: float
    overall_recall: float
    overall_f1: float
    hallucination_rate: float
    per_family: list[FamilyReport]
    cases: list[CaseResult]


def _normalize_iso_id(raw: str) -> str | None:
    """Normalize ISO 27001 control ID to '5.1' format.

    Handles both ISO 2013 Annex A style ('A.5.15') and ISO 2022 style ('5.15').
    Returns None if not a valid control ID.
    """
    cid = raw.strip()
    if cid.upper().startswith("A."):
        cid = cid[2:]
    m = re.match(r"^(\d+\.\d+)$", cid)
    if m:
        parts = cid.split(".")
        if 1 <= int(parts[0]) <= 10 and 1 <= int(parts[1]) <= 40:
            return m.group(1)
    return None


def extract_iso_ids(translation_result: dict[str, Any]) -> list[str]:
    """Extract normalized ISO 27001:2022 control IDs from translator output.

    Normalizes both A.X.XX (ISO 2013) and X.XX (ISO 2022) formats to X.XX.
    Source fields: controles_incumplidos list, then cita_normativa + justificacion text.
    """
    ids: list[str] = []
    for raw_id in translation_result.get("controles_incumplidos", []):
        normalized = _normalize_iso_id(str(raw_id))
        if normalized and normalized not in ids:
            ids.append(normalized)
    for field_name in ("cita_normativa", "justificacion"):
        text = translation_result.get(field_name, "") or ""
        for m in re.finditer(r"(?:A\.)?(\d+\.\d+)", text):
            candidate = m.group(1)
            norm = _normalize_iso_id(candidate)
            if norm and norm not in ids:
                ids.append(norm)
    return list(dict.fromkeys(ids))


def score_case(gt_ids: list[str], pred_ids: list[str]) -> dict[str, Any]:
    gt_set = set(gt_ids)
    pred_set = set(pred_ids)
    tp = len(gt_set & pred_set)
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "hallucinated_ids": sorted(pred_set - gt_set),
        "missed_ids": sorted(gt_set - pred_set),
    }


async def translate_one(
    traductor: TraductorSimbiotico, ens_code: str, ens_name: str
) -> tuple[dict[str, Any], float]:
    import time

    hallazgo = DatosRedTeam(
        origen=FuenteRedTeam.MANUAL,
        activo_detectado=f"Control ENS {ens_code}",
        evidencia=f"RD 311/2022 Anexo II medida {ens_code}: {ens_name}",
        vector_ataque=(
            f"Incumplimiento de la medida ENS {ens_code} '{ens_name}'. "
            f"Identificar controles equivalentes ISO 27001:2022."
        ),
        dificultad_explotacion=Severidad.MEDIA,
    )
    t0 = time.monotonic()
    result = await traductor.traducir(hallazgo)
    latency = round(time.monotonic() - t0, 2)
    return result.model_dump() if hasattr(result, "model_dump") else dict(result), latency


async def run_eval(
    cases: list[dict],
    limit: int | None,
    run_id: str,
) -> EvalReport:
    if limit:
        cases = cases[:limit]

    import os

    chroma_path = os.getenv("CHROMADB_PATH", ".chroma")
    rag = NormativaRAG(chromadb_path=chroma_path)
    llm = get_llm_client()
    from rosetta.core.models import MarcoNormativo

    traductor = TraductorSimbiotico(
        llm=llm, rag=rag, marcos_activos=[MarcoNormativo.ISO_27001_2022]
    )

    results: list[CaseResult] = []

    for i, case in enumerate(cases, 1):
        print(f"  [{i:3d}/{len(cases)}] {case['ens_code']} ...", end=" ", flush=True)
        cr = CaseResult(
            ens_code=case["ens_code"],
            ens_name=case["ens_name"],
            familia=case["familia"],
            nivel_exigido=case["nivel_exigido"],
            gt_iso_ids=case["iso_27001_2022_control_ids"],
            predicted_iso_ids=[],
            predicted_iso_raw="",
        )
        try:
            translation, latency = await translate_one(
                traductor, case["ens_code"], case["ens_name"]
            )
            cr.latency_s = latency
            pred_ids = extract_iso_ids(translation)
            cr.predicted_iso_ids = pred_ids
            cr.predicted_iso_raw = (translation.get("justificacion", "") or "")[:500]
            scores = score_case(case["iso_27001_2022_control_ids"], pred_ids)
            cr.true_positives = scores["true_positives"]
            cr.false_positives = scores["false_positives"]
            cr.false_negatives = scores["false_negatives"]
            cr.precision = scores["precision"]
            cr.recall = scores["recall"]
            cr.f1 = scores["f1"]
            cr.hallucinated_ids = scores["hallucinated_ids"]
            cr.missed_ids = scores["missed_ids"]
            print(f"P={cr.precision:.2f} R={cr.recall:.2f} F1={cr.f1:.2f} ({latency}s)")
        except Exception as exc:
            cr.error = str(exc)[:200]
            print(f"ERROR: {exc}")
        results.append(cr)

    ok = [r for r in results if r.error is None]
    total_fp = sum(r.false_positives for r in ok)
    total_pred = sum(r.true_positives + r.false_positives for r in ok)
    hall_rate = round(total_fp / total_pred, 4) if total_pred > 0 else 0.0

    overall_p = round(sum(r.precision for r in ok) / len(ok), 4) if ok else 0.0
    overall_r = round(sum(r.recall for r in ok) / len(ok), 4) if ok else 0.0
    overall_f1 = round(sum(r.f1 for r in ok) / len(ok), 4) if ok else 0.0

    fam_results: dict[str, list[CaseResult]] = defaultdict(list)
    for r in ok:
        fam_results[r.familia].append(r)

    per_family = []
    for fam, frs in sorted(fam_results.items()):
        fp_c = sum(r.false_positives for r in frs)
        pred_c = sum(r.true_positives + r.false_positives for r in frs)
        per_family.append(
            FamilyReport(
                familia=fam,
                n_cases=len(frs),
                avg_precision=round(sum(r.precision for r in frs) / len(frs), 4),
                avg_recall=round(sum(r.recall for r in frs) / len(frs), 4),
                avg_f1=round(sum(r.f1 for r in frs) / len(frs), 4),
                hallucination_rate=round(fp_c / pred_c, 4) if pred_c > 0 else 0.0,
            )
        )

    return EvalReport(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        marco="ens",
        total_cases=len(cases),
        evaluated=len(ok),
        errors=len(results) - len(ok),
        overall_precision=overall_p,
        overall_recall=overall_r,
        overall_f1=overall_f1,
        hallucination_rate=hall_rate,
        per_family=per_family,
        cases=results,
    )


def write_reports(report: EvalReport, reports_dir: Path, run_id: str) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    base = run_id.replace(":", "-")

    json_path = reports_dir / f"{base}_eval_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    md_path = reports_dir / f"{base}_eval_report.md"
    lines = [
        "# Eval Report — ENS → ISO 27001:2022\n\n",
        f"**Run ID:** `{report.run_id}`  \n",
        f"**Timestamp:** {report.timestamp}  \n",
        f"**Marco:** {report.marco}  \n",
        f"**Casos evaluados:** {report.evaluated}/{report.total_cases}  \n",
        f"**Errores:** {report.errors}  \n\n",
        "## Métricas globales\n\n",
        "| Métrica | Valor |\n",
        "|---------|-------|\n",
        f"| Precision (macro avg) | {report.overall_precision:.4f} |\n",
        f"| Recall (macro avg) | {report.overall_recall:.4f} |\n",
        f"| F1 (macro avg) | {report.overall_f1:.4f} |\n",
        f"| Tasa de alucinación | {report.hallucination_rate:.4f} |\n\n",
        "> **Nota metodológica:** ground truth del SoA del profesor "
        "(SoA_TechServ.xlsx, col 'Control ISO/IEC 27001:2022 equivalente').\n"
        "> Prohibido usar salida IA como ground truth.\n\n",
        "## Resultados por familia\n\n",
        "| Familia | N | Precision | Recall | F1 | Hal. rate |\n",
        "|---------|---|-----------|--------|----|-----------|\n",
    ]
    for fam in report.per_family:
        lines.append(
            f"| {fam.familia} | {fam.n_cases} | {fam.avg_precision:.4f} "
            f"| {fam.avg_recall:.4f} | {fam.avg_f1:.4f} "
            f"| {fam.hallucination_rate:.4f} |\n"
        )

    lines += [
        "\n## Casos detallados\n\n",
        "| Código | Nombre | F1 | P | R | TP | FP | FN | Alucinados | Perdidos |\n",
        "|--------|--------|----|---|---|----|----|----|------------|----------|\n",
    ]
    for c in report.cases:
        name_short = c.ens_name[:30]
        if c.error:
            lines.append(
                f"| {c.ens_code} | {name_short} | ERROR | — | — | — | — | — "
                f"| — | {c.error[:50]} |\n"
            )
        else:
            hall = ", ".join(c.hallucinated_ids[:4]) or "—"
            missed = ", ".join(c.missed_ids[:4]) or "—"
            lines.append(
                f"| {c.ens_code} | {name_short} | {c.f1:.4f} | {c.precision:.4f} "
                f"| {c.recall:.4f} | {c.true_positives} | {c.false_positives} "
                f"| {c.false_negatives} | {hall} | {missed} |\n"
            )

    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ROSETTA eval harness -- ENS->ISO 27001:2022 accuracy"
    )
    parser.add_argument("--marco", default="ens")
    parser.add_argument("--limit", type=int, default=None, help="Limit to N cases (quick test)")
    parser.add_argument("--out", default=str(REPORTS_DIR))
    parser.add_argument("--gt", default=str(GT_PATH))
    args = parser.parse_args()

    with open(args.gt, encoding="utf-8") as f:
        gt_data = json.load(f)

    cases = gt_data["cases"]
    print(f"Ground truth: {len(cases)} casos, {len(gt_data['metadata']['familias'])} familias")

    run_id = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    print(f"Run ID: {run_id}")
    print(f"Evaluando {args.limit or len(cases)} casos...\n")

    report = asyncio.run(run_eval(cases, args.limit, run_id))
    json_path, md_path = write_reports(report, Path(args.out), run_id)

    print(f"\n{'=' * 60}")
    print("RESULTADO GLOBAL")
    print(f"  Precision: {report.overall_precision:.4f}")
    print(f"  Recall:    {report.overall_recall:.4f}")
    print(f"  F1:        {report.overall_f1:.4f}")
    print(f"  Hal. rate: {report.hallucination_rate:.4f}")
    print(f"  Errores:   {report.errors}/{report.total_cases}")
    print(f"\nInformes guardados:\n  {json_path}\n  {md_path}")


if __name__ == "__main__":
    main()
