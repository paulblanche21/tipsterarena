// trending-tips.js
import { getCSRFToken } from './utils.js';

class TrendingTips {
    constructor() {
        this.trendingTipsList = document.querySelector('.trending-tips-list');
        this.initialized = false;
    }

    init() {
        if (this.initialized) return;
        console.log("Initializing trending tips...");
        
        this.fetchTrendingTips();
        // Refresh every 60 seconds
        setInterval(() => this.fetchTrendingTips(), 60000);
        
        this.initialized = true;
    }

    async fetchTrendingTips() {
        try {
            console.log('Fetching trending tips...');
            const response = await fetch('/api/trending-tips/');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            if (!this.trendingTipsList) {
                console.error('Trending tips list element not found');
                return;
            }

            this.trendingTipsList.innerHTML = ''; // Clear existing tips
            
            if (!data.trending_tips || data.trending_tips.length === 0) {
                this.trendingTipsList.innerHTML = '<p>No trending tips available.</p>';
                return;
            }

            console.log('Received trending tips:', data.trending_tips);
            data.trending_tips.forEach(tip => {
                const tipElement = this.createTipElement(tip);
                this.trendingTipsList.appendChild(tipElement);
            });

            this.attachHeartListeners();
        } catch (error) {
            console.error('Error fetching trending tips:', error);
            this.trendingTipsList.innerHTML = '<p>Error loading trending tips. Please try again later.</p>';
        }
    }

    createTipElement(tip) {
        const tipElement = document.createElement('div');
        tipElement.className = 'trending-tip';
        tipElement.dataset.tipId = tip.id; // Add tip ID to the element
        
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
        console.log('Attaching heart listeners...');
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