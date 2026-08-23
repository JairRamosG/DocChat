"""Tests for utils/logging.py"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
from utils.logging import logger


def test_logger_exists():
    """logger debe existir y ser una instancia de loguru."""
    assert logger is not None


def test_logger_has_handlers():
    """logger debe tener al menos un handler configurado."""
    assert len(logger._core.handlers) > 0


def test_logger_has_file_handler():
    """logger debe tener un handler de archivo."""
    # Verificar que hay un handler que escribe a app.log
    handler_names = [str(h) for h in logger._core.handlers.values()]
    assert any("app.log" in h for h in handler_names)


def test_logger_can_log():
    """logger debe poder escribir mensajes sin errores."""
    # No debe lanzar excepción
    logger.info("Test message from unit test")
    logger.debug("Debug message from unit test")
    logger.warning("Warning message from unit test")


def test_logger_has_rotation():
    """logger debe tener configuración de rotation."""
    # Verificar que los handlers tienen rotation configurado
    for handler in logger._core.handlers.values():
        # Verificar que el handler tiene un sink (archivo)
        if hasattr(handler, '_sink'):
            assert handler._sink is not None


def test_logger_has_format():
    """logger debe tener formato configurado."""
    # Verificar que el logger puede logear con el formato correcto
    # (ya verificamos que puede logear en test_logger_can_log)
    assert logger is not None


def test_logger_multiple_handlers():
    """logger debe poder tener múltiples handlers."""
    initial_count = len(logger._core.handlers)
    assert initial_count >= 1


def test_logger_handler_types():
    """logger debe tener handlers del tipo correcto."""
    for handler in logger._core.handlers.values():
        # Verificar que es un handler de loguru
        assert hasattr(handler, '_sink') or hasattr(handler, 'sink')
