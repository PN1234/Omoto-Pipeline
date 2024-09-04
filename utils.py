import logging
from datetime import datetime, timezone
import pytz

def new_logger(logger_name: str) -> logging.Logger:
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(logger_name)
    logger.setLevel(level=logging.DEBUG)
    return logger


# def format_iso_date(iso_date_str):
#     """
#     Convert an ISO formatted date string to 'YYYY-MM-DD HH:MM:SS' format.
#     """
#     event_time = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
#     formatted_time = event_time.strftime('%Y-%m-%d %H:%M:%S')    
#     return formatted_time


# def get_current_time_utc():
#     """
#     Get the current UTC time in 'YYYY-MM-DD HH:MM:SS' format.
#     """
#     now_utc = datetime.now(timezone.utc)
#     formatted_time = now_utc.strftime('%Y-%m-%d %H:%M:%S')    
#     return formatted_time




# Define IST timezone
# IST = pytz.timezone('Asia/Kolkata')

# def format_iso_date(iso_date_str):
#     """
#     Convert an ISO formatted date string to 'YYYY-MM-DD HH:MM:SS' format in IST.
#     """
#     # Convert ISO date string to a datetime object in UTC
#     event_time_utc = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
    
#     # Convert the UTC datetime to IST
#     event_time_ist = event_time_utc.astimezone(IST)
    
#     # Format the datetime object to the desired string format
#     formatted_time = event_time_ist.strftime('%Y-%m-%d %H:%M:%S')
    
#     return formatted_time


from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

def format_iso_date(iso_date_str):
    """
    Convert an ISO formatted date string to 'YYYY-MM-DD HH:MM:SS' format in IST.
    """
    # Convert ISO date string to a datetime object in UTC
    event_time_utc = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
    
    # Convert the UTC datetime to IST
    event_time_ist = event_time_utc.astimezone(IST)
    
    # Format the datetime object to the desired string format
    formatted_time = event_time_ist.strftime('%Y-%m-%d %H:%M:%S')
    
    return formatted_time


def get_current_time_utc():
    """
    Get the current UTC time in 'YYYY-MM-DD HH:MM:SS' format and convert it to IST.
    """
    # Get current time in UTC
    now_utc = datetime.now(pytz.utc)
    
    # Convert the current UTC time to IST
    now_ist = now_utc.astimezone(IST)
    
    # Format the datetime object to the desired string format
    formatted_time = now_ist.strftime('%Y-%m-%d %H:%M:%S')
    
    return formatted_time
