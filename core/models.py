"""Core models for Tipster Arena.

Contains database models for user profiles, tips, and sports events.
"""

# models.py
from django.db import models
from django.contrib.auth.models import User

# Model representing a user's tip
class Tip(models.Model):
    """Represents a betting tip posted by a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Tip author
    sport = models.CharField(
        max_length=20,
        choices=[
            ('football', 'Football'),
            ('golf', 'Golf'),
            ('tennis', 'Tennis'),
            ('horse_racing', 'Horse Racing'),
        ]
    )  # Sport category for the tip
    text = models.TextField()  # Main content of the tip
    image = models.ImageField(upload_to='tips/', blank=True, null=True)  # Optional image attachment
    gif_url = models.URLField(blank=True, null=True)  # URL for an attached GIF
    gif_width = models.PositiveIntegerField(null=True, blank=True)  # GIF width for display
    gif_height = models.PositiveIntegerField(null=True, blank=True)  # GIF height for display
    poll = models.TextField(blank=True, null=True, default='{}')  # JSON string for poll data
    emojis = models.TextField(blank=True, null=True, default='{}')  # JSON string for emoji data
    bookmarks = models.ManyToManyField(User, related_name='bookmarked_tips', blank=True)  # Users who bookmarked this tip
    location = models.CharField(max_length=255, blank=True, null=True)  # Optional location tag
    scheduled_at = models.DateTimeField(blank=True, null=True)  # Optional scheduled posting time
    audience = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Everyone'),
            ('followers', 'Followers'),
        ],
        default='everyone'
    )  # Visibility setting
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of tip creation
    # Updated fields for tip details
    odds = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="The odds for the tip (e.g., '2.5' or '2/1')"
    )  # Store odds as a string (e.g., "2.5" or "2/1")
    odds_format = models.CharField(
        max_length=20,
        choices=[
            ('decimal', 'Decimal'),
            ('fractional', 'Fractional'),
        ],
        null=True,
        blank=True
    )  # Format of the odds
    bet_type = models.CharField(
        max_length=50,
        choices=[
            ('single', 'Single'),
            ('double', 'Double'),
            ('treble', 'Treble'),
            ('fourfold', 'Fourfold'),
            ('fivefold', 'Fivefold'),
            ('sixfold', 'Sixfold'),
            ('sevenfold', 'Sevenfold'),
            ('eightfold', 'Eightfold'),
            ('accumulator', 'Accumulator'),
            ('trixie', 'Trixie'),
            ('yankee', 'Yankee'),
            ('canadian', 'Canadian / Super Yankee'),
            ('patent', 'Patent'),
            ('lucky15', 'Lucky 15'),
            ('lucky31', 'Lucky 31'),
            ('lucky63', 'Lucky 63'),
            ('heinz', 'Heinz'),
            ('super_heinz', 'Super Heinz'),
            ('goliath', 'Goliath'),
            ('super_heinz_singles', 'Super Heinz with Singles'),
            ('super_goliath', 'Super Goliath'),
        ],
        null=True,
        blank=True
    )  # Type of bet
    each_way = models.CharField(
        max_length=3,
        choices=[
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        default='no'
    )  # Single condition: Each Way (Yes/No)
    
    confidence = models.PositiveSmallIntegerField(
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')],
        null=True,
        blank=True,
        help_text="Confidence level (1-5 stars, optional)"
    )

    
    # Updated fields for backend verification
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('win', 'Win'),
            ('loss', 'Loss'),
            ('dead_heat', 'Dead Heat'),
            ('void_non_runner', 'Void/Non Runner'),
        ],
        default='pending'
    )  # Updated status options
    resolution_note = models.TextField(blank=True, null=True)  # Optional note explaining the verification result
    verified_at = models.DateTimeField(blank=True, null=True)  # Timestamp of verification

    def __str__(self):
        return f"{self.user.username} - {self.sport}: {self.text[:20]}"  # String representation for admin/debugging


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    handle = models.CharField(max_length=15, unique=True, blank=True)
    allow_messages = models.CharField(max_length=20, choices=[
        ('no_one', 'No one'),
        ('followers', 'Followers'),
        ('everyone', 'Everyone'),
    ], default='everyone')
    win_rate = models.FloatField(default=0.0)
    total_tips = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    kyc_completed = models.BooleanField(default=False)
    payment_completed = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)
    full_name = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)  # New field

    @property
    def followers_count(self):
        return Follow.objects.filter(followed=self.user).count()

    def __str__(self):
        return f"{self.user.username}'s profile"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='likes', null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='likes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tip', 'comment')

    def __str__(self):
        if self.tip:
            return f"{self.user.username} liked {self.tip.user.username}'s tip"
        return f"{self.user.username} liked a comment"

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"

class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='shares', null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='shares', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tip', 'comment')

    def __str__(self):
        if self.tip:
            return f"{self.user.username} shared {self.tip.user.username}'s tip"
        return f"{self.user.username} shared a comment"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    image = models.ImageField(upload_to='comments/', blank=True, null=True)
    gif_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} commented on {self.tip.user.username}'s tip: {self.content[:20]}"

class MessageThread(models.Model):
    participants = models.ManyToManyField(User, related_name='message_threads')
    last_message = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Thread with {', '.join(p.username for p in self.participants.all()[:2])}"

    def get_other_participant(self, current_user):
        return self.participants.exclude(id=current_user.id).first()

    def update_last_message(self):
        latest_message = self.messages.order_by('-created_at').first()
        if latest_message:
            self.last_message = latest_message.content[:30]
            self.updated_at = latest_message.created_at
            self.save()

class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    gif_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.sender.username} in {self.thread}: {self.content[:20]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.thread.update_last_message()

class RaceMeeting(models.Model):
    date = models.DateField()
    venue = models.CharField(max_length=100)
    url = models.URLField(unique=True)

    def __str__(self):
        return f"{self.venue} - {self.date}"

    class Meta:
        unique_together = ('date', 'venue')

class Race(models.Model):
    meeting = models.ForeignKey(RaceMeeting, on_delete=models.CASCADE, related_name="races")
    race_time = models.TimeField()
    name = models.CharField(max_length=200, blank=True)
    horses = models.JSONField()  # Store list of horses as JSON: [{"number": 1, "name": "Horse 1"}, ...]

    def __str__(self):
        return f"{self.name} at {self.race_time} - {self.meeting.venue}"

    class Meta:
        unique_together = ('meeting', 'race_time')

class RaceResult(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="results", null=True)  # Temporarily nullable
    winner = models.CharField(max_length=100, blank=True)
    placed_horses = models.JSONField(blank=True, null=True)  # e.g., [{"position": 2, "name": "Horse 2"}, ...]

    def __str__(self):
        return f"Result for {self.race} - Winner: {self.winner}"
    
    

# Model for a football league
class FootballLeague(models.Model):
    league_id = models.CharField(max_length=50, unique=True)  # e.g., "eng.1", "esp.1"
    name = models.CharField(max_length=100)  # e.g., "Premier League"
    icon = models.CharField(max_length=10, default="⚽")  # Emoji icon
    priority = models.PositiveIntegerField(default=999)  # Sorting priority

    def __str__(self):
        return self.name

# Model for a football team
class FootballTeam(models.Model):
    name = models.CharField(max_length=100)  # Team name, e.g., "Manchester United"
    logo = models.URLField(blank=True, null=True)  # Team logo URL
    form = models.CharField(max_length=50, blank=True, null=True)  # Recent form, e.g., "W-L-D"
    record = models.CharField(max_length=50, blank=True, null=True)  # Season record, e.g., "10-5-3"

    def __str__(self):
        return self.name

# Model for team statistics in a match
class TeamStats(models.Model):
    possession = models.CharField(max_length=10, default='N/A')
    shots = models.CharField(max_length=10, default='N/A')
    shots_on_target = models.CharField(max_length=10, default='N/A')
    corners = models.CharField(max_length=10, default='N/A')
    fouls = models.CharField(max_length=10, default='N/A')

    def __str__(self):
        return f"Stats: {self.possession}% possession, {self.shots} shots"

# Model for a football event (match)
class FootballEvent(models.Model):
    event_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)  # Match name, e.g., "Man United vs Arsenal"
    date = models.DateTimeField()  # Match date and time
    state = models.CharField(
        max_length=20,
        choices=[
            ('pre', 'Pre'),
            ('in', 'In Progress'),
            ('post', 'Post'),
            ('unknown', 'Unknown'),
        ],
        default='pre'
    )  # Match status
    status_description = models.CharField(max_length=100, default="Unknown")  # e.g., "Scheduled", "In Progress"
    status_detail = models.CharField(max_length=100, default="N/A")  # e.g., "Half Time", "Final"
    league = models.ForeignKey(FootballLeague, on_delete=models.CASCADE, related_name='events', null=True)
    venue = models.CharField(max_length=200, default="Location TBD")  # Venue name
    home_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name='home_events', null=True)
    away_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name='away_events', null=True)
    home_score = models.IntegerField(default=0)
    away_score = models.IntegerField(default=0)
    home_team_stats = models.OneToOneField(TeamStats, on_delete=models.SET_NULL, null=True, related_name='home_team_event')
    away_team_stats = models.OneToOneField(TeamStats, on_delete=models.SET_NULL, null=True, related_name='away_team_event')
    clock = models.CharField(max_length=10, blank=True, null=True)  # Match clock, e.g., "45:00"
    period = models.PositiveIntegerField(default=0)  # Match period, e.g., 1 for first half
    broadcast = models.CharField(max_length=100, default="N/A")  # Broadcast info
    last_updated = models.DateTimeField(auto_now=True)  # Last time event was updated

    def __str__(self):
        return f"{self.name} ({self.date})"

# Model for key events (e.g., goals, cards)
class KeyEvent(models.Model):
    event = models.ForeignKey(FootballEvent, on_delete=models.CASCADE, related_name='key_events')
    type = models.CharField(max_length=50, default="Unknown")  # e.g., "Goal", "Yellow Card"
    time = models.CharField(max_length=10, default="N/A")  # e.g., "45:00"
    team = models.CharField(max_length=100, default="Unknown")  # Team involved
    player = models.CharField(max_length=100, default="Unknown")  # Player involved
    assist = models.CharField(max_length=100, blank=True, null=True)
    is_goal = models.BooleanField(default=False)
    is_yellow_card = models.BooleanField(default=False)
    is_red_card = models.BooleanField(default=False)
    is_penalty = models.BooleanField(default=False)  # New field for penalty goals

    def __str__(self):
        return f"{self.type} by {self.player} at {self.time}"

# Model for betting odds
class BettingOdds(models.Model):
    event = models.ForeignKey(FootballEvent, on_delete=models.CASCADE, related_name='odds')
    home_odds = models.CharField(max_length=20, default="N/A")  # Home team odds
    away_odds = models.CharField(max_length=20, default="N/A")  # Away team odds
    draw_odds = models.CharField(max_length=20, default="N/A")  # Draw odds
    provider = models.CharField(max_length=100, default="Unknown Provider")  # Odds provider

    def __str__(self):
        return f"Odds for {self.event.name}"

# Model for detailed match statistics
class DetailedStats(models.Model):
    event = models.ForeignKey(FootballEvent, on_delete=models.CASCADE, related_name='detailed_stats')
    possession = models.CharField(max_length=50, default="N/A")  # e.g., "55% - 45%"
    home_shots = models.CharField(max_length=10, default="N/A")  # Home team shots
    away_shots = models.CharField(max_length=10, default="N/A")  # Away team shots
    goals = models.JSONField(default=list)  # List of goals: [{"scorer": "Player", "team": "Team", "time": "45:00", "assist": "Player"}]

    def __str__(self):
        return f"Stats for {self.event.name}"

# Model for a golf tour (e.g., PGA, LPGA)
class GolfTour(models.Model):
    tour_id = models.CharField(max_length=50, unique=True)  # e.g., "pga", "lpga"
    name = models.CharField(max_length=100)  # e.g., "PGA Tour"
    icon = models.CharField(max_length=10, default="🏌️‍♂️")  # Emoji icon
    priority = models.PositiveIntegerField(default=999)  # Sorting priority

    def __str__(self):
        return self.name

# Model for a golf course
class GolfCourse(models.Model):
    name = models.CharField(max_length=200)  # Course name
    par = models.CharField(max_length=10, default="N/A")  # Course par
    yardage = models.CharField(max_length=20, default="N/A")  # Course yardage

    def __str__(self):
        return self.name

# Model for a golf player
class GolfPlayer(models.Model):
    player_id = models.CharField(max_length=50, unique=True)  # ESPN player ID
    name = models.CharField(max_length=100)  # Player name
    country = models.CharField(max_length=100, blank=True, null=True)  # Player's country
    world_ranking = models.PositiveIntegerField(null=True, blank=True)  # World ranking

    def __str__(self):
        return self.name

# Model for a golf event
class GolfEvent(models.Model):
    event_id = models.CharField(max_length=50, unique=True)  # ESPN event ID
    name = models.CharField(max_length=200)  # Event name, e.g., "The Masters"
    short_name = models.CharField(max_length=200)  # Shortened name
    date = models.DateTimeField()  # Event date and time
    state = models.CharField(
        max_length=20,
        choices=[
            ('pre', 'Pre'),
            ('in', 'In Progress'),
            ('post', 'Post'),
            ('unknown', 'Unknown'),
        ],
        default='pre'
    )  # Event status
    completed = models.BooleanField(default=False)  # Whether event is completed
    venue = models.CharField(max_length=200, default="Location TBD")  # Venue name
    city = models.CharField(max_length=100, default="Unknown")  # City
    state_location = models.CharField(max_length=100, default="Unknown")  # State or region
    tour = models.ForeignKey(GolfTour, on_delete=models.CASCADE, related_name='events', null=True)  # Associated tour
    course = models.ForeignKey(GolfCourse, on_delete=models.CASCADE, related_name='events', null=True)  # Associated course
    purse = models.CharField(max_length=20, default="N/A")  # Prize purse
    broadcast = models.CharField(max_length=100, default="N/A")  # Broadcast info
    current_round = models.PositiveIntegerField(default=1)  # Current round
    total_rounds = models.PositiveIntegerField(default=4)  # Total rounds
    is_playoff = models.BooleanField(default=False)  # Playoff status
    weather_condition = models.CharField(max_length=100, default="N/A")  # Weather condition
    weather_temperature = models.CharField(max_length=20, default="N/A")  # Weather temperature
    last_updated = models.DateTimeField(auto_now=True)  # Last update timestamp

    def __str__(self):
        return f"{self.name} ({self.date})"

# Model for leaderboard entries
class LeaderboardEntry(models.Model):
    event = models.ForeignKey(GolfEvent, on_delete=models.CASCADE, related_name='leaderboard')
    player = models.ForeignKey(GolfPlayer, on_delete=models.CASCADE, related_name='leaderboard_entries')
    position = models.CharField(max_length=10, default="N/A")  # Position in leaderboard
    score = models.CharField(max_length=10, default="N/A")  # Current score
    rounds = models.JSONField(default=list)  # List of round scores, e.g., [70, 72, 71, "N/A"]
    strokes = models.CharField(max_length=10, default="N/A")  # Total strokes
    status = models.CharField(max_length=20, default="active")  # Player status, e.g., "active", "withdrawn"

    def __str__(self):
        return f"{self.player.name} - {self.event.name} (Pos: {self.position})"

    class Meta:
        unique_together = ('event', 'player')
        
# Tennis models
# Tennis models
class TennisLeague(models.Model):
    league_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default="🎾")
    priority = models.PositiveIntegerField(default=999)

    def __str__(self):
        return self.name

class TennisTournament(models.Model):
    tournament_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    league = models.ForeignKey(TennisLeague, on_delete=models.CASCADE, related_name='tournaments')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

class TennisPlayer(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50, blank=True)
    world_ranking = models.CharField(max_length=10, default="N/A")

    def __str__(self):
        return self.name

class TennisVenue(models.Model):
    name = models.CharField(max_length=200)
    court = models.CharField(max_length=100, default="Unknown")

    def __str__(self):
        return f"{self.name} - {self.court}"

class TennisEvent(models.Model):
    event_id = models.CharField(max_length=50, unique=True)
    tournament = models.ForeignKey(TennisTournament, on_delete=models.CASCADE, related_name='events')
    date = models.DateTimeField()
    state = models.CharField(
        max_length=20,
        choices=[
            ('pre', 'Pre'),
            ('in', 'In Progress'),
            ('post', 'Post'),
            ('unknown', 'Unknown'),
        ],
        default='pre'
    )
    completed = models.BooleanField(default=False)
    player1 = models.ForeignKey(TennisPlayer, on_delete=models.CASCADE, related_name='player1_events')
    player2 = models.ForeignKey(TennisPlayer, on_delete=models.CASCADE, related_name='player2_events')
    score = models.CharField(max_length=50, default="TBD")
    sets = models.JSONField(default=list)
    stats = models.JSONField(default=dict)
    clock = models.CharField(max_length=20, default="0:00")
    period = models.PositiveIntegerField(default=0)
    round_name = models.CharField(max_length=100, default="Unknown Round")
    venue = models.ForeignKey(TennisVenue, on_delete=models.SET_NULL, null=True, related_name='events')
    match_type = models.CharField(max_length=50, default="Unknown")
    player1_rank = models.CharField(max_length=10, default="N/A")
    player2_rank = models.CharField(max_length=10, default="N/A")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.player1.name} vs {self.player2.name} - {self.tournament.name} ({self.date})"

    class Meta:
        indexes = [
            models.Index(fields=['date', 'state']),
            models.Index(fields=['tournament']),
        ]

class TennisBettingOdds(models.Model):
    event = models.ForeignKey(TennisEvent, on_delete=models.CASCADE, related_name='odds')
    player1_odds = models.CharField(max_length=20, default="N/A")
    player2_odds = models.CharField(max_length=20, default="N/A")
    provider = models.CharField(max_length=100, default="Unknown Provider")

    def __str__(self):
        return f"Odds for {self.event.player1.name} vs {self.event.player2.name}"
    


# Model for a horse racing course
class HorseRacingCourse(models.Model):
    course_id = models.IntegerField(unique=True, null=True, blank=True)  # RacingPost course ID
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, default="Unknown")
    track_type = models.CharField(max_length=50)  # e.g., "Flat", "National Hunt"
    surface = models.CharField(max_length=50)  # e.g., "Turf", "All Weather"
    region = models.CharField(max_length=10, default="GB")  # e.g., "GB", "IRE", "FR"

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

# Model for a horse racing meeting (replaces RaceMeeting)
class HorseRacingMeeting(models.Model):
    date = models.DateField()
    course = models.ForeignKey(HorseRacingCourse, on_delete=models.CASCADE, related_name='meetings')
    url = models.URLField(unique=True, blank=True, null=True)  # Optional RacingPost URL

    def __str__(self):
        return f"{self.course.name} - {self.date}"

    class Meta:
        unique_together = ('date', 'course')

# Model for a horse racing race (replaces Race)
class HorseRacingRace(models.Model):
    meeting = models.ForeignKey(HorseRacingMeeting, on_delete=models.CASCADE, related_name='races')
    race_id = models.IntegerField(unique=True)  # RacingPost race ID
    off_time = models.CharField(max_length=5)  # e.g., "14:40"
    name = models.CharField(max_length=255)  # Race name
    distance_round = models.CharField(max_length=50, blank=True, null=True)  # e.g., "2m4½f"
    distance = models.CharField(max_length=50, blank=True, null=True)  # e.g., "2m4f127y"
    distance_f = models.FloatField(blank=True, null=True)  # Distance in furlongs
    pattern = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Grade 2", "Listed"
    race_class = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Class 1"
    type = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Chase", "Flat"
    age_band = models.CharField(max_length=50, blank=True, null=True)  # e.g., "5yo+"
    rating_band = models.CharField(max_length=50, blank=True, null=True)  # Rating band
    prize = models.CharField(max_length=50, blank=True, null=True)  # e.g., "£39,865"
    field_size = models.IntegerField(blank=True, null=True)  # Number of runners
    going = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Good"
    rail_movements = models.CharField(max_length=255, blank=True, null=True)  # Rail movements
    stalls = models.CharField(max_length=50, blank=True, null=True)  # Stalls position
    weather = models.CharField(max_length=255, blank=True, null=True)  # Weather conditions
    surface = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Turf"

    def __str__(self):
        return f"{self.name} at {self.off_time} - {self.meeting.course.name}"

    class Meta:
        unique_together = ('meeting', 'off_time', 'race_id')

# Model for a horse
class Horse(models.Model):
    horse_id = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=100)
    dob = models.DateField(blank=True, null=True)  # Date of birth
    age = models.IntegerField(blank=True, null=True)  # Age
    sex = models.CharField(max_length=50, blank=True, null=True)  # e.g., "gelding"
    sex_code = models.CharField(max_length=1, blank=True, null=True)  # e.g., "G"
    colour = models.CharField(max_length=50, blank=True, null=True)  # e.g., "b"
    region = models.CharField(max_length=50, blank=True, null=True)  # e.g., "IRE"
    breeder = models.CharField(max_length=100, blank=True, null=True)  # Breeder name
    dam = models.CharField(max_length=100, blank=True, null=True)  # Dam name
    dam_region = models.CharField(max_length=50, blank=True, null=True)  # Dam region
    sire = models.CharField(max_length=100, blank=True, null=True)  # Sire name
    sire_region = models.CharField(max_length=50, blank=True, null=True)  # Sire region
    grandsire = models.CharField(max_length=100, blank=True, null=True)  # Grandsire name
    damsire = models.CharField(max_length=100, blank=True, null=True)  # Damsire name
    damsire_region = models.CharField(max_length=50, blank=True, null=True)  # Damsire region

    def __str__(self):
        return self.name

# Model for a trainer
class Trainer(models.Model):
    trainer_id = models.CharField(max_length=16, unique=True)  # Changed to CharField
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Jockey(models.Model):
    jockey_id = models.CharField(max_length=16, unique=True)  # Changed to CharField
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Model for a runner in a race
class RaceRunner(models.Model):
    race = models.ForeignKey(HorseRacingRace, on_delete=models.CASCADE, related_name='runners')
    horse = models.ForeignKey(Horse, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True)
    jockey = models.ForeignKey(Jockey, on_delete=models.CASCADE, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Weight in stones and pounds
    number = models.IntegerField(default=0)  # Race card number
    draw = models.IntegerField(null=True, blank=True)  # Stall draw number
    headgear = models.CharField(max_length=50, blank=True, null=True)  # e.g., "b", "p", "t"
    headgear_first = models.BooleanField(default=False)  # First time wearing headgear
    lbs = models.IntegerField(blank=True, null=True)  # Weight in pounds
    official_rating = models.IntegerField(blank=True, null=True)  # Official rating
    rpr = models.IntegerField(blank=True, null=True)  # Racing Post Rating
    topspeed = models.IntegerField(blank=True, null=True)  # Topspeed rating
    form = models.CharField(max_length=50, blank=True, null=True)  # Recent form
    last_run = models.DateField(blank=True, null=True)  # Date of last run
    trainer_rtf = models.CharField(max_length=50, blank=True, null=True)  # Trainer RTF
    trainer_14_days_runs = models.IntegerField(blank=True, null=True)  # Trainer runs in last 14 days
    trainer_14_days_wins = models.IntegerField(blank=True, null=True)  # Trainer wins in last 14 days
    trainer_14_days_percent = models.FloatField(blank=True, null=True)  # Trainer win percentage in last 14 days
    owner = models.CharField(max_length=100, blank=True, null=True)  # Owner name
    comment = models.TextField(blank=True, null=True)  # Comment on horse
    spotlight = models.TextField(blank=True, null=True)  # Spotlight comment
    stats = models.JSONField(default=dict)  # Additional stats

    def __str__(self):
        return f"{self.horse.name} ({self.number})"

    class Meta:
        ordering = ['number']
        unique_together = ('race', 'number')

# Model for runner quotes
class RunnerQuote(models.Model):
    runner = models.ForeignKey(RaceRunner, on_delete=models.CASCADE, related_name='quotes')
    date = models.DateField()  # Quote date
    race_id = models.IntegerField(blank=True, null=True)  # Race ID
    course = models.CharField(max_length=100, blank=True, null=True)  # Course name
    course_id = models.IntegerField(blank=True, null=True)  # Course ID
    distance_f = models.FloatField(blank=True, null=True)  # Distance in furlongs
    distance_y = models.IntegerField(blank=True, null=True)  # Distance in yards
    quote = models.TextField()  # Quote text

    def __str__(self):
        return f"Quote for {self.runner.horse.name} on {self.date}"

# Model for race results (replaces RaceResult)
class HorseRacingResult(models.Model):
    race = models.ForeignKey(HorseRacingRace, on_delete=models.CASCADE, related_name='results')
    horse = models.ForeignKey(Horse, on_delete=models.CASCADE, related_name='results')
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, related_name='results')
    jockey = models.ForeignKey(Jockey, on_delete=models.SET_NULL, null=True, related_name='results')
    position = models.CharField(max_length=10, blank=True, null=True)  # Changed to CharField
    draw = models.IntegerField(blank=True, null=True)  # Draw position
    ovr_btn = models.FloatField(blank=True, null=True)  # Overall beaten distance
    btn = models.FloatField(blank=True, null=True)  # Beaten distance to previous horse
    lbs = models.IntegerField(blank=True, null=True)  # Weight carried
    headgear = models.CharField(max_length=50, blank=True, null=True)  # Headgear
    time = models.CharField(max_length=50, blank=True, null=True)  # Finishing time
    seconds = models.FloatField(blank=True, null=True)  # Time in seconds
    decimal_time = models.FloatField(blank=True, null=True)  # Decimal time
    prize = models.CharField(max_length=50, blank=True, null=True)  # Prize money
    official_rating = models.IntegerField(blank=True, null=True)  # Official rating
    rpr = models.IntegerField(blank=True, null=True)  # Racing Post Rating
    comment = models.TextField(blank=True, null=True)  # Comment on performance

    def __str__(self):
        return f"Result for {self.horse.name} in {self.race.name} - Pos: {self.position}"

    class Meta:
        unique_together = ('race', 'horse')

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50)  # e.g., 'like', 'comment', 'follow'
    content = models.TextField()  # Notification message
    read = models.BooleanField(default=False)  # Whether notification has been read
    created_at = models.DateTimeField(auto_now_add=True)  # When notification was created
    related_tip = models.ForeignKey(Tip, on_delete=models.CASCADE, null=True, blank=True)  # Related tip if any
    related_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)  # Related comment if any
    related_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='related_notifications')  # Related user if any

    def __str__(self):
        return f"Notification for {self.user.username}: {self.content[:50]}"

    class Meta:
        ordering = ['-created_at']  # Most recent notifications first

class HorseRacingBettingOdds(models.Model):
    runner = models.ForeignKey(RaceRunner, on_delete=models.CASCADE, related_name='odds')
    bookmaker = models.CharField(max_length=100)  # Bookmaker name
    odds = models.DecimalField(max_digits=7, decimal_places=2)  # Odds value
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bookmaker} odds for {self.runner}"

    class Meta:
        unique_together = ('runner', 'bookmaker')
        ordering = ['bookmaker', '-updated_at']