import pandas as pd
from flask import session
from io import StringIO
import sqlite3

def create_df5():
    """
    Create a DataFrame with specific session variables, save it to SQLite, and store it in the session as JSON.
    """
    try:
        # Extract required variables from the session
        data = {
            'ID': session.get('encrypted_name', 'Unknown'),
            'work_percent': session.get('work_percent', 0),
            'middle_manager': session.get('middle_manager', 'No'),
            'ft_days': session.get('ft_days', 0),
            'off_days': session.get('off_days', 0),
            'planning_time': session.get('planning_time', 0),
            'breaks': session.get('breaks', 0),
            'general': session.get('general', 0),
            'contract_teachtime': session.get('contract_teachtime', 0),
            'assigned_teach': session.get('assigned_teach', 0),
            'adjusted_contract_teach_time': session.get('adjusted_contract_teach_time', 0),
            'contract_frametime': session.get('contract_frametime', 0),
            'assigned_frametime': session.get('assigned_frametime', 0),
            'over_teachtime': session.get('over_teachtime', 0),
            'over_framtime': session.get('over_framtime', 0),
            'total_overtime': session.get('total_overtime', 0),
            'missing_break': ", ".join(session.get('missing_break', [])),  # Convert list to string
        }

        # Create the DataFrame
        df5 = pd.DataFrame([data])

        # Save DataFrame to SQLite database
        conn = sqlite3.connect('data.db')  # Create or connect to SQLite database
        df5.to_sql('df5_table', conn, if_exists='replace', index=False)  # Save to table 'df5_table'
        conn.close()

        # Save DataFrame to the session as JSON
        session['df5'] = df5.to_json(orient='split')  # Use 'split' orientation for easier reconstruction

    except Exception as e:
        print(f"Error in create_save_df5: {e}")


import pandas as pd
import json

def display_dataframes():
    try:
        # Load the dataframes dictionary from the session
        dataframes_json = session.get('dataframes')
        if not dataframes_json:
            raise ValueError("No dataframes found in session.")

        # Parse JSON strings back into DataFrames
        dataframes = {key: pd.read_json(value, orient='split') for key, value in dataframes_json.items()}

        # Display each DataFrame
        for day, df in dataframes.items():
            print(f"Data for {day}:")
            print(df)
            print("\n")

    except Exception as e:
        print(f"Error displaying dataframes: {e}")
