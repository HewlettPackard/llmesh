#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Error handler

Decorator to log catch exception error
"""

import inspect
from functools import wraps
from typing import Callable
from src.lib.core.log import Logger


logger = Logger().get_logger()


def model_error_handler(error_prefix: str):
    """
    Decorator to handle common error patterns in model operations (sync or async).
    
    :param error_prefix: Prefix for error messages (e.g., "Error invoking model")
    """
    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                self.result.status = "success"
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:  # pylint: disable=W0718
                    self.result.status = "failure"
                    self.result.error_message = f"{error_prefix}: {e}"
                    logger.error(self.result.error_message)
                    return self.result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                self.result.status = "success"
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:  # pylint: disable=W0718
                    self.result.status = "failure"
                    self.result.error_message = f"{error_prefix}: {e}"
                    logger.error(self.result.error_message)
                    return self.result
            return sync_wrapper
    return decorator

def stream_error_handler(error_prefix: str):
    """
    Decorator to handle errors in sync and async streaming functions (generators).
    
    :param error_prefix: Prefix for error messages (e.g., "Streaming error")
    """
    def decorator(func: Callable) -> Callable:
        if inspect.isasyncgenfunction(func):
            @wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                try:
                    async for item in func(self, *args, **kwargs):
                        yield item
                except Exception as e:  # pylint: disable=W0718
                    logger.error(f"{error_prefix}: {e}")
                    raise
            return async_wrapper
        elif inspect.isgeneratorfunction(func):
            @wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                try:
                    for item in func(self, *args, **kwargs):
                        yield item
                except Exception as e:  # pylint: disable=W0718
                    logger.error(f"{error_prefix}: {e}")
                    raise
            return sync_wrapper
        else:
            raise TypeError("stream_error_handler can only be used with generator functions")
    return decorator
