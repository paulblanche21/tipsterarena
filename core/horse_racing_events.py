import logging
from django.core.management import call_command

logger = logging.getLogger(__name__)

def get_racecards_json():
    """
    Fetch horse racing racecards for today and tomorrow, and results for the last 7 days.
    """
    try:
        logger.debug("Calling scrape_racecards with results=True")
        meetings = call_command('scrape_racecards', results=True)
        logger.debug(f"Raw meetings type: {type(meetings)}")
        if meetings is None:
            logger.warning("call_command returned None")
            meetings = []
        elif isinstance(meetings, str):
            logger.warning(f"Unexpected string output from call_command: {meetings}")
            meetings = []
        elif not isinstance(meetings, list):
            logger.warning(f"Unexpected output type from call_command: {type(meetings)}")
            meetings = []
        elif not meetings:
            logger.warning("No meetings returned from scrape_racecards")
        else:
            logger.info(f"Fetched {len(meetings)} meetings from rpscrape")
            logger.debug(f"Sample meeting: {meetings[0] if meetings else 'None'}")
        return meetings or []

    except Exception as e:
        logger.error(f"Error in scrape_racecards: {str(e)}", exc_info=True)
        return []