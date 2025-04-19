function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

export function setupSearch() {
  const searchBar = document.querySelector('.search-input');
  const searchResults = document.querySelector('.search-results');

  if (!searchBar || !searchResults) {
    console.warn('Search input or results container not found:', { searchBar, searchResults });
    return;
  }

  let csrfToken;
  import('./utils.js')
    .then(module => {
      csrfToken = module.getCSRFToken();
    })
    .catch(error => {
      console.error('Error loading CSRF token:', error);
      csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    });

  const performSearch = debounce(async (query) => {
    if (!query) {
      console.log('Empty query, clearing results');
      searchResults.innerHTML = '';
      searchResults.style.display = 'none';
      return;
    }

    try {
      console.log('Fetching search results for query:', query);
      const response = await fetch(`/search/?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Search response:', data);

      if (data.success) {
        searchResults.innerHTML = '';
        console.log('Cleared search results container');

        if (data.users && data.users.length > 0) {
          data.users.forEach(user => {
            const userHtml = `
              <div class="search-result-item">
                <img src="${user.avatar_url}" alt="${user.username}" class="search-avatar">
                <div class="search-details">
                  <a href="${user.profile_url}" class="search-username">${user.handle}</a>
                </div>
              </div>
            `;
            searchResults.innerHTML += userHtml;
            console.log('Added user result:', user.username);
          });
        }

        if (data.tips && data.tips.length > 0) {
          data.tips.forEach(tip => {
            const tipHtml = `
              <div class="search-result-item">
                <img src="${tip.avatar_url}" alt="${tip.username}" class="search-avatar">
                <div class="search-details">
                  <a href="${tip.profile_url}" class="search-username">${tip.handle}</a>
                  <p class="search-tip-text">${tip.text}</p>
                </div>
              </div>
            `;
            searchResults.innerHTML += tipHtml;
            console.log('Added tip result:', tip.id);
          });
        }

        if (!data.users.length && !data.tips.length) {
          searchResults.innerHTML = '<p>No results found.</p>';
          console.log('No results to display');
        }

        console.log('Final search results HTML:', searchResults.innerHTML);
        searchResults.style.display = 'block';
        console.log('Set search results display to block');
      } else {
        searchResults.innerHTML = `<p>Error: ${data.error}</p>`;
        searchResults.style.display = 'block';
        console.log('Displayed error message');
      }
    } catch (error) {
      console.error('Error fetching search results:', error);
      searchResults.innerHTML = '<p>Error loading search results.</p>';
      searchResults.style.display = 'block';
    }
  }, 300);

  searchBar.addEventListener('input', (e) => {
    console.log('Search input triggered:', e.target.value);
    const query = e.target.value.trim();
    performSearch(query);
  });

  document.addEventListener('click', (e) => {
    const eventCard = e.target.closest('.event-card, .tennis-card, .golf-card, .horse-racing-card');
    const tipAction = e.target.closest('.tip-action');
    const categoryButton = e.target.closest('.event-btn'); // New check for category buttons
    
    console.log('Click event target:', e.target);
    console.log('Closest card:', eventCard ? eventCard.className : 'None');
    console.log('Closest tip action:', tipAction ? tipAction.className : 'None');
    console.log('Closest category button:', categoryButton ? categoryButton.className : 'None');
    
    if (!searchBar.contains(e.target) && !searchResults.contains(e.target) && !eventCard && !tipAction && !categoryButton) {
      console.log('Click outside search bar, results, cards, tip actions, and category buttons, hiding results');
      searchResults.style.display = 'none';
    } else {
      console.log('Click inside search bar, results, card, tip action, or category button, keeping results visible');
    }
  });

  document.addEventListener('click', (e) => {
    const card = e.target.closest('.event-card, .tennis-card, .golf-card, .horse-racing-card');
    if (card) {
      console.log('Expandable card clicked:', card.className);
      const isExpanded = card.classList.contains('expanded');
      if (isExpanded) {
        card.classList.remove('expanded');
        console.log('Card collapsed');
      } else {
        card.classList.add('expanded');
        console.log('Card expanded');
      }
      e.stopPropagation();
    }
  });

  searchBar.addEventListener('focus', () => {
    if (searchBar.value.trim()) {
      console.log('Search bar focused, re-running search');
      performSearch(searchBar.value.trim());
    }
  });
}