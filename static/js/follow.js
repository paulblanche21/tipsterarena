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
    if (!username) {
        console.error('No username provided');
        alert('Error: Username is required');
        return;
    }

    const formData = new FormData();
    formData.append('username', username);

    fetch('/api/follow/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken(),
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            button.textContent = data.is_following ? 'Following' : 'Follow';
            button.classList.toggle('followed', data.is_following);
            console.log(data.message);
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    })
    .catch(error => {
        console.error('Error following user:', error);
        alert('An error occurred while following. Please try again.');
        // Reset button state
        button.textContent = 'Follow';
        button.classList.remove('followed');
    });
}