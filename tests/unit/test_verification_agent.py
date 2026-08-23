"""Tests for agents/verification_agent.py"""
import os
import pytest
from unittest.mock import patch, MagicMock
from agents.verification_agent import VerificationAgent
from agents.models import VerificationReport


@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


def test_verification_agent_init():
    """VerificationAgent debe inicializarse correctamente."""
    with patch("agents.verification_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = VerificationAgent()
        assert agent.model is not None
        assert agent.structured_model is not None


def test_generate_prompt():
    """generate_prompt debe crear un prompt con answer y context."""
    with patch("agents.verification_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = VerificationAgent()
        
        prompt = agent.generate_prompt("AI is great", "AI is artificial intelligence.")
        
        assert "AI is great" in prompt
        assert "AI is artificial intelligence." in prompt
        assert "Answer" in prompt
        assert "Context" in prompt


def test_check_returns_verification_report():
    """check debe devolver verification_report y context_used."""
    with patch("agents.verification_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = VerificationAgent()
        
        mock_verification = VerificationReport(
            supported="YES",
            relevant="YES",
            unsupported_claims=[],
            contradictions=[],
            additional_details=""
        )
        agent.structured_model = MagicMock()
        agent.structured_model.invoke.return_value = mock_verification
        
        mock_doc = MagicMock()
        mock_doc.page_content = "AI is artificial intelligence."
        
        result = agent.check("AI is great", [mock_doc])
        
        assert "verification_report" in result
        assert "context_used" in result
        assert "Supported:** YES" in result["verification_report"]


def test_check_returns_fallback_on_error():
    """check debe devolver reporte por defecto cuando hay error."""
    with patch("agents.verification_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = VerificationAgent()
        agent.structured_model = MagicMock()
        agent.structured_model.invoke.side_effect = Exception("API Error")
        
        mock_doc = MagicMock()
        mock_doc.page_content = "test content"
        
        result = agent.check("test answer", [mock_doc])
        
        assert "verification_report" in result
        assert "Supported:** NO" in result["verification_report"]


def test_check_combines_documents():
    """check debe combinar documentos correctamente."""
    with patch("agents.verification_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = VerificationAgent()
        
        mock_verification = VerificationReport(
            supported="YES",
            relevant="YES"
        )
        agent.structured_model = MagicMock()
        agent.structured_model.invoke.return_value = mock_verification
        
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "Document 1"
        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Document 2"
        
        result = agent.check("answer", [mock_doc1, mock_doc2])
        
        # Verificar que el contexto contiene ambos documentos
        assert "Document 1" in result["context_used"]
        assert "Document 2" in result["context_used"]


def test_check_returns_report_string():
    """check debe devolver el reporte como string formateado."""
    with patch("agents.verification_agent.settings") as mock_settings:
        mock_settings.CHAT_MODEL = "test/model"
        agent = VerificationAgent()
        
        mock_verification = VerificationReport(
            supported="YES",
            relevant="YES",
            unsupported_claims=["claim1"],
            contradictions=["contradiction1"],
            additional_details="Extra info"
        )
        agent.structured_model = MagicMock()
        agent.structured_model.invoke.return_value = mock_verification
        
        mock_doc = MagicMock()
        mock_doc.page_content = "test content"
        
        result = agent.check("answer", [mock_doc])
        
        # Verificar que el reporte contiene la información
        report = result["verification_report"]
        assert "Supported:** YES" in report
        assert "claim1" in report
        assert "contradiction1" in report
        assert "Extra info" in report
