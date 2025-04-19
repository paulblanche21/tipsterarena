// static/js/pages/bookmarks.js
export function setupBookmarkInteractions() {
    document.querySelectorAll('.tip-action-bookmark').forEach(button => {
      // Initial state is set by the template's class, no need to force it here
      button.addEventListener('click', async (e) => {
        e.preventDefault(); // Prevent any default behavior
        const tipElement = button.closest('.tip');
        const tipId = tipElement?.dataset.tipId;
  
        if (!tipId) {
          console.error('Tip ID not found on element:', tipElement);
          return;
        }
  
        try {
          const response = await fetch('/toggle-bookmark/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: `tip_id=${tipId}`
          });
  
          const data = await response.json();
          if (data.success) {
            // Toggle the bookmarked state
            button.classList.toggle('bookmarked');
            console.log(`Bookmark toggled for tip ${tipId}: ${data.bookmarked}, Class: ${button.className}`)
          } else {
            console.error('Bookmark toggle failed:', data.error);
          }
        } catch (error) {
          console.error('Error toggling bookmark:', error);
        }
      });
    });
  }