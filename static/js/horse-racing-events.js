// horse-racing-events.js
export async function fetchEvents(data, config) {
  const url = config.url || 'https://www.attheraces.com/ajax/fast-results/lhs'; // Default to today’s results
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    const events = (data || []).map(event => ({
      name: event.meeting_name || event.venue || "Unknown Meeting",
      date: event.date || new Date().toISOString(), // Fallback to today if no date
      displayDate: new Date(event.date || Date.now()).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      time: event.time || "TBC",
      state: event.results ? "completed" : "upcoming",
      venue: event.venue || "Location TBD",
      league: config.name || "Horse Racing",
      icon: config.icon || "🏇"
    }));
    return events;
  } catch (error) {
    console.error(`Error fetching ${config.name}:`, error);
    return [];
  }
}

export function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  const currentTime = new Date();
  const upcomingEvents = events.filter(event => new Date(event.date) >= currentTime);
  if (!upcomingEvents.length) {
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }

  const eventItems = upcomingEvents
    .slice(0, 5) // Limit to 5 for sidebar
    .map(event => `
      <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
        <span>${event.name} - ${event.displayDate} ${event.time}</span>
        ${showLocation ? `<span class="event-location">${event.venue}</span>` : ""}
      </p>
    `)
    .join("");

  return `<div class="league-group"><p class="league-header"><span class="sport-icon">🏇</span> <strong>Horse Racing</strong></p>${eventItems}</div>`;
}