export async function fetchEvents(data, config) {
  // No changes needed here since this function doesn't handle headshots
  const events = (data.events || []).map(event => {
    const competitions = event.competitions && event.competitions[0] ? event.competitions[0] : {};
    const venue = competitions.venue || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } };
    console.log(`Raw venue data for event ${event.name}:`, venue); // Debug log

    let finalVenue = venue;
    if (event.name === "Valero Texas Open" && venue.fullName === "Location TBD") {
      finalVenue = {
        fullName: "TPC San Antonio (Oaks Course)",
        address: { city: "San Antonio", state: "TX" }
      };
    }

    const courseDetails = competitions.course || {};
    const broadcast = event.broadcasts && event.broadcasts[0] ? event.broadcasts[0].media : { shortName: "N/A" };
    const status = event.status || {};
    const period = status.period || 1;
    const totalRounds = event.format?.rounds || 4;
    const isPlayoff = status.playoff || false;

    return {
      id: event.id,
      name: event.name,
      shortName: event.shortName || event.name,
      date: event.date,
      displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      state: event.status && event.status.type ? event.status.type.state : "unknown",
      completed: event.status && event.status.type ? event.status.type.completed : false,
      venue: finalVenue,
      course: {
        name: courseDetails.name || "Unknown Course",
        par: courseDetails.par || "N/A",
        yardage: courseDetails.yardage || "N/A",
      },
      purse: event.purse || "N/A",
      broadcast: broadcast.shortName || "N/A",
      currentRound: period,
      totalRounds: totalRounds,
      isPlayoff: isPlayoff,
      league: config.name,
      icon: config.icon,
    };
  });
  return events;
}

export async function fetchLeaderboard(eventId, sport, league) {
  const url = `https://site.api.espn.com/apis/site/v2/sports/${sport}/${league}/scoreboard/${eventId}`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    const leaderboardData = data?.competitions?.[0].competitors || [];
    console.log('Raw competitor data:', leaderboardData);

    const leaderboard = leaderboardData.map((competitor, index) => {
      const roundsStat = competitor.linescores?.map(round => round.value) || [];
      const strokesStat = roundsStat.length === 4 ? roundsStat.reduce((sum, score) => sum + score, 0) : (competitor.strokes || "N/A");

      // Log athlete data to debug world ranking
      console.log('Athlete data for competitor:', competitor.athlete);

      return {
        position: competitor.position || (index + 1),
        playerName: competitor.athlete?.displayName || "Unknown",
        score: competitor.score || "N/A",
        rounds: roundsStat.length > 0 ? roundsStat : ["N/A", "N/A", "N/A", "N/A"],
        strokes: strokesStat,
        worldRanking: competitor.athlete?.worldRanking || "N/A",
      };
    });
    console.log(`Leaderboard for event ${eventId}:`, leaderboard);
    return leaderboard;
  } catch (error) {
    console.error(`Error fetching leaderboard for event ${eventId}:`, error);
    return [];
  }
}

