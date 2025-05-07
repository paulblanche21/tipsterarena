// main.js
function getCurrentPage() {
  return window.location.pathname;
}

// Import trending tips
import trendingTips from './pages/trending-tips.js';

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
        module.initShowMore();
        return module;
      }).catch(error => {
        console.error('Failed to load follow.js:', error);
        return null;
      }),
    ]);

    const upcomingEventsModule = sharedModules[2];

    if (page === '/' || page === '/home/') {
      await Promise.all([
        import('./pages/post.js').then(module => {
          module.setupCentralFeedPost();
          module.setupPostModal();
        }),
        import('./pages/trending-tips.js').then(module => module.default.init()),
        import('./tips.js').then(module => {
          module.setupTipInteractions();
          module.setupReplyModal();
        }),
        import('./pages/bookmarks.js').then(module => module.setupBookmarkInteractions()),
        import('./pages/golf-events.js').then(module => {
          // Only call for golf-specific pages if needed
        }),
      ]);
    }

    if (page.includes('/explore/')) {
      await Promise.all([
        import('./pages/post.js').then(module => {
          module.setupCentralFeedPost();
          module.setupPostModal();
        }),
        import('./pages/trending-tips.js').then(module => module.default.init()),
        import('./tips.js').then(module => {
          module.setupTipInteractions();
          module.setupReplyModal();
        }),
        import('./pages/bookmarks.js').then(module => module.setupBookmarkInteractions()),
        import('./pages/golf-events.js').then(module => {
          // Only call for golf-specific pages if needed
        }),
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
        import('./pages/golf-events.js').then(module => {
          // Only call for golf-specific pages if needed
        }),
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
        import('./pages/golf-events.js').then(module => {
          if (page.includes('/sport/golf/')) {
            module.setupLeaderboardUpdates();
          }
        }),
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

    // Initialize trending tips if the element exists
    const trendingTipsList = document.querySelector('.trending-tips-list');
    if (trendingTipsList) {
        console.log('Initializing trending tips...');
        trendingTips.init();
    }

    // Who to Follow
    const followList = document.querySelector('.follow-list');
    if (followList) {
      try {
        const response = await fetch('/api/suggested-users/', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        });
        if (!response.ok) {
          console.warn(`Failed to fetch suggested users: ${response.status}`);
          if (response.status === 401) {
            followList.innerHTML = '<p><a href="/login/">Please log in</a> to view suggested users.</p>';
          } else {
            followList.innerHTML = '<p>Unable to load suggestions.</p>';
          }
        } else {
          const contentType = response.headers.get('content-type');
          if (!contentType || !contentType.includes('application/json')) {
            console.warn('Received non-JSON response from /api/suggested-users/');
            followList.innerHTML = '<p>Unable to load suggestions.</p>';
          } else {
            const data = await response.json();
            if (!data.success) {
              const errorMessage = data.error || 'An unexpected error occurred';
              console.warn(`Suggested users error: ${errorMessage}`);
              followList.innerHTML = `<p>${errorMessage === 'User not authenticated' ? '<a href="/login/">Please log in</a> to view suggested users.' : 'Unable to load suggestions: ' + errorMessage}</p>`;
            } else {
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
            }
          }
        }
      } catch (error) {
        console.error('Error fetching suggested users:', error);
        followList.innerHTML = '<p>Unable to load suggestions.</p>';
      }
    }
  } catch (error) {
    console.error('Error initializing:', error);
  }
});