"""
Tests de Integración - Pilar 8: Edge Cases (Casos extremos)

Verifica que el sistema maneje situaciones inusuales sin crashear.
Los sistemas fallan en los bordes, no en el centro.

Preguntas que responden estos tests:
- ¿Qué pasa con preguntas vacías?
- ¿Qué pasa con documentos vacíos?
- ¿Qué pasa con caracteres especiales?
- ¿Qué pasa con preguntas muy largas?
- ¿Qué pasa con preguntas en otro idioma?
- ¿Qué pasa con la misma pregunta dos veces?
"""
import os
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


# ============================================================
# TESTS: Preguntas vacías o nulas
# ============================================================

class TestEmptyQuestions:
    """Verifica que preguntas vacías se manejen correctamente."""

    def test_empty_string_question(self):
        """Pregunta vacía: '' → NO_MATCH."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="NO_MATCH")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result = checker.check("", retriever)

            # THEN
            assert result == RelevanceClassification.NO_MATCH

    def test_whitespace_only_question(self):
        """Pregunta solo con espacios: '   ' → NO_MATCH."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="NO_MATCH")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result = checker.check("   ", retriever)

            # THEN
            assert result == RelevanceClassification.NO_MATCH


# ============================================================
# TESTS: Documentos vacíos
# ============================================================

class TestEmptyDocuments:
    """Verifica que documentos vacíos se manejen correctamente."""

    def test_empty_documents_list(self):
        """Lista de documentos vacía → NO_MATCH."""
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

    def test_document_with_empty_content(self):
        """Documento con contenido vacío."""
        # GIVEN
        doc = Document(page_content="")

        agent = ResearchAgent()
        agent.model = MagicMock()
        agent.model.invoke.return_value = MagicMock(content="respuesta")

        # WHEN
        result = agent.generate("test", [doc])

        # THEN
        assert "draft_answer" in result


# ============================================================
# TESTS: Caracteres especiales
# ============================================================

class TestSpecialCharacters:
    """Verifica que caracteres especiales no crasheen el sistema."""

    def test_spanish_characters(self):
        """Caracteres españoles: ñ, á, é, í, ó, ú."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="CAN_ANSWER")

            retriever = MagicMock()
            retriever.invoke.return_value = [
                Document(page_content="El niño pequeño comió una tortilla de espinacas.")
            ]

            # WHEN
            result = checker.check("¿Qué comió el niño?", retriever)

            # THEN
            assert result == RelevanceClassification.CAN_ANSWER

    def test_emojis_in_question(self):
        """Emojis en la pregunta."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="NO_MATCH")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result = checker.check("¿Qué es Python? 🐍", retriever)

            # THEN
            assert result == RelevanceClassification.NO_MATCH

    def test_special_symbols(self):
        """Símbolos especiales: @#$%^&*()."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="NO_MATCH")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result = checker.check("Test @#$%^&*() characters", retriever)

            # THEN
            assert result == RelevanceClassification.NO_MATCH

    def test_mixed_scripts(self):
        """Mezcla de scripts: inglés + español + caracteres especiales."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="NO_MATCH")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result = checker.check("Hello world ¿Cómo estás? 你好", retriever)

            # THEN
            assert result == RelevanceClassification.NO_MATCH


# ============================================================
# TESTS: Preguntas muy largas
# ============================================================

class TestLongQuestions:
    """Verifica que preguntas muy largas se manejen correctamente."""

    def test_very_long_question(self):
        """Pregunta de 10,000 caracteres."""
        # GIVEN
        long_question = "¿Qué es Python? " * 1000  # ~17,000 caracteres

        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="CAN_ANSWER")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result = checker.check(long_question, retriever)

            # THEN
            assert result == RelevanceClassification.CAN_ANSWER


# ============================================================
# TESTS: Preguntas en otro idioma
# ============================================================

class TestDifferentLanguages:
    """Verifica que preguntas en otros idiomas se manejen correctamente."""

    def test_english_question(self):
        """Pregunta en inglés."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="CAN_ANSWER")

            retriever = MagicMock()
            retriever.invoke.return_value = [
                Document(page_content="Python is a programming language.")
            ]

            # WHEN
            result = checker.check("What is Python?", retriever)

            # THEN
            assert result == RelevanceClassification.CAN_ANSWER

    def test_chinese_question(self):
        """Pregunta en chino."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="NO_MATCH")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result = checker.check("什么是 Python？", retriever)

            # THEN
            assert result == RelevanceClassification.NO_MATCH


# ============================================================
# TESTS: Preguntas repetidas
# ============================================================

class TestRepeatedQuestions:
    """Verifica que preguntas repetidas se manejen correctamente."""

    def test_same_question_twice(self):
        """Mis ma pregunta dos veces consecutivas."""
        # GIVEN
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            checker.model = MagicMock()
            checker.model.invoke.return_value = MagicMock(content="CAN_ANSWER")

            retriever = MagicMock()
            retriever.invoke.return_value = [Document(page_content="test")]

            # WHEN
            result1 = checker.check("¿Qué es Python?", retriever)
            result2 = checker.check("¿Qué es Python?", retriever)

            # THEN
            assert result1 == RelevanceClassification.CAN_ANSWER
            assert result2 == RelevanceClassification.CAN_ANSWER


# ============================================================
# TESTS: State incompleto
# ============================================================

class TestIncompleteState:
    """Verifica que state incompleto no crashee el workflow."""

    def test_state_with_missing_optional_fields(self):
        """State con campos opcionales faltantes."""
        # GIVEN
        state = {
            "question": "test",
            "documents": [],
            "draft_answer": "",
            "verification_report": "",
            "is_relevant": False,
            "retriever": MagicMock()
        }

        # WHEN
        workflow = AgentWorkflow()
        result = workflow._decide_after_relevance_check(state)

        # THEN
        assert result == "irrelevant"

    def test_research_step_with_empty_documents(self):
        """research_step con documentos vacíos."""
        # GIVEN
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    workflow.researcher = MagicMock()
                    workflow.researcher.generate.return_value = {"draft_answer": "respuesta"}

                    state = {"question": "test", "documents": []}

                    # WHEN
                    result = workflow._research_step(state)

                    # THEN
                    assert "draft_answer" in result
