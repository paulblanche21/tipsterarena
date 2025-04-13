// static/js/pages/golf-events.js
console.log('Loading golf-events.js');

export async function fetchEvents(data, config) {
  console.log(`Fetching events for ${config.name}`);
  const events = (data.events || []).map(event => {
    const competitions = event.competitions?.[0] || {};
    const venue = competitions.venue || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } };
    let finalVenue = venue;
    if (event.name === "Valero Texas Open" && venue.fullName === "Location TBD") {
      finalVenue = {
        fullName: "TPC San Antonio (Oaks Course)",
        address: { city: "San Antonio", state: "TX" }
      };
    }
    const courseDetails = competitions.course || {};
    const broadcast = event.broadcasts?.[0]?.media || { shortName: "N/A" };
    const status = event.status || {};
    const period = status.period || 1;
    const totalRounds = event.format?.rounds || 4;
    const isPlayoff = status.playoff || false;
    const weather = event.weather || { condition: "N/A", temperature: "N/A" };

    return {
      id: event.id,
      name: event.name,
      shortName: event.shortName || event.name,
      date: event.date,
      displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      state: status.type?.state || "unknown",
      completed: status.type?.completed || false,
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
      weather: weather,
      priority: config.priority || 0,
    };
  });
  console.log(`Fetched ${events.length} events for ${config.name}`);
  return events;
}

export async function fetchLeaderboard(eventId, sport, league, retries = 3) {
  const url = `https://site.api.espn.com/apis/site/v2/sports/${sport}/${league}/scoreboard/${eventId}`;
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
      const data = await response.json();
      const leaderboardData = data?.competitions?.[0]?.competitors || [];
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
          status: competitor.status || "active",
        };
      });
      console.log(`Fetched leaderboard for event ${eventId}: ${leaderboard.length} players`);
      return leaderboard;
    } catch (error) {
      console.error(`Attempt ${attempt} failed for event ${eventId}:`, error);
      if (attempt === retries) {
        console.error(`All retries exhausted for event ${eventId}`);
        return [];
      }
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt)); // Exponential backoff
    }
  }
  return [];
}

