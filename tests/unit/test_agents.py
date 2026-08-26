"""
Tests Unitarios - Categoría 1: Agentes (Relevance, Research, Verification, Workflow)

Agrupa todos los tests de los agentes del sistema multi-agente.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from agents.relevance_checker import RelevanceChecker, RelevanceClassification
from agents.research_agent import ResearchAgent
from agents.verification_agent import VerificationAgent
from agents.models import VerificationReport
from agents.workflow import AgentWorkflow, AgentState


# ============================================================
# FIXTURE COMPARTIDO
# ============================================================

@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests de agentes."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


# ============================================================
# RELEVANCE CHECKER
# ============================================================

class TestRelevanceChecker:
    """Tests para RelevanceChecker."""

    def test_classification_enum_values(self):
        """Los valores del enum deben ser strings correctos."""
        assert RelevanceClassification.CAN_ANSWER.value == "CAN_ANSWER"
        assert RelevanceClassification.PARTIAL.value == "PARTIAL"
        assert RelevanceClassification.NO_MATCH.value == "NO_MATCH"

    def test_classification_from_string(self):
        """El enum debe crearse desde strings."""
        assert RelevanceClassification("CAN_ANSWER") == RelevanceClassification.CAN_ANSWER
        assert RelevanceClassification("PARTIAL") == RelevanceClassification.PARTIAL
        assert RelevanceClassification("NO_MATCH") == RelevanceClassification.NO_MATCH

    def test_init(self):
        """RelevanceChecker debe inicializarse correctamente."""
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            assert checker.model is not None

    def test_no_match_when_no_documents(self):
        """Debe devolver NO_MATCH cuando no hay documentos."""
        with patch("agents.relevance_checker.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            checker = RelevanceChecker()
            mock_retriever = MagicMock()
            mock_retriever.invoke.return_value = []

            result = checker.check("test question", mock_retriever)

            assert result == RelevanceClassification.NO_MATCH

    def test_no_match_on_api_error(self):
        """Debe devolver NO_MATCH cuando hay error en la API."""
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

    def test_returns_classification_on_success(self):
        """Debe devolver la clasificación cuando la API responde."""
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

    def test_no_match_on_invalid_response(self):
        """Debe devolver NO_MATCH cuando la respuesta no es válida."""
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

    def test_combines_documents_in_prompt(self):
        """Debe combinar documentos correctamente en el prompt."""
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

            checker.check("test question", mock_retriever, k=2)

            call_args = checker.model.invoke.call_args[0][0]
            assert "Document 1 content" in call_args
            assert "Document 2 content" in call_args


# ============================================================
# RESEARCH AGENT
# ============================================================

class TestResearchAgent:
    """Tests para ResearchAgent."""

    def test_init(self):
        """ResearchAgent debe inicializarse correctamente."""
        with patch("agents.research_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = ResearchAgent()
            assert agent.model is not None

    def test_sanitize_response(self):
        """sanitize_response debe limpiar espacios en blanco."""
        with patch("agents.research_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = ResearchAgent()

            assert agent.sanitize_response("  hello  ") == "hello"
            assert agent.sanitize_response("test\n") == "test"
            assert agent.sanitize_response("  test  ") == "test"

    def test_generate_prompt(self):
        """generate_prompt debe crear un prompt con question y context."""
        with patch("agents.research_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = ResearchAgent()

            prompt = agent.generate_prompt("What is AI?", "AI is artificial intelligence.")

            assert "What is AI?" in prompt
            assert "AI is artificial intelligence." in prompt
            assert "Question" in prompt
            assert "Context" in prompt

    def test_generate_returns_draft_answer(self):
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

    def test_generate_returns_default_on_empty_response(self):
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

    def test_generate_raises_on_api_error(self):
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

    def test_generate_combines_documents(self):
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

            assert "Document 1" in result["context_used"]
            assert "Document 2" in result["context_used"]


# ============================================================
# VERIFICATION AGENT
# ============================================================

class TestVerificationAgent:
    """Tests para VerificationAgent."""

    def test_init(self):
        """VerificationAgent debe inicializarse correctamente."""
        with patch("agents.verification_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = VerificationAgent()
            assert agent.model is not None
            assert agent.structured_model is not None

    def test_generate_prompt(self):
        """generate_prompt debe crear un prompt con answer y context."""
        with patch("agents.verification_agent.settings") as mock_settings:
            mock_settings.CHAT_MODEL = "test/model"
            agent = VerificationAgent()

            prompt = agent.generate_prompt("AI is great", "AI is artificial intelligence.")

            assert "AI is great" in prompt
            assert "AI is artificial intelligence." in prompt
            assert "Answer" in prompt
            assert "Context" in prompt

    def test_check_returns_verification_report(self):
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

    def test_check_returns_fallback_on_error(self):
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

    def test_check_combines_documents(self):
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

            assert "Document 1" in result["context_used"]
            assert "Document 2" in result["context_used"]

    def test_check_returns_report_string(self):
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

            report = result["verification_report"]
            assert "Supported:** YES" in report
            assert "claim1" in report
            assert "contradiction1" in report
            assert "Extra info" in report


# ============================================================
# VERIFICATION REPORT MODEL
# ============================================================

class TestVerificationReport:
    """Tests para el modelo VerificationReport."""

    def test_required_fields(self):
        """Debe requerir supported y relevant."""
        report = VerificationReport(supported="YES", relevant="YES")
        assert report.supported == "YES"
        assert report.relevant == "YES"

    def test_defaults(self):
        """Debe tener defaults para campos opcionales."""
        report = VerificationReport(supported="NO", relevant="NO")
        assert report.unsupported_claims == []
        assert report.contradictions == []
        assert report.additional_details == ""

    def test_with_claims(self):
        """Debe aceptar listas de claims."""
        report = VerificationReport(
            supported="NO",
            relevant="YES",
            unsupported_claims=["claim1", "claim2"],
            contradictions=["contradiction1"]
        )
        assert len(report.unsupported_claims) == 2
        assert len(report.contradictions) == 1

    def test_to_report_supported_yes(self):
        """to_report debe formatear correctamente cuando es supported."""
        report = VerificationReport(supported="YES", relevant="YES")
        result = report.to_report()

        assert "**Supported:** YES" in result
        assert "**Unsupported Claims:** None" in result
        assert "**Contradictions:** None" in result
        assert "**Relevant:** YES" in result
        assert "**Additional Details:** None" in result

    def test_to_report_supported_no(self):
        """to_report debe formatear correctamente cuando no es supported."""
        report = VerificationReport(
            supported="NO",
            relevant="YES",
            unsupported_claims=["claim1", "claim2"],
            contradictions=["contradiction1"],
            additional_details="Extra info"
        )
        result = report.to_report()

        assert "**Supported:** NO" in result
        assert "claim1, claim2" in result
        assert "contradiction1" in result
        assert "**Relevant:** YES" in result
        assert "Extra info" in result

    def test_to_report_empty_claims(self):
        """to_report debe mostrar 'None' cuando no hay claims."""
        report = VerificationReport(supported="YES", relevant="YES")
        result = report.to_report()

        lines = result.split("\n")
        unsupported_line = next(l for l in lines if "Unsupported Claims" in l)
        assert "None" in unsupported_line

    def test_serialization(self):
        """Debe serializarse correctamente a diccionario."""
        report = VerificationReport(
            supported="YES",
            relevant="YES",
            unsupported_claims=["claim1"],
            additional_details="details"
        )

        data = report.model_dump()
        assert data["supported"] == "YES"
        assert data["relevant"] == "YES"
        assert data["unsupported_claims"] == ["claim1"]
        assert data["additional_details"] == "details"

    def test_from_dict(self):
        """Debe crearse desde un diccionario."""
        data = {
            "supported": "NO",
            "relevant": "YES",
            "unsupported_claims": ["test"],
            "contradictions": [],
            "additional_details": ""
        }

        report = VerificationReport(**data)
        assert report.supported == "NO"
        assert report.relevant == "YES"
        assert report.unsupported_claims == ["test"]


# ============================================================
# WORKFLOW (LangGraph)
# ============================================================

class TestAgentWorkflow:
    """Tests para AgentWorkflow."""

    def test_agent_state_has_required_keys(self):
        """AgentState debe tener todas las claves requeridas."""
        required_keys = [
            "question", "documents", "draft_answer",
            "verification_report", "is_relevant", "retriever"
        ]
        for key in required_keys:
            assert key in AgentState.__annotations__

    def test_workflow_init(self):
        """AgentWorkflow debe inicializarse correctamente."""
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    assert workflow.researcher is not None
                    assert workflow.verifier is not None
                    assert workflow.relevance_checker is not None
                    assert workflow.compiled_workflow is not None

    def test_decide_after_relevance_check_relevant(self):
        """_decide_after_relevance_check debe devolver 'relevant' cuando is_relevant=True."""
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    state = {"is_relevant": True}
                    result = workflow._decide_after_relevance_check(state)
                    assert result == "relevant"

    def test_decide_after_relevance_check_irrelevant(self):
        """_decide_after_relevance_check debe devolver 'irrelevant' cuando is_relevant=False."""
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    state = {"is_relevant": False}
                    result = workflow._decide_after_relevance_check(state)
                    assert result == "irrelevant"

    def test_check_relevance_step_can_answer(self):
        """_check_relevance_step debe devolver is_relevant=True cuando CAN_ANSWER."""
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    workflow.relevance_checker = MagicMock()
                    workflow.relevance_checker.check.return_value = RelevanceClassification.CAN_ANSWER

                    state = {"question": "test", "retriever": MagicMock()}
                    result = workflow._check_relevance_step(state)

                    assert result["is_relevant"] is True

    def test_check_relevance_step_partial(self):
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

    def test_check_relevance_step_no_match(self):
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

    def test_research_step(self):
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

    def test_verification_step(self):
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

    def test_decide_next_step_re_research(self):
        """_decide_next_step debe devolver 're_research' cuando NO está soportado."""
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    state = {"verification_report": "Supported: NO"}
                    result = workflow._decide_next_step(state)
                    assert result == "re_research"

    def test_decide_next_step_end(self):
        """_decide_next_step debe devolver 'end' cuando está soportado."""
        with patch("agents.workflow.ResearchAgent"):
            with patch("agents.workflow.VerificationAgent"):
                with patch("agents.workflow.RelevanceChecker"):
                    workflow = AgentWorkflow()
                    state = {"verification_report": "Supported: YES"}
                    result = workflow._decide_next_step(state)
                    assert result == "end"

    def test_full_pipeline_returns_results(self):
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
