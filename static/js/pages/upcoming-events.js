import { getCSRFToken } from './utils.js';
import { FootballEventsHandler } from './football-events.js';
import { TennisEventsHandler } from './tennis-events.js';
import { GolfEventsHandler } from './golf-events.js';
import { HorseRacingEventsHandler } from './horse-racing-events.js';

// Configuration for sports and their respective leagues
const SPORT_CONFIG = {
    football: {
        leagues: new FootballEventsHandler().config.leagues,
        timePeriods: new FootballEventsHandler().config.timePeriods
    },
    tennis: {
        leagues: new TennisEventsHandler().config.leagues,
        timePeriods: new TennisEventsHandler().config.timePeriods
    },
    golf: {
        leagues: new GolfEventsHandler().config.leagues,
        timePeriods: new GolfEventsHandler().config.timePeriods
    },
    horse_racing: {
        leagues: new HorseRacingEventsHandler().config.leagues,
        timePeriods: new HorseRacingEventsHandler().config.timePeriods
    }
};

// Sport-specific handlers
const SPORT_HANDLERS = {
    football: new FootballEventsHandler(),
    tennis: new TennisEventsHandler(),
    golf: new GolfEventsHandler(),
    horse_racing: new HorseRacingEventsHandler()
};

// Global variables
let globalEvents = {};
let isInitialized = false;

// Main function to fetch events for a sport
async function fetchEventsForSport(sport, category) {
    try {
        if (SPORT_HANDLERS[sport]) {
            const events = await SPORT_HANDLERS[sport].fetchEvents(category);
            const filteredEvents = SPORT_HANDLERS[sport].filterEvents(events, category);
            globalEvents[sport] = filteredEvents; // Store filtered events in global cache
            return filteredEvents;
        }
        return [];
    } catch (error) {
        console.error(`Error fetching ${sport} events:`, error);
        return [];
    }
}

// Function to filter events based on category and sport
function filterEvents(events, category, sportKey) {
    if (!events || !Array.isArray(events)) {
        console.error('Invalid events data:', events);
        return [];
    }

    const currentTime = new Date();
    
    // Sport-specific time periods
    const timePeriods = {
        football: {
            results: 7,  // 7 days for football results
            fixtures: 14 // 14 days for football fixtures
        },
        tennis: {
            results: 30, // 30 days for tennis results
            fixtures: 30 // 30 days for tennis fixtures
        },
        golf: {
            results: 14, // 14 days for golf results
            fixtures: 30 // 30 days for golf fixtures
        },
        horse_racing: {
            results: 7,  // 7 days for horse racing results
            fixtures: 7  // 7 days for horse racing fixtures
        }
    };

    const sportPeriod = timePeriods[sportKey] || { results: 7, fixtures: 14 }; // Default to 7 days if sport not specified
    const resultsDaysAgo = new Date(currentTime);
    resultsDaysAgo.setDate(currentTime.getDate() - sportPeriod.results);
    
    const fixturesDaysAgo = new Date(currentTime);
    fixturesDaysAgo.setDate(currentTime.getDate() + sportPeriod.fixtures);

    let filteredEvents = events;

    if (category === 'fixtures') {
        filteredEvents = events.filter(match => {
            const matchDate = new Date(match.date);
            return match.state === "pre" && 
                   matchDate > currentTime && 
                   matchDate <= fixturesDaysAgo;
        });
    } else if (category === 'inplay') {
        filteredEvents = events.filter(match => match.state === "in");
    } else if (category === 'results') {
        filteredEvents = events.filter(match => {
            const matchDate = new Date(match.date);
            return (match.state === "post" || match.completed) && 
                   matchDate >= resultsDaysAgo;
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

// Function to format events for display
function formatEvents(events, category, isCentralFeed = false) {
    if (!events || events.length === 0) {
        return `<p>No ${category.replace(/_/g, ' ')} available.</p>`;
    }

    const sport = events[0]?.sport;
    if (SPORT_HANDLERS[sport]) {
        return SPORT_HANDLERS[sport].formatEvents(events, category, isCentralFeed);
    }

    // Fallback for sports without handlers
    return events.map(event => `
        <div class="event-card">
            <h3>${event.name}</h3>
            <p>${event.date}</p>
        </div>
    `).join('');
}

// Populates modal with events
let isRenderingModal = false;

async function populateModal(sport, category) {
    if (isRenderingModal) {
        console.log(`Already rendering modal for ${sport}, ${category}, skipping`);
        return;
    }
    isRenderingModal = true;
    try {
        console.log(`Populating modal for ${sport}, ${category}`);
        const modal = document.getElementById('event-modal');
        const modalTitle = document.getElementById('event-modal-title');
        const modalBody = document.getElementById('event-modal-body');
        const modalClose = document.querySelector('.event-modal-close');
        
        if (!modal || !modalTitle || !modalBody) {
            console.error('Modal elements not found');
            return;
        }

        // Set up close button handler
        if (modalClose) {
            modalClose.onclick = () => {
                modal.style.display = 'none';
                modalBody.innerHTML = '<p>Loading events...</p>';
            };
        }

        // Close modal when clicking outside
        window.onclick = (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
                modalBody.innerHTML = '<p>Loading events...</p>';
            }
        };

        const sportName = sport === 'horse_racing' ? 'Horse Racing' : sport.charAt(0).toUpperCase() + sport.slice(1);
        const categoryName = sport === 'horse_racing'
            ? category.replace('upcoming_meetings', 'Upcoming Meetings')
                      .replace('at_the_post', 'At the Post')
                      .replace('race_results', 'Race Results')
            : category.charAt(0).toUpperCase() + category.slice(1);
        modalTitle.textContent = `${sportName} ${categoryName}`;

        // Show modal immediately with loading state
        modal.style.display = 'block';
        modalBody.innerHTML = '<p>Loading events...</p>';

        // Fetch events
        const events = await fetchEventsForSport(sport, category);
        console.log(`Fetched ${events.length} events for ${sport} ${category}`);
        
        if (!events || events.length === 0) {
            modalBody.innerHTML = `<p>No ${categoryName.toLowerCase()} available for ${sportName}.</p>`;
            return;
        }

        // Format and display events
        const html = await SPORT_HANDLERS[sport].formatEvents(events, category, true);
        modalBody.innerHTML = html;
        console.log(`Modal populated for ${sport} ${category}`);
        
        // Set up expandable cards after content is loaded
        const cards = modalBody.querySelectorAll('.event-card');
        console.log(`Found ${cards.length} event cards`);
        
        cards.forEach(card => {
            const races = card.querySelectorAll('.race-item');
            console.log(`Found ${races.length} races in card`);
            
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
                                }
                            }
                        });
                        
                        // Toggle current race
                        details.style.display = isExpanded ? 'none' : 'block';
                        header.classList.toggle('expanded');
                    });
                }
            });
        });
        
        if (sport === 'golf' && (category === 'inplay' || category === 'results') && events.length > 0) {
            await SPORT_HANDLERS[sport].setupLeaderboardUpdates();
            SPORT_HANDLERS[sport].setupLeaderboardControls();
        }
    } catch (error) {
        console.error('Error populating modal:', error);
        const modalBody = document.getElementById('event-modal-body');
        if (modalBody) {
            modalBody.innerHTML = '<p>Error loading events. Please try again.</p>';
        }
    } finally {
        isRenderingModal = false;
    }
}

