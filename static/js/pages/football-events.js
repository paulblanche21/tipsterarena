// football-events.js
export async function fetchEvents(data, config) {
  const events = (data.events || []).map(event => {
    const competitors = (event.competitions && event.competitions[0]?.competitors) || [];
    const home = competitors.find(c => c?.homeAway?.toLowerCase() === "home") || competitors[0];
    const away = competitors.find(c => c?.homeAway?.toLowerCase() === "away") || competitors[1];

    return {
      id: event.id, // Add event ID for detailed fetch
      name: event.shortName || event.name,
      date: event.date,
      displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      time: new Date(event.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
      state: event.status && event.status.type ? event.status.type.state : "unknown",
      competitors: competitors,
      venue: (event.competitions && event.competitions[0]?.venue) || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } },
      league: config.name,
      icon: config.icon,
      priority: config.priority || 999,
      scores: event.status.type.state === "in" ? {
        homeScore: home?.score || "0",
        awayScore: away?.score || "0",
        clock: event.status.type.clock || "0:00",
        period: event.status.type.period || 0,
        statusDetail: event.status.type.detail || "In Progress"
      } : null
    };
  });

  // Fetch detailed data for in-progress games
  const detailedEvents = await Promise.all(events.map(async event => {
    if (event.state === "in") {
      try {
        const response = await fetch(`https://site.api.espn.com/apis/site/v2/sports/soccer/${config.league}/summary?event=${event.id}`);
        if (!response.ok) throw new Error(`Failed to fetch summary for event ${event.id}`);
        const summaryData = await response.json();
        
        // Extract goal scorers and key stats from play-by-play or box score
        const plays = summaryData.plays || [];
        const goals = plays.filter(play => play.type.text === "Goal").map(play => ({
          scorer: play.participants?.[0]?.athlete?.displayName || "Unknown",
          team: play.team?.displayName || "Unknown",
          time: play.clock?.displayValue || "N/A",
          assist: play.participants?.[1]?.athlete?.displayName || "Unassisted"
        }));

        return {
          ...event,
          detailedStats: {
            goals: goals,
            possession: summaryData.header?.competitions?.[0]?.possession?.text || "N/A",
            shots: {
              home: summaryData.boxscore?.teams?.[0]?.statistics?.find(stat => stat.name === "shots")?.displayValue || "N/A",
              away: summaryData.boxscore?.teams?.[1]?.statistics?.find(stat => stat.name === "shots")?.displayValue || "N/A"
            }
          }
        };
      } catch (error) {
        console.error(`Error fetching detailed stats for ${event.name}:`, error);
        return event; // Return basic event data if detailed fetch fails
      }
    }
    return event;
  }));

  return detailedEvents;
}

export function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  const currentTime = new Date();
  const upcomingEvents = events
    .filter(event => new Date(event.date) > currentTime || event.state === "in")
    .sort((a, b) => {
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
        
        let displayText = event.state === "in" && event.scores ? 
          `<span class="live-score" style="color: #e63946; font-weight: bold;">${event.scores.homeScore} - ${event.scores.awayScore} (${event.scores.statusDetail})</span>` 
          : `${event.displayDate} ${event.time}`;

        return `
          <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
            <span>
              ${homeCrest ? `<img src="${homeCrest}" alt="${homeTeam} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${homeTeam} vs 
              ${awayCrest ? `<img src="${awayCrest}" alt="${awayTeam} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${awayTeam} - ${displayText}
            </span>
            ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
          </p>
        `;
      }).join("");
      eventItems += `<div class="league-group"><p class="league-header"><span class="sport-icon">${icon}</span> <strong>${league}</strong></p>${leagueItems}</div>`;
      totalEvents += eventsToShow.length;
    }
  } else {
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
        
        let displayText = event.state === "in" && event.scores ? 
          `<span class="live-score" style="color: #e63946; font-weight: bold;">${event.scores.homeScore} - ${event.scores.awayScore} (${event.scores.statusDetail})</span>` 
          : `${event.displayDate} ${event.time}`;

        return `
          <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
            <span>
              ${homeCrest ? `<img src="${homeCrest}" alt="${homeTeam} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${homeTeam} vs 
              ${awayCrest ? `<img src="${awayCrest}" alt="${awayTeam} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${awayTeam} - ${displayText}
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
    return `<p class="no-events">No upcoming football fixtures available.</p>`;
  }

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

  let tableHtml = '<table class="event-table">';
  tableHtml += '<thead><tr><th>Event</th><th>Date/Time or Score</th><th>Location</th></tr></thead><tbody>';

  for (const league in eventsByLeague) {
    const leagueEvents = eventsByLeague[league];

    tableHtml += `
      <tr class="league-group">
        <td colspan="3" class="league-header"><span class="sport-icon">⚽</span> ${league}</td>
      </tr>
    `;

    leagueEvents.forEach((event, index) => {
      const homeTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "home")?.team?.displayName || "TBD";
      const awayTeam = event.competitors.find(c => c?.homeAway?.toLowerCase() === "away")?.team?.displayName || "TBD";
      const homeCrest = event.competitors.find(c => c?.homeAway?.toLowerCase() === "home")?.team?.logos?.[0]?.href || "";
      const awayCrest = event.competitors.find(c => c?.homeAway?.toLowerCase() === "away")?.team?.logos?.[0]?.href || "";
      const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
      const timeOrScore = event.state === "in" && event.scores ?
        `<span class="live-score">${event.scores.homeScore} - ${event.scores.awayScore} (${event.scores.statusDetail})</span>` :
        `${event.displayDate} ${event.time}`;

      // Prepare detailed stats for live matches (to be shown in dropdown)
      let details = "";
      if (event.state === "in" && event.detailedStats) {
        const goalsList = event.detailedStats.goals.length ?
          `<ul class="goal-list">
            ${event.detailedStats.goals.map(goal => `
              <li>${goal.scorer} (${goal.team}) - ${goal.time}${goal.assist !== "Unassisted" ? `, Assist: ${goal.assist}` : ""}</li>
            `).join("")}
          </ul>` : "<span class='no-goals'>No goals yet</span>";
        details = `
          <div class="match-details-dropdown" id="match-details-${league}-${index}">
            <div class="detailed-stats">
              ${goalsList}
              <p>Poss: ${event.detailedStats.possession}</p>
              <p>Shots: ${event.detailedStats.shots.home} - ${event.detailedStats.shots.away}</p>
            </div>
          </div>
        `;
      }

      // Add clickable class for live matches
      const rowClass = event.state === "in" ? 'event-item live-match' : 'event-item';

      tableHtml += `
        <tr class="${rowClass}" ${event.state === "in" ? `data-match-id="match-details-${league}-${index}"` : ''}>
          <td class="event-name">
            ${homeCrest ? `<img src="${homeCrest}" alt="${homeTeam} Crest" class="team-crest">` : ""}
            ${homeTeam} vs 
            ${awayCrest ? `<img src="${awayCrest}" alt="${awayTeam} Crest" class="team-crest">` : ""}
            ${awayTeam}
          </td>
          <td class="event-time">${timeOrScore}</td>
          <td class="event-location">${venue}</td>
        </tr>
        ${event.state === "in" ? details : ''}
      `;
    });
  }

  tableHtml += '</tbody></table>';
  return tableHtml;
}