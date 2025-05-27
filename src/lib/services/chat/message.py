#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chat Message Model (LAT-Mesh Compliant)

This module defines the internal ChatMessage class and block components
used across the LAT-Mesh architecture for abstracted LLM input/output handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """
    Enum for message roles.
    """
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class BlockType(str, Enum):
    """
    Enum for supported block types.
    """
    TEXT = "text"
    IMAGE = "image"
    FUNCTION_CALL = "function_call"


@dataclass
class TextBlock:
    """
    Block representing plain text.
    """
    type: BlockType = BlockType.TEXT
    text: str = ""


@dataclass
class ImageBlock:
    """
    Block representing an image.
    """
    type: BlockType = BlockType.IMAGE
    path: Optional[str] = None
    url: Optional[str] = None
    alt: Optional[str] = None


@dataclass
class FunctionCallBlock:
    """
    Block representing a function call request.
    """
    type: BlockType = BlockType.FUNCTION_CALL
    name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)


Block = Union[TextBlock, ImageBlock, FunctionCallBlock]


@dataclass
class ChatMessage:
    """
    Unified internal ChatMessage class for LAT-Mesh.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    role: MessageRole = MessageRole.USER
    blocks: List[Block] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_text(self) -> str:
        """
        Concatenate all text blocks into a single string.

        :return: Concatenated text.
        """
        return "\n".join(
            block.text for block in self.blocks if isinstance(block, TextBlock)
        )

    def get_function_call(self) -> Optional[FunctionCallBlock]:
        """
        Return the first function call block if available.

        :return: FunctionCallBlock or None.
        """
        for block in self.blocks:
            if isinstance(block, FunctionCallBlock):
                return block
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the message to a dictionary.

        :return: Dictionary representation of the message.
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "role": self.role.value,
            "blocks": [block.__dict__ for block in self.blocks],
            "metadata": self.metadata,
        }
