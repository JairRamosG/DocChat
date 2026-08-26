"""
Tests Unitarios - Categoría 2: Procesamiento de Documentos (DocumentProcessor)

Tests de hash, cache, validación y procesamiento de archivos.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pytest
from document_processor.file_handler import DocumentProcessor


class RealChunk:
    """Mock chunk object que se puede serializar con pickle."""
    def __init__(self, content):
        self.page_content = content
        self.metadata = {}


@pytest.fixture
def processor():
    """Crear una instancia de DocumentProcessor con cache temporal."""
    with patch("document_processor.file_handler.settings") as mock_settings:
        mock_settings.CACHE_DIR = tempfile.mkdtemp()
        mock_settings.CACHE_EXPIRE_DAYS = 7
        yield DocumentProcessor()


@pytest.fixture
def sample_file():
    """Crear un archivo temporal para testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test content")
        yield f.name
    os.unlink(f.name)


# ============================================================
# HASH
# ============================================================

class TestHash:
    """Tests para _generate_hash."""

    def test_returns_hexdigest(self, processor):
        """_generate_hash debe devolver un hash SHA256 en hex."""
        content = b"hello world"
        result = processor._generate_hash(content)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_is_deterministic(self, processor):
        """_generate_hash debe devolver el mismo hash para el mismo input."""
        content = b"test content"
        hash1 = processor._generate_hash(content)
        hash2 = processor._generate_hash(content)
        assert hash1 == hash2

    def test_different_for_different_content(self, processor):
        """_generate_hash debe devolver hashes diferentes para inputs diferentes."""
        hash1 = processor._generate_hash(b"content A")
        hash2 = processor._generate_hash(b"content B")
        assert hash1 != hash2


# ============================================================
# VALIDACIÓN
# ============================================================

class TestValidation:
    """Tests para validate_files."""

    def test_under_limit(self, processor, sample_file):
        """validate_files no debe fallar si el tamaño es menor al límite."""
        file_obj = MagicMock()
        file_obj.name = sample_file
        processor.validate_files([file_obj])

    def test_over_limit(self, processor, tmp_path):
        """validate_files debe fallar si excede el límite total."""
        import config.constants as const

        big_file = tmp_path / "big_file.txt"
        big_file.write_bytes(b"x" * (const.MAX_TOTAL_SIZE + 1))

        file_obj = MagicMock()
        file_obj.name = str(big_file)

        with pytest.raises(ValueError, match="exceeds"):
            processor.validate_files([file_obj])


# ============================================================
# CACHE
# ============================================================

class TestCache:
    """Tests para el sistema de cache."""

    def test_is_cache_valid_returns_false_when_not_exists(self, processor):
        """_is_cache_valid debe devolver False si el archivo no existe."""
        fake_path = Path("/nonexistent/cache/file.pkl")
        assert processor._is_cache_valid(fake_path) is False

    def test_is_cache_valid_returns_true_when_recent(self, processor):
        """_is_cache_valid debe devolver True si el cache es reciente."""
        cache_path = Path(processor.cache_dir) / "test_cache.pkl"
        cache_path.touch()
        assert processor._is_cache_valid(cache_path) is True
        cache_path.unlink()

    def test_is_cache_valid_returns_false_when_expired(self, processor):
        """_is_cache_valid debe devolver False si el cache expiró."""
        cache_path = Path(processor.cache_dir) / "expired_cache.pkl"
        cache_path.touch()
        old_time = (datetime.now() - timedelta(days=30)).timestamp()
        os.utime(cache_path, (old_time, old_time))
        assert processor._is_cache_valid(cache_path) is False
        cache_path.unlink()

    def test_save_to_cache_creates_file(self, processor, tmp_path):
        """_save_to_cache debe crear el archivo pickle."""
        cache_path = tmp_path / "test_cache.pkl"
        chunks = ["chunk1", "chunk2"]

        processor._save_to_cache(chunks, cache_path)

        assert cache_path.exists()
        assert cache_path.is_file()

    def test_load_from_cache_returns_chunks(self, processor, tmp_path):
        """_load_from_cache debe devolver los chunks guardados."""
        cache_path = tmp_path / "test_cache.pkl"
        expected_chunks = ["chunk1", "chunk2", "chunk3"]
        processor._save_to_cache(expected_chunks, cache_path)

        result = processor._load_from_cache(cache_path)

        assert result == expected_chunks

    def test_save_load_roundtrip(self, processor, tmp_path):
        """Guardar → cargar debe devolver los mismos datos."""
        cache_path = tmp_path / "roundtrip.pkl"
        original_chunks = [
            {"page_content": "test", "metadata": {"source": "test.pdf"}},
            {"page_content": "test2", "metadata": {"source": "test2.pdf"}}
        ]

        processor._save_to_cache(original_chunks, cache_path)
        loaded_chunks = processor._load_from_cache(cache_path)

        assert loaded_chunks == original_chunks


