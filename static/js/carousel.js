// carousel.js
console.log("Initializing carousel");

import { getDynamicEvents, formatFootballList, formatGolfList, formatTennisList, formatHorseRacingList } from './upcoming-events.js';

const FORMATTERS = {
  football: formatFootballList,
  golf: formatGolfList,
  tennis: formatTennisList,
  horse_racing: formatHorseRacingList
};

export async function initCarousel() {
  console.log("Initializing carousel");
  const carouselContainers = document.querySelectorAll('.carousel-container');
  carouselContainers.forEach(async container => {
    const slides = container.querySelectorAll('.carousel-slide');
    if (slides.length > 0) {
      await populateCarousel(container);
      setupDotNavigation(container);
      startAutoRotation(container);
    } else {
      console.warn("No slides found in carousel container");
    }
  });
}

async function populateCarousel(container) {
  console.log("Populating carousel");
  const dynamicEvents = await getDynamicEvents();
  console.log("All events for carousel:", Object.keys(dynamicEvents).map(key => `${key}: ${dynamicEvents[key].length}`));

  const slides = container.querySelectorAll('.carousel-slide');
  for (const slide of slides) {
    const sport = slide.getAttribute('data-sport');
    if (sport && FORMATTERS[sport]) {
      const eventList = slide.querySelector('.event-list');
      if (eventList) {
        const events = dynamicEvents[sport] || [];
        eventList.innerHTML = await FORMATTERS[sport](events, sport, false) || `<p>No upcoming ${sport} events available.</p>`;
        console.log(`${sport} carousel updated with:`, eventList.innerHTML);
      } else {
        console.warn(`Event list container not found for ${sport}`);
      }
    } else {
      console.warn(`No formatter found for sport: ${sport}`);
    }
  }
}

function setupDotNavigation(container) {
  const dots = container.querySelectorAll('.dot');
  const slides = container.querySelectorAll('.carousel-slide');

  if (slides.length <= 1) {
    console.log("Only one slide, dot navigation disabled");
    return;
  }

  if (dots.length !== slides.length) {
    console.warn("Mismatch between number of dots and slides");
  }

  dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
      showSlide(container, index);
    });
  });

  // Set initial active dot
  const activeSlideIndex = Array.from(slides).findIndex(slide => slide.classList.contains('active'));
  showSlide(container, activeSlideIndex !== -1 ? activeSlideIndex : 0);
}

function startAutoRotation(container) {
  const slides = container.querySelectorAll('.carousel-slide');
  if (slides.length <= 1) return;

  let currentSlide = Array.from(slides).findIndex(slide => slide.classList.contains('active'));
  if (currentSlide === -1) currentSlide = 0;

  const interval = setInterval(() => {
    currentSlide = (currentSlide < slides.length - 1) ? currentSlide + 1 : 0;
    showSlide(container, currentSlide);
  }, 5000); // 5 seconds

  container.addEventListener('mouseenter', () => clearInterval(interval));
  container.addEventListener('mouseleave', () => startAutoRotation(container));
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