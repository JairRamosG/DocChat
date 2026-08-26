"""
Tests de Integración - Pilar 7: Performance Budget (Tiempos de ejecución)

Verifica que cada nodo termine dentro de un tiempo razonable.
Si uno se tarda demasiado, el usuario espera.

Preguntas que responden estos tests:
- ¿Cada agente termina en menos de X segundos?
- ¿El pipeline completo no excede el presupuesto?
- ¿No hay timeouts innecesarios?
- ¿Los mocks son rápidos suficientes para CI?
"""
import os
import time
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from agents.relevance_checker import RelevanceChecker, RelevanceClassification
from agents.research_agent import ResearchAgent
from agents.verification_agent import VerificationAgent
from agents.workflow import AgentWorkflow
from agents.models import VerificationReport


@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


@pytest.fixture
def sample_documents():
    """Documentos de prueba."""
    return [
        Document(page_content="Documento de prueba 1."),
        Document(page_content="Documento de prueba 2."),
        Document(page_content="Documento de prueba 3."),
    ]


# ============================================================
# TESTS: Performance por agente
# ============================================================

class TestAgentPerformance:
    """Verifica que cada agente termine en tiempo aceptable."""

    def test_relevance_checker_performance(self):
        """RelevanceChecker debe completar en menos de 2 segundos."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="CAN_ANSWER")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            start = time.time()
            result = checker.check("test question", retriever)
            elapsed = time.time() - start

            # THEN
            assert elapsed < 2.0
            assert result == RelevanceClassification.CAN_ANSWER

    def test_research_agent_performance(self):
        """ResearchAgent debe completar en menos de 2 segundos."""
        # GIVEN
        with patch("agents.research_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = ResearchAgent()
            agent.model = MagicMock()
            agent.model.invoke.return_value = MagicMock(content="respuesta")

            docs = [Document(page_content="test")]

            # WHEN
            start = time.time()
            result = agent.generate("test", docs)
            elapsed = time.time() - start

            # THEN
            assert elapsed < 2.0
            assert "draft_answer" in result

    def test_verification_agent_performance(self):
        """VerificationAgent debe completar en menos de 2 segundos."""
        # GIVEN
        with patch("agents.verification_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = VerificationAgent()
            agent.structured_model = MagicMock()
            agent.structured_model.invoke.return_value = VerificationReport(
                supported="YES", relevant="YES"
            )

            docs = [Document(page_content="test")]

            # WHEN
            start = time.time()
            result = agent.check("test answer", docs)
            elapsed = time.time() - start

            # THEN
            assert elapsed < 2.0
            assert "verification_report" in result


# ============================================================
# TESTS: Performance del pipeline completo
# ============================================================

class TestPipelinePerformance:
    """Verifica que el pipeline completo termine en tiempo aceptable."""

    def test_full_pipeline_performance(self):
        """El pipeline completo debe completar en menos de 5 segundos."""
        # GIVEN
        workflow = AgentWorkflow()
        workflow.relevance_checker = MagicMock()
        workflow.relevance_checker.check.return_value = RelevanceClassification.CAN_ANSWER

        workflow.researcher = MagicMock()
        workflow.researcher.generate.return_value = {"draft_answer": "respuesta"}

        workflow.verifier = MagicMock()
        workflow.verifier.check.return_value = {
            "verification_report": "Supported: YES\nRelevant: YES"
        }

        retriever = MagicMock()
        retriever.invoke.return_value = [Document(page_content="test")]

        # WHEN
        start = time.time()
        result = workflow.full_pipeline("test", retriever)
        elapsed = time.time() - start

        # THEN
        assert elapsed < 5.0
        assert "draft_answer" in result

    def test_irrelevant_question_faster(self):
        """Pregunta irrelevante debe ser más rápida (no ejecuta research/verify)."""
        # GIVEN
        workflow = AgentWorkflow()
        workflow.relevance_checker = MagicMock()
        workflow.relevance_checker.check.return_value = RelevanceClassification.NO_MATCH

        retriever = MagicMock()
        retriever.invoke.return_value = [Document(page_content="test")]

        # WHEN
        start = time.time()
        result = workflow.full_pipeline("test", retriever)
        elapsed = time.time() - start

        # THEN
        assert elapsed < 2.0  # Más rápido porque no ejecuta research/verify
        assert "isn't related" in result["draft_answer"].lower()


# ============================================================
# TESTS: Performance de operaciones individuales
# ============================================================

class TestOperationPerformance:
    """Verifica performance de operaciones específicas."""

    def test_prompt_generation_performance(self):
        """La generación de prompts debe ser instantánea."""
        # GIVEN
        with patch("agents.research_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = ResearchAgent()

            # WHEN
            start = time.time()
            for _ in range(100):
                agent.generate_prompt("question", "context")
            elapsed = time.time() - start

            # THEN
            assert elapsed < 1.0  # 100 prompts en menos de 1 segundo

    def test_verification_report_formatting_performance(self):
        """El formateo del reporte debe ser instantáneo."""
        # GIVEN
        report = VerificationReport(
            supported="YES",
            relevant="YES",
            unsupported_claims=["claim1", "claim2"],
            contradictions=["contradiction1"],
            additional_details="Detalles adicionales"
        )

        # WHEN
        start = time.time()
        for _ in range(1000):
            report.to_report()
        elapsed = time.time() - start

        # THEN
        assert elapsed < 1.0  # 1000 formateos en menos de 1 segundo
