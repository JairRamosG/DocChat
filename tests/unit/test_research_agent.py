"""Tests for agents/research_agent.py"""
import os
import pytest
from unittest.mock import patch, MagicMock
from agents.research_agent import ResearchAgent


@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


def test_research_agent_init():
    """ResearchAgent debe inicializarse correctamente."""
    with patch("agents.research_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = ResearchAgent()
        assert agent.model is not None


def test_sanitize_response():
    """sanitize_response debe limpiar espacios en blanco."""
    with patch("agents.research_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = ResearchAgent()
        
        assert agent.sanitize_response("  hello  ") == "hello"
        assert agent.sanitize_response("test\n") == "test"
        assert agent.sanitize_response("  test  ") == "test"


def test_generate_prompt():
    """generate_prompt debe crear un prompt con question y context."""
    with patch("agents.research_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = ResearchAgent()
        
        prompt = agent.generate_prompt("What is AI?", "AI is artificial intelligence.")
        
        assert "What is AI?" in prompt
        assert "AI is artificial intelligence." in prompt
        assert "Question" in prompt
        assert "Context" in prompt


def test_generate_returns_draft_answer():
    """generate debe devolver draft_answer y context_used."""
    with patch("agents.research_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = ResearchAgent()
        agent.model = MagicMock()
        
        mock_response = MagicMock()
        mock_response.content = "AI is artificial intelligence."
        agent.model.invoke.return_value = mock_response
        
        mock_doc = MagicMock()
        mock_doc.page_content = "AI is artificial intelligence."
        
        result = agent.generate("What is AI?", [mock_doc])
        
        assert "draft_answer" in result
        assert "context_used" in result
        assert result["draft_answer"] == "AI is artificial intelligence."


def test_generate_returns_default_on_empty_response():
    """generate debe devolver mensaje por defecto cuando la respuesta está vacía."""
    with patch("agents.research_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = ResearchAgent()
        agent.model = MagicMock()
        
        mock_response = MagicMock()
        mock_response.content = ""
        agent.model.invoke.return_value = mock_response
        
        mock_doc = MagicMock()
        mock_doc.page_content = "test content"
        
        result = agent.generate("test question", [mock_doc])
        
        assert "cannot answer" in result["draft_answer"].lower()


def test_generate_raises_on_api_error():
    """generate debe lanzar RuntimeError cuando hay error en la API."""
    with patch("agents.research_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = ResearchAgent()
        agent.model = MagicMock()
        agent.model.invoke.side_effect = Exception("API Error")
        
        mock_doc = MagicMock()
        mock_doc.page_content = "test content"
        
        with pytest.raises(RuntimeError, match="Failed to generate"):
            agent.generate("test question", [mock_doc])


def test_generate_combines_documents():
    """generate debe combinar documentos correctamente."""
    with patch("agents.research_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = ResearchAgent()
        agent.model = MagicMock()
        
        mock_response = MagicMock()
        mock_response.content = "answer"
        agent.model.invoke.return_value = mock_response
        
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "Document 1"
        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Document 2"
        
        result = agent.generate("question", [mock_doc1, mock_doc2])
        
        # Verificar que el contexto contiene ambos documentos
        assert "Document 1" in result["context_used"]
        assert "Document 2" in result["context_used"]
