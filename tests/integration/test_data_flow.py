"""
Tests de Integración - Pilar 1: Data Flow (Flujo de datos entre nodos)

Verifica que el output de cada nodo sea exactamente lo que el siguiente nodo espera.
Si el formato no coincide, el sistema falla silenciosamente o crashea.

Preguntas que responden estos tests:
- ¿Research recibe los documentos que check_relevance procesó?
- ¿Verify recibe el draft_answer que research generó?
- ¿El retriever retorna documentos con page_content?
- ¿Cada nodo retorna el tipo de dato correcto?
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from agents.relevance_checker import RelevanceChecker, RelevanceClassification
from agents.research_agent import ResearchAgent
from agents.verification_agent import VerificationAgent
from agents.workflow import AgentWorkflow, AgentState
from agents.models import VerificationReport


@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


@pytest.fixture
def sample_documents():
    """Documentos de prueba que simulan lo que retorna el retriever."""
    return [
        Document(
            page_content="Python es un lenguaje de programación interpretado.",
            metadata={"source": "test.pdf", "page": 1}
        ),
        Document(
            page_content="Python fue creado por Guido van Rossum en 1991.",
            metadata={"source": "test.pdf", "page": 2}
        ),
        Document(
            page_content="Python se usa para inteligencia artificial.",
            metadata={"source": "test.pdf", "page": 3}
        ),
    ]


@pytest.fixture
def workflow():
    """Workflow con agentes mock (solo para tests de data flow)."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                return AgentWorkflow()


# ============================================================
# TESTS: Data Flow entre nodos
# ============================================================

class TestRetrieverToCheckRelevance:
    """Pilar 1: ¿El retriever pasa datos compatibles a check_relevance?"""

    def test_retriever_returns_documents_with_page_content(self, workflow):
        """El retriever debe retornar documentos con page_content."""
        # GIVEN
        mock_retriever = MagicMock()
        mock_doc = Document(page_content="Contenido de prueba")
        mock_retriever.invoke.return_value = [mock_doc]

        # WHEN
        docs = mock_retriever.invoke("¿Qué es Python?")

        # THEN
        assert len(docs) == 1
        assert hasattr(docs[0], "page_content")
        assert len(docs[0].page_content) > 0

    def test_check_relevance_receives_retriever(self, workflow):
        """check_relevance debe recibir un retriever invoke-able."""
        # GIVEN
        workflow.relevance_checker = MagicMock()
        workflow.relevance_checker.check.return_value = RelevanceClassification.CAN_ANSWER

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [Document(page_content="test")]

        state = {"question": "test question", "retriever": mock_retriever}

        # WHEN
        result = workflow._check_relevance_step(state)

        # THEN
        assert "is_relevant" in result
        assert isinstance(result["is_relevant"], bool)


class TestCheckRelevanceToResearch:
    """Pilar 1: ¿check_relevance pasa datos compatibles a research?"""

    def test_relevant_state_triggers_research(self, workflow):
        """Cuando is_relevant=True, research debe recibir question + documents."""
        # GIVEN
        state = {
            "question": "¿Qué es Python?",
            "is_relevant": True,
            "documents": [Document(page_content="Python es un lenguaje")]
        }

        # WHEN
        decision = workflow._decide_after_relevance_check(state)

        # THEN
        assert decision == "relevant"

    def test_irrelevant_state_skips_research(self, workflow):
        """Cuando is_relevant=False, research NO debe ejecutarse."""
        # GIVEN
        state = {
            "is_relevant": False,
            "draft_answer": "This question isn't related..."
        }

        # WHEN
        decision = workflow._decide_after_relevance_check(state)

        # THEN
        assert decision == "irrelevant"


class TestResearchToVerify:
    """Pilar 1: ¿research pasa datos compatibles a verify?"""

    def test_research_output_has_draft_answer(self):
        """research debe generar un draft_answer que verify puede recibir."""
        # GIVEN
        agent = ResearchAgent()
        agent.model = MagicMock()
        agent.model.invoke.return_value = MagicMock(
            content="Python es un lenguaje interpretado."
        )

        docs = [Document(page_content="Python es un lenguaje.")]

        # WHEN
        result = agent.generate("¿Qué es Python?", docs)

        # THEN
        assert "draft_answer" in result
        assert isinstance(result["draft_answer"], str)
        assert len(result["draft_answer"]) > 0

    def test_verify_receives_draft_answer_as_string(self):
        """verify debe recibir draft_answer como string."""
        # GIVEN
        verifier = VerificationAgent()
        verifier.structured_model = MagicMock()
        verifier.structured_model.invoke.return_value = VerificationReport(
            supported="YES", relevant="YES"
        )

        draft_answer = "Python es un lenguaje interpretado."
        docs = [Document(page_content="Python es un lenguaje.")]

        # WHEN
        result = verifier.check(draft_answer, docs)

        # THEN
        assert "verification_report" in result
        assert isinstance(result["verification_report"], str)


class TestResearchVerifyChain:
    """Pilar 1: ¿El output de research funciona como input de verify?"""

    def test_draft_answer_feeds_into_verification(self):
        """El draft_answer de research debe ser válido para verify."""
        # GIVEN
        agent = ResearchAgent()
        agent.model = MagicMock()
        agent.model.invoke.return_value = MagicMock(
            content="Python es un lenguaje de programación."
        )

        verifier = VerificationAgent()
        verifier.structured_model = MagicMock()
        verifier.structured_model.invoke.return_value = VerificationReport(
            supported="YES", relevant="YES"
        )

        docs = [Document(page_content="Python es un lenguaje de programación.")]

        # WHEN
        agent_result = agent.generate("¿Qué es Python?", docs)
        verifier_result = verifier.check(agent_result["draft_answer"], docs)

        # THEN
        assert "verification_report" in verifier_result
        assert "Supported:** YES" in verifier_result["verification_report"]