# ============================================================
# PROCESAMIENTO DE ARCHIVOS
# ============================================================

class TestFileProcessing:
    """Tests para _process_file y process."""

    def test_unsupported_type_returns_empty(self, processor):
        """_process_file debe devolver [] para archivos no soportados."""
        unsupported_file = MagicMock()
        unsupported_file.name = "test.xyz"

        result = processor._process_file(unsupported_file)

        assert result == []

    def test_supported_type_processes(self, processor):
        """_process_file debe procesar archivos soportados."""
        supported_file = MagicMock()
        supported_file.name = "test.pdf"

        with patch("document_processor.file_handler.DocumentConverter") as MockConverter:
            mock_doc = MagicMock()
            mock_doc.document.export_to_markdown.return_value = "# Test\nContent"
            MockConverter.return_value.convert.return_value = mock_doc

            with patch("document_processor.file_handler.MarkdownHeaderTextSplitter") as MockSplitter:
                MockSplitter.return_value.split_text.return_value = ["chunk1", "chunk2"]

                result = processor._process_file(supported_file)

                assert len(result) == 2
                MockConverter.return_value.convert.assert_called_once_with("test.pdf")

    def test_deduplicates_chunks(self, processor, tmp_path):
        """process() debe eliminar chunks duplicados."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Same content")
        file2.write_text("Same content")

        file_obj1 = MagicMock()
        file_obj1.name = str(file1)
        file_obj2 = MagicMock()
        file_obj2.name = str(file2)

        with patch.object(processor, "_process_file") as mock_process:
            mock_process.return_value = [RealChunk("Same content")]

            result = processor.process([file_obj1, file_obj2])

            assert len(result) == 1

    def test_caches_results(self, processor, tmp_path):
        """process() debe guardar en cache después de procesar."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        file_obj = MagicMock()
        file_obj.name = str(test_file)

        with patch.object(processor, "_process_file") as mock_process:
            mock_chunk = MagicMock()
            mock_chunk.page_content = "Test content"
            mock_process.return_value = [mock_chunk]

            processor.process([file_obj])

            cache_files = list(processor.cache_dir.glob("*.pkl"))
            assert len(cache_files) > 0

    def test_loads_from_cache(self, processor, tmp_path):
        """process() debe usar el cache si existe."""
        test_file = tmp_path / "cached.txt"
        test_file.write_text("Cached content")

        file_obj = MagicMock()
        file_obj.name = str(test_file)

        cached_chunk = RealChunk("cached_chunk")

        file_hash = processor._generate_hash(test_file.read_bytes())
        cache_path = processor.cache_dir / f"{file_hash}.pkl"
        processor._save_to_cache([cached_chunk], cache_path)

        with patch.object(processor, "_process_file") as mock_process:
            result = processor.process([file_obj])

            mock_process.assert_not_called()
            assert len(result) == 1
            assert result[0].page_content == "cached_chunk"
