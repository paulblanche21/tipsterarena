// upcoming-events.js: Handles fetching and rendering events in a modal for Tipster Arena

import { getCSRFToken } from './utils.js';
import { fetchEvents as fetchFootballEvents, formatEventList as formatFootballList, formatEventTable as formatFootballTable } from './football-events.js';
import { fetchEvents as fetchTennisEvents, formatEventList as formatTennisList, formatEventTable as formatTennisTable } from './tennis-events.js';
import { fetchEvents as fetchGolfEvents, formatEventList as formatGolfList } from './golf-events.js';
import { fetchEvents as fetchHorseRacingEvents, formatEventList as formatHorseRacingList } from './horse-racing-events.js';

// Configuration for sports and their respective leagues
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

// Mapping of sports to their fetch and format functions
const SPORT_MODULES = {
  football: { fetch: fetchFootballEvents, format: formatFootballList, formatCentral: formatFootballTable },
  golf: { fetch: fetchGolfEvents, format: formatGolfList, formatCentral: formatGolfList },
  tennis: { fetch: fetchTennisEvents, format: formatTennisList, formatCentral: formatTennisTable },
  horse_racing: { fetch: fetchHorseRacingEvents, format: formatHorseRacingList, formatCentral: formatHorseRacingList }
};

// Formatters for modal rendering
const FORMATTERS = {
  football: formatFootballTable,
  golf: formatGolfList,
  tennis: formatTennisTable,
  horse_racing: formatHorseRacingList
};

let globalEvents = {};

