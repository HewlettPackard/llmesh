#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module re-exports key functionalities related to Chat handling
within the lib. It simplifies the import for clients 
of the lib package.

The package name 'athon' is a shorthand for 'agentic-python', reflecting
its focus on building and managing agentic behaviors in Python-based systems.
"""

from src.lib.services.chat.model import ChatModel
from src.lib.services.chat.memory import ChatMemory
from src.lib.services.chat.message_manager import MessageManager
from src.lib.services.chat.prompt_render import PromptRender


__all__ = [
    'ChatModel',
    'ChatMemory',
    'MessageManager',
    'PromptRender'
]
