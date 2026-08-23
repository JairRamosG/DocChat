"""Tests for document_processor/file_handler.py"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
import pytest
from document_processor.file_handler import DocumentProcessor


# ============================================
# TESTS YA IMPLEMENTADOS (ejemplos)
# ============================================


@pytest.fixture
def processor():
    """Create a DocumentProcessor instance."""
    with patch("document_processor.file_handler.settings") as mock_settings:
        mock_settings.CACHE_DIR = tempfile.mkdtemp()
        mock_settings.CACHE_EXPIRE_DAYS = 7
        yield DocumentProcessor()


@pytest.fixture
def sample_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test content")
        yield f.name
    os.unlink(f.name)


def test_generate_hash_returns_hexdigest(processor):
    """_generate_hash debe devolver un hash SHA256 en hex."""
    content = b"hello world"
    result = processor._generate_hash(content)
    assert isinstance(result, str)
    assert len(result) == 64  # SHA256 hex digest length


def test_generate_hash_is_deterministic(processor):
    """_generate_hash debe devolver el mismo hash para el mismo input."""
    content = b"test content"
    hash1 = processor._generate_hash(content)
    hash2 = processor._generate_hash(content)
    assert hash1 == hash2


def test_generate_hash_different_for_different_content(processor):
    """_generate_hash debe devolver hashes diferentes para inputs diferentes."""
    hash1 = processor._generate_hash(b"content A")
    hash2 = processor._generate_hash(b"content B")
    assert hash1 != hash2


def test_validate_files_under_limit(processor, sample_file):
    """validate_files no debe fallar si el tamaño es menor al límite."""
    file_obj = MagicMock()
    file_obj.name = sample_file
    # No debe lanzar excepción
    processor.validate_files([file_obj])


def test_validate_files_over_limit(processor, sample_file):
    """validate_files debe fallar si excede el límite total."""
    with patch("document_processor.file_handler.constants") as mock_constants:
        mock_constants.MAX_TOTAL_SIZE = 1  # 1 byte - muy pequeño
        file_obj = MagicMock()
        file_obj.name = sample_file
        with pytest.raises(ValueError, match="exceeds"):
            processor.validate_files([file_obj])


def test_is_cache_valid_returns_false_when_not_exists(processor):
    """_is_cache_valid debe devolver False si el archivo no existe."""
    fake_path = Path("/nonexistent/cache/file.pkl")
    assert processor._is_cache_valid(fake_path) is False


def test_is_cache_valid_returns_true_when_recent(processor):
    """_is_cache_valid debe devolver True si el cache es reciente."""
    cache_path = Path(processor.cache_dir) / "test_cache.pkl"
    # Crear archivo con timestamp actual
    cache_path.touch()
    assert processor._is_cache_valid(cache_path) is True
    cache_path.unlink()


def test_is_cache_valid_returns_false_when_expired(processor):
    """_is_cache_valid debe devolver False si el cache expiró."""
    cache_path = Path(processor.cache_dir) / "expired_cache.pkl"
    cache_path.touch()
    # Modificar timestamp a hace 30 días
    old_time = (datetime.now() - timedelta(days=30)).timestamp()
    os.utime(cache_path, (old_time, old_time))
    assert processor._is_cache_valid(cache_path) is False
    cache_path.unlink()


# ============================================
# TESTS PARA QUE VOS IMPLEMENTES
# ============================================

# TODO: test_save_to_cache_creates_file
# Verifica que _save_to_cache crea el archivo pickle
# Hint: usa tmp_path de pytest y mockea pickle.dump


# TODO: test_load_from_cache_returns_chunks
# Verifica que _load_from_cache devuelve los chunks guardados
# Hint: crea un archivo pickle manualmente y verificá que se lee correctamente


# TODO: test_load_from_cache_roundtrip
# Verifica que guardar → cargar devuelve los mismos datos
# Hint: guarda chunks, luego cargalos y compará


# TODO: test_process_file_unsupported_type
# Verifica que _process_file devuelve [] para archivos no soportados
# Hint: mockea un archivo con extensión .xyz


# TODO: test_process_deduplicates_chunks
# Verifica que process() elimina chunks duplicados
# Hint: crea dos archivos con el mismo contenido


# TODO: test_process_caches_results
# Verifica que process() guarda en cache después de procesar
# Hint: verifica que se crea el archivo pickle después de process()


# TODO: test_process_loads_from_cache
# Verifica que process() usa el cache si existe
# Hint: pre-carga un cache y verificá que no se llama a _process_file
