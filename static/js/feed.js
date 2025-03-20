// feed.js
import { attachFollowButtonListeners } from './follow.js';
import { getEventList } from './upcoming-events.js';

export function setupShowMoreButtons() {
  const showMoreButtons = document.querySelectorAll('.show-more');
  console.log('Found show-more buttons:', showMoreButtons.length); // Debug log
  showMoreButtons.forEach(button => {
    button.addEventListener('click', async function(e) {
      e.preventDefault();
      console.log('Show more button clicked:', this.getAttribute('data-target')); // Debug log
      const target = this.getAttribute('data-target');
      const content = document.querySelector('.content');
      let previousUrl = window.location.pathname;

      try {
        const activeSlide = document.querySelector('.carousel-slide.active');
        const activeSport = activeSlide ? activeSlide.getAttribute('data-sport') : 'football';
        content.innerHTML = await getEventList(window.location.pathname, target, activeSport);

        switch (target) {
          case 'trending-tips':
            content.innerHTML = `
              <div class="follow-card">
                <h2>Trending Tips</h2>
                <p>Hot tips for today’s big tournaments in Tipster Arena:</p>
                <div class="tip-list">
                  <div class="tip-item">
                    <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                    <div class="tip-details">
                      <strong>User 1</strong> - Rory McIlroy to win The Players Championship (Odds: 10.0) - Likes: 150
                    </div>
                  </div>
                  <div class="tip-item">
                    <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                    <div class="tip-details">
                      <strong>User 2</strong> - Scottie Scheffler top 10 at Masters (Odds: 2.5) - Likes: 120
                    </div>
                  </div>
                </div>
                <a href="#" class="show-less" data-target="${target}">Show less</a>
              </div>
            `;
            break;
          case 'who-to-follow':
            content.innerHTML = `
              <div class="follow-card">
                <h2>Who to Follow</h2>
                <p>Suggested tipsters for you to follow in Tipster Arena:</p>
                <div class="follow-list" id="follow-list">
                  <p>Loading suggestions...</p>
                </div>
                <a href="#" class="show-less" data-target="${target}">Show less</a>
              </div>
            `;
            fetch('/api/suggested-users/', {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json'
              }
            })
            .then(response => response.json())
            .then(data => {
              const followList = document.getElementById('follow-list');
              followList.innerHTML = '';
              if (data.users && data.users.length > 0) {
                data.users.forEach(user => {
                  followList.innerHTML += `
                    <div class="follow-item">
                      <img src="${user.avatar_url}" alt="${user.username}" class="follow-avatar">
                      <div class="follow-details">
                        <a href="${user.profile_url}" class="follow-username">@${user.username}</a>
                        <p class="follow-bio">${user.bio}</p>
                      </div>
                      <button class="follow-btn" data-username="${user.username}">Follow</button>
                    </div>
                  `;
                });
                attachFollowButtonListeners();
              } else {
                followList.innerHTML = '<p>No suggestions available.</p>';
              }
            })
            .catch(error => {
              console.error('Error fetching suggested users:', error);
              document.getElementById('follow-list').innerHTML = '<p>Error loading suggestions.</p>';
            });
            break;
        }

        const showLessButtons = document.querySelectorAll('.show-less');
        showLessButtons.forEach(lessButton => {
          lessButton.addEventListener('click', function(e) {
            e.preventDefault();
            content.innerHTML = '';
            window.location.href = previousUrl;
          });
        });
      } catch (error) {
        console.error('Error handling show-more click:', error);
        content.innerHTML = '<p>Error loading events. Please try again later.</p>';
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupShowMoreButtons();
});