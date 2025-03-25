// static/js/main.js
function getCurrentPage() {
  return window.location.pathname;
}

document.addEventListener('DOMContentLoaded', async function() {
  console.log('DOM fully loaded');

  const page = getCurrentPage();

  // Load scripts for the home page
  if (page === '/' || page === '/home/') {
    Promise.all([
      import('./post.js').then(module => {
        module.setupCentralFeedPost();
        module.setupPostModal();
      }),
      import('./trending-tips.js').then(module => module.init()),
      import('./feed.js').then(module => module.setupShowMoreButtons()),
      import('./tips.js').then(module => {
        module.setupTipInteractions();
        module.setupReplyModal();
      }),
      import('./nav.js').then(module => module.setupNavigation()),
      import('./carousel.js').then(module => module.initCarousel()),
      import('./upcoming-events.js').then(module => {
        module.getDynamicEvents().then(dynamicEvents => {
          const footballEventsElement = document.getElementById('football-events');
          if (footballEventsElement) {
            const footballEvents = dynamicEvents.football || [];
            footballEventsElement.innerHTML = module.formatFootballList(footballEvents, 'football', false) || '<p>No upcoming events available.</p>';
          }

          const golfEventsElement = document.getElementById('golf-events');
          if (golfEventsElement) {
            const golfEvents = dynamicEvents.golf || [];
            golfEventsElement.innerHTML = module.formatGolfList(golfEvents, 'golf', false) || '<p>No upcoming events available.</p>';
          }

          const tennisEventsElement = document.getElementById('tennis-events');
          if (tennisEventsElement) {
            const tennisEvents = dynamicEvents.tennis || [];
            tennisEventsElement.innerHTML = module.formatTennisList(tennisEvents, 'tennis', false) || '<p>No upcoming tournaments available.</p>';
          }

          const horseRacingEventsElement = document.getElementById('horse-racing-events');
          if (horseRacingEventsElement) {
            const horseRacingEvents = dynamicEvents.horse_racing || [];
            horseRacingEventsElement.innerHTML = module.formatHorseRacingList(horseRacingEvents, 'horse_racing', false) || '<p>No upcoming races available.</p>';
          }
        });
      }),
      import('./golf-events.js').then(module => module.setupLeaderboardUpdates()),
      import('./follow.js').then(module => module.attachFollowButtonListeners())
    ]).catch(error => console.error('Error loading scripts for home page:', error));
  }

  // Load scripts for the explore page
  if (page.includes('/explore/')) {
    Promise.all([
      import('./post.js').then(module => {
        module.setupCentralFeedPost();
        module.setupPostModal();
      }),
      import('./trending-tips.js').then(module => module.init()),
      import('./feed.js').then(module => module.setupShowMoreButtons()),
      import('./tips.js').then(module => {
        module.setupTipInteractions();
        module.setupReplyModal();
      }),
      import('./nav.js').then(module => module.setupNavigation()),
      import('./carousel.js').then(module => module.initCarousel()),
      import('./upcoming-events.js').then(module => {
        module.getDynamicEvents().then(dynamicEvents => {
          const footballEventsElement = document.getElementById('football-events');
          if (footballEventsElement) {
            const footballEvents = dynamicEvents.football || [];
            footballEventsElement.innerHTML = module.formatFootballList(footballEvents, 'football', false) || '<p>No upcoming events available.</p>';
          }

          const golfEventsElement = document.getElementById('golf-events');
          if (golfEventsElement) {
            const golfEvents = dynamicEvents.golf || [];
            golfEventsElement.innerHTML = module.formatGolfList(golfEvents, 'golf', false) || '<p>No upcoming events available.</p>';
          }

          const tennisEventsElement = document.getElementById('tennis-events');
          if (tennisEventsElement) {
            const tennisEvents = dynamicEvents.tennis || [];
            tennisEventsElement.innerHTML = module.formatTennisList(tennisEvents, 'tennis', false) || '<p>No upcoming tournaments available.</p>';
          }

          const horseRacingEventsElement = document.getElementById('horse-racing-events');
          if (horseRacingEventsElement) {
            const horseRacingEvents = dynamicEvents.horse_racing || [];
            horseRacingEventsElement.innerHTML = module.formatHorseRacingList(horseRacingEvents, 'horse_racing', false) || '<p>No upcoming races available.</p>';
          }
        });
      }),
      import('./golf-events.js').then(module => module.setupLeaderboardUpdates()),
      import('./follow.js').then(module => module.attachFollowButtonListeners())
    ]).catch(error => console.error('Error loading scripts for explore page:', error));
  }

  // Load scripts for the profile page
  if (page.includes('/profile/')) {
    Promise.all([
      import('./profile.js').then(module => module.setupProfileEditing()),
      import('./follow.js').then(module => module.attachFollowButtonListeners()),
      import('./post.js').then(module => {
        // Skip setupCentralFeedPost since profile.html doesn't have a post box
        module.setupPostModal();
      }),
      import('./feed.js').then(module => module.setupShowMoreButtons()),
      import('./nav.js').then(module => module.setupNavigation()),
      import('./carousel.js').then(module => module.initCarousel()),
      import('./upcoming-events.js').then(module => {
        module.getDynamicEvents().then(dynamicEvents => {
          const footballEventsElement = document.getElementById('football-events');
          if (footballEventsElement) {
            const footballEvents = dynamicEvents.football || [];
            footballEventsElement.innerHTML = module.formatFootballList(footballEvents, 'football', false) || '<p>No upcoming events available.</p>';
          }

          const golfEventsElement = document.getElementById('golf-events');
          if (golfEventsElement) {
            const golfEvents = dynamicEvents.golf || [];
            golfEventsElement.innerHTML = module.formatGolfList(golfEvents, 'golf', false) || '<p>No upcoming events available.</p>';
          }

          const tennisEventsElement = document.getElementById('tennis-events');
          if (tennisEventsElement) {
            const tennisEvents = dynamicEvents.tennis || [];
            tennisEventsElement.innerHTML = module.formatTennisList(tennisEvents, 'tennis', false) || '<p>No upcoming tournaments available.</p>';
          }

          const horseRacingEventsElement = document.getElementById('horse-racing-events');
          if (horseRacingEventsElement) {
            const horseRacingEvents = dynamicEvents.horse_racing || [];
            horseRacingEventsElement.innerHTML = module.formatHorseRacingList(horseRacingEvents, 'horse_racing', false) || '<p>No upcoming races available.</p>';
          }
        });
      }),
      import('./golf-events.js').then(module => module.setupLeaderboardUpdates())
    ]).catch(error => console.error('Error loading scripts for profile page:', error));
  }

  // Load scripts for sports pages (e.g., /sport/football/, /sport/golf/)
  if (page.includes('/sport/')) {
    Promise.all([
      import('./post.js').then(module => {
        module.setupCentralFeedPost();
        module.setupPostModal();
      }),
      import('./feed.js').then(module => module.setupShowMoreButtons()),
      import('./tips.js').then(module => {
        module.setupTipInteractions();
        module.setupReplyModal();
      }),
      import('./nav.js').then(module => module.setupNavigation()),
      import('./carousel.js').then(module => module.initCarousel()),
      import('./upcoming-events.js').then(module => {
        module.getDynamicEvents().then(dynamicEvents => {
          const footballEventsElement = document.getElementById('football-events');
          if (footballEventsElement) {
            const footballEvents = dynamicEvents.football || [];
            footballEventsElement.innerHTML = module.formatFootballList(footballEvents, 'football', false) || '<p>No upcoming events available.</p>';
          }

          const golfEventsElement = document.getElementById('golf-events');
          if (golfEventsElement) {
            const golfEvents = dynamicEvents.golf || [];
            golfEventsElement.innerHTML = module.formatGolfList(golfEvents, 'golf', false) || '<p>No upcoming events available.</p>';
          }

          const tennisEventsElement = document.getElementById('tennis-events');
          if (tennisEventsElement) {
            const tennisEvents = dynamicEvents.tennis || [];
            tennisEventsElement.innerHTML = module.formatTennisList(tennisEvents, 'tennis', false) || '<p>No upcoming tournaments available.</p>';
          }

          const horseRacingEventsElement = document.getElementById('horse-racing-events');
          if (horseRacingEventsElement) {
            const horseRacingEvents = dynamicEvents.horse_racing || [];
            horseRacingEventsElement.innerHTML = module.formatHorseRacingList(horseRacingEvents, 'horse_racing', false) || '<p>No upcoming races available.</p>';
          }
        });
      }),
      import('./golf-events.js').then(module => module.setupLeaderboardUpdates()),
      import('./follow.js').then(module => module.attachFollowButtonListeners())
    ]).catch(error => console.error('Error loading scripts for sports page:', error));
  }

  // Load scripts for the messages page
  if (page === '/messages/') {
    import('./messages.js').then(module => module.init())
      .catch(error => console.error('Error loading scripts for messages page:', error));
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
        import('./follow.js').then(module => module.attachFollowButtonListeners());
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