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
                fixtures: 1, // days ahead for fixtures
                inplay: 0, // current day
                results: 7 // days back for results
            }
        };
    }

    async fetchEvents(category) {
        try {
            const response = await fetch(`/api/horse-racing-events/?category=${category}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return this.mapEvents(data);
        } catch (error) {
            console.error('Error fetching horse racing events:', error);
            return [];
        }
    }

    mapEvents(events) {
        if (!events || !Array.isArray(events)) {
            console.warn('Invalid events data received:', events);
            return [];
        }

        return events.map(event => {
            if (!event || !event.date || !event.venue) {
                console.warn('Invalid event data:', event);
                return null;
            }

            return {
                id: event.id || `${event.date}-${event.venue}`,
                name: event.name || `${event.venue} Racing`,
                date: event.date,
                venue: event.venue,
                races: event.races || [],
                state: this.determineEventState(event),
                sport: 'horse_racing'
            };
        }).filter(event => event !== null);
    }

    determineEventState(event) {
        const now = new Date();
        const eventDate = new Date(event.date);
        
        if (eventDate > now) {
            return 'pre';
        } else if (eventDate.toDateString() === now.toDateString()) {
            return 'in';
        } else {
            return 'post';
        }
    }

    filterEvents(events, category) {
        if (!events || !Array.isArray(events)) {
            return [];
        }

        const now = new Date();
        const filteredEvents = events.filter(event => {
            const eventDate = new Date(event.date);
            
            switch (category) {
                case 'fixtures':
                    return eventDate > now;
                case 'inplay':
                    return eventDate.toDateString() === now.toDateString();
                case 'results':
                    return eventDate < now;
                default:
                    return true;
            }
        });

        // Sort events by date
        return filteredEvents.sort((a, b) => new Date(a.date) - new Date(b.date));
    }

    formatEvents(events, category, isCentralFeed = false) {
        if (!events || events.length === 0) {
            return `<p>No ${category.replace(/_/g, ' ')} available.</p>`;
        }

        return events.map(event => `
            <div class="event-card ${isCentralFeed ? 'central-feed' : ''}">
                <div class="event-header">
                    <h3>${event.venue}</h3>
                    <span class="event-date">${new Date(event.date).toLocaleDateString()}</span>
                </div>
                <div class="event-races">
                    ${event.races.map(race => `
                        <div class="race-item">
                            <span class="race-time">${race.race_time}</span>
                            <span class="race-name">${race.name}</span>
                            <span class="race-runners">${race.runners}</span>
                        </div>
                    `).join('')}
                </div>
                <div class="event-footer">
                    <span class="event-status">${this.getStatusText(event.state)}</span>
                </div>
            </div>
        `).join('');
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
}