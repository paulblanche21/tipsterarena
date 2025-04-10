// upcoming-events.js

import { getCSRFToken } from './utils.js';
import { fetchEvents as fetchFootballEvents, formatEventList as formatFootballList, formatEventTable as formatFootballTable } from './football-events.js';
import { fetchEvents as fetchTennisEvents, formatEventList as formatTennisList, formatEventTable as formatTennisTable } from './tennis-events.js';
import { fetchEvents as fetchGolfEvents, formatEventList as formatGolfList, fetchLeaderboard } from './golf-events.js';
import { fetchMeetingList as fetchHorseRacingMeetings, fetchEvents as fetchHorseRacingEvents, formatEventList as formatHorseRacingList, formatMeetingList as formatHorseRacingMeetingList } from './horse-racing-events.js';

const SPORT_CONFIG = {
  football: [
    { sport: "soccer", league: "eng.1", icon: "⚽", name: "Premier League", priority: 1 },
    { sport: "soccer", league: "esp.1", icon: "⚽", name: "La Liga", priority: 2 },
    { sport: "soccer", league: "ita.1", icon: "⚽", name: "Serie A", priority: 3 },
    { sport: "soccer", league: "fra.1", icon: "⚽", name: "Ligue 1", priority: 4 },
    { sport: "soccer", league: "uefa.champions", icon: "⚽", name: "Champions League", priority: 5 },
    { sport: "soccer", league: "uefa.europa", icon: "⚽", name: "Europa League", priority: 6 },
    { sport: "soccer", league: "eng.fa", icon: "⚽", name: "FA Cup", priority: 7 },
    { sport: "soccer", league: "eng.2", icon: "⚽", name: "EFL Championship", priority: 8 },
    { sport: "soccer", league: "por.1", icon: "⚽", name: "Primeira Liga", priority: 9 },
    { sport: "soccer", league: "ned.1", icon: "⚽", name: "Eredivisie", priority: 10 },
    { sport: "soccer", league: "nir.1", icon: "⚽", name: "Irish League", priority: 11 },
    { sport: "soccer", league: "usa.1", icon: "⚽", name: "MLS", priority: 12 },
    { sport: "soccer", league: "sco.1", icon: "⚽", name: "Scottish Premiership", priority: 13 }
  ],
  golf: [
    { sport: "golf", league: "pga", icon: "⛳", name: "PGA Tour" },
    { sport: "golf", league: "lpga", icon: "⛳", name: "LPGA Tour" }
  ],
  tennis: [
    { sport: "tennis", league: "atp", icon: "🎾", name: "ATP Tour" }
  ],
  horse_racing: [
    { sport: "horse_racing", league: "uk_irish", icon: "🏇", name: "UK & Irish Racing" }
  ]
};

const SPORT_MODULES = {
  football: { fetch: fetchFootballEvents, format: formatFootballList },
  golf: { fetch: fetchGolfEvents, format: formatGolfList },
  tennis: { fetch: fetchTennisEvents, format: formatTennisList },
  horse_racing: { fetch: fetchHorseRacingEvents, format: formatHorseRacingList }
};

// Use formatMeetingList for sidebar rendering
const FORMATTERS = {
  football: formatFootballList,
  golf: formatGolfList,
  tennis: formatTennisList,
  horse_racing: formatHorseRacingMeetingList
};

let globalEvents = {};

