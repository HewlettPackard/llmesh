/**
 * Appends tool details to the DOM.
 * @param {Object} tool - The tool object containing details.
 */
function appendRagToolDetails(tool) {
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
function generateRagToolSettingsForm(tool) {
    generateInjectionToolConfigurationForm(tool)
    generateRetrievalToolConfigurationForm(tool)
}

/**
 * Generates the configuration injection form.
 * @param {Object} tool - The tool object containing settings.
 */
function generateInjectionToolConfigurationForm(tool) {
    let settingsForm = `
    <div class="interface-header">
        <h1>Configuration</h1>
    </div>
    <fieldset class="parameter-config" id="injectionSettings">
        <legend>Injection</legend>
        <div>`
    settingsForm += generateExtractorForm();
    settingsForm += generateActionsForm();
    settingsForm += generateStorageForm();
    settingsForm += generateFilesForm();
    //settingsForm += generateButtons() 
    settingsForm += '</div></fieldset>'
    document.getElementById('toolConfiguration').innerHTML = settingsForm;
    let functionSettings = tool.settings.service
    let fileSettings = tool.settings.data
    let options = tool.options
    populateExtractorOptions(options.extractors, functionSettings.extractor);
    populateActionsCheckboxes(options.trasformations, functionSettings.actions);
    populateStorageOptions(options.storages, functionSettings.storage);
    populateFilesCheckboxes(options.files, fileSettings.files);
    //bindLoadResetEvents();
}

/**
 * Generates the Extractor form section.
 * @returns {string} The HTML for the LLM form.
 */
function generateExtractorForm() {
    return `
        <div class="configurable-field" style="margin-bottom: 1rem;">
            <label for="extractor_select">Extractor</label>
            <select id="extractor_select">
                <option>Placeholder</option>
            </select>
        </div>`;
}

/**
 * Generates the Actions form section with multiple visible options for selection.
 * @returns {string} The HTML for the LLM accordion with checkboxes.
 */
function generateActionsForm() {
    return `
        <div class="configurable-field" style="margin-bottom: 1rem;">
            <label for="actions_checkboxes">Trasformations</label>
            <div id="actions_checkboxes">
                <div>
                    <input type="checkbox" id="action_option1"value="Placeholder">
                    <label for="action_option1" style="font-size: 1rem;">Placeholder</label>
                </div>
            </div>
        </div>`;
}

/**
 * Generates the Storage form section.
 * @returns {string} The HTML for the LLM form.
 */
function generateStorageForm() {
    return `
        <div class="configurable-field" style="margin-bottom: 1rem;">
            <label for="storage_select">Storage</label>
            <select id="storage_select">
                <option>Placeholder</option>
            </select>
        </div>`;
}

/**
 * Generates the Files form section with multiple visible options for selection.
 * @returns {string} The HTML for the LLM with checkboxes.
 */
function generateFilesForm() {
    return `
        <div class="configurable-field" style="margin-bottom: 1rem;">
            <label for="files_checkboxes">Files</label>
            <div id="files_checkboxes">
                <div>
                    <input type="checkbox" id="file_option1" name="asction" value="Placeholder">
                    <label for="file_option1" style="font-size: 1rem;">Placeholder</label>
                </div>
            </div>
        </div>`;
}

/**
 * Generates the injection Buttons.
 * @returns {string} The HTML for the buttons.
 */
function generateButtons() {
    return `
    <div>
        <button type="button" class="btn-remove-config reset-interface-button">Reset dB</button>
        <button type="button" class="btn-load-config load-interface-button">Load Files</button>
    </div>`;
}

/**
 * Populates the Extractor options dropdown.
 * @param {Array} extractorOptions - Array of Extractor option objects.
 */
function populateExtractorOptions(extractorOptions, extractorSelected) {
    const extractorSelect = document.getElementById('extractor_select');
    extractorSelect.innerHTML = extractorOptions.map(option => {
        const isSelected = option.settings.type === extractorSelected.type ? 'selected' : '';
        return `<option value="${option.label}" ${isSelected}>${option.label}</option>`;
    }).join('');
}

/**
 * Populates the Extractor options dropdown.
 * @param {Array} trasformationOptions - Array of actions.
 */
function populateActionsCheckboxes(trasformationOptions, actionsSelected) {
    const trasformationSelect = document.getElementById('actions_checkboxes');
    trasformationSelect.innerHTML = trasformationOptions.map((option, index) => {
        const isChecked = actionsSelected.includes(option) ? 'checked' : '';
        return `
    <div>
        <input type="checkbox" id="action_${index}" value="${option}" ${isChecked}>
        <label for="action_${index}" style="font-size: 1rem;">${option}</label>
    </div>`;
    }).join('');
}

/**
 * Populates the Storage options dropdown.
 * @param {Array} storageOptions - Array of Storage option objects.
 */
function populateStorageOptions(storageOptions, storageSelected) {
    const storageSelect = document.getElementById('storage_select');
    storageSelect.innerHTML = storageOptions.map(option => {
        const isSelected = option.settings.type === storageSelected.type ? 'selected' : '';
        return `<option value="${option.label}" ${isSelected}>${option.label}</option>`;
    }).join('');
}

/**
 * Populates the Extractor options dropdown.
 * @param {Array} fileOptions - Array of actions.
 * @param {Array} filesSelected - Array of Files.
 */
function populateFilesCheckboxes(fileOptions, filesSelected) {
    const filesSelect = document.getElementById('files_checkboxes');
    filesSelect.innerHTML = fileOptions.map((option, index) => {
        const isChecked = filesSelected.some(file => file.source === option) ? 'checked' : '';
        return `
    <div>
        <input type="checkbox" id="file_${index}" value="${option}" ${isChecked}>
        <label for="file_${index}" style="font-size: 1rem;">${option}</label>
    </div>`;
    }).join('');
}

/**
 * Generates the configuration retrieval form.
 * @param {Object} tool - The tool object containing settings.
 */
function generateRetrievalToolConfigurationForm(tool) {
    let settingsForm = `
    <fieldset class="parameter-config" id="retrievalSettings">
        <legend>Retrieval</legend><div>`
    settingsForm += generateLlmForm();
    settingsForm += generateSystemForm();
    settingsForm += generateChunksForm();
    settingsForm += '</div></fieldset>'
    document.getElementById('toolConfiguration').innerHTML += settingsForm;
    let functionSettings = tool.settings.service
    let options = tool.options
    populateLLMOptions(options.llms, functionSettings.llm);
    populateSystemPrompt(functionSettings.query_expantion);
    populateChunks(functionSettings.retriever.n_results, functionSettings.rerank.summary_chunks)
}

/**
 * Generates the LLM form section.
 * @returns {string} The HTML for the LLM accordion.
 */
function generateLlmForm() {
    return `
        <div class="configurable-field" style="margin-bottom: 1rem;">
            <label for="llm_select">LLM</label>
            <select id="llm_select">
                <option>Placeholder</option>
            </select>
        </div>`;
}

/**
 * Generates the System Prompt form section.
 * @returns {string} The HTML for the System Prompt accordion.
 */
function generateSystemForm() {
    return `
        <div class="configurable-field" style="margin-bottom: 0.5rem;">
            <label for="tool-textarea">Query Augmentation Prompt</label>
            <textarea id="system_prompt_textarea" rows="9" placeholder="Enter your notes..."></textarea>
        </div>`;
}

/**
 * Generates the Chunk form section.
 * @returns {string} The HTML for the Chunk inputs.
 */
function generateChunksForm() {
    return `
        <div class="configurable-field">
            <label for="chunk_number">Retrieved Chunks</label>
            <input type="text" id="chunk_number"/>
            <label for="rerank_number">Reranked Chunks</label>
            <input type="text" id="rerank_number"/>
        </div>`;
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
 * Populates the system prompt textarea.
 * @param {string} systemPrompt - The system prompt text.
 */
function populateSystemPrompt(systemPrompt) {
    document.getElementById('system_prompt_textarea').value = systemPrompt;
}

/**
 * Populates the retrieved chunks.
 * @param {string} n_chunk - The retrieved chunks.
 * @param {string} r_chunk - The reranked chunks.
 */
function populateChunks(n_chunk, r_chunk) {
    // Find the input fields by their IDs
    const chunkInput = document.getElementById('chunk_number');
    const rerankInput = document.getElementById('rerank_number');

    // Set the values of the input fields
    if (chunkInput) {
        chunkInput.value = n_chunk;
    }
    if (rerankInput) {
        rerankInput.value = r_chunk;
    }
}

/**
 * Collects settings from the form inputs.
 * @returns {Object} The settings object.
 */
function collectRagToolSettings() {
    const settings = {};
    // Injection
    settings['extractor'] = document.getElementById('extractor_select').value;
    const actions_checkboxes = document.querySelectorAll('#actions_checkboxes input[type="checkbox"]:checked');
    settings['actions'] = Array.from(actions_checkboxes).map(checkbox => checkbox.value);
    settings['storage'] = document.getElementById('storage_select').value;
    const files_checkboxes = document.querySelectorAll('#files_checkboxes input[type="checkbox"]:checked');
    settings['files'] = Array.from(files_checkboxes).map(checkbox => checkbox.value);
    // Retrieval
    settings['llm'] = document.getElementById('llm_select').value;
    settings['query_expantion'] = document.getElementById('system_prompt_textarea').value;
    settings['n_results'] = document.getElementById('chunk_number').value;
    settings['summary_chunks'] = document.getElementById('rerank_number').value;
    return settings;
}

/**
 * Apply the settings via a POST request.
 * @param {string} toolId - The ID of the selected tool.
 * @param {Object} settings - The settings object to save.
 */
function applyRagToolSettings(toolId, settings) {
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
    appendRagToolDetails,
    generateRagToolSettingsForm,
    collectRagToolSettings,
    applyRagToolSettings
};
