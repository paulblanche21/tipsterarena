// horse-racing-events.js

async function fetchMeetingList() {
  const url = '/horse-racing/meetings/';  // Endpoint for simple meeting list (sidebar)
  try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.text();  // Expecting HTML
      return data;
  } catch (error) {
      console.error('Error fetching horse racing meeting list:', error);
      return '';
  }
}

async function fetchEvents() {
  const url = '/horse-racing/cards/';  // Endpoint for detailed racecards (center feed and carousel)
  try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.text();  // Expecting HTML
      return data;
  } catch (error) {
      console.error('Error fetching horse racing fixtures:', error);
      return '';
  }
}

async function formatEventList(events, sportKey, showLocation = false) {
  // Used for center feed and carousel (detailed racecards)
  if (!events) {
      return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  return events;  // The events are already HTML from fetchEvents (get_racecards)
}

async function formatMeetingList(events, sportKey) {
  // Used for sidebar (simple list of meetings)
  if (!events) {
      return `<p>No upcoming ${sportKey} meetings available.</p>`;
  }
  return events;  // The events are already HTML from fetchMeetingList (get_meeting_list)
}

export { fetchMeetingList, fetchEvents, formatEventList, formatMeetingList };