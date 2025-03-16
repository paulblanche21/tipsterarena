// main.js
import { attachFollowButtonListeners } from './follow.js';
import { setupShowMoreButtons } from './feed.js';
import { setupCentralFeedPost, setupPostModal } from './post.js';
import { setupTipInteractions } from './tips.js';
import { setupNavigation } from './nav.js';
import { setupProfileEditing } from './profile.js';
import { initCarousel, populateEvents } from './carousel.js';
import { getDynamicEvents, getEventList } from './upcoming-events.js';
import { formatFootballList, formatGolfList, formatTennisList, formatHorseRacingList } from './upcoming-events.js';

// Add 'async' to the function to allow 'await' inside
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM fully loaded');

    // Initialize all modules
    attachFollowButtonListeners();
    setupShowMoreButtons();
    setupCentralFeedPost();
    setupPostModal();
    setupTipInteractions();
    setupNavigation();
    setupProfileEditing();
    initCarousel(); // This will now handle the upcoming events carousel

    // Populate football events for the sidebar if on the football page
    if (document.getElementById('football-events')) {
        const dynamicEvents = await getDynamicEvents();
        const footballEvents = dynamicEvents.football || [];
        const eventList = document.getElementById('football-events');
        eventList.innerHTML = formatFootballList(footballEvents, 'football', false) || '<p>No upcoming events available.</p>';
    }
});