/**
 * Appends tool details to the DOM.
 * @param {Object} tool - The tool object containing details.
 */
function appendAgentToolDetails(tool) {
    // Show configuration & interface and restore detail width
    document.getElementById('toolConfigurationBox').style.display = 'block';

    const toolDetails = document.getElementById('toolDetails');
    let manifest = tool.settings.tool
    const descriptionDetails = `<h1>Description</h1><p style="margin-bottom: 1rem;">${manifest.description}</p>`;
    toolDetails.insertAdjacentHTML('beforeend', descriptionDetails);

    let argumentsDetails = '<h1>Arguments</h1><ul style="margin-bottom: 1rem; padding-left: 20px;">';
    manifest.arguments.forEach(argument => {
        argumentsDetails += `<li><b>${argument.name} (${argument.type}):</b> ${argument.description}</li>`;
    });
    argumentsDetails += '</ul>'
    toolDetails.insertAdjacentHTML('beforeend', argumentsDetails);
}

/**
 * Generates the settings form.
 * @param {Object} tool - The tool object containing settings.
 */
function generateAgentToolSettingsForm(tool) {
    generateAgentToolConfigurationForm(tool)
}

/**
 * Generates the configuration form.
 * @param {Object} tool - The tool object containing settings.
 */
function generateAgentToolConfigurationForm(tool) {
    let functionSettings = tool.settings.function
    let options = tool.options
    let settingsForm = ''
    settingsForm += generateLLMForm();
    settingsForm += generatePlanForm();
    settingsForm += generateTaskForm(functionSettings.multi_agents.tasks);
    document.getElementById('toolConfiguration').innerHTML = settingsForm;
    populateLLMOptions(options.llms, functionSettings.multi_agents.llm);
    populatePlanOptions(options.plan_types, functionSettings.multi_agents.plan_type);
}

/**
 * Generates the LLM form section.
 * @returns {string} The HTML for the LLM accordion.
 */
function generateLLMForm() {
    return `
        <div class="configurable-field" style="margin-bottom: 1rem;">
            <label for="llm_select">LLM</label>
            <select id="llm_select">
                <option>Placeholder</option>
            </select>
        </div>`;
}

/**
 * Generates the Plan form section.
 * @returns {string} The HTML for the Plan accordion.
 */
function generatePlanForm() {
    return `
        <div class="configurable-field" style="margin-bottom: 1rem;">
            <label for="plan_select">Planner Type</label>
            <select id="plan_select">
                <option>Placeholder</option>
            </select>
        </div>`;
}

/**
 * Generates the Task form section.
 * @returns {string} The HTML for the Task object.
 */
function generateTaskForm(taskSettings) {
    let TaskFields = '<div id="taskFieldsContainer">';

    Object.entries(taskSettings).forEach(([key, value]) => {
        TaskFields += createTaskField(key, value);
    });

    TaskFields += '</div>';

    return TaskFields
}

/** 
 * Helper function to create a single task 
 * @param {int} key - The task key
 * @returns {string} The HTML for the task
 */
function createTaskField(key, taskSettings) {
    return `
    <fieldset class="parameter-config" id="taskField_${key}">
        <legend>Task-${Number(key)+1}</legend>
        ${createTaskTextArea(key, "description", taskSettings.description)}
        ${createTaskTextArea(key, "expected_output", taskSettings.expected_output)}
        ${createTaskTextArea(key, "agent goal", taskSettings.agent.goal)}
        ${createTaskTextArea(key, "agent backstory", taskSettings.agent.backstory)}        
    </fieldset>`;
}

/** 
 * Helper function to create the task field
 * @param {int} key - The task key
 * @param {string} type - The type of field
 * @returns {string} The HTML for the label
 */ 
function createTaskTextArea(key, type, value) {
    return `
        <div class="configurable-field" style="margin-bottom: 0.5rem;">
            <label for="${type}_${key}">${type}</label>
            <textarea id="${type}_${key}" rows="4" readonly>${value}</textarea>
        </div>`
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
 * Populates the Plan options dropdown.
 * @param {Array} planOptions - Array of LLM option objects.
 */
function populatePlanOptions(planOptions, planSelected) {
    const planSelect = document.getElementById('plan_select');
    planSelect.innerHTML = planOptions.map(option => {
        const isSelected = option === planSelected ? 'selected' : '';
        return `<option value="${option}" ${isSelected}>${option}</option>`;
    }).join('');
}

/**
 * Collects settings from the form inputs.
 * @returns {Object} The settings object.
 */
function collectAgentToolSettings() {
    const settings = {};
    settings['llm'] = document.getElementById('llm_select').value;
    settings['plan_type'] = document.getElementById('plan_select').value;
    
    return settings;
}

/**
 * Apply the settings via a POST request.
 * @param {string} toolId - The ID of the selected tool.
 * @param {Object} settings - The settings object to save.
 */
function applyAgentToolSettings(toolId, settings) {
    fetch(`/tools/${toolId}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(response => {
        const spinner = document.getElementById('loading-spinner');
        alert(response.message);
        spinner.style.display = 'none';
    });
}

export {
    appendAgentToolDetails,
    generateAgentToolSettingsForm,
    collectAgentToolSettings,
    applyAgentToolSettings
};
