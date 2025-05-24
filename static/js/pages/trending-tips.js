// trending-tips.js
import { getCSRFToken } from './utils.js';

class TrendingTips {
    constructor() {
        this.trendingTipsList = document.querySelector('.trending-tips-list');
        this.showMoreBtn = document.querySelector('.show-more[data-target="trending-tips"]');
        this.modal = document.getElementById('trending-tips-modal');
        this.closeBtn = this.modal?.querySelector('.trending-tips-modal-close');
        this.tipsList = this.modal?.querySelector('.trending-tips-list-modal');
        this.initialized = false;
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    init() {
        if (this.initialized) {
            return;
        }
        
        if (!this.trendingTipsList) {
            return;
        }
        
        this.fetchTrendingTips();
        // Refresh every 60 seconds
        setInterval(() => this.fetchTrendingTips(), 120000);
        
        // Initialize modal functionality
        if (this.showMoreBtn && this.modal && this.closeBtn && this.tipsList) {
            this.initModal();
        }
        
        this.initialized = true;
    }

    initModal() {
        // Show modal
        this.showMoreBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.loadModalTrendingTips();
            this.modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        });

        // Close modal
        this.closeBtn.addEventListener('click', () => {
            this.modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        });

        // Close modal when clicking outside
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }

    async loadModalTrendingTips() {
        try {
            const response = await fetch('/api/trending-tips/?limit=30');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            this.tipsList.innerHTML = ''; // Clear existing tips
            data.forEach(tip => {
                const tipElement = this.createModalTipElement(tip);
                this.tipsList.appendChild(tipElement);
            });
        } catch (error) {
            console.error('Error loading modal trending tips:', error);
            this.tipsList.innerHTML = '<p class="error-message">Failed to load trending tips. Please try again later.</p>';
        }
    }

    createModalTipElement(tip) {
        const div = document.createElement('div');
        div.className = 'trending-tip-modal-item';
        div.innerHTML = `
            <div class="trending-tip-modal-content">
                <p class="trending-tip-modal-text">${this.escapeHtml(tip.text)}</p>
                <div class="trending-tip-modal-user">
                    <img src="${tip.user.avatar_url || '/static/img/default-avatar.png'}" 
                         alt="${tip.user.username}" 
                         class="trending-tip-modal-avatar">
                    <span>@${tip.user.username}</span>
                </div>
                <div class="trending-tip-modal-stats">
                    <div class="trending-tip-modal-stat">
                        <i class="fas fa-heart"></i>
                        <span>${tip.likes_count}</span>
                    </div>
                    <div class="trending-tip-modal-stat">
                        <i class="fas fa-comment"></i>
                        <span>${tip.comments_count}</span>
                    </div>
                    <div class="trending-tip-modal-stat">
                        <i class="fas fa-share"></i>
                        <span>${tip.shares_count}</span>
                    </div>
                </div>
            </div>
        `;
        return div;
    }

    async fetchTrendingTips() {
        try {
            const response = await fetch('/api/trending-tips/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            if (!this.trendingTipsList) {
                console.error('Trending tips list element not found');
                return;
            }

            this.trendingTipsList.innerHTML = ''; // Clear existing tips
            
            if (!data.trending_tips || data.trending_tips.length === 0) {
                console.log('No trending tips available');
                this.trendingTipsList.innerHTML = '<p>No trending tips available.</p>';
                return;
            }

            data.trending_tips.forEach(tip => {
                const tipElement = this.createTipElement(tip);
                this.trendingTipsList.appendChild(tipElement);
            });

            this.attachHeartListeners();
            this.retryCount = 0; // Reset retry count on success
        } catch (error) {
            console.error('Error fetching trending tips:', error);
            this.trendingTipsList.innerHTML = '<p>Error loading trending tips. Please try again later.</p>';
            
            // Implement retry logic
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                setTimeout(() => this.fetchTrendingTips(), 5000); // Retry after 5 seconds
            }
        }
    }

    createTipElement(tip) {
        const tipElement = document.createElement('div');
        tipElement.className = 'trending-tip';
        tipElement.dataset.tipId = tip.id;
        
        tipElement.innerHTML = `
            <div class="trending-tip-content">
                <p class="trending-tip-text">${this.escapeHtml(tip.text)}</p>
                <p class="trending-tip-user">
                    <a href="/profile/${this.escapeHtml(tip.username)}/" class="user-link">@${this.escapeHtml(tip.username)}</a>
                </p>
            </div>
            <div class="trending-tip-heart ${tip.is_liked ? 'liked' : ''}" data-tip-id="${tip.id}">
                <i class="fas fa-heart"></i>
                <span class="trending-tip-heart-count">${tip.likes_count || 0}</span>
            </div>
        `;
        
        return tipElement;
    }

    attachHeartListeners() {
        const hearts = this.trendingTipsList.querySelectorAll('.trending-tip-heart');
        hearts.forEach(heart => {
            // Remove existing listeners
            const newHeart = heart.cloneNode(true);
            heart.parentNode.replaceChild(newHeart, heart);
            
            newHeart.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                const tipId = newHeart.dataset.tipId;
                console.log('Heart clicked for tip:', tipId);
                await this.toggleLike(tipId, newHeart);
            });
        });
    }

    async toggleLike(tipId, heartElement) {
        try {
            console.log('Toggling like for tip:', tipId);
            const csrfToken = getCSRFToken();
            if (!csrfToken) {
                console.error('CSRF token not found');
                return;
            }

            const formData = new FormData();
            formData.append('tip_id', tipId);

            const response = await fetch('/api/like-tip/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData,
                credentials: 'include'
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            console.log('Like response:', data);

            if (data.success) {
                const countElement = heartElement.querySelector('.trending-tip-heart-count');
                const currentCount = parseInt(countElement.textContent) || 0;
                
                if (data.message === 'Tip liked') {
                    console.log('Tip liked');
                    heartElement.classList.add('liked');
                    countElement.textContent = currentCount + 1;
                } else {
                    console.log('Tip unliked');
                    heartElement.classList.remove('liked');
                    countElement.textContent = Math.max(0, currentCount - 1);
                }
            } else {
                console.error('Like toggle failed:', data.error);
            }
        } catch (error) {
            console.error('Error toggling like:', error);
        }
    }

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Create and export instance
const trendingTips = new TrendingTips();
export default trendingTips;