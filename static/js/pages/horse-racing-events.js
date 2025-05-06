// static/js/horse-racing-events.js
import { getCSRFToken } from './utils.js';

export async function fetchEvents() {
    console.log('Fetching race data from: /horse-racing/cards-json/');
    try {
        const response = await fetch('/horse-racing/cards-json/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
        });
        console.log(`Response status: ${response.status}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(`Fetched ${data.length} horse racing events`, data);
        return data;
    } catch (error) {
        console.error('Error fetching race data:', error);
        return [];
    }
}

export function formatEventList(events, sport, category, isCentral = false) {
    // Not used, as renderHorseRacingEvents handles rendering
    return '';
}

export class HorseRacingEventsHandler {
    constructor() {
        this.config = {
            leagues: [
                { sport: "horse_racing", league: "uk", icon: "🏇", name: "UK Racing", priority: 1 },
                { sport: "horse_racing", league: "ire", icon: "🏇", name: "Irish Racing", priority: 2 }
            ],
            timePeriods: {
                fixtures: 1,
                inplay: 0,
                results: 7
            }
        };
        
        this.events = new Map();
        this.pollInterval = 60000; // Poll every minute
        this.startPolling();
    }

    startPolling() {
        // Initial fetch with default category
        this.fetchEvents('upcoming_meetings');
        
        // Set up polling
        setInterval(() => {
            this.fetchEvents('upcoming_meetings');
        }, this.pollInterval);
    }

    async fetchEvents(category = 'upcoming_meetings') {
        console.log('Fetching race data...');
        try {
            const response = await fetch('/horse-racing/cards-json/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log(`Fetched ${data.length} racing events`);
            
            // Store events in Map using venue and date as key
            data.forEach(meeting => {
                const key = `${meeting.venue}-${meeting.date}`;
                this.events.set(key, meeting);
            });
            
            // Return filtered events
            const filteredEvents = this.filterEvents(Array.from(this.events.values()), category);
            console.log(`Filtered ${filteredEvents.length} events for category ${category}`);
            return filteredEvents;
        } catch (error) {
            console.error('Error fetching race data:', error);
            return [];
        }
    }

    filterEvents(events, category) {
        if (!events || !Array.isArray(events)) {
            return [];
        }

        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const threeDaysAgo = new Date(today);
        threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);

        return events.filter(event => {
            const eventDate = new Date(event.date);
            const eventDateOnly = new Date(eventDate.getFullYear(), eventDate.getMonth(), eventDate.getDate());
            
            switch (category) {
                case 'upcoming_meetings':
                    // Show today and tomorrow's meetings
                    return eventDateOnly >= today && eventDateOnly <= tomorrow;
                case 'at_the_post':
                    // Show only today's races that are in progress
                    return eventDateOnly.getTime() === today.getTime() && 
                           event.state === 'in';
                case 'race_results':
                    // Show results from the last 3 days
                    return eventDateOnly >= threeDaysAgo && eventDateOnly < today;
                default:
                    return true;
            }
        }).sort((a, b) => new Date(a.date) - new Date(b.date));
    }

    formatEvents(events, category, isCentralFeed = false) {
        if (!events || events.length === 0) {
            return `<p>No ${category.replace(/_/g, ' ')} available.</p>`;
        }

        // Filter events based on category
        const filteredEvents = this.filterEvents(events, category);
        if (filteredEvents.length === 0) {
            return `<p>No ${category.replace(/_/g, ' ')} available.</p>`;
        }

        // Create container for all events
        const container = document.createElement('div');
        container.className = 'events-container';

        // Format each event
        filteredEvents.forEach(event => {
            const eventCard = this.formatEventCard(event, isCentralFeed);
            container.innerHTML += eventCard;
        });

        return container.innerHTML;
    }

    formatEventCard(event, isCentralFeed) {
        if (!event) return '';
        
        return `
            <div class="event-card ${isCentralFeed ? 'central-feed' : ''}" data-meeting-id="${event.url}">
                <div class="event-header">
                    <h3>${event.venue}</h3>
                    <span class="event-date">${event.displayDate}</span>
                </div>
                <div class="event-races">
                    ${this.formatRaces(event.races)}
                </div>
                <div class="event-footer">
                    <span class="event-status">${this.getStatusText(event.state || 'pre')}</span>
                </div>
            </div>
        `;
    }

    formatRaces(races) {
        if (!races || !Array.isArray(races)) {
            console.log('No races data available:', races);
            return '';
        }
        
        console.log('Formatting races:', races); // Debug log
        
        return races.map(race => {
            console.log('Processing race:', race); // Debug log
            
            // Get the number of runners from the runners field
            const numRunners = race.runners ? race.runners.split(' ')[0] : 
                             (race.horses ? race.horses.length : 0);
            
            console.log('Number of runners:', numRunners); // Debug log
            
            const raceHtml = `
                <div class="race-item" data-race-id="${race.race_id || ''}">
                    <div class="race-header">
                        <span class="race-time">${race.race_time || 'TBC'}</span>
                        <span class="race-name">${race.name || 'Unnamed Race'}</span>
                        <span class="race-runners">${numRunners} runners</span>
                    </div>
                    <div class="race-details">
                        ${this.formatHorses(race.horses)}
                        ${race.going_data && race.going_data !== 'N/A' ? `<p><strong>Going:</strong> ${race.going_data}</p>` : ''}
                        ${race.race_class ? `<p><strong>Class:</strong> ${race.race_class}</p>` : ''}
                        ${race.distance ? `<p><strong>Distance:</strong> ${race.distance}</p>` : ''}
                        ${race.result && race.result.positions ? this.formatRaceResult(race.result.positions) : ''}
                    </div>
                </div>
            `;
            
            console.log('Generated race HTML:', raceHtml); // Debug log
            return raceHtml;
        }).join('');
    }

    formatHorses(horses) {
        if (!horses || !Array.isArray(horses) || horses.length === 0) {
            console.log('No horses data available:', horses);
            return '';
        }
        
        console.log('Formatting horses:', horses); // Debug log
        
        const horsesHtml = `
            <div class="race-runners">
                <h4>Runners</h4>
                <div class="runners-list">
                    ${horses.map(horse => {
                        console.log('Processing horse:', horse); // Debug log
                        return `
                            <div class="runner-item">
                                <div class="runner-header">
                                    <span class="runner-number">${horse.number || ''}</span>
                                    <span class="runner-name">${horse.name || 'Unknown Horse'}</span>
                                    ${horse.draw ? `<span class="runner-draw">(${horse.draw})</span>` : ''}
                                </div>
                                <div class="runner-details">
                                    <p>
                                        <span class="runner-jockey">Jockey: ${horse.jockey || 'No Jockey'}</span>
                                        <span class="runner-trainer">Trainer: ${horse.trainer || 'No Trainer'}</span>
                                    </p>
                                    ${horse.owner && horse.owner !== 'Unknown' ? `<p><span class="runner-owner">Owner: ${horse.owner}</span></p>` : ''}
                                    ${horse.form && horse.form !== 'N/A' ? `<p class="runner-form">Form: ${horse.form}</p>` : ''}
                                    ${horse.rpr && horse.rpr !== 'N/A' ? `<p class="runner-rating">RPR: ${horse.rpr}</p>` : ''}
                                    ${horse.spotlight && horse.spotlight !== 'N/A' ? `<p class="runner-stats">Spotlight: ${horse.spotlight}</p>` : ''}
                                    ${horse.trainer_14_days ? `
                                        <p class="trainer-stats">
                                            Trainer Stats (14 days): 
                                            Runs: ${horse.trainer_14_days.runs || 0}, 
                                            Wins: ${horse.trainer_14_days.wins || 0}, 
                                            Win%: ${horse.trainer_14_days.percent || 0}%
                                        </p>
                                    ` : ''}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
        
        console.log('Generated horses HTML:', horsesHtml); // Debug log
        return horsesHtml;
    }

    formatRaceResult(positions) {
        if (!positions || !Array.isArray(positions) || positions.length === 0) return '';
        
        return `
            <div class="race-result">
                <h4>Result</h4>
                <ul>
                    ${positions.map(result => `
                        <li>
                            ${result.position}. ${result.name}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    formatWeatherInfo(event) {
        if (!event.weather) return '';
        
        return `
            <div class="weather-info">
                <span class="temperature">${event.weather.temperature}°C</span>
                <span class="conditions">${event.weather.conditions}</span>
            </div>
        `;
    }

    getStatusText(state) {
        switch (state) {
            case 'pre':
                return 'Upcoming';
            case 'in':
                return 'In Progress';
            case 'post':
                return 'Completed';
            default:
                return 'Unknown';
        }
    }

    updateDisplay() {
        // Find all event containers
        const containers = document.querySelectorAll('.event-container');
        console.log(`Found ${containers.length} event containers`);
        
        containers.forEach(container => {
            const category = container.dataset.category;
            console.log(`Updating container for category: ${category}`);
            
            // Get filtered events for this category
            const events = this.filterEvents(Array.from(this.events.values()), category);
            console.log(`Found ${events.length} events for category ${category}`);
            
            // Format and update the container content
            const html = this.formatEvents(events, category, true);
            container.innerHTML = html;
            
            // Set up expandable cards after updating content
            const cards = container.querySelectorAll('.event-card');
            console.log(`Found ${cards.length} event cards in container`);
            
            cards.forEach(card => {
                const races = card.querySelectorAll('.race-item');
                races.forEach(race => {
                    const header = race.querySelector('.race-header');
                    const details = race.querySelector('.race-details');
                    
                    if (header && details) {
                        // Initially hide details
                        details.style.display = 'none';
                        
                        // Add click handler
                        header.addEventListener('click', () => {
                            const isExpanded = header.classList.contains('expanded');
                            
                            // Close all other races in this card
                            races.forEach(otherRace => {
                                if (otherRace !== race) {
                                    const otherHeader = otherRace.querySelector('.race-header');
                                    const otherDetails = otherRace.querySelector('.race-details');
                                    if (otherHeader && otherDetails) {
                                        otherDetails.style.display = 'none';
                                        otherHeader.classList.remove('expanded');
                                        otherDetails.classList.remove('expanded');
                                    }
                                }
                            });
                            
                            // Toggle current race
                            if (isExpanded) {
                                details.style.display = 'none';
                                header.classList.remove('expanded');
                                details.classList.remove('expanded');
                            } else {
                                details.style.display = 'block';
                                header.classList.add('expanded');
                                details.classList.add('expanded');
                            }
                        });
                    }
                });
            });
        });
    }
}