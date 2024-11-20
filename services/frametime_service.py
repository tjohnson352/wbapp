# frametime_service.py code file
import pandas as pd
from flask import session
import re

# Default frametime settings
def get_default_frametime():
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    default_times = {"ft_start": "08:00", "ft_end": "16:00"}
    df4 = pd.DataFrame(days, columns=["day"])
    df4 = df4.assign(**default_times)
    return df4

# Function to get frametime data from session
def get_frametime():
    if 'df4' in session:
        df4 = pd.read_json(session['df4'])
    else:
        df4 = get_default_frametime()
    return df4

# Function to save frametime data to session
def save_frametime(df4):
    session['df4'] = df4.to_json()

# Function to validate and format input times
def validate_time(input_time):
    try:
        if re.match(r'^\d{3,4}$', input_time):  # Match time in formats like '850', '1330'
            input_time = input_time.zfill(4)  # Pad with leading zero if less than 4 digits
            hours = int(input_time[:2])
            minutes = int(input_time[2:])
        elif ":" in input_time:
            hours, minutes = map(int, input_time.split(":"))
        else:
            hours = int(input_time)
            minutes = 0

        # Adjust hours if the value is less than 7 (add 12 to convert to PM time)
        if hours < 7:
            hours += 12
        
        # Ensure valid time constraints
        if hours > 18:
            hours = 18
        if minutes < 0 or minutes >= 60:
            minutes = 0

        # Format and return time in HH:MM
        return f"{hours:02d}:{minutes:02d}"
    except ValueError:
        return "08:00"

# Function to process and update frametime data
def update_frametime(request_form):
    df4 = get_frametime()  # Get the current frametime data from session
    for index, row in df4.iterrows():
        day = row['day']
        # Update the start and end times based on the form data
        start_time = request_form.get(f"start_{day}", row['ft_start'])
        end_time = request_form.get(f"end_{day}", row['ft_end'])
        df4.at[index, 'ft_start'] = validate_time(start_time)
        df4.at[index, 'ft_end'] = validate_time(end_time)

    save_frametime(df4)

# Function to submit the final frametime
def submit_frametime():
    df4 = get_frametime()
    # Save the finalized frametime in session
    session['final_frametime'] = df4.to_json()

# Handle frametime actions
def handle_frametime_action(request_form):
    action = request_form.get("action", "")
    update_frametime(request_form)  # Save changes to the session

    if action == "back":
        # Redirect to the upload page
        return "back"
    elif action == "save_forward":
        # Redirect to the schedule update page
        return "forward"
    return "stay"  # Default behavior

