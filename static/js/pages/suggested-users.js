import { attachFollowButtonListeners } from '../follow.js';

export function initSuggestedUsersModal() {
    const showMoreLinks = document.querySelectorAll('.show-more[data-target="who-to-follow"]');
    
    showMoreLinks.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            
            // Create modal if it doesn't exist
            let modal = document.querySelector('.suggested-users-modal');
            if (!modal) {
                modal = document.createElement('div');
                modal.className = 'suggested-users-modal';
                modal.innerHTML = `
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2>Suggested Tipsters</h2>
                            <span class="modal-close">&times;</span>
                        </div>
                        <div class="modal-body">
                            <div class="suggested-users-list"></div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
                
                // Add close button functionality
                const closeBtn = modal.querySelector('.modal-close');
                closeBtn.addEventListener('click', () => {
                    modal.style.display = 'none';
                });
                
                // Close modal when clicking outside
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        modal.style.display = 'none';
                    }
                });
            }
            
            // Show modal
            modal.style.display = 'block';
            
            // Fetch and display suggested users
            try {
                const response = await fetch('/api/suggested-users/?limit=20', {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const usersList = modal.querySelector('.suggested-users-list');
                    
                    if (data.users && data.users.length > 0) {
                        usersList.innerHTML = data.users.map(user => `
                            <div class="suggested-user-card">
                                <div class="user-info">
                                    <div class="user-avatar">
                                        <img src="${user.avatar_url}" alt="${user.username}">
                                    </div>
                                    <div class="user-details">
                                        <a href="${user.profile_url}" class="user-name">${user.username}</a>
                                        <span class="user-handle">${user.handle}</span>
                                        <p class="user-bio">${user.bio}</p>
                                        <div class="user-stats">
                                            <span><strong>${user.total_tips || 0}</strong> Tips</span>
                                            <span><strong>${user.win_rate || 0}%</strong> Win Rate</span>
                                            <span><strong>${user.followers_count || 0}</strong> Followers</span>
                                        </div>
                                    </div>
                                    <button class="follow-btn" data-username="${user.username}">Follow</button>
                                </div>
                            </div>
                        `).join('');
                        
                        // Attach follow button listeners
                        attachFollowButtonListeners();
                    } else {
                        usersList.innerHTML = '<div class="no-suggestions">No suggested tipsters available.</div>';
                    }
                }
            } catch (error) {
                console.error('Error loading suggested users:', error);
                const usersList = modal.querySelector('.suggested-users-list');
                usersList.innerHTML = '<div class="no-suggestions">Unable to load suggestions.</div>';
            }
        });
    });
} 