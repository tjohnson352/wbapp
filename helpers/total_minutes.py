from flask import session, current_app
import pandas as pd

def total_minutes():
    """
    Calculates the total minutes for each activity type in df2c 
    and stores them in variables for session use.

    Returns:
    None
    """
    try:
        # Load DataFrame from the session
        df2c = pd.read_json(session['df2c'])

        # Ensure the 'minutes' column in df2c is numeric
        df2c['minutes'] = pd.to_numeric(df2c['minutes'], errors='coerce')

        # Calculate the total minutes for each activity type
        totals = df2c.groupby('type')['minutes'].sum().to_dict()

        # Store totals in session variables
        for activity_type, total_minutes in totals.items():
            variable_name = f"{activity_type.lower().replace('/', '_')}"  # Format variable names
            session[variable_name] = total_minutes

        # Log the saved variables
        current_app.logger.info(f"Saved total minutes in variables: {totals}")

    except Exception as e:
        current_app.logger.error(f"Error in total_minutes function: {e}")
