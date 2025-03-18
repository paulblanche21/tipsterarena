// upcoming-events.js
console.log("Upcoming-events.js loaded successfully");

import { fetchEvents as fetchFootballEvents, formatEventList as formatFootballList, formatEventTable } from './football-events.js';
import { fetchEvents as fetchTennisEvents, formatEventList as formatTennisList, fetchTournamentMatches } from './tennis-events.js';
import { fetchEvents as fetchGolfEvents, formatEventList as formatGolfList, setupLeaderboardUpdates } from './golf-events.js';
import { fetchEvents as fetchHorseRacingEvents, formatEventList as formatHorseRacingList } from './horse-racing-events.js';

const SPORT_CONFIG = {
  football: [
    { sport: "soccer", league: "eng.1", icon: "⚽", name: "Premier League" },
    { sport: "soccer", league: "esp.1", icon: "⚽", name: "La Liga" },
    { sport: "soccer", league: "ita.1", icon: "⚽", name: "Serie A" },
    { sport: "soccer", league: "fra.1", icon: "⚽", name: "Ligue 1" },
    { sport: "soccer", league: "uefa.champions", icon: "⚽", name: "Champions League" },
    { sport: "soccer", league: "uefa.europa", icon: "⚽", name: "Europa League" },
    { sport: "soccer", league: "eng.fa", icon: "⚽", name: "FA Cup" },
    { sport: "soccer", league: "eng.2", icon: "⚽", name: "EFL Championship" },
    { sport: "soccer", league: "por.1", icon: "⚽", name: "Primeira Liga" },
    { sport: "soccer", league: "ned.1", icon: "⚽", name: "Eredivisie" },
    { sport: "soccer", league: "nir.1", icon: "⚽", name: "Irish League" },
    { sport: "soccer", league: "usa.1", icon: "⚽", name: "MLS" },
    { sport: "soccer", league: "sco.1", icon: "⚽", name: "Scottish Premiership" }
  ],
  golf: [
    { sport: "golf", league: "pga", icon: "⛳", name: "PGA Tour" },
    { sport: "golf", league: "lpga", icon: "⛳", name: "LPGA Tour" }
  ],
  tennis: [
    { sport: "tennis", league: "atp", icon: "🎾", name: "ATP Tour" }
  ],
  horse_racing: [
    { sport: "horse_racing", league: "uk_irish", icon: "🏇", name: "UK & Irish Racing", url: "https://www.attheraces.com/ajax/fast-results/lhs" }, // Today’s results
    { sport: "horse_racing", league: "tomorrow", icon: "🏇", name: "Tomorrow’s Racing", url: "https://www.attheraces.com/ajax/racecards/tomorrow" } // Hypothetical tomorrow endpoint
  ]
};

const SPORT_MODULES = {
  football: { fetch: fetchFootballEvents, format: formatFootballList },
  golf: { fetch: fetchGolfEvents, format: formatGolfList },
  tennis: { fetch: fetchTennisEvents, format: formatTennisList },
  horse_racing: { fetch: fetchHorseRacingEvents, format: formatHorseRacingList }
};

let globalEvents = {}; // Store events globally

