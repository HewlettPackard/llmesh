#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Game Factory Class

This module defines the Game class and associated class for 
managing different LLM game. 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from examples.app_games.games.who_am_i import (
    WhoAmI)
from examples.app_games.games.fantasia_genesis import (
    FantasiaGenesis)


class Game:  # pylint: disable=R0903
    """
    A game class that uses a factory pattern to return
    the selected ones
    """

    _games: Dict[str, Type] = {
        'WhoAmI': WhoAmI,
        'FantasiaGenesis': FantasiaGenesis,
    }

    @staticmethod
    def create(config: Dict[str, Any]) -> object:
        """
        Return the game class.

        :param config: Configuration dictionary containing the type of game.
        :return: An instance of the selected game.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        game_type = config.get('type')
        if not game_type:
            raise ValueError("Configuration must include 'type'.")
        game_class = Game._games.get(game_type)
        if not game_class:
            raise ValueError(f"Unsupported extractor type: {game_type}")
        return game_class(config)
