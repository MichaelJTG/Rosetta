"""
Eval harness for ROSETTA Traductor Simbiótico.

Modos de evaluación:
  correspondencia  (por defecto) — mide precisión del mapeo ENS → ISO 27001:2022
                   contra el ground truth del SoA del profesor (ens_iso.json).
  hallazgo         — mide la traducción de hallazgos técnicos reales a controles ISO 27001:2022
                   contra el ground truth provisional ens_hallazgos_tecnicos.json
                   (marcado 'pendiente revisión del autor').

Separación de falsos positivos (item 3a):
  alucinados   — IDs predichos que NO existen en el Anexo A de ISO 27001:2022 (control inventado).
  discrepancias — IDs predichos que SÍ existen en ISO 27001:2022 pero no están en el ground truth
                  (control real, pero no el que CCN-STIC 825 / el autor esperaba).

Comparativa Traductor solo vs Traductor + Validador (item 3d):
  --validar    — activa el Validador después de cada traducción y registra si aprueba o rechaza.
                 NO modifica las predicciones; mide si el Validador es un buen filtro de calidad.

Uso:
    python eval/run_eval.py [--mode correspondencia|hallazgo] [--limit N]
                            [--out eval/reports/] [--gt PATH] [--validar]

Salida:
    eval/reports/YYYY-MM-DDTHH-MM-SS_<mode>_eval_report.json
    eval/reports/YYYY-MM-DDTHH-MM-SS_<mode>_eval_report.md

Ground truth (correspondencia): SoA_TechServ.xlsx (profesor) — NOT AI-generated.
Ground truth (hallazgo): ens_hallazgos_tecnicos.json — pendiente revisión del autor.
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

# Add project root to path and load .env before importing rosetta modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).parent.parent / ".env")

from rosetta.core.models import DatosRedTeam, FuenteRedTeam, Severidad  # noqa: E402
from rosetta.core.rag import NormativaRAG  # noqa: E402
from rosetta.core.traductor import TraductorSimbiotico  # noqa: E402
from rosetta.llm.factory import get_llm_client  # noqa: E402

GT_CORRESPONDENCIA = Path(__file__).parent / "ground_truth" / "ens_iso.json"
GT_HALLAZGO = Path(__file__).parent / "ground_truth" / "ens_hallazgos_tecnicos.json"
REPORTS_DIR = Path(__file__).parent / "reports"

# ISO 27001:2022 Annex A — 93 controles en 4 cláusulas.
# Construido manualmente a partir de la norma; NO generado por IA.
# Referencia: ISO/IEC 27001:2022 Annex A (cláusulas 5–8).
VALID_ISO_27001_2022_IDS: frozenset[str] = frozenset(
    [f"5.{i}" for i in range(1, 38)]  # 5.1 – 5.37  (37 controles)
    + [f"6.{i}" for i in range(1, 9)]  # 6.1 – 6.8   (8 controles)
    + [f"7.{i}" for i in range(1, 15)]  # 7.1 – 7.14  (14 controles)
    + [f"8.{i}" for i in range(1, 35)]  # 8.1 – 8.34  (34 controles)
)  # Total: 93


@dataclass
class CaseResult:
    ens_code: str  # código ENS (correspondencia) o hallazgo_id (hallazgo)
    ens_name: str  # nombre ENS (correspondencia) o descripción (hallazgo)
    familia: str
    nivel_exigido: str  # nivel ENS (correspondencia) o dificultad_explotacion (hallazgo)
    gt_iso_ids: list[str]
    predicted_iso_ids: list[str]
    predicted_iso_raw: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    # FP breakdown (item 3a)
    hallucinated_ids: list[str] = field(default_factory=list)  # todos los FP (compat)
    alucinados: list[str] = field(default_factory=list)  # FP ∩ ¬ISO_27001_2022
    discrepancias: list[str] = field(default_factory=list)  # FP ∩ ISO_27001_2022
    missed_ids: list[str] = field(default_factory=list)
    error: str | None = None
    latency_s: float = 0.0
    # Validador (item 3d)
    validacion_valida: bool | None = None
    validacion_confianza: float | None = None
    validacion_problemas: list[str] = field(default_factory=list)
    validacion_error: str | None = None


@dataclass
class FamilyReport:
    familia: str
    n_cases: int
    avg_precision: float
    avg_recall: float
    avg_f1: float
    hallucination_rate: float  # todos los FP / total predichos
    alucinacion_rate: float = 0.0  # FP no-existentes / total predichos
    discrepancia_rate: float = 0.0  # FP válidos-mal-mapeados / total predichos


@dataclass
class EvalReport:
    run_id: str
    timestamp: str
    mode: str  # "correspondencia" | "hallazgo"
    marco: str
    total_cases: int
    evaluated: int
    errors: int
    overall_precision: float
    overall_recall: float
    overall_f1: float
    hallucination_rate: float  # FP totales / total predichos
    alucinacion_rate: float  # FP ∩ ¬ISO_27001_2022 / total predichos
    discrepancia_rate: float  # FP ∩ ISO_27001_2022 / total predichos
    per_family: list[FamilyReport]
    cases: list[CaseResult]
    validador_stats: dict[str, Any] | None = None


def _normalize_iso_id(raw: str) -> str | None:
    """Normalize ISO 27001 control ID to '5.1' format.

    Handles both ISO 2013 Annex A style ('A.5.15') and ISO 2022 style ('5.15').
    Returns None if not a valid-looking control ID pattern.
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
    """Extract normalized ISO 27001:2022 control IDs from translator output."""
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
    """Score one case and classify false positives.

    alucinados   = FP IDs that do NOT exist in ISO 27001:2022 Annex A (hallucinated control).
    discrepancias = FP IDs that DO exist in ISO 27001:2022 but were not expected per CCN-STIC 825
                   (real control, but wrong mapping — genuine disagreement, not hallucination).
    """
    gt_set = set(gt_ids)
    pred_set = set(pred_ids)
    tp = len(gt_set & pred_set)
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    all_fps = sorted(pred_set - gt_set)
    alucinados = [x for x in all_fps if x not in VALID_ISO_27001_2022_IDS]
    discrepancias = [x for x in all_fps if x in VALID_ISO_27001_2022_IDS]

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "hallucinated_ids": all_fps,
        "alucinados": alucinados,
        "discrepancias": discrepancias,
        "missed_ids": sorted(gt_set - pred_set),
    }


