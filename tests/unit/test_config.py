"""
Tests Unitarios - Categoría 3: Configuración (Constants + Settings)

Tests para las constantes y la configuración del proyecto.
"""
import os
from unittest.mock import patch
import pytest
from config.constants import MAX_FILE_SIZE, MAX_TOTAL_SIZE, ALLOWED_TYPES
from config.settings import Settings


# ============================================================
# CONSTANTS
# ============================================================

class TestConstants:
    """Tests para config/constants.py."""

    def test_max_file_size_is_50mb(self):
        """MAX_FILE_SIZE debe ser 50 MB."""
        assert MAX_FILE_SIZE == 50 * 1024 * 1024

    def test_max_total_size_is_200mb(self):
        """MAX_TOTAL_SIZE debe ser 200 MB."""
        assert MAX_TOTAL_SIZE == 200 * 1024 * 1024

    def test_allowed_types_are_list(self):
        """ALLOWED_TYPES debe ser una lista."""
        assert isinstance(ALLOWED_TYPES, list)

    def test_allowed_types_contains_expected(self):
        """ALLOWED_TYPES debe contener .txt, .pdf, .docx, .md."""
        expected = [".txt", ".pdf", ".docx", ".md"]
        assert ALLOWED_TYPES == expected

    def test_max_total_size_greater_than_max_file(self):
        """MAX_TOTAL_SIZE debe ser mayor que MAX_FILE_SIZE."""
        assert MAX_TOTAL_SIZE > MAX_FILE_SIZE


# ============================================================
# SETTINGS
# ============================================================

@pytest.fixture
def mock_env():
    """Mock environment variables para testing."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield


class TestSettings:
    """Tests para config/settings.py."""

    def test_loads_with_api_key(self, mock_env):
        """Settings debe cargar con API key válida."""
        settings = Settings()
        assert settings.OPENROUTER_API_KEY == "test-key-12345"

    def test_default_chat_model(self, mock_env):
        """El modelo por defecto debe ser deepseek."""
        settings = Settings()
        assert settings.CHAT_MODEL == "deepseek/deepseek-chat"

    def test_default_embedding_model(self, mock_env):
        """El modelo de embedding por defecto debe ser qwen."""
        settings = Settings()
        assert settings.EMBEDDING_MODEL == "qwen/qwen3-embedding-8b"

    def test_default_max_file_size(self, mock_env):
        """MAX_FILE_SIZE por defecto debe coincidir con la constante."""
        settings = Settings()
        assert settings.MAX_FILE_SIZE == 50 * 1024 * 1024

    def test_default_max_total_size(self, mock_env):
        """MAX_TOTAL_SIZE por defecto debe coincidir con la constante."""
        settings = Settings()
        assert settings.MAX_TOTAL_SIZE == 200 * 1024 * 1024

    def test_default_allowed_types(self, mock_env):
        """ALLOWED_TYPES por defecto debe coincidir con la constante."""
        settings = Settings()
        assert settings.ALLOWED_TYPES == [".txt", ".pdf", ".docx", ".md"]

    def test_default_chroma_db_path(self, mock_env):
        """ChromaDB path por defecto debe ser ./chroma_db."""
        settings = Settings()
        assert settings.CHROMA_DB_PATH == "./chroma_db"

    def test_default_chroma_collection_name(self, mock_env):
        """ChromaDB collection name por defecto debe ser 'documents'."""
        settings = Settings()
        assert settings.CHROMA_COLLECTION_NAME == "documents"

    def test_default_vector_search_k(self, mock_env):
        """Vector search K por defecto debe ser 10."""
        settings = Settings()
        assert settings.VECTOR_SEARCH_K == 10

    def test_default_hybrid_weights(self, mock_env):
        """Hybrid weights por defecto deben ser [0.4, 0.6]."""
        settings = Settings()
        assert settings.HYBRID_RETRIEVER_WEIGHTS == [0.4, 0.6]

    def test_default_log_level(self, mock_env):
        """Log level por defecto debe ser INFO."""
        settings = Settings()
        assert settings.LOG_LEVEL == "INFO"

    def test_default_cache_dir(self, mock_env):
        """Cache dir por defecto debe ser document_cache."""
        settings = Settings()
        assert settings.CACHE_DIR == "document_cache"

    def test_default_cache_expire_days(self, mock_env):
        """Cache expire days por defecto debe ser 7."""
        settings = Settings()
        assert settings.CACHE_EXPIRE_DAYS == 7

    def test_custom_values(self, mock_env):
        """Settings debe aceptar valores personalizados."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "custom-key",
            "CHAT_MODEL": "openai/gpt-4",
            "LOG_LEVEL": "DEBUG"
        }):
            settings = Settings()
            assert settings.OPENROUTER_API_KEY == "custom-key"
            assert settings.CHAT_MODEL == "openai/gpt-4"
            assert settings.LOG_LEVEL == "DEBUG"
