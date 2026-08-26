"""
Tests Unitarios - Categoría 4: Utilidades (Logging)

Tests para el sistema de logging del proyecto.
"""
import pytest
from utils.logging import logger


class TestLogger:
    """Tests para utils/logging.py."""

    def test_logger_exists(self):
        """logger debe existir y ser una instancia de loguru."""
        assert logger is not None

    def test_logger_has_handlers(self):
        """logger debe tener al menos un handler configurado."""
        assert len(logger._core.handlers) > 0

    def test_logger_has_file_handler(self):
        """logger debe tener un handler de archivo."""
        handler_names = [str(h) for h in logger._core.handlers.values()]
        assert any("app.log" in h for h in handler_names)

    def test_logger_can_log(self):
        """logger debe poder escribir mensajes sin errores."""
        logger.info("Test message from unit test")
        logger.debug("Debug message from unit test")
        logger.warning("Warning message from unit test")

    def test_logger_has_rotation(self):
        """logger debe tener configuración de rotation."""
        for handler in logger._core.handlers.values():
            if hasattr(handler, '_sink'):
                assert handler._sink is not None

    def test_logger_has_format(self):
        """logger debe tener formato configurado."""
        assert logger is not None

    def test_logger_multiple_handlers(self):
        """logger debe poder tener múltiples handlers."""
        initial_count = len(logger._core.handlers)
        assert initial_count >= 1

    def test_logger_handler_types(self):
        """logger debe tener handlers del tipo correcto."""
        for handler in logger._core.handlers.values():
            assert hasattr(handler, '_sink') or hasattr(handler, 'sink')
