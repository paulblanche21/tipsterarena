// trending-tips.js

export function init() {
    console.log("trending-tips.js initialized");
}

function fetchTrendingTips() {
    fetch('/api/trending-tips/')
        .then(response => response.json())
        .then(data => {
            const trendingTipsList = document.querySelector('.trending-tips-list');
            trendingTipsList.innerHTML = ''; // Clear existing tips
            if (data.trending_tips.length === 0) {
                trendingTipsList.innerHTML = '<p>No trending tips available.</p>';
                return;
            }
            data.trending_tips.forEach(tip => {
                const tipElement = document.createElement('div');
                tipElement.className = 'trending-tip';
                tipElement.innerHTML = `
                    <img src="${tip.avatar_url}" alt="${tip.username} Avatar" class="tip-avatar">
                    <div class="tip-details">
                        <a href="${tip.profile_url}" class="tip-username"><strong>${tip.handle}</strong></a>
                        <p class="tip-text">${tip.text}</p>
                    </div>
                    <span class="tip-likes"><i class="fas fa-heart"></i> ${tip.likes}</span>
                `;
                trendingTipsList.appendChild(tipElement);
            });
        })
        .catch(error => console.error('Error fetching trending tips:', error));
}

// Fetch trending tips on page load
document.addEventListener('DOMContentLoaded', fetchTrendingTips);

// Optionally, refresh every 60 seconds
setInterval(fetchTrendingTips, 60000);