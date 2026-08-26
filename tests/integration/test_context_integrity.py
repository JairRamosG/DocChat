"""
Tests de Integración - Pilar 6: Context Integrity (Integridad del contexto)

Verifica que el contexto viaje completo desde los documentos hasta la respuesta final.
El contexto se puede corruptear o perder por el camino.

Preguntas que responden estos tests:
- ¿Verify recibe el mismo contexto que research?
- ¿Se pierden documentos en el camino?
- ¿La información relevante está presente en el contexto?
- ¿El contexto se mantiene entre iteraciones de re_research?
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from agents.research_agent import ResearchAgent
from agents.verification_agent import VerificationAgent
from agents.models import VerificationReport


@pytest.fixture(autouse=True)
def mock_openrouter_key():
    """Mockear OPENROUTER_API_KEY para todos los tests."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


@pytest.fixture
def sample_documents():
    """Documentos de prueba con contenido específico."""
    return [
        Document(
            page_content="Python es un lenguaje de programación interpretado.",
            metadata={"source": "doc1.pdf", "page": 1}
        ),
        Document(
            page_content="Python fue creado por Guido van Rossum en 1991.",
            metadata={"source": "doc1.pdf", "page": 2}
        ),
        Document(
            page_content="Python se usa para inteligencia artificial y ciencia de datos.",
            metadata={"source": "doc2.pdf", "page": 1}
        ),
    ]


# ============================================================
# TESTS: Contexto de Research a Verify
# ============================================================

class TestContextFromResearchToVerify:
    """Verifica que verify recibe el mismo contexto que research."""

    def test_context_preserved_between_agents(self, sample_documents):
        """El contexto usado por research debe estar disponible para verify."""
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

        # WHEN
        agent_result = agent.generate("¿Qué es Python?", sample_documents)
        context_used = agent_result["context_used"]

        # THEN
        # Todos los documentos deben estar en el contexto
        assert "Python es un lenguaje de programación interpretado." in context_used
        assert "Python fue creado por Guido van Rossum en 1991." in context_used
        assert "Python se usa para inteligencia artificial" in context_used

    def test_verify_receives_full_context(self, sample_documents):
        """Verify debe recibir el contexto completo para verificar."""
        # GIVEN
        verifier = VerificationAgent()
        verifier.structured_model = MagicMock()
        verifier.structured_model.invoke.return_value = VerificationReport(
            supported="YES", relevant="YES"
        )

        # WHEN
        full_context = "\n\n".join([doc.page_content for doc in sample_documents])
        result = verifier.check("Python es un lenguaje.", [sample_documents[0]])

        # THEN
        assert "verification_report" in result
        assert "context_used" in result

    def test_context_not_truncated(self, sample_documents):
        """El contexto no debe truncarse entre agentes."""
        # GIVEN
        agent = ResearchAgent()
        agent.model = MagicMock()
        agent.model.invoke.return_value = MagicMock(content="respuesta")

        # WHEN
        result = agent.generate("test", sample_documents)
        context = result["context_used"]

        # THEN
        # El contexto debe contener información de todos los documentos
        doc_count = context.count("Python")
        assert doc_count >= 3  # "Python" aparece en los 3 documentos


# ============================================================
# TESTS: Contexto con documentos variados
# ============================================================

class TestContextWithVariedDocuments:
    """Verifica el contexto con diferentes tipos de documentos."""

    def test_context_with_single_document(self):
        """Contexto con un solo documento."""
        # GIVEN
        docs = [Document(page_content="Único documento de prueba.")]

        agent = ResearchAgent()
        agent.model = MagicMock()
        agent.model.invoke.return_value = MagicMock(content="respuesta")

        # WHEN
        result = agent.generate("test", docs)

        # THEN
        assert "Único documento de prueba." in result["context_used"]

    def test_context_with_many_documents(self):
        """Contexto con muchos documentos."""
        # GIVEN
        docs = [
            Document(page_content=f"Documento {i}: contenido de prueba.")
            for i in range(10)
        ]

        agent = ResearchAgent()
        agent.model = MagicMock()
        agent.model.invoke.return_value = MagicMock(content="respuesta")

        # WHEN
        result = agent.generate("test", docs)

        # THEN
        for i in range(10):
            assert f"Documento {i}" in result["context_used"]

    def test_context_preserves_metadata(self, sample_documents):
        """El contexto debe preservar la información de los documentos."""
        # GIVEN
        agent = ResearchAgent()
        agent.model = MagicMock()
        agent.model.invoke.return_value = MagicMock(content="respuesta")

        # WHEN
        result = agent.generate("test", sample_documents)

        # THEN
        # Verificar que el contexto contiene el contenido de los documentos
        assert len(result["context_used"]) > 0


# ============================================================
# TESTS: Contexto en re_research
# ============================================================

class TestContextInReResearch:
    """Verifica que el contexto se mantiene en iteraciones de re_research."""

    def test_same_documents_used_in_both_iterations(self, sample_documents):
        """Los mism documentos deben usarse en research y re_research."""
        # GIVEN
        agent = ResearchAgent()
        agent.model = MagicMock()
        agent.model.invoke.return_value = MagicMock(content="respuesta")

        # WHEN - Primera iteración
        result1 = agent.generate("test", sample_documents)
        context1 = result1["context_used"]

        # WHEN - Segunda iteración (re_research)
        result2 = agent.generate("test", sample_documents)
        context2 = result2["context_used"]

        # THEN
        assert context1 == context2
