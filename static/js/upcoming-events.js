// upcoming-events.js
const UPCOMING_EVENTS = {
    all: `
        <div class="event-list">
            <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Manchester United vs. Tottenham, Mar 12, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Real Madrid vs. Barcelona, Mar 15, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Champions League: Bayern Munich vs. PSG, Mar 16, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> FA Cup: Chelsea vs. Arsenal, Mar 17, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: Juventus vs. Inter Milan, Mar 18, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Bundesliga: Dortmund vs. Leipzig, Mar 19, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Europa League: Ajax vs. Roma, Mar 20, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Liverpool vs. Manchester City, Mar 21, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Atletico Madrid vs. Sevilla, Mar 22, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: AC Milan vs. Napoli, Mar 23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Arsenal vs. Chelsea, Mar 25, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Barcelona vs. Real Madrid, Mar 26, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Champions League: PSG vs. Bayern Munich, Mar 27, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> FA Cup: Tottenham vs. Manchester United, Mar 28, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: Inter Milan vs. Juventus, Mar 29, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Bundesliga: Leipzig vs. Dortmund, Mar 30, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Europa League: Roma vs. Ajax, Mar 31, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Manchester City vs. Liverpool, Apr 1, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Sevilla vs. Atletico Madrid, Apr 2, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: Napoli vs. AC Milan, Apr 3, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: The Players Championship, Mar 13-16, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: Valspar Championship, Mar 20-23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: WGC-Dell Technologies Match Play, Mar 26-30, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: Houston Open, Apr 3-6, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: Masters Tournament, Apr 10-13, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Magical Kenya Open, Mar 13-16, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Qatar Masters, Mar 20-23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Hero Indian Open, Mar 27-30, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Volvo China Open, Apr 3-6, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Open de Espana, Apr 10-13, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> Tennis: Australian Open Qualifiers, Mar 10-12, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> Tennis: Wimbledon Warm-Up, Mar 18, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> Tennis: French Open Trials, Mar 20, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> Tennis: US Open Prep, Mar 21, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> Tennis: ATP Finals Qualifier, Mar 22, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Horse Racing: Grand National Trials, Mar 14, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Horse Racing: Cheltenham Festival, Mar 19, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Horse Racing: Kentucky Derby Prep, Mar 21, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Horse Racing: Preakness Stakes Warm-Up, Mar 22, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Horse Racing: Belmont Stakes Trials, Mar 23, 2025</p></div>
        </div>
    `,
    football: `
        <div class="event-list">
            <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Manchester United vs. Tottenham, Mar 12, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Real Madrid vs. Barcelona, Mar 15, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Champions League: Bayern Munich vs. PSG, Mar 16, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> FA Cup: Chelsea vs. Arsenal, Mar 17, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: Juventus vs. Inter Milan, Mar 18, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Bundesliga: Dortmund vs. Leipzig, Mar 19, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Europa League: Ajax vs. Roma, Mar 20, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Liverpool vs. Manchester City, Mar 21, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Atletico Madrid vs. Sevilla, Mar 22, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: AC Milan vs. Napoli, Mar 23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Arsenal vs. Chelsea, Mar 25, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Barcelona vs. Real Madrid, Mar 26, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Champions League: PSG vs. Bayern Munich, Mar 27, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> FA Cup: Tottenham vs. Manchester United, Mar 28, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: Inter Milan vs. Juventus, Mar 29, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Bundesliga: Leipzig vs. Dortmund, Mar 30, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Europa League: Roma vs. Ajax, Mar 31, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Manchester City vs. Liverpool, Apr 1, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Sevilla vs. Atletico Madrid, Apr 2, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: Napoli vs. AC Milan, Apr 3, 2025</p></div>
        </div>
    `,
    golf: `
        <div class="event-list">
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: The Players Championship, Mar 13-16, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: Valspar Championship, Mar 20-23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: WGC-Dell Technologies Match Play, Mar 26-30, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: Houston Open, Apr 3-6, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: Masters Tournament, Apr 10-13, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Magical Kenya Open, Mar 13-16, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Qatar Masters, Mar 20-23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Hero Indian Open, Mar 27-30, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Volvo China Open, Apr 3-6, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Open de Espana, Apr 10-13, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Jeddah, Mar 14-16, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Hong Kong, Mar 21-23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Tucson, Mar 28-30, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Miami, Apr 4-6, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Adelaide, Apr 11-13, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: Honda LPGA Thailand, Feb 20-23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: HSBC Women’s World Championship, Mar 6-9, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: Blue Bay LPGA, Mar 13-16, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: Kia Classic, Mar 20-23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: ANA Inspiration, Apr 3-6, 2025</p></div>
        </div>
    `,
    tennis: `
        <div class="event-list">
            <div class="event-item"><p><span class="sport-icon">🎾</span> Australian Open Qualifiers, Mar 10-12, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> Wimbledon Warm-Up, Mar 18, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> French Open Trials, Mar 20, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> US Open Prep, Mar 21, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> ATP Finals Qualifier, Mar 22, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> WTA Finals, Mar 23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> Australian Open, Jan 12-26, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> French Open Qualifiers, May 19-24, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> French Open, May 25-Jun 8, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> Wimbledon, Jun 30-Jul 13, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🎾</span> US Open, Aug 25-Sep 7, 2025</p></div>
        </div>
    `,
    horse_racing: `
        <div class="event-list">
            <div class="event-item"><p><span class="sport-icon">🏇</span> Grand National Trials, Mar 14, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Cheltenham Festival, Mar 19, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Kentucky Derby Prep, Mar 21, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Preakness Stakes Warm-Up, Mar 22, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Belmont Stakes Trials, Mar 23, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Royal Ascot Preview, Mar 24, 2025</p></div>
            <div class="event-item"><p><span class="sport-icon">🏇</span> Grand National, Apr 5, 2025</p></div>
        </div>
    `
};

function getEventList(currentPath, target) {
    const path = currentPath.toLowerCase();
    let eventList = '';
    let title = '';
    let description = '';

    if (target === 'upcoming-events') {
        if (path === '/' || path === '/home/') {
            title = 'Upcoming Events';
            description = 'Here are the latest upcoming events in Tipster Arena:';
            eventList = UPCOMING_EVENTS.all;
        } else if (path.includes('/sport/football/')) {
            title = 'Upcoming Football Fixtures';
            description = 'Here are the latest football fixtures in Tipster Arena:';
            eventList = UPCOMING_EVENTS.football;
        } else if (path.includes('/sport/golf/')) {
            title = 'Upcoming Golf Events';
            description = 'Here are the latest golf events in Tipster Arena:';
            eventList = UPCOMING_EVENTS.golf;
        } else if (path.includes('/sport/tennis/')) {
            title = 'Upcoming Tennis Events';
            description = 'Here are the latest tennis events in Tipster Arena:';
            eventList = UPCOMING_EVENTS.tennis;
        } else if (path.includes('/sport/horse_racing/')) {
            title = 'Upcoming Horse Racing Events';
            description = 'Here are the latest horse racing events in Tipster Arena:';
            eventList = UPCOMING_EVENTS.horse_racing;
        }
    }

    return `
        <div class="events-popup">
            <h2>${title}</h2>
            <p>${description}</p>
            ${eventList}
            <a href="#" class="show-less" data-target="${target}">Show less</a>
        </div>
    `;
}

// Export the function for use in other files (if using modules)
// If not using modules, this will be available globally
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getEventList };
}