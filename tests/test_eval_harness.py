"""
D-1: Unit tests for eval harness pure functions (C-2).

Tests cover: ID normalization, ISO ID extraction from LLM output, case scoring.
No LLM calls — all pure functions from eval/run_eval.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

# eval/ is not a package — add project root so we can import from eval/
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from eval.run_eval import _normalize_iso_id, extract_iso_ids, score_case

# ---------------------------------------------------------------------------
# _normalize_iso_id
# ---------------------------------------------------------------------------


class TestNormalizeIsoId:
    def test_plain_id(self):
        assert _normalize_iso_id("5.1") == "5.1"

    def test_annex_a_prefix_stripped(self):
        assert _normalize_iso_id("A.5.15") == "5.15"

    def test_lowercase_annex_a(self):
        assert _normalize_iso_id("a.8.24") == "8.24"

    def test_leading_trailing_whitespace(self):
        assert _normalize_iso_id("  6.7  ") == "6.7"

    def test_high_chapter_valid(self):
        assert _normalize_iso_id("10.1") == "10.1"

    def test_chapter_zero_invalid(self):
        assert _normalize_iso_id("0.1") is None

    def test_chapter_above_ten_invalid(self):
        assert _normalize_iso_id("11.1") is None

    def test_control_above_40_invalid(self):
        assert _normalize_iso_id("5.41") is None

    def test_control_zero_invalid(self):
        assert _normalize_iso_id("5.0") is None

    def test_non_numeric_returns_none(self):
        assert _normalize_iso_id("A.access") is None

    def test_empty_string_returns_none(self):
        assert _normalize_iso_id("") is None

    def test_iso_2022_high(self):
        assert _normalize_iso_id("8.34") == "8.34"


# ---------------------------------------------------------------------------
# extract_iso_ids
# ---------------------------------------------------------------------------


class TestExtractIsoIds:
    def test_from_controles_incumplidos(self):
        result_dict = {
            "controles_incumplidos": ["A.5.15", "8.24"],
            "cita_normativa": "",
            "justificacion": "",
        }
        ids = extract_iso_ids(result_dict)
        assert "5.15" in ids
        assert "8.24" in ids

    def test_deduplication(self):
        result_dict = {
            "controles_incumplidos": ["5.15", "A.5.15"],
            "cita_normativa": "",
            "justificacion": "",
        }
        ids = extract_iso_ids(result_dict)
        assert ids.count("5.15") == 1

    def test_extracted_from_justificacion_text(self):
        result_dict = {
            "controles_incumplidos": [],
            "cita_normativa": "",
            "justificacion": "Incumple el control 8.20 y también A.5.10",
        }
        ids = extract_iso_ids(result_dict)
        assert "8.20" in ids
        assert "5.10" in ids

    def test_extracted_from_cita_normativa(self):
        result_dict = {
            "controles_incumplidos": [],
            "cita_normativa": "ISO 27001:2022 controles 6.1, 6.2",
            "justificacion": "",
        }
        ids = extract_iso_ids(result_dict)
        assert "6.1" in ids
        assert "6.2" in ids

    def test_controles_take_priority_order(self):
        """IDs from controles_incumplidos appear before those from text."""
        result_dict = {
            "controles_incumplidos": ["5.1"],
            "cita_normativa": "Ver también 8.2",
            "justificacion": "",
        }
        ids = extract_iso_ids(result_dict)
        assert ids[0] == "5.1"

    def test_invalid_ids_filtered(self):
        result_dict = {
            "controles_incumplidos": ["0.1", "11.5", "5.41"],
            "cita_normativa": "",
            "justificacion": "",
        }
        ids = extract_iso_ids(result_dict)
        assert ids == []

    def test_empty_input(self):
        assert extract_iso_ids({}) == []


# ---------------------------------------------------------------------------
# score_case
# ---------------------------------------------------------------------------


class TestScoreCase:
    def test_perfect_match(self):
        gt = ["5.1", "8.2"]
        pred = ["5.1", "8.2"]
        s = score_case(gt, pred)
        assert s["precision"] == 1.0
        assert s["recall"] == 1.0
        assert s["f1"] == 1.0
        assert s["true_positives"] == 2
        assert s["false_positives"] == 0
        assert s["false_negatives"] == 0

    def test_all_false_positives(self):
        gt = ["5.1"]
        pred = ["8.2", "8.3"]
        s = score_case(gt, pred)
        assert s["precision"] == 0.0
        assert s["recall"] == 0.0
        assert s["f1"] == 0.0
        assert s["false_positives"] == 2
        assert s["false_negatives"] == 1

    def test_partial_overlap(self):
        gt = ["5.1", "5.2", "5.3"]
        pred = ["5.1", "5.2", "8.9"]
        s = score_case(gt, pred)
        assert s["true_positives"] == 2
        assert s["false_positives"] == 1
        assert s["false_negatives"] == 1
        assert round(s["precision"], 4) == round(2 / 3, 4)
        assert round(s["recall"], 4) == round(2 / 3, 4)

    def test_empty_prediction(self):
        s = score_case(["5.1", "8.2"], [])
        assert s["precision"] == 0.0
        assert s["recall"] == 0.0
        assert s["f1"] == 0.0
        assert s["false_negatives"] == 2

    def test_empty_ground_truth(self):
        s = score_case([], ["5.1"])
        assert s["precision"] == 0.0
        assert s["recall"] == 0.0
        assert s["false_positives"] == 1

    def test_hallucinated_ids_reported(self):
        gt = ["5.1"]
        pred = ["5.1", "9.9"]
        s = score_case(gt, pred)
        assert "9.9" in s["hallucinated_ids"]

    def test_missed_ids_reported(self):
        gt = ["5.1", "5.2"]
        pred = ["5.1"]
        s = score_case(gt, pred)
        assert "5.2" in s["missed_ids"]

    def test_both_empty(self):
        s = score_case([], [])
        assert s["precision"] == 0.0
        assert s["recall"] == 0.0
        assert s["f1"] == 0.0