export async function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming or in-progress ${sportKey} events available.</p>`;
  }

  const currentTime = new Date();
  const pgaEvents = events.filter(event => event.league === "PGA Tour");
  const inProgressEvents = pgaEvents.filter(event => event.state === "in" && new Date(event.date) <= currentTime);
  const upcomingEvents = pgaEvents
    .filter(event => new Date(event.date) > currentTime && event.state !== "in")
    .sort((a, b) => new Date(a.date) - new Date(b.date));
  const completedEvents = pgaEvents
    .filter(event => event.state === "post" && event.completed)
    .sort((a, b) => new Date(b.date) - new Date(a.date));

  if (!inProgressEvents.length && !upcomingEvents.length && !completedEvents.length) {
    return `<p>No PGA Tour events available.</p>`;
  }

  let eventItems = '';

  if (sportKey !== "all") {
    const displayEvents = [
      ...(inProgressEvents.length > 0 ? inProgressEvents.slice(0, 1) : []),
      ...upcomingEvents.slice(0, 3 - inProgressEvents.length)
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
    let currentEvent = null;
    let displayType = '';
    let nextEvent = null;

    if (inProgressEvents.length > 0) {
      currentEvent = inProgressEvents[0];
      displayType = 'in-progress';
    } else {
      nextEvent = upcomingEvents[0];
      const nextEventStartTime = nextEvent ? new Date(nextEvent.date) : null;

      if (completedEvents.length > 0) {
        const mostRecentEvent = completedEvents[0];
        if (!nextEventStartTime || currentTime < nextEventStartTime) {
          currentEvent = mostRecentEvent;
          displayType = 'completed';
        }
      }

      if (!currentEvent && nextEvent) {
        currentEvent = nextEvent;
        displayType = 'upcoming';
        nextEvent = upcomingEvents[1];
      }
    }

    console.log('Selected currentEvent:', currentEvent, 'Display Type:', displayType, 'Next Event:', nextEvent);

    if (currentEvent) {
      const venue = currentEvent.venue.fullName || `${currentEvent.venue.address.city}, ${currentEvent.venue.address.state}`;
      let contentHtml = '';

      if (displayType === 'in-progress' || displayType === 'completed') {
        const leaderboard = await fetchLeaderboard(currentEvent.id, "golf", "pga");
        contentHtml = leaderboard.length > 0
          ? `
            <div class="leaderboard-content">
              <h4>Full Leaderboard</h4>
              <div class="leaderboard-wrapper" style="max-height: 400px; overflow-y: auto;">
                <table class="leaderboard-table" data-event-id="${currentEvent.id}">
                  <thead>
                    <tr>
                      <th>Position</th>
                      <th>Player</th>
                      <th>Score</th>
                      <th>Rounds</th>
                      <th>Total Strokes</th>
                      <th>World Ranking</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${leaderboard.map(player => `
                      <tr>
                        <td>${player.position}</td>
                        <td>${player.playerName}</td>
                        <td>${player.score}</td>
                        <td>${player.rounds.join(", ") || "N/A"}</td>
                        <td>${player.strokes}</td>
                        <td>${player.worldRanking}</td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>
              </div>
            </div>
          `
          : "<p>No leaderboard data available for this event.</p>";
      } else if (displayType === 'upcoming') {
        contentHtml = `
          <div class="event-details">
            <p><strong>Next Event:</strong> ${currentEvent.name}</p>
            <p><strong>Date:</strong> ${currentEvent.displayDate}</p>
            <p><strong>Location:</strong> ${venue}</p>
            <p><strong>Course:</strong> ${currentEvent.course.name}</p>
            <p><strong>Par:</strong> ${currentEvent.course.par}</p>
            <p><strong>Yardage:</strong> ${currentEvent.course.yardage}</p>
            <p><strong>Purse:</strong> ${currentEvent.purse}</p>
            <p><strong>Broadcast:</strong> ${currentEvent.broadcast}</p>
            <p><strong>Total Rounds:</strong> ${currentEvent.totalRounds}</p>
          </div>
        `;
      }

      const additionalDetails = `
        <div class="additional-details">
          <h4>Event Details</h4>
          <p><strong>Course:</strong> ${currentEvent.course.name}</p>
          <p><strong>Par:</strong> ${currentEvent.course.par}</p>
          <p><strong>Yardage:</strong> ${currentEvent.course.yardage}</p>
          <p><strong>Purse:</strong> ${currentEvent.purse}</p>
          <p><strong>Broadcast:</strong> ${currentEvent.broadcast}</p>
          <p><strong>Current Round:</strong> ${currentEvent.currentRound} of ${currentEvent.totalRounds}</p>
          ${currentEvent.isPlayoff ? '<p><strong>Playoff:</strong> In Progress</p>' : ''}
        </div>
      `;

      let nextEventHtml = '';
      if (displayType === 'completed' && nextEvent) {
        const nextVenue = nextEvent.venue.fullName || `${nextEvent.venue.address.city}, ${nextEvent.venue.address.state}`;
        nextEventHtml = `
          <div class="next-event-details">
            <h4>Next Event</h4>
            <p><strong>Event:</strong> ${nextEvent.name}</p>
            <p><strong>Date:</strong> ${nextEvent.displayDate}</p>
            <p><strong>Location:</strong> ${nextVenue}</p>
            <p><strong>Course:</strong> ${nextEvent.course.name}</p>
            <p><strong>Par:</strong> ${nextEvent.course.par}</p>
            <p><strong>Yardage:</strong> ${nextEvent.course.yardage}</p>
            <p><strong>Purse:</strong> ${nextEvent.purse}</p>
            <p><strong>Broadcast:</strong> ${nextEvent.broadcast}</p>
            <p><strong>Total Rounds:</strong> ${nextEvent.totalRounds}</p>
          </div>
        `;
      }

      const liveIndicator = displayType === 'in-progress' ? '<span class="live-indicator">Live</span>' : '';

      eventItems = `
        <div class="golf-card">
          <div class="card-header">
            <div class="event-info">
              <span class="event-name">${currentEvent.name}</span>
              <span class="event-status">(${displayType === 'in-progress' ? 'In Progress' : displayType === 'completed' ? 'Completed' : 'Upcoming'})</span>
              ${liveIndicator}
            </div>
            <div class="event-meta">
              <span class="datetime">${currentEvent.displayDate}</span>
              <span class="location">${venue}</span>
            </div>
          </div>
          <div class="card-content">
            ${contentHtml}
            ${additionalDetails}
            ${nextEventHtml}
          </div>
        </div>
      `;
    } else {
      eventItems = `<p>No PGA Tour events available.</p>`;
    }
  }

  console.log('Generated eventItems:', eventItems);
  return eventItems || `<p>No upcoming or in-progress PGA Tour events available.</p>`;
}

