// Utility functions
export function getCSRFToken() {
    const tokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!tokenElement) {
        console.warn("CSRF token not found on page");
        return null;
    }
    return tokenElement.value;
}