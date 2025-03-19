import { attachFollowButtonListeners } from './follow.js';
import { setupShowMoreButtons } from './feed.js';
import { setupCentralFeedPost, setupPostModal } from './post.js';
import { setupTipInteractions } from './tips.js';
import { setupNavigation } from './nav.js';
import { setupProfileEditing } from './profile.js';
import { initCarousel } from './carousel.js';
import { getDynamicEvents, getEventList, formatFootballList, formatGolfList, formatTennisList, formatHorseRacingList } from './upcoming-events.js';

document.addEventListener('DOMContentLoaded', async function() {
  console.log('DOM fully loaded');

  attachFollowButtonListeners();
  setupShowMoreButtons();
  setupCentralFeedPost();
  setupPostModal();
  setupTipInteractions();
  setupNavigation();
  setupProfileEditing();
  initCarousel();

  const dynamicEvents = await getDynamicEvents();

  // Sidebar population
  const footballEventsElement = document.getElementById('football-events');
  if (footballEventsElement) {
    const footballEvents = dynamicEvents.football || [];
    footballEventsElement.innerHTML = await formatFootballList(footballEvents, 'football', false) || '<p>No upcoming events available.</p>';
  }

  const golfEventsElement = document.getElementById('golf-events');
  if (golfEventsElement) {
    const golfEvents = dynamicEvents.golf || [];
    golfEventsElement.innerHTML = await formatGolfList(golfEvents, 'golf', false) || '<p>No upcoming events available.</p>';
    // Optionally setup leaderboard if in `golf-events.js`
    setupLeaderboardUpdates();
  }

  const tennisEventsElement = document.getElementById('tennis-events');
  if (tennisEventsElement) {
    const tennisEvents = dynamicEvents.tennis || [];
    tennisEventsElement.innerHTML = await formatTennisList(tennisEvents, 'tennis', false) || '<p>No upcoming tournaments available.</p>';
  }

  const horseRacingEventsElement = document.getElementById('horse-racing-events');
  if (horseRacingEventsElement) {
    const horseRacingEvents = dynamicEvents.horse_racing || [];
    horseRacingEventsElement.innerHTML = await formatHorseRacingList(horseRacingEvents, 'horse_racing', false) || '<p>No upcoming races available.</p>';
  }
});