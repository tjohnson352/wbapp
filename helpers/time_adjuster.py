# time_adjuster.py

# Summary of Functions
# -------------------------------------------------------------------------------
# | Function Name | Description                                                |
# -------------------------------------------------------------------------------
# | time1         | Adds a leading zero to time strings in the form #:## to     |
# |               | convert them to ##:##.                                      |
# -------------------------------------------------------------------------------
# | time2         | Finds strings in a timespan format (##:## - ##:## or        |
# |               | ##:##-##:##) and ensures times are properly formatted by    |
# |               | applying time1 to adjust any instances of #:## to ##:##.    |
# -------------------------------------------------------------------------------
# | time3         | Takes a time string in the format ##:## and returns the     |
# |               | hours and minutes as integers.                              |
# -------------------------------------------------------------------------------
# | time4         | Takes a timespan string (formatted as ##:## - ##:##) and    |
# |               | calculates the total number of minutes for the time span.   |
# -------------------------------------------------------------------------------
# | time5         | Searches for substrings in various timespan formats (e.g.,  |
# |               | ##:## - ##:##, #:## - #:##) within the given text.          |
# -------------------------------------------------------------------------------
# | time6         | Returns the start time as the part of the timespan preceding|
# |               | the dash.                                                   |
# -------------------------------------------------------------------------------
# | time7         | Returns the end time as the part of the timespan following  |
# |               | the dash.                                                   |
# -------------------------------------------------------------------------------

import re
import pandas as pd
import traceback
import inspect


def time1(time_str):
    """
    Finds strings in the form #:## and changes it to ##:## by adding a leading zero.
    """
    return re.sub(r'\b(\d):(\d{2})\b', r'0\1:\2', time_str)

def time2(timespan_str):
    """
    Finds strings in a timespan format ##:## - ##:## or ##:##-##:##.
    Applies time1 to adjust instances where time is in the form #:## instead of ##:##.
    """
    timespan_str = time1(timespan_str)  # Apply time1 to ensure times are properly formatted
    return re.sub(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})', r'\1 - \2', timespan_str)

def time3(time_str):
    """
    Takes a time string in the format ##:## and returns the hours and minutes as integers.
    """
    hours, minutes = map(int, time_str.split(':'))
    return hours, minutes

def time4(timespan_str):
    """
    Takes a timespan string in the format 'hh:mm - hh:mm', splits it, extracts hours and minutes for start and end times,
    and calculates the total duration in minutes.

    Parameters:
        timespan_str (str): The time span in the format 'hh:mm - hh:mm'.

    Returns:
        int: The total duration in minutes.
    """
    try:
        if not timespan_str or timespan_str.strip() == "":
            # Return None if the timespan is blank
            return None

        # Split the time span into start and end parts
        time_span_start, time_span_end = timespan_str.split(' - ')

        # Extract hours and minutes for the start time
        start_hr, start_min = map(int, time_span_start.split(':'))

        # Extract hours and minutes for the end time
        end_hr, end_min = map(int, time_span_end.split(':'))

        # Calculate the total duration in minutes
        duration_minutes = (end_hr - start_hr) * 60 + (end_min - start_min)

        return duration_minutes
    except Exception as e:
        raise ValueError(f"Invalid timespan format: {timespan_str}. Error: {e}")

def time5(text):
    """
    Searches for substrings in the format ##:## - ##:##, #:## - #:##, #:## - ##:##, or other similar combinations.
    """
    pattern = r'\b\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\b'
    return re.findall(pattern, text)

def time6(timespan_str):
    """
    Returns the start time as the part of the timespan preceding the dash.
    """
    timespan_str = time2(timespan_str)  # Ensure the timespan is properly formatted
    start_time = timespan_str.split(' - ')[0]
    return start_time

def time7(timespan_str):
    """
    Returns the end time as the part of the timespan following the dash.
    """
    timespan_str = time2(timespan_str)  # Ensure the timespan is properly formatted
    end_time = timespan_str.split(' - ')[1]
    return end_time

def time8(minutes):
    """
    Convert an integer representing minutes since midnight to HH:MM format.

    Args:
        minutes (int): Total minutes since midnight.

    Returns:
        str: Time in HH:MM format.
    """
    if minutes is None:
        return "N/A"  # Handle None input case

    # Calculate hours and minutes
    hh = minutes // 60  # Integer division to get hours
    mm = minutes % 60   # Modulus to get remaining minutes

    # Format with leading zeros and return
    return f"{hh:02d}:{mm:02d}"