export async function getDynamicEvents() {
  const events = {};
  const now = new Date();
  for (const sportKey of Object.keys(SPORT_CONFIG)) {
    const sportConfigs = SPORT_CONFIG[sportKey];
    const module = SPORT_MODULES[sportKey];
    if (module && sportConfigs.length > 0) {
      let allEvents = [];
      if (sportKey === "horse_racing") {
        // Handle At The Races API for horse racing
        for (const config of sportConfigs) {
          try {
            const response = await fetch(config.url, {
              method: 'GET',
              headers: { 'Accept': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status} for ${config.name}`);
            const data = await response.json();
            const leagueEvents = await module.fetch(data, config); // Pass raw data to horse-racing-events.js
            allEvents = allEvents.concat(leagueEvents);
          } catch (error) {
            console.error(`Error fetching ${config.name} from At The Races:`, error);
          }
        }
      } else {
        // ESPN API for football, golf, tennis
        const today = new Date();
        const endDate = new Date();
        endDate.setDate(today.getDate() + 90); // Look ahead 3 months
        const todayStr = today.toISOString().split('T')[0].replace(/-/g, '');
        const endDateStr = endDate.toISOString().split('T')[0].replace(/-/g, '');
        for (const config of sportConfigs) {
          const url = `https://site.api.espn.com/apis/site/v2/sports/${config.sport}/${config.league}/scoreboard?dates=${todayStr}-${endDateStr}`;
          try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status} for ${config.name}`);
            const data = await response.json();
            const leagueEvents = await module.fetch(data, config);
            allEvents = allEvents.concat(leagueEvents);
          } catch (error) {
            console.error(`Error fetching ${config.name} from ESPN:`, error);
          }
        }
      }
      events[sportKey] = allEvents;
    }
  }
  globalEvents = events;
  events.all = [
    ...(events.football || []),
    ...(events.golf || []),
    ...(events.tennis || []),
    ...(events.horse_racing || [])
  ].sort((a, b) => new Date(a.date) - new Date(b.date));
  return events;
}

export async function getEventList(currentPath, target, activeSport = 'football') {
  const path = currentPath.toLowerCase();
  let title = "";
  let description = "";
  let eventList = "";
  const dynamicEvents = await getDynamicEvents();

  if (target === "upcoming-events") {
    if (path === "/" || path === "/home/") {
      const formatFunc = {
        'football': formatFootballList,
        'golf': formatGolfList,
        'tennis': formatTennisList,
        'horse_racing': formatHorseRacingList
      }[activeSport] || formatFootballList;
      title = `Upcoming ${activeSport.charAt(0).toUpperCase() + activeSport.slice(1)} Events`;
      description = `Here are the latest upcoming ${activeSport} events in Tipster Arena:`;
      const events = dynamicEvents[activeSport] || [];
      if (activeSport === 'football') {
        eventList = `<div class="event-table">${formatEventTable(events)}</div>`;
      } else {
        eventList = `<div class="event-list">${await formatFunc(events, activeSport, true)}</div>`;
      }
    } else if (path.includes("/sport/football/")) {
      title = "Upcoming Football Fixtures";
      description = "Here are the latest football fixtures in Tipster Arena:";
      const events = dynamicEvents.football || [];
      eventList = `<div class="event-table">${formatEventTable(events)}</div>`;
    } else if (path.includes("/sport/golf/")) {
      title = "Upcoming Golf Events";
      description = "Here are the latest golf events in Tipster Arena:";
      eventList = `<div class="event-list">${await formatGolfList(dynamicEvents.golf, "golf", true)}</div>`;
    } else if (path.includes("/sport/tennis/")) {
      title = "Upcoming ATP Tournament Matches";
      description = "Here are the latest matches for the current ATP tournament:";
      const tennisEvents = dynamicEvents.tennis || [];
      const currentTournament = tennisEvents.find(event => new Date(event.date) > new Date()) || tennisEvents[0];
      if (currentTournament) {
        const matches = await fetchTournamentMatches(currentTournament.id);
        eventList = matches.length
          ? matches
              .map(match => `
                <p class="event-item">
                  ${match.player1} vs ${match.player2} - ${match.displayDate} ${match.time} (${match.round})
                </p>
              `)
              .join("")
          : `<p>No matches available for ${currentTournament.name}.</p>`;
      } else {
        eventList = `<p>No current ATP tournament found.</p>`;
      }
      eventList = `<div class="event-list">${eventList}</div>`;
    } else if (path.includes("/sport/horse_racing/")) {
      title = "Today’s Results & Tomorrow’s Horse Racing";
      description = "Here are today’s completed races and tomorrow’s scheduled races:";
      const horseRacingEvents = dynamicEvents.horse_racing || [];
      eventList = `<div class="event-list">${await formatHorseRacingList(horseRacingEvents, "horse_racing", true)}</div>`;
    }
  }

  return `
    <div class="events-popup">
      <h2>${title}</h2>
      <p>${description}</p>
      ${eventList}
      <a href="#" class="show-less" data-target="${target}">Show less</a>
    </div>
  `;
}

// Populate tennis events in sidebar on page load (unchanged for tennis)
document.addEventListener("DOMContentLoaded", async () => {
  const tennisEventsElement = document.getElementById('tennis-events');
  if (tennisEventsElement) {
    const dynamicEvents = await getDynamicEvents();
    const tennisEvents = dynamicEvents.tennis || [];
    tennisEventsElement.innerHTML = await formatTennisList(tennisEvents, 'tennis', false) || '<p>No upcoming tournaments available.</p>';
  }
  // Optionally populate horse racing sidebar if you have an element for it
  const horseRacingEventsElement = document.getElementById('horse-racing-events');
  if (horseRacingEventsElement) {
    const dynamicEvents = await getDynamicEvents();
    const horseRacingEvents = dynamicEvents.horse_racing || [];
    horseRacingEventsElement.innerHTML = await formatHorseRacingList(horseRacingEvents, 'horse_racing', false) || '<p>No upcoming races available.</p>';
  }
});

// Export all necessary functions
export { formatFootballList, formatGolfList, formatTennisList, formatHorseRacingList, formatEventTable };