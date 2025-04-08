// tennis-events.js

// Fetch tournament matches directly from the initial API response
export async function fetchEvents(data, config) {
  const events = (data.events || []).flatMap(tournament => {
    const groupings = tournament.groupings || [];
    return groupings.flatMap(grouping => {
      const competitions = grouping.competitions || [];
      return competitions.map(comp => ({
        id: comp.id,
        tournamentId: tournament.id,
        tournamentName: tournament.name,
        date: comp.date,
        displayDate: new Date(comp.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
        time: new Date(comp.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
        state: comp.status?.type?.state || "unknown",
        completed: comp.status?.type?.completed || false,
        player1: comp.competitors[0]?.athlete?.displayName || "TBD",
        player2: comp.competitors[1]?.athlete?.displayName || "TBD",
        score: comp.competitors.length === 2 ? 
          `${comp.competitors[0].linescores?.map(set => set.value).join('-') || "0"} - ${comp.competitors[1].linescores?.map(set => set.value).join('-') || "0"}` : "TBD",
        clock: comp.status?.displayClock || "",
        period: comp.status?.period || 0,
        round: comp.round?.displayName || "TBD",
        venue: comp.venue?.fullName || "Location TBD",
        league: config.name,
        icon: config.icon
      }));
    });
  });

  console.log(`fetchEvents for ${config.name}: Returning ${events.length} matches`);
  return events;
}

// Fetch detailed stats for a live match
export async function fetchMatchDetails(matchId) {
  const url = `https://site.api.espn.com/apis/site/v2/sports/tennis/atp/summary?event=${matchId}`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    console.log(`fetchMatchDetails for match ${matchId}: Fetched sets (${data.sets?.length || 0}) and stats`);
    return {
      sets: data.sets || [],
      stats: data.statistics || {}
    };
  } catch (error) {
    console.error(`Error fetching match details for ${matchId}:`, error);
    return { sets: [], stats: {} };
  }
}

// Format the center feed with cards (no tournament grouping, just render the cards)
export async function formatEventTable(matches, tournamentName) {
  if (!matches || !Array.isArray(matches) || !matches.length) {
    console.log(`formatEventTable for ${tournamentName}: No matches available`);
    return `<p>No matches available for ${tournamentName}.</p>`;
  }

  let eventHtml = '<div class="tennis-feed">';

  // Live Matches
  for (const match of matches.filter(m => m.state === "in")) {
    const matchId = match.id;
    const matchDetails = await fetchMatchDetails(matchId);
    const sets = matchDetails.sets || [];
    const stats = matchDetails.stats || {};

    const setsList = sets.length ?
      `<ul class="sets-list">${
        sets.map(set => `
          <li>Set ${set.setNumber}: ${set.team1Score || 0} - ${set.team2Score || 0}</li>
        `).join("")
      }</ul>` : "<span class='no-sets'>No set data available</span>";

    const statsContent = stats && Object.keys(stats).length ?
      `<div class="match-stats">
        <p>Aces: ${stats.aces?.team1 || 0} - ${stats.aces?.team2 || 0}</p>
        <p>Double Faults: ${stats.doubleFaults?.team1 || 0} - ${stats.doubleFaults?.team2 || 0}</p>
        <p>Service Points Won: ${stats.servicePointsWon?.team1 || 0} - ${stats.servicePointsWon?.team2 || 0}</p>
      </div>` : "<p>No stats available</p>";

    const detailsContent = `
      <div class="match-details" style="display: none;">
        <div class="match-stats">
          <div class="sets">
            <p><strong>Sets:</strong></p>
            ${setsList}
          </div>
          ${statsContent}
        </div>
      </div>
    `;

    eventHtml += `
      <div class="tennis-card expandable-card live-match" data-match-id="${matchId}">
        <div class="card-header" style="cursor: pointer;">
          <div class="match-info">
            <div class="players">
              <span class="player-name">${match.player1}</span>
              <span class="score">${match.score} (Set ${match.period}, ${match.clock})</span>
              <span class="player-name">${match.player2}</span>
            </div>
          </div>
          <div class="match-meta">
            <span class="round">${match.round}</span>
            <span class="datetime">${match.displayDate} ${match.time}</span>
          </div>
        </div>
        ${detailsContent}
      </div>
    `;
  }

  // Upcoming Fixtures
  matches.filter(m => m.state === "pre").forEach(match => {
    eventHtml += `
      <div class="tennis-card expandable-card fixture" data-match-id="${match.id}">
        <div class="card-header" style="cursor: pointer;">
          <div class="match-info">
            <div class="players">
              <span class="player-name">${match.player1}</span>
              <span class="score">vs</span>
              <span class="player-name">${match.player2}</span>
            </div>
          </div>
          <div class="match-meta">
            <span class="round">${match.round}</span>
            <span class="datetime">${match.displayDate} ${match.time}</span>
          </div>
        </div>
      </div>
    `;
  });

  // Full-Time Results
  matches.filter(m => m.state === "post" && m.completed).forEach(match => {
    eventHtml += `
      <div class="tennis-card expandable-card result" data-match-id="${match.id}">
        <div class="card-header" style="cursor: pointer;">
          <div class="match-info">
            <div class="players">
              <span class="player-name">${match.player1}</span>
              <span class="score">${match.score}</span>
              <span class="player-name">${match.player2}</span>
            </div>
          </div>
          <div class="match-meta">
            <span class="round">${match.round}</span>
            <span class="datetime">${match.displayDate}</span>
          </div>
        </div>
      </div>
    `;
  });

  eventHtml += '</div>';
  console.log(`formatEventTable for ${tournamentName}: Generated ${matches.length} cards (Live: ${matches.filter(m => m.state === "in").length}, Fixtures: ${matches.filter(m => m.state === "pre").length}, Results: ${matches.filter(m => m.state === "post" && m.completed).length})`);
  return eventHtml;
}

// Format the sidebar list (unchanged)
export function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming ${sportKey} tournaments available.</p>`;
  }
  const currentTime = new Date();
  const tournaments = events.reduce((acc, match) => {
    if (!acc[match.tournamentId]) {
      acc[match.tournamentId] = {
        id: match.tournamentId,
        name: match.tournamentName,
        date: match.date,
        displayDate: match.displayDate,
        venue: match.venue
      };
    }
    return acc;
  }, {});
  const upcomingTournaments = Object.values(tournaments)
    .filter(tournament => new Date(tournament.date) > currentTime)
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(0, 3);
  if (!upcomingTournaments.length) {
    return `<p>No upcoming ${sportKey} tournaments available.</p>`;
  }

  const eventItems = upcomingTournaments
    .map(tournament => {
      const venue = tournament.venue || "Location TBD";
      return `
        <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;" data-tournament-id="${tournament.id}">
          <span>${tournament.name} - ${tournament.displayDate}</span>
          ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
        </p>
      `;
    })
    .join("");

  return `<div class="league-group"><p class="league-header"><span class="sport-icon">🎾</span> <strong>ATP Tour</strong></p>${eventItems}</div>`;
}