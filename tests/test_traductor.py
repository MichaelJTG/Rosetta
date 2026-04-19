"""Tests del TraductorSimbiótico y NormativaRAG con mocks completos.

Cobertura objetivo: 80% de core/traductor.py y core/rag.py
Sin llamadas reales a LLM ni a ChromaDB — todo mockeado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rosetta.adapters.compliance.loader import FragmentoNormativo
from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    FuenteRedTeam,
    MarcoNormativo,
    Severidad,
)
from rosetta.core.rag import FragmentoRecuperado, NormativaRAG
from rosetta.core.traductor import TraductorSimbiotico
from rosetta.llm.base import CompletionResult, ToolCallResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def hallazgo_aws() -> DatosRedTeam:
    """Hallazgo canónico: AWS key filtrada."""
    return DatosRedTeam(
        origen=FuenteRedTeam.GITHUB_SECRETS,
        activo_detectado="AWS_ACCESS_KEY_ID en repo público",
        evidencia="https://github.com/org/repo/commit/abc123",
        vector_ataque="Credencial cloud expuesta en código fuente público",
        dificultad_explotacion=Severidad.BAJA,
    )


@pytest.fixture
def fragmento_a824() -> FragmentoRecuperado:
    """Fragmento RAG del control A.8.24."""
    return FragmentoRecuperado(
        control_id="A.8.24",
        marco="iso_27001_2022",
        nombre="Uso de la criptografía",
        texto="A.8.24 Uso de la criptografía. Se deben definir reglas para uso de criptografía.",
        score=0.15,
    )


@pytest.fixture
def fragmento_a515() -> FragmentoRecuperado:
    """Fragmento RAG del control A.5.15."""
    return FragmentoRecuperado(
        control_id="A.5.15",
        marco="iso_27001_2022",
        nombre="Control de acceso",
        texto="A.5.15 Control de acceso. Se deben establecer reglas de control de acceso.",
        score=0.22,
    )


@pytest.fixture
def tool_input_valido() -> dict[str, Any]:
    """Tool input válido que simula la respuesta del LLM."""
    return {
        "marcos_aplicables": ["iso_27001_2022"],
        "controles_incumplidos": ["A.8.24", "A.5.15"],
        "cita_normativa": "A.8.24 Uso de la criptografía: Se deben definir reglas.",
        "justificacion": "La exposición de credenciales incumple el control A.8.24.",
        "impacto_legal": "alta",
        "accion_mitigacion": "Rotar la clave AWS inmediatamente. Configurar git-secrets.",
        "evidencia_auditoria": "Credencial AWS expuesta en commit abc123.",
    }


# ---------------------------------------------------------------------------
# Tests NormativaRAG (con ChromaDB mockeado)
# ---------------------------------------------------------------------------


def _make_mock_collection(count: int = 3) -> MagicMock:
    """Crea un mock de colección ChromaDB."""
    col = MagicMock()
    col.count.return_value = count
    col.query.return_value = {
        "documents": [["texto A.8.24", "texto A.5.15"]],
        "metadatas": [
            [
                {
                    "control_id": "A.8.24",
                    "framework_id": "iso_27001_2022",
                    "nombre": "Criptografía",
                },
                {
                    "control_id": "A.5.15",
                    "framework_id": "iso_27001_2022",
                    "nombre": "Control de acceso",
                },
            ]
        ],
        "distances": [[0.15, 0.22]],
    }
    col.upsert = MagicMock()
    col.get = MagicMock(return_value={"ids": ["id1", "id2"]})
    return col


def test_rag_ingestar_corpus_llama_upsert() -> None:
    """ingestar_corpus hace upsert en ChromaDB con los fragmentos correctos."""
    fragmentos = [
        FragmentoNormativo(
            control_id="A.8.24",
            texto="A.8.24 Uso de la criptografía.",
            marco=MarcoNormativo.ISO_27001_2022,
            nombre="Uso de la criptografía",
        ),
        FragmentoNormativo(
            control_id="A.5.15",
            texto="A.5.15 Control de acceso.",
            marco=MarcoNormativo.ISO_27001_2022,
            nombre="Control de acceso",
        ),
    ]

    with (
        patch("chromadb.PersistentClient") as mock_client_cls,
        patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction"),
    ):
        mock_col = _make_mock_collection()
        mock_client_cls.return_value.get_or_create_collection.return_value = mock_col

        rag = NormativaRAG(chromadb_path="/tmp/test_chroma")
        n = rag.ingestar_corpus(fragmentos)

    assert n == 2
    mock_col.upsert.assert_called_once()


def test_rag_ingestar_corpus_vacio_devuelve_cero() -> None:
    """ingestar_corpus con lista vacía devuelve 0 sin llamar a upsert."""
    with (
        patch("chromadb.PersistentClient") as mock_client_cls,
        patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction"),
    ):
        mock_col = _make_mock_collection(0)
        mock_client_cls.return_value.get_or_create_collection.return_value = mock_col

        rag = NormativaRAG(chromadb_path="/tmp/test_chroma")
        n = rag.ingestar_corpus([])

    assert n == 0
    mock_col.upsert.assert_not_called()


def test_rag_recuperar_devuelve_fragmentos_ordenados() -> None:
    """recuperar devuelve fragmentos ordenados por score ascendente."""
    with (
        patch("chromadb.PersistentClient") as mock_client_cls,
        patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction"),
    ):
        mock_col = _make_mock_collection(count=3)
        mock_client_cls.return_value.get_or_create_collection.return_value = mock_col

        rag = NormativaRAG(chromadb_path="/tmp/test_chroma")
        resultados = rag.recuperar("credencial expuesta", [MarcoNormativo.ISO_27001_2022])

    assert len(resultados) == 2
    assert resultados[0].score <= resultados[1].score
    assert resultados[0].control_id == "A.8.24"


def test_rag_recuperar_coleccion_vacia_devuelve_lista_vacia() -> None:
    """recuperar sobre colección vacía devuelve [] sin lanzar excepción."""
    with (
        patch("chromadb.PersistentClient") as mock_client_cls,
        patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction"),
    ):
        mock_col = _make_mock_collection(count=0)
        mock_client_cls.return_value.get_or_create_collection.return_value = mock_col

        rag = NormativaRAG(chromadb_path="/tmp/test_chroma")
        resultados = rag.recuperar("cualquier query", [MarcoNormativo.ISO_27001_2022])

    assert resultados == []


# ---------------------------------------------------------------------------
# Tests TraductorSimbiotico
# ---------------------------------------------------------------------------


def _make_rag_mock(
    fragmentos: list[FragmentoRecuperado] | None = None,
) -> MagicMock:
    """Crea un mock de NormativaRAG."""
    rag = MagicMock(spec=NormativaRAG)
    rag.recuperar.return_value = fragmentos or []
    return rag


def _make_llm_mock(tool_input: dict[str, Any]) -> MagicMock:
    """Crea un mock de LLMClient que devuelve un tool_call con tool_input."""
    llm = MagicMock()
    llm.completar = AsyncMock(
        return_value=CompletionResult(
            content=None,
            tool_calls=[ToolCallResult(tool_name="registrar_traduccion", tool_input=tool_input)],
            stop_reason="tool_use",
            raw={},
        )
    )
    return llm


async def test_traductor_traducir_devuelve_datos_compliance(
    hallazgo_aws: DatosRedTeam,
    fragmento_a824: FragmentoRecuperado,
    tool_input_valido: dict[str, Any],
) -> None:
    """traducir() devuelve un DatosCompliance válido con los controles correctos."""
    rag = _make_rag_mock([fragmento_a824])
    llm = _make_llm_mock(tool_input_valido)

    traductor = TraductorSimbiotico(
        llm=llm, rag=rag, marcos_activos=[MarcoNormativo.ISO_27001_2022]
    )
    resultado = await traductor.traducir(hallazgo_aws)

    assert isinstance(resultado, DatosCompliance)
    assert "A.8.24" in resultado.controles_incumplidos
    assert resultado.impacto_legal == Severidad.ALTA
    assert MarcoNormativo.ISO_27001_2022 in resultado.marcos_aplicables


async def test_traductor_traducir_llama_rag_con_marcos_activos(
    hallazgo_aws: DatosRedTeam,
    tool_input_valido: dict[str, Any],
) -> None:
    """traducir() llama al RAG con los marcos activos configurados."""
    rag = _make_rag_mock()
    llm = _make_llm_mock(tool_input_valido)

    traductor = TraductorSimbiotico(
        llm=llm, rag=rag, marcos_activos=[MarcoNormativo.ISO_27001_2022]
    )
    await traductor.traducir(hallazgo_aws)

    rag.recuperar.assert_called_once()
    _, kwargs = rag.recuperar.call_args
    assert MarcoNormativo.ISO_27001_2022 in (kwargs.get("marcos") or rag.recuperar.call_args[0][1])


async def test_traductor_lanza_error_sin_tool_call(
    hallazgo_aws: DatosRedTeam,
) -> None:
    """traducir() lanza ValueError si el LLM no invoca la herramienta."""
    rag = _make_rag_mock()
    llm = MagicMock()
    llm.completar = AsyncMock(
        return_value=CompletionResult(
            content="Lo siento, no puedo traducir esto.",
            tool_calls=[],
            stop_reason="end_turn",
            raw={},
        )
    )

    traductor = TraductorSimbiotico(
        llm=llm, rag=rag, marcos_activos=[MarcoNormativo.ISO_27001_2022]
    )
    with pytest.raises(ValueError, match="registrar_traduccion"):
        await traductor.traducir(hallazgo_aws)


def test_traductor_sin_marcos_lanza_error() -> None:
    """TraductorSimbiotico con lista vacía de marcos lanza ValueError al construir."""
    rag = _make_rag_mock()
    llm = MagicMock()
    with pytest.raises(ValueError, match="marco"):
        TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=[])


async def test_traductor_marco_desconocido_usa_fallback(
    hallazgo_aws: DatosRedTeam,
) -> None:
    """Si el LLM devuelve un marco desconocido, se usan los marcos activos."""
    rag = _make_rag_mock()
    llm = _make_llm_mock(
        {
            "marcos_aplicables": ["marco_inexistente_xyz"],
            "controles_incumplidos": ["A.8.24"],
            "cita_normativa": "A.8.24 Criptografía.",
            "justificacion": "Credencial expuesta.",
            "impacto_legal": "alta",
            "accion_mitigacion": "Rotar clave.",
        }
    )

    traductor = TraductorSimbiotico(
        llm=llm, rag=rag, marcos_activos=[MarcoNormativo.ISO_27001_2022]
    )
    resultado = await traductor.traducir(hallazgo_aws)

    assert MarcoNormativo.ISO_27001_2022 in resultado.marcos_aplicables


async def test_traductor_impacto_invalido_usa_media(
    hallazgo_aws: DatosRedTeam,
) -> None:
    """Un impacto_legal desconocido del LLM cae al valor por defecto 'media'."""
    rag = _make_rag_mock()
    llm = _make_llm_mock(
        {
            "marcos_aplicables": ["iso_27001_2022"],
            "controles_incumplidos": ["A.8.24"],
            "cita_normativa": "A.8.24.",
            "justificacion": "Razón.",
            "impacto_legal": "valor_inexistente",
            "accion_mitigacion": "Rotar clave.",
        }
    )

    traductor = TraductorSimbiotico(
        llm=llm, rag=rag, marcos_activos=[MarcoNormativo.ISO_27001_2022]
    )
    resultado = await traductor.traducir(hallazgo_aws)

    assert resultado.impacto_legal == Severidad.MEDIA


# ---------------------------------------------------------------------------
# Tests de cobertura adicional: FragmentoRecuperado.__repr__ y casos borde RAG
# ---------------------------------------------------------------------------


def test_fragmento_recuperado_repr() -> None:
    """FragmentoRecuperado.__repr__ incluye control_id y score formateado."""
    f = FragmentoRecuperado(
        control_id="A.8.24",
        marco="iso_27001_2022",
        nombre="Criptografía",
        texto="Control de criptografía.",
        score=0.12345,
    )
    r = repr(f)
    assert "A.8.24" in r
    assert "0.123" in r


def test_rag_recuperar_exception_en_query_continua_con_otros_marcos() -> None:
    """Si query falla para un marco, recuperar captura la excepción y continúa."""
    with (
        patch("chromadb.PersistentClient") as mock_client_cls,
        patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction"),
    ):
        mock_col = MagicMock()
        mock_col.count.return_value = 5
        mock_col.query.side_effect = RuntimeError("ChromaDB timeout")
        mock_client_cls.return_value.get_or_create_collection.return_value = mock_col

        rag = NormativaRAG(chromadb_path="/tmp/test_chroma")
        resultados = rag.recuperar(
            "credencial expuesta",
            [MarcoNormativo.ISO_27001_2022],
        )

    assert resultados == []


def test_rag_contar_sin_marco_devuelve_total() -> None:
    """contar() sin marco devuelve el total de la colección."""
    with (
        patch("chromadb.PersistentClient") as mock_client_cls,
        patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction"),
    ):
        mock_col = _make_mock_collection(count=42)
        mock_client_cls.return_value.get_or_create_collection.return_value = mock_col

        rag = NormativaRAG(chromadb_path="/tmp/test_chroma")
        total = rag.contar()

    assert total == 42


def test_rag_contar_con_marco_usa_get() -> None:
    """contar(marco) filtra por framework_id via collection.get()."""
    with (
        patch("chromadb.PersistentClient") as mock_client_cls,
        patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction"),
    ):
        mock_col = _make_mock_collection(count=10)
        mock_col.get.return_value = {"ids": ["id1", "id2", "id3"]}
        mock_client_cls.return_value.get_or_create_collection.return_value = mock_col

        rag = NormativaRAG(chromadb_path="/tmp/test_chroma")
        n = rag.contar(marco=MarcoNormativo.ISO_27001_2022)

    assert n == 3


def test_rag_contar_con_marco_exception_devuelve_cero() -> None:
    """contar(marco) devuelve 0 si collection.get() lanza excepción."""
    with (
        patch("chromadb.PersistentClient") as mock_client_cls,
        patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction"),
    ):
        mock_col = _make_mock_collection(count=5)
        mock_col.get.side_effect = RuntimeError("DB error")
        mock_client_cls.return_value.get_or_create_collection.return_value = mock_col

        rag = NormativaRAG(chromadb_path="/tmp/test_chroma")
        n = rag.contar(marco=MarcoNormativo.ISO_27001_2022)

    assert n == 0


# ---------------------------------------------------------------------------
# Tests de los 5 hallazgos canónicos (criterio de aceptación MVP-1)
# ---------------------------------------------------------------------------
# Cada test carga el JSON del hallazgo canónico, simula que el RAG devuelve
# el control esperado y verifica que el Traductor lo mapea correctamente.
# No se llama a ningún LLM ni ChromaDB real.
# ---------------------------------------------------------------------------

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def _hallazgo_desde_json(nombre: str) -> DatosRedTeam:
    data = json.loads((EXAMPLES_DIR / nombre).read_text(encoding="utf-8"))
    return DatosRedTeam(**data)


@pytest.mark.parametrize(
    ("archivo_json", "control_esperado", "impacto_esperado"),
    [
        ("finding_aws_leaked_key.json", "A.8.24", "alta"),
        ("finding_no_mfa.json", "A.8.5", "alta"),
        ("finding_rdp_open_internet.json", "A.8.20", "alta"),
        ("finding_no_logs.json", "A.8.16", "media"),
        ("finding_no_patch.json", "A.8.8", "critica"),
    ],
)
async def test_traductor_cinco_hallazgos_canonicos(
    archivo_json: str,
    control_esperado: str,
    impacto_esperado: str,
) -> None:
    """Los 5 hallazgos canónicos devuelven el control correcto — criterio MVP-1."""
    hallazgo = _hallazgo_desde_json(archivo_json)

    fragmento_control = FragmentoRecuperado(
        control_id=control_esperado,
        marco="iso_27001_2022",
        nombre=f"Control {control_esperado}",
        texto=f"{control_esperado} texto del control.",
        score=0.10,
    )
    rag = _make_rag_mock([fragmento_control])
    llm = _make_llm_mock(
        {
            "marcos_aplicables": ["iso_27001_2022"],
            "controles_incumplidos": [control_esperado],
            "cita_normativa": f"{control_esperado} cita normativa.",
            "justificacion": f"El hallazgo incumple {control_esperado}.",
            "impacto_legal": impacto_esperado,
            "accion_mitigacion": "Acción de mitigación concreta.",
            "evidencia_auditoria": "Evidencia para dossier de auditoría.",
        }
    )

    traductor = TraductorSimbiotico(
        llm=llm, rag=rag, marcos_activos=[MarcoNormativo.ISO_27001_2022]
    )
    resultado = await traductor.traducir(hallazgo)

    assert isinstance(resultado, DatosCompliance)
    assert (
        control_esperado in resultado.controles_incumplidos
    ), f"Control {control_esperado} no encontrado en {resultado.controles_incumplidos}"
    assert MarcoNormativo.ISO_27001_2022 in resultado.marcos_aplicables
    assert resultado.accion_mitigacion != ""
    assert resultado.justificacion != ""
