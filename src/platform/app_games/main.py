#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web Chat Application for games

This script serves as the main entry point for the HPE Games web application, 
integrating an interactive chat interface. 
The application utilizes Flask for web server capabilities,
rendering a chat interface, and handling user input. 
"""

from flask import Flask, render_template, request, jsonify
from src.lib.package.athon.system import Config, Logger
from src.lib.package.athon.chat import PromptRender
from src.platform.app_games.game import Game


# Supported Brands
BRANDS = ["athonet", "hpe"]
# Parse command-line arguments and start the application
PATH = 'src/platform/app_games/'
CONFIG = Config(PATH+'config.yaml').get_settings()
# Create Logger
logger = Logger().configure(CONFIG['logger']).get_logger()


def create_webapp(config):
    """
    Create the Flask application with its routes.
    """
    logger.debug("Create Flask Web App")
    app = Flask(__name__, template_folder = "./html/templates", static_folder = "./html/static")
    logger.debug("Configure Web App Routes")
    _configure_routes(app, config)
    return app

def _discover_games(config):
    games_list = []
    for game_config in config["games"]:
        game_object = Game().create(game_config)
        games_list.append(game_object)
    return games_list

def _configure_routes(app, config):
    """
    Configures the routes for the Flask application.
    """

    games = _discover_games(config)
    selected_game_id = [1]

    @app.route("/")
    def index():
        """
        Route to the index page.
        Clears the chat history and renders the chat interface.
        """
        logger.debug("Load Home page")
        _reset_games()
        session_variables = _get_session_variables(config["webapp"]["brand"])
        result = render_template('index.html', **session_variables)
        return result

    def _reset_games():
        for game in games:
            game.reset()

    def _get_session_variables(brand):
        if brand not in BRANDS:
            brand = "intelligen"
        session_variables = {}
        session_variables['theme'] = brand
        return session_variables

    @app.route("/message", methods=['POST'])
    def chat():
        """
        Route to handle chat requests.
        Accepts POST requests. Retrieves the user's message from the request,
        and passes it to the chat response generator.
        """
        try:
            data = request.get_json()  # Parse JSON data
            msg = data.get("msg")  # Get the 'msg' value from the JSON data
            logger.debug("Invoke Game agent")
            result = games[selected_game_id[0]-1].play(msg)
            if result.status == "failure":
                raise RuntimeError(result.error_message)
            return result.completion
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Catch Exception running Game")
            prompt = PromptRender.create(config["prompts"])
            result = prompt.load("chat_error_message", error = {str(e)})
            return result.content

    @app.route('/games', methods=['GET'])
    def get_games():
        """Endpoint to get a list of games."""
        game_list = []
        game_id = 1
        for game in config["games"]:
            game_list.append({
                "id": game_id,
                "name": game["name"]
            })
            game_id += 1
        return jsonify(game_list)

    @app.route('/games/<int:game_id>', methods=['GET'])
    def select_game(game_id):
        """Endpoint to select the project"""
        try:
            selected_game_id[0] = game_id
            game = config["games"][game_id-1]
            logger.debug(f"Game selected: {game['name']}")
            response = {
                "status": "success",
                "selected_game": game['name']
            }
            return jsonify(response)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Catch Exception selecting a Game: {e}")
            return jsonify({})

    @app.route('/games/<int:game_id>/settings', methods=['GET'])
    def get_game_settings(game_id):
        """Endpoint to get the settings for a specific tool."""
        logger.debug("Get Game settings")
        result = games[game_id-1].get_settings()
        if result.status == "success":
            return jsonify(_encode_settings(result.settings))
        return jsonify({})

    def _encode_settings(settings_dict):
        """
        Encode a settings dict into a new structure:
        - For string values, return a 'textarea' object.
        - For number values, return a 'number' object.
        - For dict with 'Options' and 'Selected', return a 'select' object.
        """
        encoded = []
        for field_name, value in settings_dict.items():
            # Handle dictionary with "Options" and "Selected" keys
            if isinstance(value, dict) and "Options" in value and "Selected" in value:
                options_encoded = []
                for option in value["Options"]:
                    # Convert each option into the requested format
                    options_encoded.append({
                        "value": option,
                        "text": option,
                        # Mark selected = True if it matches the "Selected" field
                        "selected": (option == value["Selected"])
                    })
                encoded.append({
                    "type": "select",
                    "label": field_name,
                    "name": field_name,
                    "options": options_encoded
                })
            # Handle strings
            elif isinstance(value, str):
                encoded.append({
                    "type": "textarea",
                    "label": field_name,
                    "name": field_name,
                    "rows": 3,
                    "value": value
                })
            # Handle numbers
            elif isinstance(value, (int, float)):
                encoded.append({
                    "type": "number",
                    "label": field_name,
                    "name": field_name,
                    "value": value
                })
            # If there's some other structure, decide how you want to handle it
            else:
                encoded.append({
                    "type": "input",
                    "label": field_name,
                    "name": field_name,
                    "value": value
                })
        return encoded

    @app.route('/games/<int:game_id>/settings', methods=['POST'])
    def set_game_settings(game_id):
        try:
            data = request.get_json()  # Parse JSON data
            settings = data.get("settings")  # Get the 'settings' value from the JSON data
            logger.debug("Configure Game agent")
            result = games[game_id-1].set_settings(settings)
            if result.status == "failure":
                raise RuntimeError(result.error_message)
            return "Game settings updated"
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Catch Exception configuring Game")
            prompt = PromptRender.create(config["prompts"])
            result = prompt.load("chat_error_message", error = {str(e)})
            return result.content


def main():
    """
    Main function that serves as the entry point for the application.
    It create the Flask web app with all its routes and run it.
    """
    logger.info('Starting the Web App...')
    chat_bot = create_webapp(CONFIG)
    # Assuming self.settings['webapp'] is a dictionary with configuration settings
    webapp_config = CONFIG.get('webapp') or {'ip': '127.0.0.1'}
    # Run App using settings web app params
    app_run_args = {
        'host': webapp_config.get('ip', '127.0.0.1')
    }
    if 'port' in webapp_config:
        app_run_args['port'] = webapp_config['port']
    if 'ssh_cert' in webapp_config:
        app_run_args['ssl_context'] = webapp_config['ssh_cert']
    chat_bot.run(**app_run_args)


if __name__ == "__main__":
     # Run web application.
    main()
