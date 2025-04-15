async function fetchRaceData() {
  const url = 'http://localhost:8000/horse-racing/cards-json/';
  try {
    console.log('Fetching race data from:', url);
    document.dispatchEvent(new CustomEvent('raceDataLoading', { detail: true }));
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP error! status: ${response.status}, body: ${text}`);
    }
    const data = await response.json();
    console.log('Raw response data:', data);
    const meetings = Array.isArray(data) ? data : data.meetings || [];
    console.log('Parsed horse racing meetings:', meetings);
    return meetings;
  } catch (error) {
    console.error('Error fetching horse racing data:', error);
    return [];
  } finally {
    document.dispatchEvent(new CustomEvent('raceDataLoading', { detail: false }));
  }
}

export async function fetchEvents() {
  return fetchRaceData();
}

export async function fetchMeetingList() {
  return fetchRaceData();
}

export async function formatEventList(events, sportKey, category, isCentralFeed = false) {
  console.log(`Formatting events for category: ${category}, events:`, events);
  if (!events || !events.length) {
    return `<div class="error-message"><p>No ${category.replace('_', ' ')} available. Please check back later.</p></div>`;
  }

  const currentTime = new Date();
  let filteredEvents = [];

  if (category === 'upcoming_meetings') {
    // Include today and tomorrow for upcoming meetings
    filteredEvents = events.filter(meeting => {
      const meetingDate = new Date(meeting.date);
      const today = new Date(currentTime.setHours(0, 0, 0, 0));
      const tomorrow = new Date(today);
      tomorrow.setDate(today.getDate() + 1);
      const isTodayOrTomorrow = meetingDate >= today && meetingDate <= tomorrow;
      console.log(`Meeting ${meeting.venue} (${meeting.date}): isTodayOrTomorrow=${isTodayOrTomorrow}`);
      return isTodayOrTomorrow;
    });
  } else if (category === 'at_the_post') {
    filteredEvents = events
      .filter(meeting => new Date(meeting.date).toDateString() === currentTime.toDateString())
      .map(meeting => ({
        ...meeting,
        races: (meeting.races || []).filter(race => {
          const raceTime = new Date(`${meeting.date}T${race.race_time}`);
          const timeDiff = Math.abs(raceTime - currentTime) / (1000 * 60);
          return timeDiff <= 30;
        })
      }))
      .filter(meeting => meeting.races.length > 0);
  } else if (category === 'race_results') {
    filteredEvents = events
      .map(meeting => ({
        ...meeting,
        races: (meeting.races || []).filter(race => race.result && race.result.winner)
      }))
      .filter(meeting => meeting.races.length > 0);
  }

  console.log(`Filtered events for ${category}:`, filteredEvents);
  if (!filteredEvents.length) {
    return `<div class="info-message"><p>No ${category.replace('_', ' ')} found for the selected criteria.</p></div>`;
  }

  if (isCentralFeed) {
    let eventHtml = '<div class="racecard-feed">';
    for (const meeting of filteredEvents) {
      eventHtml += `
        <div class="meeting-card expandable-card">
          <div class="card-header">
            <div class="meeting-info">
              <span class="meeting-name">${meeting.venue} - ${new Date(meeting.date).toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })}</span>
            </div>
          </div>
          <div class="card-content" style="display: none;">
      `;
      for (const race of meeting.races || []) {
        const horsesList = race.horses && race.horses.length
          ? race.horses.map(h => `
              <li>${h.number || 'N/A'}. ${h.name || 'Unknown'} (Jockey: ${h.jockey || 'Unknown'}, Odds: ${h.odds || 'N/A'}, Trainer: ${h.trainer || 'Unknown'}, Owner: ${h.owner || 'Unknown'})</li>
            `).join('')
          : '<li>No horses available.</li>';
        const resultContent = race.result && race.result.winner
          ? `
              <div class="race-result">
                <p><strong>Winner:</strong> ${race.result.winner}</p>
                ${race.result.positions && race.result.positions.length ? '<ul>' + race.result.positions.map(h => `<li>${h.position || 'N/A'}nd: ${h.name || 'Unknown'}</li>`).join('') + '</ul>' : ''}
              </div>
            `
          : '';
        eventHtml += `
          <div class="race-details">
            <p><strong>Race Time:</strong> ${race.race_time || 'N/A'}</p>
            <p><strong>Race Name:</strong> ${race.name || 'Unnamed Race'}</p>
            <div class="horses-list">
              <p><strong>Horses:</strong></p>
              <ul>${horsesList}</ul>
            </div>
            ${resultContent}
          </div>
        `;
      }
      eventHtml += '</div></div>';
    }
    eventHtml += '</div>';
    return eventHtml;
  } else {
    let eventHtml = '<div class="league-group"><p class="league-header"><span class="sport-icon">🏇</span> <strong>UK & Irish Racing</strong></p>';
    if (category === 'upcoming_meetings') {
      eventHtml += filteredEvents.map(meeting => `
        <div class="event-item horse_racing-event expandable-card">
          <div class="card-header">
            <span>${meeting.venue} - ${new Date(meeting.date).toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short' })}</span>
          </div>
          <div class="card-content" style="display: none;">
            ${meeting.races && meeting.races.length > 0 ? meeting.races.map(race => `
              <div class="race-details">
                <p><strong>Race Time:</strong> ${race.race_time || 'N/A'}</p>
                <p><strong>Race Name:</strong> ${race.name || 'Unnamed Race'}</p>
                ${race.horses && race.horses.length > 0 ? `
                  <div class="horses-list">
                    <p><strong>Horses:</strong></p>
                    <ul>
                      ${race.horses.map(h => `
                        <li>${h.number || 'N/A'}. ${h.name || 'Unknown'} (Jockey: ${h.jockey || 'Unknown'}, Odds: ${h.odds || 'N/A'})</li>
                      `).join('')}
                    </ul>
                  </div>
                ` : '<p>No horses available.</p>'}
              </div>
            `).join('') : '<p>No races available for this meeting.</p>'}
          </div>
        </div>
      `).join('');
    } else {
      eventHtml += filteredEvents.flatMap(meeting => 
        (meeting.races || []).map(race => {
          const resultContent = category === 'race_results' && race.result
            ? `<p><strong>Winner:</strong> ${race.result.winner}</p>`
            : '';
          return `
            <div class="event-item horse_racing-event expandable-card">
              <div class="card-header">
                <span>${race.name || 'Unnamed Race'} - ${meeting.venue} - ${race.race_time || 'N/A'}</span>
              </div>
              <div class="card-content" style="display: none;">
                <p><strong>Time:</strong> ${race.race_time || 'N/A'}</p>
                ${resultContent}
              </div>
            </div>
          `;
        })
      ).join('');
    }
    eventHtml += '</div>';
    return eventHtml;
  }
}

export async function formatMeetingList(events, sportKey) {
  return formatEventList(events, sportKey, 'upcoming_meetings', false);
}