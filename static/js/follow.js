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

// Create and append modal to body if it doesn't exist
function createSuggestedUsersModal() {
    if (!document.getElementById('suggestedUsersModal')) {
        const modalHTML = `
            <div id="suggestedUsersModal" class="suggested-users-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Suggested Users to Follow</h2>
                        <span class="modal-close">&times;</span>
                    </div>
                    <div class="modal-body">
                        <div class="suggested-users-list"></div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Add modal close functionality
        const modal = document.getElementById('suggestedUsersModal');
        const closeBtn = modal.querySelector('.modal-close');
        
        closeBtn.onclick = () => modal.style.display = 'none';
        window.onclick = (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        };
    }
}

// Initialize show more functionality
export function initShowMore() {
    createSuggestedUsersModal();
    const showMoreBtn = document.querySelector('.show-more[data-target="who-to-follow"]');
    const modal = document.getElementById('suggestedUsersModal');
    
    if (showMoreBtn && modal) {
        showMoreBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            try {
                // Show the modal with loading state
                modal.style.display = 'block';
                const usersList = modal.querySelector('.suggested-users-list');
                if (usersList) {
                    usersList.innerHTML = '<div class="loading">Loading suggested users...</div>';
                }

                // Use the same endpoint as the sidebar but request more users
                const response = await fetch('/api/suggested-users/', {
                    method: 'GET',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    credentials: 'include'
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || 'Failed to load suggested users');
                }

                if (usersList) {
                    if (!data.users || data.users.length === 0) {
                        usersList.innerHTML = '<div class="no-suggestions">No suggested users available at the moment.</div>';
                        return;
                    }

                    usersList.innerHTML = data.users.map(user => `
                        <div class="suggested-user-card">
                            <div class="user-info">
                                <div class="user-avatar">
                                    <img src="${user.avatar_url || '/static/img/default-avatar.png'}" 
                                         alt="${user.username} Avatar"
                                         onerror="this.src='/static/img/default-avatar.png'">
                                </div>
                                <div class="user-details">
                                    <a href="/profile/${user.username}/" class="user-name">${user.username}</a>
                                    <span class="user-handle">${user.handle || '@' + user.username}</span>
                                    <p class="user-bio">${user.bio || 'No description provided.'}</p>
                                    <div class="user-stats">
                                        <span><strong>${user.total_tips || 0}</strong> Tips</span>
                                        <span><strong>${(user.win_rate || 0).toFixed(1)}%</strong> Win Rate</span>
                                        <span><strong>${user.followers_count || 0}</strong> Followers</span>
                                    </div>
                                </div>
                                <button class="follow-btn ${user.is_following ? 'followed' : ''}" 
                                        data-username="${user.username}">
                                    ${user.is_following ? 'Following' : 'Follow'}
                                </button>
                            </div>
                        </div>
                    `).join('');

                    // Re-attach follow button listeners
                    attachFollowButtonListeners();
                }
            } catch (error) {
                console.error('Error loading suggested users:', error);
                const usersList = modal.querySelector('.suggested-users-list');
                if (usersList) {
                    usersList.innerHTML = `
                        <div class="error-message">
                            Failed to load suggested users. Please try again later.
                            <button class="retry-btn">Retry</button>
                        </div>
                    `;
                    
                    // Add retry functionality
                    const retryBtn = usersList.querySelector('.retry-btn');
                    if (retryBtn) {
                        retryBtn.onclick = () => initShowMore();
                    }
                }
            }
        });
    }
}

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
        background: var(--red-accent);
        color: white;
        border: none;
        border-radius: 20px;
        cursor: pointer;
    }
    
    .retry-btn:hover {
        background: var(--red-dark);
    }
    
    .no-suggestions {
        text-align: center;
        padding: 20px;
        color: var(--gray-600);
    }
`;

// Add styles to document
if (!document.getElementById('follow-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'follow-styles';
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    attachFollowButtonListeners();
    initShowMore();
});