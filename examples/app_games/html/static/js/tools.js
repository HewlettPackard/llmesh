/**
 * Populates the dropdown list with tools from the API.
 */
async function populateToolOptions() {
    try {
        const response = await fetch('/tools');
        if (!response.ok) {
            throw new Error('Failed to fetch tools');
        }

        const tools = await response.json();
        const selectElement = document.getElementById('toolSelection');
        const container = document.getElementById('toolFormFields');
        clearElement(selectElement);
        clearElement(container);

        if (tools.length === 0) {
            displayNoToolsAvailable(selectElement, container);
        } else {
            addToolOptions(selectElement, tools);
            updateFormFields(tools[0].id); // Automatically load fields for the first available tool
        }
    } catch (error) {
        console.error(error.message);
    }
}

/**
 * Displays a message when no tools are available.
 * @param {HTMLElement} selectElement - The dropdown select element.
 * @param {HTMLElement} container - The container element for form fields.
 */
function displayNoToolsAvailable(selectElement, container) {
    const noToolsOption = document.createElement('option');
    noToolsOption.textContent = "No tools available";
    selectElement.appendChild(noToolsOption);
    container.innerHTML = '<p>Close the modal, there are no tools available.</p>';
}

/**
 * Adds tool options to the dropdown list.
 * @param {HTMLElement} selectElement - The dropdown select element.
 * @param {Array} tools - List of tool objects to populate.
 */
function addToolOptions(selectElement, tools) {
    tools.forEach(tool => {
        const option = document.createElement('option');
        option.value = tool.id; // Assuming each tool has an 'id'
        option.textContent = tool.name; // Assuming each tool has a 'name'
        selectElement.appendChild(option);
    });
}

/**
 * Creates form fields based on the selected tool.
 * @param {string} toolId - The ID of the selected tool.
 */
async function updateFormFields(toolId) {
    try {
        const response = await fetch(`/tools/${toolId}/fields`);
        if (!response.ok) {
            throw new Error('Failed to fetch tool fields');
        }

        const fields = await response.json();
        const container = document.getElementById('toolFormFields');
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
 * Sends the tool data when the Send button is clicked.
 */
function sendToolData() {
    const toolSelection = document.getElementById('toolSelection');
    const selectedText = toolSelection.options[toolSelection.selectedIndex].text;
    const toolFormFields = document.querySelectorAll('#toolFormFields input, #toolFormFields select, #toolFormFields textarea');
    const parameters = {};

    toolFormFields.forEach(field => {
        parameters[field.name] = field.value;
    });

    submitUserMessage(`${selectedText}, run considering the data ${JSON.stringify(parameters)}`);
    $('#toolsModal').modal('hide'); // Close the modal
}

// Event listener for tool selection change
document.getElementById('toolSelection').addEventListener('change', function() {
    updateFormFields(this.value);
});

// Populate tools dropdown when the modal is shown
$('#toolsModal').on('shown.bs.modal', populateToolOptions);

import { submitUserMessage } from './chat.js';

// Initialize event listeners when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('sendButton').addEventListener('click', sendToolData);
});
