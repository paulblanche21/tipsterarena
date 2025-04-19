window.LOGOUT_URL = "{{ logout_url }}";
window.LANDING_URL = "{{ landing_url }}";
const DEFAULT_AVATAR_URL = "{{ default_avatar_url }}";
const DEFAULT_BANNER_URL = "{{ default_banner_url }}";

function setDefaultBanner(img) {
    if (!img.dataset.retryCount) {
        img.dataset.retryCount = 0;
    }
    if (parseInt(img.dataset.retryCount) >= 3) {
        console.warn(`Max retries reached for banner image: ${img.src}`);
        return;
    }
    img.dataset.retryCount = parseInt(img.dataset.retryCount) + 1;
    console.log(`Setting default banner for image: ${img.src}`);
    img.src = DEFAULT_BANNER_URL;
    img.onerror = null;
}

function setDefaultAvatar(img) {
    if (!img.dataset.retryCount) {
        img.dataset.retryCount = 0;
    }
    if (parseInt(img.dataset.retryCount) >= 3) {
        console.warn(`Max retries reached for avatar image: ${img.src}`);
        return;
    }
    img.dataset.retryCount = parseInt(img.dataset.retryCount) + 1;
    console.log(`Setting default avatar for image: ${img.src}`);
    img.src = DEFAULT_AVATAR_URL;
    img.onerror = null;
}

window.currentUser = "{{ request.user.username|default:'Guest' }}";