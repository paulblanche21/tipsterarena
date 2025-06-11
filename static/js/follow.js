import { getCSRFToken } from './pages/utils.js';

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
        // Remove any existing click listeners
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        // Initialize button state
        const username = newButton.dataset.username;
        if (newButton.dataset.isFollowing === 'true') {
            newButton.classList.add('followed');
            newButton.textContent = 'Following';
        }
        
        newButton.addEventListener('click', async (e) => {
            e.preventDefault();
            const username = newButton.dataset.username;
            const isFollowing = newButton.classList.contains('followed');
            
            // Store original state for rollback
            const originalText = newButton.textContent;
            const originalClass = newButton.className;
            
            // Optimistic update
            newButton.disabled = true;
            newButton.classList.toggle('followed');
            newButton.textContent = isFollowing ? 'Follow' : 'Following';
            
            // Add loading animation
            newButton.classList.add('loading');
            
            try {
                const response = await fetch(`/api/follow/${username}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    credentials: 'include'
                });

                const data = await response.json();

                if (!response.ok) {
                    // Rollback on error
                    newButton.className = originalClass;
                    newButton.textContent = originalText;
                    
                    // Show error toast with server's error message
                    showToast(data.error || `Error: ${response.status}`, 'error');
                    return;
                }
                
                // Update button state
                if (data.is_following) {
                    newButton.classList.add('followed');
                    newButton.textContent = 'Following';
                } else {
                    newButton.classList.remove('followed');
                    newButton.textContent = 'Follow';
                }
                
                // Update follower count if available
                const followerCountElement = document.querySelector('.follower-count');
                if (followerCountElement && data.follower_count !== undefined) {
                    followerCountElement.textContent = data.follower_count;
                }
                
                // Show success toast
                showToast(data.message || (data.is_following ? 'Followed successfully' : 'Unfollowed successfully'), 'success');
                
            } catch (error) {
                // Rollback on network error
                newButton.className = originalClass;
                newButton.textContent = originalText;
                
                // Show error toast
                showToast('Network error. Please try again.', 'error');
                console.error('Error toggling follow status:', error);
            } finally {
                // Remove loading state
                newButton.classList.remove('loading');
                newButton.disabled = false;
            }
        });
    });
}

// Toast notification function
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Add toast to container or create one
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
} 