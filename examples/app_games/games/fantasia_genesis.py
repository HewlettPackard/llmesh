#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
'Fantasia Genesis' class

This is the class related to the 'Fantasia Genesis' game
"""

import sys
from typing import Any
from crewai.tools import BaseTool
from self_serve_platform.agents.task_force import TaskForce
from self_serve_platform.system.config import Config
from self_serve_platform.system.log import Logger
from examples.app_games.games.base import BaseGame
# Import tool classes needed to resolve properly the config file
from examples.app_games.games.fantasia_genesis_tools import (  # pylint: disable=W0611
    SaveWorld,
    SaveHero,
    GetWorld,
    GetHero,
    GetRules)


setup = {
    "tool": {
        "module": sys.modules[__name__],
        "base_class": BaseTool
    }
}
CONFIG = Config(
    'examples/app_games/config.yaml',
    setup_parameters=setup
).get_settings()
SETUP_CONFIG = CONFIG["games"][1]["chat"]["setup"]
logger = Logger().get_logger()


class FantasiaGenesis(BaseGame):
    """
    Class for 'Fantasia Genesis' game.
    """

    _world = None
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
        self.setup = self._init_setup()
        #TODO: check if world exist and initialize variable

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

    def _init_setup(self) -> Any:
        """
        Initialize and return the game setup instance.

        :return: Game setup instance.
        """
        return TaskForce.create(SETUP_CONFIG)

    def play(self, message) -> 'FantasiaGenesis.Result':
        """
        Play the game.

        :param message: Message to be processed by the model.
        :return: Result object containing the status of the play operation.
        """
        if self._world is None:
            settings = self._get_selected_settings()
            result = self.setup.run({"settings": settings})
            logger.debug(f"Fantasia created: {result.completion}")
        # TODO: play task force
        return "Pippo"

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

    def set_settings(self, settings) -> 'FantasiaGenesis.Result':
        """
        Set the settings of the game.

        :param settings: Settings of the game.
        :return: Result object containing the status of the set operation.
        """
        try:
            self.result.status = "success"
            self._world = None
            self._set_selected_settings(settings)
            #TODO: prompt engineering
            result = self.setup.run({"settings": settings})
            logger.debug(f"Fantasia created: {result.completion}")
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
        # TODO: add code
        logger.error("work in progress")
        return None
