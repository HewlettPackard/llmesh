/**
 * Populates the dropdown list with projects from the API.
 */
async function populateProjectOptions() {
    try {
        const response = await fetch('/projects');
        
        if (!response.ok) {
            throw new Error('Failed to fetch projects');
        }
        
        const projects = await response.json();
        const selectElement = document.getElementById('chatTypeDropdown');
        selectElement.innerHTML = ''; // Clear existing options

        if (projects.length === 0) {
            displayNoProjectsAvailable(selectElement);
        } else {
            addProjectOptions(selectElement, projects);
        }
    } catch (error) {
        console.error(error.message);
    }
}

/**
 * Displays a message when no projects are available.
 * @param {HTMLElement} selectElement - The dropdown select element.
 */
function displayNoProjectsAvailable(selectElement) {
    const noProjectsOption = document.createElement('option');
    noProjectsOption.textContent = "No projects available";
    selectElement.appendChild(noProjectsOption);
}

/**
 * Adds project options to the dropdown list.
 * @param {HTMLElement} selectElement - The dropdown select element.
 * @param {Array} projects - List of project objects to populate.
 */
function addProjectOptions(selectElement, projects) {
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project.id; // Assuming each project has an 'id'
        option.textContent = project.name; // Assuming each project has a 'name'
        selectElement.appendChild(option);
    });
}

/**
 * Handles project selection change.
 * @param {string} projectId - The ID of the selected project.
 */
async function onProjectChange(projectId) {
    try {
        const response = await fetch(`/projects/${projectId}`);
        
        if (!response.ok) {
            throw new Error('Failed to select project');
        }
        
        const projectData = await response.json();
        console.log('Project selected:', projectData);
        showProjectChat(projectId); // Show the selected project's chat
    } catch (error) {
        console.error(error.message);
    }
}

import { scrollToBottom } from './chat.js';

/**
 * Shows only the selected project's chat and hides others.
 * @param {string} projectId - The ID of the selected project.
 */
function showProjectChat(projectId) {
    const projectChatDivs = document.getElementsByClassName('project-chat');
    Array.from(projectChatDivs).forEach(div => {
        div.style.display = div.id === `messageFormeight-${projectId}` ? 'block' : 'none';
    });
    scrollToBottom(); // Ensure the chat is scrolled to the bottom when switching projects
}

/**
 * Initializes the event listeners and populates project options when the document is ready.
 */
function initialize() {
    populateProjectOptions();
    document.getElementById('chatTypeDropdown').addEventListener('change', function() {
        const selectedProjectId = this.value;
        onProjectChange(selectedProjectId);
    });
}

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', initialize);