export async function formatEventList(events, sportKey, category, isCentralFeed = false) {
  if (!events?.length) {
    console.log(`No ${category} ${sportKey} events to format`);
    return `<p>No ${category} ${sportKey} events available.</p>`;
  }

  const eventItems = await Promise.all(events.map(async event => {
    const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
    let contentHtml = '';
    if (category === 'inplay' || category === 'results') {
      const leaderboard = await fetchLeaderboard(event.id, "golf", event.league.toLowerCase().replace(" ", ""));
      contentHtml = leaderboard.length > 0
        ? `
          <div class="leaderboard-content">
            <h4>${category === 'inplay' ? 'Live Leaderboard' : 'Final Leaderboard'}</h4>
            <div class="leaderboard-wrapper">
              <table class="leaderboard-table" data-event-id="${event.id}">
                <thead>
                  <tr>
                    <th>Pos</th>
                    <th>Player</th>
                    <th>Score</th>
                    <th>R1</th>
                    <th>R2</th>
                    <th>R3</th>
                    <th>R4</th>
                    <th>Total</th>
                    <th>Rank</th>
                  </tr>
                </thead>
                <tbody>
                  ${leaderboard.slice(0, 5).map(player => `
                    <tr class="${player.status === 'active' ? 'player-active' : 'player-inactive'}">
                      <td>${player.position}</td>
                      <td>${player.playerName}</td>
                      <td>${player.score}</td>
                      <td>${player.rounds[0] || "N/A"}</td>
                      <td>${player.rounds[1] || "N/A"}</td>
                      <td>${player.rounds[2] || "N/A"}</td>
                      <td>${player.rounds[3] || "N/A"}</td>
                      <td>${player.strokes}</td>
                      <td>${player.worldRanking}</td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
              <button class="view-full-leaderboard" data-event-id="${event.id}">View Full Leaderboard</button>
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
          <p><strong>Weather:</strong> ${event.weather.condition}, ${event.weather.temperature}</p>
        </div>
      `;
    }
    const status = category === 'inplay' ? 'In Progress' : category === 'results' ? 'Completed' : 'Upcoming';
    const liveIndicator = category === 'inplay' ? '<span class="live-indicator">Live</span>' : '';
    return `
      <div class="golf-card expandable-card ${category === 'inplay' ? 'live-event' : ''}">
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
        <div class="card-content" style="display: none;">
          ${contentHtml}
        </div>
      </div>
    `;
  }));

  console.log(`Formatted ${eventItems.length} golf events for ${category}`);
  return `<div class="golf-feed">${eventItems.join("")}</div>`;
}

export async function setupLeaderboardUpdates() {
  console.log('Setting up leaderboard updates');
  const leaderboardTables = document.querySelectorAll('.leaderboard-table');
  if (leaderboardTables.length === 0) {
    console.log('No leaderboard tables found');
    return;
  }

  const updateLeaderboard = async (table) => {
    const eventId = table.getAttribute('data-event-id');
    if (!eventId) return;
    const leaderboard = await fetchLeaderboard(eventId, "golf", "pga");
    if (leaderboard.length > 0) {
      const tbody = table.querySelector('tbody');
      tbody.innerHTML = leaderboard.slice(0, 5).map(player => `
        <tr class="${player.status === 'active' ? 'player-active' : 'player-inactive'}">
          <td>${player.position}</td>
          <td>${player.playerName}</td>
          <td>${player.score}</td>
          <td>${player.rounds[0] || "N/A"}</td>
          <td>${player.rounds[1] || "N/A"}</td>
          <td>${player.rounds[2] || "N/A"}</td>
          <td>${player.rounds[3] || "N/A"}</td>
          <td>${player.strokes}</td>
          <td>${player.worldRanking}</td>
        </tr>
      `).join("");
      console.log(`Updated leaderboard for event ${eventId}`);
    }
  };

  leaderboardTables.forEach(table => {
    updateLeaderboard(table);
    const intervalId = setInterval(() => updateLeaderboard(table), 30000);
    table.dataset.intervalId = intervalId; // Store for cleanup if needed
  });

  document.querySelectorAll('.view-full-leaderboard').forEach(button => {
    button.addEventListener('click', async () => {
      const eventId = button.getAttribute('data-event-id');
      const modalBody = document.getElementById('event-modal-body');
      const modalTitle = document.getElementById('event-modal-title');
      modalTitle.textContent = 'Full Leaderboard';
      modalBody.innerHTML = '<p>Loading...</p>';

      const leaderboard = await fetchLeaderboard(eventId, "golf", "pga");
      if (leaderboard.length > 0) {
        modalBody.innerHTML = `
          <div class="leaderboard-content">
            <table class="full-leaderboard-table">
              <thead>
                <tr>
                  <th>Pos</th>
                  <th>Player</th>
                  <th>Score</th>
                  <th>R1</th>
                  <th>R2</th>
                  <th>R3</th>
                  <th>R4</th>
                  <th>Total</th>
                  <th>Rank</th>
                </tr>
              </thead>
              <tbody>
                ${leaderboard.map(player => `
                  <tr class="${player.status === 'active' ? 'player-active' : 'player-inactive'}">
                    <td>${player.position}</td>
                    <td>${player.playerName}</td>
                    <td>${player.score}</td>
                    <td>${player.rounds[0] || "N/A"}</td>
                    <td>${player.rounds[1] || "N/A"}</td>
                    <td>${player.rounds[2] || "N/A"}</td>
                    <td>${player.rounds[3] || "N/A"}</td>
                    <td>${player.strokes}</td>
                    <td>${player.worldRanking}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        `;
      } else {
        modalBody.innerHTML = '<p>No leaderboard data available.</p>';
      }
      console.log(`Displayed full leaderboard for event ${eventId}`);
    });
  });
}