document.addEventListener('DOMContentLoaded', function() {
    const showMoreBtn = document.querySelector('.show-more[data-target="trending-tips"]');
    const modal = document.getElementById('trending-tips-modal');
    const closeBtn = modal.querySelector('.trending-tips-modal-close');
    const tipsList = modal.querySelector('.trending-tips-list-modal');

    // Show modal when "Show more" is clicked
    showMoreBtn.addEventListener('click', function(e) {
        e.preventDefault();
        modal.style.display = 'block';
        loadTrendingTips();
    });

    // Close modal when close button is clicked
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Load trending tips into modal
    async function loadTrendingTips() {
        try {
            const response = await fetch('/api/trending-tips/');
            const tips = await response.json();
            
            tipsList.innerHTML = ''; // Clear existing tips
            
            tips.forEach(tip => {
                const tipElement = createTipElement(tip);
                tipsList.appendChild(tipElement);
            });
        } catch (error) {
            console.error('Error loading trending tips:', error);
            tipsList.innerHTML = '<p>Error loading trending tips. Please try again later.</p>';
        }
    }

    // Create tip element for modal
    function createTipElement(tip) {
        const div = document.createElement('div');
        div.className = 'trending-tip-modal-item';
        div.innerHTML = `
            <div class="trending-tip-modal-content">
                <div class="trending-tip-modal-avatar">
                    <img src="${tip.user.avatar_url || '/static/img/default-avatar.png'}" alt="${tip.user.username}">
                </div>
                <div class="trending-tip-modal-text">
                    <p>${escapeHtml(tip.text)}</p>
                    <div class="trending-tip-modal-user">
                        <a href="/profile/${tip.user.username}/">@${tip.user.username}</a>
                    </div>
                </div>
                <div class="trending-tip-modal-stats">
                    <div class="trending-tip-modal-stat">
                        <i class="fas fa-heart"></i>
                        <span>${tip.likes_count}</span>
                    </div>
                </div>
            </div>
        `;
        return div;
    }

    // Helper function to escape HTML
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}); 