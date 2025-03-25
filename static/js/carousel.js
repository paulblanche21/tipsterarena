// carousel.js


import { getDynamicEvents, formatFootballList, formatGolfList, formatTennisList, formatHorseRacingList } from './upcoming-events.js';

const FORMATTERS = {
  football: formatFootballList,
  golf: formatGolfList,
  tennis: formatTennisList,
  horse_racing: formatHorseRacingList
};

export async function initCarousel() {
  const carouselContainers = document.querySelectorAll('.carousel-container');
  
  for (const container of carouselContainers) {
    const slides = container.querySelectorAll('.carousel-slide');
    if (slides.length > 0) {
      await populateCarousel(container);
      setupDotNavigation(container);
      startAutoRotation(container);
    } else {
      console.warn("No slides found in carousel container:", container);
    }
  }
}

async function populateCarousel(container) {
  const dynamicEvents = await getDynamicEvents();
  const slides = container.querySelectorAll('.carousel-slide');
  for (const slide of slides) {
    const sport = slide.getAttribute('data-sport');
    if (sport && FORMATTERS[sport]) {
      const eventList = slide.querySelector('.event-list');
      if (eventList) {
        const events = dynamicEvents[sport] || [];
        eventList.innerHTML = await FORMATTERS[sport](events, sport, false) || `<p>No upcoming ${sport} events available.</p>`;
      } else {
        console.warn(`Event list container not found for ${sport} in slide:`, slide);
      }
    } else {
      console.warn(`No formatter found for sport: ${sport} in slide:`, slide);
    }
  }
}

function setupDotNavigation(container) {
  // Adjust query to find dots outside the container, as siblings
  const dotsContainer = container.parentElement.querySelector('.carousel-dots');
  const dots = dotsContainer ? dotsContainer.querySelectorAll('.dot') : [];
  const slides = container.querySelectorAll('.carousel-slide');

  if (slides.length <= 1) {
    return;
  }

  if (dots.length !== slides.length) {
    console.warn(`Mismatch detected: ${slides.length} slides vs ${dots.length} dots`);
    console.log("Slides:", Array.from(slides).map(s => s.getAttribute('data-sport')));
    console.log("Dots:", Array.from(dots).map(d => d.getAttribute('data-sport')));
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

  let interval;
  const rotate = () => {
    currentSlide = (currentSlide < slides.length - 1) ? currentSlide + 1 : 0;
    showSlide(container, currentSlide);
  };
  
  interval = setInterval(rotate, 5000);

  container.removeEventListener('mouseenter', clearIntervalHandler);
  container.removeEventListener('mouseleave', restartRotationHandler);
  
  function clearIntervalHandler() { clearInterval(interval); }
  function restartRotationHandler() { interval = setInterval(rotate, 5000); }
  
  container.addEventListener('mouseenter', clearIntervalHandler);
  container.addEventListener('mouseleave', restartRotationHandler);
}

function showSlide(container, index) {
  const slides = container.querySelectorAll('.carousel-slide');
  const dotsContainer = container.parentElement.querySelector('.carousel-dots');
  const dots = dotsContainer ? dotsContainer.querySelectorAll('.dot') : [];

  
  slides.forEach((slide, i) => {
    slide.classList.toggle('active', i === index);
  });

  dots.forEach((dot, i) => {
    dot.classList.toggle('active', i === index);
  });
}