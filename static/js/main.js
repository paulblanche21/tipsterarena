// main.js
import { attachFollowButtonListeners } from './follow.js';
import { setupShowMoreButtons } from './feed.js';
import { setupCentralFeedPost, setupPostModal } from './post.js';
import { setupTipInteractions, setupReplyModal } from './tips.js'; // Kept setupReplyModal import for flexibility
import { setupNavigation } from './nav.js';
import { setupProfileEditing } from './profile.js';
import { initCarousel } from './carousel.js';
import { setupLeaderboardUpdates } from './golf-events.js';
import { getDynamicEvents, getEventList, formatFootballList, formatGolfList, formatTennisList, formatHorseRacingList } from './upcoming-events.js';

document.addEventListener('DOMContentLoaded', async function() {
  console.log('DOM fully loaded');

  attachFollowButtonListeners();
  setupShowMoreButtons();
  setupCentralFeedPost();
  setupPostModal();
  setupTipInteractions(); // This now handles setupReplyModal internally
  setupNavigation();
  setupProfileEditing();
  initCarousel();

  // Only initialize carousel if the container exists
  if (document.querySelector('.carousel-container')) {
    initCarousel();
  }

  const dynamicEvents = await getDynamicEvents();

  // Sidebar population for upcoming events
  const footballEventsElement = document.getElementById('football-events');
  if (footballEventsElement) {
    const footballEvents = dynamicEvents.football || [];
    footballEventsElement.innerHTML = await formatFootballList(footballEvents, 'football', false) || '<p>No upcoming events available.</p>';
  }

  const golfEventsElement = document.getElementById('golf-events');
  if (golfEventsElement) {
    const golfEvents = dynamicEvents.golf || [];
    golfEventsElement.innerHTML = await formatGolfList(golfEvents, 'golf', false) || '<p>No upcoming events available.</p>';
    setupLeaderboardUpdates();
  }

  const tennisEventsElement = document.getElementById('tennis-events');
  if (tennisEventsElement) {
    const tennisEvents = dynamicEvents.tennis || [];
    tennisEventsElement.innerHTML = await formatTennisList(tennisEvents, 'tennis', false) || '<p>No upcoming tournaments available.</p>';
  }

  const horseRacingEventsElement = document.getElementById('horse-racing-events');
  if (horseRacingEventsElement) {
    const horseRacingEvents = dynamicEvents.horse_racing || [];
    horseRacingEventsElement.innerHTML = await formatHorseRacingList(horseRacingEvents, 'horse_racing', false) || '<p>No upcoming races available.</p>';
  }

  // Populate Trending Tips dynamically on page load
  const trendingTipsList = document.querySelector('.trending-tips-list');
  if (trendingTipsList) {
    fetch('/api/trending-tips/', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => response.json())
    .then(data => {
      trendingTipsList.innerHTML = '';
      if (data.trending_tips && data.trending_tips.length > 0) {
        data.trending_tips.forEach(tip => {
          trendingTipsList.innerHTML += `
            <div class="trending-tip">
              <img src="${tip.avatar_url}" alt="${tip.username} Avatar" class="tip-avatar">
              <div class="tip-details">
                <a href="${tip.profile_url}" class="tip-username"><strong>@${tip.handle}</strong></a>
                <p class="tip-text">${tip.text}</p>
              </div>
              <span class="tip-likes"><i class="fas fa-heart"></i> ${tip.likes}</span>
            </div>
          `;
        });
      } else {
        trendingTipsList.innerHTML = '<p>No trending tips available.</p>';
      }
    })
    .catch(error => {
      console.error('Error fetching trending tips:', error);
      trendingTipsList.innerHTML = '<p>Error loading trending tips.</p>';
    });
  }

  // Populate Who to Follow dynamically on page load
  const followList = document.querySelector('.follow-list');
  if (followList) {
    fetch('/api/suggested-users/', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => response.json())
    .then(data => {
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
        followList.innerHTML = '<p>No suggested tipsters available.</p>';
      }
    })
    .catch(error => {
      console.error('Error fetching suggested users:', error);
      followList.innerHTML = '<p>Error loading suggestions.</p>';
    });
  }
});