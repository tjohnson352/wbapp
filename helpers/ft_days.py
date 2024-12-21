from flask import session
import pandas as pd
from io import StringIO


def ft_days():
    """
    Extracts unique values from the 'day' column of df2c stored in the session,
    dynamically creates DataFrames for each day, saves them back to the session,
    stores the names of the created DataFrames in df_names, and identifies off_days.

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

        # Save the unique values to the session as ft_days
        session['ft_days'] = unique_days

        # Define all weekdays
        all_weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        # Determine off_days as the days not in unique_days
        off_days = [day for day in all_weekdays if day not in unique_days]
        session['off_days'] = off_days

        # Mapping of days to DataFrame variable names
        day_to_variable = {
            'Monday': 'df3a',
            'Tuesday': 'df3b',
            'Wednesday': 'df3c',
            'Thursday': 'df3d',
            'Friday': 'df3e'
        }

        # List to store the names of created DataFrames
        df_names = []

        # Save all day-specific DataFrames in a single `dataframes` dictionary in the session
        dataframes = {}

        # Dynamically create DataFrames for each day and save them to session
        for day in unique_days:
            if day in day_to_variable:
                day_df = df2c[df2c['day'] == day].reset_index(drop=True)
                variable_name = day_to_variable[day]
                session[variable_name] = day_df.to_json()  # Save individual DataFrame to session
                dataframes[variable_name] = day_df.to_json()  # Add to the `dataframes` dictionary
                df_names.append(variable_name)  # Add the name to the list

        # Save the list of DataFrame names and the consolidated `dataframes` dictionary
        session['df_names'] = df_names
        session['dataframes'] = dataframes
        session.modified = True  # Ensure session is marked as modified

        # Debugging information
        print(f"ft_days: {unique_days}")
        print(f"off_days: {off_days}")
        print(f"df_names: {df_names}")
        print("Session Keys after saving df_names, off_days, and dataframes:", session.keys())

    except Exception as e:
        print(f"Error: {e}")


def prime_dfs():
    """
    Reads dynamically created DataFrames from the session and fills them based on the 'day' condition.

    Saves the DataFrames back to the session for further processing.

    Returns:
        None
    """
    try:
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
        dataframes = {}
        for day, variable in day_to_variable.items():
            if day in session.get('ft_days', []):  # Check if day is in session's ft_days
                # Filter df2c for the specific day
                day_df = df2c[df2c['day'] == day].reset_index(drop=True)
                # Save filtered DataFrame in the session
                session[variable] = day_df.to_json()
                dataframes[variable] = day_df.to_json()  # Add to the consolidated `dataframes` dictionary

        # Update `dataframes` in the session
        session['dataframes'] = dataframes
        session.modified = True  # Ensure session is marked as modified

        # Debugging information
        print("DataFrames successfully updated in session.")
        print(f"Session DataFrames: {list(dataframes.keys())}")

    except Exception as e:
        print(f"Error in prime_dfs: {e}")
