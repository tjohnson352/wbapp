from flask import session, current_app
import pandas as pd

def total_minutes():
    """
    Calculates the total minutes for each activity type in df2d 
    and stores them in variables for session use.

    Returns:
    None
    """
    try:
        # Load DataFrame from the session
        df2d = pd.read_json(session['df2d'])

        # Ensure the 'minutes' column in df2d is numeric
        df2d['minutes'] = pd.to_numeric(df2d['minutes'], errors='coerce')

        # Calculate the total minutes for each activity type
        totals = df2d.groupby('type')['minutes'].sum().to_dict()

        # Store totals in session variables
        for activity_type, total_minutes in totals.items():
            variable_name = f"{activity_type.lower().replace('/', '_')}"  # Format variable names
            session[variable_name] = total_minutes

        # Log the saved variables
        current_app.logger.info(f"Saved total minutes in variables: {totals}")

    except Exception as e:
        current_app.logger.error(f"Error in total_minutes function: {e}")
