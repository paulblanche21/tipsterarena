// static/js/pages/golf-events.js

export async function fetchEvents(state = 'pre', tourId = null) {
    console.log(`Fetching golf events for state: ${state}, tour: ${tourId || 'all'}`);
    try {
        // Map category names to state values
        const stateMap = {
            'fixtures': 'pre',
            'inplay': 'in',
            'results': 'post'
        };
        const mappedState = stateMap[state] || state;

        const url = new URL('/api/golf-events/', window.location.origin);
        url.searchParams.append('state', mappedState);
        if (tourId) {
            url.searchParams.append('tour_id', tourId);
        }

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Raw API response:', data);

        // Handle paginated response
        if (data && typeof data === 'object') {
            if (Array.isArray(data)) {
                return data;  // Direct array response
            } else if (data.results && Array.isArray(data.results)) {
                return data.results;  // Paginated response
            } else {
                console.warn('Unexpected API response format:', data);
                return [];
            }
        }
        return [];
    } catch (error) {
        console.error('Error fetching golf events:', error);
        return [];
    }
}

export async function fetchLeaderboard(eventId, sport, apiLeague) {
    console.log(`Fetching leaderboard for event ${eventId}, tour: ${apiLeague}`);
    try {
        const response = await fetch(`/api/golf-events/${eventId}/`);
        console.log(`Leaderboard API status: ${response.status} ${response.statusText}`);
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        if (!data.leaderboard) {
            throw new Error(`No leaderboard data found for event ${eventId}`);
        }
        return data.leaderboard.map(entry => ({
            position: entry.position,
            playerName: entry.player.name,
            score: entry.score,
            rounds: entry.rounds,
            strokes: entry.strokes,
            worldRanking: entry.player.world_ranking,
            status: entry.status
        }));
    } catch (error) {
        console.error(`Error fetching leaderboard for event ${eventId}:`, error);
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
        console.log(`Formatting event: ${event.name}, ID: ${event.event_id}, League: ${event.tour.name}`);
        const venue = event.venue || 'Venue TBA';
        let contentHtml = '';
        
        // For fixtures, only show tournament details
        if (category === 'fixtures') {
            contentHtml = `
                <div class="event-details">
                    <p><strong>Tournament:</strong> ${event.name || 'Tournament Name TBA'}</p>
                    <p><strong>Date:</strong> ${new Date(event.date).toLocaleDateString()}</p>
                    <p><strong>Venue:</strong> ${venue}</p>
                    <p><strong>Course:</strong> ${event.course?.name || 'Course TBA'}</p>
                    <p><strong>Par:</strong> ${event.course?.par || 'TBA'}</p>
                    <p><strong>Yardage:</strong> ${event.course?.yardage || 'TBA'}</p>
                    <p><strong>Purse:</strong> ${event.purse || 'TBA'}</p>
                    <p><strong>Broadcast:</strong> ${event.broadcast || 'TBA'}</p>
                    <p><strong>Tour:</strong> ${event.tour?.name || 'Tour TBA'}</p>
                </div>
            `;
        } else if (category === 'inplay' || category === 'results') {
            // For inplay and results, show leaderboard
            const leaderboard = event.leaderboard || [];
            contentHtml = `
                <div class="leaderboard-content">
                    <div class="tournament-info">
                        <p><strong>Tournament:</strong> ${event.name || 'Tournament Name TBA'}</p>
                        <p><strong>Round:</strong> ${event.current_round}/${event.total_rounds}</p>
                        ${event.weather_condition ? `
                            <p><strong>Weather:</strong> ${event.weather_condition}, ${event.weather_temperature}</p>
                        ` : ''}
                    </div>
                    ${leaderboard.length > 0 ? `
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
                            <table class="leaderboard-table" data-event-id="${event.event_id}" data-api-league="${event.tour?.tour_id || 'pga'}">
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
                                            data-player="${player.player.name.toLowerCase()}"
                                            data-position="${player.position}"
                                            data-score="${player.score}"
                                            data-total="${player.strokes}"
                                            data-rank="${player.player.world_ranking}">
                                            <td>${player.position}</td>
                                            <td>${player.player.name}</td>
                                            <td>${player.score}</td>
                                            <td>${player.rounds[0] || "N/A"}</td>
                                            <td>${player.rounds[1] || "N/A"}</td>
                                            <td>${player.rounds[2] || "N/A"}</td>
                                            <td>${player.rounds[3] || "N/A"}</td>
                                            <td>${player.strokes}</td>
                                            <td>${player.player.world_ranking}</td>
                                        </tr>
                                    `).join("")}
                                </tbody>
                            </table>
                            <button class="view-full-leaderboard" data-event-id="${event.event_id}" data-api-league="${event.tour?.tour_id || 'pga'}">View Full Leaderboard</button>
                        </div>
                        ${category === 'inplay' ? '<p class="leaderboard-status">Updating...</p>' : ''}
                    ` : `
                        <p>No leaderboard data available yet.</p>
                    `}
                </div>
            `;
        }

        const status = category === 'inplay' ? 'In Progress' : category === 'results' ? 'Completed' : 'Upcoming';
        const liveIndicator = category === 'inplay' ? '<span class="live-indicator">Live</span>' : '';
        
        return `
            <div class="golf-card expandable-card ${category === 'inplay' ? 'live-event' : ''}">
                <div class="card-header">
                    <div class="event-info">
                        <span class="tour-icon">${event.tour?.icon || '🏌️'}</span>
                        <span class="event-name">${event.name || 'Tournament Name TBA'}</span>
                        <span class="event-status">(${status})</span>
                        ${liveIndicator}
                    </div>
                    <div class="event-meta">
                        <span class="datetime"><i class="far fa-calendar-alt"></i> ${new Date(event.date).toLocaleDateString()}</span>
                        <span class="location"><i class="fas fa-map-marker-alt"></i> ${venue}</span>
                        <span class="tour-name">${event.tour?.name || 'Tour TBA'}</span>
                    </div>
                </div>
                <div class="card-content" style="display: none;">
                    ${contentHtml}
                </div>
            </div>
        `;
    }));

    return eventItems.join('');
}

export function setupLeaderboardControls() {
    // Add event listeners for filtering and sorting
    document.querySelectorAll('.player-filter-input').forEach(input => {
        input.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const table = e.target.closest('.leaderboard-content').querySelector('.leaderboard-table');
            table.querySelectorAll('tbody tr').forEach(row => {
                const playerName = row.getAttribute('data-player');
                row.style.display = playerName.includes(searchTerm) ? '' : 'none';
            });
        });
    });

    document.querySelectorAll('.sort-select').forEach(select => {
        select.addEventListener('change', (e) => {
            const sortBy = e.target.value;
            const table = e.target.closest('.leaderboard-content').querySelector('.leaderboard-table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {
                const aValue = a.getAttribute(`data-${sortBy}`);
                const bValue = b.getAttribute(`data-${sortBy}`);
                if (sortBy === 'name') {
                    return aValue.localeCompare(bValue);
                }
                return parseFloat(aValue) - parseFloat(bValue);
            });

            rows.forEach(row => tbody.appendChild(row));
        });
    });

    // Handle horizontal scroll indicator
    document.querySelectorAll('.leaderboard-wrapper').forEach(wrapper => {
        const checkOverflow = () => {
            const hasOverflow = wrapper.scrollWidth > wrapper.clientWidth;
            wrapper.classList.toggle('has-overflow', hasOverflow);
        };

        // Check on initial load
        checkOverflow();

        // Check on window resize
        window.addEventListener('resize', checkOverflow);

        // Check when the table content changes
        const observer = new MutationObserver(checkOverflow);
        observer.observe(wrapper, { childList: true, subtree: true });
    });
}

export async function setupLeaderboardUpdates(retryCount = 0, maxRetries = 5) {
    const updateInterval = 60000; // Update every minute
    const tables = document.querySelectorAll('.leaderboard-table');
    
    if (!tables.length) {
        if (retryCount < maxRetries) {
            setTimeout(() => setupLeaderboardUpdates(retryCount + 1, maxRetries), 1000);
        }
        return;
    }

    const updateLeaderboard = async (table) => {
        const eventId = table.getAttribute('data-event-id');
        const apiLeague = table.getAttribute('data-api-league');
        
        try {
            const leaderboard = await fetchLeaderboard(eventId, 'golf', apiLeague);
            if (!leaderboard.length) {
                console.warn(`No leaderboard data for event ${eventId}`);
                return;
            }

            const tbody = table.querySelector('tbody');
            tbody.innerHTML = leaderboard.slice(0, 10).map(player => `
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
            `).join("");

            const status = table.closest('.leaderboard-content').querySelector('.leaderboard-status');
            if (status) {
                status.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
            }
        } catch (error) {
            console.error(`Error updating leaderboard for event ${eventId}:`, error);
        }
    };

    // Initial update
    tables.forEach(table => updateLeaderboard(table));

    // Set up periodic updates
    setInterval(() => {
        tables.forEach(table => updateLeaderboard(table));
    }, updateInterval);
}

export class GolfEventsHandler {
    constructor() {
        this.setupLeaderboardUpdates = setupLeaderboardUpdates;
        this.setupLeaderboardControls = setupLeaderboardControls;
        this.config = {
            leagues: [
                { id: 'pga', name: 'PGA Tour', icon: '🏌️‍♂️' },
                { id: 'lpga', name: 'LPGA Tour', icon: '🏌️‍♀️' }
            ],
            timePeriods: {
                results: 14, // 14 days for golf results
                fixtures: 30 // 30 days for golf fixtures
            }
        };
    }

    async fetchEvents(category) {
        console.log(`Fetching golf events for category: ${category}`);
        const events = await fetchEvents(category);
        if (!events || !Array.isArray(events)) {
            console.warn(`Invalid events data received: ${events}`);
            return [];
        }
        return events;
    }

    async formatEvents(events, category, isCentralFeed = false) {
        return formatEventList(events, 'golf', category, isCentralFeed);
    }

    filterEvents(events, category) {
        if (!events || !Array.isArray(events)) {
            console.error('Invalid events data:', events);
            return [];
        }

        const currentTime = new Date();
        const sportPeriod = this.config.timePeriods;
        const resultsDaysAgo = new Date(currentTime);
        resultsDaysAgo.setDate(currentTime.getDate() - sportPeriod.results);
        
        const fixturesDaysAgo = new Date(currentTime);
        fixturesDaysAgo.setDate(currentTime.getDate() + sportPeriod.fixtures);

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
}