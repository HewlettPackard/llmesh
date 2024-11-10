// Declare global variables
let botImageUrl;
let userImageUrl;

/**
 * Fetches the theme settings from a JSON file and applies them to the document.
 * @param {string} themeName - The name of the theme to apply.
 */
function applyTheme(themeName) {
    const themeUrl = `static/json/${themeName}_settings.json`;
    
    fetch(themeUrl)
        .then(response => response.json())
        .then(settings => {
            updateDocumentTitle(settings.page_title);
            updateFavicon(settings.favicon_link);
            updateImages(settings);
            updateCompanyInfo(settings);
            updateCSSVariables(settings.cssVariables);
        })
        .catch(error => console.error('Error loading theme:', error));
}

/**
 * Updates the document title.
 * @param {string} title - The title to set for the document.
 */
function updateDocumentTitle(title) {
    document.title = title;
}

/**
 * Updates the favicon link.
 * @param {string} faviconPath - The path to the favicon file.
 */
function updateFavicon(faviconPath) {
    const faviconElement = document.getElementById('dynamic-favicon');
    if (faviconElement) {
        faviconElement.href = `static/${faviconPath}`;
    }
}

/**
 * Updates the bot and user images on the document.
 * @param {Object} settings - The settings object containing image paths.
 */
function updateImages(settings) {
    logoImageUrl = `static/${settings.logo_image_src}`;
    botImageUrl = `static/${settings.bot_image_src}`;
    userImageUrl = `static/${settings.user_image_src}`;

    const logoImageElement = document.querySelector(".logo_img");
    if (logoImageElement) {
        logoImageElement.src = logoImageUrl;
    }

    const botImageElement = document.querySelector(".user_img");
    if (botImageElement) {
        botImageElement.src = botImageUrl;
    }

    const userImageElement = document.querySelector(".user_image");
    if (userImageElement) {
        userImageElement.src = userImageUrl;
    }
}

/**
 * Updates the company announcement and motto in the document.
 * @param {Object} settings - The settings object containing company information.
 */
function updateCompanyInfo(settings) {
    const announcementElement = document.querySelector(".user_info span");
    const mottoElement = document.querySelector(".user_info p");
    
    if (announcementElement) {
        announcementElement.textContent = settings.company_announcement;
    }

    if (mottoElement) {
        mottoElement.textContent = settings.company_motto;
    }
}

/**
 * Updates the CSS variables for theming.
 * @param {Object} cssVariables - An object containing CSS variable names and values.
 */
function updateCSSVariables(cssVariables) {
    const root = document.documentElement;
    Object.entries(cssVariables).forEach(([key, value]) => {
        root.style.setProperty(key, value);
    });
}
