"""Tests for agents/relevance_checker.py"""
import os
import pytest
from unittest.mock import patch, MagicMock
from agents.relevance_checker import RelevanceChecker, RelevanceClassification


@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


def test_relevance_classification_enum():
    """RelevanceClassification debe tener los valores correctos."""
    assert RelevanceClassification.CAN_ANSWER.value == "CAN_ANSWER"
    assert RelevanceClassification.PARTIAL.value == "PARTIAL"
    assert RelevanceClassification.NO_MATCH.value == "NO_MATCH"


def test_relevance_classification_from_string():
    """RelevanceClassification debe crearse desde strings."""
    assert RelevanceClassification("CAN_ANSWER") == RelevanceClassification.CAN_ANSWER
    assert RelevanceClassification("PARTIAL") == RelevanceClassification.PARTIAL
    assert RelevanceClassification("NO_MATCH") == RelevanceClassification.NO_MATCH


def test_relevance_checker_init():
    """RelevanceChecker debe inicializarse correctamente."""
    with patch("agents.relevance_checker.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        checker = RelevanceChecker()
        assert checker.model is not None


def test_check_returns_no_match_when_no_documents():
    """check debe devolver NO_MATCH cuando no hay documentos."""
    with patch("agents.relevance_checker.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        
        checker = RelevanceChecker()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        
        result = checker.check("test question", mock_retriever)
        
        assert result == RelevanceClassification.NO_MATCH


def test_check_returns_no_match_on_api_error():
    """check debe devolver NO_MATCH cuando hay error en la API."""
    with patch("agents.relevance_checker.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        
        checker = RelevanceChecker()
        checker.model = MagicMock()
        checker.model.invoke.side_effect = Exception("API Error")
        
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "test content"
        mock_retriever.invoke.return_value = [mock_doc]
        
        result = checker.check("test question", mock_retriever)
        
        assert result == RelevanceClassification.NO_MATCH


def test_check_returns_classification_on_success():
    """check debe devolver la clasificación cuando la API responde."""
    with patch("agents.relevance_checker.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        
        checker = RelevanceChecker()
        checker.model = MagicMock()
        
        mock_response = MagicMock()
        mock_response.content = "CAN_ANSWER"
        checker.model.invoke.return_value = mock_response
        
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "test content"
        mock_retriever.invoke.return_value = [mock_doc]
        
        result = checker.check("test question", mock_retriever)
        
        assert result == RelevanceClassification.CAN_ANSWER


def test_check_returns_no_match_on_invalid_response():
    """check debe devolver NO_MATCH cuando la respuesta no es válida."""
    with patch("agents.relevance_checker.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        
        checker = RelevanceChecker()
        checker.model = MagicMock()
        
        mock_response = MagicMock()
        mock_response.content = "INVALID_RESPONSE"
        checker.model.invoke.return_value = mock_response
        
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "test content"
        mock_retriever.invoke.return_value = [mock_doc]
        
        result = checker.check("test question", mock_retriever)
        
        assert result == RelevanceClassification.NO_MATCH


def test_check_combines_documents():
    """check debe combinar documentos correctamente."""
    with patch("agents.relevance_checker.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        
        checker = RelevanceChecker()
        checker.model = MagicMock()
        
        mock_response = MagicMock()
        mock_response.content = "CAN_ANSWER"
        checker.model.invoke.return_value = mock_response
        
        mock_retriever = MagicMock()
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "Document 1 content"
        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Document 2 content"
        mock_retriever.invoke.return_value = [mock_doc1, mock_doc2]
        
        result = checker.check("test question", mock_retriever, k=2)
        
        # Verificar que el modelo fue llamado
        checker.model.invoke.assert_called_once()
        # Verificar que el prompt contiene ambos documentos
        call_args = checker.model.invoke.call_args[0][0]
        assert "Document 1 content" in call_args
        assert "Document 2 content" in call_args
