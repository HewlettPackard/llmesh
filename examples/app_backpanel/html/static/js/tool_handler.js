// Map to store tool information by tool ID
const toolMap = new Map(); 


// Import the PromptTool handlers
import {
    appendPromptToolDetails,
    generatePromptToolSettingsForm,
    collectPromptToolSettings,
    applyPromptToolSettings
} from './prompt_tool_handler.js';
// Import the RagTool handlers
import {
    appendRagToolDetails,
    generateRagToolSettingsForm,
    collectRagToolSettings,
    applyRagToolSettings
} from './rag_tool_handler.js';


// Handlers for different tool types
const toolHandlers = {
    'PromptTool': {
        appendDetails: appendPromptToolDetails,
        generateSettingsForm: generatePromptToolSettingsForm,
        collectSettings: collectPromptToolSettings,
        applySettings: applyPromptToolSettings
    },
    'RagTool': {
        appendDetails: appendRagToolDetails,
        generateSettingsForm: generateRagToolSettingsForm,
        collectSettings: collectRagToolSettings,
        applySettings: applyRagToolSettings
    },
    // Others tool types
};


// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    const customerType = getCustomerType();
    setCustomerStyles(customerType);
    loadTools();

    // Event listener for tool selection change
    document.getElementById('toolSelection').addEventListener('change', function() {
        const toolId = this.value;
        clearToolDetailsAndSettings();
        fetch(`/tools/${toolId}`)
            .then(response => response.json())
            .then(tool => {
                const toolType = tool.type;
                const handlers = toolHandlers[toolType];
                if (!handlers) {
                    alert(`Unsupported tool type '${toolType}'`);
                    return;
                }
                document.getElementById('toolDetails').innerHTML = ''
                handlers.appendDetails(tool);
                handlers.generateSettingsForm(tool);
            });
    });

    // Apply button click event
    document.getElementById('applyButton').addEventListener('click', () => {
        const toolId = document.getElementById('toolSelection').value; // Get toolId from the selected option
        const toolType = getToolType(toolId)
        const handlers = toolHandlers[toolType];
        if (!handlers) {
            alert(`Unsupported tool type '${toolType}'`);
            return;
        }
        const settings = handlers.collectSettings();
        if (settings) {
            handlers.applySettings(toolId, settings);
        }
    });

    // Cancel button click event
    document.getElementById('cancelButton').addEventListener('click', () => {
        document.getElementById('toolSelection').dispatchEvent(new Event('change'));
    });

    // Reset button click event
    document.getElementById('resetButton').addEventListener('click', () => {
        const toolId = document.getElementById('toolSelection').value; // Get toolId from the selected option
        clearToolDetailsAndSettings();
        fetch(`/tools/${toolId}/reset`, {
            method: 'POST', // Specify POST method
            headers: {
                'Content-Type': 'application/json' // Set headers if needed
            }
        })
        .then(response => response.json())
        .then(tool => {
            const toolType = tool.type;
            const handlers = toolHandlers[toolType];
            if (!handlers) {
                alert(`Unsupported tool type '${toolType}'`);
                return;
            }
            document.getElementById('toolDetails').innerHTML = ''
            handlers.appendDetails(tool);
            handlers.generateSettingsForm(tool);
        })
        .catch(error => {
            console.error('Error resetting tool:', error);
        });
    });
});

/**
 * Retrieves the customer type set in the HTML by Flask.
 * @returns {string} The customer type.
 */
function getCustomerType() {
    return document.body.dataset.customerType;
}

/**
 * Sets the customer-specific styles based on the customer type.
 * @param {string} customerType - The customer type.
 */
function setCustomerStyles(customerType) {
    if (customerType) {
        document.body.classList.add(customerType);
    }
}

/**
 * Loads tools into the selection dropdown.
 */
function loadTools() {
    fetch("/tools")
        .then(response => response.json())
        .then(data => {
            // Populate the toolMap with tool ID as key and tool info as value
            data.forEach(tool => {
                toolMap.set(tool.id, tool); // Store the full tool object, including type and other properties
            });

            let options = data.map(tool => `<option value="${tool.id}">${tool.name}</option>`).join('');
            if (options == "")
                options = "<option selected disabled>No Tool Available</option>"
            document.getElementById('toolSelection').innerHTML = options;
            document.getElementById('toolSelection').dispatchEvent(new Event('change'));
        });
}

/**
 * Example function to retrieve a tool type by its ID
 */ 
function getToolType(toolId) {
    const tool = toolMap.get(Number(toolId));
    return tool ? tool.type : null; // Return the type if found, otherwise null
}

/**
 * Clears existing tool details and settings.
 */
function clearToolDetailsAndSettings() {
    // Get the relevant elements
    document.getElementById('toolDetails').innerHTML = '<p>No tools were found. Please verify the endpoint and ensure the connection is properly configured.</p>';
    document.getElementById('toolConfiguration').innerHTML = '';
    document.getElementById('toolInterface').innerHTML = '';

    // Hide configuration and interface
    document.getElementById('toolConfigurationBox').style.display = 'none';
    document.getElementById('toolInterfaceBox').style.display = 'none';
}
