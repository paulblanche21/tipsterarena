// golf-events.js

/**
 * Fetches and formats event data into a structured object.
 * @param {Object} data - The raw event data from the API.
 * @param {Object} config - Configuration object containing league name and icon.
 * @returns {Promise<Array>} - A promise resolving to an array of formatted event objects.
 */
export async function fetchEvents(data, config) {
  const events = (data.events || []).map(event => ({
    id: event.id,
    name: event.shortName || event.name,
    date: event.date,
    displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
    state: event.status && event.status.type ? event.status.type.state : "unknown",
    competitors: (event.competitions && event.competitions[0]?.competitors) || [],
    venue: (event.competitions && event.competitions[0]?.venue) || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } },
    league: config.name,
    icon: config.icon,
    leaderboard: event.competitions && event.competitions[0]?.competitors && event.status?.type?.state === "in"
      ? event.competitions[0].competitors.map(comp => ({
          playerName: comp.athlete ? comp.athlete.displayName : "Unknown",
          score: comp.score?.value || comp.score || "N/A",
          position: comp.order || "N/A"  // Use comp.order for position
        }))
      : []
  }));
  return events;
}

/**
 * Fetches leaderboard data for a specific event.
 * @param {string} eventId - The ID of the event.
 * @param {string} sport - The sport type (e.g., "golf").
 * @param {string} league - The league name (e.g., "pga").
 * @returns {Promise<Array>} - A promise resolving to an array of leaderboard entries.
 */
export async function fetchLeaderboard(eventId, sport, league) {
  const url = `https://site.api.espn.com/apis/site/v2/sports/${sport}/${league}/scoreboard/${eventId}`;
  console.log(`Fetching leaderboard for event ${eventId}: ${url}`);
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log("Raw competitor data:", data.competitions[0]?.competitors); // Add this log
    const leaderboard = data.competitions && data.competitions[0]?.competitors
      ? data.competitions[0].competitors.map(comp => ({
          playerName: comp.athlete ? comp.athlete.displayName : "Unknown",
          score: comp.score?.value || comp.score || "N/A",
          position: comp.order || "N/A"  // Use comp.order for position
        }))
      : [];
    console.log(`Leaderboard for event ${eventId}:`, leaderboard);
    return leaderboard;
  } catch (error) {
    console.error(`Error fetching leaderboard for event ${eventId}:`, error);
    return [];
  }
}

/**
 * Formats a list of events into HTML for display.
 * @param {Array} events - Array of event objects.
 * @param {string} sportKey - The sport identifier (e.g., "golf" or "all").
 * @param {boolean} [showLocation=false] - Whether to display event locations.
 * @returns {Promise<string>} - A promise resolving to an HTML string of formatted events.
 */
export async function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming or in-progress ${sportKey} events available.</p>`;
  }
  const currentTime = new Date();
  const pgaEvents = events.filter(event => event.league === "PGA Tour");
  const upcomingEvents = pgaEvents.filter(event => {
    const eventTime = new Date(event.date);
    const isUpcoming = eventTime > currentTime && event.state !== "in";
    console.log(`Event for ${event.league} (${event.name}): ${event.displayDate} - State: ${event.state}, Is Upcoming: ${isUpcoming}`);
    return isUpcoming;
  });
  const inProgressEvents = pgaEvents.filter(event => event.state === "in" && new Date(event.date) <= currentTime);

  if (!upcomingEvents.length && !inProgressEvents.length) {
    return `<p>No upcoming or in-progress PGA Tour events available.</p>`;
  }

  let eventItems = '';

  if (sportKey !== "all") {
    // Sidebar view: Show 1 in-progress and up to 3 upcoming PGA Tour events
    const displayEvents = [
      ...(inProgressEvents.length > 0 ? inProgressEvents.slice(0, 1) : []),
      ...upcomingEvents.slice(0, 3)
    ].sort((a, b) => new Date(a.date) - new Date(b.date));

    if (displayEvents.length > 0) {
      const leagueEvents = displayEvents.map(event => {
        const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
        const status = event.state === "in" ? "(In Progress)" : "";
        return `
          <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
            <span>${event.name} ${status} - ${event.displayDate}</span>
            ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
          </p>
        `;
      }).join("");
      const icon = displayEvents[0].icon || "🏟️";
      eventItems = `
        <div class="league-group">
          <p class="league-header"><span class="sport-icon">${icon}</span> <strong>PGA Tour</strong></p>
          <div class="event-list" style="max-height: 200px; overflow-y: auto;">
            ${leagueEvents}
          </div>
        </div>
      `;
    }
  } else {
    // Center feed view: Leaderboard for the current or most recent PGA Tour event
    const currentEvent = inProgressEvents[0] || upcomingEvents[0] || pgaEvents[pgaEvents.length - 1];
    if (currentEvent) {
      const venue = currentEvent.venue.fullName || `${currentEvent.venue.address.city}, ${currentEvent.venue.address.state}`;
      const leaderboard = await fetchLeaderboard(currentEvent.id, "golf", "pga");
      const leaderboardHtml = leaderboard.length > 0
        ? `
          <table class="leaderboard-table" data-event-id="${currentEvent.id}">
            <thead>
              <tr>
                <th>Position</th>
                <th>Player</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              ${leaderboard.slice(0, 5).map(player => `
                <tr>
                  <td>${player.position}</td>
                  <td>${player.playerName}</td>
                  <td>${player.score}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        `
        : "<p>No leaderboard data available.</p>";
      eventItems = `
        <div class="in-progress-event">
          <h2>${currentEvent.name}</h2>
          <p class="event-location">${venue}</p>
          ${leaderboardHtml}
        </div>
      `;
    } else {
      eventItems = `<p>No PGA Tour events available.</p>`;
    }
  }

  console.log(`Formatted ${sportKey} events:`, eventItems);
  return eventItems || `<p>No upcoming or in-progress PGA Tour events available.</p>`;
}

/**
 * Sets up periodic updates for leaderboards of in-progress events.
 * @param {string} sport - The sport type (e.g., "golf").
 * @param {string} league - The league name (e.g., "pga").
 */
export function setupLeaderboardUpdates(sport, league) {
  const interval = 15 * 60 * 1000; // 15 minutes in milliseconds
  setInterval(async () => {
    const inProgressEvents = document.querySelectorAll(".in-progress-event");
    for (const eventElement of inProgressEvents) {
      const eventId = eventElement.querySelector(".leaderboard-table")?.getAttribute("data-event-id");
      if (eventId) {
        const leaderboard = await fetchLeaderboard(eventId, sport, league);
        const leaderboardContainer = eventElement.querySelector(".leaderboard-table");
        if (leaderboardContainer && leaderboard.length > 0) {
          leaderboardContainer.innerHTML = `
            <thead>
              <tr>
                <th>Position</th>
                <th>Player</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              ${leaderboard.slice(0, 5).map(player => `
                <tr>
                  <td>${player.position}</td>
                  <td>${player.playerName}</td>
                  <td>${player.score}</td>
                </tr>
              `).join("")}
            </tbody>
          `;
        }
      }
    }
  }, interval);
}