window.LOGOUT_URL = "{{ logout_url }}";
window.LANDING_URL = "{{ landing_url }}";
const DEFAULT_AVATAR_URL = "{{ default_avatar_url }}";
const DEFAULT_BANNER_URL = "{{ default_banner_url }}";
function setDefaultBanner(img) {
    img.src = DEFAULT_BANNER_URL;
    img.onerror = null;
}
function setDefaultAvatar(img) {
    img.src = DEFAULT_AVATAR_URL;
    img.onerror = null;
}
window.currentUser = "{{ request.user.username|default:'Guest' }}";