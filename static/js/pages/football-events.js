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
            let allEvents = [];
            let nextUrl = `/api/football-events/?category=${category}`;
            
            while (nextUrl) {
                const response = await fetch(nextUrl, {
                    headers: {
                        'Authorization': `Token ${localStorage.getItem('authToken') || 'b9e24e9c8e2247396e4062c2cb58dd76972fa790'}`
                    },
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error: ${response.status}`);
                }
                
                const data = await response.json();
                console.log('API Response:', data); // Debug log
                
                if (!Array.isArray(data)) {
                    console.error('Expected array of events, got:', typeof data);
                    return [];
                }
                
                allEvents = allEvents.concat(data);
                nextUrl = data.next;
            }
            
            return this.mapEvents(allEvents);
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

                    // Process team stats with proper fallbacks
                    const home_team_stats = event.home_team_stats || {};
                    const away_team_stats = event.away_team_stats || {};

                    return {
                        id: event.id || event.event_id,
                        name: event.name || `${event.home_team?.name || 'Unknown'} vs ${event.away_team?.name || 'Unknown'}`,
                        date: event.date,
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
                        home_team: {
                            name: event.home_team?.name || 'Unknown Team',
                            logo: event.home_team?.logo || window.default_avatar_url || '/static/img/default-avatar.png',
                            form: event.home_team?.form || 'N/A',
                            record: event.home_team?.record || 'N/A'
                        },
                        away_team: {
                            name: event.away_team?.name || 'Unknown Team',
                            logo: event.away_team?.logo || window.default_avatar_url || '/static/img/default-avatar.png',
                            form: event.away_team?.form || 'N/A',
                            record: event.away_team?.record || 'N/A'
                        },
                        home_score: event.home_score || '0',
                        away_score: event.away_score || '0',
                        home_team_stats: {
                            possession: home_team_stats.possession || 'N/A',
                            shots: home_team_stats.shots || 'N/A',
                            shots_on_target: home_team_stats.shots_on_target || 'N/A',
                            corners: home_team_stats.corners || 'N/A',
                            fouls: home_team_stats.fouls || 'N/A'
                        },
                        away_team_stats: {
                            possession: away_team_stats.possession || 'N/A',
                            shots: away_team_stats.shots || 'N/A',
                            shots_on_target: away_team_stats.shots_on_target || 'N/A',
                            corners: away_team_stats.corners || 'N/A',
                            fouls: away_team_stats.fouls || 'N/A'
                        },
                        clock: event.clock || null,
                        period: event.period || 0,
                        broadcast: event.broadcast || 'N/A',
                        key_events: event.key_events || [],
                        odds: event.odds || [],
                        detailed_stats: event.detailed_stats || []
                    };
                } catch (error) {
                    console.error('Error mapping event:', error, event);
                    return null;
                }
            })
            .filter(event => event !== null) // Remove any failed mappings
            .sort((a, b) => {
                // First sort by date
                const dateComparison = new Date(a.date) - new Date(b.date);
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
                const home_logo = event.home_team?.logo || defaultAvatar;
                const away_logo = event.away_team?.logo || defaultAvatar;
                const home_team = event.home_team || { name: 'Unknown Team' };
                const away_team = event.away_team || { name: 'Unknown Team' };
                const eventClass = this.getEventClass(event);
                const scoreDisplay = event.state === 'pre' ? 'vs' : `${event.home_score} - ${event.away_score}`;

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
                                    <div class="stat-value">${event.home_team_stats?.possession || 'N/A'}</div>
                                    <div class="stat-label">Possession</div>
                                    <div class="stat-value">${event.away_team_stats?.possession || 'N/A'}</div>
                                </div>
                                <div class="stats-row">
                                    <div class="stat-value">${event.home_team_stats?.shots || 'N/A'}</div>
                                    <div class="stat-label">Shots</div>
                                    <div class="stat-value">${event.away_team_stats?.shots || 'N/A'}</div>
                                </div>
                                <div class="stats-row">
                                    <div class="stat-value">${event.home_team_stats?.shots_on_target || 'N/A'}</div>
                                    <div class="stat-label">Shots on Target</div>
                                    <div class="stat-value">${event.away_team_stats?.shots_on_target || 'N/A'}</div>
                                </div>
                                <div class="stats-row">
                                    <div class="stat-value">${event.home_team_stats?.corners || 'N/A'}</div>
                                    <div class="stat-label">Corners</div>
                                    <div class="stat-value">${event.away_team_stats?.corners || 'N/A'}</div>
                                </div>
                                <div class="stats-row">
                                    <div class="stat-value">${event.home_team_stats?.fouls || 'N/A'}</div>
                                    <div class="stat-label">Fouls</div>
                                    <div class="stat-value">${event.away_team_stats?.fouls || 'N/A'}</div>
                                </div>
                            </div>
                            ${event.key_events && event.key_events.length > 0 ? `
                                <div class="key-events">
                                    <h4>Key Events</h4>
                                    <ul>
                                        ${event.key_events.map(e => `<li>${e.time}' - ${e.description}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
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
        const home_logo = event.home_team?.logo || defaultAvatar;
        const away_logo = event.away_team?.logo || defaultAvatar;
        const home_team = event.home_team || { name: 'Unknown Team' };
        const away_team = event.away_team || { name: 'Unknown Team' };
        const eventClass = this.getEventClass(event);
        const scoreDisplay = event.state === 'pre' ? 'vs' : `${event.home_score} - ${event.away_score}`;

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
        `<span class="live-score">${event.scores.homeScore} vs ${event.scores.awayScore}</span>` :
        event.state === "post" ?
        `<span class="final-score">${event.homeTeam.score} vs ${event.awayTeam.score}</span>` :
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