import { getCSRFToken } from './pages/utils.js';

export function attachFollowButtonListeners() {
    const followButtons = document.querySelectorAll('.follow-btn');
    followButtons.forEach(button => {
        button.addEventListener('click', function() {
            const username = this.getAttribute('data-username');
            followUser(username, this);
        });
    });
}

export function followUser(username, button) {
    const formData = new FormData();
    formData.append('username', username);
    fetch('/api/follow/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.textContent = 'Following';
            button.disabled = true;
            button.classList.add('followed');
            console.log(data.message);
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error following user:', error);
        alert('An error occurred while following.');
    });
}