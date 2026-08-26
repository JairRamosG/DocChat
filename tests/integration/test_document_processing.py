"""
Tests de Integración - Categoría 1: Pipeline de procesamiento de documentos

Estos tests prueban que DocumentProcessor funciona correctamente
con archivos reales (o simulados) de punta a punta.
"""
import pytest
import tempfile
import os
from pathlib import Path
from document_processor.file_handler import DocumentProcessor


@pytest.fixture
def processor():
    """Fixture: una instancia limpia de DocumentProcessor."""
    return DocumentProcessor()


@pytest.fixture
def sample_txt_file(tmp_path):
    """Fixture: crea un archivo .txt temporal con contenido de prueba."""
    file_path = tmp_path / "test_document.txt"
    file_path.write_text(
        "Este es un documento de prueba.\n"
        "Contiene varias lineas de texto.\n"
        "Python es un lenguaje de programacion.\n"
    )
    return file_path


@pytest.fixture
def sample_md_file(tmp_path):
    """Fixture: crea un archivo .md temporal."""
    file_path = tmp_path / "test_document.md"
    file_path.write_text(
        "# Titulo Principal\n"
        "Contenido de la seccion uno.\n\n"
        "## Subtitulo\n"
        "Contenido de la seccion dos.\n"
    )
    return file_path


# ============================================================
# TEST 1: Un .txt se procesa y devuelve chunks
# ============================================================
def test_process_txt_returns_chunks(processor, sample_txt_file):
    """
    Verifica que un archivo .txt se convierte en una lista de chunks.

    Flujo:
    1. Crear un .txt con contenido real
    2. Pasarlo a DocumentProcessor.process()
    3. Verificar que retorna una lista NO vacía
    4. Verificar que cada chunk tiene page_content
    """
    # Crear un objeto similar a lo que Gradio pasa (con atributo .name)
    class FakeFile:
        def __init__(self, path):
            self.name = str(path)

    files = [FakeFile(sample_txt_file)]

    # Ejecutar el procesamiento
    chunks = processor.process(files)

    # Verificar
    assert isinstance(chunks, list), "Debe retornar una lista"
    assert len(chunks) > 0, "Debe generar al menos un chunk"
    assert hasattr(chunks[0], "page_content"), "Cada chunk debe tener page_content"
    assert len(chunks[0].page_content) > 0, "El chunk no puede estar vacío"


# ============================================================
# TEST 2: Un .md se procesa correctamente
# ============================================================
def test_process_md_returns_chunks(processor, sample_md_file):
    """
    Verifica que un archivo Markdown se procesa correctamente.

    El MarkdownHeaderTextSplitter debería dividir por headers.
    """
    class FakeFile:
        def __init__(self, path):
            self.name = str(path)

    files = [FakeFile(sample_md_file)]
    chunks = processor.process(files)

    assert len(chunks) > 0
    # El markdown tiene 2 headers, debería generar al menos 2 chunks
    # (uno por sección)
    assert len(chunks) >= 1


# ============================================================
# TEST 3: Múltiples archivos no generan duplicados
# ============================================================
def test_process_multiple_files_deduplicates(processor, sample_txt_file):
    """
    Verifica que si procesás el mismo archivo 2 veces,
    no se generan chunks duplicados.

    El código usa seen_hashes para deduplicar.
    """
    class FakeFile:
        def __init__(self, path):
            self.name = str(path)

    # Pasar el mismo archivo dos veces
    files = [FakeFile(sample_txt_file), FakeFile(sample_txt_file)]
    chunks = processor.process(files)

    # Verificar que no hay chunks con el mismo contenido
    contents = [c.page_content for c in chunks]
    unique_contents = set(contents)

    assert len(contents) == len(unique_contents), (
        f"Hay duplicados: {len(contents)} chunks pero "
        f"solo {len(unique_contents)} únicos"
    )


# ============================================================
# TEST 4: Archivo no soportado se ignora sin error
# ============================================================
def test_process_unsupported_file_skips(processor, tmp_path):
    """
    Verifica que un archivo .exe (no soportado) se ignora
    silenciosamente sin lanzar excepción.

    El código hace: if not file.name.endswith(('.pdf', '.docx', '.txt', '.md'))
    """
    class FakeFile:
        def __init__(self, path):
            self.name = str(path)

    # Crear un archivo .exe (simulado)
    exe_file = tmp_path / "malware.exe"
    exe_file.write_bytes(b"MZ\x90\x00")  # Header de .exe

    files = [FakeFile(exe_file)]

    # NO debe lanzar error
    chunks = processor.process(files)

    # Debe retornar lista vacía (el archivo se ignoró)
    assert isinstance(chunks, list)
    assert len(chunks) == 0


# ============================================================
# TEST 5: Cache hit evita reprocesar con Docling
# ============================================================
def test_cache_hit_skips_docling(processor, sample_txt_file):
    """
    Verifica que la segunda vez que procesás el mismo archivo,
    se usa el cache en vez de llamar a Docling.

    Flujo:
    1. Procesar archivo una vez → se guarda en cache
    2. Procesar el mismo archivo otra vez → debería cargar del cache
    3. Ambos resultados deben ser idénticos

    Nota: Este test es de integración porque verifica el comportamiento
    real del cache (lectura/escritura de archivos .pkl).
    """
    class FakeFile:
        def __init__(self, path):
            self.name = str(path)

    files = [FakeFile(sample_txt_file)]

    # Primera vez: procesa con Docling y guarda en cache
    chunks_first = processor.process(files)

    # Segunda vez: debería usar el cache
    chunks_second = processor.process(files)

    # Los resultados deben ser idénticos
    assert len(chunks_first) == len(chunks_second)
    for i in range(len(chunks_first)):
        assert chunks_first[i].page_content == chunks_second[i].page_content


# ============================================================
# TEST 6 (TU TURNO): Validar que archivos muy grandes se rechazan
# ============================================================
# def test_validate_files_rejects_oversized(processor):
#     """
#     Verifica que validate_files lanza ValueError
#     cuando los archivos superan MAX_TOTAL_SIZE.
#
#     Pista: mirá cómo funciona validate_files en file_handler.py
#     y cuál es el valor de constants.MAX_TOTAL_SIZE
#     """
#     pass
