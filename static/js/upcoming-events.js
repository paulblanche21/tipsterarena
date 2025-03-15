// upcoming-events.js
console.log("Upcoming-events.js loaded successfully");

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
  golf: [{ sport: "golf", league: "pga", icon: "⛳", name: "PGA Tour" }],
  tennis: [{ sport: "tennis", league: "atp", icon: "🎾", name: "ATP" }],
  horse_racing: [{ sport: "racing", league: "horseracing", icon: "🏇", name: "Horse Racing" }]
};

async function fetchEvents(sportKey) {
  const configs = SPORT_CONFIG[sportKey] || [];
  let allEvents = [];
  const today = new Date();
  const endDate = new Date();
  endDate.setDate(today.getDate() + 16); // Fetch up to March 31, 2025
  const todayStr = today.toISOString().split('T')[0].replace(/-/g, ''); // 20250315
  const endDateStr = endDate.toISOString().split('T')[0].replace(/-/g, ''); // 20250331
  for (const config of configs) {
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
      const events = (data.events || []).map(event => ({
        name: event.shortName || event.name,
        date: event.date,
        displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
        time: new Date(event.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
        state: event.status && event.status.type ? event.status.type.state : "unknown",
        competitors: (event.competitions && event.competitions[0]?.competitors) || [],
        venue: (event.competitions && event.competitions[0]?.venue) || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } },
        league: config.name,
        icon: config.icon
      }));
      allEvents = allEvents.concat(events);
      console.log(`${sportKey} events fetched for ${config.name}:`, events);
    } catch (error) {
      console.error(`Error fetching ${config.name}:`, error);
      if (sportKey === "horse_racing") {
        console.log("Horse racing not supported by ESPN API. Awaiting alternative API.");
      }
    }
  }
  console.log(`All ${sportKey} events combined:`, allEvents);
  return allEvents;
}

function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  const currentTime = new Date();
  const upcomingEvents = events.filter(event => {
    const eventTime = new Date(event.date);
    const isUpcoming = eventTime > currentTime;
    console.log(`Event for ${event.league} (${event.name}): ${event.displayDate}, ${event.time} - State: ${event.state}, Is Upcoming: ${isUpcoming}`);
    return isUpcoming;
  });
  if (!upcomingEvents.length) {
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  console.log(`Upcoming ${sportKey} events before grouping:`, upcomingEvents);
  // Group by league
  const eventsByLeague = upcomingEvents.reduce((acc, event) => {
    const league = event.league || "Other";
    if (!acc[league]) {
      acc[league] = [];
    }
    acc[league].push(event);
    return acc;
  }, {});
  console.log(`Events grouped by league for ${sportKey}:`, eventsByLeague);

  let eventItems = '';
  for (const league in eventsByLeague) {
    const leagueEvents = eventsByLeague[league]
      .slice(0, sportKey === "all" ? 20 : 5)
      .map(event => {
        const competitors = event.competitors || [];
        const home = competitors.find(c => c.homeAway === "home");
        const away = competitors.find(c => c.homeAway === "away");
        const homeCrest = home?.team.logos?.[0]?.href || "";
        const awayCrest = away?.team.logos?.[0]?.href || "";
        const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
        // Conditionally include location based on showLocation parameter
        return `
          <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
            <span>
              ${homeCrest ? `<img src="${homeCrest}" alt="${home.team.displayName} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${home.team.displayName} vs 
              ${awayCrest ? `<img src="${awayCrest}" alt="${away.team.displayName} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${away.team.displayName}, ${event.displayDate}, ${event.time}
            </span>
            ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
          </p>
        `;
      })
      .join("");
    const icon = upcomingEvents.find(event => event.league === league)?.icon || "🏟️";
    eventItems += `<div class="league-group"><p class="league-header"><span class="sport-icon">${icon}</span> <strong>${league}</strong></p>${leagueEvents}</div>`;
  }
  console.log(`Formatted ${sportKey} events:`, eventItems);
  return eventItems || `<p>No upcoming ${sportKey} fixtures available.</p>`;
}

async function getDynamicEvents() {
  const events = {};
  for (const sportKey of Object.keys(SPORT_CONFIG)) {
    events[sportKey] = await fetchEvents(sportKey);
  }
  console.log("All events fetched:", events);
  events.all = [
    ...(events.football || []),
    ...(events.golf || []),
    ...(events.tennis || []),
    ...(events.horse_racing || [])
  ].sort((a, b) => new Date(a.date) - new Date(b.date));
  console.log("All events after sorting:", events.all);
  return events;
}

async function getEventList(currentPath, target) {
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
      // Show all football leagues in the "Show more" modal with location
      eventList = `<div class="event-list">${formatEventList(dynamicEvents.football, "all", true)}</div>`;
    } else if (path.includes("/sport/football/")) {
      title = "Upcoming Football Fixtures";
      description = "Here are the latest football fixtures in Tipster Arena:";
      eventList = `<div class="event-list">${formatEventList(dynamicEvents.football, "all", true)}</div>`;
    } else if (path.includes("/sport/golf/")) {
      title = "Upcoming Golf Events";
      description = "Here are the latest golf events in Tipster Arena:";
      eventList = `<div class="event-list">${formatEventList(dynamicEvents.golf, "golf", true)}</div>`;
    } else if (path.includes("/sport/tennis/")) {
      title = "Upcoming Tennis Events";
      description = "Here are the latest tennis events in Tipster Arena:";
      eventList = `<div class="event-list">${formatEventList(dynamicEvents.tennis, "tennis", true)}</div>`;
    } else if (path.includes("/sport/horse_racing/")) {
      title = "Upcoming Horse Racing Events";
      description = "Here are the latest horse racing events in Tipster Arena:";
      eventList = `<div class="event-list">${formatEventList(dynamicEvents.horse_racing, "horse_racing", true)}</div>`;
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

async function populateCarousel() {
  if (document.querySelector(".carousel-container")) {
    console.log("Populating carousel");
    const events = await getDynamicEvents();
    console.log("All events for carousel:", events);
    const sports = ["football", "golf", "tennis", "horse_racing"];
    sports.forEach(sport => {
      const container = document.getElementById(`${sport.replace('_', '-')}-events`);
      if (container) {
        const filteredEvents = sport === "football"
          ? events[sport].filter(event => event.league === "Premier League")
          : events[sport];
        // Do not show location in the carousel
        const eventList = formatEventList(filteredEvents, sport, false);
        container.innerHTML = eventList;
        console.log(`${sport} carousel updated with:`, container.innerHTML);
      } else {
        console.error(`Container not found for ${sport}`);
      }
    });

    const dots = document.querySelectorAll(".carousel-dots .dot");
    const slides = document.querySelectorAll(".carousel-slide");
    dots.forEach(dot => {
      dot.addEventListener("click", () => {
        dots.forEach(d => d.classList.remove("active"));
        slides.forEach(s => s.classList.remove("active"));
        dot.classList.add("active");
        const sport = dot.getAttribute("data-sport");
        document.querySelector(`.carousel-slide[data-sport="${sport}"]`).classList.add("active");
      });
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  populateCarousel();
});

export { fetchEvents, formatEventList, getDynamicEvents, getEventList };