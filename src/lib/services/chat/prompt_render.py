#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prompt Module

This module defines the Prompt class and associated factory class for 
managing prompt rendering. 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from src.lib.services.chat.prompt_renders.jinja.template import (
    JinjaTemplatePromptRender)


class PromptRender:  # pylint: disable=R0903
    """
    A factory class to create Prompt Manager objects with the selected services.
    """

    _prompts: Dict[str, Type] = {
        'JinjaTemplate': JinjaTemplatePromptRender,
    }

    @staticmethod
    def create(config: dict) -> Any:
        """
        Create and return a Prompt object based on the provided configuration.

        :param config: Dictionary containing configurations for file_render and message_manager.
        :return: Prompt object
        """
        prompt_type = config.get('type')
        if not prompt_type:
            raise ValueError("Configuration must include 'type'.")
        prompt_class = PromptRender._prompts.get(prompt_type)
        if not prompt_class:
            raise ValueError(f"Unsupported prompt file render type: {prompt_type}")
        return prompt_class(config)
