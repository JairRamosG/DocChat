"""Tests for retriever/builder.py"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from retriever.builder import RetrieverBuilder


def test_retriever_builder_init():
    """RetrieverBuilder debe inicializarse correctamente."""
    with patch("retriever.builder.settings") as mock_settings:
        mock_settings.EMBEDDING_MODEL = "test/model"
        mock_settings.OPENROUTER_API_KEY = "test-key"
        
        builder = RetrieverBuilder()
        assert builder.embeddings is not None


def test_build_hybrid_retriever_returns_ensemble():
    """build_hybrid_retriever debe devolver un EnsembleRetriever."""
    with patch("retriever.builder.settings") as mock_settings:
        mock_settings.EMBEDDING_MODEL = "test/model"
        mock_settings.OPENROUTER_API_KEY = "test-key"
        mock_settings.CHROMA_DB_PATH = "./test_db"
        mock_settings.VECTOR_SEARCH_K = 5
        mock_settings.HYBRID_RETRIEVER_WEIGHTS = [0.4, 0.6]
        
        builder = RetrieverBuilder()
        
        with patch("retriever.builder.Chroma") as MockChroma:
            with patch("retriever.builder.BM25Retriever") as MockBM25:
                with patch("retriever.builder.EnsembleRetriever") as MockEnsemble:
                    mock_vector_store = MagicMock()
                    MockChroma.from_documents.return_value = mock_vector_store
                    
                    mock_bm25 = MagicMock()
                    MockBM25.from_documents.return_value = mock_bm25
                    
                    mock_ensemble = MagicMock()
                    MockEnsemble.return_value = mock_ensemble
                    
                    mock_docs = [MagicMock(), MagicMock()]
                    
                    result = builder.build_hybrid_retriever(mock_docs)
                    
                    assert result == mock_ensemble


def test_build_hybrid_retriever_creates_vector_store():
    """build_hybrid_retriever debe crear el vector store con los documentos."""
    with patch("retriever.builder.settings") as mock_settings:
        mock_settings.EMBEDDING_MODEL = "test/model"
        mock_settings.OPENROUTER_API_KEY = "test-key"
        mock_settings.CHROMA_DB_PATH = "./test_db"
        mock_settings.VECTOR_SEARCH_K = 5
        mock_settings.HYBRID_RETRIEVER_WEIGHTS = [0.4, 0.6]
        
        builder = RetrieverBuilder()
        
        with patch("retriever.builder.Chroma") as MockChroma:
            with patch("retriever.builder.BM25Retriever") as MockBM25:
                with patch("retriever.builder.EnsembleRetriever"):
                    mock_vector_store = MagicMock()
                    MockChroma.from_documents.return_value = mock_vector_store
                    
                    mock_bm25 = MagicMock()
                    MockBM25.from_documents.return_value = mock_bm25
                    
                    mock_docs = [MagicMock(), MagicMock()]
                    
                    builder.build_hybrid_retriever(mock_docs)
                    
                    # Verificar que Chroma.from_documents fue llamado
                    MockChroma.from_documents.assert_called_once()
                    call_kwargs = MockChroma.from_documents.call_args[1]
                    assert call_kwargs["documents"] == mock_docs
                    assert call_kwargs["persist_directory"] == "./test_db"


def test_build_hybrid_retriever_creates_bm25():
    """build_hybrid_retriever debe crear el retriever BM25."""
    with patch("retriever.builder.settings") as mock_settings:
        mock_settings.EMBEDDING_MODEL = "test/model"
        mock_settings.OPENROUTER_API_KEY = "test-key"
        mock_settings.CHROMA_DB_PATH = "./test_db"
        mock_settings.VECTOR_SEARCH_K = 5
        mock_settings.HYBRID_RETRIEVER_WEIGHTS = [0.4, 0.6]
        
        builder = RetrieverBuilder()
        
        with patch("retriever.builder.Chroma") as MockChroma:
            with patch("retriever.builder.BM25Retriever") as MockBM25:
                with patch("retriever.builder.EnsembleRetriever"):
                    MockChroma.from_documents.return_value = MagicMock()
                    
                    mock_bm25 = MagicMock()
                    MockBM25.from_documents.return_value = mock_bm25
                    
                    mock_docs = [MagicMock()]
                    
                    builder.build_hybrid_retriever(mock_docs)
                    
                    # Verificar que BM25Retriever.from_documents fue llamado
                    MockBM25.from_documents.assert_called_once_with(mock_docs)


def test_build_hybrid_retriever_creates_ensemble_with_weights():
    """build_hybrid_retriever debe crear el ensemble con los pesos correctos."""
    with patch("retriever.builder.settings") as mock_settings:
        mock_settings.EMBEDDING_MODEL = "test/model"
        mock_settings.OPENROUTER_API_KEY = "test-key"
        mock_settings.CHROMA_DB_PATH = "./test_db"
        mock_settings.VECTOR_SEARCH_K = 5
        mock_settings.HYBRID_RETRIEVER_WEIGHTS = [0.4, 0.6]
        
        builder = RetrieverBuilder()
        
        with patch("retriever.builder.Chroma") as MockChroma:
            with patch("retriever.builder.BM25Retriever") as MockBM25:
                with patch("retriever.builder.EnsembleRetriever") as MockEnsemble:
                    MockChroma.from_documents.return_value = MagicMock()
                    MockBM25.from_documents.return_value = MagicMock()
                    
                    mock_docs = [MagicMock()]
                    
                    builder.build_hybrid_retriever(mock_docs)
                    
                    # Verificar que EnsembleRetriever fue llamado con los pesos correctos
                    MockEnsemble.assert_called_once()
                    call_kwargs = MockEnsemble.call_args[1]
                    assert call_kwargs["weights"] == [0.4, 0.6]


def test_build_hybrid_retriever_raises_on_error():
    """build_hybrid_retriever debe lanzar excepción cuando hay error."""
    with patch("retriever.builder.settings") as mock_settings:
        mock_settings.EMBEDDING_MODEL = "test/model"
        mock_settings.OPENROUTER_API_KEY = "test-key"
        mock_settings.CHROMA_DB_PATH = "./test_db"
        mock_settings.VECTOR_SEARCH_K = 5
        mock_settings.HYBRID_RETRIEVER_WEIGHTS = [0.4, 0.6]
        
        builder = RetrieverBuilder()
        
        with patch("retriever.builder.Chroma") as MockChroma:
            MockChroma.from_documents.side_effect = Exception("ChromaDB Error")
            
            mock_docs = [MagicMock()]
            
            with pytest.raises(Exception, match="ChromaDB Error"):
                builder.build_hybrid_retriever(mock_docs)
