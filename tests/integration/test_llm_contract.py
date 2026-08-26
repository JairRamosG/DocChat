"""
Tests de Integración - Pilar 4: LLM Output Contract (Formato de respuestas del LLM)

Verifica que el sistema tolere respuestas malformadas del LLM sin crashear.
Los LLMs son impredecibles: a veces responden "YES", "Yes", "yes", "YES.", etc.

Preguntas que responden estos tests:
- ¿Qué pasa si el LLM responde algo que no es un enum válido?
- ¿Qué pasa si el LLM responde vacío?
- ¿Qué pasa si el LLM responde en mayúsculas/minúsculas?
- ¿Qué pasa si el LLM responde con puntuación extra?
- ¿Qué pasa si el LLM responde en otro idioma?
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from agents.relevance_checker import RelevanceChecker, RelevanceClassification
from agents.research_agent import ResearchAgent
from agents.verification_agent import VerificationAgent
from agents.models import VerificationReport


@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


@pytest.fixture
def checker():
    """RelevanceChecker con modelo mock."""
    with patch("agents.relevance_checker.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        c = RelevanceChecker()
        c.model = MagicMock()
        return c


@pytest.fixture
def mock_retriever():
    """Retriever mock con documentos."""
    retriever = MagicMock()
    retriever.invoke.return_value = [
        Document(page_content="Python es un lenguaje de programación.")
    ]
    return retriever


# ============================================================
# TESTS: RelevanceChecker con respuestas inválidas
# ============================================================

class TestRelevanceCheckerMalformedResponses:
    """Verifica que RelevanceChecker maneja respuestas inválidas del LLM."""

    def test_handles_response_with_extra_punctuation(self, checker, mock_retriever):
        """Respuesta con puntuación extra: 'CAN_ANSWER.' → NO_MATCH."""
        # GIVEN
        mock_response = MagicMock()
        mock_response.content = "CAN_ANSWER."
        checker.model.invoke.return_value = mock_response

        # WHEN
        result = checker.check("test question", mock_retriever)

        # THEN
        assert result == RelevanceClassification.NO_MATCH

    def test_handles_response_with_spaces(self, checker, mock_retriever):
        """Respuesta con espacios: ' CAN_ANSWER ' → CAN_ANSWER (strip lo limpia)."""
        # GIVEN
        mock_response = MagicMock()
        mock_response.content = " CAN_ANSWER "
        checker.model.invoke.return_value = mock_response

        # WHEN
        result = checker.check("test question", mock_retriever)

        # THEN - .strip().upper() limpia el espacio, por eso funciona
        assert result == RelevanceClassification.CAN_ANSWER

    def test_handles_lowercase_response(self, checker, mock_retriever):
        """Respuesta en minúsculas: 'can_answer' → CAN_ANSWER (upper lo normaliza)."""
        # GIVEN
        mock_response = MagicMock()
        mock_response.content = "can_answer"
        checker.model.invoke.return_value = mock_response

        # WHEN
        result = checker.check("test question", mock_retriever)

        # THEN - .upper() normaliza a mayúsculas, por eso funciona
        assert result == RelevanceClassification.CAN_ANSWER

    def test_handles_completely_invalid_response(self, checker, mock_retriever):
        """Respuesta completamente inválida: 'Yes, I think so' → NO_MATCH."""
        # GIVEN
        mock_response = MagicMock()
        mock_response.content = "Yes, I think this is relevant"
        checker.model.invoke.return_value = mock_response

        # WHEN
        result = checker.check("test question", mock_retriever)

        # THEN
        assert result == RelevanceClassification.NO_MATCH

    def test_handles_empty_response(self, checker, mock_retriever):
        """Respuesta vacía: '' → NO_MATCH."""
        # GIVEN
        mock_response = MagicMock()
        mock_response.content = ""
        checker.model.invoke.return_value = mock_response

        # WHEN
        result = checker.check("test question", mock_retriever)

        # THEN
        assert result == RelevanceClassification.NO_MATCH

    def test_handles_response_in_another_language(self, checker, mock_retriever):
        """Respuesta en otro idioma: 'sí, puede responder' → NO_MATCH."""
        # GIVEN
        mock_response = MagicMock()
        mock_response.content = "sí, puede responder"
        checker.model.invoke.return_value = mock_response

        # WHEN
        result = checker.check("test question", mock_retriever)

        # THEN
        assert result == RelevanceClassification.NO_MATCH

    def test_handles_response_with_newlines(self, checker, mock_retriever):
        """Respuesta con saltos de línea: 'CAN_ANSWER\\n' → CAN_ANSWER (strip lo limpia)."""
        # GIVEN
        mock_response = MagicMock()
        mock_response.content = "CAN_ANSWER\n"
        checker.model.invoke.return_value = mock_response

        # WHEN
        result = checker.check("test question", mock_retriever)

        # THEN - .strip() elimina el \n, por eso funciona
        assert result == RelevanceClassification.CAN_ANSWER

    def test_valid_uppercase_response_works(self, checker, mock_retriever):
        """Respuesta válida en mayúsculas: 'CAN_ANSWER' → CAN_ANSWER."""
        # GIVEN
        mock_response = MagicMock()
        mock_response.content = "CAN_ANSWER"
        checker.model.invoke.return_value = mock_response

        # WHEN
        result = checker.check("test question", mock_retriever)

        # THEN
        assert result == RelevanceClassification.CAN_ANSWER


# ============================================================
# TESTS: ResearchAgent con respuestas inválidas
# ============================================================

class TestResearchAgentMalformedResponses:
    """Verifica que ResearchAgent maneja respuestas inválidas del LLM."""

    def test_handles_empty_response(self):
        """Respuesta vacía del LLM → mensaje por defecto."""
        # GIVEN
        agent = ResearchAgent()
        agent.model = MagicMock()

        mock_response = MagicMock()
        mock_response.content = ""
        agent.model.invoke.return_value = mock_response

        docs = [Document(page_content="test content")]

        # WHEN
        result = agent.generate("test question", docs)

        # THEN
        assert "cannot answer" in result["draft_answer"].lower()

    def test_handles_none_content(self):
        """Contenido None del LLM → mensaje por defecto."""
        # GIVEN
        agent = ResearchAgent()
        agent.model = MagicMock()

        mock_response = MagicMock()
        mock_response.content = None
        agent.model.invoke.return_value = mock_response

        docs = [Document(page_content="test content")]

        # WHEN
        result = agent.generate("test question", docs)

        # THEN
        assert "cannot answer" in result["draft_answer"].lower()

    def test_handles_response_with_only_whitespace(self):
        """Respuesta solo con espacios → strip() genera vacío → default."""
        # GIVEN
        agent = ResearchAgent()
        agent.model = MagicMock()

        mock_response = MagicMock()
        mock_response.content = "   \n\t  "
        agent.model.invoke.return_value = mock_response

        docs = [Document(page_content="test content")]

        # WHEN
        result = agent.generate("test question", docs)

        # THEN
        assert "cannot answer" in result["draft_answer"].lower()


# ============================================================
# TESTS: VerificationAgent con respuestas inválidas
# ============================================================

class TestVerificationAgentMalformedResponses:
    """Verifica que VerificationAgent maneja respuestas inválidas del LLM."""

    def test_handles_invalid_structured_output(self):
        """Structured output inválido → fallback a NO supportado."""
        # GIVEN
        agent = VerificationAgent()
        agent.structured_model = MagicMock()
        agent.structured_model.invoke.side_effect = Exception("Invalid output")

        docs = [Document(page_content="test content")]

        # WHEN
        result = agent.check("test answer", docs)

        # THEN
        assert "Supported:** NO" in result["verification_report"]

    def test_handles_api_timeout(self):
        """Timeout de API → fallback a NO supportado."""
        # GIVEN
        agent = VerificationAgent()
        agent.structured_model = MagicMock()
        agent.structured_model.invoke.side_effect = TimeoutError("API timeout")

        docs = [Document(page_content="test content")]

        # WHEN
        result = agent.check("test answer", docs)

        # THEN
        assert "Supported:** NO" in result["verification_report"]

    def test_handles_connection_error(self):
        """Error de conexión → fallback a NO supportado."""
        # GIVEN
        agent = VerificationAgent()
        agent.structured_model = MagicMock()
        agent.structured_model.invoke.side_effect = ConnectionError("No connection")

        docs = [Document(page_content="test content")]

        # WHEN
        result = agent.check("test answer", docs)

        # THEN
        assert "Supported:** NO" in result["verification_report"]
