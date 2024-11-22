# frametime_service.py code file
import pandas as pd
from flask import session
import re

# Default frametime settings
def get_default_frametime():
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    default_times = {"ft_start": "08:00", "ft_end": "16:00"}
    df1b = pd.DataFrame(days, columns=["day"])
    df1b = df1b.assign(**default_times)
    return df1b

# Ensure all time values are validated and formatted in get_frametime()
def get_frametime():
    if 'df1b' in session:
        df1b = pd.read_json(session['df1b'])

        # Validate and correct times to ensure consistent formatting
        df1b['ft_start'] = df1b['ft_start'].apply(validate_time)
        df1b['ft_end'] = df1b['ft_end'].apply(validate_time)
    else:
        df1b = get_default_frametime()
    return df1b

# Function to save frametime data to session

def save_frametime(df1b):
    session['df1b'] = df1b.to_json()

# Function to validate and format input times
def validate_time(input_time):
    try:
        # Ensure the input is a string
        if not isinstance(input_time, str):
            input_time = str(input_time)

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
    except (ValueError, TypeError):
        return "08:00"  # Default value for invalid inputs

# Function to process and update frametime data
def update_frametime(request_form):
    df1b = get_frametime()  # Get the current frametime data from session

    for index, row in df1b.iterrows():
        day = row['day']
        # Validate and update the start and end times based on the form data
        start_time = request_form.get(f"start_{day}", row['ft_start'])
        end_time = request_form.get(f"end_{day}", row['ft_end'])
        df1b.at[index, 'ft_start'] = validate_time(start_time)
        df1b.at[index, 'ft_end'] = validate_time(end_time)

    # Save the updated DataFrame back to the session
    save_frametime(df1b)

# Function to submit the final frametime
def submit_frametime():
    df1b = get_frametime()
    # Save the finalized frametime in session
    session['final_frametime'] = df1b.to_json()

# Handle frametime actions
# Handle frametime actions
def handle_frametime_action(request_form):
    action = request_form.get("action", "")
    update_frametime(request_form)  # Save changes to the session

    if action == "Go Back":
        # Redirect to the upload page (previous page)
        return "back"
    elif action == "Save and Move Forward":
        # Redirect to the schedule update page
        return "forward"
    return "stay"  # Default behavior


