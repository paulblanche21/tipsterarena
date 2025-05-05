// football-events.js

console.log('FETCH EVENTS CALLED!');

export class FootballEventsHandler {
    constructor() {
        this.config = {
            leagues: [
                { sport: "soccer", league: "eng.1", icon: "⚽", name: "Premier League", priority: 1 },
                { sport: "soccer", league: "esp.1", icon: "⚽", name: "La Liga", priority: 2 },
                { sport: "soccer", league: "ita.1", icon: "⚽", name: "Serie A", priority: 3 },
            ],
            timePeriods: {
                results: 7,  // 7 days for football results
                fixtures: 14 // 14 days for football fixtures
            }
        };
    }

    async fetchEvents(category) {
        try {
            const response = await fetch(`/api/events/football/?category=${category}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error('API Error:', errorData);
                throw new Error(`HTTP error: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('API Response:', data);
            
            if (!Array.isArray(data)) {
                console.error('Expected array of events, got:', typeof data);
                return [];
            }
            
            return this.mapEvents(data);
        } catch (error) {
            console.error(`Error fetching football events (${category}):`, error);
            return [];
        }
    }

    mapEvents(events) {
        if (!Array.isArray(events)) {
            console.error('mapEvents received non-array:', events);
            return [];
        }

        return events
            .filter(event => event && typeof event === 'object') // Filter out null/undefined events
            .map(event => {
                try {
                    // Ensure we have the required fields
                    if (!event.id && !event.event_id) {
                        console.error('Event missing ID:', event);
                        return null;
                    }

                    // Log the raw event data for debugging
                    console.log('Processing event:', event);

                    // Extract team data from the event structure
                    const homeTeam = event.home_team || {};
                    const awayTeam = event.away_team || {};
                    const homeTeamStats = event.home_team_stats || {};
                    const awayTeamStats = event.away_team_stats || {};

                    return {
                        id: event.id || event.event_id,
                        name: event.name || `${homeTeam.name || 'Unknown'} vs ${awayTeam.name || 'Unknown'}`,
                        date: event.date,
                        time: event.time,
                        state: event.state,
                        status_description: event.status_description || 'Unknown',
                        status_detail: event.status_detail || 'N/A',
                        league: {
                            id: event.league?.league_id,
                            name: event.league?.name,
                            icon: event.league?.icon,
                            priority: event.league?.priority
                        },
                        venue: event.venue || 'Location TBD',
                        homeTeam: {
                            name: homeTeam.name || 'Unknown Team',
                            logo: homeTeam.logo || window.default_avatar_url || '/static/img/default-avatar.png',
                            score: event.home_score || '0',
                            stats: homeTeamStats,
                            form: homeTeam.form || 'N/A',
                            record: homeTeam.record || 'N/A'
                        },
                        awayTeam: {
                            name: awayTeam.name || 'Unknown Team',
                            logo: awayTeam.logo || window.default_avatar_url || '/static/img/default-avatar.png',
                            score: event.away_score || '0',
                            stats: awayTeamStats,
                            form: awayTeam.form || 'N/A',
                            record: awayTeam.record || 'N/A'
                        },
                        broadcast: event.broadcast || 'N/A',
                        odds: event.odds || [],
                        goals: event.key_events?.filter(e => e.type === 'Goal') || [],
                        cards: event.key_events?.filter(e => e.type === 'Yellow Card' || e.type === 'Red Card') || []
                    };
                } catch (error) {
                    console.error('Error mapping event:', error, event);
                    return null;
                }
            })
            .filter(event => event !== null) // Remove any failed mappings
            .sort((a, b) => {
                // First sort by date (newest first)
                const dateComparison = new Date(b.date) - new Date(a.date);
                if (dateComparison !== 0) return dateComparison;
                
                // Then sort by league priority
                const leaguePriorityComparison = (a.league?.priority || 999) - (b.league?.priority || 999);
                if (leaguePriorityComparison !== 0) return leaguePriorityComparison;
                
                // Finally sort by league name
                return (a.league?.name || '').localeCompare(b.league?.name || '');
            });
    }

    filterEvents(events, category) {
        const currentTime = new Date();
        const resultsDaysAgo = new Date(currentTime);
        resultsDaysAgo.setDate(currentTime.getDate() - this.config.timePeriods.results);
        
        const fixturesDaysAgo = new Date(currentTime);
        fixturesDaysAgo.setDate(currentTime.getDate() + this.config.timePeriods.fixtures);

        let filteredEvents = events;

        if (category === 'fixtures') {
            filteredEvents = events.filter(match => {
                const matchDate = new Date(match.date);
                return match.state === "pre" && 
                       matchDate > currentTime && 
                       matchDate <= fixturesDaysAgo;
            });
        } else if (category === 'inplay') {
            filteredEvents = events.filter(match => {
                const matchDate = new Date(match.date);
                // Only show matches that are currently in progress
                return match.state === "in" && 
                       matchDate <= currentTime && 
                       matchDate >= new Date(currentTime.getTime() - 3 * 60 * 60 * 1000); // Within last 3 hours
            });
        } else if (category === 'results') {
            filteredEvents = events.filter(match => {
                const matchDate = new Date(match.date);
                // Only show completed matches from the last 7 days
                return (match.state === "post" || match.completed || 
                       (match.home_score !== null && match.away_score !== null)) && 
                       matchDate >= resultsDaysAgo && 
                       matchDate <= currentTime;
            });
        }

        // Sort events based on category
        if (category === 'fixtures') {
            filteredEvents.sort((a, b) => new Date(a.date) - new Date(b.date));
        } else {
            filteredEvents.sort((a, b) => new Date(b.date) - new Date(a.date));
        }

        return filteredEvents;
    }

    formatEvents(events, category, isCentralFeed = false) {
        if (!events || events.length === 0) {
            return '<p>No events found.</p>';
        }

        const eventsByDate = this.groupEventsByDate(events);
        const sortedDates = Object.keys(eventsByDate).sort((a, b) => new Date(a) - new Date(b));

        return sortedDates.map(date => {
            const eventsHtml = eventsByDate[date].map(event => {
                const defaultAvatar = window.default_avatar_url || '/static/img/default-avatar.png';
                const home_logo = event.homeTeam?.logo || defaultAvatar;
                const away_logo = event.awayTeam?.logo || defaultAvatar;
                const home_team = event.homeTeam || { name: 'Unknown Team' };
                const away_team = event.awayTeam || { name: 'Unknown Team' };
                const eventClass = this.getEventClass(event);
                const scoreDisplay = event.state === 'pre' ? 'vs' : `${event.homeTeam.score || '0'} - ${event.awayTeam.score || '0'}`;

                // Process key events
                const goals = event.key_events?.filter(e => e.is_goal) || [];
                const cards = event.key_events?.filter(e => e.is_yellow_card || e.is_red_card) || [];

                const homeGoals = goals.filter(g => g.team === home_team.name);
                const awayGoals = goals.filter(g => g.team === away_team.name);

                const homeCards = cards.filter(c => c.team === home_team.name);
                const awayCards = cards.filter(c => c.team === away_team.name);

                const formatGoals = (goals) => {
                    if (!goals.length) return '<span class="no-goals">No goals</span>';
                    return goals.map(g => `
                        <li class="goal-item">
                            <span class="goal-time">${g.time}</span>
                            <span class="goal-scorer">${g.player}</span>
                            ${g.is_penalty ? ' (Penalty)' : ''}
                        </li>
                    `).join('');
                };

                const formatCards = (cards) => {
                    if (!cards.length) return '<span class="no-cards">No cards</span>';
                    return cards.map(c => `
                        <li class="${c.is_red_card ? 'red-card' : 'yellow-card'}-item">
                            <span class="card-time">${c.time}</span>
                            <span class="card-player">${c.player}</span>
                            <span class="card-type">${c.is_red_card ? 'Red Card' : 'Yellow Card'}</span>
                        </li>
                    `).join('');
                };

                return `
                    <div class="expandable-card ${eventClass}" data-event-id="${event.id}">
                        <div class="card-header">
                            <div class="match-info">
                                <div class="teams">
                                    <div class="team">
                                        <img src="${home_logo}" alt="${home_team.name}" onerror="this.src='${defaultAvatar}'">
                                        <span class="team-name">${home_team.name}</span>
                                    </div>
                                    <div class="score">
                                        ${scoreDisplay}
                                    </div>
                                    <div class="team">
                                        <img src="${away_logo}" alt="${away_team.name}" onerror="this.src='${defaultAvatar}'">
                                        <span class="team-name">${away_team.name}</span>
                                    </div>
                                </div>
                                <div class="match-meta">
                                    <span class="datetime">${new Date(event.date).toLocaleString()}</span>
                                    ${event.venue ? `<span class="location">${event.venue}</span>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="card-details" style="display: none;">
                            <div class="match-stats">
                                <div class="stats-row">
                                    <div class="stat-value">${event.homeTeam.stats?.possession || 'N/A'}</div>
                                    <div class="stat-label">Possession</div>
                                    <div class="stat-value">${event.awayTeam.stats?.possession || 'N/A'}</div>
                                </div>
                                <div class="stats-row">
                                    <div class="stat-value">${event.homeTeam.stats?.shots || 'N/A'}</div>
                                    <div class="stat-label">Shots</div>
                                    <div class="stat-value">${event.awayTeam.stats?.shots || 'N/A'}</div>
                                </div>
                                <div class="stats-row">
                                    <div class="stat-value">${event.homeTeam.stats?.shots_on_target || 'N/A'}</div>
                                    <div class="stat-label">Shots on Target</div>
                                    <div class="stat-value">${event.awayTeam.stats?.shots_on_target || 'N/A'}</div>
                                </div>
                                <div class="stats-row">
                                    <div class="stat-value">${event.homeTeam.stats?.corners || 'N/A'}</div>
                                    <div class="stat-label">Corners</div>
                                    <div class="stat-value">${event.awayTeam.stats?.corners || 'N/A'}</div>
                                </div>
                                <div class="stats-row">
                                    <div class="stat-value">${event.homeTeam.stats?.fouls || 'N/A'}</div>
                                    <div class="stat-label">Fouls</div>
                                    <div class="stat-value">${event.awayTeam.stats?.fouls || 'N/A'}</div>
                                </div>
                            </div>
                            <div class="key-events">
                                <div class="team-events">
                                    <div class="home-team-events">
                                        <h4>${home_team.name}</h4>
                                        <div class="goals">
                                            <h5>Goals</h5>
                                            <ul class="goals-list">
                                                ${formatGoals(homeGoals)}
                                            </ul>
                                        </div>
                                        <div class="cards">
                                            <h5>Cards</h5>
                                            <ul class="cards-list">
                                                ${formatCards(homeCards)}
                                            </ul>
                                        </div>
                                    </div>
                                    <div class="away-team-events">
                                        <h4>${away_team.name}</h4>
                                        <div class="goals">
                                            <h5>Goals</h5>
                                            <ul class="goals-list">
                                                ${formatGoals(awayGoals)}
                                            </ul>
                                        </div>
                                        <div class="cards">
                                            <h5>Cards</h5>
                                            <ul class="cards-list">
                                                ${formatCards(awayCards)}
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            return `
                <div class="date-group">
                    <h3 class="date-header">${date}</h3>
                    <div class="events-container">
                        ${eventsHtml}
                    </div>
                </div>
            `;
        }).join('');
    }

    formatMatchDetails(event) {
        const defaultAvatar = window.default_avatar_url || '/static/img/default-avatar.png';
        const home_logo = event.homeTeam?.logo || defaultAvatar;
        const away_logo = event.awayTeam?.logo || defaultAvatar;
        const home_team = event.homeTeam || { name: 'Unknown Team' };
        const away_team = event.awayTeam || { name: 'Unknown Team' };
        const eventClass = this.getEventClass(event);
        const scoreDisplay = event.state === 'pre' ? 'vs' : `${event.homeTeam.score || '0'} - ${event.awayTeam.score || '0'}`;

        return `
            <div class="match-info">
                <div class="teams">
                    <div class="team">
                        <img src="${home_logo}" alt="${home_team.name}" onerror="this.src='${defaultAvatar}'">
                        <span class="team-name">${home_team.name}</span>
                    </div>
                    <div class="score">
                        ${scoreDisplay}
                    </div>
                    <div class="team">
                        <img src="${away_logo}" alt="${away_team.name}" onerror="this.src='${defaultAvatar}'">
                        <span class="team-name">${away_team.name}</span>
                    </div>
                </div>
                <div class="match-meta">
                    <span class="datetime">${new Date(event.date).toLocaleString()}</span>
                    ${event.venue ? `<span class="location">${event.venue}</span>` : ''}
                </div>
            </div>
        `;
    }

    getEventClass(event) {
        if (event.is_goal) return 'goal';
        if (event.is_yellow_card) return 'yellow-card';
        if (event.is_red_card) return 'red-card';
        return '';
    }

    groupEventsByDate(events) {
        return events.reduce((acc, event) => {
            const date = new Date(event.date).toLocaleDateString('en-GB', {
                weekday: 'long',
                day: 'numeric',
                month: 'long'
            });
            if (!acc[date]) {
                acc[date] = [];
            }
            acc[date].push(event);
            return acc;
        }, {});
    }
}

// Create and export a singleton instance
const footballHandler = new FootballEventsHandler();

// Export the handler instance and its methods
export const formatEvents = (events, category, isCentralFeed) => footballHandler.formatEvents(events, category, isCentralFeed);
export const fetchEvents = (category) => footballHandler.fetchEvents(category);
export const formatEventList = (events, sportKey, showLocation) => footballHandler.formatEventList(events, sportKey, showLocation);
export const formatMatchDetails = (event) => footballHandler.formatMatchDetails(event);
export const getEventClass = (event) => footballHandler.getEventClass(event);

export function formatFootballTable(events) {
  if (!events || !events.length) {
    console.log("No events to format for football table");
    return `<p class="no-events">No football results available.</p>`;
  }

  console.log(`Formatting ${events.length} events for football table`);

  const sortedEvents = events.sort((a, b) => {
    if (a.priority !== b.priority) return a.priority - b.priority;
    return new Date(b.date) - new Date(a.date); // Newest first
  });

  const eventsByLeague = sortedEvents.reduce((acc, event) => {
    const league = event.league || "Other";
    if (!acc[league]) acc[league] = [];
    acc[league].push(event);
    return acc;
  }, {});

  let eventHtml = '<div class="event-feed">';

  for (const league in eventsByLeague) {
    const leagueEvents = eventsByLeague[league];

    eventHtml += `
      <div class="league-group">
        <p class="league-header"><span class="sport-icon">⚽</span> ${league}</p>
      </div>
    `;

    leagueEvents.forEach((event, index) => {
      const venue = event.venue || "Location TBD"; // venue is a string
      const eventId = event.id || `${league}-${index}`;
      const timeOrScore = event.state === "in" && event.scores ?
        `<span class="live-score">${event.homeTeam.score || '0'} - ${event.awayTeam.score || '0'}</span>` :
        event.state === "post" ?
        `<span class="final-score">${event.homeTeam.score || '0'} - ${event.awayTeam.score || '0'}</span>` :
        `${event.displayDate} ${event.time}`;

      const oddsContent = event.odds ? `
        <div class="betting-odds">
          <p><strong>Betting Odds (${event.odds.provider}):</strong></p>
          <p>${event.homeTeam.name}: ${event.odds.home}</p>
          <p>${event.awayTeam.name}: ${event.odds.away}</p>
          <p>Draw: ${event.odds.draw}</p>
        </div>
      ` : "<p>Betting odds not available.</p>";

      let detailsContent = '';
      if (event.state === "in" && event.detailedStats) {
        const homeGoals = event.goals?.filter(goal => goal.team === event.homeTeam.name) || [];
        const awayGoals = event.goals?.filter(goal => goal.team === event.awayTeam.name) || [];

        const homeGoalsList = homeGoals.length ?
          `<ul class="goal-list">${
            homeGoals.map(goal => `
              <li>${goal.scorer} - ${goal.time}${goal.assist && goal.assist !== "Unassisted" ? `, Assist: ${goal.assist}` : ""}</li>
            `).join("")
          }</ul>` : "<span class='no-goals'>No goals</span>";

        const awayGoalsList = awayGoals.length ?
          `<ul class="goal-list">${
            awayGoals.map(goal => `
              <li>${goal.scorer} - ${goal.time}${goal.assist && goal.assist !== "Unassisted" ? `, Assist: ${goal.assist}` : ""}</li>
            `).join("")
          }</ul>` : "<span class='no-goals'>No goals</span>";

        const cards = event.cards || [];
        const cardsList = cards.length
          ? `<ul class="card-list">${
              cards.map(card => `
                <li class="${card.isRedCard ? 'red-card' : 'yellow-card'}">
                  ${card.player} (${card.team}) - ${card.time} (${card.type})
                </li>
              `).join("")
            }</ul>`
          : "<span class='no-cards'>No cards</span>";

        detailsContent = `
          <div class="match-details" style="display: none;">
            <div class="match-stats">
              <div class="key-events">
                <div class="team-goals">
                  <p><strong>${event.homeTeam.name} Goals:</strong></p>
                  ${homeGoalsList}
                </div>
                <div class="team-goals">
                  <p><strong>${event.awayTeam.name} Goals:</strong></p>
                  ${awayGoalsList}
                </div>
              </div>
              <div class="team-stats">
                <p><strong>${event.homeTeam.name}:</strong> Form: ${event.homeTeam.form} | Record: ${event.homeTeam.record}</p>
                <p><strong>${event.awayTeam.name}:</strong> Form: ${event.awayTeam.form} | Record: ${event.awayTeam.record}</p>
              </div>
              <div class="game-stats">
                <p>Possession: ${event.homeTeam.stats.possession} - ${event.awayTeam.stats.possession}</p>
                <p>Shots (On Target): ${event.homeTeam.stats.shots} (${event.homeTeam.stats.shotsOnTarget}) - ${event.awayTeam.stats.shots} (${event.awayTeam.stats.shotsOnTarget})</p>
                <p>Corners: ${event.homeTeam.stats.corners} - ${event.awayTeam.stats.corners}</p>
                <p>Fouls: ${event.homeTeam.stats.fouls} - ${event.awayTeam.stats.fouls}</p>
              </div>
              <div class="broadcast-info">
                <p>Broadcast: ${event.broadcast}</p>
              </div>
              ${oddsContent}
            </div>
          </div>
        `;
        console.log(`Added .match-details for in-progress match (ID: ${eventId})`);
      } else if (event.state === "post") {
        console.log(`Formatting post event: ${event.homeTeam.name} vs ${event.awayTeam.name}, Scores: ${event.homeTeam.score} - ${event.awayTeam.score}, KeyEvents: ${event.keyEvents.length}`);
        
        const homeGoals = event.goals?.filter(goal => goal.team === event.homeTeam.name) || [];
        const awayGoals = event.goals?.filter(goal => goal.team === event.awayTeam.name) || [];

        const homeGoalsList = homeGoals.length ?
          `<ul class="goal-list">${
            homeGoals.map(goal => `
              <li>${goal.scorer} - ${goal.time}${goal.assist && goal.assist !== "Unassisted" ? `, Assist: ${goal.assist}` : ""}</li>
            `).join("")
          }</ul>` : "<span class='no-goals'>No goals</span>";

        const awayGoalsList = awayGoals.length ?
          `<ul class="goal-list">${
            awayGoals.map(goal => `
              <li>${goal.scorer} - ${goal.time}${goal.assist && goal.assist !== "Unassisted" ? `, Assist: ${goal.assist}` : ""}</li>
            `).join("")
          }</ul>` : "<span class='no-goals'>No goals</span>";

        const cards = event.cards || [];
        const cardsList = cards.length
          ? `<ul class="card-list">${
              cards.map(card => `
                <li class="${card.isRedCard ? 'red-card' : 'yellow-card'}">
                  ${card.player} (${card.team}) - ${card.time} (${card.type})
                </li>
              `).join("")
            }</ul>`
          : "<span class='no-cards'>No cards</span>";

        detailsContent = `
          <div class="match-details" style="display: none;">
            <div class="match-stats">
              <div class="game-stats">
                <p><strong>Final Score:</strong> ${event.homeTeam.score} - ${event.awayTeam.score} </p>
                <p><strong>Possession:</strong> ${event.homeTeam.stats.possession} - ${event.awayTeam.stats.possession}</p>
                <p><strong>Shots (On Target):</strong> ${event.homeTeam.stats.shots} (${event.homeTeam.stats.shotsOnTarget}) - ${event.awayTeam.stats.shots} (${event.awayTeam.stats.shotsOnTarget})</p>
                <p><strong>Corners:</strong> ${event.homeTeam.stats.corners} - ${event.awayTeam.stats.corners}</p>
                <p><strong>Fouls:</strong> ${event.homeTeam.stats.fouls} - ${event.awayTeam.stats.fouls}</p>
              </div>
              <div class="key-events">
                <div class="team-goals">
                  <p><strong>${event.homeTeam.name} Goals:</strong></p>
                  ${homeGoalsList}
                </div>
                <div class="team-goals">
                  <p><strong>${event.awayTeam.name} Goals:</strong></p>
                  ${awayGoalsList}
                </div>
                <p><strong>Cards:</strong></p>
                ${cardsList}
              </div>
              <div class="team-stats">
                <p><strong>${event.homeTeam.name}:</strong> Form: ${event.homeTeam.form} | Record: ${event.homeTeam.record}</p>
                <p><strong>${event.awayTeam.name}:</strong> Form: ${event.awayTeam.form} | Record: ${event.awayTeam.record}</p>
              </div>
              <div class="broadcast-info">
                <p><strong>Broadcast:</strong> ${event.broadcast}</p>
              </div>
              ${oddsContent}
            </div>
          </div>
        `;
        console.log(`Added .match-details for completed match (ID: ${eventId})`);
      } else {
        detailsContent = `
          <div class="match-details" style="display: none;">
            <div class="match-stats">
              <div class="team-stats">
                <p><strong>${event.homeTeam.name}:</strong> Form: ${event.homeTeam.form} | Record: ${event.homeTeam.record}</p>
                <p><strong>${event.awayTeam.name}:</strong> Form: ${event.awayTeam.form} | Record: ${event.awayTeam.record}</p>
              </div>
              <div class="game-stats">
                <p>Match stats will be available once the game starts.</p>
              </div>
              <div class="broadcast-info">
                <p>Broadcast: ${event.broadcast}</p>
              </div>
              ${oddsContent}
            </div>
          </div>
        `;
        console.log(`Added .match-details for pre-state match (ID: ${eventId})`);
      }

      eventHtml += `
        <div class="event-card expandable-card ${event.state === "in" ? 'live-match' : ''}" data-event-id="${eventId}">
          <div class="card-header" style="cursor: pointer;">
            <div class="match-info">
              <div class="teams">
                ${event.homeTeam.logo ? `<img src="${event.homeTeam.logo}" alt="${event.homeTeam.name} Crest" class="team-crest">` : ""}
                <span class="team-name">${event.homeTeam.name}</span>
                <span class="score">${timeOrScore}</span>
                ${event.awayTeam.logo ? `<img src="${event.awayTeam.logo}" alt="${event.awayTeam.name} Crest" class="team-crest">` : ""}
                <span class="team-name">${event.awayTeam.name}</span>
              </div>
            </div>
            <div class="match-meta">
              <span class="datetime">${event.state === "in" || event.state === "post" ? event.statusDetail : `${event.displayDate} ${event.time}`}</span>
              <span class="location">${venue}</span>
            </div>
          </div>
          ${detailsContent}
        </div>
      `;
    });
  }

  eventHtml += '</div>';
  return eventHtml || `<p class="no-events">No football results available.</p>`;
}