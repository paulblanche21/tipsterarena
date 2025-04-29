// static/js/pages/golf-events.js

export async function fetchEvents(state = 'pre', tourId = null) {
    console.log(`Fetching golf events for state: ${state}, tour: ${tourId || 'all'}`);
    try {
        let url = `/api/golf/events/?state=${state}`;
        if (tourId) {
            url += `&tour_id=${tourId}`;
        }
        console.log(`Making API request to: ${url}`);
        const response = await fetch(url, {
            headers: {
                'Authorization': `Token ${localStorage.getItem('authToken') || 'ba59ecf8d26672d59c949b70453c361e74c2eec8'}`
            },
            credentials: 'include'
        });
        console.log(`API status for ${state}: ${response.status} ${response.statusText}`);
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        console.log(`Raw API response for ${state}:`, data);
        if (!Array.isArray(data)) {
            console.error(`API response is not an array for ${state}:`, data);
            return [];
        }
        console.log(`Fetched ${data.length} golf events for ${state}`);

        const uniqueEvents = Array.from(new Map(data.map(event => [event.event_id, event])).values());
        console.log(`After deduplication, ${uniqueEvents.length} unique events for ${state}`);
        console.log('Unique events:', uniqueEvents);

        const mappedEvents = uniqueEvents.map(event => {
            const mapped = {
                id: event.event_id,
                name: event.name,
                shortName: event.short_name,
                date: event.date,
                displayDate: new Date(event.date).toLocaleDateString("en-US", { 
                    weekday: 'long',
                    month: "long", 
                    day: "numeric", 
                    year: "numeric",
                    hour: "numeric",
                    minute: "2-digit",
                    timeZoneName: "short"
                }),
                state: event.state,
                completed: event.completed,
                venue: {
                    fullName: event.venue,
                    address: { city: event.city, state: event.state_location }
                },
                tour: event.tour,
                course: event.course,
                purse: event.purse,
                broadcast: event.broadcast,
                currentRound: event.current_round,
                totalRounds: event.total_rounds,
                isPlayoff: event.is_playoff,
                weather: {
                    condition: event.weather_condition,
                    temperature: event.weather_temperature
                },
                league: event.tour?.name || 'Unknown Tour',
                icon: event.tour?.icon || '🏌️‍♂️',
                priority: event.tour?.priority || 999,
                apiLeague: event.tour?.tour_id || 'pga',
                leaderboard: (event.leaderboard || []).map(entry => ({
                    position: entry.position,
                    playerName: entry.player?.name || 'Unknown Player',
                    score: entry.score,
                    rounds: entry.rounds || [],
                    strokes: entry.strokes,
                    worldRanking: entry.player?.world_ranking || 'N/A',
                    status: entry.status || 'active'
                }))
            };
            console.log(`Mapped event ${event.event_id}:`, mapped);
            return mapped;
        });

        console.log(`Mapped ${mappedEvents.length} events for ${state}`);
        return mappedEvents;
    } catch (error) {
        console.error(`Error fetching golf events for ${state}:`, error);
        return [];
    }
}


export async function fetchLeaderboard(eventId, sport, apiLeague) {
    console.log(`Fetching leaderboard for event ${eventId}, tour: ${apiLeague}`);
    try {
        const response = await fetch(`/api/golf/events/?state=in`, {
            headers: {
                'Authorization': `Token ${localStorage.getItem('authToken') || 'ba59ecf8d26672d59c949b70453c361e74c2eec8'}`
            },
            credentials: 'include'
        });
        console.log(`Leaderboard API status: ${response.status} ${response.statusText}`);
        if (!response.ok) {
            // Fallback to results
            const responseResults = await fetch(`/api/golf/events/?state=post`, {
                headers: {
                    'Authorization': `Token ${localStorage.getItem('authToken') || 'ba59ecf8d26672d59c949b70453c361e74c2eec8'}`
                },
                credentials: 'include'
            });
            if (!responseResults.ok) throw new Error(`HTTP error: ${responseResults.status} ${response.statusText}`);
            const data = await responseResults.json();
            const event = data.find(e => e.event_id === eventId);
            if (!event) throw new Error(`Event ${eventId} not found in results`);
            return event.leaderboard.map(entry => ({
                position: entry.position,
                playerName: entry.player.name,
                score: entry.score,
                rounds: entry.rounds,
                strokes: entry.strokes,
                worldRanking: entry.player.world_ranking,
                status: entry.status
            }));
        }
        const data = await response.json();
        const event = data.find(e => e.event_id === eventId);
        if (!event) throw new Error(`Event ${eventId} not found in inplay events`);
        return event.leaderboard.map(entry => ({
            position: entry.position,
            playerName: entry.player.name,
            score: entry.score,
            rounds: entry.rounds,
            strokes: entry.strokes,
            worldRanking: entry.player.world_ranking,
            status: entry.status
        }));
    } catch (error) {
        console.error(`Error fetching leaderboard for event ${eventId}: ${error}`);
        return [];
    }
}

