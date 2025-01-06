#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Model

Placeholder class that has to be overwritten.
"""

import abc
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class BaseGame(abc.ABC):
    """
    Abstract base class for chat game.
    """

    class Config(BaseModel):
        """
        Configuration for the Game class.
        """
        type: str = Field(
            ...,
            description="Game type."
        )
        name: str = Field(
            ...,
            description="Game name to be show in the web app."
        )
        chat: Dict[str, Any] = Field(
            ...,
            description="Game chat settings."
        )

    class Result(BaseModel):
        """
        Result of the Game operation.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        completion: Optional[Any] = Field(
            default=None,
            description="Chat completion."
        )
        settings: Optional[Dict[str, Any]] = Field(
            default=None,
            description="Settings of the game."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )

    @abc.abstractmethod
    def play(self, message) -> 'BaseGame.Result':
        """
        Play the game.

        :param message: Message to be processed by the model.
        :return: Result object containing the status of the clear operation.
        """

    @abc.abstractmethod
    def set_settings(self, settings) -> 'BaseGame.Result':
        """
        Set the settings of the game.

        :param settings: Settings of the game.
        :return: Result object containing the status of the clear operation.
        """

    @abc.abstractmethod
    def get_settings(self) -> 'BaseGame.Result':
        """
        Get the settings of the game.

        :return: Result object containing the status of the clear operation.
        """

    @abc.abstractmethod
    def reset(self) -> 'BaseGame.Result':
        """
        Reset the game.

        :return: Result object containing the status of the clear operation.
        """
