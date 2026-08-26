"""
Tests de Integración - Pilar 3: Routing (Ruteo condicional)

Verifica que las bifurcaciones del grafo lleven al nodo correcto.
Si el routing falla, el sistema va por el camino equivocado.

Preguntas que responden estos tests:
- ¿CAN_ANSWER va a research?
- ¿NO_MATCH va a END?
- ¿PARTIAL va a research?
- ¿Supported: YES va a END?
- ¿Supported: NO hace re_research?
- ¿El grafo completo rutea correctamente?
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from agents.relevance_checker import RelevanceClassification
from agents.workflow import AgentWorkflow


@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


@pytest.fixture
def workflow():
    """Workflow con agentes mock."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                return AgentWorkflow()


# ============================================================
# TESTS: Routing después de check_relevance
# ============================================================

class TestRoutingAfterRelevanceCheck:
    """Verifica que check_relevance rutea correctamente."""

    def test_can_answer_routes_to_research(self, workflow):
        """CAN_ANSWER debe routing a 'relevant' → research."""
        # GIVEN
        state = {"is_relevant": True}

        # WHEN
        result = workflow._decide_after_relevance_check(state)

        # THEN
        assert result == "relevant"

    def test_partial_routes_to_research(self, workflow):
        """PARTIAL debe routing a 'relevant' → research."""
        # GIVEN
        state = {"is_relevant": True}  # PARTIAL también设置 is_relevant=True

        # WHEN
        result = workflow._decide_after_relevance_check(state)

        # THEN
        assert result == "relevant"

    def test_no_match_routes_to_end(self, workflow):
        """NO_MATCH debe routing a 'irrelevant' → END."""
        # GIVEN
        state = {"is_relevant": False}

        # WHEN
        result = workflow._decide_after_relevance_check(state)

        # THEN
        assert result == "irrelevant"

    def test_can_answer_sets_is_relevant_true(self, workflow):
        """_check_relevance_step debe设置 is_relevant=True cuando CAN_ANSWER."""
        # GIVEN
        workflow.relevance_checker = MagicMock()
        workflow.relevance_checker.check.return_value = RelevanceClassification.CAN_ANSWER

        state = {"question": "test", "retriever": MagicMock()}

        # WHEN
        result = workflow._check_relevance_step(state)

        # THEN
        assert result["is_relevant"] is True

    def test_partial_sets_is_relevant_true(self, workflow):
        """_check_relevance_step debe设置 is_relevant=True cuando PARTIAL."""
        # GIVEN
        workflow.relevance_checker = MagicMock()
        workflow.relevance_checker.check.return_value = RelevanceClassification.PARTIAL

        state = {"question": "test", "retriever": MagicMock()}

        # WHEN
        result = workflow._check_relevance_step(state)

        # THEN
        assert result["is_relevant"] is True

    def test_no_match_sets_is_relevant_false(self, workflow):
        """_check_relevance_step debe设置 is_relevant=False cuando NO_MATCH."""
        # GIVEN
        workflow.relevance_checker = MagicMock()
        workflow.relevance_checker.check.return_value = RelevanceClassification.NO_MATCH

        state = {"question": "test", "retriever": MagicMock()}

        # WHEN
        result = workflow._check_relevance_step(state)

        # THEN
        assert result["is_relevant"] is False


# ============================================================
# TESTS: Routing después de verify
# ============================================================

class TestRoutingAfterVerification:
    """Verifica que verify rutea correctamente."""

    def test_supported_yes_routes_to_end(self, workflow):
        """Supported: YES debe routing a 'end' → END."""
        # GIVEN
        state = {"verification_report": "Supported: YES\nRelevant: YES"}

        # WHEN
        result = workflow._decide_next_step(state)

        # THEN
        assert result == "end"

    def test_supported_no_routes_to_rerun(self, workflow):
        """Supported: NO debe routing a 're_research' → research."""
        # GIVEN
        state = {"verification_report": "Supported: NO\nRelevant: YES"}

        # WHEN
        result = workflow._decide_next_step(state)

        # THEN
        assert result == "re_research"

    def test_relevant_no_routes_to_rerun(self, workflow):
        """Relevant: NO debe routing a 're_research'."""
        # GIVEN
        state = {"verification_report": "Supported: YES\nRelevant: NO"}

        # WHEN
        result = workflow._decide_next_step(state)

        # THEN
        assert result == "re_research"

    def test_both_no_routes_to_rerun(self, workflow):
        """Ambos NO deben routing a 're_research'."""
        # GIVEN
        state = {"verification_report": "Supported: NO\nRelevant: NO"}

        # WHEN
        result = workflow._decide_next_step(state)

        # THEN
        assert result == "re_research"


# ============================================================
# TESTS: Grafo completo
# ============================================================

class TestCompleteGraphRouting:
    """Verifica el routing en el grafo completo."""

    def test_full_workflow_relevant_question(self):
        """Pregunta relevante → check_relevance → research → verify → END."""
        # GIVEN
        workflow = AgentWorkflow()

        # Mock de todos los agentes
        workflow.relevance_checker = MagicMock()
        workflow.relevance_checker.check.return_value = RelevanceClassification.CAN_ANSWER

        workflow.researcher = MagicMock()
        workflow.researcher.generate.return_value = {
            "draft_answer": "Python es un lenguaje de programación."
        }

        workflow.verifier = MagicMock()
        workflow.verifier.check.return_value = {
            "verification_report": "Supported: YES\nRelevant: YES"
        }

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            Document(page_content="Python es un lenguaje.")
        ]

        # WHEN
        result = workflow.full_pipeline("¿Qué es Python?", mock_retriever)

        # THEN
        assert result["draft_answer"] == "Python es un lenguaje de programación."
        assert "Supported: YES" in result["verification_report"]

    def test_full_workflow_irrelevant_question(self):
        """Pregunta irrelevante → check_relevance → END (sin research)."""
        # GIVEN
        workflow = AgentWorkflow()

        workflow.relevance_checker = MagicMock()
        workflow.relevance_checker.check.return_value = RelevanceClassification.NO_MATCH

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            Document(page_content="Contenido no relacionado")
        ]

        # WHEN
        result = workflow.full_pipeline("¿Cuál es el precio del dólar?", mock_retriever)

        # THEN
        assert "isn't related" in result["draft_answer"].lower()
        assert result["verification_report"] == ""  # verify nunca se ejecutó