export async function formatEventList(events, sportKey, category, isCentralFeed = false) {
    if (!events?.length) {
        console.log(`No ${category} ${sportKey} events to format`);
        return `<p>No ${category} ${sportKey} events available.</p>`;
    }
    console.log(`Events to render for ${category} (length: ${events.length}):`, events);
    const eventItems = await Promise.all(events.map(async event => {
        console.log(`Formatting event: ${event.name}, ID: ${event.id}, League: ${event.apiLeague}`);
        const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
        let contentHtml = '';
        if (category === 'inplay' || category === 'results') {
            const leaderboard = event.leaderboard || [];  // Ensure leaderboard is an array
            contentHtml = leaderboard.length > 0 ? `
                <div class="leaderboard-content">
                    <h4>${category === 'inplay' ? 'Live Leaderboard' : 'Final Leaderboard'}</h4>
                    <div class="leaderboard-controls">
                        <div class="leaderboard-filter">
                            <label for="player-filter">Filter Players:</label>
                            <input type="text" id="player-filter" placeholder="Search players..." class="player-filter-input">
                        </div>
                        <div class="leaderboard-sort">
                            <label for="sort-by">Sort By:</label>
                            <select id="sort-by" class="sort-select">
                                <option value="position">Position</option>
                                <option value="score">Score</option>
                                <option value="name">Player Name</option>
                                <option value="rounds">Current Round</option>
                            </select>
                        </div>
                    </div>
                    <div class="leaderboard-wrapper">
                        <table class="leaderboard-table" data-event-id="${event.id}" data-api-league="${event.apiLeague || 'pga'}">
                            <thead>
                                <tr>
                                    <th data-sort="position">Pos</th>
                                    <th data-sort="name">Player</th>
                                    <th data-sort="score">Score</th>
                                    <th>R1</th>
                                    <th>R2</th>
                                    <th>R3</th>
                                    <th>R4</th>
                                    <th data-sort="total">Total</th>
                                    <th data-sort="rank">Rank</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${leaderboard.slice(0, 10).map(player => `
                                    <tr class="${player.status === 'active' ? 'player-active' : 'player-inactive'}" 
                                        data-player="${player.playerName.toLowerCase()}"
                                        data-position="${player.position}"
                                        data-score="${player.score}"
                                        data-total="${player.strokes}"
                                        data-rank="${player.worldRanking}">
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
                        <button class="view-full-leaderboard" data-event-id="${event.id}" data-api-league="${event.apiLeague || 'pga'}">View Full Leaderboard</button>
                    </div>
                    ${category === 'inplay' ? '<p class="leaderboard-status">Updating...</p>' : ''}
                </div>
            ` : `
                <div class="leaderboard-content">
                    <h4>${category === 'inplay' ? 'Live Leaderboard' : 'Final Leaderboard'}</h4>
                    <p>No leaderboard data available.</p>
                </div>
            `;
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
                        <span class="tour-icon">${event.icon}</span>
                        <span class="event-name">${event.name}</span>
                        <span class="event-status">(${status})</span>
                        ${liveIndicator}
                    </div>
                    <div class="event-meta">
                        <span class="datetime"><i class="far fa-calendar-alt"></i> ${event.displayDate}</span>
                        <span class="location"><i class="fas fa-map-marker-alt"></i> ${venue}</span>
                        <span class="tour-name">${event.league}</span>
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

// Add leaderboard sorting and filtering functionality
export function setupLeaderboardControls() {
    document.querySelectorAll('.leaderboard-table').forEach(table => {
        const filterInput = table.closest('.leaderboard-content')?.querySelector('.player-filter-input');
        const sortSelect = table.closest('.leaderboard-content')?.querySelector('.sort-select');
        
        if (filterInput) {
            filterInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase();
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const playerName = row.getAttribute('data-player');
                    row.style.display = playerName.includes(searchTerm) ? '' : 'none';
                });
            });
        }

        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                const sortBy = e.target.value;
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                
                rows.sort((a, b) => {
                    const aValue = a.getAttribute(`data-${sortBy}`);
                    const bValue = b.getAttribute(`data-${sortBy}`);
                    
                    if (sortBy === 'name') {
                        return aValue.localeCompare(bValue);
                    }
                    
                    const aNum = parseFloat(aValue);
                    const bNum = parseFloat(bValue);
                    
                    if (isNaN(aNum) || isNaN(bNum)) {
                        return 0;
                    }
                    
                    return aNum - bNum;
                });
                
                tbody.innerHTML = '';
                rows.forEach(row => tbody.appendChild(row));
            });
        }
    });
}

// In-memory cache for leaderboard data
const leaderboardCache = new Map();

export async function setupLeaderboardUpdates(retryCount = 0, maxRetries = 5) {
    console.log('Setting up leaderboard updates');
    const leaderboardTables = document.querySelectorAll('table.leaderboard-table, div.leaderboard-table');
    if (leaderboardTables.length === 0) {
        if (retryCount < maxRetries) {
            console.log(`No leaderboard tables found, scheduling retry ${retryCount + 1}/${maxRetries}`);
            setTimeout(() => setupLeaderboardUpdates(retryCount + 1, maxRetries), 5000);
        } else {
            console.log('Max retries reached, stopping leaderboard updates');
        }
        return;
    }

    const updateLeaderboard = async (table) => {
        const eventId = table.getAttribute('data-event-id');
        const apiLeague = table.getAttribute('data-api-league') || 'pga';
        if (!eventId) return;  // Remove isInplay check

        const cacheKey = `${eventId}-${apiLeague}`;
        let leaderboard;

        if (leaderboardCache.has(cacheKey)) {
            const cached = leaderboardCache.get(cacheKey);
            if (Date.now() - cached.timestamp < 30000) {
                leaderboard = cached.data;
                console.log(`Cache hit for leaderboard ${eventId}`);
            }
        }

        if (!leaderboard) {
            leaderboard = await fetchLeaderboard(eventId, "golf", apiLeague);
            if (leaderboard.length > 0) {
                leaderboardCache.set(cacheKey, { data: leaderboard, timestamp: Date.now() });
            }
        }

        if (leaderboard.length > 0) {
            const tbody = table.querySelector('tbody');
            tbody.innerHTML = leaderboard.slice(0, 10).map(player => `
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
            const statusEl = table.closest('.leaderboard-content')?.querySelector('.leaderboard-status');
            if (statusEl) {
                statusEl.textContent = 'Updated just now';
                setTimeout(() => {
                    if (statusEl.textContent === 'Updated just now') {
                        statusEl.textContent = 'Updating...';
                    }
                }, 5000);
            }
        }
    };

    leaderboardTables.forEach(table => {
        updateLeaderboard(table).catch(error => {
            console.error(`Error updating leaderboard for table ${table.getAttribute('data-event-id')}:`, error);
        });
        const intervalId = setInterval(() => {
            updateLeaderboard(table).catch(error => {
                console.error(`Polling error for leaderboard ${table.getAttribute('data-event-id')}:`, error);
            });
        }, 3600000); // 1 hour
        table.dataset.intervalId = intervalId;
    });

    document.querySelectorAll('.view-full-leaderboard').forEach(button => {
        button.addEventListener('click', async () => {
            const eventId = button.getAttribute('data-event-id');
            const apiLeague = button.getAttribute('data-api-league') || 'pga';
            const modalBody = document.getElementById('event-modal-body');
            const modalTitle = document.getElementById('event-modal-title');
            modalTitle.textContent = 'Full Leaderboard';
            modalBody.innerHTML = '<p>Loading...</p>';

            const cacheKey = `${eventId}-${apiLeague}`;
            let leaderboard = leaderboardCache.get(cacheKey)?.data;

            if (!leaderboard) {
                leaderboard = await fetchLeaderboard(eventId, "golf", apiLeague);
                if (leaderboard.length > 0) {
                    leaderboardCache.set(cacheKey, { data: leaderboard, timestamp: Date.now() });
                }
            }

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

export class GolfEventsHandler {
    constructor() {
        this.config = {
            leagues: [
                { sport: "golf", league: "pga", icon: "⛳", name: "PGA Tour", priority: 1 },
                { sport: "golf", league: "lpga", icon: "⛳", name: "LPGA Tour", priority: 2 }
            ],
            timePeriods: {
                results: 14, // 14 days for golf results
                fixtures: 30 // 30 days for golf fixtures
            }
        };
    }

    async fetchEvents(category) {
        try {
            const response = await fetch(`/api/golf-events/?category=${category}`, {
                headers: {
                    'Authorization': `Token ${localStorage.getItem('authToken') || 'ba59ecf8d26672d59c949b70453c361e74c2eec8'}`
                },
                credentials: 'include'
            });
            if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
            const events = await response.json();
            return this.mapEvents(events);
        } catch (error) {
            console.error(`Error fetching golf events (${category}):`, error);
            return [];
        }
    }

    mapEvents(events) {
        return events
            .filter(event => {
                if (!event || !event.event_id || !event.tour) {
                    console.warn(`Skipping invalid event:`, event);
                    return false;
                }
                return true;
            })
            .map(event => ({
                id: event.event_id,
                name: event.name,
                shortName: event.short_name,
                date: event.date,
                displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
                time: new Date(event.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
                state: event.state,
                completed: event.completed,
                venue: event.venue || "Location TBD",
                city: event.city,
                stateLocation: event.state_location,
                tour: event.tour.name,
                course: {
                    name: event.course.name,
                    par: event.course.par,
                    yardage: event.course.yardage
                },
                purse: event.purse,
                broadcast: event.broadcast,
                currentRound: event.current_round,
                totalRounds: event.total_rounds,
                isPlayoff: event.is_playoff,
                weather: {
                    condition: event.weather_condition,
                    temperature: event.weather_temperature
                },
                leaderboard: event.leaderboard || []
            }));
    }

    filterEvents(events, category) {
        const currentTime = new Date();
        const resultsDaysAgo = new Date(currentTime);
        resultsDaysAgo.setDate(currentTime.getDate() - this.config.timePeriods.results);
        
        const fixturesDaysAgo = new Date(currentTime);
        fixturesDaysAgo.setDate(currentTime.getDate() + this.config.timePeriods.fixtures);

        let filteredEvents = events;

        if (category === 'fixtures') {
            filteredEvents = events.filter(event => {
                const eventDate = new Date(event.date);
                return event.state === "pre" && 
                       eventDate > currentTime && 
                       eventDate <= fixturesDaysAgo;
            });
        } else if (category === 'inplay') {
            filteredEvents = events.filter(event => event.state === "in");
        } else if (category === 'results') {
            filteredEvents = events.filter(event => {
                const eventDate = new Date(event.date);
                return (event.state === "post" || event.completed) && 
                       eventDate >= resultsDaysAgo;
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
            return `<p>No ${category.replace(/_/g, ' ')} available.</p>`;
        }

        let html = '<div class="golf-feed">';
        events.forEach(event => {
            html += `
                <div class="tournament-card">
                    <div class="tournament-header">
                        <span class="tour-name">${event.tour}</span>
                        <span class="tournament-time">${event.time}</span>
                    </div>
                    <div class="tournament-content">
                        <h3 class="tournament-name">${event.name}</h3>
                        <div class="tournament-details">
                            <p><strong>Course:</strong> ${event.course.name}</p>
                            <p><strong>Location:</strong> ${event.venue}, ${event.city}, ${event.stateLocation}</p>
                            <p><strong>Purse:</strong> ${event.purse}</p>
                            <p><strong>Par:</strong> ${event.course.par} | <strong>Yardage:</strong> ${event.course.yardage}</p>
                        </div>
                        ${event.state === 'in' ? `
                            <div class="tournament-status">
                                <p><strong>Current Round:</strong> ${event.currentRound}/${event.totalRounds}</p>
                                <p><strong>Weather:</strong> ${event.weather.condition}, ${event.weather.temperature}</p>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';
        return html;
    }

    async setupLeaderboardUpdates() {
        // Implementation for live leaderboard updates
        // This can be called from the main page to set up live updates
    }
}