// tennis-events.js
export class TennisEventsHandler {
    constructor() {
        this.events = [];
        this.config = {
            sport: "tennis",
            leagues: [
                { league: "atp", icon: "🎾", name: "ATP Tour", priority: 1 },
                { league: "wta", icon: "🎾", name: "WTA Tour", priority: 2 },
            ]
        };
    }

    async fetchEvents(category) {
        console.log(`Fetching tennis events for category: ${category}`);
        try {
            const endpoint = `/api/tennis-events/?category=${category}`;
            const response = await fetch(endpoint, {
                headers: {
                    'Authorization': `Token ${localStorage.getItem('authToken') || 'ba59ecf8d26672d59c949b70453c361e74c2eec8'}`
                },
                credentials: 'include'
            });
            
            if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
            const events = await response.json();
            console.log(`Fetched ${events.length} ${category} tennis events`);

            return this.mapEvents(events);
        } catch (error) {
            console.error(`Error fetching tennis events (${category}):`, error);
            return [];
        }
    }

    mapEvents(events) {
        return events
            .filter(event => {
                if (!event || !event.event_id || !event.tournament || !event.tournament.id) {
                    console.warn(`Skipping invalid tennis event:`, event);
                    return false;
                }
                return true;
            })
            .map(event => ({
                id: event.event_id,
                tournamentId: event.tournament.id,
                tournamentName: event.tournament.name,
                date: event.date,
                displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
                time: new Date(event.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
                state: event.state,
                completed: event.completed,
                player1: event.player1.name,
                player2: event.player2.name,
                player1_rank: event.player1.world_ranking,
                player2_rank: event.player2.world_ranking,
                score: event.score,
                sets: event.sets || [],
                clock: event.clock,
                period: event.period,
                round: event.round,
                venue: event.venue || "Location TBD",
                league: event.tournament.league.name,
                icon: event.tournament.league.icon,
                priority: event.tournament.league.priority || 1,
                stats: event.stats || {}
            }));
    }

    filterEvents(events, category) {
        if (!events || !Array.isArray(events)) {
            console.error('Invalid tennis events data:', events);
            return [];
        }

        const currentTime = new Date();
        const thirtyDaysAgo = new Date(currentTime);
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        let filteredEvents = events;

        if (category === 'fixtures') {
            filteredEvents = events.filter(match => match.state === "pre" && new Date(match.date) > currentTime);
        } else if (category === 'inplay') {
            filteredEvents = events.filter(match => match.state === "in");
        } else if (category === 'results') {
            filteredEvents = events.filter(match => {
                const matchDate = new Date(match.date);
                return match.state === "post" && matchDate >= thirtyDaysAgo;
            });
        }

        return filteredEvents;
    }

    formatEvents(events, category, isCentralFeed = false) {
        // Tennis-specific formatting logic
        if (!events || !events.length) {
            return `<p>No ${category} tennis matches available.</p>`;
        }

        // Group by tournament
        const eventsByTournament = events.reduce((acc, event) => {
            const tournament = event.tournamentName || "Other";
            if (!acc[tournament]) acc[tournament] = [];
            acc[tournament].push(event);
            return acc;
        }, {});

        let html = '<div class="tennis-feed">';
        
        for (const tournament in eventsByTournament) {
            const tournamentEvents = eventsByTournament[tournament];
            html += `
                <div class="tournament-group">
                    <p class="tournament-header"><span class="sport-icon">🎾</span> ${tournament}</p>
                </div>
            `;

            // Sort matches: In Play first, then Fixtures, then Results (newest first)
            const sortedMatches = tournamentEvents.sort((a, b) => {
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

                const timeOrScore = match.state === "in" ? `(Set ${match.period}, ${match.clock})` : '';

                html += `
                    <div class="tennis-card expandable-card ${match.state === "in" ? 'live-match' : match.state === "post" ? 'result' : 'fixture'}" data-match-id="${match.id}">
                        <div class="card-header" style="cursor: pointer;">
                            <div class="match-info">
                                <div class="players vertical">
                                    <span class="player-name">${match.player1} ${match.player1_rank ? `(${match.player1_rank})` : ''}</span>
                                    <span class="player-name">${match.player2} ${match.player2_rank ? `(${match.player2_rank})` : ''}</span>
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
                    </div>
                `;
            }
        }

        html += '</div>';
        return html;
    }
}

// Cache for failed match IDs to avoid repeated failed requests
export async function fetchEvents(category) {
  console.log(`fetchEvents called with category ${category}, but data is fetched from backend`);
  return []; // Return empty list as data comes from /api/tennis-events/
}

// Keep fetchMatchDetails for stats if needed
export async function fetchMatchDetails(matchId) {
  const failedMatchIds = new Set();
  if (failedMatchIds.has(matchId)) {
      console.log(`Skipping fetch for failed match ID ${matchId}`);
      return { sets: [], stats: {} };
  }
  const url = `/api/tennis-events/${matchId}/stats/`; // Backend stats endpoint
  const maxRetries = 3;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
          const response = await fetch(url);
          if (!response.ok) {
              if (response.status === 400 || response.status === 404) {
                  failedMatchIds.add(matchId);
                  console.warn(`Bad Request for match ${matchId}, caching to skip future attempts`);
                  return { sets: [], stats: {} };
              }
              throw new Error(`HTTP error: ${response.status}`);
          }
          const data = await response.json();
          console.log(`Fetched details for match ${matchId}:`, data);
          return {
              sets: data.sets || [],
              stats: data.stats || {
                  aces: { team1: data.player1_aces || 0, team2: data.player2_aces || 0 },
                  doubleFaults: { team1: data.player1_double_faults || 0, team2: data.player2_double_faults || 0 },
                  servicePointsWon: { team1: data.player1_service_points_won || 0, team2: data.player2_service_points_won || 0 },
              },
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
    console.log('Current time:', currentTime.toISOString());
    filteredEvents = events.filter(match => {
      const matchDate = new Date(match.date);
      console.log(`Match ${match.id} - Date: ${match.date}, Parsed: ${matchDate.toISOString()}, State: ${match.state}`);
      return match.state === "pre" && matchDate > currentTime;
    });
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
              <span class="player-name">${match.player1} ${match.player1_rank ? `(${match.player1_rank})` : ''}</span>
              <span class="player-name">${match.player2} ${match.player2_rank ? `(${match.player2_rank})` : ''}</span>
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
                <span class="player-name">${match.player1} ${match.player1_rank ? `(${match.player1_rank})` : ''}</span>
                <span class="player-name">${match.player2} ${match.player2_rank ? `(${match.player2_rank})` : ''}</span>
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
    const statsElement = e.target;
    statsElement.textContent = 'Loading stats...';
    try {
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
      statsElement.outerHTML = statsContent;
    } catch (error) {
      console.error('Error loading stats:', error);
      statsElement.textContent = 'Error loading stats';
    }
  }
});