// main.js
import { attachFollowButtonListeners } from './follow.js';
import { setupShowMoreButtons } from './feed.js';
import { setupCentralFeedPost, setupPostModal } from './post.js';
import { setupTipInteractions } from './tips.js';
import { setupNavigation } from './nav.js';
import { setupProfileEditing } from './profile.js';
import { initCarousel } from './carousel.js';

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');

    // Initialize all modules
    attachFollowButtonListeners();
    setupShowMoreButtons();
    setupCentralFeedPost();
    setupPostModal();
    setupTipInteractions();
    setupNavigation();
    setupProfileEditing();
    initCarousel(); // Initialize the carousel for the right sidebar
});