def _make_hallazgo_from_correspondencia(case: dict[str, Any]) -> DatosRedTeam:
    """Build DatosRedTeam for correspondencia mode (ENS code → ISO mapping)."""
    return DatosRedTeam(
        origen=FuenteRedTeam.MANUAL,
        activo_detectado=f"Control ENS {case['ens_code']}",
        evidencia=f"RD 311/2022 Anexo II medida {case['ens_code']}: {case['ens_name']}",
        vector_ataque=(
            f"Incumplimiento de la medida ENS {case['ens_code']} '{case['ens_name']}'. "
            f"Identificar controles equivalentes ISO 27001:2022."
        ),
        dificultad_explotacion=Severidad.MEDIA,
    )


def _make_hallazgo_from_tecnico(case: dict[str, Any]) -> DatosRedTeam:
    """Build DatosRedTeam for hallazgo técnico mode (real technical finding)."""
    h = case["hallazgo"]
    severidad_map = {
        "informativa": Severidad.INFORMATIVA,
        "baja": Severidad.BAJA,
        "media": Severidad.MEDIA,
        "alta": Severidad.ALTA,
        "critica": Severidad.CRITICA,
    }
    return DatosRedTeam(
        origen=FuenteRedTeam(h["origen"]),
        activo_detectado=h["activo_detectado"],
        evidencia=h["evidencia"],
        vector_ataque=h["vector_ataque"],
        dificultad_explotacion=severidad_map.get(h["dificultad_explotacion"], Severidad.MEDIA),
    )


