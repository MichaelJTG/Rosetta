"""Tests para compliance_timeline — seguimiento temporal de cumplimiento."""

from __future__ import annotations

from datetime import datetime

from rosetta.core.models import MarcoNormativo


def test_snapshot_campos() -> None:
    from rosetta.core.compliance_timeline import SnapshotCompliance

    snap = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=["A.5.1"],
        controles_ko=["A.8.24"],
    )

    assert snap.hallazgo_id == "SEC-001"
    assert MarcoNormativo.ISO_27001_2022 in snap.marcos
    assert "A.8.24" in snap.controles_ko
    assert isinstance(snap.timestamp, datetime)


def test_timeline_ultimo_snapshot() -> None:
    from rosetta.core.compliance_timeline import ComplianceTimeline, SnapshotCompliance

    t1 = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=[],
        controles_ko=["A.8.24"],
        timestamp=datetime(2026, 4, 1),
    )
    t2 = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=["A.8.24"],
        controles_ko=[],
        timestamp=datetime(2026, 4, 23),
    )

    tl = ComplianceTimeline(hallazgo_id="SEC-001", snapshots=[t1, t2])
    ultimo = tl.ultimo_snapshot()

    assert ultimo is not None
    assert ultimo.timestamp == datetime(2026, 4, 23)


def test_timeline_vacia_devuelve_none() -> None:
    from rosetta.core.compliance_timeline import ComplianceTimeline

    tl = ComplianceTimeline(hallazgo_id="SEC-001", snapshots=[])
    assert tl.ultimo_snapshot() is None


def test_timeline_tendencia_mejorando() -> None:
    from rosetta.core.compliance_timeline import ComplianceTimeline, SnapshotCompliance

    t1 = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=[],
        controles_ko=["A.8.24", "A.5.1"],
        timestamp=datetime(2026, 4, 1),
    )
    t2 = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=["A.5.1"],
        controles_ko=["A.8.24"],
        timestamp=datetime(2026, 4, 23),
    )

    tl = ComplianceTimeline(hallazgo_id="SEC-001", snapshots=[t1, t2])
    assert tl.tendencia() == "mejorando"


def test_timeline_tendencia_empeorando() -> None:
    from rosetta.core.compliance_timeline import ComplianceTimeline, SnapshotCompliance

    t1 = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=["A.5.1"],
        controles_ko=["A.8.24"],
        timestamp=datetime(2026, 4, 1),
    )
    t2 = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=[],
        controles_ko=["A.8.24", "A.5.1"],
        timestamp=datetime(2026, 4, 23),
    )

    tl = ComplianceTimeline(hallazgo_id="SEC-001", snapshots=[t1, t2])
    assert tl.tendencia() == "empeorando"


def test_timeline_tendencia_estable() -> None:
    from rosetta.core.compliance_timeline import ComplianceTimeline, SnapshotCompliance

    t1 = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=["A.5.1"],
        controles_ko=["A.8.24"],
        timestamp=datetime(2026, 4, 1),
    )
    t2 = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=["A.5.1"],
        controles_ko=["A.8.24"],
        timestamp=datetime(2026, 4, 23),
    )

    tl = ComplianceTimeline(hallazgo_id="SEC-001", snapshots=[t1, t2])
    assert tl.tendencia() == "estable"


def test_timeline_un_snapshot_es_estable() -> None:
    from rosetta.core.compliance_timeline import ComplianceTimeline, SnapshotCompliance

    snap = SnapshotCompliance(
        hallazgo_id="SEC-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
        controles_ok=["A.5.1"],
        controles_ko=[],
    )
    tl = ComplianceTimeline(hallazgo_id="SEC-001", snapshots=[snap])
    assert tl.tendencia() == "estable"
