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
# TESTS IMPLEMENTADOS
# ============================================


def test_save_to_cache_creates_file(processor, tmp_path):
    """_save_to_cache debe crear el archivo pickle."""
    # Arrange
    cache_path = tmp_path / "test_cache.pkl"
    chunks = ["chunk1", "chunk2"]
    
    # Act
    processor._save_to_cache(chunks, cache_path)
    
    # Assert
    assert cache_path.exists()
    assert cache_path.is_file()


def test_load_from_cache_returns_chunks(processor, tmp_path):
    """_load_from_cache debe devolver los chunks guardados."""
    # Arrange
    cache_path = tmp_path / "test_cache.pkl"
    expected_chunks = ["chunk1", "chunk2", "chunk3"]
    processor._save_to_cache(expected_chunks, cache_path)
    
    # Act
    result = processor._load_from_cache(cache_path)
    
    # Assert
    assert result == expected_chunks


def test_load_from_cache_roundtrip(processor, tmp_path):
    """Guardar → cargar debe devolver los mismos datos."""
    # Arrange
    cache_path = tmp_path / "roundtrip.pkl"
    original_chunks = [
        {"page_content": "test", "metadata": {"source": "test.pdf"}},
        {"page_content": "test2", "metadata": {"source": "test2.pdf"}}
    ]
    
    # Act
    processor._save_to_cache(original_chunks, cache_path)
    loaded_chunks = processor._load_from_cache(cache_path)
    
    # Assert
    assert loaded_chunks == original_chunks


def test_process_file_unsupported_type(processor):
    """_process_file debe devolver [] para archivos no soportados."""
    # Arrange
    unsupported_file = MagicMock()
    unsupported_file.name = "test.xyz"  # Extensión no soportada
    
    # Act
    result = processor._process_file(unsupported_file)
    
    # Assert
    assert result == []


def test_process_file_supported_type(processor):
    """_process_file debe procesar archivos soportados."""
    # Arrange
    supported_file = MagicMock()
    supported_file.name = "test.pdf"
    
    with patch("document_processor.file_handler.DocumentConverter") as MockConverter:
        mock_doc = MagicMock()
        mock_doc.document.export_to_markdown.return_value = "# Test\nContent"
        MockConverter.return_value.convert.return_value = mock_doc
        
        with patch("document_processor.file_handler.MarkdownHeaderTextSplitter") as MockSplitter:
            MockSplitter.return_value.split_text.return_value = ["chunk1", "chunk2"]
            
            # Act
            result = processor._process_file(supported_file)
            
            # Assert
            assert len(result) == 2
            MockConverter.return_value.convert.assert_called_once_with("test.pdf")


def test_process_deduplicates_chunks(processor, tmp_path):
    """process() debe eliminar chunks duplicados."""
    # Arrange - crear dos archivos con el mismo contenido
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("Same content")
    file2.write_text("Same content")
    
    file_obj1 = MagicMock()
    file_obj1.name = str(file1)
    file_obj2 = MagicMock()
    file_obj2.name = str(file2)
    
    with patch.object(processor, "_process_file") as mock_process:
        # Retornar el mismo chunk para ambos archivos
        mock_chunk = MagicMock()
        mock_chunk.page_content = "Same content"
        mock_process.return_value = [mock_chunk]
        
        # Act
        result = processor.process([file_obj1, file_obj2])
        
        # Assert - solo debe haber 1 chunk, no 2
        assert len(result) == 1


def test_process_caches_results(processor, tmp_path):
    """process() debe guardar en cache después de procesar."""
    # Arrange
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    
    file_obj = MagicMock()
    file_obj.name = str(test_file)
    
    with patch.object(processor, "_process_file") as mock_process:
        mock_chunk = MagicMock()
        mock_chunk.page_content = "Test content"
        mock_process.return_value = [mock_chunk]
        
        # Act
        processor.process([file_obj])
        
        # Assert - debe crear archivos en cache
        cache_files = list(processor.cache_dir.glob("*.pkl"))
        assert len(cache_files) > 0


def test_process_loads_from_cache(processor, tmp_path):
    """process() debe usar el cache si existe."""
    # Arrange - crear un archivo y pre-cargar su cache
    test_file = tmp_path / "cached.txt"
    test_file.write_text("Cached content")
    
    file_obj = MagicMock()
    file_obj.name = str(test_file)
    
    # Pre-cargar el cache
    file_hash = processor._generate_hash(test_file.read_bytes())
    cache_path = processor.cache_dir / f"{file_hash}.pkl"
    processor._save_to_cache(["cached_chunk"], cache_path)
    
    with patch.object(processor, "_process_file") as mock_process:
        # Act
        result = processor.process([file_obj])
        
        # Assert - NO debe llamar a _process_file porque usa cache
        mock_process.assert_not_called()
        assert result == ["cached_chunk"]
