"""Tests del índice control → marco construido desde el corpus (RF-19)."""

from __future__ import annotations

from rosetta.core.control_marcos import marcos_de_control
from rosetta.core.models import MarcoNormativo

ISO = MarcoNormativo.ISO_27001_2022
ENS = MarcoNormativo.ENS_2022
RGPD = MarcoNormativo.RGPD
DORA = MarcoNormativo.DORA


def test_control_del_corpus_se_asigna_a_su_marco_aunque_no_se_declare() -> None:
    assert marcos_de_control("op.ext.4", [ISO]) == [ENS]


def test_control_ambiguo_prefiere_los_marcos_declarados() -> None:
    """Art.28.1 existe en el RGPD y en DORA."""
    assert marcos_de_control("Art.28.1", [RGPD]) == [RGPD]
    assert set(marcos_de_control("Art.28.1", [ISO])) == {DORA, RGPD}


def test_control_desconocido_solo_se_asigna_si_hay_un_marco_declarado() -> None:
    assert marcos_de_control("X.99", [ISO]) == [ISO]
    assert marcos_de_control("X.99", [ISO, ENS]) == []


def test_comparacion_ignora_mayusculas_y_espacios() -> None:
    assert marcos_de_control(" a.8.12 ", [ENS]) == [ISO]
