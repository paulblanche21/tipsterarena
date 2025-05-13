"""Views for Tipster Arena.

This module is a placeholder that imports all views from their respective modules.
The actual view implementations can be found in the views/ directory.
"""

from .views.auth_views import *
from .views.tip_views import *
from .views.profile_views import *
from .views.sport_views import *
from .views.api_views import *
from .views.horse_racing_views import *
from .views.tennis_views import *
from .views.football_views import *
from .views.golf_views import *
from .views.general_views import *

# Move this to the very end of the file:
# from .views.interaction_views import mark_notification_read
# mark_notification_read = mark_notification_read

# ... existing code ...

# --- At the very end of the file ---
from .views.interaction_views import mark_notification_read
mark_notification_read = mark_notification_read