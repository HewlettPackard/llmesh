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
            updateLogo(settings.logo_url);
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
 * Updates the logo URL.
 * @param {string} logoUrl - The path to the logo file.
 */
function updateLogo(logoUrl) {
    const logoElement = document.getElementById('dynamic-logo');
    if (logoElement) {
        logoElement.src = `static/${logoUrl}`;
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
