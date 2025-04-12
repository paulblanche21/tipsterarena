export async function fetchEvents(data, config) {
  const events = (data.events || []).map(event => {
    const competitions = event.competitions && event.competitions[0] ? event.competitions[0] : {};
    const venue = competitions.venue || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } };
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
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    const data = await response.json();
    const leaderboardData = data?.competitions?.[0].competitors || [];
    const leaderboard = leaderboardData.map((competitor, index) => {
      const roundsStat = competitor.linescores?.map(round => round.value) || [];
      const strokesStat = roundsStat.length === 4 ? roundsStat.reduce((sum, score) => sum + score, 0) : (competitor.strokes || "N/A");
      return {
        position: competitor.position || (index + 1),
        playerName: competitor.athlete?.displayName || "Unknown",
        score: competitor.score || "N/A",
        rounds: roundsStat.length > 0 ? roundsStat : ["N/A", "N/A", "N/A", "N/A"],
        strokes: strokesStat,
        worldRanking: competitor.athlete?.worldRanking || "N/A",
      };
    });
    return leaderboard;
  } catch (error) {
    console.error(`Error fetching leaderboard for event ${eventId}:`, error);
    return [];
  }
}

export async function formatEventList(events, sportKey, category, isCentralFeed = false) {
  if (!events || !events.length) {
    return `<p>No ${category} ${sportKey} events available.</p>`;
  }

  const currentTime = new Date();
  const pgaEvents = events.filter(event => event.league === "PGA Tour");
  let filteredEvents = [];

  if (category === 'fixtures') {
    filteredEvents = pgaEvents
      .filter(event => event.state === "pre" && new Date(event.date) > currentTime)
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  } else if (category === 'inplay') {
    filteredEvents = pgaEvents.filter(event => event.state === "in");
  } else if (category === 'results') {
    filteredEvents = pgaEvents
      .filter(event => event.state === "post" && event.completed)
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .slice(0, 1); // Most recent event
  }

  if (!filteredEvents.length) {
    return `<p>No ${category} PGA Tour events available.</p>`;
  }

  if (isCentralFeed) {
    // Central feed: detailed view (golf-card)
    const eventItems = await Promise.all(filteredEvents.map(async event => {
      const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
      let contentHtml = '';
      if (category === 'inplay' || category === 'results') {
        const leaderboard = await fetchLeaderboard(event.id, "golf", "pga");
        contentHtml = leaderboard.length > 0
          ? `
            <div class="leaderboard-content">
              <h4>Full Leaderboard</h4>
              <div class="leaderboard-wrapper">
                <table class="leaderboard-table" data-event-id="${event.id}">
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
          : "<p>No leaderboard data available.</p>";
      } else {
        contentHtml = `
          <div class="event-details">
            <p><strong>Event:</strong> ${event.name}</p>
            <p><strong>Date:</strong> ${event.displayDate}</p>
            <p><strong>Location:</strong> ${venue}</p>
            <p><strong>Course:</strong> ${event.course.name}</p>
            <p><strong>Par:</strong> ${event.course.par}</p>
            <p><strong>Yardage:</strong> ${event.course.yardage}</p>
            <p><strong>Purse:</strong> ${event.purse}</p>
            <p><strong>Broadcast:</strong> ${event.broadcast}</p>
            <p><strong>Total Rounds:</strong> ${event.totalRounds}</p>
          </div>
        `;
      }
      const status = category === 'inplay' ? 'In Progress' : category === 'results' ? 'Completed' : 'Upcoming';
      const liveIndicator = category === 'inplay' ? '<span class="live-indicator">Live</span>' : '';
      return `
        <div class="golf-card">
          <div class="card-header">
            <div class="event-info">
              <span class="event-name">${event.name}</span>
              <span class="event-status">(${status})</span>
              ${liveIndicator}
            </div>
            <div class="event-meta">
              <span class="datetime">${event.displayDate}</span>
              <span class="location">${venue}</span>
            </div>
          </div>
          <div class="card-content">
            ${contentHtml}
            <div class="additional-details">
              <h4>Event Details</h4>
              <p><strong>Course:</strong> ${event.course.name}</p>
              <p><strong>Par:</strong> ${event.course.par}</p>
              <p><strong>Yardage:</strong> ${event.course.yardage}</p>
              <p><strong>Purse:</strong> ${event.purse}</p>
              <p><strong>Broadcast:</strong> ${event.broadcast}</p>
              <p><strong>Current Round:</strong> ${event.currentRound} of ${event.totalRounds}</p>
              ${event.isPlayoff ? '<p><strong>Playoff:</strong> In Progress</p>' : ''}
            </div>
          </div>
        </div>
      `;
    }));
    return `<div class="golf-feed">${eventItems.join("")}</div>`;
  } else {
    // Sidebar: simple list
    const eventItems = filteredEvents.map(event => {
      const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
      const status = category === 'inplay' ? '(In Progress)' : category === 'results' ? '(Completed)' : '';
      return `
        <p class="event-item golf-event">
          <span>${event.name} ${status} - ${event.displayDate}</span>
          <span class="event-location">${venue}</span>
        </p>
      `;
    }).join("");
    const icon = filteredEvents[0]?.icon || "⛳";
    return `
      <div class="league-group">
        <p class="league-header"><span class="sport-icon">${icon}</span> <strong>PGA Tour</strong></p>
        <div class="event-list">${eventItems}</div>
      </div>
    `;
  }
}

export async function setupLeaderboardUpdates() {
  const leaderboardTables = document.querySelectorAll('.leaderboard-table');
  if (leaderboardTables.length === 0) return;

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