async def run_eval(
    cases: list[dict[str, Any]],
    limit: int | None,
    run_id: str,
    mode: str = "correspondencia",
    validar: bool = False,
) -> EvalReport:
    import os
    import time

    if limit:
        cases = cases[:limit]

    chroma_path = os.getenv("CHROMADB_PATH", ".chroma")
    rag = NormativaRAG(chromadb_path=chroma_path)
    llm = get_llm_client()

    from rosetta.core.models import MarcoNormativo  # noqa: PLC0415

    traductor = TraductorSimbiotico(
        llm=llm, rag=rag, marcos_activos=[MarcoNormativo.ISO_27001_2022]
    )

    validador = None
    if validar:
        from rosetta.agents.validator import Validador  # noqa: PLC0415

        validador = Validador(llm=llm)

    results: list[CaseResult] = []

    for i, case in enumerate(cases, 1):
        case_id = case.get("ens_code") or case.get("hallazgo_id", f"case-{i}")
        case_name = case.get("ens_name") or case.get("descripcion", "")
        familia = case.get("familia", "")
        nivel = case.get("nivel_exigido") or case.get("hallazgo", {}).get(
            "dificultad_explotacion", ""
        )

        print(f"  [{i:3d}/{len(cases)}] {case_id} ...", end=" ", flush=True)

        cr = CaseResult(
            ens_code=case_id,
            ens_name=case_name,
            familia=familia,
            nivel_exigido=nivel,
            gt_iso_ids=case["iso_27001_2022_control_ids"],
            predicted_iso_ids=[],
            predicted_iso_raw="",
        )

        try:
            if mode == "correspondencia":
                hallazgo = _make_hallazgo_from_correspondencia(case)
            else:
                hallazgo = _make_hallazgo_from_tecnico(case)

            t0 = time.monotonic()
            result = await traductor.traducir(hallazgo)
            latency = round(time.monotonic() - t0, 2)
            cr.latency_s = latency

            translation = result.model_dump() if hasattr(result, "model_dump") else dict(result)
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
            cr.alucinados = scores["alucinados"]
            cr.discrepancias = scores["discrepancias"]
            cr.missed_ids = scores["missed_ids"]

            print(
                f"P={cr.precision:.2f} R={cr.recall:.2f} F1={cr.f1:.2f} "
                f"aluc={len(cr.alucinados)} disc={len(cr.discrepancias)} ({latency}s)",
                end="",
            )

            if validador is not None:
                from rosetta.core.models import Traduccion  # noqa: PLC0415

                tr = Traduccion(
                    marco=MarcoNormativo.ISO_27001_2022,
                    datos=result,
                    agente_id="rosetta-traductor",
                    fragmentos_usados=pred_ids,
                    confianza=0.8,
                )
                try:
                    vr = await validador.validar(tr, hallazgo)
                    cr.validacion_valida = vr.valida
                    cr.validacion_confianza = vr.confianza
                    cr.validacion_problemas = vr.problemas
                    print(f" | validador={'OK' if vr.valida else 'KO'}", end="")
                except Exception as vexc:
                    cr.validacion_error = str(vexc)[:100]
                    print(" | validador=ERR", end="")

            print()

        except Exception as exc:
            cr.error = str(exc)[:200]
            print(f"ERROR: {exc}")

        results.append(cr)

    ok = [r for r in results if r.error is None]

    total_pred = sum(r.true_positives + r.false_positives for r in ok)
    total_fp = sum(r.false_positives for r in ok)
    total_aluc = sum(len(r.alucinados) for r in ok)
    total_disc = sum(len(r.discrepancias) for r in ok)

    hall_rate = round(total_fp / total_pred, 4) if total_pred > 0 else 0.0
    aluc_rate = round(total_aluc / total_pred, 4) if total_pred > 0 else 0.0
    disc_rate = round(total_disc / total_pred, 4) if total_pred > 0 else 0.0

    overall_p = round(sum(r.precision for r in ok) / len(ok), 4) if ok else 0.0
    overall_r = round(sum(r.recall for r in ok) / len(ok), 4) if ok else 0.0
    overall_f1 = round(sum(r.f1 for r in ok) / len(ok), 4) if ok else 0.0

    fam_results: dict[str, list[CaseResult]] = defaultdict(list)
    for r in ok:
        fam_results[r.familia].append(r)

    per_family = []
    for fam, frs in sorted(fam_results.items()):
        fp_c = sum(r.false_positives for r in frs)
        aluc_c = sum(len(r.alucinados) for r in frs)
        disc_c = sum(len(r.discrepancias) for r in frs)
        pred_c = sum(r.true_positives + r.false_positives for r in frs)
        per_family.append(
            FamilyReport(
                familia=fam,
                n_cases=len(frs),
                avg_precision=round(sum(r.precision for r in frs) / len(frs), 4),
                avg_recall=round(sum(r.recall for r in frs) / len(frs), 4),
                avg_f1=round(sum(r.f1 for r in frs) / len(frs), 4),
                hallucination_rate=round(fp_c / pred_c, 4) if pred_c > 0 else 0.0,
                alucinacion_rate=round(aluc_c / pred_c, 4) if pred_c > 0 else 0.0,
                discrepancia_rate=round(disc_c / pred_c, 4) if pred_c > 0 else 0.0,
            )
        )

    # Validador stats — mide si es buen filtro de calidad (item 3d)
    validador_stats: dict[str, Any] | None = None
    if validar:
        val_ok = [r for r in ok if r.validacion_valida is not None]
        rejected = [r for r in val_ok if r.validacion_valida is False]
        approved = [r for r in val_ok if r.validacion_valida is True]
        # "rejection_precision": % de rechazados donde F1 < 0.5 (el Validador tenía razón)
        rej_prec = (
            round(sum(1 for r in rejected if r.f1 < 0.5) / len(rejected), 4) if rejected else None
        )
        validador_stats = {
            "cases_with_validacion": len(val_ok),
            "cases_approved": len(approved),
            "cases_rejected": len(rejected),
            "approved_avg_f1": round(sum(r.f1 for r in approved) / len(approved), 4)
            if approved
            else None,
            "rejected_avg_f1": round(sum(r.f1 for r in rejected) / len(rejected), 4)
            if rejected
            else None,
            "rejection_precision_at_f1_05": rej_prec,
            "note": (
                "rejection_precision_at_f1_05: fracción de casos rechazados por el Validador "
                "cuyo F1 real es < 0.5 (el Validador acertó al rechazar)."
            ),
        }

    return EvalReport(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        mode=mode,
        marco="ens",
        total_cases=len(cases),
        evaluated=len(ok),
        errors=len(results) - len(ok),
        overall_precision=overall_p,
        overall_recall=overall_r,
        overall_f1=overall_f1,
        hallucination_rate=hall_rate,
        alucinacion_rate=aluc_rate,
        discrepancia_rate=disc_rate,
        per_family=per_family,
        cases=results,
        validador_stats=validador_stats,
    )


