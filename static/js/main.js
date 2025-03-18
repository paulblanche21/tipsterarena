import { attachFollowButtonListeners } from './follow.js';
import { setupShowMoreButtons } from './feed.js';
import { setupCentralFeedPost, setupPostModal } from './post.js';
import { setupTipInteractions } from './tips.js';
import { setupNavigation } from './nav.js';
import { setupProfileEditing } from './profile.js';
import { initCarousel, populateEvents } from './carousel.js';
import { getDynamicEvents, getEventList } from './upcoming-events.js';
import { formatFootballList, formatGolfList, formatTennisList, formatHorseRacingList } from './upcoming-events.js';

document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM fully loaded');

    // Initialize all modules
    attachFollowButtonListeners();
    setupShowMoreButtons();
    console.log('Initializing central feed post setup...');
    setupCentralFeedPost(); // This will now use emoji-mart from the CDN
    console.log('Initializing post modal setup...');
    setupPostModal();
    setupTipInteractions();
    setupNavigation();
    setupProfileEditing();
    initCarousel(); // Handles the upcoming events carousel on home.html

    // Fetch dynamic events once for all sports
    const dynamicEvents = await getDynamicEvents();

    // Populate football events
    const footballEventsElement = document.getElementById('football-events');
    if (footballEventsElement && !footballEventsElement.closest('.carousel-container')) {
        const footballEvents = dynamicEvents.football || [];
        footballEventsElement.innerHTML = await formatFootballList(footballEvents, 'football', false) || '<p>No upcoming events available.</p>';
    }

    // Populate tennis events
    const tennisEventsElement = document.getElementById('tennis-events');
    if (tennisEventsElement && !tennisEventsElement.closest('.carousel-container')) {
        const tennisEvents = dynamicEvents.tennis || [];
        tennisEventsElement.innerHTML = await formatTennisList(tennisEvents, 'tennis', false) || '<p>No upcoming tournaments available.</p>';
    }

    // Populate golf events
    const golfEventsElement = document.getElementById('golf-events');
    if (golfEventsElement && !golfEventsElement.closest('.carousel-container')) {
        const golfEvents = dynamicEvents.golf || [];
        golfEventsElement.innerHTML = await formatGolfList(golfEvents, 'golf', false) || '<p>No upcoming events available.</p>';
    }

    // Populate horse racing events
    const horseRacingEventsElement = document.getElementById('horse-racing-events');
    if (horseRacingEventsElement && !horseRacingEventsElement.closest('.carousel-container')) {
        const horseRacingEvents = dynamicEvents.horse_racing || [];
        horseRacingEventsElement.innerHTML = await formatHorseRacingList(horseRacingEvents, 'horse_racing', false) || '<p>No upcoming events available.</p>';
    }
});