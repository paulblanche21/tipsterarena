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
    initCarousel(); // Handles the upcoming events carousel on home.html

    // Populate events for each sport
    const footballEventsElement = document.getElementById('football-events');
    if (footballEventsElement && !footballEventsElement.closest('.carousel-container')) {
      const dynamicEvents = await getDynamicEvents();
      const footballEvents = dynamicEvents.football || [];
      footballEventsElement.innerHTML = await formatFootballList(footballEvents, 'football', false) || '<p>No upcoming events available.</p>';
    }

   
    // Populate golf events
    const golfEventsElement = document.getElementById('golf-events');
    if (golfEventsElement && !golfEventsElement.closest('.carousel-container')) {
      const dynamicEvents = await getDynamicEvents();
      const golfEvents = dynamicEvents.golf || [];
      golfEventsElement.innerHTML = await formatGolfList(golfEvents, 'golf', false) || '<p>No upcoming events available.</p>';
    }
  
});
   
