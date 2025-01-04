#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
'Fantasia Genesis' class

This is the class related to the 'Fantasia Genesis' game
"""

import random
import string
from typing import Any
from langchain.tools import StructuredTool
from langchain.schema import SystemMessage, HumanMessage
from self_serve_platform.chat.prompt_render import PromptRender
from self_serve_platform.chat.model import ChatModel
from self_serve_platform.agents.tool_repository import ToolRepository
from self_serve_platform.agents.task_force import TaskForce
from self_serve_platform.system.log import Logger
from examples.app_games.games.base import BaseGame


logger = Logger().get_logger()


class FantasiaGenesis(BaseGame):
    """
    Class for 'Fantasia Genesis' game.
    """

    _world = None
    _player = None
    _story = None
    _situation = None
    _settings = {
        "Difficulty": {
            "Options": ["Easy", "Medium", "Hard"],
            "Selected": "Easy"
        },
        "World": {
            "Options": ["Fantasy", "Futuristic", "Nautical", "Post-Apocalyptic", "Steampunk"],
            "Selected": "Fantasy"
        },
        "World Description": "",
        "Skills": {
            "Options": ["Swordsmanship", "Magic", "Stealth", "Marksmanship", "Alchemy"],
            "Selected": "Swordsmanship"
        },
        "Alignment": {
            "Options": ["Lawful Good", "Neutral Good", "Chaotic Neutral", "Chaotic Evil"],
            "Selected": "Chaotic Neutral"
        },
        "Player Background": ""
    }

    def __init__(self, config: dict) -> None:
        """
        Initialize the game with the given configuration.

        :param config: Configuration dictionary for the game.
        """
        self.config = FantasiaGenesis.Config(**config)
        self.result = FantasiaGenesis.Result()
        self._init_settings()
        self._init_tools()
        self.game = self._init_game()

    def _init_settings(self):
        """
        Initialize the selected settings.
        """
        self._settings["Difficulty"]["Selected"] = "Easy"
        self._settings["World"]["Selected"] = "Fantasy"
        self._settings["World Description"] = ""
        self._settings["Skills"]["Selected"] = "Swordsmanship"
        self._settings["Alignment"]["Selected"] = "Chaotic Neutral"
        self._settings["Player Background"] = ""

    def _init_tools(self):
        """
        Initialize the tools inside the repository.
        """
        tool_repository = ToolRepository.create(self.config.chat["tools"])
        self._init_tool_rules(tool_repository)

    def _init_tool_rules(self, tool_repository):
        """
        Add the tool rules inside the repository.
        """
        tool_object = StructuredTool.from_function(
            name="FantasiaGenesisRules",
            func=self._tool_get_rules,
            description="Uses this tool to get the rules of the game"
        )
        tool_metadata = {
            "id": 1,
            "game": "FantasiaGenesis"
        }
        tool_repository.add_tool(tool_object, tool_metadata)

    def _tool_get_rules(self) -> str:
        """
        A tool that return the rules.
        """
        return self.config.chat["rules_prompt"]

    def _init_game(self) -> Any:
        """
        Initialize and return the game instance.

        :return: Game instance.
        """
        # TODO: add code
        logger.error("work in progress")
        return None

    def play(self, message) -> 'FantasiaGenesis.Result':
        """
        Play the game.

        :param message: Message to be processed by the model.
        :return: Result object containing the status of the play operation.
        """
        result = self.game.run(message)
        self.result.status = result.status
        if result.status == "success":
            self.result.completion = result.completion
        else:
            self.result.error_message = result.error_message
        return self.result

    def set_settings(self, settings) -> 'FantasiaGenesis.Result':
        """
        Set the settings of the game.

        :param settings: Settings of the game.
        :return: Result object containing the status of the set operation.
        """
        try:
            self.result.status = "success"
            self._world = None
            self._player = None
            self._story = None
            self._situation = None
            self._settings["Difficulty"]["Selected"] = settings["Difficulty"]
            self._settings["World"]["Selected"] = settings["World"]
            self._settings["World Description"] = settings["World Description"]
            self._settings["Skills"]["Selected"] = settings["Skills"]
            self._settings["Alignment"]["Selected"] = settings["Alignment"]
            self._settings["Player Background"] = settings["Player Background"]
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while updating the settings: {e}"
            logger.error(self.result.error_message)
        return self.result

    def get_settings(self) -> 'FantasiaGenesis.Result':
        """
        Get the settings of the game.

        :return: Result object containing the status of the get operation.
        """
        self.result.status = "success"
        self.result.settings = self._settings
        return self.result

    def reset(self) -> 'FantasiaGenesis.Result':
        """
        Reset the game.

        :return: Result object containing the status of the clear operation.
        """
        # TODO: add code
        logger.error("work in progress")
        return None
