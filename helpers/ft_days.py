import pandas as pd
from flask import session
import traceback
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

        session['ft_days'] = []
        # Get unique values from the 'day' column and create a comma-separated string
        unique_days = df2c['day'].unique().tolist()
        session['ft_days'] = ", ".join(unique_days)

        # Define all weekdays
        all_weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        # Determine off_days as the days not in unique_days and create a comma-separated string
        off_days = [day for day in all_weekdays if day not in unique_days]
        session['off_days'] = ", ".join(off_days)

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
                session[variable_name] = day_df.to_json(orient='split')  # Save individual DataFrame to session
                dataframes[variable_name] = day_df.to_json(orient='split')  # Add to the `dataframes` dictionary
                df_names.append(variable_name)  # Add the name to the list

        # Save the list of DataFrame names and the consolidated `dataframes` dictionary
        session['df_names'] = df_names
        session['dataframes'] = dataframes
        session.modified = True  # Ensure session is marked as modified

    except Exception as e:
        # Get traceback details
        tb = traceback.extract_tb(e.__traceback__)
        # Extract the most recent traceback entry
        filename, lineno, _, _ = tb[-1]
        print(f"Error in file {filename} at line {lineno}: {e}")


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
            ft_days = session.get('ft_days', [])
            print("WWW",ft_days)
            if day in ft_days:  # Check if day is in session's ft_days
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
        # Get traceback details
        tb = traceback.extract_tb(e.__traceback__)
        # Extract the most recent traceback entry
        filename, lineno, _, _ = tb[-1]
        print(f"Error in file {filename} at line {lineno}: {e}")
