// football-events.js
export async function fetchEvents(data, config) {
  const events = (data.events || []).map(event => {
    const competitors = (event.competitions && event.competitions[0]?.competitors) || [];
    const home = competitors.find(c => c?.homeAway?.toLowerCase() === "home") || competitors[0];
    const away = competitors.find(c => c?.homeAway?.toLowerCase() === "away") || competitors[1];

    return {
      name: event.shortName || event.name,
      date: event.date,
      displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      time: new Date(event.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
      state: event.status && event.status.type ? event.status.type.state : "unknown", // pre, in, post
      competitors: competitors,
      venue: (event.competitions && event.competitions[0]?.venue) || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } },
      league: config.name,
      icon: config.icon,
      priority: config.priority || 999,
      // Add real-time score data for in-progress games
      scores: event.status.type.state === "in" ? {
        homeScore: home?.score || "0",
        awayScore: away?.score || "0",
        clock: event.status.type.clock || "0:00",
        period: event.status.type.period || 0,
        statusDetail: event.status.type.detail || "In Progress"
      } : null
    };
  });
  return events;
}

export function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  const currentTime = new Date();
  const upcomingEvents = events
    .filter(event => new Date(event.date) > currentTime || event.state === "in") // Include in-progress games
    .sort((a, b) => {
      // Sort by state (in-progress first), then priority, then date
      if (a.state === "in" && b.state !== "in") return -1;
      if (a.state !== "in" && b.state === "in") return 1;
      if (a.priority !== b.priority) return a.priority - b.priority;
      return new Date(a.date) - new Date(b.date);
    });

  if (!upcomingEvents.length) {
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }

  let eventItems = '';
  if (sportKey !== "all") {
    // Sidebar view: Group by league, limit to 4 total events (prioritize live games)
    const eventsByLeague = upcomingEvents.reduce((acc, event) => {
      const league = event.league || "Other";
      if (!acc[league]) acc[league] = [];
      acc[league].push(event);
      return acc;
    }, {});

    let totalEvents = 0;
    for (const league in eventsByLeague) {
      if (totalEvents >= 4) break;
      const leagueEvents = eventsByLeague[league];
      const eventsToShow = leagueEvents.slice(0, 4 - totalEvents);
      const icon = leagueEvents[0].icon || "⚽";
      const leagueItems = eventsToShow.map(event => {
        const homeTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "home")?.team?.displayName || "TBD";
        const awayTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "away")?.team?.displayName || "TBD";
        const homeCrest = event.competitors.find(c => c?.homeAway?.toLowerCase() === "home")?.team?.logos?.[0]?.href || "";
        const awayCrest = event.competitors.find(c => c?.homeAway?.toLowerCase() === "away")?.team?.logos?.[0]?.href || "";
        const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
        
        // Add live score display for in-progress games
        const liveScore = event.state === "in" && event.scores ? 
          `<span class="live-score" style="color: #e63946; font-weight: bold;">${event.scores.homeScore} - ${event.scores.awayScore} (${event.scores.statusDetail})</span>` 
          : `${event.displayDate} ${event.time}`;

        return `
          <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
            <span>
              ${homeCrest ? `<img src="${homeCrest}" alt="${homeTeam} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${homeTeam} vs 
              ${awayCrest ? `<img src="${awayCrest}" alt="${awayTeam} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${awayTeam} - ${liveScore}
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
        const homeTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "home")?.team?.displayName || "TBD";
        const awayTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "away")?.team?.displayName || "TBD";
        const homeCrest = event.competitors.find(c => c?.homeAway?.toLowerCase() === "home")?.team?.logos?.[0]?.href || "";
        const awayCrest = event.competitors.find(c => c?.homeAway?.toLowerCase() === "away")?.team?.logos?.[0]?.href || "";
        const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
        
        // Add live score display for in-progress games
        const liveScore = event.state === "in" && event.scores ? 
          `<span class="live-score" style="color: #e63946; font-weight: bold;">${event.scores.homeScore} - ${event.scores.awayScore} (${event.scores.statusDetail})</span>` 
          : `${event.displayDate} ${event.time}`;

        return `
          <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
            <span>
              ${homeCrest ? `<img src="${homeCrest}" alt="${homeTeam} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${homeTeam} vs 
              ${awayCrest ? `<img src="${awayCrest}" alt="${awayTeam} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${awayTeam} - ${liveScore}
            </span>
            ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
          </p>
        `;
      }).join("");
      const icon = eventsByLeague[league][0].icon || "⚽";
      eventItems += `<div class="league-group"><p class="league-header"><span class="sport-icon">${icon}</span> <strong>${league}</strong></p>${leagueEvents}</div>`;
    }
  }

  return eventItems || `<p>No upcoming ${sportKey} fixtures available.</p>`;
}

export function formatEventTable(events) {
  if (!events || !events.length) {
    return `<p>No upcoming football fixtures available.</p>`;
  }

  // Sort events: in-progress first, then by priority, then by date
  const sortedEvents = events.sort((a, b) => {
    if (a.state === "in" && b.state !== "in") return -1;
    if (a.state !== "in" && b.state === "in") return 1;
    if (a.priority !== b.priority) return a.priority - b.priority;
    return new Date(a.date) - new Date(b.date);
  });

  const eventsByLeague = sortedEvents.reduce((acc, event) => {
    const league = event.league || "Other";
    if (!acc[league]) acc[league] = [];
    acc[league].push(event);
    return acc;
  }, {});

  let tableHtml = '<table>';
  tableHtml += '<tr><th>Event</th><th>Date/Time or Score</th><th>Location</th></tr>';

  for (const league in eventsByLeague) {
    const leagueEvents = eventsByLeague[league];

    tableHtml += `
      <tr>
        <td colspan="3" style="font-weight: bold; background-color: #f2f2f2;">${league}</td>
      </tr>
    `;

    leagueEvents.forEach(event => {
      const homeTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "home")?.team?.displayName || "TBD";
      const awayTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "away")?.team?.displayName || "TBD";
      const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
      // Show live score if in-progress, otherwise show date/time
      const timeOrScore = event.state === "in" && event.scores ?
        `${event.scores.homeScore} - ${event.scores.awayScore} (${event.scores.statusDetail})` :
        `${event.displayDate} ${event.time}`;

      tableHtml += `
        <tr>
          <td>${homeTeam} vs ${awayTeam}</td>
          <td style="${event.state === 'in' ? 'color: #e63946; font-weight: bold;' : ''}">${timeOrScore}</td>
          <td>${venue}</td>
        </tr>
      `;
    });
  }

  tableHtml += '</table>';
  return tableHtml;
}