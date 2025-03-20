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
            // Fetch trending tips dynamically
            content.innerHTML = `
              <div class="follow-card">
                <h2>Trending Tips</h2>
                <p>Hot tips for today’s big tournaments in Tipster Arena:</p>
                <div class="tip-list" id="trending-tips-list">
                  <p>Loading trending tips...</p>
                </div>
                <a href="#" class="show-less" data-target="${target}">Show less</a>
              </div>
            `;
            fetch('/api/trending-tips/', {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json'
              }
            })
            .then(response => response.json())
            .then(data => {
              const trendingTipsList = document.getElementById('trending-tips-list');
              trendingTipsList.innerHTML = '';
              if (data.trending_tips && data.trending_tips.length > 0) {
                data.trending_tips.forEach(tip => {
                  trendingTipsList.innerHTML += `
                    <div class="tip-item">
                      <img src="${tip.avatar_url}" alt="${tip.username} Avatar" class="tip-avatar">
                      <div class="tip-details">
                        <a href="${tip.profile_url}" class="tip-username">@${tip.handle}</a>
                        <p>${tip.text}</p>
                        <span class="tip-likes"><i class="fas fa-heart"></i> ${tip.likes}</span>
                      </div>
                    </div>
                  `;
                });
              } else {
                trendingTipsList.innerHTML = '<p>No trending tips available.</p>';
              }
            })
            .catch(error => {
              console.error('Error fetching trending tips:', error);
              document.getElementById('trending-tips-list').innerHTML = '<p>Error loading trending tips.</p>';
            });
            break;

          case 'who-to-follow':
            // Fetch suggested users dynamically (already implemented, but let's refine it)
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