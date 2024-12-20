from flask import session
import pandas as pd
from io import StringIO

def ft_days():
    """
    Extracts unique values from the 'day' column of df2c stored in the session,
    dynamically creates DataFrames for each day, and saves them back to the session.

    Returns:
        None
    """
    try:
        # Retrieve df2c from session
        df2c_json = session.get('df2c')
        if not df2c_json:
            raise ValueError("df2c not found in session.")

        # Convert JSON string back to DataFrame
        df2c = pd.read_json(StringIO(df2c_json))

        # Check if 'day' column exists
        if 'day' not in df2c.columns:
            raise ValueError("The DataFrame does not contain a 'day' column.")

        # Get unique values from the 'day' column
        unique_days = df2c['day'].unique().tolist()

        # Save the unique values to the session
        session['ft_days'] = unique_days

        # Mapping of days to DataFrame variable names
        day_to_variable = {
            'Monday': 'df3a',
            'Tuesday': 'df3b',
            'Wednesday': 'df3c',
            'Thursday': 'df3d',
            'Friday': 'df3e'
        }

        # Dynamically create DataFrames for each day and save them to session
        for day in unique_days:
            if day in day_to_variable:
                day_df = df2c[df2c['day'] == day].reset_index(drop=True)
                session[day_to_variable[day]] = day_df.to_json()

    except Exception as e:
        print(f"Error: {e}")



import pandas as pd
from io import StringIO
from flask import session

import pandas as pd
from io import StringIO
from flask import session

def prime_dfs():
    """
    Reads dynamically created DataFrames from the session and fills them based on the 'day' condition.

    Saves the DataFrames back to the session for further processing.

    Returns:
        None
    """
    # Mapping of days to variable names
    day_to_variable = {
        'Monday': 'df3a',
        'Tuesday': 'df3b',
        'Wednesday': 'df3c',
        'Thursday': 'df3d',
        'Friday': 'df3e'
    }

    # Retrieve df2c from session
    df2c_json = session.get('df2c')
    if not df2c_json:
        raise ValueError("df2c not found in session.")
    
    # Convert JSON string back to DataFrame
    df2c = pd.read_json(StringIO(df2c_json))

    # Fill DataFrames for each day in the mapping
    for day, variable in day_to_variable.items():
        if day in session.get('ft_days', []):  # Check if day is in session's ft_days
            # Filter df2c for the specific day
            day_df = df2c[df2c['day'] == day].reset_index(drop=True)
            # Save filtered DataFrame in the session
            session[variable] = day_df.to_json()

