/**
 * Appends tool details to the DOM.
 * @param {Object} tool - The tool object containing details.
 */
function appendPromptToolDetails(tool) {
    const toolDetails = document.getElementById('toolDetails');
    let manifest = tool.settings.tool
    const descriptionDetails = `<h5>Description:</h5><p>${manifest.description}</p>`;
    toolDetails.insertAdjacentHTML('beforeend', descriptionDetails);

    let argumentsDetails = '<h5>Arguments:</h5>';
    manifest.arguments.forEach(argument => {
        argumentsDetails += `<p>&#x2022; ${argument.description}</p>`;
    });
    toolDetails.insertAdjacentHTML('beforeend', argumentsDetails);

    const interfaceDetails = '<h5>Settings:</h5>';
    toolDetails.insertAdjacentHTML('beforeend', interfaceDetails);
}

/**
 * Generates the settings form.
 * @param {Object} tool - The tool object containing settings.
 */
function generatePromptToolSettingsForm(tool) {
    let settingsForm = '<div id="InterfacesAccordion" class="accordion">';
    let manifest = tool.settings.tool
    settingsForm += generateSystemPromptAccordion();
    settingsForm += generateLLMAccordion();
    settingsForm += generateInterfaceFields(manifest);
    settingsForm += '</div>';
    document.getElementById('toolSettings').innerHTML = settingsForm;
    bindLlmEvents();
    bindAddRemoveEvents();
    attachTypeChangeHandlers(manifest);
    let functionSettings = tool.settings.function
    populateSystemPrompt(functionSettings.system_prompt);
    let options = tool.options
    populateLLMOptions(options.llms, functionSettings.llm);
}

/**
 * Generates the System Prompt accordion section.
 * @returns {string} The HTML for the System Prompt accordion.
 */
function generateSystemPromptAccordion() {
    return `
        <div>
            <div id="headingSystemPrompt">
                <h5 class="mb-0">
                    <button type="button" class="btn btn-primary accordion-button" data-toggle="collapse" data-target="#collapseSystemPrompt" aria-expanded="true" aria-controls="collapseSystemPrompt">
                        System Prompt
                    </button>
                </h5>
            </div>
            <div id="collapseSystemPrompt" class="collapse" aria-labelledby="headingSystemPrompt" data-parent="#InterfacesAccordion">
                <div>
                    <textarea class="form-control" id="system_prompt_textarea" rows="6"></textarea>
                </div>
                <button type="button" class="btn btn-secondary llm-button" id="llmButton" style="margin: 10px 0px;">
                    Improve with LLM
                </button>
            </div>
        </div>`;
}

/**
 * Function to bind events for LLM button
 */ 
function bindLlmEvents() {
    // Bind LLM button
    const llmButton = document.getElementById('llmButton');
    const systemPromptTextarea = document.getElementById('system_prompt_textarea');

    if (llmButton && systemPromptTextarea) {
        llmButton.onclick = async function () {
            // Get the text from the textarea
            const promptText = systemPromptTextarea.value;

            // Define the tool ID and endpoint
            const toolId = document.getElementById('toolSelection').value; // Get toolId from the selected option
            const url = `/tools/${toolId}/prompt`;

            // Start spinner
            const spinner = document.getElementById('loading-spinner');
        
            if (spinner) {
                spinner.style.display = 'flex';
            }

            // Send a POST request with the prompt text
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ prompt: promptText })
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log("Response from LLM:", data);                    
                    // Update the system prompt textarea with the improved prompt from the response
                    if (data) {
                        systemPromptTextarea.value = data;
                    } else {
                        console.warn("Improved prompt not found in response.");
                    }
                } else {
                    console.error("Error in LLM request:", response.statusText);
                    alert("Failed to improve prompt. Please try again.");
                }
            } catch (error) {
                console.error("Request error:", error);
                alert("An error occurred while improving the prompt. Please check your connection and try again.");
            } finally {
                // Hide the spinner after the request is complete (success or error)
                spinner.style.display = 'none';
            }
        };
    } else {
        console.warn("LLM button or system prompt textarea not found.");
    }
}

/**
 * Generates the LLM accordion section.
 * @returns {string} The HTML for the LLM accordion.
 */
function generateLLMAccordion() {
    return `
        <div>
            <div id="headingLLM">
                <h5 class="mb-0">
                    <button type="button" class="btn btn-primary accordion-button" data-toggle="collapse" data-target="#collapseLLM" aria-expanded="true" aria-controls="collapseLLM">
                        LLM
                    </button>
                </h5>
            </div>
            <div id="collapseLLM" class="collapse" aria-labelledby="headingLLM" data-parent="#InterfacesAccordion">
                <div>
                    <select class="form-control" id="llm_select">
                        <option value="placeholder1">Placeholder</option>
                    </select>
                </div>
            </div>
        </div>`;
}

/**
 * Generates interface fields for the settings form.
 * @param {Object} toolConfig - The tool configuration object.
 * @returns {string} The HTML for the interface fields.
 */
