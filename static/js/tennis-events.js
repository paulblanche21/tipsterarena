// tennis-events.js
export async function fetchEvents(data, config) {
  const events = (data.events || []).map(event => ({
    id: event.id, // Store event ID for later use
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

// New function to fetch matches for a specific tournament
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
        round: comp.notes?.[0]?.headline || "TBD"
      }))
    );
    return matches;
  } catch (error) {
    console.error(`Error fetching matches for tournament ${tournamentId}:`, error);
    return [];
  }
}

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