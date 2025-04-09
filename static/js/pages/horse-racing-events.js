// horse-racing-events.js
async function fetchEvents() {
  const url = '/horse-racing/cards-json/';  // JSON endpoint for center feed
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();  // Parse as JSON
    return data;  // Array of meeting objects
  } catch (error) {
    console.error('Error fetching horse racing fixtures:', error);
    return [];
  }
}

async function fetchMeetingList() {
  const url = '/horse-racing/cards-json/';  // Use same JSON endpoint for sidebar
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();  // Parse as JSON
    return data;  // Array of meeting objects
  } catch (error) {
    console.error('Error fetching horse racing meeting list:', error);
    return [];
  }
}

async function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  let event_html = '<div class="racecard-feed">';
  for (const meeting of events) {
    event_html += `
      <div class="meeting-card">
        <div class="card-header">
          <div class="meeting-info">
            <span class="meeting-name">${meeting.venue} - ${new Date(meeting.date).toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })}</span>
          </div>
        </div>
        <div class="card-content">
    `;
    for (const race of meeting.races) {
      const horses_list = race.horses.length
        ? race.horses.map(h => `
            <li>${h.number}. ${h.name} (Jockey: ${h.jockey || 'Unknown'}, Odds: ${h.odds || 'N/A'}, Trainer: ${h.trainer || 'Unknown'}, Owner: ${h.owner || 'Unknown'})</li>
          `).join('')
        : '<li>No horses available.</li>';
      const result_content = race.result && race.result.winner
        ? `
            <div class="race-result">
              <p><strong>Winner:</strong> ${race.result.winner}</p>
              ${race.result.placed_horses.length ? '<ul>' + race.result.placed_horses.map(h => `<li>${h.position}nd: ${h.name}</li>`).join('') + '</ul>' : ''}
            </div>
          `
        : '';
      event_html += `
        <div class="race-details">
          <p><strong>Race Time:</strong> ${race.race_time}</p>
          <p><strong>Race Name:</strong> ${race.name}</p>
          <div class="horses-list">
            <p><strong>Horses:</strong></p>
            <ul>${horses_list}</ul>
          </div>
          ${result_content}
        </div>
      `;
    }
    event_html += `
        </div>
      </div>
    `;
  }
  event_html += '</div>';
  return event_html;
}

async function formatMeetingList(events, sportKey) {
  if (!events || !events.length) {
    return `<p>No upcoming ${sportKey} meetings available.</p>`;
  }
  let meeting_html = '<ul class="meeting-list">';
  for (const meeting of events) {
    meeting_html += `
      <li>
        <span class="meeting-item">${meeting.venue} - ${new Date(meeting.date).toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short' })}</span>
      </li>
    `;
  }
  meeting_html += '</ul>';
  return meeting_html;
}

export { fetchMeetingList, fetchEvents, formatEventList, formatMeetingList };