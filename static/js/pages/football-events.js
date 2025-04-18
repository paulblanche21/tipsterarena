// football-events.js

export async function fetchEvents(data, config) {
  const events = (data.events || []).map(event => {
    const competitions = event.competitions && event.competitions[0] ? event.competitions[0] : {};
    const competitors = competitions.competitors || [];
    const home = competitors.find(c => c?.homeAway?.toLowerCase() === "home") || competitors[0] || {};
    const away = competitors.find(c => c?.homeAway?.toLowerCase() === "away") || competitors[1] || {};

    console.log(`Parsing event: ${event.shortName || event.name}, State: ${event.status?.type?.state}, Home Score: ${home.score}, Away Score: ${away.score}`);

    const getTeamStats = (team) => {
      const stats = team.statistics || [];
      return {
        possession: stats.find(s => s.name === "possessionPct")?.displayValue || "N/A",
        shots: stats.find(s => s.name === "totalShots")?.displayValue || "N/A",
        shotsOnTarget: stats.find(s => s.name === "shotsOnTarget")?.displayValue || "N/A",
        corners: stats.find(s => s.name === "wonCorners")?.displayValue || "N/A",
        fouls: stats.find(s => s.name === "foulsCommitted")?.displayValue || "N/A",
      };
    };

    const details = competitions.details || [];
    const keyEvents = details.map(detail => ({
      type: detail.type.text || "Unknown",
      time: detail.clock?.displayValue || "N/A",
      team: detail.team?.displayName || "Unknown",
      player: detail.athletesInvolved?.[0]?.displayName || "Unknown",
      isGoal: detail.scoringPlay,
      isYellowCard: detail.yellowCard,
      isRedCard: detail.redCard,
    }));

    return {
      id: event.id,
      name: event.shortName || event.name,
      date: event.date,
      displayDate: new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      time: new Date(event.date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "GMT" }),
      state: event.status && event.status.type ? event.status.type.state : "unknown",
      statusDescription: event.status?.type?.description || "Unknown",
      statusDetail: event.status?.type?.detail || "N/A",
      competitors: competitors,
      venue: competitions.venue || { fullName: "Location TBD", address: { city: "Unknown", state: "Unknown" } },
      league: config.name,
      icon: config.icon,
      priority: config.priority || 999,
      homeTeam: {
        name: home.team?.displayName || "TBD",
        logo: home.team?.logo || "",
        score: home.score || "0",
        form: home.form || "N/A",
        record: home.records?.[0]?.summary || "N/A",
        stats: getTeamStats(home),
      },
      awayTeam: {
        name: away.team?.displayName || "TBD",
        logo: away.team?.logo || "",
        score: away.score || "0",
        form: away.form || "N/A",
        record: away.records?.[0]?.summary || "N/A",
        stats: getTeamStats(away),
      },
      keyEvents: keyEvents,
      scores: event.status.type.state === "in" ? {
        homeScore: home.score || "0",
        awayScore: away.score || "0",
        clock: event.status.type.clock || "0:00",
        period: event.status.type.period || 0,
        statusDetail: event.status.type.detail || "In Progress"
      } : event.status.type.state === "post" ? {
        homeScore: home.score || "0",
        awayScore: away.score || "0",
        statusDetail: event.status.type.detail || "Final"
      } : null,
      broadcast: competitions.geoBroadcasts?.[0]?.media?.shortName || "N/A",
    };
  });

  const detailedEvents = await Promise.all(events.map(async event => {
    try {
      const response = await fetch(`https://site.api.espn.com/apis/site/v2/sports/soccer/${config.league}/summary?event=${event.id}`);
      if (!response.ok) throw new Error(`Failed to fetch summary for event ${event.id}`);
      const summaryData = await response.json();

      const plays = summaryData.plays || [];
      const keyEventsFallback = plays.filter(play => play.type.text.toLowerCase().includes("goal") || play.yellowCard || play.redCard).map(play => ({
        type: play.type.text || "Unknown",
        time: play.clock?.displayValue || "N/A",
        team: play.team?.displayName || "Unknown",
        player: play.participants?.[0]?.athlete?.displayName || "Unknown",
        isGoal: play.type.text.toLowerCase().includes("goal"),
        isYellowCard: play.yellowCard,
        isRedCard: play.redCard,
      }));

      const keyEvents = event.keyEvents.length ? event.keyEvents : keyEventsFallback;
      console.log(`Event ${event.name}: Using ${keyEvents.length} key events (${event.keyEvents.length} from details, ${keyEventsFallback.length} from plays)`);

      const goals = plays.filter(play => play.type.text.toLowerCase().includes("goal")).map(event => ({
        scorer: event.participants?.[0]?.athlete?.displayName || event.scorer || "Unknown",
        team: event.team?.displayName || event.team || "Unknown",
        time: event.clock?.displayValue || event.time || "N/A",
        assist: event.participants?.[1]?.athlete?.displayName || event.assist || "Unassisted",
      }));

      const oddsData = summaryData.header?.competitions?.[0]?.odds?.[0] || {};
      const odds = {
        homeOdds: oddsData.homeTeamOdds?.moneyLine || "N/A",
        awayOdds: oddsData.awayTeamOdds?.moneyLine || "N/A",
        drawOdds: oddsData.drawOdds?.moneyLine || "N/A",
        provider: oddsData.provider?.name || "Unknown Provider",
      };

      const detailedStats = {
        goals: goals,
        possession: summaryData.header?.competitions?.[0]?.possession?.text || event.homeTeam.stats.possession + " - " + event.awayTeam.stats.possession,
        shots: {
          home: summaryData.boxscore?.teams?.[0]?.statistics?.find(stat => stat.name === "shots")?.displayValue || event.homeTeam.stats.shots,
          away: summaryData.boxscore?.teams?.[1]?.statistics?.find(stat => stat.name === "shots")?.displayValue || event.awayTeam.stats.shots,
        },
      };

      return {
        ...event,
        keyEvents,
        odds,
        detailedStats,
      };
    } catch (error) {
      console.error(`Error fetching detailed stats for ${event.name}:`, error);
      return event;
    }
  }));

  return detailedEvents;
}

