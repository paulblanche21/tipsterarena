// golf-events.js
export async function fetchEvents(data, config) {
    const events = (data.events || []).map(event => ({
      id: event.id, // Add event ID for leaderboard fetching
      name: event.shortName || event.name,
      date: event.date,
      displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      time: new Date(event.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
      state: event.status && event.status.type ? event.status.type.state : "unknown",
      competitors: (event.competitions && event.competitions[0]?.competitors) || [],
      venue: (event.competitions && event.competitions[0]?.venue) || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } },
      league: config.name,
      icon: config.icon,
      leaderboard: event.competitions && event.competitions[0]?.competitors && event.state === "in"
        ? event.competitions[0].competitors.map(comp => ({
            playerName: comp.athlete ? comp.athlete.displayName : "Unknown",
            score: comp.score || "N/A",
            position: comp.position || "N/A"
          }))
        : [] // Only include leaderboard for in-progress events
    }));
    return events;
  }
  
  // Function to fetch updated leaderboard data for a specific event
  export async function fetchLeaderboard(eventId, sport, league) {
    const url = `https://site.api.espn.com/apis/site/v2/sports/${sport}/${league}/scoreboard/${eventId}`;
    console.log(`Fetching leaderboard for event ${eventId}: ${url}`);
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      const leaderboard = data.competitions && data.competitions[0]?.competitors
        ? data.competitions[0].competitors.map(comp => ({
            playerName: comp.athlete ? comp.athlete.displayName : "Unknown",
            score: comp.score || "N/A",
            position: comp.position || "N/A"
          }))
        : [];
      console.log(`Leaderboard for event ${eventId}:`, leaderboard);
      return leaderboard;
    } catch (error) {
      console.error(`Error fetching leaderboard for event ${eventId}:`, error);
      return [];
    }
  }
  
  export function formatEventList(events, sportKey, showLocation = false) {
    if (!events || !events.length) {
      return `<p>No upcoming or in-progress ${sportKey} events available.</p>`;
    }
    const currentTime = new Date(); // March 16, 2025, 12:57 AM GMT
    const upcomingEvents = events.filter(event => {
      const eventTime = new Date(event.date);
      const isUpcoming = eventTime > currentTime && event.state !== "in";
      console.log(`Event for ${event.league} (${event.name}): ${event.displayDate}, ${event.time} - State: ${event.state}, Is Upcoming: ${isUpcoming}`);
      return isUpcoming;
    });
    const inProgressEvents = events.filter(event => event.state === "in" && new Date(event.date) <= currentTime);
  
    if (!upcomingEvents.length && !inProgressEvents.length) {
      return `<p>No upcoming or in-progress ${sportKey} events available.</p>`;
    }
  
    let eventItems = '';
  
    // Format in-progress events with leaderboards
    if (inProgressEvents.length > 0) {
      const inProgressItems = inProgressEvents.map(event => {
        const leaderboardHtml = event.leaderboard && event.leaderboard.length > 0
          ? `
            <div class="leaderboard" data-event-id="${event.id}">
              <h4>Leaderboard (Updated)</h4>
              <ul>
                ${event.leaderboard.slice(0, 5).map(player => `
                  <li>${player.position}. ${player.playerName}: ${player.score}</li>
                `).join("")}
              </ul>
            </div>
          `
          : "<p>No leaderboard data available.</p>";
        return `
          <div class="in-progress-event">
            <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
              <span>${event.name} (In Progress)</span>
              ${showLocation ? `<span class="event-location">${event.venue.fullName}</span>` : ""}
            </p>
            ${leaderboardHtml}
          </div>
        `;
      }).join("");
      eventItems += `<div class="in-progress-section"><h3>In-Progress Events</h3>${inProgressItems}</div>`;
    }
  
    // Format upcoming events
    if (upcomingEvents.length > 0) {
      const eventsByLeague = upcomingEvents.reduce((acc, event) => {
        const league = event.league || "Other";
        if (!acc[league]) {
          acc[league] = [];
        }
        acc[league].push(event);
        return acc;
      }, {});
  
      for (const league in eventsByLeague) {
        const leagueEvents = eventsByLeague[league]
          .slice(0, sportKey === "all" ? 20 : 5)
          .map(event => {
            const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
            return `
              <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
                <span>${event.name} ${event.time}</span>
                ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
              </p>
            `;
          })
          .join("");
        const icon = upcomingEvents.find(event => event.league === league)?.icon || "🏟️";
        eventItems += `<div class="league-group"><p class="league-header"><span class="sport-icon">${icon}</span> <strong>${league}</strong></p>${leagueEvents}</div>`;
      }
    }
  
    console.log(`Formatted ${sportKey} events:`, eventItems);
    return eventItems || `<p>No upcoming or in-progress ${sportKey} events available.</p>`;
  }
  
  // Function to set up periodic leaderboard updates
  export function setupLeaderboardUpdates(sport, league) {
    const interval = 15 * 60 * 1000; // 15 minutes in milliseconds
    setInterval(async () => {
      const inProgressEvents = document.querySelectorAll(".in-progress-event");
      for (const eventElement of inProgressEvents) {
        const eventId = eventElement.querySelector(".leaderboard").getAttribute("data-event-id");
        if (eventId) {
          const leaderboard = await fetchLeaderboard(eventId, sport, league);
          const leaderboardContainer = eventElement.querySelector(".leaderboard");
          if (leaderboardContainer && leaderboard.length > 0) {
            leaderboardContainer.innerHTML = `
              <h4>Leaderboard (Updated)</h4>
              <ul>
                ${leaderboard.slice(0, 5).map(player => `
                  <li>${player.position}. ${player.playerName}: ${player.score}</li>
                `).join("")}
              </ul>
            `;
          }
        }
      }
    }, interval);
  }