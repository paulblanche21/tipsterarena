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

        modalBody.innerHTML = ''; // Clear previous content
        modalBody.innerHTML = '<p>Loading events...</p>';

        // Always fetch fresh events for the requested category
        const events = await fetchEventsForSport(sport, category);
        console.log(`Fetched ${events.length} events for ${sport} ${category}`);
        
        const html = await SPORT_HANDLERS[sport].formatEvents(events, category, true);
        modalBody.innerHTML = html || `<p>No ${categoryName.toLowerCase()} available for ${sportName}.</p>`;
        console.log(`Modal populated for ${sport} ${category}`);
        
        setupExpandableCards();
        
        if (sport === 'golf' && (category === 'inplay' || category === 'results') && events.length > 0) {
            await SPORT_HANDLERS[sport].setupLeaderboardUpdates();
            SPORT_HANDLERS[sport].setupLeaderboardControls();
        }
        
        modal.style.display = 'flex';
    } catch (error) {
        console.error(`Error populating modal for ${sport} ${category}:`, error);
        const modalBody = document.getElementById('event-modal-body');
        if (modalBody) {
            modalBody.innerHTML = '<p>Error loading events. Please try again later.</p>';
        } else {
            console.error('Cannot display error message: modalBody element not found');
        }
    } finally {
        isRenderingModal = false;
    }
}

// Adds toggle functionality for expandable cards
export function setupExpandableCards() {
    console.log('Setting up expandable cards');
    const cards = document.querySelectorAll('.expandable-card');
    console.log(`Found ${cards.length} expandable cards`);
    cards.forEach((card, index) => {
        const header = card.querySelector('.card-header');
        const details = card.querySelector('.match-details, .card-content');
        if (!header || !details) return;

        if (header._toggleHandler) {
            header.removeEventListener('click', header._toggleHandler, true);
        }

        const handler = (e) => {
            e.stopPropagation();
            const isVisible = details.style.display === 'block';
            details.style.display = isVisible ? 'none' : 'block';
            card.classList.toggle('expanded', !isVisible);
            console.log(`Toggled card ${index}, visible: ${!isVisible}`);
        };

        header.addEventListener('click', handler, { capture: true });
        header._toggleHandler = handler;
    });

    if (!document._cardCloseListener) {
        const closeHandler = (e) => {
            if (!e.target.closest('.expandable-card')) {
                document.querySelectorAll('.match-details, .card-content').forEach(details => {
                    details.style.display = 'none';
                });
                document.querySelectorAll('.expandable-card').forEach(card => {
                    card.classList.remove('expanded');
                });
                console.log('Closed all expandable cards');
            }
        };
        document.addEventListener('click', closeHandler, { capture: true });
        document._cardCloseListener = closeHandler;
    }
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