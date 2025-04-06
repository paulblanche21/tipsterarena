// tennis-events.js

// Fetch tournament events (e.g., list of tournaments)
export async function fetchEvents(data, config) {
  const events = (data.events || []).map(event => ({
    id: event.id,
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
  return events;
}

// Fetch matches for a specific tournament with detailed status and scores
export async function fetchTournamentMatches(tournamentId) {
  const url = `https://site.api.espn.com/apis/site/v2/sports/tennis/atp/scoreboard?event=${tournamentId}`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    const matches = (data.events || []).flatMap(event =>
      (event.competitions || []).map(comp => ({
        id: comp.id,
        date: comp.date,
        displayDate: new Date(comp.date).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "GMT" }),
        time: new Date(comp.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
        player1: comp.competitors[0]?.athlete?.displayName || "TBD",
        player2: comp.competitors[1]?.athlete?.displayName || "TBD",
        status: comp.status?.type?.state || "unknown",
        score: comp.competitors.length === 2 ? `${comp.competitors[0].score || "0"} - ${comp.competitors[1].score || "0"}` : "TBD",
        clock: comp.status?.displayClock || "",
        period: comp.status?.period || 0, // Set number
        round: comp.notes?.[0]?.headline || "TBD",
        completed: comp.status?.type?.completed || false
      }))
    );
    return {
      fixtures: matches.filter(m => m.status === "pre"),
      live: matches.filter(m => m.status === "in"),
      results: matches.filter(m => m.status === "post" && m.completed)
    };
  } catch (error) {
    console.error(`Error fetching matches for tournament ${tournamentId}:`, error);
    return { fixtures: [], live: [], results: [] };
  }
}

// Fetch detailed stats for a live match
export async function fetchMatchDetails(matchId) {
  const url = `https://site.api.espn.com/apis/site/v2/sports/tennis/atp/summary?event=${matchId}`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    return {
      sets: data.sets || [], // Array of set scores
      stats: data.statistics || {} // e.g., aces, double faults
    };
  } catch (error) {
    console.error(`Error fetching match details for ${matchId}:`, error);
    return { sets: [], stats: {} };
  }
}

// Format the center feed table with fixtures, live matches, and results
export function formatEventTable(matches, tournamentName) {
  if (!matches || (!matches.fixtures.length && !matches.live.length && !matches.results.length)) {
    return `<p>No matches available for ${tournamentName}.</p>`;
  }

  let html = `<table class="tennis-feed"><thead><tr><th>Match</th><th>Score/Time</th><th>Round</th></tr></thead><tbody>`;

  // Live Matches
  matches.live.forEach(match => {
    const score = `${match.score} (Set ${match.period}, ${match.clock})`;
    html += `
      <tr class="live-match" data-match-id="${match.id}">
        <td>${match.player1} vs ${match.player2}</td>
        <td style="color: #e63946">${score}</td>
        <td>${match.round}</td>
      </tr>`;
  });

  // Upcoming Fixtures
  matches.fixtures.forEach(match => {
    html += `
      <tr class="fixture">
        <td>${match.player1} vs ${match.player2}</td>
        <td>${match.time}</td>
        <td>${match.round}</td>
      </tr>`;
  });

  // Full-Time Results
  matches.results.forEach(match => {
    html += `
      <tr class="result">
        <td>${match.player1} vs ${match.player2}</td>
        <td>${match.score}</td>
        <td>${match.round}</td>
      </tr>`;
  });

  html += `</tbody></table>`;
  return html;
}

// Keep the existing list format for sidebar or other views
export function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming ${sportKey} tournaments available.</p>`;
  }
  const currentTime = new Date();
  const upcomingEvents = events
    .filter(event => new Date(event.date) > currentTime)
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(0, 3); // Limit to next 3 events
  if (!upcomingEvents.length) {
    return `<p>No upcoming ${sportKey} tournaments available.</p>`;
  }

  const eventItems = upcomingEvents
    .map(event => {
      const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
      return `
        <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;" data-tournament-id="${event.id}">
          <span>${event.name} - ${event.displayDate}</span>
          ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
        </p>
      `;
    })
    .join("");

  return `<div class="league-group"><p class="league-header"><span class="sport-icon">🎾</span> <strong>ATP Tour</strong></p>${eventItems}</div>`;
}