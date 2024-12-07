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
    Takes a timespan string (formatted as ##:## - ##:##) and calculates the number of minutes for the time span.
    """
    timespan_str = time2(timespan_str)  # Apply time2 to ensure times are properly formatted
    start_time, end_time = timespan_str.split(' - ')
    start_hours, start_minutes = time3(start_time)
    end_hours, end_minutes = time3(end_time)
    
    start_total_minutes = start_hours * 60 + start_minutes
    end_total_minutes = end_hours * 60 + end_minutes
    
    return end_total_minutes - start_total_minutes

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