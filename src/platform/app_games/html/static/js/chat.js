// Initialize chat when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    const customerType = getCustomerType();
    setCustomerStyles(customerType);
    initChat();
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
 * Initializes the chat by setting up event listeners.
 */
function initChat() {
    document.getElementById("messageArea").addEventListener("submit", handleSubmit);
}

/**
 * Handles the form submission event.
 * @param {Event} event - The form submission event.
 */
function handleSubmit(event) {
    event.preventDefault();
    const rawText = document.getElementById("text").value.trim();
    if (rawText) {
        submitUserMessage(rawText);
    }
}

/**
 * Submits the user's message, updates the chat, and sends the message to the server.
 * @param {string} rawText - The raw user input.
 */
function submitUserMessage(rawText) {
    const str_time = formatTime(new Date());
    const userHtml = createUserMessageHtml(rawText, str_time);
    clearInputField();
    appendMessageToChat(userHtml);
    sendChatMessage(rawText, str_time);
    scrollToBottom();
}

/**
 * Formats a given date into a time string (HH:MM).
 * @param {Date} date - The date to format.
 * @returns {string} The formatted time string.
 */
function formatTime(date) {
    return date.getHours().toString().padStart(2, '0') + ":" + date.getMinutes().toString().padStart(2, '0');
}

/**
 * Creates the HTML structure for a user's message.
 * @param {string} message - The user's message.
 * @param {string} time - The time the message was sent.
 * @returns {string} The HTML string for the user's message.
 */
function createUserMessageHtml(message, time) {
    return `
        <div class="d-flex justify-content-end mb-4">
            <div class="msg_cotainer_send">
                ${message}
                <span class="msg_time_send">${time}</span>
            </div>
            <div class="img_cont_msg">
                <img src="${userImageUrl}" class="rounded-circle user_img_msg">
            </div>
        </div>
    `;
}

/**
 * Clears the input field.
 */
function clearInputField() {
    document.getElementById("text").value = "";
}

/**
 * Appends a message to the selected game's chat div.
 * @param {string} htmlContent - The HTML content to append.
 */
function appendMessageToChat(htmlContent) {
    const gameId = document.getElementById('chatTypeDropdown').value;
    let gameChatDiv = document.getElementById(`messageFormeight-${gameId}`);

    if (!gameChatDiv) {
        gameChatDiv = document.createElement('div');
        gameChatDiv.id = `messageFormeight-${gameId}`;
        gameChatDiv.className = 'game-chat';
        document.getElementById('messageContainers').appendChild(gameChatDiv);
    }

    gameChatDiv.innerHTML += htmlContent;
}

/**
 * Sends the user's message to the server and processes the response.
 * @param {string} message - The user's message.
 * @param {string} time - The time the message was sent.
 */
async function sendChatMessage(message, time) {
    try {
        const response = await fetch("/message", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ msg: message })
        });
        const data = await response.text();
        processBotResponse(data, time);
    } catch (error) {
        console.error('Error sending message:', error);
    }
}

/**
 * Processes the bot's response and updates the chat.
 * @param {string} data - The bot's response in Markdown format.
 * @param {string} time - The time the message was received.
 */
function processBotResponse(data, time) {
    const converter = new showdown.Converter();
    const dataHtml = convertMarkdownToHtml(converter.makeHtml(data));
    const botHtml = createBotMessageHtml(dataHtml, time);
    appendMessageToChat(botHtml);
    scrollToBottom();
    addEventListenerToAllAccordions();
}

/**
 * Converts Markdown to HTML and applies additional formatting.
 * @param {string} text - The Markdown text.
 * @returns {string} The formatted HTML.
 */
function convertMarkdownToHtml(text) {
    const linkHtml = convertMarkdownLinksToHtml(text);
    const tableHtml = convertMarkdownTablesToHtml(linkHtml);
    const imageHtml = convertImagesToHtml(tableHtml);
    return convertCodeToAccordion(imageHtml);
}

