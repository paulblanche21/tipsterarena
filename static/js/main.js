// main.js
function getCurrentPage() {
  return window.location.pathname;
}

// Add loading state management
document.documentElement.classList.add('js-loading');
window.addEventListener('load', function() {
  document.documentElement.classList.remove('js-loading');
  document.body.classList.add('loaded');
});

// Import notifications
import { setupNotifications } from './notifications.js';
import { attachFollowButtonListeners } from './follow.js';

document.addEventListener('DOMContentLoaded', async () => {
  console.log('DOM loaded, page:', getCurrentPage());
  const page = getCurrentPage();

  // Initialize WebSocket notifications
  setupNotifications((notification) => {
    console.log('Received notification via WebSocket:', notification);
    // TODO: Update notification badge or DOM here
  });

  // Initialize sidebar components
  await import('./pages/sidebar.js').then(module => {
    module.initSuggestedUsersModal();
    new module.TrendingTips();
  });

  // Initialize upcoming events if the element exists
  const upcomingEventsCard = document.querySelector('.upcoming-events-card');
  if (upcomingEventsCard) {
    await import('./pages/upcoming-events.js').then(module => {
      new module.UpcomingEvents();
    });
  }

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
      import('./pages/search.js').then(module => {
        module.setupSearch();
        return module;
      }).catch(error => {
        console.error('Failed to load search.js:', error);
        return null;
      }),
      import('./follow.js').then(module => {
        module.attachFollowButtonListeners();
        return module;
      }).catch(error => {
        console.error('Failed to load follow.js:', error);
        return null;
      }),
    ]);

    if (page === '/' || page === '/home/') {
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
      ]);
    }

    if (page.includes('/explore/')) {
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

    // Messages page is initialized in the template's extra_js block
    // No need to initialize it here to avoid double initialization

    // Who to Follow
    const followList = document.querySelector('.follow-list');
    if (followList) {
      try {
        const response = await fetch('/api/suggested-users/?limit=10', {
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
                data.users.forEach(user => {
                  followList.innerHTML += `
                    <div class="follow-item">
                      <img src="${user.avatar_url || '/static/img/default-avatar.png'}" 
                           alt="${user.username}" 
                           class="follow-avatar"
                           onerror="this.onerror=null; this.src='/static/img/default-avatar.png';">
                      <div class="follow-details">
                        <a href="${user.profile_url}" class="follow-username">@${user.username}</a>
                        <p class="follow-bio">${user.bio || 'No bio'}</p>
                      </div>
                      <button class="follow-btn" data-username="${user.username}">Follow</button>
                    </div>
                  `;
                });
                // Reattach follow button listeners after adding new buttons
                attachFollowButtonListeners();
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
    console.error('Error initializing shared modules:', error);
  }
});