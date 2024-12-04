# time_handling.py
from datetime import datetime

def format_time(value):
    """
    Formats a given time value (in string format) to 24-hour format without AM/PM.
    
    Args:
        value (str): The time string in "HH:MM" format.
    
    Returns:
        str: The formatted time string in "HH:MM" format, or the original value if formatting fails.
    """
    if isinstance(value, str):
        try:
            time_obj = datetime.strptime(value, "%H:%M")
            return time_obj.strftime("%H:%M")  # Formats time as "14:30"
        except ValueError:
            return value
    return value
