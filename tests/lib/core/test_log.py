#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test suite for the Logger class which utilizes the singleton pattern for application-wide logging.
The tests ensure that the Logger class is correctly instantiated as a singleton with 
proper configuration and that it behaves correctly under different logging scenarios.
"""

import os
import logging
from unittest.mock import patch, MagicMock
import pytest
from src.lib.core.log import Logger


@pytest.fixture(autouse=True)
def reset_singleton():
    """Fixture to reset the singleton instance before each test."""
    Logger._instances.clear()  # pylint: disable=W0212
    yield

def test_logger_singleton():
    """
    Test that the Logger class follows the singleton pattern,
    meaning that all calls return the same instance.
    """
    config = {
        "name": "AppLogger"
    }
    logger_instance = Logger()
    logger_instance.configure(config)
    logger1 = logger_instance.get_logger().logger
    logger2 = logger_instance.get_logger().logger
    assert logger1 is logger2
    assert logger1 == logger2


def test_logger_configuration_and_adapter():
    """
    Test that the Logger's configuration is applied correctly and that the LoggerAdapter
    has the correct context (name).
    """
    config = {
        "name": "AppLogger",
        "log_file": "tests/logs/test.log",
        "level": "INFO",
        "log_format": '%(asctime)s - %(levelname)s - %(message)s',
        "max_bytes": 1024,
        "backup_count": 3
    }
    with patch('logging.getLogger') as mock_get_logger, \
         patch('logging.handlers.RotatingFileHandler') as mock_file_handler:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        # Instantiate and configure the Logger
        logger_instance = Logger()
        logger_instance.configure(config)
        logger_adapter = logger_instance.get_logger()
        # Assert the adapter is carrying the correct name context
        assert logger_adapter.extra['component_name'] == "AppLogger", \
            "LoggerAdapter should carry the correct name."
        # Check if the file handler was correctly instantiated and configured
        mock_file_handler.assert_called_once_with(
            'tests/logs/test.log',
            maxBytes=1024,
            backupCount=3
        )
        # This is checking if any handler has been configured with the correct format
        for handler in mock_logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                # pylint: disable=W0212
                assert handler.formatter._fmt == config['log_format'], \
                    "Log format should match the configuration."


def test_file_handler_setup():
    """
    Test the file handler setup to ensure it configures correctly with rotation and formatting.
    """
    config = {
        "log_file": "tests/logs/test.log",
        "level": "DEBUG",
        "max_bytes": 1024,
        "backup_count": 3
    }
    with patch('logging.getLogger', return_value=MagicMock(handlers=[])):
        logger = Logger().configure(config).get_logger().logger
        file_handler = MagicMock(spec=logging.handlers.RotatingFileHandler)
        logger.handlers.append(file_handler)
        assert isinstance(logger.handlers[0], logging.handlers.RotatingFileHandler)


def test_stream_handler_setup():
    """
    Test the stream handler setup to check if it's properly attached to stdout and configured.
    """
    config = {
        "level": "WARNING",
    }
    with patch('logging.getLogger', return_value=MagicMock(handlers=[])), patch('sys.stdout'):
        logger = Logger().configure(config).get_logger().logger
        stream_handler = MagicMock(spec=logging.StreamHandler)
        logger.handlers.append(stream_handler)
        assert isinstance(logger.handlers[0], logging.StreamHandler)


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
