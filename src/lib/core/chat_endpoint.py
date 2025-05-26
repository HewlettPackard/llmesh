#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChatEndpoint Module

This module provides a class that handles OpenAI-compatible
chat completion requests, designed to be used within a FastAPI app.
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
from fastapi import HTTPException
from src.lib.core.log import Logger


logger = Logger().get_logger()


class Message(BaseModel):
    """
    Message model representing a single chat message.
    """
    role: Literal["system", "user", "assistant"]
    content: str

class MessageResponse(BaseModel):
    """
    Message model for assistant response.
    """
    role: str
    content: str

class ChatResponseChoice(BaseModel):
    """
    Single choice object for response, containing the assistant message.
    """
    index: int
    message: MessageResponse
    finish_reason: str = "stop"

class ChatStreamDelta(BaseModel):
    """
    Delta message for streaming chunk.
    """
    content: Optional[str] = None

class ChatStreamChoice(BaseModel):
    """
    Single choice in a stream chunk.
    """
    delta: ChatStreamDelta
    index: int = 0
    finish_reason: Optional[str] = None

class ModelInfo(BaseModel):
    """
    Model information.
    """
    id: str
    object: str = "model"
    owned_by: str = "local"

class ChatEndpoint:
    """
    A class used to handle OpenAI-compatible /v1/chat/completions endpoint logic.
    It validates incoming requests, logs unknown fields, and returns
    standard-compatible responses.
    """

    class Config(BaseModel):
        """
        Configuration model for ChatEndpoint settings.
        """
        endpoint_prefix: str = Field(
            default="/v1",
            description="Base path prefix for all API endpoints."
        )
        available_models: List[str] = Field(
            default_factory=lambda: ["gpt-4o"],
            description="List of model identifiers exposed by this endpoint."
        )

    class ChatRequest(BaseModel):
        """
        Request model for chat completion following OpenAI API schema.
        Accepts extra fields and logs them as warnings.
        """
        model: str
        messages: List[Message]
        temperature: Optional[float] = None
        top_p: Optional[float] = None
        n: Optional[int] = None
        stream: Optional[bool] = None
        stop: Optional[Any] = None
        max_tokens: Optional[int] = None
        presence_penalty: Optional[float] = None
        frequency_penalty: Optional[float] = None
        logit_bias: Optional[Dict[str, float]] = None
        user: Optional[str] = None
        model_config = ConfigDict(extra="allow")
        @model_validator(mode="before")
        @classmethod
        def warn_extra_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            """
            Warn if unexpected fields are present in the request.
            """
            known = cls.model_fields.keys()
            for key in values:
                if key not in known:
                    logger.warning("Unexpected field in request: %s=%s", key, values[key])
            return values

    class ChatResponse(BaseModel):
        """
        Full chat response model, following OpenAI response format.
        """
        id: str
        object: str = "chat.completion"
        created: int
        model: str
        choices: List[ChatResponseChoice]
        usage: Dict[str, int]

    class ModelsResponse(BaseModel):
        """
        Full models response, following OpenAI response format.
        """
        object: str = "list"
        data: List[ModelInfo]

    class ChatStreamChunk(BaseModel):
        """
        Streaming-compatible response chunk.
        """
        id: str
        object: str = "chat.completion.chunk"
        created: int
        model: str
        choices: List[ChatStreamChoice]

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the ChatEndpoint.

        :param config: Optional configuration dictionary.
        """
        self.config = ChatEndpoint.Config(**(config or {}))

    def validate_request(self, request: "ChatRequest") -> None:
        """
        Validate that required fields are present in the request.

        :param request: Parsed chat request model.
        :raises HTTPException: If required fields are missing.
        """
        if not request.model:
            raise HTTPException(status_code=400, detail="Missing 'model' in request.")
        if not request.messages:
            raise HTTPException(status_code=400, detail="Missing 'messages' in request.")
        logger.info("Validated request for model: %s", request.model)

    def build_response(
        self,
        request: ChatRequest,
        content: Optional[str] = None,
        message_index: int = 0,
        message_id: Optional[str] = None,
        created_at: Optional[int] = None
    ) -> ChatResponse:
        """
        Build a response compatible with OpenAI's chat completion format.

        :param request: The original chat request.
        :param content: The assistant's response content.
        :param message_index: The index of the choice in the list.
        :param message_id: Optional override for response ID.
        :param created_at: Optional override for created timestamp.
        :return: ChatResponse instance.
        """
        user_message = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            ""
        )
        assistant_reply = content or f"Echo: {user_message}"
        return ChatEndpoint.ChatResponse(
            id=message_id or f"chatcmpl-{uuid.uuid4().hex}",
            created=created_at or int(time.time()),
            model=request.model,
            choices=[
                ChatResponseChoice(
                    index=message_index,
                    message=MessageResponse(
                        role="assistant",
                        content=assistant_reply
                    )
                )
            ],
            usage={
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(assistant_reply.split()),
                "total_tokens": len(user_message.split()) + len(assistant_reply.split())
            }
        )

    def get_models(self) -> "ChatEndpoint.ModelsResponse":
        """
        Return a list of available models in OpenAI-compatible format.

        :return: ModelsResponse object
        """
        models = [
            ModelInfo(id=model_name)
            for model_name in self.config.available_models
        ]
        return ChatEndpoint.ModelsResponse(data=models)

    def build_stream_chunk(
        self,
        content: str,
        model: Optional[str] = None,
        index: int = 0,
        message_id: Optional[str] = None,
        created_at: Optional[int] = None,
        finish_reason: Optional[str] = None
    ) -> ChatStreamChunk:
        """
        Build a streaming-compatible response chunk using Pydantic model.

        :param content: The partial assistant message.
        :param model: Optional model name override.
        :param index: Index of the choice.
        :param message_id: Optional response ID.
        :param created_at: Optional timestamp.
        :param finish_reason: Optional reason for finish.
        :return: ChatStreamChunk model instance.
        """
        return ChatEndpoint.ChatStreamChunk(
            id=message_id or f"chatcmpl-{uuid.uuid4().hex}",
            object="chat.completion.chunk",
            created=created_at or int(time.time()),
            model=model or self.config.available_models[0],
            choices=[
                ChatStreamChoice(
                    delta=ChatStreamDelta(content=content),
                    index=index,
                    finish_reason=finish_reason
                )
            ]
        )
