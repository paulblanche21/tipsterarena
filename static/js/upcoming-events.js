// upcoming-events.js
console.log("Upcoming-events.js loaded successfully");

import { fetchEvents as fetchFootballEvents, formatEventList as formatFootballList, formatEventTable } from './football-events.js';
import { fetchEvents as fetchTennisEvents, formatEventList as formatTennisList, fetchTournamentMatches } from './tennis-events.js';
import { fetchEvents as fetchGolfEvents, formatEventList as formatGolfList, fetchLeaderboard } from './golf-events.js';
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
    { sport: "horse_racing", league: "uk_irish", icon: "🏇", name: "UK & Irish Racing" }
  ]
};

const SPORT_MODULES = {
  football: { fetch: fetchFootballEvents, format: formatFootballList },
  golf: { fetch: fetchGolfEvents, format: formatGolfList },
  tennis: { fetch: fetchTennisEvents, format: formatTennisList },
  horse_racing: { fetch: fetchHorseRacingEvents, format: formatHorseRacingList }
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
        allEvents = await module.fetch();
        console.log(`Horse Racing: Fetched ${allEvents.length} events`);
      } else {
        const today = new Date();
        const endDate = new Date();
        endDate.setDate(today.getDate() + 90);
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
            console.log(`${config.name}: Fetched ${leagueEvents.length} events`);
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
  console.log("All events fetched:", Object.keys(events).map(key => `${key}: ${events[key].length}`));
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
      title = "Upcoming Events Across All Sports";
      description = "Here are the latest upcoming events in Tipster Arena across all sports:";
      const allEvents = dynamicEvents.all || [];
      if (allEvents.length) {
        const eventsBySport = allEvents.reduce((acc, event) => {
          const sport = event.league ? event.league.split(" ")[0].toLowerCase() : "other"; // Rough sport key derivation
          if (!acc[sport]) acc[sport] = [];
          acc[sport].push(event);
          return acc;
        }, { football: [], golf: [], tennis: [], horse_racing: [] });

        eventList = Object.keys(eventsBySport).map(sport => {
          const sportEvents = eventsBySport[sport];
          if (!sportEvents.length) return "";
          const formatFunc = {
            football: formatFootballList,
            golf: formatGolfList,
            tennis: formatTennisList,
            horse_racing: formatHorseRacingList
          }[sport];
          return `
            <div class="sport-group">
              <h3>${sport.charAt(0).toUpperCase() + sport.slice(1)}</h3>
              <div class="event-list">${formatFunc(sportEvents, sport, true)}</div>
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
      const events = dynamicEvents.football || [];
      const eventsByLeague = events.reduce((acc, event) => {
        const league = event.league || "Other";
        if (!acc[league]) acc[league] = [];
        acc[league].push(event);
        return acc;
      }, {});
      const leagueList = Object.keys(eventsByLeague).map(league => {
        const leagueEvents = eventsByLeague[league];
        const eventItems = leagueEvents.map(event => {
          const home = event.competitors.find(c => c?.homeAway?.toLowerCase() === "home")?.team?.displayName || "TBD";
          const away = event.competitors.find(c => c?.homeAway?.toLowerCase() === "away")?.team?.displayName || "TBD";
          const venue = event.venue.fullName || "TBD";
          return `
            <p class="event-item" style="display: flex; justify-content: space-between; align-items: center;">
              <span>${home} vs ${away} - ${event.displayDate} ${event.time}</span>
              <span class="event-location">${venue}</span>
            </p>
          `;
        }).join("");
        return `<div class="league-group"><p class="league-header"><span class="sport-icon">⚽</span> <strong>${league}</strong></p>${eventItems}</div>`;
      }).join("");
      eventList = events.length ? `<div class="event-list">${leagueList}</div>` : `<p>No upcoming football fixtures available.</p>`;
    } else if (path.includes("/sport/golf/")) {
      // ... (unchanged golf section)
    } else if (path.includes("/sport/tennis/")) {
      // ... (unchanged tennis section)
    } else if (path.includes("/sport/horse_racing/")) {
      // ... (unchanged horse racing section)
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

export { formatFootballList, formatGolfList, formatTennisList, formatHorseRacingList, formatEventTable };