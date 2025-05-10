#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FileCache Module

This module provides functionalities to cache files.
"""

import os
import pickle
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field
from src.lib.core.log import Logger


logger = Logger().get_logger()


class FileCache:
    """
    A class used to cache files.
    """

    class Config(BaseModel):
        """
        Configuration model for logging settings within an application.
        """
        cache_to_file: Optional[bool] = Field(
            default=False,
            description="Flag to cache the file."
        )
        cache_file_postfix: Optional[str] = Field(
            default="cached",
            description="Postfix of the cached file."
        )
        cache_file_extension: Optional[str] = Field(
            default="pkl",
            description="Extention of the cached file."
        )

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the FileCache with the option to cache to a file.

        :param confi: configuration file.
        """
        self.config = FileCache.Config(**(config or {}))

    def is_cached(self, file_path: str) -> bool:
        """
        Check if a file is cached at the given path.

        :param file_path: The path to the original file.
        :return: Boolean indicating if the file is cached.
        """
        cached_file_path = self._get_cached_file_path(file_path)
        return os.path.exists(cached_file_path) and self.config.cache_to_file

    def _get_cached_file_path(self, file_path: str) -> str:
        """
        Generate the cached file path based on the original file path.

        :param file_path: The path to the original file.
        :return: The path to the cached file.
        """
        base, _ = os.path.splitext(file_path)
        return f"{base}_{self.config.cache_file_postfix}.{self.config.cache_file_extension}"

    def save(self, file_path: str, data: Any) -> None:
        """
        Save data to a pickle file.

        :param file_path: The path to the original file.
        :param data: Data to be saved.
        """
        if self.config.cache_to_file:
            cached_file_path = self._get_cached_file_path(file_path)
            try:
                with open(cached_file_path, 'wb') as file:
                    pickle.dump(data, file)
                logger.info(f"Data saved to {cached_file_path}.")
            except Exception as e:  # pylint: disable=W0718
                logger.error(f"Failed to save data to {file_path}: {e}")
        else:
            logger.warning("Data not saved because the cache is disabled.")

    def load(self, file_path: str) -> Any:
        """
        Load data from a pickle file.

        :param file_path: The path to the original file.
        :return: The loaded data, or None if loading fails.
        """
        if self.is_cached(file_path):
            try:
                cached_file_path = self._get_cached_file_path(file_path)
                with open(cached_file_path, 'rb') as file:
                    data = pickle.load(file)
                logger.info(f"Data loaded from {cached_file_path}.")
                return data
            except Exception as e:  # pylint: disable=W0718
                logger.error(f"Failed to load data from {file_path}: {e}")
                return None
        else:
            logger.warning("No file found or cache disabled.")
            return None
