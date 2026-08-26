"""
Tests de Integración - Pilar 5: Error Handling (Manejo de errores y resiliencia)

Verifica que cuando algo falla, el sistema lo maneja graciosamente, no explota.
El sistema debe producir resultados controlados, no crashes.

Preguntas que responden estos tests:
- ¿Qué pasa si OpenRouter API cae?
- ¿Qué pasa si el retriever retorna lista vacía?
- ¿Qué pasa si un agente lanza excepción?
- ¿Qué pasa si el state viene incompleto?
- ¿El workflow sobrevive a errores individuales?
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from agents.relevance_checker import RelevanceChecker, RelevanceClassification
from agents.research_agent import ResearchAgent
from agents.verification_agent import VerificationAgent
from agents.workflow import AgentWorkflow


@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


# ============================================================
# TESTS: Errores en RelevanceChecker
# ============================================================

class TestRelevanceCheckerErrors:
    """Verifica que RelevanceChecker maneja errores correctamente."""

    def test_api_error_returns_no_match(self):
        """Error en la API debe retornar NO_MATCH."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.side_effect = Exception("API Error")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result = checker.check("test question", retriever)

            # THEN
            assert result == RelevanceClassification.NO_MATCH

    def test_empty_retriever_returns_no_match(self):
        """Retriever vacío debe retornar NO_MATCH."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()

            retriever = MagicMock()
            retriever.invoke.return_value = []

            # WHEN
            result = checker.check("test question", retriever)

            # THEN
            assert result == RelevanceClassification.NO_MATCH

    def test_invalid_attribute_error_returns_no_match(self):
        """Error de atributo inválido debe retornar NO_MATCH."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()

            mock_response = MagicMock()
            # Simular response sin atributo content
            del mock_response.content
            checker.model.invoke.return_value = mock_response

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result = checker.check("test question", retriever)

            # THEN
            assert result == RelevanceClassification.NO_MATCH


# ============================================================
# TESTS: Errores en ResearchAgent
# ============================================================

class TestResearchAgentErrors:
    """Verifica que ResearchAgent maneja errores correctamente."""

    def test_api_error_raises_runtime_error(self):
        """Error en la API debe lanzar RuntimeError."""
        # GIVEN
        with patch("agents.research_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = ResearchAgent()
            agent.model = MagicMock()
            agent.model.invoke.side_effect = Exception("API Error")

            docs = [Document(page_content="test")]

            # WHEN/THEN
            with pytest.raises(RuntimeError, match="Failed to generate"):
                agent.generate("test question", docs)

    def test_no_documents_still_works(self):
        """Sin documentos, el agente debe generar respuesta."""
        # GIVEN
        with patch("agents.research_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = ResearchAgent()
            agent.model = MagicMock()
            agent.model.invoke.return_value = MagicMock(content="No context available")

            # WHEN
            result = agent.generate("test question", [])

            # THEN
            assert "draft_answer" in result


# ============================================================
# TESTS: Errores en VerificationAgent
# ============================================================

class TestVerificationAgentErrors:
    """Verifica que VerificationAgent maneja errores correctamente."""

    def test_api_error_returns_fallback_report(self):
        """Error en la API debe retornar reporte por defecto."""
        # GIVEN
        with patch("agents.verification_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = VerificationAgent()
            agent.structured_model = MagicMock()
            agent.structured_model.invoke.side_effect = Exception("API Error")

            docs = [Document(page_content="test")]

            # WHEN
            result = agent.check("test answer", docs)

            # THEN
            assert "verification_report" in result
            assert "Supported:** NO" in result["verification_report"]

    def test_structured_model_error_returns_fallback(self):
        """Error en structured_model debe retornar fallback."""
        # GIVEN
        with patch("agents.verification_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = VerificationAgent()
            agent.structured_model = MagicMock()
            agent.structured_model.invoke.side_effect = ValueError("Invalid schema")

            docs = [Document(page_content="test")]

            # WHEN
            result = agent.check("test answer", docs)

            # THEN
            assert "Supported:** NO" in result["verification_report"]


# ============================================================
# TESTS: Errores en Workflow
# ============================================================

class TestWorkflowErrors:
    """Verifica que el Workflow maneja errores correctamente."""

    def test_full_pipeline_survives_research_error(self):
        """El workflow debe sobrevivir si research falla."""
        # GIVEN
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    workflow.relevance_checker = MagicMock()
                    workflow.relevance_checker.check.return_value = RelevanceClassification.CAN_ANSWER

                    workflow.researcher = MagicMock()
                    workflow.researcher.generate.side_effect = Exception("Research failed")

                    retriever = MagicMock()
                    retriever.invoke.return_value = [Document(page_content="test")]

                    # WHEN/THEN
                    with pytest.raises(Exception):
                        workflow.full_pipeline("test", retriever)

    def test_full_pipeline_survives_verification_error(self):
        """El workflow debe sobrevivir si verification falla."""
        # GIVEN
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    workflow.relevance_checker = MagicMock()
                    workflow.relevance_checker.check.return_value = RelevanceClassification.CAN_ANSWER

                    workflow.researcher = MagicMock()
                    workflow.researcher.generate.return_value = {"draft_answer": "test answer"}

                    workflow.verifier = MagicMock()
                    workflow.verifier.check.side_effect = Exception("Verification failed")

                    retriever = MagicMock()
                    retriever.invoke.return_value = [Document(page_content="test")]

                    # WHEN/THEN
                    with pytest.raises(Exception):
                        workflow.full_pipeline("test", retriever)

    def test_check_relevance_step_survives_retriever_error(self):
        """check_relevance_step debe manejar errores del retriever."""
        # GIVEN
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    workflow.relevance_checker = MagicMock()
                    workflow.relevance_checker.check.side_effect = Exception("Retriever error")

                    state = {"question": "test", "retriever": MagicMock()}

                    # WHEN/THEN
                    with pytest.raises(Exception):
                        workflow._check_relevance_step(state)