function generateInterfaceFields(toolConfig) {
    let interfaceFields = '';

    Object.entries(toolConfig.interface.fields).forEach(([key, value]) => {
        interfaceFields += createInterfaceField(key, value.name, value.label, value.type);
    });

    interfaceFields += createAddButton();

    return interfaceFields
}

/** 
 * Helper function to create a single interface field
 * @param {int} key - The interface key
 * @param {string} name - The name of interface
 * @param {string} label - The label of interface
 * @param {string} type - The type of interface
 * @returns {string} The HTML for the interface
 */
function createInterfaceField(key, name = "new_name", label = 'New Field Label', type = 'input') {
    return `
        <div id="interfaceField_${key}">
            <div id="heading${key}">
                <h5 class="mb-0">
                    <button type="button" class="btn btn-primary accordion-button" data-toggle="collapse" data-target="#collapse${key}" aria-expanded="true" aria-controls="collapse${key}">
                        Interface Field ${Number(key)+1}
                    </button>
                </h5>
            </div>
            <div id="collapse${key}" class="collapse" aria-labelledby="heading${key}" data-parent="#InterfacesAccordion">
                <div>
                    ${createNameInput(key, name)}
                    ${createLabelInput(key, label)}
                    ${createTypeSelect(key, type)}
                    <div class="form-group field_${key}_additional" style="margin: 0;"></div>
                    <button type="button" class="btn btn-secondary remove-interface-button" data-key="${key}">
                        Remove Interface Field ${Number(key)+1}
                    </button>
                </div>
            </div>
        </div>`;
}

/** 
 * Helper function to create the name input field
 * @param {int} key - The interface key
 * @param {string} name - The name of interface
 * @returns {string} The HTML for the label
 */ 
function createNameInput(key, name) {
    return `
        <div class="form-row">
            <div class="form-group col-md-9">
                <input type="text" class="form-control" id="${key}_name" value="${name}">
            </div>
            <div class="form-group col-md-3">
                <name for="${key}_name">Name</name>
            </div>
        </div>`;
}

/** 
 * Helper function to create the label input field
 * @param {int} key - The interface key
 * @param {string} label - The label of interface
 * @returns {string} The HTML for the label
 */ 
function createLabelInput(key, label) {
    return `
        <div class="form-row">
            <div class="form-group col-md-9">
                <input type="text" class="form-control" id="${key}_label" value="${label}">
            </div>
            <div class="form-group col-md-3">
                <label for="${key}_label">Label</label>
            </div>
        </div>`;
}

/** 
 * Helper function to create the type select dropdown
 * @param {int} key - The interface key
 * @param {string} selectedType - The type of interface
 * @returns {string} The HTML for the Type selection
 */ 
function createTypeSelect(key, selectedType) {
    const options = ['input', 'select', 'textarea'].map(type =>
        `<option value="${type}"${selectedType === type ? ' selected' : ''}>${capitalize(type)}</option>`
    ).join('');
    
    return `
        <div class="form-row">
            <div class="form-group col-md-9">
                <select class="form-control" id="${key}_type">
                    ${options}
                </select>
            </div>
            <div class="form-group col-md-3">
                <label for="${key}_type">Type</label>
            </div>
        </div>`;
}

/** 
 * Function to capitalize the first letter of a word
 * @param {string} word - The word to modify
 * @returns {string} The word modified
 */
function capitalize(word) {
    return word.charAt(0).toUpperCase() + word.slice(1);
}

/** 
 * Function to create the "Add New Interface Field" button
 * @returns {string} The HTML for the Add button.
 */
function createAddButton() {
    return `
            <button type="button" class="btn btn-primary" id="addInterfaceButton" style="margin: 15px 0px 10px 0px;">
                Add New Interface Field
            </button>
        `;
}

/** 
 * Function to remove an interface field by key
 */
function removeInterfaceField(key) {
    const fieldElement = document.getElementById(`interfaceField_${key}`);
    if (fieldElement) {
        fieldElement.remove();
    }
}

/**
 * Function to add a new interface field with default input type
 */
function addInterfaceField() {
    // Determine the maximum field number currently in use
    const interfaceFields = document.querySelectorAll('#InterfacesAccordion > div[id^="interfaceField_"]');
    let newCounter = 0;

    // Check if interfaceFields is empty
    if (interfaceFields.length === 0) {
        // If no fields exist, start the counter at 1
        newCounter = 0;
    } else {
        // If fields exist, find the max counter and increment it
        let maxCounter = 0;
        interfaceFields.forEach(field => {
            // Extract the number from the field's ID (e.g., "interfaceField_3" -> 3)
            const fieldNum = parseInt(field.id.replace('interfaceField_', ''), 10);
            if (fieldNum > maxCounter) {
                maxCounter = fieldNum;
            }
        });
        newCounter = maxCounter + 1;
    }

    const key = `${newCounter}`;
    const newField = createInterfaceField(key);

    // Find the "Add New Interface Field" button
    const addButton = document.getElementById('addInterfaceButton');
    if (addButton) {
        // Insert the new field before the "Add New Interface Field" button
        addButton.insertAdjacentHTML('beforebegin', newField);
    }

    // Re-bind events for dynamically added elements
    bindAddRemoveEvents();
    attachTypeChangeHandlers({});
}

