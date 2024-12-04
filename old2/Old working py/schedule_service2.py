# services/schedule_service.py
import pandas as pd
from flask import session

# Function to create df6 and populate with data from df3
def create_df6(df3):
    # Define empty DataFrame df6 with specified columns
    df6 = pd.DataFrame(columns=["day", "activity_type", "activity_name", "start_time", "end_time", "duration_minutes"])
    
    # Populate columns from df3
    df6["activity_name"] = df3["activities"]

    # Ensure start and end times remain as HH:MM strings
    df6["start_time"] = df3["start"]
    df6["end_time"] = df3["end"]
    # Function to calculate duration in minutes from start and end times
    def calculate_duration(start, end):
        if start and end:
            # Split times into hours and minutes
            start_hours, start_minutes = map(int, start.split(":"))
            end_hours, end_minutes = map(int, end.split(":"))
            
            # Convert to minutes
            start_total_minutes = start_hours * 60 + start_minutes
            end_total_minutes = end_hours * 60 + end_minutes
            
            # Calculate duration in minutes
            return max(0, end_total_minutes - start_total_minutes)  # Avoid negative durations
        return None

    # Apply the duration calculation function
    df6["duration_minutes"] = df6.apply(
        lambda row: calculate_duration(row["start_time"], row["end_time"]), axis=1
    )

    # Set default values for dropdown columns
    df6["day"] = "REMOVE"  # Default value for dropdown, can be changed by user
    df6["activity_type"] = "TEACHING"  # Default value for dropdown, can be changed by user
    
    # Save df6 to session
    
    session['df6'] = df6.to_json()
    
    
    return df6


# Function to get df6 from session
def get_df6():
    if 'df6' in session:
        df6 = pd.read_json(session['df6'])
    else:
        df6 = pd.DataFrame(columns=["day", "activity_type", "activity_name", "start_time", "end_time", "duration_minutes"])
    return df6

# Function to save df6 to session
def save_df6(df6):
    session['df6'] = df6.to_json()
