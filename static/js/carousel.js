// carousel.js
import { getDynamicEvents } from './upcoming-events.js';
import { formatEventList as formatFootballList } from './football-events.js';
import { formatEventList as formatTennisList } from './tennis-events.js';
import { formatEventList as formatGolfList } from './golf-events.js';
import { formatEventList as formatHorseRacingList } from './horse-racing-events.js';

const SPORT_MODULES = {
  football: { format: formatFootballList },
  golf: { format: formatGolfList },
  tennis: { format: formatTennisList },
  horse_racing: { format: formatHorseRacingList }
};

async function populateCarousel() {
  if (document.querySelector(".carousel-container")) {
    console.log("Populating carousel");
    const events = await getDynamicEvents();
    console.log("All events for carousel:", events);
    const sports = ["football", "golf", "tennis", "horse_racing"];
    sports.forEach(sport => {
      const container = document.getElementById(`${sport.replace('_', '-')}-events`);
      if (container) {
        const filteredEvents = sport === "football"
          ? events[sport].filter(event => event.league === "Premier League")
          : events[sport];
        // Do not show location in the carousel
        const module = SPORT_MODULES[sport];
        const eventList = module.format(filteredEvents, sport, false);
        container.innerHTML = eventList;
        console.log(`${sport} carousel updated with:`, container.innerHTML);
      } else {
        console.error(`Container not found for ${sport}`);
      }
    });
  }
}

export function initCarousel() {
  console.log("Initializing carousel");
  if (document.querySelector(".carousel-container")) {
    populateCarousel().then(() => {
      const dots = document.querySelectorAll(".carousel-dots .dot");
      const slides = document.querySelectorAll(".carousel-slide");
      dots.forEach(dot => {
        dot.addEventListener("click", () => {
          dots.forEach(d => d.classList.remove("active"));
          slides.forEach(s => s.classList.remove("active"));
          dot.classList.add("active");
          const sport = dot.getAttribute("data-sport");
          document.querySelector(`.carousel-slide[data-sport="${sport}"]`).classList.add("active");
        });
      });
    }).catch(error => console.error("Carousel initialization failed:", error));
  } else {
    console.error("Carousel container not found");
  }
}