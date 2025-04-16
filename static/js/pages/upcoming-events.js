// static/js/pages/upcoming-events.js
import { getCSRFToken } from './utils.js';
import { fetchEvents as fetchFootballEvents, formatEventList as formatFootballList, formatFootballTable } from './football-events.js';
import { fetchEvents as fetchTennisEvents, formatEventList as formatTennisList, formatEventTable as formatTennisTable } from './tennis-events.js';
import { fetchEvents as fetchGolfEvents, formatEventList as formatGolfList, setupLeaderboardUpdates } from './golf-events.js';
import { fetchEvents as fetchHorseRacingEvents, formatEventList as formatHorseRacingList } from './horse-racing-events.js';

console.log('Loading upcoming-events.js');

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
    { sport: "golf", league: "pga", icon: "⛳", name: "PGA Tour", priority: 1 },
    { sport: "golf", league: "lpga", icon: "⛳", name: "LPGA Tour", priority: 2 }
  ],
  tennis: [
    { sport: "tennis", league: "atp", icon: "🎾", name: "ATP Tour", priority: 1 }
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
  horse_racing: renderHorseRacingEvents // Updated to custom function
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
    console.log(`Horse Racing: Fetched ${allEvents.length} events`, allEvents);
  } else {
    const today = new Date();
    const startDate = new Date();
    const endDate = new Date();
    const daysToFetchPast = 14;
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
        console.log(`Raw API data for ${config.name}:`, data);
        const leagueEvents = await module.fetch(data, config);
        console.log(`${config.name}: Fetched ${leagueEvents.length} events, Start: ${startDateStr}, End: ${endDateStr}`);
        allEvents = allEvents.concat(leagueEvents);
      } catch (error) {
        console.error(`Error fetching ${config.name}:`, error);
      }
    }
  }
  // Filter events within range
  const currentTime = new Date();
  const fourteenDaysAgo = new Date();
  const sevenDaysFuture = new Date();
  fourteenDaysAgo.setDate(currentTime.getDate() - 14);
  sevenDaysFuture.setDate(currentTime.getDate() + 7);
  allEvents = allEvents.filter(event => {
    const eventDate = new Date(event.date);
    const isWithinRange = eventDate >= fourteenDaysAgo && eventDate <= sevenDaysFuture;
    if (!isWithinRange) {
      console.log(`Excluding event: ${event.name || event.venue}, Date: ${event.date}`);
    }
    return isWithinRange;
  });
  globalEvents[sport] = allEvents;
  console.log(`Total ${sport} events fetched: ${allEvents.length}`);
  return allEvents;
}

