"""Tests for agents/workflow.py"""
import pytest
from unittest.mock import patch, MagicMock
from agents.workflow import AgentWorkflow, AgentState
from agents.relevance_checker import RelevanceClassification


def test_agent_state_has_required_keys():
    """AgentState debe tener todas las claves requeridas."""
    required_keys = ["question", "documents", "draft_answer", "verification_report", "is_relevant", "retriever"]
    for key in required_keys:
        assert key in AgentState.__annotations__


def test_workflow_init():
    """AgentWorkflow debe inicializarse correctamente."""
    with patch("agents.workflow.ResearchAgent") as MockResearch:
        with patch("agents.workflow.VerificationAgent") as MockVerify:
            with patch("agents.workflow.RelevanceChecker") as MockRelevance:
                workflow = AgentWorkflow()
                assert workflow.researcher is not None
                assert workflow.verifier is not None
                assert workflow.relevance_checker is not None
                assert workflow.compiled_workflow is not None


def test_decide_after_relevance_check_relevant():
    """_decide_after_relevance_check debe devolver 'relevant' cuando is_relevant es True."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                workflow = AgentWorkflow()
                state = {"is_relevant": True}
                result = workflow._decide_after_relevance_check(state)
                assert result == "relevant"


def test_decide_after_relevance_check_irrelevant():
    """_decide_after_relevance_check debe devolver 'irrelevant' cuando is_relevant es False."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                workflow = AgentWorkflow()
                state = {"is_relevant": False}
                result = workflow._decide_after_relevance_check(state)
                assert result == "irrelevant"


def test_check_relevance_step_can_answer():
    """_check_relevance_step debe devolver is_relevant=True cuando CAN_ANSWER."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker") as MockRelevance:
                workflow = AgentWorkflow()
                workflow.relevance_checker = MagicMock()
                workflow.relevance_checker.check.return_value = RelevanceClassification.CAN_ANSWER
                
                state = {"question": "test", "retriever": MagicMock()}
                result = workflow._check_relevance_step(state)
                
                assert result["is_relevant"] is True


def test_check_relevance_step_partial():
    """_check_relevance_step debe devolver is_relevant=True cuando PARTIAL."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                workflow = AgentWorkflow()
                workflow.relevance_checker = MagicMock()
                workflow.relevance_checker.check.return_value = RelevanceClassification.PARTIAL
                
                state = {"question": "test", "retriever": MagicMock()}
                result = workflow._check_relevance_step(state)
                
                assert result["is_relevant"] is True


def test_check_relevance_step_no_match():
    """_check_relevance_step debe devolver is_relevant=False cuando NO_MATCH."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                workflow = AgentWorkflow()
                workflow.relevance_checker = MagicMock()
                workflow.relevance_checker.check.return_value = RelevanceClassification.NO_MATCH
                
                state = {"question": "test", "retriever": MagicMock()}
                result = workflow._check_relevance_step(state)
                
                assert result["is_relevant"] is False
                assert "draft_answer" in result
                assert "isn't related" in result["draft_answer"]


def test_research_step():
    """_research_step debe llamar a researcher.generate."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                workflow = AgentWorkflow()
                workflow.researcher = MagicMock()
                workflow.researcher.generate.return_value = {"draft_answer": "test answer"}
                
                state = {"question": "test", "documents": [MagicMock()]}
                result = workflow._research_step(state)
                
                assert result["draft_answer"] == "test answer"
                workflow.researcher.generate.assert_called_once()


def test_verification_step():
    """_verification_step debe llamar a verifier.check."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                workflow = AgentWorkflow()
                workflow.verifier = MagicMock()
                workflow.verifier.check.return_value = {"verification_report": "test report"}
                
                state = {"draft_answer": "test answer", "documents": [MagicMock()]}
                result = workflow._verification_step(state)
                
                assert result["verification_report"] == "test report"
                workflow.verifier.check.assert_called_once()


def test_decide_next_step_re_research():
    """_decide_next_step debe devolver 're_research' cuando NO está soportado."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                workflow = AgentWorkflow()
                state = {"verification_report": "Supported: NO"}
                result = workflow._decide_next_step(state)
                assert result == "re_research"


def test_decide_next_step_end():
    """_decide_next_step debe devolver 'end' cuando está soportado."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                workflow = AgentWorkflow()
                state = {"verification_report": "Supported: YES"}
                result = workflow._decide_next_step(state)
                assert result == "end"


def test_full_pipeline_returns_results():
    """full_pipeline debe devolver draft_answer y verification_report."""
    with patch("agents.workflow.ResearchAgent"):
        with patch("agents.workflow.VerificationAgent"):
            with patch("agents.workflow.RelevanceChecker"):
                workflow = AgentWorkflow()
                workflow.compiled_workflow = MagicMock()
                workflow.compiled_workflow.invoke.return_value = {
                    "draft_answer": "test answer",
                    "verification_report": "test report"
                }
                
                mock_retriever = MagicMock()
                mock_retriever.invoke.return_value = [MagicMock()]
                
                result = workflow.full_pipeline("test question", mock_retriever)
                
                assert "draft_answer" in result
                assert "verification_report" in result
                assert result["draft_answer"] == "test answer"
                assert result["verification_report"] == "test report"
