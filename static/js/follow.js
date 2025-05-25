// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export function attachFollowButtonListeners() {
    const followButtons = document.querySelectorAll('.follow-btn');
    followButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const username = button.dataset.username;
            const isFollowing = button.classList.contains('followed');
            
            try {
                const response = await fetch(`/api/follow/${username}/`, {
                    method: isFollowing ? 'DELETE' : 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    credentials: 'include'
                });

                if (response.ok) {
                    button.classList.toggle('followed');
                    button.textContent = isFollowing ? 'Follow' : 'Following';
                }
            } catch (error) {
                console.error('Error toggling follow status:', error);
            }
        });
    });
} 