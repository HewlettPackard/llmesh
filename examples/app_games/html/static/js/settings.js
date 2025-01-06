/**
 * Populates the dropdown list with settings from the API.
 */
async function populateSettingOptions() {
    try {
        const response = await fetch('/games');
        if (!response.ok) {
            throw new Error('Failed to fetch settings');
        }

        const games = await response.json();
        const selectElement = document.getElementById('gameSelection');
        const container = document.getElementById('gameFormSettings');
        clearElement(selectElement);
        clearElement(container);

        if (games.length === 0) {
            displayNoSettingsAvailable(selectElement, container);
        } else {
            const gameId = addSelectedGame(selectElement, games);
            updateFormFields(gameId); // Automatically load settings for the first available setting
        }
    } catch (error) {
        console.error(error.message);
    }
}

/**
 * Displays a message when no settings are available.
 * @param {HTMLElement} selectElement - The dropdown select element.
 * @param {HTMLElement} container - The container element for form fields.
 */
function displayNoSettingsAvailable(selectElement, container) {
    const noSettingsOption = document.createElement('option');
    noSettingsOption.textContent = "No settings available";
    selectElement.appendChild(noSettingsOption);
    container.innerHTML = '<p>Close the modal, there are no settings available.</p>';
}

/**
 * Adds selected game option to the dropdown list.
 * @param {HTMLElement} selectElement - The dropdown select element.
 * @param {Array} games - List of setting objects to populate.
 */
function addSelectedGame(selectElement, games) {
    const chatTypeDropdown = document.getElementById('chatTypeDropdown');
    const selectedValue = chatTypeDropdown.value;
    const game = games.find(g => g.id.toString() === selectedValue);
    if (game) {
        const option = document.createElement('option');
        option.value = game.id;
        option.textContent = game.name;
        selectElement.appendChild(option);
    }
    return game.id
}

/**
 * Creates form fields based on the selected setting.
 * @param {string} gameId - The ID of the selected setting.
 */
async function updateFormFields(gameId) {
    try {
        const response = await fetch(`/games/${gameId}/settings`);
        if (!response.ok) {
            throw new Error('Failed to fetch setting fields');
        }

        const fields = await response.json();
        const container = document.getElementById('gameFormSettings');
        clearElement(container);

        if (fields) {
            fields.forEach(field => createFormField(container, field));
        }
    } catch (error) {
        console.error(error.message);
    }
}

/**
 * Clears the content of an HTML element.
 * @param {HTMLElement} element - The element to clear.
 */
function clearElement(element) {
    element.innerHTML = '';
}

/**
 * Creates and appends a form field to the container based on the field data.
 * @param {HTMLElement} container - The container element to append the field to.
 * @param {Object} field - The field data.
 */
function createFormField(container, field) {
    // Create and append the label element
    const label = document.createElement('label');
    label.textContent = field.label;
    container.appendChild(label);

    let formElement;
    switch (field.type) {
        case 'textarea':
            formElement = document.createElement('textarea');
            formElement.rows = field.rows || 4;
            formElement.value = field.value || '';
            break;
        case 'select':
            formElement = document.createElement('select');
            field.options.forEach(optionData => {
                const option = document.createElement('option');
                option.value = optionData.value;
                option.textContent = optionData.text;
                if (optionData.selected) {
                    option.selected = true;
                }
                formElement.appendChild(option);
            });
            break;
        default:
            formElement = document.createElement('input');
            formElement.type = field.type;
            break;
    }

    formElement.name = field.name;
    formElement.classList.add('form-control');
    container.appendChild(formElement);
}

/**
 * Sends the setting data when the Send button is clicked.
 */
function sendSettingData() {
    const gameSelection = document.getElementById('gameSelection');
    const gameId = gameSelection.value;
    const gameFormSettings = document.querySelectorAll('#gameFormSettings input, #gameFormSettings select, #gameFormSettings textarea, #gameFormSettings number');
    const parameters = {};

    gameFormSettings.forEach(field => {
        parameters[field.name] = field.value;
    });

    // POST the data to /games/<gameId>/settings
    fetch(`/games/${gameId}/settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ settings: parameters })
    }).then(response => {
        if (!response.ok) {
            throw new Error(`Error: ${response.status} - ${response.statusText}`);
        }
        return response.json();
    }).catch(error => {
        console.error('Error:', error);
    });

    $('#settingsModal').modal('hide'); // Close the modal
}

// Event listener for setting selection change
document.getElementById('gameSelection').addEventListener('change', function() {
    updateFormFields(this.value);
});

// Populate settings dropdown when the modal is shown
$('#settingsModal').on('shown.bs.modal', populateSettingOptions);

import { submitUserMessage } from './chat.js';

// Initialize event listeners when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('sendButton').addEventListener('click', sendSettingData);
});
