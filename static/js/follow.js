// Add loading and error styles
const styles = `
    .loading {
        text-align: center;
        padding: 20px;
        color: var(--gray-600);
    }
    
    .error-message {
        text-align: center;
        padding: 20px;
        color: var(--red-accent);
    }
    
    .retry-btn {
        margin-top: 10px;
        padding: 8px 16px;
        background: linear-gradient(45deg, var(--red-accent), var(--red-dark));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        border: 1px solid var(--red-accent);
        border-radius: 20px;
        cursor: pointer;
    }
    
    .retry-btn:hover {
        background: var(--red-dark);
        color: white;
        -webkit-text-fill-color: white;
    }
    
    .no-suggestions {
        text-align: center;
        padding: 20px;
        color: var(--gray-600);
    }

    .suggested-user-card .user-stats strong {
        background: linear-gradient(45deg, var(--black), var(--gray-800));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
`;

// Add styles to document
const styleSheet = document.createElement("style");
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);

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
            const isFollowing = button.textContent === 'Following';
            
            try {
                const csrfToken = getCookie('csrftoken');
                if (!csrfToken) {
                    console.error('CSRF token not found');
                    return;
                }

                const response = await fetch('/api/follow/', {
                    method: isFollowing ? 'DELETE' : 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ username }),
                    credentials: 'include'
                });

                if (response.ok) {
                    button.textContent = isFollowing ? 'Follow' : 'Following';
                    button.classList.toggle('following');
                } else {
                    console.error('Failed to follow/unfollow user:', await response.text());
                }
            } catch (error) {
                console.error('Error following/unfollowing user:', error);
            }
        });
    });
}

export function initShowMore() {
    const showMoreLinks = document.querySelectorAll('.show-more[data-target="who-to-follow"]');
    showMoreLinks.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            const followList = document.querySelector('.follow-list');
            if (!followList) return;

            try {
                const response = await fetch('/api/suggested-users/?limit=10', {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.users && data.users.length > 0) {
                        followList.innerHTML = '';
                        data.users.forEach(user => {
                            followList.innerHTML += `
                                <div class="follow-item">
                                    <img src="${user.avatar_url}" alt="${user.username}" class="follow-avatar">
                                    <div class="follow-details">
                                        <a href="${user.profile_url}" class="follow-username">@${user.username}</a>
                                        <p class="follow-bio">${user.bio}</p>
                                    </div>
                                    <button class="follow-btn" data-username="${user.username}">Follow</button>
                                </div>
                            `;
                        });
                        attachFollowButtonListeners();
                    }
                }
            } catch (error) {
                console.error('Error loading more users:', error);
            }
        });
    });
} 