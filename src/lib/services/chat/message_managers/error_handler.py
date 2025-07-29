#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Error handler

Decorator to log catch exception error
"""

from functools import wraps
from typing import Callable
from src.lib.services.core.log import Logger


logger = Logger().get_logger()


def message_error_handler(error_prefix: str):
    """
    Decorator to handle common error patterns in message operations.
    
    :param error_prefix: Prefix for error messages (e.g., "Error saving message")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.result.status = "success"
            try:
                return func(self, *args, **kwargs)
            except Exception as e:  # pylint: disable=W0718
                self.result.status = "failure"
                self.result.error_message = f"{error_prefix}: {e}"
                logger.error(self.result.error_message)
                return self.result
        return wrapper
    return decorator