// Adds toggle functionality for expandable cards
export function setupExpandableCards() {
    const cards = document.querySelectorAll('.event-card');
    console.log('Found event cards:', cards.length);
    
    cards.forEach(card => {
        const races = card.querySelectorAll('.race-item');
        console.log(`Found ${races.length} races in card`);
        
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
                            }
                        }
                    });
                    
                    // Toggle current race
                    details.style.display = isExpanded ? 'none' : 'block';
                    header.classList.toggle('expanded');
                });
            }
        });
    });
}

// Initializes button-based event navigation
export async function initButtons() {
    if (isInitialized) {
        console.log('initButtons already called, skipping');
        return;
    }
    isInitialized = true;

    console.log('Initializing event buttons');
    const sidebar = document.querySelector('.upcoming-events-card');
    if (!sidebar) {
        console.warn('Upcoming events card not found');
        return;
    }

    const sportSelector = sidebar.querySelector('.sport-selector');
    const buttonsContainer = sidebar.querySelector('.event-buttons');
    const modal = document.getElementById('event-modal');
    const modalCloseBtn = document.querySelector('.event-modal-close');

    if (!buttonsContainer || !modal || !modalCloseBtn) {
        console.warn('Event buttons or modal elements not found');
        return;
    }

    let activeSport;
    if (sportSelector) {
        activeSport = sportSelector.value;
    } else {
        const sportClass = Array.from(sidebar.classList)
            .find(cls => cls.startsWith('upcoming-events-') && cls !== 'upcoming-events-card');
        activeSport = sportClass ? sportClass.replace('upcoming-events-', '') : 'football';
    }
    console.log(`Active sport: ${activeSport}`);

    const updateButtonLabels = (sport) => {
        const buttons = buttonsContainer.querySelectorAll('.event-btn');
        buttons.forEach(button => {
            const baseCategory = button.dataset.category;
            const horseRacingLabel = button.dataset.horseRacing;
            if (sport === 'horse_racing') {
                button.textContent = horseRacingLabel.replace(/_/g, ' ');
            } else {
                button.textContent = baseCategory.charAt(0).toUpperCase() + baseCategory.slice(1);
            }
        });
    };

    updateButtonLabels(activeSport);

    if (sportSelector) {
        sportSelector.addEventListener('change', () => {
            activeSport = sportSelector.value;
            console.log(`Sport changed to ${activeSport}`);
            updateButtonLabels(activeSport);
            const buttons = buttonsContainer.querySelectorAll('.event-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
        });
    }

    // Remove existing listeners to prevent duplicates
    buttonsContainer.removeEventListener('click', handleButtonClick);
    buttonsContainer.addEventListener('click', handleButtonClick);

    let debounceTimeout;
    function handleButtonClick(e) {
        const button = e.target.closest('.event-btn');
        if (!button) return;

        console.log(`Button clicked: ${button.dataset.category || button.dataset.horseRacing}`);
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            const buttons = buttonsContainer.querySelectorAll('.event-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const category = activeSport === 'horse_racing' ? button.dataset.horseRacing : button.dataset.category;

            populateModal(activeSport, category);
        }, 300); // 300ms debounce
    }

    modalCloseBtn.addEventListener('click', () => {
        console.log('Closing modal');
        modal.style.display = 'none';
        const buttons = buttonsContainer.querySelectorAll('.event-btn');
        buttons.forEach(btn => btn.classList.remove('active'));
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            console.log('Closing modal (outside click)');
            modal.style.display = 'none';
            const buttons = buttonsContainer.querySelectorAll('.event-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
        }
    });
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    console.log('DOMContentLoaded: Initializing upcoming-events.js');
    initButtons();
});