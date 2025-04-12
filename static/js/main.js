// main.js: Entry point for Tipster Arena's frontend, handling page-specific and shared module initialization

// Utility function to get the current page path
function getCurrentPage() {
  return window.location.pathname;
}

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function () {
  console.log('DOM fully loaded');
  console.log('Current page:', getCurrentPage());

  const page = getCurrentPage();

  // Async IIFE to handle module imports and initialization
  (async () => {
    // Shared utilities loaded on all pages
    let upcomingEventsModule;
    try {
      const sharedModules = await Promise.all([
        import('./config.js').catch(error => {
          console.error('Failed to load config.js:', error);
          return null;
        }),
        import('./pages/nav.js').then(module => {
          module.setupNavigation();
          return module;
        }).catch(error => {
          console.error('Failed to load nav.js:', error);
          return null;
        }),
        import('./pages/upcoming-events.js').then(module => {
          console.log('Successfully loaded upcoming-events.js for shared modules');
          module.initCarousel(); // Calls getDynamicEvents
          module.attachFollowButtonListeners();
          upcomingEventsModule = module; // Store for reuse
          return module;
        }).catch(error => {
          console.error('Failed to load upcoming-events.js:', error);
          throw error; // Rethrow to catch in outer block
        }),
        import('./pages/search.js').then(module => {
          module.setupSearch();
          return module;
        }).catch(error => {
          console.error('Failed to load search.js:', error);
          return null;
        }),
      ]);
    } catch (error) {
      console.error('Error loading shared modules:', error);
      return; // Exit to prevent further errors
    }

    // Page-specific script loading
    try {
      if (page === '/' || page === '/home/') {
        await Promise.all([
          import('./pages/post.js').then(module => {
            module.setupCentralFeedPost();
            module.setupPostModal();
          }).catch(error => console.error('Failed to load post.js:', error)),
          import('./pages/trending-tips.js').then(module => {
            module.init();
          }).catch(error => console.error('Failed to load trending-tips.js:', error)),
          import('./tips.js').then(module => {
            module.setupTipInteractions();
            module.setupReplyModal();
          }).catch(error => console.error('Failed to load tips.js:', error)),
          import('./pages/bookmarks.js').then(module => {
            module.setupBookmarkInteractions();
          }).catch(error => console.error('Failed to load bookmarks.js:', error)),
          Promise.resolve(upcomingEventsModule).then(async module => {
            if (!module) throw new Error('upcoming-events.js not loaded');
            module.setupShowMoreButtons();
            const dynamicEvents = await module.getDynamicEvents();

            const footballEventsElement = document.getElementById('football-events');
            if (footballEventsElement) {
              const footballEvents = dynamicEvents.football || [];
              const footballHtml = await module.formatFootballList(footballEvents, 'football', false);
              footballEventsElement.innerHTML = footballHtml || '<p>No upcoming events available.</p>';
            }

            const golfEventsElement = document.getElementById('golf-events');
            if (golfEventsElement) {
              const golfEvents = dynamicEvents.golf || [];
              const golfHtml = await module.formatGolfList(golfEvents, 'golf', false);
              golfEventsElement.innerHTML = golfHtml || '<p>No upcoming events available.</p>';
            }

            const tennisEventsElement = document.getElementById('tennis-events');
            if (tennisEventsElement) {
              const tennisEvents = dynamicEvents.tennis || [];
              const tennisHtml = await module.formatTennisList(tennisEvents, 'tennis', false);
              tennisEventsElement.innerHTML = tennisHtml || '<p>No upcoming tournaments available.</p>';
            }

            const horseRacingEventsElement = document.getElementById('horse-racing-events');
            if (horseRacingEventsElement) {
              const horseRacingEvents = dynamicEvents.horse_racing || [];
              const horseRacingHtml = await module.formatHorseRacingList(horseRacingEvents, 'horse_racing', false);
              horseRacingEventsElement.innerHTML = horseRacingHtml || '<p>No upcoming races available.</p>';
            }
          }).catch(error => console.error('Error in upcoming-events for home:', error)),
          import('./pages/golf-events.js').then(module => {
            module.setupLeaderboardUpdates();
          }).catch(error => console.error('Failed to load golf-events.js:', error)),
        ]);
      }

      if (page.includes('/explore/')) {
        await Promise.all([
          import('./pages/post.js').then(module => {
            module.setupCentralFeedPost();
            module.setupPostModal();
          }),
          import('./pages/trending-tips.js').then(module => module.init()),
          import('./tips.js').then(module => {
            module.setupTipInteractions();
            module.setupReplyModal();
          }),
          import('./pages/bookmarks.js').then(module => module.setupBookmarkInteractions()),
          Promise.resolve(upcomingEventsModule).then(async module => {
            if (!module) throw new Error('upcoming-events.js not loaded');
            module.setupShowMoreButtons();
            const dynamicEvents = await module.getDynamicEvents();

            const footballEventsElement = document.getElementById('football-events');
            if (footballEventsElement) {
              const footballEvents = dynamicEvents.football || [];
              const footballHtml = await module.formatFootballList(footballEvents, 'football', false);
              footballEventsElement.innerHTML = footballHtml || '<p>No upcoming events available.</p>';
            }

            const golfEventsElement = document.getElementById('golf-events');
            if (golfEventsElement) {
              const golfEvents = dynamicEvents.golf || [];
              const golfHtml = await module.formatGolfList(golfEvents, 'golf', false);
              golfEventsElement.innerHTML = golfHtml || '<p>No upcoming events available.</p>';
            }

            const tennisEventsElement = document.getElementById('tennis-events');
            if (tennisEventsElement) {
              const tennisEvents = dynamicEvents.tennis || [];
              const tennisHtml = await module.formatTennisList(tennisEvents, 'tennis', false);
              tennisEventsElement.innerHTML = tennisHtml || '<p>No upcoming tournaments available.</p>';
            }

            const horseRacingEventsElement = document.getElementById('horse-racing-events');
            if (horseRacingEventsElement) {
              const horseRacingEvents = dynamicEvents.horse_racing || [];
              const horseRacingHtml = await module.formatHorseRacingList(horseRacingEvents, 'horse_racing', false);
              horseRacingEventsElement.innerHTML = horseRacingHtml || '<p>No upcoming races available.</p>';
            }
          }),
          import('./pages/golf-events.js').then(module => module.setupLeaderboardUpdates()),
        ]).catch(error => console.error('Error loading scripts for explore page:', error));
      }

      if (page.includes('/profile/')) {
        await Promise.all([
          import('./pages/profile.js').then(module => module.setupProfileEditing()),
          import('./pages/post.js').then(module => {
            module.setupPostModal();
          }),
          import('./tips.js').then(module => {
            module.setupTipInteractions();
            module.setupReplyModal();
          }),
          import('./pages/bookmarks.js').then(module => module.setupBookmarkInteractions()),
          Promise.resolve(upcomingEventsModule).then(async module => {
            if (!module) throw new Error('upcoming-events.js not loaded');
            module.setupShowMoreButtons();
            const dynamicEvents = await module.getDynamicEvents();

            const footballEventsElement = document.getElementById('football-events');
            if (footballEventsElement) {
              const footballEvents = dynamicEvents.football || [];
              const footballHtml = await module.formatFootballList(footballEvents, 'football', false);
              footballEventsElement.innerHTML = footballHtml || '<p>No upcoming events available.</p>';
            }

            const golfEventsElement = document.getElementById('golf-events');
            if (golfEventsElement) {
              const golfEvents = dynamicEvents.golf || [];
              const golfHtml = await module.formatGolfList(golfEvents, 'golf', false);
              golfEventsElement.innerHTML = golfHtml || '<p>No upcoming events available.</p>';
            }

            const tennisEventsElement = document.getElementById('tennis-events');
            if (tennisEventsElement) {
              const tennisEvents = dynamicEvents.tennis || [];
              const tennisHtml = await module.formatTennisList(tennisEvents, 'tennis', false);
              tennisEventsElement.innerHTML = tennisHtml || '<p>No upcoming tournaments available.</p>';
            }

            const horseRacingEventsElement = document.getElementById('horse-racing-events');
            if (horseRacingEventsElement) {
              const horseRacingEvents = dynamicEvents.horse_racing || [];
              const horseRacingHtml = await module.formatHorseRacingList(horseRacingEvents, 'horse_racing', false);
              horseRacingEventsElement.innerHTML = horseRacingHtml || '<p>No upcoming races available.</p>';
            }
          }),
          import('./pages/golf-events.js').then(module => module.setupLeaderboardUpdates()),
        ]).catch(error => console.error('Error loading scripts for profile page:', error));
      }

      if (page.includes('/sport/')) {
        await Promise.all([
          import('./pages/post.js').then(module => {
            module.setupCentralFeedPost();
            module.setupPostModal();
          }),
          import('./tips.js').then(module => {
            module.setupTipInteractions();
            module.setupReplyModal();
          }),
          import('./pages/bookmarks.js').then(module => module.setupBookmarkInteractions()),
          Promise.resolve(upcomingEventsModule).then(async module => {
            if (!module) throw new Error('upcoming-events.js not loaded');
            module.setupShowMoreButtons();
            const dynamicEvents = await module.getDynamicEvents();

            const footballEventsElement = document.getElementById('football-events');
            if (footballEventsElement) {
              const footballEvents = dynamicEvents.football || [];
              const footballHtml = await module.formatFootballList(footballEvents, 'football', false);
              footballEventsElement.innerHTML = footballHtml || '<p>No upcoming events available.</p>';
            }

            const golfEventsElement = document.getElementById('golf-events');
            if (golfEventsElement) {
              const golfEvents = dynamicEvents.golf || [];
              const golfHtml = await module.formatGolfList(golfEvents, 'golf', false);
              golfEventsElement.innerHTML = golfHtml || '<p>No upcoming events available.</p>';
            }

            const tennisEventsElement = document.getElementById('tennis-events');
            if (tennisEventsElement) {
              const tennisEvents = dynamicEvents.tennis || [];
              const tennisHtml = await module.formatTennisList(tennisEvents, 'tennis', false);
              tennisEventsElement.innerHTML = tennisHtml || '<p>No upcoming tournaments available.</p>';
            }

            const horseRacingEventsElement = document.getElementById('horse-racing-events');
            if (horseRacingEventsElement) {
              const horseRacingEvents = dynamicEvents.horse_racing || [];
              const horseRacingHtml = await module.formatHorseRacingList(horseRacingEvents, 'horse_racing', false);
              horseRacingEventsElement.innerHTML = horseRacingHtml || '<p>No upcoming races available.</p>';
            }
          }),
          import('./pages/golf-events.js').then(module => module.setupLeaderboardUpdates()),
        ]).catch(error => console.error('Error loading scripts for sports page:', error));
      }

      if (page === '/bookmarks/') {
        await Promise.all([
          import('./pages/bookmarks.js').then(module => module.setupBookmarkInteractions()),
          import('./tips.js').then(module => {
            module.setupTipInteractions();
            module.setupReplyModal();
          }),
          Promise.resolve(upcomingEventsModule).then(async module => {
            if (!module) throw new Error('upcoming-events.js not loaded');
            const dynamicEvents = await module.getDynamicEvents();

            const footballEventsElement = document.getElementById('football-events');
            if (footballEventsElement) {
              const footballEvents = dynamicEvents.football || [];
              const footballHtml = await module.formatFootballList(footballEvents, 'football', false);
              footballEventsElement.innerHTML = footballHtml || '<p>No upcoming events available.</p>';
            }

            const golfEventsElement = document.getElementById('golf-events');
            if (golfEventsElement) {
              const golfEvents = dynamicEvents.golf || [];
              const golfHtml = await module.formatGolfList(golfEvents, 'golf', false);
              golfEventsElement.innerHTML = golfHtml || '<p>No upcoming events available.</p>';
            }

            const tennisEventsElement = document.getElementById('tennis-events');
            if (tennisEventsElement) {
              const tennisEvents = dynamicEvents.tennis || [];
              const tennisHtml = await module.formatTennisList(tennisEvents, 'tennis', false);
              tennisEventsElement.innerHTML = tennisHtml || '<p>No upcoming tournaments available.</p>';
            }

            const horseRacingEventsElement = document.getElementById('horse-racing-events');
            if (horseRacingEventsElement) {
              const horseRacingEvents = dynamicEvents.horse_racing || [];
              const horseRacingHtml = await module.formatHorseRacingList(horseRacingEvents, 'horse_racing', false);
              horseRacingEventsElement.innerHTML = horseRacingHtml || '<p>No upcoming races available.</p>';
            }
          }),
        ]).catch(error => console.error('Error loading scripts for bookmarks page:', error));
      }

      if (page === '/messages/') {
        console.log('Importing messages.js for messages page');
        await import('./pages/messages.js')
          .then(module => {
            console.log('messages.js loaded successfully');
            module.init();
          })
          .catch(error => console.error('Error loading scripts for messages page:', error));
      }

      // Trending Tips (shared across pages)
      const trendingTipsList = document.querySelector('.trending-tips-list');
      if (trendingTipsList) {
        fetch('/api/trending-tips/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
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

      // Who to Follow (shared across pages, including home)
      const followList = document.querySelector('.follow-list');
      if (followList) {
        fetch('/api/suggested-users/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        })
        .then(response => response.json())
        .then(data => {
          followList.innerHTML = '';
          if (data.users && data.users.length > 0) {
            const limitedUsers = data.users.slice(0, 3);
            limitedUsers.forEach(user => {
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
            Promise.resolve(upcomingEventsModule).then(module => {
              if (module) module.attachFollowButtonListeners();
            });
          } else {
            followList.innerHTML = '<p>No suggested tipsters available.</p>';
          }
        })
        .catch(error => {
          console.error('Error fetching suggested users:', error);
          followList.innerHTML = '<p>Error loading suggestions.</p>';
        });
      }
    } catch (error) {
      console.error('Error in async IIFE:', error);
    }
  })();
});