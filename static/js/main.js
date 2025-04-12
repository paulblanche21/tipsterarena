// main.js: Entry point for Tipster Arena's frontend

function getCurrentPage() {
  return window.location.pathname;
}

document.addEventListener('DOMContentLoaded', async () => {
  console.log('DOM loaded, page:', getCurrentPage());
  const page = getCurrentPage();

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
        console.log('Loaded upcoming-events.js');
        module.initButtons();
        return module;
      }).catch(error => {
        console.error('Failed to load upcoming-events.js:', error);
        throw error;
      }),
      import('./pages/search.js').then(module => {
        module.setupSearch();
        return module;
      }).catch(error => {
        console.error('Failed to load search.js:', error);
        return null;
      }),
      import('./follow.js').then(module => {
        console.log('Loaded follow.js');
        module.attachFollowButtonListeners();
        return module;
      }).catch(error => {
        console.error('Failed to load follow.js:', error);
        return null;
      }),
    ]);

    const upcomingEventsModule = sharedModules[2]; // Store for reuse

    if (page === '/' || page === '/home/') {
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
        import('./pages/golf-events.js').then(module => module.setupLeaderboardUpdates()),
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
        import('./pages/golf-events.js').then(module => module.setupLeaderboardUpdates()),
      ]);
    }

    if (page.includes('/profile/')) {
      await Promise.all([
        import('./pages/profile.js').then(module => module.setupProfileEditing()),
        import('./pages/post.js').then(module => module.setupPostModal()),
        import('./tips.js').then(module => {
          module.setupTipInteractions();
          module.setupReplyModal();
        }),
        import('./pages/bookmarks.js').then(module => module.setupBookmarkInteractions()),
        import('./pages/golf-events.js').then(module => module.setupLeaderboardUpdates()),
      ]);
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
        import('./pages/golf-events.js').then(module => module.setupLeaderboardUpdates()),
      ]);
    }

    if (page === '/bookmarks/') {
      await Promise.all([
        import('./pages/bookmarks.js').then(module => module.setupBookmarkInteractions()),
        import('./tips.js').then(module => {
          module.setupTipInteractions();
          module.setupReplyModal();
        }),
      ]);
    }

    if (page === '/messages/') {
      await import('./pages/messages.js').then(module => module.init());
    }

    // Trending Tips
    const trendingTipsList = document.querySelector('.trending-tips-list');
    if (trendingTipsList) {
      fetch('/api/trending-tips/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
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

    // Who to Follow
    const followList = document.querySelector('.follow-list');
    if (followList) {
      fetch('/api/suggested-users/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
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
    console.error('Error initializing:', error);
  }
});