// Fetches events for a specific sport
async function fetchEventsForSport(sport) {
  console.log(`Fetching events for ${sport}`);
  const sportConfigs = SPORT_CONFIG[sport];
  const module = SPORT_MODULES[sport];
  if (!module || !sportConfigs.length) {
    console.warn(`No module or configs for ${sport}`);
    return [];
  }

  let allEvents = [];
  if (sport === "horse_racing") {
    allEvents = await module.fetch();
    console.log(`Horse Racing: Fetched ${allEvents.length} events`);
  } else {
    const today = new Date();
    const startDate = new Date();
    const endDate = new Date();
    const daysToFetchPast = 3;
    const daysToFetchFuture = 7;
    startDate.setDate(today.getDate() - daysToFetchPast);
    endDate.setDate(today.getDate() + daysToFetchFuture);
    const startDateStr = startDate.toISOString().split('T')[0].replace(/-/g, '');
    const endDateStr = endDate.toISOString().split('T')[0].replace(/-/g, '');
    for (const config of sportConfigs) {
      const url = `https://site.api.espn.com/apis/site/v2/sports/${config.sport}/${config.league}/scoreboard?dates=${startDateStr}-${endDateStr}`;
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error: ${response.status} for ${config.name}`);
        const data = await response.json();
        const leagueEvents = await module.fetch(data, config);
        console.log(`${config.name}: Fetched ${leagueEvents.length} events`);
        allEvents = allEvents.concat(leagueEvents);
      } catch (error) {
        console.error(`Error fetching ${config.name}:`, error);
      }
    }
  }
  globalEvents[sport] = allEvents;
  return allEvents;
}

// Filters events by category
function filterEvents(events, category, sportKey) {
  console.log(`Filtering events for ${sportKey}, category: ${category}`);
  const currentTime = new Date();
  const threeDaysAgo = new Date();
  threeDaysAgo.setDate(currentTime.getDate() - 3);

  if (sportKey === 'horse_racing') {
    if (category === 'upcoming_meetings') {
      return events.filter(meeting => new Date(meeting.date) > currentTime);
    } else if (category === 'at_the_post') {
      return events
        .filter(meeting => new Date(meeting.date).toDateString() === currentTime.toDateString())
        .map(meeting => ({
          ...meeting,
          races: (meeting.races || []).filter(race => {
            const raceTime = new Date(`${meeting.date}T${race.race_time}`);
            const timeDiff = Math.abs(raceTime - currentTime) / (1000 * 60);
            return timeDiff <= 30;
          })
        }))
        .filter(meeting => meeting.races.length > 0);
    } else if (category === 'race_results') {
      return events
        .map(meeting => ({
          ...meeting,
          races: (meeting.races || []).filter(race => race.result && race.result.winner)
        }))
        .filter(meeting => meeting.races.length > 0);
    }
  } else if (sportKey === 'golf') {
    if (category === 'fixtures') {
      return events
        .filter(event => event.state === "pre" && new Date(event.date) > currentTime)
        .sort((a, b) => new Date(a.date) - new Date(b.date));
    } else if (category === 'inplay') {
      return events.filter(event => event.state === "in");
    } else if (category === 'results') {
      return events
        .filter(event => event.state === "post" && event.completed)
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 1);
    }
  } else {
    return events.filter(event => {
      const eventDate = new Date(event.date);
      if (category === 'fixtures') {
        return event.state === 'pre' && eventDate > currentTime;
      } else if (category === 'inplay') {
        return event.state === 'in';
      } else if (category === 'results') {
        return event.state === 'post' && event.completed && eventDate >= threeDaysAgo && eventDate <= currentTime;
      }
      return false;
    }).sort((a, b) => {
      if (sportKey === 'football') {
        if (a.priority !== b.priority) return a.priority - b.priority;
      }
      return new Date(a.date) - new Date(b.date);
    });
  }
  return [];
}

// Populates modal with events
async function populateModal(sport, category) {
  console.log(`Populating modal for ${sport}, ${category}`);
  const modal = document.getElementById('event-modal');
  const modalTitle = document.getElementById('event-modal-title');
  const modalBody = document.getElementById('event-modal-body');
  if (!modal || !modalTitle || !modalBody) {
    console.error('Modal elements not found:', { modal, modalTitle, modalBody });
    return;
  }

  // Set modal title
  const sportName = sport === 'horse_racing' ? 'Horse Racing' : sport.charAt(0).toUpperCase() + sport.slice(1);
  const categoryName = sport === 'horse_racing'
    ? category.replace('upcoming_meetings', 'Upcoming Meetings')
              .replace('at_the_post', 'At the Post')
              .replace('race_results', 'Race Results')
    : category.charAt(0).toUpperCase() + category.slice(1);
  modalTitle.textContent = `${sportName} ${categoryName}`;

  modalBody.innerHTML = '<p>Loading events...</p>';

  try {
    // Fetch events if not already loaded
    if (!globalEvents[sport]) {
      console.log(`No cached events for ${sport}, fetching...`);
      await fetchEventsForSport(sport);
    }
    const events = globalEvents[sport] || [];
    console.log(`Found ${events.length} events for ${sport}`);
    const filteredEvents = filterEvents(events, category, sport);
    console.log(`Filtered ${filteredEvents.length} events for ${category}`);
    const formatter = FORMATTERS[sport];
    if (!formatter) {
      console.warn(`No formatter for ${sport}`);
      modalBody.innerHTML = `<p>No ${categoryName.toLowerCase()} available for ${sportName}.</p>`;
      return;
    }
    const html = await formatter(filteredEvents, sport, category, true);
    modalBody.innerHTML = html || `<p>No ${categoryName.toLowerCase()} available for ${sportName}.</p>`;
    console.log(`Modal populated with HTML for ${sport} ${category}`);
    setupExpandableCards();
    if (sport === 'golf' && (category === 'inplay' || category === 'results')) {
      setupLeaderboardUpdates();
    }
    modal.style.display = 'flex';
  } catch (error) {
    console.error(`Error populating modal for ${sport} ${category}:`, error);
    modalBody.innerHTML = '<p>Error loading events.</p>';
  }
}

// Adds toggle functionality for expandable cards
export function setupExpandableCards() {
  console.log('Setting up expandable cards');
  const cards = document.querySelectorAll('.event-item.expandable-card, .tennis-card.expandable-card, .event-card.expandable-card, .golf-card, .meeting-card.expandable-card');
  console.log(`Found ${cards.length} expandable cards`);
  cards.forEach((card, index) => {
    const header = card.querySelector('.card-header');
    const details = card.querySelector('.card-content, .match-details');
    if (!header || !details) return;

    if (header._toggleHandler) {
      header.removeEventListener('click', header._toggleHandler, true);
    }

    const handler = (e) => {
      e.stopPropagation();
      const isVisible = details.style.display === 'block';
      details.style.display = isVisible ? 'none' : 'block';
      card.classList.toggle('expanded', !isVisible);
      console.log(`Toggled card ${index}, visible: ${!isVisible}`);
    };

    header.addEventListener('click', handler, { capture: true });
    header._toggleHandler = handler;
  });

  if (!document._cardCloseListener) {
    const closeHandler = (e) => {
      if (!e.target.closest('.event-item.expandable-card, .tennis-card.expandable-card, .event-card.expandable-card, .golf-card, .meeting-card.expandable-card')) {
        document.querySelectorAll('.card-content, .match-details').forEach(details => {
          details.style.display = 'none';
        });
        document.querySelectorAll('.expandable-card, .golf-card').forEach(card => {
          card.classList.remove('expanded');
        });
        console.log('Closed all expandable cards');
      }
    };
    document.addEventListener('click', closeHandler, { capture: true });
    document._cardCloseListener = closeHandler;
  }
}

// Initializes button-based event navigation
export async function initButtons() {
  console.log('Initializing event buttons');
  const sidebar = document.querySelector('.upcoming-events-card');
  if (!sidebar) {
    console.warn('Upcoming events card not found');
    return;
  }

  const sportSelector = sidebar.querySelector('.sport-selector');
  const buttonsContainer = sidebar.querySelector('.event-buttons');
  const modal = document.getElementById('event-modal');
  const modalCloseBtn = document.querySelector('.event-modal-close');

  if (!buttonsContainer || !modal || !modalCloseBtn) {
    console.warn('Event buttons or modal elements not found:', { buttonsContainer, modal, modalCloseBtn });
    return;
  }

  // Determine active sport
  let activeSport;
  if (sportSelector) {
    // Home page: Use sport selector
    activeSport = sportSelector.value;
  } else {
    // Sport page: Extract from class like 'upcoming-events-football'
    const sportClass = Array.from(buttonsContainer.closest('.upcoming-events-card').classList)
      .find(cls => cls.startsWith('upcoming-events-') && cls !== 'upcoming-events-card');
    activeSport = sportClass ? sportClass.replace('upcoming-events-', '') : 'football';
  }
  console.log(`Active sport: ${activeSport}`);

  // Update button labels based on sport
  const updateButtonLabels = (sport) => {
    const buttons = buttonsContainer.querySelectorAll('.event-btn');
    buttons.forEach(button => {
      const baseCategory = button.dataset.category;
      const horseRacingLabel = button.dataset.horseRacing;
      if (sport === 'horse_racing') {
        button.textContent = horseRacingLabel.replace(/_/g, ' ');
      } else {
        button.textContent = baseCategory.charAt(0).toUpperCase() + baseCategory.slice(1);
      }
    });
  };

  updateButtonLabels(activeSport);

  // Sport selector change
  if (sportSelector) {
    sportSelector.addEventListener('change', () => {
      activeSport = sportSelector.value;
      console.log(`Sport changed to ${activeSport}`);
      updateButtonLabels(activeSport);
      const buttons = buttonsContainer.querySelectorAll('.event-btn');
      buttons.forEach(btn => btn.classList.remove('active'));
    });
  }

  // Button clicks to open modal
  buttonsContainer.addEventListener('click', (e) => {
    const button = e.target.closest('.event-btn');
    if (!button) return;

    console.log(`Button clicked: ${button.dataset.category || button.dataset.horseRacing}`);
    const buttons = buttonsContainer.querySelectorAll('.event-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');
    const category = activeSport === 'horse_racing' ? button.dataset.horseRacing : button.dataset.category;

    // Open modal and load events
    populateModal(activeSport, category);
  });

  // Close modal
  modalCloseBtn.addEventListener('click', () => {
    console.log('Closing modal');
    modal.style.display = 'none';
    const buttons = buttonsContainer.querySelectorAll('.event-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
  });

  // Close modal on outside click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      console.log('Closing modal (outside click)');
      modal.style.display = 'none';
      const buttons = buttonsContainer.querySelectorAll('.event-btn');
      buttons.forEach(btn => btn.classList.remove('active'));
    }
  });
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  console.log('DOMContentLoaded: Initializing upcoming-events.js');
  initButtons();
});