export async function setupLeaderboardUpdates() {
  const leaderboardTables = document.querySelectorAll('.leaderboard-table');
  if (leaderboardTables.length === 0) return;

  // In formatEventList, within the leaderboard table
contentHtml = leaderboard.length > 0
? `
  <div class="leaderboard-content">
    <h4>Full Leaderboard</h4>
    <div class="leaderboard-wrapper" style="max-height: 400px; overflow-y: auto;">
      <table class="leaderboard-table" data-event-id="${currentEvent.id}">
        <thead>
          <tr>
            <th>Position</th>
            <th>Player</th>
            <th>Score</th>
            <th>Rounds</th>
            <th>Total Strokes</th>
            <th>World Ranking</th>
          </tr>
        </thead>
        <tbody>
          ${leaderboard.map(player => `
            <tr>
              <td>${player.position}</td>
              <td>${player.playerName}</td>
              <td>${player.score}</td>
              <td>${player.rounds.join(", ") || "N/A"}</td>
              <td>${player.strokes}</td>
              <td>${player.worldRanking}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  </div>
`
: "<p>No leaderboard data available for this event.</p>";

// In setupLeaderboardUpdates
const updateLeaderboard = async (table) => {
const eventId = table.getAttribute('data-event-id');
if (!eventId) return;

const leaderboard = await fetchLeaderboard(eventId, "golf", "pga");
if (leaderboard.length > 0) {
  const tbody = table.querySelector('tbody');
  tbody.innerHTML = leaderboard.map(player => `
    <tr>
      <td>${player.position}</td>
      <td>${player.playerName}</td>
      <td>${player.score}</td>
      <td>${player.rounds.join(", ") || "N/A"}</td>
      <td>${player.strokes}</td>
      <td>${player.worldRanking}</td>
    </tr>
  `).join("");
}
};

  leaderboardTables.forEach(table => {
    updateLeaderboard(table);
    setInterval(() => updateLeaderboard(table), 60000);
  });
}