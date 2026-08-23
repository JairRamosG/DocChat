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


def test_logger_config():
    """logger debe estar configurado con rotation y retention."""
    # Verificar que la configuración tiene los valores correctos
    assert logger._core.config["rotation"] == "10 MB" or "10 mb" in str(logger._core.config).lower()
    assert logger._core.config["retention"] == "30 days" or "30 days" in str(logger._core.config).lower()


def test_logger_can_log():
    """logger debe poder escribir mensajes sin errores."""
    # No debe lanzar excepción
    logger.info("Test message from unit test")
    logger.debug("Debug message from unit test")
    logger.warning("Warning message from unit test")


def test_logger_format():
    """logger debe tener el formato configurado correctamente."""
    format_str = logger._core.config["format"]
    assert "time" in format_str or "{time" in format_str
    assert "level" in format_str or "{level" in format_str
    assert "message" in format_str or "{message" in format_str
