// upcoming-events.js
console.log("Upcoming-events.js loaded successfully");

import { fetchEvents as fetchFootballEvents, formatEventList as formatFootballList, formatEventTable } from './football-events.js';
import { fetchEvents as fetchTennisEvents, formatEventList as formatTennisList, fetchTournamentMatches } from './tennis-events.js';
import { fetchEvents as fetchGolfEvents, formatEventList as formatGolfList, fetchLeaderboard } from './golf-events.js';
import { fetchEvents as fetchHorseRacingEvents, formatEventList as formatHorseRacingList } from './horse-racing-events.js';

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
        // Set date range: 7 days for football, 90 days for others
        const daysToFetch = sportKey === "football" ? 7 : 90;
        endDate.setDate(today.getDate() + daysToFetch);
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
      // Sort other sports by date (football sorting is handled in football-events.js)
      if (sportKey !== "football") {
        allEvents.sort((a, b) => new Date(a.date) - new Date(b.date));
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
    if (path === "/" || path === "/home/" || path === "/explore/") {
      title = "Upcoming Events Across All Sports";
      description = "Here are the latest upcoming events across all sports:";
      const allEvents = dynamicEvents.all || [];
      if (allEvents.length) {
        // Group events by sport using a more reliable method
        const eventsBySport = {
          football: dynamicEvents.football || [],
          golf: dynamicEvents.golf || [],
          tennis: dynamicEvents.tennis || [],
          horse_racing: dynamicEvents.horse_racing || []
        };

        eventList = Object.keys(eventsBySport).map(sport => {
          const sportEvents = eventsBySport[sport];
          if (!sportEvents.length) return "";
          const formatFunc = {
            football: sport === 'football' ? formatEventTable : formatFootballList, // Use table for football
            golf: formatGolfList,
            tennis: formatTennisList,
            horse_racing: formatHorseRacingList
          }[sport];
          return `
            <div class="sport-group">
              <h3>${sport.charAt(0).toUpperCase() + sport.slice(1)}</h3>
              <div class="${sport === 'football' ? 'event-table' : 'event-list'}">
                ${sport === 'football' ? formatFunc(sportEvents) : formatFunc(sportEvents, sport, true)}
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
      const events = dynamicEvents.football || [];
      // Use formatEventTable for consistency with home.html
      eventList = events.length ? `<div class="event-table">${formatEventTable(events)}</div>` : `<p>No upcoming football fixtures available.</p>`;
    } else if (path.includes("/sport/golf/")) {
      title = "PGA Tour Leaderboard";
      description = "Leaderboard for the most recent or in-progress PGA Tour event:";
      const pgaEvents = (dynamicEvents.golf || []).filter(event => event.league === "PGA Tour");
      const currentEvent = pgaEvents.find(event => event.state === "in") || pgaEvents.sort((a, b) => new Date(b.date) - new Date(a.date))[0];
      if (currentEvent) {
        const leaderboard = await fetchLeaderboard(currentEvent.id, "golf", "pga");
        const venue = currentEvent.venue.fullName || "TBD";
        eventList = leaderboard.length ? `
          <div class="in-progress-event">
            <h3>${currentEvent.name} - ${currentEvent.displayDate}</h3>
            <p class="event-location">${venue}</p>
            <table class="leaderboard-table">
              <thead>
                <tr>
                  <th>Position</th>
                  <th>Player</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                ${leaderboard.map(player => `
                  <tr>
                    <td>${player.position}</td>
                    <td>${player.playerName}</td>
                    <td>${player.score}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        ` : `<p>No leaderboard data available for ${currentEvent.name}.</p>`;
      } else {
        eventList = `<p>No current or recent PGA Tour events available.</p>`;
      }
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
        const eventItems = dateEvents.map(async event => {
          const matches = await fetchTournamentMatches(event.id);
          const matchItems = matches.map(match => `
            <p class="event-item" style="display: flex; justify-content: space-between; align-items: center;">
              <span>${match.player1} vs ${match.player2} ${match.time ? '- ' + match.time : ''}</span>
              <span class="event-location">${event.venue.fullName || "TBD"}</span>
            </p>
          `).join("");
          return `<div class="tournament-group"><p class="tournament-header">${event.name}</p>${matchItems}</div>`;
        });
        return Promise.all(eventItems).then(items => `${dateHeader}<div class="event-list">${items.join("")}</div>`);
      });
      eventList = await Promise.all(eventList).then(results => results.join(""));
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