// static/js/pages/bookmarks.js
import { getCSRFToken } from './utils.js';

export function setupBookmarkInteractions() {
    
    
    document.querySelectorAll('.tip-action-bookmark').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const tipElement = button.closest('.tip');
            const tipId = tipElement?.dataset.tipId;

            if (!tipId) {
                console.error('Tip ID not found on element:', tipElement);
                return;
            }

            try {
                console.log('Sending bookmark request for tip:', tipId);
                const response = await fetch('/api/toggle-bookmark/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({ tip_id: parseInt(tipId) }),
                    credentials: 'include'
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                console.log('Bookmark response:', data);
                
                if (data.success) {
                    // Toggle the bookmarked state
                    button.classList.toggle('bookmarked');
                    
                    // Update the icon color
                    const icon = button.querySelector('i');
                    if (icon) {
                        if (data.is_bookmarked) {
                            icon.style.color = '#FFD700'; // Yellow for bookmarked
                        } else {
                            icon.style.color = '#808080'; // Grey for unbookmarked
                        }
                    }
                    
                    // If we're on the bookmarks page and unbookmarking, remove the tip
                    if (window.location.pathname === '/bookmarks/' && !data.is_bookmarked) {
                        const tipCard = button.closest('.tip');
                        if (tipCard) {
                            tipCard.style.opacity = '0';
                            setTimeout(() => {
                                tipCard.remove();
                                // Check if there are any tips left
                                const remainingTips = document.querySelectorAll('.tip');
                                if (remainingTips.length === 0) {
                                    location.reload(); // Reload to show empty state
                                }
                            }, 300);
                        }
                    }
                } else {
                    console.error('Bookmark toggle failed:', data.error);
                    alert('Failed to bookmark tip. Please try again.');
                }
            } catch (error) {
                console.error('Error toggling bookmark:', error);
                alert('An error occurred while bookmarking. Please try again.');
            }
        });
    });
}