export async function getDynamicEvents() {
  const events = {};
  for (const sportKey of Object.keys(SPORT_CONFIG)) {
    const sportConfigs = SPORT_CONFIG[sportKey];
    const module = SPORT_MODULES[sportKey];
    if (module && sportConfigs.length > 0) {
      let allEvents = [];
      if (sportKey === "horse_racing") {
        allEvents = await module.fetch();  // fetchEvents returns HTML string for horse racing
        console.log(`Horse Racing: Fetched ${typeof allEvents === 'string' ? 'HTML content' : allEvents.length + ' events'}`);
      } else {
        const today = new Date();
        const startDate = new Date();
        const endDate = new Date();
        const daysToFetchPast = 7;
        const daysToFetchFuture = 7;
        startDate.setDate(today.getDate() - daysToFetchPast);
        endDate.setDate(today.getDate() + daysToFetchFuture);
        const startDateStr = startDate.toISOString().split('T')[0].replace(/-/g, '');
        const endDateStr = endDate.toISOString().split('T')[0].replace(/-/g, '');
        for (const config of sportConfigs) {
          const url = `https://site.api.espn.com/apis/site/v2/sports/${config.sport}/${config.league}/scoreboard?dates=${startDateStr}-${endDateStr}`;
          try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status} for ${config.name}`);
            const data = await response.json();
            const leagueEvents = await module.fetch(data, config);
            console.log(`${config.name}: Fetched ${leagueEvents.length} events`);
            allEvents = allEvents.concat(leagueEvents);
          } catch (error) {
            console.error(`Error fetching ${config.name} from ESPN:`, error);
          }
        }
      }
      // Only sort if allEvents is an array (i.e., not for horse racing)
      if (sportKey !== "football" && Array.isArray(allEvents)) {
        allEvents.sort((a, b) => new Date(a.date) - new Date(b.date));
      }
      events[sportKey] = allEvents;
    }
  }
  globalEvents = events;
  // Combine events for all sports, excluding horse racing since it's HTML
  events.all = [
    ...(events.football || []),
    ...(events.golf || []),
    ...(events.tennis || [])
  ].sort((a, b) => new Date(a.date) - new Date(b.date));
  return events;
}

/**
 * Adds toggle functionality for expandable match cards (football and tennis)
 */
export function setupExpandableCards() {
  console.log('Entering setupExpandableCards');
  const cards = document.querySelectorAll('.event-card.expandable-card, .tennis-card.expandable-card');
  console.log('Found expandable cards:', cards.length);

  if (cards.length === 0) {
    console.warn('No expandable cards found in the DOM. Check if the cards are rendered correctly.');
    return;
  }

  cards.forEach((card, index) => {
    const header = card.querySelector('.card-header');
    const details = card.querySelector('.match-details');

    if (!header) {
      console.error(`Card ${index} (ID: ${card.dataset.matchId || card.dataset.eventId}) is missing a .card-header element.`, card);
      return;
    }

    if (!details) {
      console.log(`Card ${index} (ID: ${card.dataset.matchId || card.dataset.eventId}) has no .match-details element. This is expected for non-live matches.`, card);
      return;
    }

    if (header._toggleHandler) {
      header.removeEventListener('click', header._toggleHandler, true);
      console.log(`Removed existing listener for card ${index} (ID: ${card.dataset.matchId || card.dataset.eventId})`);
    }

    const handler = (e) => {
      e.stopPropagation();
      console.log(`Card header clicked for card ${index} (ID: ${card.dataset.matchId || card.dataset.eventId})`);
      const isVisible = details.style.display === 'block';
      console.log(`Toggling card ${index} (ID: ${card.dataset.matchId || card.dataset.eventId}), Visible: ${isVisible}`);
      details.style.display = isVisible ? 'none' : 'block';
      card.classList.toggle('expanded', !isVisible);
    };

    header.addEventListener('click', handler, { capture: true });
    header._toggleHandler = handler;
    console.log(`Attached click listener to card ${index} (ID: ${card.dataset.matchId || card.dataset.eventId})`);
  });

  if (!document._cardCloseListener) {
    const closeHandler = (e) => {
      if (!e.target.closest('.event-card.expandable-card') && !e.target.closest('.tennis-card.expandable-card')) {
        console.log('Click outside, closing all expandable cards');
        document.querySelectorAll('.match-details').forEach(details => {
          details.style.display = 'none';
        });
        document.querySelectorAll('.expandable-card').forEach(card => {
          card.classList.remove('expanded');
        });
      }
    };
    document.addEventListener('click', closeHandler, { capture: true });
    document._cardCloseListener = closeHandler;
    console.log('Attached outside click listener');
  }
}

// New function to populate the center feed with detailed racecards
async function populateCenterFeed(sport) {
  if (sport !== 'horse_racing') return;  // Only handle horse racing for now

  const centerFeed = document.querySelector('.center-feed');
  if (!centerFeed) {
    console.warn('Center feed container not found');
    return;
  }

  const events = await fetchHorseRacingEvents();  // Fetch detailed racecards
  centerFeed.innerHTML = events || '<p>No upcoming horse racing meetings available.</p>';
}

export async function getEventList(currentPath, target, activeSport = 'football') {
  const path = currentPath.toLowerCase();
  let title = "";
  let description = "";
  let eventList = "";
  const dynamicEvents = await getDynamicEvents();
  const currentTime = new Date();
  const sevenDaysAgo = new Date();
  const sevenDaysFuture = new Date();
  sevenDaysAgo.setDate(currentTime.getDate() - 7);
  sevenDaysFuture.setDate(currentTime.getDate() + 7);

  if (target === "upcoming-events") {
    if (path === "/" || path === "/home/" || path === "/explore/") {
      title = "Upcoming Events Across All Sports";
      description = "Here are the latest upcoming events across all sports:";
      const allEvents = dynamicEvents.all || [];
      if (allEvents.length) {
        const eventsBySport = {
          football: dynamicEvents.football || [],
          golf: dynamicEvents.golf || [],
          tennis: dynamicEvents.tennis || [],
          horse_racing: dynamicEvents.horse_racing || []
        };
        eventList = Object.keys(eventsBySport).map(sport => {
          const sportEvents = eventsBySport[sport];
          if (!sportEvents.length) return "";
          const formatFunc = FORMATTERS[sport];
          return `
            <div class="sport-group">
              <h3>${sport.charAt(0).toUpperCase() + sport.slice(1)}</h3>
              <div class="event-list">
                ${formatFunc(sportEvents, sport, true)}
              </div>
            </div>
          `;
        }).join("");
        eventList = `<div class="all-events">${eventList}</div>`;
      } else {
        eventList = "<p>No upcoming events available across all sports.</p>";
      }
    } else if (path.includes("/sport/football/")) {
      title = "Upcoming Football Fixtures";
      description = "Here are the latest football fixtures in Tipster Arena:";
      const events = (dynamicEvents.football || []).filter(event => new Date(event.date) >= currentTime);
      eventList = events.length ? formatFootballTable(events) : `<p>No upcoming football fixtures available.</p>`;
    } else if (path.includes("/sport/golf/")) {
      title = "PGA Tour Events";
      description = "Here are the latest PGA Tour events (in-progress, recently completed, or upcoming):";
      const golfEvents = dynamicEvents.golf || [];
      const golfContent = await formatGolfList(golfEvents, "all", true);
      eventList = `
        <div class="golf-feed">
          ${golfContent}
        </div>
      `;
    } else if (path.includes("/sport/tennis/")) {
      title = "ATP Tournament Matches";
      description = "Here are the latest matches for ATP tournaments (past 7 days to next 7 days):";
      const tennisMatches = (dynamicEvents.tennis || []).filter(match => 
        new Date(match.date) >= sevenDaysAgo && new Date(match.date) <= sevenDaysFuture
      );
      if (!tennisMatches.length) {
        eventList = `<p>No recent or upcoming tennis matches available.</p>`;
      } else {
        const matchesByTournament = tennisMatches.reduce((acc, match) => {
          const tournamentKey = match.tournamentName;
          if (!acc[tournamentKey]) acc[tournamentKey] = [];
          acc[tournamentKey].push(match);
          return acc;
        }, {});
        const sortedTournaments = Object.keys(matchesByTournament).sort();
        eventList = await Promise.all(sortedTournaments.map(async tournament => {
          const tournamentMatches = matchesByTournament[tournament];
          tournamentMatches.sort((a, b) => new Date(a.date) - new Date(b.date));
          const matchItems = await formatTennisTable(tournamentMatches, tournament);
          return `
            <div class="tennis-feed">
              <div class="tournament-group">
                <p class="tournament-header"><span class="sport-icon">🎾</span> ${tournament}</p>
                <div class="event-list">
                  ${matchItems}
                </div>
              </div>
            </div>
          `;
        }));
        eventList = eventList.filter(item => item).join("");
        eventList = eventList ? `<div class="event-list">${eventList}</div>` : `<p>No recent or upcoming tennis matches available.</p>`;
      }
    } else if (path.includes("/sport/horse_racing/")) {
      title = "Upcoming Horse Racing Meetings";
      description = "Here are the race meetings for the next 3 days (detailed racecards are in the center feed):";
      const horseRacingEvents = await fetchHorseRacingMeetings();  // Fetch simple meeting list
      const horseRacingContent = await formatHorseRacingMeetingList(horseRacingEvents, "horse_racing");
      eventList = horseRacingEvents ? `
        <div class="meeting-list">
          ${horseRacingContent}
        </div>
      ` : `<p>No upcoming horse racing meetings available.</p>`;
    }
  }

  const popupHtml = `
    <div class="events-popup">
      <h2>${title}</h2>
      <p>${description}</p>
      ${eventList}
      <a href="#" class="show-less" data-target="${target}">Show less</a>
    </div>
  `;

  console.log('getEventList: About to call setupExpandableCards');
  setTimeout(() => {
    setupExpandableCards();
    console.log('setupExpandableCards called after DOM update in getEventList');
  }, 0);

  return popupHtml;
}

function attachFollowButtonListeners() {
  const followButtons = document.querySelectorAll('.follow-btn');
  followButtons.forEach(button => {
    button.addEventListener('click', function() {
      const username = this.getAttribute('data-username');
      followUser(username, this);
    });
  });
}

function followUser(username, button) {
  const formData = new FormData();
  formData.append('username', username);
  fetch('/api/follow/', {
    method: 'POST',
    body: formData,
    headers: {
      'X-CSRFToken': getCSRFToken(),
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      button.textContent = 'Following';
      button.disabled = true;
      button.classList.add('followed');
      console.log(data.message);
    } else {
      alert('Error: ' + data.error);
    }
  })
  .catch(error => {
    console.error('Error following user:', error);
    alert('An error occurred while following.');
  });
}

export function setupShowMoreButtons() {
  const showMoreButtons = document.querySelectorAll('.show-more');
  console.log('Found show-more buttons:', showMoreButtons.length);
  showMoreButtons.forEach(button => {
    console.log('Attaching listener to show-more button:', button);
    button.addEventListener('click', async function(e) {
      e.preventDefault();
      const target = this.getAttribute('data-target');
      const content = document.querySelector('.content');
      let previousUrl = window.location.pathname;

      try {
        const activeSlide = document.querySelector('.carousel-slide.active');
        const activeSport = activeSlide ? activeSlide.getAttribute('data-sport') : 'football';
        console.log('Calling getEventList for target:', target);

        const popupHtml = await getEventList(window.location.pathname, target, activeSport);
        console.log('getEventList returned, setting content HTML');
        content.innerHTML = popupHtml;

        setTimeout(() => {
          setupExpandableCards();
          console.log('Fallback call to setupExpandableCards after setting content HTML');
        }, 0);

        switch (target) {
          case 'trending-tips':
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
                      <img src="${user.avatar_url}" alt="${user.username}" class="follow-avatar" width="48" height="48">
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

async function populateCarousel(container) {
  const dynamicEvents = await getDynamicEvents();
  const slides = container.querySelectorAll('.carousel-slide');
  for (const slide of slides) {
    const sport = slide.getAttribute('data-sport');
    if (sport && FORMATTERS[sport]) {
      const eventList = slide.querySelector('.event-list');
      if (eventList) {
        const events = dynamicEvents[sport] || [];
        eventList.innerHTML = await FORMATTERS[sport](events, sport, false) || `<p>No upcoming ${sport} events available.</p>`;
      } else {
        console.warn(`Event list container not found for ${sport} in slide:`, slide);
      }
    } else {
      console.warn(`No formatter found for sport: ${sport} in slide:`, slide);
    }
  }
  setupExpandableCards();
}

function setupDotNavigation(container) {
  const dotsContainer = container.parentElement.querySelector('.carousel-dots');
  const dots = dotsContainer ? dotsContainer.querySelectorAll('.dot') : [];
  const slides = container.querySelectorAll('.carousel-slide');

  if (slides.length <= 1) {
    if (dotsContainer) dotsContainer.style.display = 'none';
    return;
  }

  if (dots.length !== slides.length) {
    console.warn(`Mismatch detected: ${slides.length} slides vs ${dots.length} dots`);
    console.log("Slides:", Array.from(slides).map(s => s.getAttribute('data-sport')));
    console.log("Dots:", Array.from(dots).map(d => s.getAttribute('data-sport')));
  }

  dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
      showSlide(container, index);
    });
  });

  const activeSlideIndex = Array.from(slides).findIndex(slide => slide.classList.contains('active'));
  showSlide(container, activeSlideIndex !== -1 ? activeSlideIndex : 0);
}

function startAutoRotation(container) {
  const slides = container.querySelectorAll('.carousel-slide');
  if (slides.length <= 1) return;

  let currentSlide = Array.from(slides).findIndex(slide => slide.classList.contains('active'));
  if (currentSlide === -1) currentSlide = 0;

  let interval;
  const rotate = () => {
    currentSlide = (currentSlide < slides.length - 1) ? currentSlide + 1 : 0;
    showSlide(container, currentSlide);
  };
  
  interval = setInterval(rotate, 5000);

  container.removeEventListener('mouseenter', clearIntervalHandler);
  container.removeEventListener('mouseleave', restartRotationHandler);
  
  function clearIntervalHandler() { clearInterval(interval); }
  function restartRotationHandler() { interval = setInterval(rotate, 5000); }
  
  container.addEventListener('mouseenter', clearIntervalHandler);
  container.addEventListener('mouseleave', restartRotationHandler);
}

function showSlide(container, index) {
  const slides = container.querySelectorAll('.carousel-slide');
  const dotsContainer = container.parentElement.querySelector('.carousel-dots');
  const dots = dotsContainer ? dotsContainer.querySelectorAll('.dot') : [];

  slides.forEach((slide, i) => {
    slide.classList.toggle('active', i === index);
  });

  dots.forEach((dot, i) => {
    dot.classList.toggle('active', i === index);
  });
}

export async function initCarousel() {
  const dynamicEvents = await getDynamicEvents();
  const carouselContainers = document.querySelectorAll('.carousel-container');
  for (const container of carouselContainers) {
    const slides = container.querySelectorAll('.carousel-slide');
    if (slides.length > 0) {
      await populateCarousel(container);
      setupDotNavigation(container);
      startAutoRotation(container);
      const footballSlide = container.querySelector('.carousel-slide[data-sport="football"]');
      if (footballSlide) {
        setInterval(async () => {
          const dynamicEvents = await getDynamicEvents();
          const eventList = footballSlide.querySelector('.event-list');
          if (eventList) {
            eventList.innerHTML = await FORMATTERS.football(dynamicEvents.football || [], 'football', false);
            setupExpandableCards();
          }
        }, 30000);
      }
    }
  }

  const eventLists = document.querySelectorAll('.event-list[id$="-events"]');
  for (const eventList of eventLists) {
    const sport = eventList.id.replace('-events', '');
    if (sport && FORMATTERS[sport] && !eventList.closest('.carousel-container')) {
      const events = dynamicEvents[sport] || [];
      eventList.innerHTML = await FORMATTERS[sport](events, sport, false) || `<p>No upcoming ${sport} events available.</p>`;
      setupExpandableCards();
    }
  }

  // Populate the center feed for horse racing
  if (window.location.pathname.includes('/sport/horse_racing/')) {
    await populateCenterFeed('horse_racing');
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupShowMoreButtons();
  initCarousel();
});

export { 
  attachFollowButtonListeners, 
  formatFootballList, 
  formatGolfList, 
  formatTennisList, 
  formatHorseRacingList, 
  formatFootballTable 
};