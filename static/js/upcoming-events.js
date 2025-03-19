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
      title = "Upcoming Golf Events";
      description = "Here are the latest golf events in Tipster Arena:";
      const golfEvents = dynamicEvents.golf || [];
      const eventsByDate = golfEvents.reduce((acc, event) => {
        const dateKey = event.date.split('T')[0];
        if (!acc[dateKey]) acc[dateKey] = [];
        acc[dateKey].push(event);
        return acc;
      }, {});
      const sortedDates = Object.keys(eventsByDate).sort((a, b) => new Date(a) - new Date(b));
      eventList = sortedDates.map(date => {
        const dateEvents = eventsByDate[date];
        const dateHeader = `<h4>${dateEvents[0].displayDate}</h4>`;
        const eventItems = dateEvents.map(event => `
          <p class="event-item" style="display: flex; justify-content: space-between; align-items: center;">
            <span>${event.name}</span>
            <span class="event-location">${event.venue.fullName || "TBD"}</span>
          </p>
        `).join("");
        return `${dateHeader}<div class="event-list">${eventItems}</div>`;
      }).join("");
      eventList = golfEvents.length ? `<div class="event-list">${eventList}</div>` : `<p>No upcoming golf events available.</p>`;
    } else if (path.includes("/sport/tennis/")) {
      title = "Upcoming ATP Tournament Matches";
      description = "Here are the latest matches for upcoming ATP tournaments:";
      const tennisEvents = dynamicEvents.tennis || [];
      const eventsByDate = tennisEvents.reduce((acc, event) => {
        const dateKey = event.date.split('T')[0];
        if (!acc[dateKey]) acc[dateKey] = [];
        acc[dateKey].push(event);
        return acc;
      }, {});
      const sortedDates = Object.keys(eventsByDate).sort((a, b) => new Date(a) - new Date(b));
      eventList = sortedDates.map(date => {
        const dateEvents = eventsByDate[date];
        const dateHeader = `<h4>${dateEvents[0].displayDate}</h4>`;
        const eventItems = dateEvents.map(event => `
          <p class="event-item" style="display: flex; justify-content: space-between; align-items: center;">
            <span>${event.name}</span>
            <span class="event-location">${event.venue || "TBD"}</span>
          </p>
        `).join("");
        return `${dateHeader}<div class="event-list">${eventItems}</div>`;
      }).join("");
      eventList = tennisEvents.length ? `<div class="event-list">${eventList}</div>` : `<p>No upcoming tennis events available.</p>`;
    } else if (path.includes("/sport/horse_racing/")) {
      title = "Upcoming Horse Racing Meetings";
      description = "Here are the race meetings for the next 7 days:";
      const horseRacingEvents = dynamicEvents.horse_racing || [];
      const eventsByDate = horseRacingEvents.reduce((acc, event) => {
        const dateKey = event.date;
        if (!acc[dateKey]) acc[dateKey] = [];
        acc[dateKey].push(event);
        return acc;
      }, {});
      const sortedDates = Object.keys(eventsByDate).sort((a, b) => new Date(a) - new Date(b));
      eventList = sortedDates.map(date => {
        const dateEvents = eventsByDate[date];
        const dateHeader = `<h4>${dateEvents[0].displayDate}</h4>`;
        const eventItems = dateEvents.map(event => `
          <p class="event-item" style="display: flex; justify-content: space-between; align-items: center;">
            <span>${event.name}</span>
            <span class="event-location">${event.venue}</span>
          </p>
        `).join("");
        return `${dateHeader}<div class="event-list">${eventItems}</div>`;
      }).join("");
      eventList = horseRacingEvents.length ? `<div class="event-list">${eventList}</div>` : `<p>No upcoming horse racing meetings available.</p>`;
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