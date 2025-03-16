// upcoming-events.js
console.log("Upcoming-events.js loaded successfully");

import { fetchEvents as fetchFootballEvents, formatEventList as formatFootballList } from './football-events.js';
import { fetchEvents as fetchTennisEvents, formatEventList as formatTennisList } from './tennis-events.js';
import { fetchEvents as fetchGolfEvents, formatEventList as formatGolfList } from './golf-events.js';
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
    { sport: "golf", league: "pga", icon: "⛳", name: "PGA Tour" }
  ],
  tennis: [
    { sport: "tennis", league: "atp", icon: "🎾", name: "ATP" }
  ],
  horse_racing: [
    { sport: "racing", league: "horseracing", icon: "🏇", name: "Horse Racing" }
  ]
};

const SPORT_MODULES = {
  football: { fetch: fetchFootballEvents, format: formatFootballList },
  golf: { fetch: fetchGolfEvents, format: formatGolfList },
  tennis: { fetch: fetchTennisEvents, format: formatTennisList },
  horse_racing: { fetch: fetchHorseRacingEvents, format: formatHorseRacingList }
};

export async function getDynamicEvents() {
  const events = {};
  const now = new Date(); // Current date and time (e.g., March 16, 2025, current time)
  for (const sportKey of Object.keys(SPORT_CONFIG)) {
    const sportConfigs = SPORT_CONFIG[sportKey];
    const module = SPORT_MODULES[sportKey];
    if (module) {
      let allEvents = [];
      const today = new Date();
      const endDate = new Date();
      endDate.setDate(today.getDate() + 16); // Fetch up to March 31, 2025
      const todayStr = today.toISOString().split('T')[0].replace(/-/g, ''); // 20250315
      const endDateStr = endDate.toISOString().split('T')[0].replace(/-/g, ''); // 20250331
      for (const config of sportConfigs) {
        const url = `https://site.api.espn.com/apis/site/v2/sports/${config.sport}/${config.league}/scoreboard?dates=${todayStr}-${endDateStr}`;
        console.log(`Fetching with URL for ${config.name}: ${url}`);
        try {
          const response = await fetch(url);
          if (!response.ok) {
            console.log(`Response text for ${config.name}:`, await response.text());
            throw new Error(`HTTP error! status: ${response.status} for ${config.name}`);
          }
          const data = await response.json();
          console.log(`Raw response for ${config.name}:`, data);
          const leagueEvents = await module.fetch(data, config);
          // Filter out past events
          const futureEvents = leagueEvents.filter(event => new Date(event.date) > now);
          allEvents = allEvents.concat(futureEvents);
          console.log(`${sportKey} future events fetched for ${config.name}:`, futureEvents);
        } catch (error) {
          console.error(`Error fetching ${config.name}:`, error);
          if (sportKey === "horse_racing") {
            console.log("Horse racing not supported by ESPN API. Awaiting alternative API.");
          }
        }
      }
      events[sportKey] = allEvents;
      console.log(`All ${sportKey} future events combined:`, allEvents);
    }
  }
  console.log("All future events fetched:", events);
  events.all = [
    ...(events.football || []),
    ...(events.golf || []),
    ...(events.tennis || []),
    ...(events.horse_racing || [])
  ].sort((a, b) => new Date(a.date) - new Date(b.date));
  console.log("All future events after sorting:", events.all);
  return events;
}

export async function getEventList(currentPath, target) {
  const path = currentPath.toLowerCase();
  let title = "";
  let description = "";
  let eventList = "";
  const dynamicEvents = await getDynamicEvents();
  console.log("Dynamic events for rendering:", dynamicEvents);
  if (target === "upcoming-events") {
    if (path === "/" || path === "/home/") {
      title = "Upcoming Events";
      description = "Here are the latest upcoming events in Tipster Arena:";
      // Show all football events (not just Premier League)
      eventList = `<div class="event-list">${formatFootballList(dynamicEvents.football, "football", true)}</div>`;
      // Optional: Uncomment below to show all sports on home page "Show More"
      // eventList = `<div class="event-list">${formatFootballList(dynamicEvents.football, "football", true) + formatGolfList(dynamicEvents.golf, "golf", true) + formatTennisList(dynamicEvents.tennis, "tennis", true) + formatHorseRacingList(dynamicEvents.horse_racing, "horse_racing", true)}</div>`;
    } else if (path.includes("/sport/football/")) {
      title = "Upcoming Football Fixtures";
      description = "Here are the latest football fixtures in Tipster Arena:";
      // Show all football fixtures
      eventList = `<div class="event-list">${formatFootballList(dynamicEvents.football, "all", true)}</div>`;
    } else if (path.includes("/sport/golf/")) {
      title = "Upcoming Golf Events";
      description = "Here are the latest golf events in Tipster Arena:";
      eventList = `<div class="event-list">${formatGolfList(dynamicEvents.golf, "golf", true)}</div>`;
    } else if (path.includes("/sport/tennis/")) {
      title = "Upcoming Tennis Events";
      description = "Here are the latest tennis events in Tipster Arena:";
      eventList = `<div class="event-list">${formatTennisList(dynamicEvents.tennis, "tennis", true)}</div>`;
    } else if (path.includes("/sport/horse_racing/")) {
      title = "Upcoming Horse Racing Events";
      description = "Here are the latest horse racing events in Tipster Arena:";
      eventList = `<div class="event-list">${formatHorseRacingList(dynamicEvents.horse_racing, "horse_racing", true)}</div>`;
    }
  }
  console.log(`Generated event list for ${target}:`, eventList);
  return `
    <div class="events-popup">
      <h2>${title}</h2>
      <p>${description}</p>
      ${eventList}
      <a href="#" class="show-less" data-target="${target}">Show less</a>
    </div>
  `;
}