def write_reports(report: EvalReport, reports_dir: Path, run_id: str) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    base = f"{run_id.replace(':', '-')}_{report.mode}"

    json_path = reports_dir / f"{base}_eval_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    mode_label = (
        "ENS → ISO 27001:2022 (correspondencia)"
        if report.mode == "correspondencia"
        else "Hallazgos técnicos → ISO 27001:2022"
    )
    md_path = reports_dir / f"{base}_eval_report.md"
    lines = [
        f"# Eval Report — {mode_label}\n\n",
        f"**Run ID:** `{report.run_id}`  \n",
        f"**Modo:** `{report.mode}`  \n",
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
        f"| Tasa FP total | {report.hallucination_rate:.4f} |\n",
        f"| — Tasa **alucinación** (control inventado) | {report.alucinacion_rate:.4f} |\n",
        f"| — Tasa **discrepancia** (control real, mapeo distinto) | {report.discrepancia_rate:.4f} |\n\n",
        "> **Nota metodológica:** ground truth del SoA del profesor "
        "(SoA_TechServ.xlsx) para modo correspondencia; "
        "casos ficticios pendientes de revisión del autor para modo hallazgo.  \n"
        "> **Prohibido usar salida IA como ground truth.**  \n"
        "> Alucinación ≠ Discrepancia: un control inventado es cualitativamente peor "
        "que un control real con mapeo diferente.\n\n",
    ]

    if report.validador_stats:
        vs = report.validador_stats
        lines += [
            "## Comparativa Traductor solo vs Traductor + Validador\n\n",
            "| Métrica | Valor |\n",
            "|---------|-------|\n",
            f"| Casos con validación | {vs['cases_with_validacion']} |\n",
            f"| Aprobados por Validador | {vs['cases_approved']} |\n",
            f"| Rechazados por Validador | {vs['cases_rejected']} |\n",
            f"| F1 medio (aprobados) | {vs['approved_avg_f1']} |\n",
            f"| F1 medio (rechazados) | {vs['rejected_avg_f1']} |\n",
            f"| Precision rechazo @F1<0.5 | {vs['rejection_precision_at_f1_05']} |\n\n",
            "> Si F1(rechazados) < F1(aprobados), el Validador discrimina correctamente.  \n"
            "> Precision rechazo @F1<0.5: fracción de rechazos donde el Traductor "
            "efectivamente se equivocaba (F1 < 0.5).  \n\n",
        ]

    lines += [
        "## Resultados por familia\n\n",
        "| Familia | N | Precision | Recall | F1 | FP total | Aluc. | Discr. |\n",
        "|---------|---|-----------|--------|----|---------:|------:|-------:|\n",
    ]
    for fam in report.per_family:
        lines.append(
            f"| {fam.familia} | {fam.n_cases} | {fam.avg_precision:.4f} "
            f"| {fam.avg_recall:.4f} | {fam.avg_f1:.4f} "
            f"| {fam.hallucination_rate:.4f} "
            f"| {fam.alucinacion_rate:.4f} "
            f"| {fam.discrepancia_rate:.4f} |\n"
        )

    lines += [
        "\n## Casos detallados\n\n",
        "| Código | Nombre | F1 | P | R | TP | FP | FN | Alucinados | Discrepancias | Perdidos |\n",
        "|--------|--------|----|---|---|----|----|----|------------|---------------|----------|\n",
    ]
    for c in report.cases:
        name_short = c.ens_name[:28]
        if c.error:
            lines.append(
                f"| {c.ens_code} | {name_short} | ERROR | — | — | — | — | — "
                f"| — | — | {c.error[:50]} |\n"
            )
        else:
            aluc = ", ".join(c.alucinados[:3]) or "—"
            disc = ", ".join(c.discrepancias[:3]) or "—"
            missed = ", ".join(c.missed_ids[:3]) or "—"
            val_col = ""
            if c.validacion_valida is not None:
                val_col = f" ({'OK' if c.validacion_valida else 'KO'})"
            lines.append(
                f"| {c.ens_code} | {name_short}{val_col} | {c.f1:.4f} | {c.precision:.4f} "
                f"| {c.recall:.4f} | {c.true_positives} | {c.false_positives} "
                f"| {c.false_negatives} | {aluc} | {disc} | {missed} |\n"
            )

    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "ROSETTA eval harness. "
            "Modos: 'correspondencia' (ENS→ISO, ground truth del profesor) "
            "| 'hallazgo' (hallazgo técnico, ground truth provisional)."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["correspondencia", "hallazgo"],
        default="correspondencia",
        help="Modo de evaluación (default: correspondencia)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limitar a N casos (prueba rápida)")
    parser.add_argument("--out", default=str(REPORTS_DIR))
    parser.add_argument(
        "--gt",
        default=None,
        help="Path al fichero de ground truth (por defecto según --mode)",
    )
    parser.add_argument(
        "--validar",
        action="store_true",
        default=False,
        help="Activar Validador tras cada traducción (comparativa item 3d)",
    )
    args = parser.parse_args()

    # Seleccionar GT por defecto según modo
    gt_path = (
        Path(args.gt)
        if args.gt
        else (GT_HALLAZGO if args.mode == "hallazgo" else GT_CORRESPONDENCIA)
    )

    with open(gt_path, encoding="utf-8") as f:
        gt_data = json.load(f)

    cases = gt_data["cases"]

    # Advertencia para modo hallazgo con ground truth pendiente
    if (
        args.mode == "hallazgo"
        and gt_data.get("metadata", {}).get("revision_global") == "pendiente"
    ):
        print(
            "AVISO: ground truth 'hallazgo' esta PENDIENTE de revision del autor.\n"
            "   Los resultados son orientativos, no definitivos.\n"
        )

    fam_count = len(gt_data["metadata"].get("familias", []))
    print(f"Ground truth: {len(cases)} casos, {fam_count} familias  [{gt_path.name}]")
    print(f"Modo: {args.mode}  |  Validador: {'activado' if args.validar else 'desactivado'}")

    run_id = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    print(f"Run ID: {run_id}")
    print(f"Evaluando {args.limit or len(cases)} casos...\n")

    report = asyncio.run(run_eval(cases, args.limit, run_id, mode=args.mode, validar=args.validar))
    json_path, md_path = write_reports(report, Path(args.out), run_id)

    print(f"\n{'=' * 60}")
    print(f"RESULTADO GLOBAL  [{report.mode}]")
    print(f"  Precision:    {report.overall_precision:.4f}")
    print(f"  Recall:       {report.overall_recall:.4f}")
    print(f"  F1:           {report.overall_f1:.4f}")
    print(f"  FP total:     {report.hallucination_rate:.4f}")
    print(f"  — Alucinados: {report.alucinacion_rate:.4f}  (control inventado)")
    print(f"  — Discrepancias: {report.discrepancia_rate:.4f}  (control real, mapeo distinto)")
    print(f"  Errores:      {report.errors}/{report.total_cases}")

    if report.validador_stats:
        vs = report.validador_stats
        print("\n  Validador:")
        print(f"    Aprobados:          {vs['cases_approved']}")
        print(f"    Rechazados:         {vs['cases_rejected']}")
        print(f"    F1 medio aprobados: {vs['approved_avg_f1']}")
        print(f"    F1 medio rechazados:{vs['rejected_avg_f1']}")
        print(f"    Precision rechazo:  {vs['rejection_precision_at_f1_05']}")

    print(f"\nInformes guardados:\n  {json_path}\n  {md_path}")


if __name__ == "__main__":
    main()
