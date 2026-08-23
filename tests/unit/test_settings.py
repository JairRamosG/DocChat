"""Tests for config/settings.py"""
import os
from unittest.mock import patch
import pytest
from config.settings import Settings


@pytest.fixture
def mock_env():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-12345"}):
        yield

def test_settings_loads_with_api_key(mock_env):
    """Settings should load with valid API key."""
    settings = Settings()
    assert settings.OPENROUTER_API_KEY == "test-key-12345"


def test_default_chat_model(mock_env):
    """Default chat model should be deepseek."""
    settings = Settings()
    assert settings.CHAT_MODEL == "deepseek/deepseek-chat"


def test_default_embedding_model(mock_env):
    """Default embedding model should be qwen."""
    settings = Settings()
    assert settings.EMBEDDING_MODEL == "qwen/qwen3-embedding-8b"


def test_default_max_file_size(mock_env):
    """Max file size should match constant."""
    settings = Settings()
    assert settings.MAX_FILE_SIZE == 50 * 1024 * 1024


def test_default_max_total_size(mock_env):
    """Max total size should match constant."""
    settings = Settings()
    assert settings.MAX_TOTAL_SIZE == 200 * 1024 * 1024


def test_default_allowed_types(mock_env):
    """Allowed types should match constant."""
    settings = Settings()
    assert settings.ALLOWED_TYPES == [".txt", ".pdf", ".docx", ".md"]


def test_default_chroma_db_path(mock_env):
    """ChromaDB path should be ./chroma_db."""
    settings = Settings()
    assert settings.CHROMA_DB_PATH == "./chroma_db"


def test_default_chroma_collection_name(mock_env):
    """ChromaDB collection name should be 'documents'."""
    settings = Settings()
    assert settings.CHROMA_COLLECTION_NAME == "documents"


def test_default_vector_search_k(mock_env):
    """Vector search K should be 10."""
    settings = Settings()
    assert settings.VECTOR_SEARCH_K == 10


def test_default_hybrid_weights(mock_env):
    """Hybrid weights should be [0.4, 0.6]."""
    settings = Settings()
    assert settings.HYBRID_RETRIEVER_WEIGHTS == [0.4, 0.6]


def test_default_log_level(mock_env):
    """Log level should be INFO."""
    settings = Settings()
    assert settings.LOG_LEVEL == "INFO"


def test_default_cache_dir(mock_env):
    """Cache dir should be document_cache."""
    settings = Settings()
    assert settings.CACHE_DIR == "document_cache"


def test_default_cache_expire_days(mock_env):
    """Cache expire days should be 7."""
    settings = Settings()
    assert settings.CACHE_EXPIRE_DAYS == 7


def test_custom_values(mock_env):
    """Settings should accept custom values."""
    with patch.dict(os.environ, {
        "OPENROUTER_API_KEY": "custom-key",
        "CHAT_MODEL": "openai/gpt-4",
        "LOG_LEVEL": "DEBUG"
    }):
        settings = Settings()
        assert settings.OPENROUTER_API_KEY == "custom-key"
        assert settings.CHAT_MODEL == "openai/gpt-4"
        assert settings.LOG_LEVEL == "DEBUG"
