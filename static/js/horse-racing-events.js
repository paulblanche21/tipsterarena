export async function fetchEvents() {
  const url = '/api/horse-racing-fixtures/';  // Your Django endpoint
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    const events = (data.fixtures || []).map(event => ({
      name: event.venue,  // Use venue as the meeting name
      date: event.date,
      displayDate: event.displayDate,
      time: "TBC",  // No time in your scraper yet; adjust if added later
      venue: event.venue,
      league: "Horse Racing",
      icon: "🏇"
    }));
    return events;
  } catch (error) {
    console.error('Error fetching horse racing fixtures:', error);
    return [];
  }
}

export function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  
  const today = new Date().toISOString().split('T')[0];  // YYYY-MM-DD
  const todayEvents = events.filter(event => event.date === today);
  const eventItems = todayEvents
    .slice(0, 5)  // Limit to 5 for sidebar
    .map(event => `
      <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
        <span>${event.name} - ${event.displayDate}</span>
        ${showLocation ? `<span class="event-location">${event.venue}</span>` : ""}
      </p>
    `)
    .join("");

  return todayEvents.length
    ? `<div class="league-group"><p class="league-header"><span class="sport-icon">🏇</span> <strong>Horse Racing</strong></p>${eventItems}</div>`
    : `<p>No ${sportKey} meetings today.</p>`;
}