export function formatEventList(events, sportKey, showLocation = false) {
  if (!events || !events.length) {
    console.log(`No events to format for ${sportKey} event list`);
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }
  const currentTime = new Date();
  const sevenDaysFuture = new Date();
  sevenDaysFuture.setDate(currentTime.getDate() + 7);

  const upcomingEvents = events
    .filter(event => {
      const eventDate = new Date(event.date);
      return (eventDate > currentTime && eventDate <= sevenDaysFuture) || event.state === "in";
    })
    .sort((a, b) => {
      if (a.state === "in" && b.state !== "in") return -1;
      if (a.state !== "in" && b.state === "in") return 1;
      if (a.priority !== b.priority) return a.priority - b.priority;
      return new Date(a.date) - new Date(b.date);
    });

  if (!upcomingEvents.length) {
    console.log(`No upcoming events after filtering for ${sportKey}`);
    return `<p>No upcoming ${sportKey} fixtures available.</p>`;
  }

  let eventItems = '';
  const eventsByLeague = upcomingEvents.reduce((acc, event) => {
    const league = event.league || "Other";
    if (!acc[league]) acc[league] = [];
    acc[league].push(event);
    return acc;
  }, {});

  let totalEvents = 0;
  for (const league in eventsByLeague) {
    if (totalEvents >= 4) break;
    const leagueEvents = eventsByLeague[league];
    const eventsToShow = leagueEvents.slice(0, 4 - totalEvents);
    const icon = leagueEvents[0].icon || "⚽";

    const leagueItems = eventsToShow.map((event, index) => {
      const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
      const eventId = event.id || `${league}-${index}`;

      let displayText = event.state === "in" && event.scores ?
        `<span class="live-score" style="color: #e63946; font-weight: bold;">${event.scores.homeScore} - ${event.scores.awayScore} (${event.scores.statusDetail})</span>` :
        event.state === "post" ? `${event.homeTeam.score} - ${event.awayTeam.score} (${event.statusDetail})` :
        `${event.displayDate} ${event.time}`;

      return `
        <div class="carousel-event-card expandable-card ${event.state === "in" ? 'live-match' : ''}" data-event-id="${eventId}">
          <div class="card-header" style="display: flex; justify-content: ${showLocation ? 'space-between' : 'flex-start'}; align-items: center; cursor: pointer;">
            <span>
              ${event.homeTeam.logo ? `<img src="${event.homeTeam.logo}" alt="${event.homeTeam.name} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${event.homeTeam.name} vs 
              ${event.awayTeam.logo ? `<img src="${event.awayTeam.logo}" alt="${event.awayTeam.name} Crest" class="team-crest" style="width: 20px; height: 20px; margin-right: 5px;">` : ""}
              ${event.awayTeam.name} - ${displayText}
            </span>
            ${showLocation ? `<span class="event-location">${venue}</span>` : ""}
          </div>
          <div class="match-details" style="display: none;" data-state="${event.state}" data-home-team="${event.homeTeam.name}" data-away-team="${event.awayTeam.name}">
            <p>Loading details...</p>
          </div>
        </div>
      `;
    }).join("");

    eventItems += `<div class="league-group"><p class="league-header"><span class="sport-icon">${icon}</span> <strong>${league}</strong></p>${leagueItems}</div>`;
    totalEvents += eventsToShow.length;
  }

  return eventItems || `<p>No upcoming ${sportKey} fixtures available.</p>`;
}

export function formatFootballTable(events) {
  if (!events || !events.length) {
    console.log("No events to format for football table");
    return `<p class="no-events">No football results available.</p>`;
  }

  console.log(`Formatting ${events.length} events for football table`);

  const sortedEvents = events.sort((a, b) => {
    if (a.priority !== b.priority) return a.priority - b.priority;
    return new Date(b.date) - new Date(a.date); // Newest first
  });

  const eventsByLeague = sortedEvents.reduce((acc, event) => {
    const league = event.league || "Other";
    if (!acc[league]) acc[league] = [];
    acc[league].push(event);
    return acc;
  }, {});

  let eventHtml = '<div class="event-feed">';

  for (const league in eventsByLeague) {
    const leagueEvents = eventsByLeague[league];

    eventHtml += `
      <div class="league-group">
        <p class="league-header"><span class="sport-icon">⚽</span> ${league}</p>
      </div>
    `;

    leagueEvents.forEach((event, index) => {
      const venue = event.venue.fullName || `${event.venue.address.city}, ${event.venue.address.state}`;
      const eventId = event.id || `${league}-${index}`;
      const timeOrScore = event.state === "in" && event.scores ?
        `<span class="live-score">${event.scores.homeScore} vs ${event.scores.awayScore}</span>` :
        event.state === "post" ?
        `<span class="final-score">${event.homeTeam.score} vs ${event.awayTeam.score} (${event.statusDetail})</span>` :
        `${event.displayDate} ${event.time}`;

      eventHtml += `
        <div class="event-card expandable-card ${event.state === "in" ? 'live-match' : ''}" data-event-id="${eventId}">
          <div class="card-header" style="cursor: pointer;">
            <div class="match-info">
              <div class="teams">
                ${event.homeTeam.logo ? `<img src="${event.homeTeam.logo}" alt="${event.homeTeam.name} Crest" class="team-crest">` : ""}
                <span class="team-name">${event.homeTeam.name}</span>
                <span class="score">${timeOrScore}</span>
                ${event.awayTeam.logo ? `<img src="${event.awayTeam.logo}" alt="${event.awayTeam.name} Crest" class="team-crest">` : ""}
                <span class="team-name">${event.awayTeam.name}</span>
              </div>
            </div>
            <div class="match-meta">
              <span class="datetime">${event.state === "in" || event.state === "post" ? event.statusDetail : `${event.displayDate} ${event.time}`}</span>
              <span class="location">${venue}</span>
            </div>
          </div>
          <div class="match-details" style="display: none;" data-state="${event.state}" data-home-team="${event.homeTeam.name}" data-away-team="${event.awayTeam.name}">
            <p>Loading details...</p>
          </div>
        </div>
      `;
    });
  }

  eventHtml += '</div>';
  return eventHtml || `<p class="no-events">No football results available.</p>`;
}

export async function fetchMatchDetails(eventId, detailsElement) {
  try {
    const response = await fetch(`/api/football/fixtures/${eventId}/`);
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    const summaryData = await response.json();

    const plays = summaryData.plays || [];
    const keyEvents = plays.filter(play => play.type.text.toLowerCase().includes("goal") || play.yellowCard || play.redCard).map(play => ({
      type: play.type.text || "Unknown",
      time: play.clock?.displayValue || "N/A",
      team: play.team?.displayName || "Unknown",
      player: play.participants?.[0]?.athlete?.displayName || "Unknown",
      isGoal: play.type.text.toLowerCase().includes("goal"),
      isYellowCard: play.yellowCard,
      isRedCard: play.redCard,
    }));

    const goals = plays.filter(play => play.type.text.toLowerCase().includes("goal")).map(event => ({
      scorer: event.participants?.[0]?.athlete?.displayName || "Unknown",
      team: event.team?.displayName || "Unknown",
      time: event.clock?.displayValue || "N/A",
      assist: event.participants?.[1]?.athlete?.displayName || "Unassisted",
    }));

    const oddsData = summaryData.header?.competitions?.[0]?.odds?.[0] || {};
    const odds = {
      homeOdds: oddsData.homeTeamOdds?.moneyLine || "N/A",
      awayOdds: oddsData.awayTeamOdds?.moneyLine || "N/A",
      drawOdds: oddsData.drawOdds?.moneyLine || "N/A",
      provider: oddsData.provider?.name || "Unknown Provider",
    };

    const detailedStats = {
      goals: goals,
      possession: summaryData.header?.competitions?.[0]?.possession?.text || "N/A",
      shots: {
        home: summaryData.boxscore?.teams?.[0]?.statistics?.find(stat => stat.name === "shots")?.displayValue || "N/A",
        away: summaryData.boxscore?.teams?.[1]?.statistics?.find(stat => stat.name === "shots")?.displayValue || "N/A",
      },
    };

    let detailsContent = '';
    const event = { state: detailsElement.dataset.state, homeTeam: { name: detailsElement.dataset.homeTeam }, awayTeam: { name: detailsElement.dataset.awayTeam } };
    if (event.state === "in" && detailedStats) {
      const goalsList = detailedStats.goals.length ?
        `<ul class="goal-list">${detailedStats.goals.map(goal => `<li>${goal.scorer} (${goal.team}) - ${goal.time}${goal.assist && goal.assist !== "Unassisted" ? `, Assist: ${goal.assist}` : ""}</li>`).join("")}</ul>` :
        "<span class='no-goals'>No goals</span>";

      detailsContent = `
        <div class="match-stats">
          <div class="game-stats">
            <p>Possession: ${detailedStats.possession}</p>
            <p>Shots: ${detailedStats.shots.home} - ${detailedStats.shots.away}</p>
          </div>
          <div class="key-events">
            ${goalsList}
          </div>
          <div class="betting-odds">
            <p><strong>Betting Odds (${odds.provider}):</strong></p>
            <p>${event.homeTeam.name}: ${odds.homeOdds}</p>
            <p>${event.awayTeam.name}: ${odds.awayOdds}</p>
            <p>Draw: ${odds.drawOdds}</p>
          </div>
        </div>
      `;
    } else if (event.state === "post") {
      const goalsList = keyEvents.filter(e => e.isGoal).length ?
        `<ul class="goal-list">${keyEvents.filter(e => e.isGoal).map(goal => `<li>${goal.player} (${goal.team}) - ${goal.time}</li>`).join("")}</ul>` :
        "<span class='no-goals'>No goals</span>";

      const cardsList = keyEvents.filter(e => e.isYellowCard || e.isRedCard).length ?
        `<ul class="card-list">${keyEvents.filter(e => e.isYellowCard || e.isRedCard).map(card => `<li class="${card.isRedCard ? 'red-card' : 'yellow-card'}">${card.player} (${card.team}) - ${card.time} (${card.type})</li>`).join("")}</ul>` :
        "<span class='no-cards'>No cards</span>";

      detailsContent = `
        <div class="match-stats">
          <div class="game-stats">
            <p>Possession: ${detailedStats.possession}</p>
            <p>Shots: ${detailedStats.shots.home} - ${detailedStats.shots.away}</p>
          </div>
          <div class="key-events">
            <p><strong>Goals:</strong></p>
            ${goalsList}
            <p><strong>Cards:</strong></p>
            ${cardsList}
          </div>
          <div class="betting-odds">
            <p><strong>Betting Odds (${odds.provider}):</strong></p>
            <p>${event.homeTeam.name}: ${odds.homeOdds}</p>
            <p>${event.awayTeam.name}: ${odds.awayOdds}</p>
            <p>Draw: ${odds.drawOdds}</p>
          </div>
        </div>
      `;
    }

    detailsElement.innerHTML = detailsContent;
  } catch (error) {
    console.error(`Error fetching details for event ${eventId}:`, error);
    detailsElement.innerHTML = '<p>Error loading match details.</p>';
  }
}