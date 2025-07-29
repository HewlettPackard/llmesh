#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
'Fantasia Genesis' class

This is the class related to the 'Fantasia Genesis' game
"""

import sys
import copy
from typing import Any
from crewai.tools import BaseTool
from langchain_core.messages.utils import get_buffer_string
from langchain.schema import SystemMessage, HumanMessage
from athon.chat import ChatModel, ChatMemory, PromptRender
from athon.agents import TaskForce
from athon.rag import DataStorage
from athon.system import Config, Logger
from src.infra.app_games.games.base import BaseGame
# Import tool classes needed to resolve properly the config file
from src.infra.app_games.games.fantasia_genesis_tools import (  # pylint: disable=W0611
    SaveWorld,
    SaveHero,
    GetWorld,
    GetHero,
    GetRules,
    PlayLottery)


setup = {
    "tool": {
        "module": sys.modules[__name__],
        "base_class": BaseTool
    }
}
CONFIG = Config(
    'src//app_games/config.yaml',
    setup_parameters=setup
).get_settings()
MEMORY_CONFIG = CONFIG["games"][1]["chat"]["memory"]
MODEL_CONFIG = CONFIG["games"][1]["chat"]["setup"]["llm"]
PROMPT_CONFIG = CONFIG["prompts"]
SETUP_CONFIG = CONFIG["games"][1]["chat"]["setup"]
PLAY_CONFIG = CONFIG["games"][1]["chat"]["play"]
WORLD_STORAGE_CONFIG = CONFIG["games"][1]["chat"]["world_db"]
HERO_STORAGE_CONFIG = CONFIG["games"][1]["chat"]["hero_db"]
logger = Logger().get_logger()


class FantasiaGenesis(BaseGame):
    """
    Class for 'Fantasia Genesis' game.
    """

    _world = None
    _story= None
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
        self.memory = self._init_memory()
        self.setup = self._init_setup()
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

    def _init_memory(self) -> Any:
        """
        Initialize and return the game memory.

        :return: Game memory.
        """
        chat_memory = ChatMemory.create(MEMORY_CONFIG)
        result = chat_memory.get_memory()
        return result.memory

    def _init_setup(self) -> Any:
        """
        Initialize and return the game setup instance.

        :return: Game setup instance.
        """
        return TaskForce.create(SETUP_CONFIG)

    def _init_game(self) -> Any:
        """
        Initialize and return the game instance.

        :return: Game instance.
        """
        return TaskForce.create(PLAY_CONFIG)

    def play(self, message) -> 'FantasiaGenesis.Result':
        """
        Play the game.

        :param message: Message to be processed by the model.
        :return: Result object containing the status of the play operation.
        """
        try:
            self.result.status = "success"
            if self._world is None:
                self._create_world()
                self._situation = self._update_situation([], self._world)
            result = self._run_game(message)
            self.result.completion =  self._save_context(result, message)
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while playing the game: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _create_world(self):
        """
        Reset game and create a new world using Setup Task Force.
        """
        self.reset()
        settings = self._get_selected_settings()
        result = self.setup.run({"settings": settings})
        self._world = self.setup.crew.tasks[0].output.raw
        self._story = result.completion
        logger.debug(f"Fantasia created: {self._world}\n{self._story}")

    def _get_selected_settings(self) -> dict:
        """
        Get the selected settings.

        :return: Dict of settings
        """
        return {
            "Difficulty": self._settings["Difficulty"]["Selected"],
            "World": self._settings["World"]["Selected"],
            "World Description": self._settings["World Description"],
            "Skills": self._settings["Skills"]["Selected"],
            "Alignment": self._settings["Alignment"]["Selected"],
            "Player Background": self._settings["Player Background"]
        }

    def _get_messages(self, inputs):
        """
        Get the memory messages.

        :return: Messages
        """
        messages = self.memory.load_memory_variables(inputs)
        return get_buffer_string(messages["chat_history"])

    def _run_game(self, message):
        """
        Run the gam.

        :return: Crew Result
        """
        context = {
            "situation": self._situation,
            "message": message,
            "chat_history": self._get_messages({"input": message}),
            "difficulty": self._settings["Difficulty"]["Selected"]
        }
        return self.game.run({"context": context})

    def _save_context(self, result, message):
        """
        Save the new context after the run.

        :return: Crew completion
        """
        self._save_messages({"input": message}, {"output": result.completion})
        self._situation = self._update_situation(
            [
                f"input: {message}",
                f"output: {result.completion}"
            ],
            self._situation)
        return self._create_game_response(result.completion)

    def _save_messages(self, inputs, outputs):
        """
        Save the memory messages.
        """
        self.memory.save_context(inputs, outputs)

    def _update_situation(self, memories, situation):
        """
        Update the situation with LLM.
        """
        chat_model = ChatModel.create(MODEL_CONFIG)
        prompt_render = PromptRender.create(PROMPT_CONFIG)
        messages = [
            SystemMessage(content = prompt_render.load("fantasia_situation").content),
            HumanMessage(content = self._get_situation_prompt(prompt_render, memories, situation))
        ]
        llm = chat_model.get_model()
        result = llm.model.invoke(messages)
        return result.content

    def _get_situation_prompt(self, prompt_render, memories, situation):
        """
        Render the prompt
        """
        result = prompt_render.render(
            (
                "The messagges are:\n" 
                "{{ messages }}\n"
                "The current situation is:\n"
                "{{ situation }}" 
            ),
            messages = memories,
            situation = situation
        )
        return result.content

    def _create_game_response(self, completion):
        """
        Create the Game response with world and story info
        """
        return (
            f"{completion}"
            "<code>"
            f"SITUATION:\n{self._situation}\n\n"
            f"STORY:\n{self._story}\n\n"
            f"WORLD:\n{self._world}"
            "</code>"
        )

    def set_settings(self, settings) -> 'FantasiaGenesis.Result':
        """
        Set the settings of the game.

        :param settings: Settings of the game.
        :return: Result object containing the status of the set operation.
        """
        try:
            self.result.status = "success"
            self.reset()
            self._set_selected_settings(settings)
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while updating the settings: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _set_selected_settings(self, settings):
        """
        Set the selected settings.

        :param: Dict of settings
        """
        self._settings["Difficulty"]["Selected"] = settings["Difficulty"]
        self._settings["World"]["Selected"] = settings["World"]
        self._settings["World Description"] = settings["World Description"]
        self._settings["Skills"]["Selected"] = settings["Skills"]
        self._settings["Alignment"]["Selected"] = settings["Alignment"]
        self._settings["Player Background"] = settings["Player Background"]

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
        self.result.status = "success"
        self._world = None
        self._reset_collection(WORLD_STORAGE_CONFIG)
        self._reset_collection(HERO_STORAGE_CONFIG)
        return self.result

    def _reset_collection(self, storage_config):
        reset_config = copy.deepcopy(storage_config)
        reset_config["reset"] = True
        data_storage= DataStorage.create(reset_config)
        result = data_storage.get_collection()
        return result.status