/**
 * Converts Markdown links to HTML links.
 * @param {string} text - The text containing Markdown links.
 * @returns {string} The text with converted HTML links.
 */
function convertMarkdownLinksToHtml(text) {
    const markdownLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    return text.replace(markdownLinkRegex, (match, linkText, url) =>
        `<a href="${url}" target="_blank">${linkText}</a>`
    );
}

/**
 * Converts Markdown tables to HTML tables.
 * @param {string} text - The text containing Markdown tables.
 * @returns {string} The text with converted HTML tables.
 */
function convertMarkdownTablesToHtml(text) {
    const tableRegex = /((\|.+\|[\r\n]?)+)/g;
    return text.replace(tableRegex, match => markdownTableToHtml(match));
}

/**
 * Converts Markdown table to HTML table.
 * @param {string} markdown - The Markdown table.
 * @returns {string} The HTML table.
 */
function markdownTableToHtml(markdown) {
    const lines = markdown.trim().split('\n');
    const headers = lines[0].trim().split('|').filter(header => header.trim());
    const rows = lines.slice(2).map(line => line.trim().split('|').filter(cell => cell.trim()));
    let html = '<table>\n<thead>\n<tr>';

    headers.forEach(header => html += `<th>${header.trim()}</th>`);
    html += '</tr>\n</thead>\n<tbody>\n';

    rows.forEach(row => {
        html += '<tr>';
        row.forEach(cell => html += `<td>${cell.trim()}</td>`);
        html += '</tr>\n';
    });

    html += '</tbody>\n</table>';
    return html;
}

/**
 * Converts image placeholders in text to actual HTML image elements.
 * @param {string} text - The text containing image placeholders.
 * @returns {string} The text with converted HTML images.
 */
function convertImagesToHtml(text) {
    const regex = /<img>(.*?)<\/img>/gs;
    return text.replace(regex, `<img src='data:image/png;base64,$1' alt='Plot Image' style='opacity: 0.9;'/>`);
}

/**
 * Converts code blocks to an accordion format.
 * @param {string} text - The text containing code blocks.
 * @returns {string} The text with converted accordions.
 */
function convertCodeToAccordion(text) {
    const regex = /<code>(.*?)<\/code>/gs;
    return text.replace(regex, `
        <br/>
        <button class="accordion"><b>INFORMATION</b></button>
        <div class="panel">
          <code>$1</code>
        </div>
      `);
}

/**
 * Creates the HTML structure for a bot's message.
 * @param {string} message - The bot's message.
 * @param {string} time - The time the message was sent.
 * @returns {string} The HTML string for the bot's message.
 */
function createBotMessageHtml(message, time) {
    return `
        <div class="d-flex justify-content-start mb-4">
            <div class="img_cont_msg">
                <img src="${botImageUrl}" class="rounded-circle user_img_msg">
            </div>
            <div class="msg_cotainer">
                ${message}
                <span class="msg_time">${time}</span>
            </div>
        </div>
    `;
}

/**
 * Adds event listeners to all accordion elements.
 */
export function addEventListenerToAllAccordions() {
    const accordions = document.querySelectorAll('.accordion');
    accordions.forEach(accordion => {
        if (!accordion.hasEventListener) {
            accordion.addEventListener("click", function () {
                this.classList.toggle("active");
                // Search for the next `.panel` relative to the button
                let panel = this.parentElement.parentElement.querySelector('.panel');
                // Toggle panel visibility if a valid `.panel` is found
                if (panel) {
                    panel.style.display = panel.style.display === "block" ? "none" : "block";
                }
            });
            accordion.hasEventListener = true; // Mark as having an event listener
        }
    });
}


/**
 * Scrolls to the bottom of the selected game's chat div.
 */
function scrollToBottom() {
    const gameId = document.getElementById('chatTypeDropdown').value;
    const gameChatDiv = document.getElementById(`messageFormeight-${gameId}`);
    if (gameChatDiv) {
        gameChatDiv.scrollTop = gameChatDiv.scrollHeight;
    }
}

export { submitUserMessage, scrollToBottom };
