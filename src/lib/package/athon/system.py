#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module re-exports key functionalities related to System handling
within the src.lib. It simplifies the import for clients 
of the lib package.

The package name 'athon' is a shorthand for 'agentic-python', reflecting
its focus on building and managing agentic behaviors in Python-based systems.
"""

from src.lib.core.config import Config
from src.lib.core.log import Logger
from src.lib.system_services.tool_client import AthonTool
from src.lib.system_services.tool_server import ToolDiscovery


__all__ = [
    'Config',
    'Logger',
    'AthonTool',
    'ToolDiscovery'
]
