import { attachFollowButtonListeners } from '../follow.js';
import { getCSRFToken } from './utils.js';

// Suggested Users Modal
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
                                    <button class="follow-btn" data-username="${user.username}" data-is-following="${user.is_following}">${user.is_following ? 'Following' : 'Follow'}</button>
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

// Trending Tips
export class TrendingTips {
    constructor() {
        this.trendingTipsList = document.querySelector('.trending-tips-list');
        this.init();
    }

    init() {
        if (this.trendingTipsList) {
            this.fetchTrendingTips();
        }
    }

    async fetchTrendingTips() {
        if (!this.trendingTipsList) return;

        this.trendingTipsList.classList.add('loading');

        try {
            const response = await fetch('/api/trending-tips/');
            const data = await response.json();

            if (data.trending_tips && data.trending_tips.length > 0) {
                this.trendingTipsList.innerHTML = data.trending_tips.map(tip => `
                    <div class="trending-tip" data-tip-id="${tip.id}">
                        <div class="trending-tip-content">
                            <p class="tip-text">${tip.text}</p>
                            <div class="tip-meta">
                                <span class="tip-user">${tip.username}</span>
                                <div class="tip-actions">
                                    <div class="tip-action-group">
                                        <a href="#" class="tip-action tip-action-like" data-action="like">
                                            <i class="fas fa-heart"></i>
                                        </a>
                                        <span class="tip-action-count like-count">${tip.likes_count}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');

                this.attachLikeListeners();
            } else {
                this.trendingTipsList.innerHTML = '<p class="no-tips">No trending tips available</p>';
            }
        } catch (error) {
            console.error('Error fetching trending tips:', error);
            this.trendingTipsList.innerHTML = '<p class="error">Error loading trending tips</p>';
        } finally {
            this.trendingTipsList.classList.remove('loading');
        }
    }

    attachLikeListeners() {
        const likeButtons = this.trendingTipsList.querySelectorAll('.tip-action-like');
        likeButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const tipElement = button.closest('.trending-tip');
                const tipId = tipElement.dataset.tipId;
                const likeCount = button.nextElementSibling;

                try {
                    const formData = new FormData();
                    formData.append('tip_id', tipId);

                    const response = await fetch('/api/like-tip/', {
                        method: 'POST',
                        body: formData,
                        headers: { 'X-CSRFToken': getCSRFToken() },
                        credentials: 'include'
                    });

                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    
                    const data = await response.json();
                    if (data.success) {
                        // Toggle the liked class on the button
                        button.classList.toggle('liked', data.message === 'Tip liked');
                        // Update the like count
                        likeCount.textContent = data.likes_count;
                    }
                } catch (error) {
                    console.error('Error liking tip:', error);
                }
            });
        });
    }
}

// Initialize both features when the DOM is loaded
// Remove the DOMContentLoaded event listener since we're exporting the functions 