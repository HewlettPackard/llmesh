#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module defines the Logger class, responsible for handling
application logging.

It implements a singleton pattern using Python's logging module.
The singleton ensures that the same logger instance is used throughout the application,
providing a centralized logging mechanism. This setup includes both file and console handlers,
allowing logs to be written simultaneously to a file and standard output.
A RotatingFileHandler is used for file logging to manage log size and log rotation.
"""

import sys
import logging
import logging.handlers
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LoggerSingleton(type):
    """
    A metaclass for creating a singleton instance of the Logger class.
    Ensures that only one instance of the Logger is created throughout the application.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(LoggerSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Logger(metaclass=LoggerSingleton):
    """
    Logger class for application-wide logging. This class is a singleton,
    ensuring all logging is centralized through one instance.
    """

    class Config(BaseModel):
        """
        Configuration model for logging settings within an application.
        """
        name: str = Field(
            default="ATHON",
            description="The name of the logger."
        )
        level: str = Field(
            default="DEBUG",
            description="The logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)."
        )
        log_file: str = Field(
            default="application.log",
            description="The file path where the log file will be stored."
        )
        log_format: Optional[str] = Field(
            default='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            description="The format in which log messages will be written."
        )
        max_bytes: Optional[int] = Field(
            default=10485760,  # 10 MB
            description="The maximum file size (in bytes) before the log is rotated."
        )
        backup_count: Optional[int] = Field(
            default=5,
            description="The number of backup files to keep before rotation."
        )

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Logger class with the provided configuration.
        If no configuration is provided, default settings are used.

        :param config: Optional dictionary with configuration settings.
        """
        self.config = Logger.Config(**(config or {}))
        self.logger = logging.getLogger(self.config.name)
        self.logger.propagate = False  # Prevent logging events from being passed to the parent
        self.logger.setLevel(self.config.level)
        self._setup_stdout_handler()

    def _setup_stdout_handler(self):
        """
        Set up the stdout handler for logging to the console.
        """
        if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.config.level)
            console_handler.setFormatter(logging.Formatter(self.config.log_format))
            self.logger.addHandler(console_handler)

    def _setup_file_handler(self):
        """
        Set up the file handler for logging to a file with rotation.
        """
        if not any(isinstance(handler, logging.FileHandler) for handler in self.logger.handlers):
            file_handler = logging.handlers.RotatingFileHandler(
                self.config.log_file,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count
            )
            file_handler.setLevel(self.config.level)
            file_handler.setFormatter(logging.Formatter(self.config.log_format))
            self.logger.addHandler(file_handler)


    def configure(self, config: Dict[str, Any]):
        """
        Reconfigure the logger with new settings.

        :param config: Dictionary with new configuration settings.
        :return: The reconfigured Logger instance.
        """
        self.logger.handlers.clear()  # Clear existing handlers to avoid duplicates
        self.config = Logger.Config(**config)
        self.logger.setLevel(self.config.level)
        self._setup_stdout_handler()
        self._setup_file_handler()
        return self


    def get_logger(self) -> logging.LoggerAdapter:
        """
        Retrieve the singleton logger instance with an adapter for additional context.

        :return: A LoggerAdapter instance with the component name included in the context.
        """
        return logging.LoggerAdapter(self.logger, {'component_name': self.config.name})