// Filters events by category
function filterEvents(events, category, sportKey) {
  console.log(`Filtering events for ${sportKey}, category: ${category}`);
  const currentTime = new Date();
  const fourteenDaysAgo = new Date();
  const sevenDaysFuture = new Date();
  fourteenDaysAgo.setDate(currentTime.getDate() - 14);
  sevenDaysFuture.setDate(currentTime.getDate() + 7);

  if (sportKey === 'horse_racing') {
    if (category === 'upcoming_meetings') {
      return events.filter(meeting => {
        const meetingDate = new Date(meeting.date);
        const today = new Date(currentTime.setHours(0, 0, 0, 0));
        const tomorrow = new Date(today);
        tomorrow.setDate(today.getDate() + 1);
        const isTodayOrTomorrow = meetingDate >= today && meetingDate <= tomorrow;
        console.log(`Meeting ${meeting.venue} (${meeting.date}): isTodayOrTomorrow=${isTodayOrTomorrow}`);
        return isTodayOrTomorrow;
      });
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
  } else {
    return events.filter(event => {
      const eventDate = new Date(event.date);
      if (category === 'fixtures') {
        return event.state === 'pre' && eventDate > currentTime && eventDate <= sevenDaysFuture;
      } else if (category === 'inplay') {
        return event.state === 'in';
      } else if (category === 'results') {
        const isWithinFourteenDays = eventDate >= fourteenDaysAgo && eventDate <= currentTime;
        return event.state === 'post' && isWithinFourteenDays;
      }
      return false;
    }).sort((a, b) => {
      if (sportKey === 'tennis' || sportKey === 'football') {
        if (a.priority !== b.priority) return a.priority - b.priority;
      }
      return new Date(b.date) - new Date(a.date);
    });
  }
  return [];
}

// Renders horse racing events for modal
// static/js/upcoming-events.js
async function renderHorseRacingEvents(events, sport, category) {
  console.log(`Rendering horse racing events for ${category}, count: ${events.length}`);
  if (!events || events.length === 0) {
    return `<p>No ${category.replace(/_/g, ' ')} available.</p>`;
  }

  let html = '<div class="racecard-feed">';
  events.forEach(event => {
    html += `
      <div class="meeting-card expandable-card">
        <div class="card-header">
          <div class="meeting-info">
            <span class="meeting-name">${event.venue} - ${event.displayDate}</span>
            <a href="${event.url}" target="_blank">View Full Card</a>
          </div>
        </div>
        <div class="card-content" style="display: none;">
          ${event.races.map(race => `
            <div class="race-card">
              <div class="race-header">
                <p class="race-title"><strong>${race.race_time} - ${race.name}</strong></p>
                <p class="race-meta">Runners: ${race.runners} | Going: ${race.going_data} | TV: ${race.tv}</p>
              </div>
              ${category === 'race_results' && race.result ? `
                <div class="race-result">
                  <p><strong>Winner:</strong> ${race.result.winner}</p>
                  <p><strong>Placed:</strong> ${race.result.positions.map(p => `${p.position}. ${p.name}`).join(', ')}</p>
                </div>
              ` : ''}
              <div class="horses-list">
                <ul>
                  ${race.horses.map(h => `
                    <li>
                      <strong>${h.finish_status === h.number ? h.number : `${h.number} (${h.finish_status})`}. ${h.name}</strong>
                      <span class="jockey">Jockey: ${h.jockey}</span>
                      <span class="trainer">Trainer: ${h.trainer}</span>
                      <span class="owner">Owner: ${h.owner}</span>
                      <span class="odds">Odds: ${h.odds}</span>
                      <span>Form: ${h.form}</span>
                      <span>RPR: ${h.rpr}</span>
                      <span>Spotlight: ${h.spotlight}</span>
                      <span>Trainer 14 Days: ${h.trainer_14_days.runs ? `${h.trainer_14_days.wins}/${h.trainer_14_days.runs} (${h.trainer_14_days.percent}%)` : 'N/A'}</span>
                    </li>
                  `).join('')}
                </ul>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  });
  html += '</div>';
  return html;
}

// Populates modal with events
async function populateModal(sport, category) {
  console.log(`Populating modal for ${sport}, ${category}`);
  const modal = document.getElementById('event-modal');
  const modalTitle = document.getElementById('event-modal-title');
  const modalBody = document.getElementById('event-modal-body');
  if (!modal || !modalTitle || !modalBody) {
    console.error('Modal elements not found');
    return;
  }

  const sportName = sport === 'horse_racing' ? 'Horse Racing' : sport.charAt(0).toUpperCase() + sport.slice(1);
  const categoryName = sport === 'horse_racing'
    ? category.replace('upcoming_meetings', 'Upcoming Meetings')
              .replace('at_the_post', 'At the Post')
              .replace('race_results', 'Race Results')
    : category.charAt(0).toUpperCase() + category.slice(1);
  modalTitle.textContent = `${sportName} ${categoryName}`;

  modalBody.innerHTML = '<p>Loading events...</p>';

  try {
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
    console.log(`Modal populated for ${sport} ${category}`);
    setupExpandableCards();
    if (sport === 'golf' && (category === 'inplay' || category === 'results') && filteredEvents.length > 0) {
      if (typeof setupLeaderboardUpdates === 'function') {
        setupLeaderboardUpdates();
      } else {
        console.warn('setupLeaderboardUpdates is not defined');
      }
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
  const cards = document.querySelectorAll('.event-item.expandable-card, .tennis-card.expandable-card, .event-card.expandable-card, .golf-card.expandable-card, .meeting-card.expandable-card');
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
      if (!e.target.closest('.event-item.expandable-card, .tennis-card.expandable-card, .event-card.expandable-card, .golf-card.expandable-card, .meeting-card.expandable-card')) {
        document.querySelectorAll('.card-content, .match-details').forEach(details => {
          details.style.display = 'none';
        });
        document.querySelectorAll('.expandable-card').forEach(card => {
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
    console.warn('Event buttons or modal elements not found');
    return;
  }

  let activeSport;
  if (sportSelector) {
    activeSport = sportSelector.value;
  } else {
    const sportClass = Array.from(sidebar.classList)
      .find(cls => cls.startsWith('upcoming-events-') && cls !== 'upcoming-events-card');
    activeSport = sportClass ? sportClass.replace('upcoming-events-', '') : 'football';
  }
  console.log(`Active sport: ${activeSport}`);

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

  if (sportSelector) {
    sportSelector.addEventListener('change', () => {
      activeSport = sportSelector.value;
      console.log(`Sport changed to ${activeSport}`);
      updateButtonLabels(activeSport);
      const buttons = buttonsContainer.querySelectorAll('.event-btn');
      buttons.forEach(btn => btn.classList.remove('active'));
    });
  }

  buttonsContainer.addEventListener('click', (e) => {
    const button = e.target.closest('.event-btn');
    if (!button) return;

    console.log(`Button clicked: ${button.dataset.category || button.dataset.horseRacing}`);
    const buttons = buttonsContainer.querySelectorAll('.event-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');
    const category = activeSport === 'horse_racing' ? button.dataset.horseRacing : button.dataset.category;

    populateModal(activeSport, category);
  });

  modalCloseBtn.addEventListener('click', () => {
    console.log('Closing modal');
    modal.style.display = 'none';
    const buttons = buttonsContainer.querySelectorAll('.event-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
  });

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