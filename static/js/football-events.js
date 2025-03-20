// football-events.js
export async function fetchEvents(data, config) {
  const events = (data.events || []).map(event => ({
      name: event.shortName || event.name,
      date: event.date,
      displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      time: new Date(event.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
      state: event.status && event.status.type ? event.status.type.state : "unknown",
      competitors: (event.competitions && event.competitions[0]?.competitors) || [],
      venue: (event.competitions && event.competitions[0]?.venue) || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } },
      league: config.name,
      icon: config.icon,
      priority: config.priority || 999  // Add priority from SPORT_CONFIG
  }));
  return events;
}

export function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
      return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  const currentTime = new Date();
  const upcomingEvents = events
      .filter(event => new Date(event.date) > currentTime)
      .sort((a, b) => {
        // Sort by priority first, then by date
        if (a.priority !== b.priority) {
          return a.priority - b.priority;
        }
        return new Date(a.date) - new Date(b.date);
      });

  if (!upcomingEvents.length) {
      return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }

  let eventItems = '';
  if (sportKey !== "all") {
      // Sidebar view: Group by league, limit to 4 total events
      const eventsByLeague = upcomingEvents.reduce((acc, event) => {
          const league = event.league || "Other";
          if (!acc[league]) acc[league] = [];
          acc[league].push(event);
          return acc;
      }, {});

      let totalEvents = 0;
      for (const league in eventsByLeague) {
          if (totalEvents >= 4) break; // Stop after 4 total events
          const leagueEvents = eventsByLeague[league];
          const eventsToShow = leagueEvents.slice(0, 4 - totalEvents); // Take only what fits within 4
          const icon = leagueEvents[0].icon || "🏟️";
          const leagueItems = eventsToShow.map(event => {
              const competitors = event.competitors || [];
              const home = competitors.find(c => c?.homeAway?.toLowerCase() === "home") || competitors[0];
              const away = competitors.find(c => c?.homeAway?.toLowerCase() === "away") || competitors[1];
              const homeTeam = home?.team || { displayName: "TBD" };
              const awayTeam = away?.team || { displayName: "TBD" };
              const homeCrest = homeTeam.logos?.[0]?.href || "";
              const awayCrest = awayTeam.logos?.[0]?.href || "";
              const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
              return `
                  <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
                      <span>
                          ${homeCrest ? `<img src="${homeCrest}" alt="${homeTeam.displayName} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
                          ${homeTeam.displayName} vs 
                          ${awayCrest ? `<img src="${awayCrest}" alt="${awayTeam.displayName} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
                          ${awayTeam.displayName} - ${event.displayDate} ${event.time}
                      </span>
                      ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
                  </p>
              `;
          }).join("");
          eventItems += `<div class="league-group"><p class="league-header"><span class="sport-icon">${icon}</span> <strong>${league}</strong></p>${leagueItems}</div>`;
          totalEvents += eventsToShow.length;
      }
  } else {
      // "Show more" view: Group by league, up to 20 events per league
      const eventsByLeague = upcomingEvents.reduce((acc, event) => {
          const league = event.league || "Other";
          if (!acc[league]) acc[league] = [];
          acc[league].push(event);
          return acc;
      }, {});

      for (const league in eventsByLeague) {
          const leagueEvents = eventsByLeague[league].slice(0, 20).map(event => {
              const competitors = event.competitors || [];
              const home = competitors.find(c => c?.homeAway?.toLowerCase() === "home") || competitors[0];
              const away = competitors.find(c => c?.homeAway?.toLowerCase() === "away") || competitors[1];
              const homeTeam = home?.team || { displayName: "TBD" };
              const awayTeam = away?.team || { displayName: "TBD" };
              const homeCrest = homeTeam.logos?.[0]?.href || "";
              const awayCrest = awayTeam.logos?.[0]?.href || "";
              const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
              return `
                  <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
                      <span>
                          ${homeCrest ? `<img src="${homeCrest}" alt="${homeTeam.displayName} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
                          ${homeTeam.displayName} vs 
                          ${awayCrest ? `<img src="${awayCrest}" alt="${awayTeam.displayName} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
                          ${awayTeam.displayName} - ${event.displayDate} ${event.time}
                      </span>
                      ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
                  </p>
              `;
          }).join("");
          const icon = eventsByLeague[league][0].icon || "🏟️";
          eventItems += `<div class="league-group"><p class="league-header"><span class="sport-icon">${icon}</span> <strong>${league}</strong></p>${leagueEvents}</div>`;
      }
  }

  return eventItems || `<p>No upcoming ${sportKey} fixtures available.</p>`;
}

export function formatEventTable(events) {
  // Check if events exist
  if (!events || !events.length) {
    return `<p>No upcoming football fixtures available.</p>`;
  }

  // Sort events by priority and then by date
  const sortedEvents = events.sort((a, b) => {
    if (a.priority !== b.priority) {
      return a.priority - b.priority;
    }
    return new Date(a.date) - new Date(b.date);
  });

  // Group events by league
  const eventsByLeague = events.reduce((acc, event) => {
    const league = event.league || "Other"; // Default to "Other" if league is missing
    if (!acc[league]) acc[league] = [];
    acc[league].push(event);
    return acc;
  }, {});

  // Start building the table
  let tableHtml = '<table>';
  tableHtml += '<tr><th>Event</th><th>Date</th><th>Time</th><th>Location</th></tr>';

  // Loop through each league and its events
  for (const league in eventsByLeague) {
    const leagueEvents = eventsByLeague[league];

    // Add league header row
    tableHtml += `
      <tr>
        <td colspan="4" style="font-weight: bold; background-color: #f2f2f2;">${league}</td>
      </tr>
    `;

    // Add event rows for this league
    leagueEvents.forEach(event => {
      const homeTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "home")?.team?.displayName || "TBD";
      const awayTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "away")?.team?.displayName || "TBD";
      const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
      tableHtml += `
        <tr>
          <td>${homeTeam} vs ${awayTeam}</td>
          <td>${event.displayDate}</td>
          <td>${event.time}</td>
          <td>${venue}</td>
        </tr>
      `;
    });
  }

  tableHtml += '</table>';
  return tableHtml;
}