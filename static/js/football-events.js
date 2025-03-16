// football-events.js
export async function fetchEvents(data, config) {
    const events = (data.events || []).map(event => ({
      name: event.shortName || event.name,
      date: event.date,
      displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      time: new Date(event.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
      state: event.status && event.status.type ? event.status.type.state : "unknown",
      competitors: (event.competitions && event.competitions[0]?.competitors) || [],
      venue: (event.competitions && event.competitions[0]?.venue) || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } },
      league: config.name,
      icon: config.icon
    }));
    return events;
  }
  
  export function formatEventList(events, sportKey, showLocation = false) {
    if (!events || !events.length) {
      return `<p>No upcoming ${sportKey} fixtures available.</p>`;
    }
    const currentTime = new Date();
    const upcomingEvents = events.filter(event => {
      const eventTime = new Date(event.date);
      // Always filter for upcoming events, regardless of sportKey
      const isUpcoming = eventTime > currentTime;
      console.log(`Event for ${event.league} (${event.name}): ${event.displayDate}, ${event.time} - State: ${event.state}, Is Upcoming: ${isUpcoming}`);
      return isUpcoming;
    });
    if (!upcomingEvents.length) {
      return `<p>No upcoming ${sportKey} fixtures available.</p>`;
    }
    console.log(`Upcoming ${sportKey} events before grouping:`, upcomingEvents);
  
    const eventsByLeague = upcomingEvents.reduce((acc, event) => {
      const league = event.league || "Other";
      if (!acc[league]) {
        acc[league] = [];
      }
      acc[league].push(event);
      return acc;
    }, {});
    console.log(`Events grouped by league for ${sportKey}:`, eventsByLeague);
  
    let eventItems = '';
    for (const league in eventsByLeague) {
      const leagueEvents = eventsByLeague[league]
        .slice(0, sportKey === "all" ? 20 : 5) // Limit to 5 for carousel, 20 for "Show More"
        .map(event => {
          const competitors = event.competitors || [];
          console.log(`Competitors for ${event.name}:`, competitors); // Debug competitors
          const home = competitors.find(c => c?.homeAway?.toLowerCase() === "home") || competitors[0];
          const away = competitors.find(c => c?.homeAway?.toLowerCase() === "away") || competitors[1];
          const homeTeam = home?.team || { displayName: "TBD" };
          const awayTeam = away?.team || { displayName: "TBD" };
          const homeCrest = homeTeam.logos?.[0]?.href || "";
          const awayCrest = awayTeam.logos?.[0]?.href || "";
          const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
          return `
            <p class="event-item" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center;">
              <span>
                ${homeCrest ? `<img src="${homeCrest}" alt="${homeTeam.displayName} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
                ${homeTeam.displayName} vs 
                ${awayCrest ? `<img src="${awayCrest}" alt="${awayTeam.displayName} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
                ${awayTeam.displayName} - ${event.displayDate} ${event.time}
              </span>
              ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
            </p>
          `;
        })
        .join("");
      const icon = upcomingEvents.find(event => event.league === league)?.icon || "🏟️";
      eventItems += `<div class="league-group"><p class="league-header"><span class="sport-icon">${icon}</span> <strong>${league}</strong></p>${leagueEvents}</div>`;
    }
    console.log(`Formatted ${sportKey} events:`, eventItems);
    return eventItems || `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }