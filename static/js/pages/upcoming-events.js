export class UpcomingEvents {
    static sportUrls = {
        football: {
            fixtures: 'https://www.livescore.com/en/',
            inplay: 'https://www.livescore.com/en/',
            results: 'https://www.livescore.com/en/'
        },
        golf: {
            fixtures: 'https://www.pgatour.com/schedule',
            inplay: 'https://www.pgatour.com/leaderboard',
            results: 'https://www.pgatour.com/results'
        },
        tennis: {
            fixtures: 'https://www.skysports.com/tennis/scores-schedule',
            inplay: 'https://www.skysports.com/tennis/scores-schedule',
            results: 'https://www.skysports.com/tennis/scores-schedule'
        },
        horse_racing: {
            fixtures: 'https://www.racingpost.com/racecards',
            inplay: 'https://www.racingpost.com/results',
            results: 'https://www.racingpost.com/results'
        },
        american_football: {
            fixtures: 'https://www.nfl.com/schedules',
            inplay: 'https://www.nfl.com/scores',
            results: 'https://www.nfl.com/scores'
        },
        baseball: {
            fixtures: 'https://www.mlb.com/schedule',
            inplay: 'https://www.mlb.com/scores',
            results: 'https://www.mlb.com/scores'
        },
        basketball: {
            fixtures: 'https://www.nba.com/schedule',
            inplay: 'https://www.nba.com/scores',
            results: 'https://www.nba.com/scores'
        },
        boxing: {
            fixtures: 'https://www.boxingscene.com/schedule',
            inplay: 'https://www.boxingscene.com/live',
            results: 'https://www.boxingscene.com/results'
        },
        cricket: {
            fixtures: 'https://www.espncricinfo.com/cricket-schedule',
            inplay: 'https://www.espncricinfo.com/live-cricket-score',
            results: 'https://www.espncricinfo.com/cricket-match-results'
        },
        cycling: {
            fixtures: 'https://www.procyclingstats.com/races.php',
            inplay: 'https://www.procyclingstats.com/live',
            results: 'https://www.procyclingstats.com/results.php'
        },
        darts: {
            fixtures: 'https://www.pdc.tv/tournaments',
            inplay: 'https://www.pdc.tv/live-scores',
            results: 'https://www.pdc.tv/results'
        },
        gaelic_games: {
            fixtures: 'https://www.gaa.ie/fixtures-results',
            inplay: 'https://www.gaa.ie/fixtures-results',
            results: 'https://www.gaa.ie/fixtures-results'
        },
        greyhound_racing: {
            fixtures: 'https://www.gbgb.org.uk/racing/fixtures',
            inplay: 'https://www.gbgb.org.uk/racing/results',
            results: 'https://www.gbgb.org.uk/racing/results'
        },
        motor_sport: {
            fixtures: 'https://www.formula1.com/en/racing/2024.html',
            inplay: 'https://www.formula1.com/en/latest/all.html',
            results: 'https://www.formula1.com/en/results.html'
        },
        rugby_union: {
            fixtures: 'https://www.rugbypass.com/fixtures',
            inplay: 'https://www.rugbypass.com/live',
            results: 'https://www.rugbypass.com/results'
        },
        snooker: {
            fixtures: 'https://wst.tv/tournaments',
            inplay: 'https://wst.tv/live-scores',
            results: 'https://wst.tv/results'
        },
        volleyball: {
            fixtures: 'https://www.volleyballworld.com/volleyball/competitions',
            inplay: 'https://www.volleyballworld.com/volleyball/competitions/live',
            results: 'https://www.volleyballworld.com/volleyball/competitions/results'
        }
    };

    constructor() {
        this.sportSelector = document.querySelector('.sport-selector');
        this.eventButtons = document.querySelectorAll('.event-btn');
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setInitialState();
    }

    setupEventListeners() {
        this.eventButtons.forEach(button => {
            button.addEventListener('click', () => this.handleEventButtonClick(button));
        });

        if (this.sportSelector) {
            this.sportSelector.addEventListener('change', () => {
                // Reset to fixtures view when sport changes
                const fixturesButton = document.querySelector('.event-btn[data-category="fixtures"]');
                if (fixturesButton) {
                    this.handleEventButtonClick(fixturesButton);
                }
            });
        }
    }

    handleEventButtonClick(clickedButton) {
        // Remove active class from all buttons
        this.eventButtons.forEach(btn => btn.classList.remove('active'));
        
        // Add active class to clicked button
        clickedButton.classList.add('active');
        
        const selectedSport = this.sportSelector.value;
        const category = clickedButton.dataset.category;
        const url = UpcomingEvents.sportUrls[selectedSport][category];
        
        if (url) {
            window.open(url, '_blank');
        }
    }

    setInitialState() {
        const defaultButton = document.querySelector('.event-btn[data-category="fixtures"]');
        if (defaultButton) {
            defaultButton.classList.add('active');
        }
    }
}

// Initialize if the element exists and we're not in a module context
if (typeof import.meta === 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        const upcomingEventsCard = document.querySelector('.upcoming-events-card');
        if (upcomingEventsCard) {
            new UpcomingEvents();
        }
    });
} 