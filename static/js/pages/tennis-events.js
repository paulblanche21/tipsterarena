// tennis-events.js

// Cache for failed match IDs to avoid repeated failed requests
const failedMatchIds = new Set();

export async function fetchEvents(data, config) {
  console.log(`Fetching tennis events for ${config.name}`);
  const events = (data.events || []).flatMap(tournament => {
    const groupings = tournament.groupings || [];
    return groupings.flatMap(grouping => {
      const competitions = grouping.competitions || [];
      return competitions.map(comp => {
        const competitors = comp.competitors || [];
        const player1 = competitors[0]?.athlete?.displayName || "TBD";
        const player2 = competitors[1]?.athlete?.displayName || "TBD";
        // Handle scores for completed matches
        let score = "TBD";
        let sets = [];
        if (competitors.length === 2) {
          const p1Scores = competitors[0].linescores?.map(set => set.value) || ["0"];
          const p2Scores = competitors[1].linescores?.map(set => set.value) || ["0"];
          score = `${p1Scores.join('-')} - ${p2Scores.join('-')}`;
          // Create sets array for rendering
          const maxSets = Math.max(p1Scores.length, p2Scores.length);
          for (let i = 0; i < maxSets; i++) {
            sets.push({
              setNumber: i + 1,
              team1Score: p1Scores[i] || "-",
              team2Score: p2Scores[i] || "-"
            });
          }
        }
        return {
          id: comp.id,
          tournamentId: tournament.id,
          tournamentName: tournament.name,
          date: comp.date,
          displayDate: new Date(comp.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
          time: new Date(comp.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
          state: comp.status?.type?.state || "unknown",
          completed: comp.status?.type?.completed || false,
          player1,
          player2,
          score,
          sets, // Store sets for rendering
          clock: comp.status?.displayClock || "0:00",
          period: comp.status?.period || 0,
          round: comp.round?.displayName || "Unknown Round",
          venue: comp.venue?.fullName || "Location TBD",
          league: config.name,
          icon: config.icon,
          priority: config.priority || 999
        };
      });
    });
  });
  console.log(`Parsed ${events.length} tennis matches`);
  return events;
}

export async function fetchMatchDetails(matchId) {
  if (failedMatchIds.has(matchId)) {
    console.log(`Skipping fetch for failed match ID ${matchId}`);
    return { sets: [], stats: {} };
  }
  const url = `https://site.api.espn.com/apis/site/v2/sports/tennis/atp/summary?event=${matchId}`;
  const maxRetries = 3;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        if (response.status === 400) {
          failedMatchIds.add(matchId);
          console.warn(`Bad Request for match ${matchId}, caching to skip future attempts`);
          return { sets: [], stats: {} };
        }
        throw new Error(`HTTP error: ${response.status}`);
      }
      const data = await response.json();
      const sets = data.sets || [];
      const stats = data.boxscore?.statistics || {};
      console.log(`Fetched details for match ${matchId}: ${sets.length} sets`);
      return {
        sets: sets.map(set => ({
          setNumber: set.setNumber || "N/A",
          team1Score: set.team1Score || 0,
          team2Score: set.team2Score || 0
        })),
        stats: {
          aces: stats.aces || { team1: 0, team2: 0 },
          doubleFaults: stats.doubleFaults || { team1: 0, team2: 0 },
          servicePointsWon: stats.servicePointsWon || { team1: 0, team2: 0 }
        }
      };
    } catch (error) {
      if (attempt === maxRetries) {
        console.error(`Error fetching match details for ${matchId} after ${maxRetries} attempts:`, error);
        failedMatchIds.add(matchId);
        return { sets: [], stats: {} };
      }
      console.warn(`Attempt ${attempt} failed for match ${matchId}, retrying...`);
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
}

export async function formatEventList(events, sportKey = 'tennis', category, isCentralFeed = false) {
  console.log(`Formatting tennis events for ${category}, ${events.length} events`);
  if (!events || !events.length) {
    return `<p>No ${category} ${sportKey} matches available.</p>`;
  }

  const currentTime = new Date();
  const sevenDaysFuture = new Date();
  const sevenDaysAgo = new Date();
  sevenDaysFuture.setDate(currentTime.getDate() + 7);
  sevenDaysAgo.setDate(currentTime.getDate() - 7);

  let filteredEvents = [];
  if (category === 'fixtures') {
    filteredEvents = events.filter(match => match.state === "pre" && new Date(match.date) > currentTime && new Date(match.date) <= sevenDaysFuture);
  } else if (category === 'inplay') {
    filteredEvents = events.filter(match => match.state === "in");
  } else if (category === 'results') {
    filteredEvents = events.filter(match => match.state === "post" && new Date(match.date) >= sevenDaysAgo && new Date(match.date) <= currentTime);
  }

  if (!filteredEvents.length) {
    console.log(`No ${category} tennis matches after filtering`);
    return `<p>No ${category} ${sportKey} matches available.</p>`;
  }

  if (isCentralFeed) {
    return formatEventTable(filteredEvents, sportKey);
  }

  // Sidebar rendering
  const eventItems = filteredEvents.map(match => {
    const setsDisplay = match.sets && match.sets.length
      ? `
        <div class="sets-display">
          <div class="sets-row">${match.sets.map(set => `<span>${set.team1Score}</span>`).join(' ')}</div>
          <div class="sets-row">${match.sets.map(set => `<span>${set.team2Score}</span>`).join(' ')}</div>
        </div>`
      : `<span class="score-fallback">${match.score}</span>`;
    const detailsContent = (category === 'inplay' || category === 'results')
      ? `
        <div class="match-details">
          <div class="sets">
            <p><strong>Sets:</strong></p>
            ${setsDisplay}
          </div>
          <p class="load-stats" data-match-id="${match.id}">Load stats...</p>
        </div>`
      : '';
    return `
      <div class="event-item tennis-event ${category === 'inplay' ? 'live-match' : ''}" data-match-id="${match.id}">
        <div class="card-header">
          <div class="match-info">
            <div class="players vertical">
              <span class="player-name">${match.player1}</span>
              <span class="player-name">${match.player2}</span>
            </div>
            <div class="score vertical">
              ${category === 'fixtures' ? '<span>vs</span><span></span>' : setsDisplay}
              ${category === 'inplay' ? `<span class="inplay-meta">(Set ${match.period}, ${match.clock})</span>` : ''}
            </div>
          </div>
          <div class="match-meta">
            <span class="round">${match.round}</span>
            <span class="datetime">${match.displayDate}${category === 'fixtures' ? ' ' + match.time : ''}</span>
          </div>
        </div>
        ${detailsContent}
      </div>
    `;
  });

  return `
    <div class="league-group">
      <p class="league-header"><span class="sport-icon">🎾</span> <strong>ATP Tour</strong></p>
      <div class="event-list">${eventItems.join("")}</div>
    </div>
  `;
}

export async function formatEventTable(matches, sportKey = 'tennis') {
  console.log(`Formatting ${matches.length} tennis matches for table`);
  if (!matches || !Array.isArray(matches) || !matches.length) {
    return `<p>No ${sportKey} matches available.</p>`;
  }

  // Group matches by tournament
  const matchesByTournament = matches.reduce((acc, match) => {
    const tournament = match.tournamentName || "Other";
    if (!acc[tournament]) acc[tournament] = [];
    acc[tournament].push(match);
    return acc;
  }, {});

  let eventHtml = '<div class="tennis-feed">';

  for (const tournament in matchesByTournament) {
    const tournamentMatches = matchesByTournament[tournament];
    eventHtml += `
      <div class="tournament-group">
        <p class="tournament-header"><span class="sport-icon">🎾</span> ${tournament}</p>
      </div>
    `;

    // Sort matches: In Play first, then Fixtures, then Results (newest first)
    const sortedMatches = tournamentMatches.sort((a, b) => {
      if (a.state === "in" && b.state !== "in") return -1;
      if (a.state !== "in" && b.state === "in") return 1;
      if (a.state === "pre" && b.state !== "pre") return -1;
      if (a.state !== "pre" && b.state === "pre") return 1;
      return new Date(b.date) - new Date(a.date);
    });

    for (const match of sortedMatches) {
      const setsDisplay = match.sets && match.sets.length
        ? `
          <div class="sets-display">
            <div class="sets-row">${match.sets.map(set => `<span>${set.team1Score}</span>`).join(' ')}</div>
            <div class="sets-row">${match.sets.map(set => `<span>${set.team2Score}</span>`).join(' ')}</div>
          </div>`
        : `<span class="score-fallback">${match.score}</span>`;
      const detailsContent = (match.state === "in" || match.state === "post")
        ? `
          <div class="match-details" style="display: none;">
            <div class="match-stats">
              <div class="sets">
                <p><strong>Sets:</strong></p>
                ${setsDisplay}
              </div>
              <p class="load-stats" data-match-id="${match.id}">Load stats...</p>
            </div>
          </div>
        `
        : '';

      const timeOrScore = match.state === "in" ? `(Set ${match.period}, ${match.clock})` : '';

      eventHtml += `
        <div class="tennis-card expandable-card ${match.state === "in" ? 'live-match' : match.state === "post" ? 'result' : 'fixture'}" data-match-id="${match.id}">
          <div class="card-header" style="cursor: pointer;">
            <div class="match-info">
              <div class="players vertical">
                <span class="player-name">${match.player1}</span>
                <span class="player-name">${match.player2}</span>
              </div>
              <div class="score vertical">
                ${match.state === "pre" ? '<span>vs</span><span></span>' : setsDisplay}
                ${match.state === "in" ? `<span class="inplay-meta">${timeOrScore}</span>` : ''}
              </div>
            </div>
            <div class="match-meta">
              <span class="round">${match.round}</span>
              <span class="datetime">${match.displayDate}${match.state === "pre" ? ' ' + match.time : ''}</span>
            </div>
          </div>
          ${detailsContent}
        </div>
      `;
    }
  }

  eventHtml += '</div>';
  return eventHtml || `<p>No ${sportKey} matches available.</p>`;
}

// Add event listener for loading stats on demand
document.addEventListener('click', async (e) => {
  if (e.target.classList.contains('load-stats')) {
    const matchId = e.target.getAttribute('data-match-id');
    e.target.textContent = 'Loading stats...';
    const matchDetails = await fetchMatchDetails(matchId);
    const stats = matchDetails.stats || {};
    const statsContent = stats && Object.keys(stats).length
      ? `
        <div class="match-stats">
          <p>Aces: ${stats.aces.team1 || 0} - ${stats.aces.team2 || 0}</p>
          <p>Double Faults: ${stats.doubleFaults.team1 || 0} - ${stats.doubleFaults.team2 || 0}</p>
          <p>Service Points Won: ${stats.servicePointsWon.team1 || 0} - ${stats.servicePointsWon.team2 || 0}</p>
        </div>`
      : "<p>No stats available</p>";
    e.target.outerHTML = statsContent;
  }
});