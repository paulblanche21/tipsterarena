// trending-tips.js
import { getCSRFToken } from './utils.js';

class TrendingTips {
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
                    <div class="trending-tip">
                        <p class="tip-text">${tip.text}</p>
                        <div class="tip-meta">
                            <span class="tip-user">${tip.username}</span>
                            <span class="tip-likes">${tip.likes_count} likes</span>
                        </div>
                    </div>
                `).join('');
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
}

export const trendingTips = new TrendingTips();