// carousel.js
console.log("Initializing carousel");
// Initialize the carousel
export async function initCarousel() {
  console.log("Initializing carousel");
  const carouselContainers = document.querySelectorAll('.carousel-container');
  carouselContainers.forEach(container => {
    const slides = container.querySelectorAll('.carousel-slide');
    if (slides.length > 0) {
      populateCarousel(container);
      setupSlideNavigation(container);
      setupDotNavigation(container);
    }
  });
}

async function populateCarousel(container) {
  console.log("Populating carousel");
  const dynamicEvents = await getDynamicEvents(); // Assuming this is also async
  console.log("All events for carousel:", dynamicEvents);

  const slides = container.querySelectorAll('.carousel-slide');
  for (const slide of slides) {
      const sport = slide.getAttribute('data-sport');
      if (sport) {
          const eventList = slide.querySelector('.event-list');
          if (eventList) {
              const events = dynamicEvents[sport] || dynamicEvents.all || [];
              // Use await to get the resolved HTML string
              eventList.innerHTML = await formatEventList(events, sport, false) || '<p>No upcoming events available.</p>';
              console.log(`${sport} carousel updated with:`, eventList.innerHTML);
          } else {
              console.warn(`Event list container not found for ${sport}`);
          }
      }
  }
}

export async function populateEvents(sport, elementId) {
  console.log(`Populating events for ${sport}`);
  const dynamicEvents = await getDynamicEvents();
  console.log("All events:", dynamicEvents);
  const eventList = document.getElementById(elementId);
  if (eventList) {
    const events = dynamicEvents[sport] || [];
    const formattedEvents = await formatEventList(events, sport, false); // Add await
    eventList.innerHTML = formattedEvents || '<p>No upcoming events available.</p>';
    console.log(`${sport} events updated with:`, eventList.innerHTML);
  } else {
    console.warn(`Event list container not found for ${sport}`);
  }
}

// carousel.js
function setupSlideNavigation(container) {
  const prevButton = container.querySelector('.carousel-prev');
  const nextButton = container.querySelector('.carousel-next');
  const slides = container.querySelectorAll('.carousel-slide');

  if (slides.length <= 1) return; // No navigation if only one slide

  let currentSlide = 0;
  showSlide(container, currentSlide);

  prevButton?.addEventListener('click', () => {
    currentSlide = (currentSlide > 0) ? currentSlide - 1 : slides.length - 1;
    showSlide(container, currentSlide);
  });

  nextButton?.addEventListener('click', () => {
    currentSlide = (currentSlide < slides.length - 1) ? currentSlide + 1 : 0;
    showSlide(container, currentSlide);
  });
}

function setupDotNavigation(container) {
  const dots = container.querySelectorAll('.dot');
  const slides = container.querySelectorAll('.carousel-slide');

  if (slides.length <= 1) return; // No navigation if only one slide

  dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
      showSlide(container, index);
    });
  });
}

function showSlide(container, index) {
  const slides = container.querySelectorAll('.carousel-slide');
  const dots = container.querySelectorAll('.dot');

  slides.forEach((slide, i) => {
    slide.classList.toggle('active', i === index);
  });

  dots.forEach((dot, i) => {
    dot.classList.toggle('active', i === index);
  });
}

// Import necessary functions (adjust imports based on your project structure)
import { getDynamicEvents } from './upcoming-events.js';
import { formatEventList } from './golf-events.js'; // Import from the appropriate module