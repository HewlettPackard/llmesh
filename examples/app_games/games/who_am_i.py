#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
'Who am I?' class

This is the class related to the 'Who am I?' game
"""

import random
import string
from typing import Any
from langchain.tools import StructuredTool
from langchain.schema import SystemMessage, HumanMessage
from self_serve_platform.chat.prompt_render import PromptRender
from self_serve_platform.chat.model import ChatModel
from self_serve_platform.agents.tool_repository import ToolRepository
from self_serve_platform.agents.reasoning_engine import ReasoningEngine
from self_serve_platform.system.log import Logger
from examples.app_games.games.base import BaseGame


logger = Logger().get_logger()


class WhoAmI(BaseGame):
    """
    Class for 'Who Am I?' game.
    """

    _who = None
    _settings = {
        "Difficulty": {
            "Options": ["Easy", "Medium", "Hard"],
            "Selected": "Easy"
        },
        "Region": {
            "Options": ["All", "Europe", "Asia", "Africa", "Americas"],
            "Selected": "All"
        },
        "TimePeriod": {
            "Options": ["All", "Ancient", "Middle Ages", "Modern", "Futuristic"],
            "Selected": "All"
        },
        "Essence": {
            "Options": ["All", "Reality", "Literature", "Movies", "Comics"],
            "Selected": "All"
        },
        "Profession": {
            "Options": ["All", "Politics", "Music", "Science", "Sports"],
            "Selected": "All"
        },
        "Comment": ""
    }

    def __init__(self, config: dict) -> None:
        """
        Initialize the game with the given configuration.

        :param config: Configuration dictionary for the game.
        """
        self.config = WhoAmI.Config(**config)
        self.result = WhoAmI.Result()
        self._init_settings()
        self._init_tools()
        self.game = self._init_game()

    def _init_settings(self):
        """
        Initialize the selected settings.
        """
        self._settings["Difficulty"]["Selected"] = "Easy"
        self._settings["Region"]["Selected"] = "All"
        self._settings["TimePeriod"]["Selected"] = "All"
        self._settings["Essence"]["Selected"] = "All"
        self._settings["Profession"]["Selected"] = "All"
        self._settings["Comment"] = ""

    def _init_tools(self):
        """
        Initialize the tools inside the repository.
        """
        tool_repository = ToolRepository.create(self.config.chat["tools"])
        self._init_tool_rules(tool_repository)
        self._init_tool_secret_identity(tool_repository)
        self._init_tool_end_game(tool_repository)

    def _init_tool_rules(self, tool_repository):
        """
        Add the tool rules inside the repository.
        """
        tool_object = StructuredTool.from_function(
            name="WhoAmIRules",
            func=self._tool_get_rules,
            description="Uses this tool to get the rules of the game"
        )
        tool_metadata = {
            "id": 1,
            "game": "WhoAmI"
        }
        tool_repository.add_tool(tool_object, tool_metadata)

    def _init_tool_secret_identity(self, tool_repository):
        """
        Add the tool secret identity inside the repository.
        """
        tool_object = StructuredTool.from_function(
            name="WhoAmISecretIdentity",
            func=self._tool_handle_secret_identity,
            description="Uses this tool to get the secret identity"
        )
        tool_metadata = {
            "id": 2,
            "game": "WhoAmI"
        }
        tool_repository.add_tool(tool_object, tool_metadata)

    def _init_tool_end_game(self, tool_repository):
        """
        Add the tool end game inside the repository.
        """
        tool_object = StructuredTool.from_function(
            name="WhoAmIEndGame",
            func=self._tool_end_game,
            description="Uses this tool when user guesses the secret identity"
        )
        tool_metadata = {
            "id": 3,
            "game": "WhoAmI"
        }
        tool_repository.add_tool(tool_object, tool_metadata)

    def _tool_get_rules(self) -> str:
        """
        A tool that return the rules.
        """
        return self.config.chat["rules_prompt"]

    def _tool_end_game(self) -> str:
        """
        A tool that handle the end of a game
        """
        self._who = None
        result = self.game.clear_memory()
        self.result.status = result.status
        if result.status != "success":
            return result.error_message
        return "Congratulation you guess the secret identity."

    def _tool_handle_secret_identity(self) -> str:
        """
        A tool that handle the secret identity
        """
        if self._who is None:
            self._who = self._get_secret_identity()
        return self._who

    def _get_secret_identity(self):
        chat_model = ChatModel.create(self.config.chat["model"])
        messages = [
            SystemMessage(content = self.config.chat["secret_identity_prompt"]),
            HumanMessage(content = self._get_identity_prompt())
        ]
        llm = chat_model.get_model()
        result = llm.model.invoke(messages)
        return result.content

    def _get_identity_prompt(self):
        prompt_render = PromptRender.create({"type": "JinjaTemplate"})
        result = prompt_render.render(
            (
                "Game Settings:\n"
                "- Difficulty: {{ difficulty }}\n"
                "- First Letter: {{ first_letter }}"
                "- Region: {{ region }}\n"
                "- Time Period: {{ time_period }}\n"
                "- Essence: {{ essence }}\n"
                "- Profession: {{ profession }}\n"
                "- Comment: {{ comment }}\n"
            ),
            difficulty = self._settings["Difficulty"]["Selected"],
            first_letter = self._get_random_char(),
            region = self._settings["Region"]["Selected"],
            time_period = self._settings["TimePeriod"]["Selected"],
            essence = self._settings["Essence"]["Selected"],
            profession = self._settings["Profession"]["Selected"],
            comment = self._settings["Comment"]
        )
        return result.content

    def _get_random_char(self) -> str:
        """
        Get a random character from the English alphabet (a-z).
        
        :return: A single lowercase character.
        """
        char = random.choice(string.ascii_lowercase)
        logger.debug(f"First Char: {char}")
        return char

    def _init_game(self) -> Any:
        """
        Initialize and return the game instance.

        :return: Game instance.
        """
        logger.debug("Initializing game: 'Who am I?'")
        game = ReasoningEngine.create(self.config.chat)
        game.set_tools(["WhoAmIRules", "WhoAmISecretIdentity", "WhoAmIEndGame"])
        return game

    def play(self, message) -> 'WhoAmI.Result':
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

    def set_settings(self, settings) -> 'WhoAmI.Result':
        """
        Set the settings of the game.

        :param settings: Settings of the game.
        :return: Result object containing the status of the set operation.
        """
        try:
            self.result.status = "success"
            self._who = None
            self._settings["Difficulty"]["Selected"] = settings["Difficulty"]
            self._settings["Region"]["Selected"] = settings["Region"]
            self._settings["TimePeriod"]["Selected"] = settings["TimePeriod"]
            self._settings["Essence"]["Selected"] = settings["Essence"]
            self._settings["Profession"]["Selected"] = settings["Profession"]
            self._settings["Comment"] = settings["Comment"]
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while updating the settings: {e}"
            logger.error(self.result.error_message)
        return self.result

    def get_settings(self) -> 'WhoAmI.Result':
        """
        Get the settings of the game.

        :return: Result object containing the status of the get operation.
        """
        self.result.status = "success"
        self.result.settings = self._settings
        return self.result

    def reset(self) -> 'WhoAmI.Result':
        """
        Reset the game.

        :return: Result object containing the status of the clear operation.
        """
        self._who = None
        self._init_settings()
        result = self.game.clear_memory()
        self.result.status = result.status
        if result.status != "success":
            self.result.error_message = result.error_message
        return self.result
