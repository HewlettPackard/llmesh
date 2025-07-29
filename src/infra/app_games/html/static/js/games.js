/**
 * Populates the dropdown list with games from the API.
 */
async function populateGamesOptions() {
    try {
        const response = await fetch('/games');
        
        if (!response.ok) {
            throw new Error('Failed to fetch games');
        }
        
        const games = await response.json();
        const selectElement = document.getElementById('chatTypeDropdown');
        selectElement.innerHTML = ''; // Clear existing options

        if (games.length === 0) {
            displayNoGamesAvailable(selectElement);
        } else {
            addGameOptions(selectElement, games);
        }
    } catch (error) {
        console.error(error.message);
    }
}

/**
 * Displays a message when no games are available.
 * @param {HTMLElement} selectElement - The dropdown select element.
 */
function displayNoGamesAvailable(selectElement) {
    const noGamesOption = document.createElement('option');
    noGamesOption.textContent = "No games available";
    selectElement.appendChild(noGamesOption);
}

/**
 * Adds game options to the dropdown list.
 * @param {HTMLElement} selectElement - The dropdown select element.
 * @param {Array} games - List of game objects to populate.
 */
function addGameOptions(selectElement, games) {
    games.forEach(game => {
        const option = document.createElement('option');
        option.value = game.id; // Assuming each game has an 'id'
        option.textContent = game.name; // Assuming each game has a 'name'
        selectElement.appendChild(option);
    });
}

/**
 * Handles game selection change.
 * @param {string} gameId - The ID of the selected game.
 */
async function onGameChange(gameId) {
    try {
        const response = await fetch(`/games/${gameId}`);
        
        if (!response.ok) {
            throw new Error('Failed to select game');
        }
        
        const gameData = await response.json();
        console.log('Game selected:', gameData);
        showGameChat(gameId); // Show the selected game's chat
    } catch (error) {
        console.error(error.message);
    }
}

import { scrollToBottom } from './chat.js';

/**
 * Shows only the selected game's chat and hides others.
 * @param {string} gameId - The ID of the selected game.
 */
function showGameChat(gameId) {
    const gameChatDivs = document.getElementsByClassName('game-chat');
    Array.from(gameChatDivs).forEach(div => {
        div.style.display = div.id === `messageFormeight-${gameId}` ? 'block' : 'none';
    });
    scrollToBottom(); // Ensure the chat is scrolled to the bottom when switching games
}

/**
 * Initializes the event listeners and populates game options when the document is ready.
 */
function initialize() {
    populateGamesOptions();
    document.getElementById('chatTypeDropdown').addEventListener('change', function() {
        const selectedGameId = this.value;
        onGameChange(selectedGameId);
    });
}

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', initialize);
