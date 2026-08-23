"""Tests for config/constants.py"""
from config.constants import MAX_FILE_SIZE, MAX_TOTAL_SIZE, ALLOWED_TYPES


def test_max_file_size_is_50mb():
    """MAX_FILE_SIZE debe ser 50 MB."""
    assert MAX_FILE_SIZE == 50 * 1024 * 1024


def test_max_total_size_is_200mb():
    """MAX_TOTAL_SIZE debe ser 200 MB."""
    assert MAX_TOTAL_SIZE == 200 * 1024 * 1024


def test_allowed_types_are_list():
    """ALLOWED_TYPES debe ser una lista."""
    assert isinstance(ALLOWED_TYPES, list)


def test_allowed_types_contains_expected():
    """ALLOWED_TYPES debe contener .txt, .pdf, .docx, .md."""
    expected = [".txt", ".pdf", ".docx", ".md"]
    assert ALLOWED_TYPES == expected


def test_max_total_size_greater_than_max_file():
    """MAX_TOTAL_SIZE debe ser mayor que MAX_FILE_SIZE."""
    assert MAX_TOTAL_SIZE > MAX_FILE_SIZE
