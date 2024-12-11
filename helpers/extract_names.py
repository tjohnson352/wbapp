import pandas as pd
from collections import Counter
from flask import session


def get_names():
    """
    Extract the teacher's full name, first name, last name, and school name from the DataFrame.

    Returns:
        tuple: A tuple containing full_name, first_name, last_name, and school_name.
    """
    try:
        # Load df1a from the session
        df1a = pd.read_json(session['df1a'])

        # Filter the Content column to remove NaN and whitespace
        filtered_content = df1a['Content'].dropna().str.strip()

        # Identify name candidates allowing for names with more than two words
        name_candidates = filtered_content[filtered_content.str.contains(r'^[A-Za-z]+(?:\s[A-Za-z]+)*$', na=False)]

        # Find the most common string among the candidates
        most_common_string = Counter(name_candidates).most_common(1)
        full_name = most_common_string[0][0] if most_common_string else ""

        # Extract first and last names from the full name
        name_parts = full_name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        # Extract school name by searching for rows starting with 'IES'
        school_name_row = filtered_content[filtered_content.str.contains(r'^IES\s\w+', na=False)]
        school_name = school_name_row.iloc[0] if not school_name_row.empty else "Unknown School"

        session['first_name'] = first_name
        session['last_name'] = last_name
        session['full_name'] = full_name
        session['school_name'] = school_name
        session['most_common_string'] = most_common_string

        return full_name, first_name, last_name, school_name

    except Exception as e:
        print(f"Error in get_names: {e}")
        return "", "", "", ""