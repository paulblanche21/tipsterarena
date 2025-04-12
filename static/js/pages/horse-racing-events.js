async function fetchRaceData() {
  const url = 'http://localhost:8000/horse-racing/cards-json/';
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP error! status: ${response.status}, body: ${text}`);
    }
    const data = await response.json();
    const meetings = data.meetings || [];
    console.log('Fetched horse racing meetings:', meetings);
    return meetings;
  } catch (error) {
    console.error('Error fetching horse racing data:', error);
    return [];
  }
}

export async function fetchEvents() {
  return fetchRaceData();
}

export async function fetchMeetingList() {
  return fetchRaceData();
}

export async function formatEventList(events, sportKey, category, isCentralFeed = false) {
  if (!events || !events.length) {
    return `<p>No ${category.replace('_', ' ')} available.</p>`;
  }

  const currentTime = new Date();
  let filteredEvents = [];

  if (category === 'upcoming_meetings') {
    filteredEvents = events.filter(meeting => new Date(meeting.date) > currentTime);
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

  if (!filteredEvents.length) {
    return `<p>No ${category.replace('_', ' ')} available.</p>`;
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
                ${race.result.placed_horses && race.result.placed_horses.length ? '<ul>' + race.result.placed_horses.map(h => `<li>${h.position || 'N/A'}nd: ${h.name || 'Unknown'}</li>`).join('') + '</ul>' : ''}
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
        <p class="event-item horse_racing-event">
          <span>${meeting.venue} - ${new Date(meeting.date).toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short' })}</span>
        </p>
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