/**
 * Function to bind events for add and remove buttons
 */ 
function bindAddRemoveEvents() {
    // Bind add button
    const addButton = document.getElementById('addInterfaceButton');
    if (addButton) {
        addButton.onclick = addInterfaceField;
    }

    // Bind remove buttons
    document.querySelectorAll('.remove-interface-button').forEach(button => {
        button.onclick = function () {
            removeInterfaceField(button.dataset.key);
        };
    });
}

/**
 * Populates the system prompt textarea.
 * @param {string} systemPrompt - The system prompt text.
 */
function populateSystemPrompt(systemPrompt) {
    document.getElementById('system_prompt_textarea').value = systemPrompt;
}

/**
 * Populates the LLM options dropdown.
 * @param {Array} llmOptions - Array of LLM option objects.
 */
function populateLLMOptions(llmOptions, llmSelected) {
    const llmSelect = document.getElementById('llm_select');
    llmSelect.innerHTML = llmOptions.map(option => {
        const isSelected = option.settings.type === llmSelected.type ? 'selected' : '';
        return `<option value="${option.label}" ${isSelected}>${option.label}</option>`;
    }).join('');
}

/**
 * Handles additional fields based on the type selected.
 * @param {string} key - The key identifier for the field.
 * @param {string} type - The type of the field.
 * @param {Object} value - The value object containing field details.
 */
function handleAdditionalFields(key, type, value) {
    let additionalFields = '';
    if (type === 'select') {
        additionalFields += `
            <div class="form-row">
                <div class="form-group col-md-9">
                    <input type="text" class="form-control" id="${key}_options" value="${value.options || ''}">
                </div>
                <div class="form-group col-md-3">
                    <label for="${key}_options">Options</label>
                </div>
            </div>
            <small>Use ; to separate options. E.g., Option1;Option2;Option3</small>`;
    } else if (type === 'textarea') {
        additionalFields += `
            <div class="form-row">
                <div class="form-group col-md-9">
                    <input type="number" class="form-control" id="${key}_rows" value="${value.rows || 3}">
                </div>
                <div class="form-group col-md-3">
                    <label for="${key}_rows">Rows</label>
                </div>
            </div>`;
    }
    document.querySelector(`.field_${key}_additional`).innerHTML = additionalFields;
}

/**
 * Attaches change event handlers to the type dropdowns.
 * @param {Object} toolConfig - The tool configuration object.
 */
function attachTypeChangeHandlers(toolConfig) {
    // Select all elements with the ID pattern *_type
    const typeElements = document.querySelectorAll('[id$="_type"]'); // Matches all elements ending with "_type"
    
    typeElements.forEach(typeElement => {
        const key = typeElement.id.replace('_type', ''); // Extract the key from the ID
        const value = toolConfig.interface?.fields?.[key] || {}; // Use config value if it exists, or default to an empty object


        // Attach change event listener if not already attached
        if (!typeElement.hasAttribute('data-handler-attached')) {
            typeElement.addEventListener('change', function() {
                handleAdditionalFields(key, this.value, value);
            });
            // Mark this element as having the event handler attached
            typeElement.setAttribute('data-handler-attached', 'true');
        }

        // Initial call to set up additional fields based on current type
        handleAdditionalFields(key, typeElement.value, value);
    });
}

/**
 * Collects settings from the form inputs.
 * @returns {Object} The settings object.
 */
function collectPromptToolSettings() {
    const settings = {};
    settings['llm'] = document.getElementById('llm_select').value;
    settings['system_prompt'] = document.getElementById('system_prompt_textarea').value;
    settings['fields'] = [];

    const fieldElements = document.querySelectorAll('[id$="_label"]');
    fieldElements.forEach(labelElement => {
        const key = labelElement.id.replace('_label', '');
        const nameElement = document.getElementById(`${key}_name`);
        const typeElement = document.getElementById(`${key}_type`);
        const field = {
            name: nameElement.value,
            label: labelElement.value,
            type: typeElement.value
        };

        const rowsElement = document.getElementById(`${key}_rows`);
        if (rowsElement) field.rows = rowsElement.value;

        const optionsElement = document.getElementById(`${key}_options`);
        if (optionsElement) field.options = optionsElement.value;

        settings['fields'].push(field);
    });

    return settings;
}

/**
 * Apply the settings via a POST request.
 * @param {string} toolId - The ID of the selected tool.
 * @param {Object} settings - The settings object to save.
 */
function applyPromptToolSettings(toolId, settings) {
    fetch(`/tools/${toolId}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(response => {
        alert(response.message);
    });
}

export {
    appendPromptToolDetails,
    generatePromptToolSettingsForm,
    collectPromptToolSettings,
    applyPromptToolSettings
};
