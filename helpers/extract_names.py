import pandas as pd
from collections import Counter
from flask import session
import regex as re
from io import StringIO


def get_names():
    """
    Extract the teacher's full name and school name from the DataFrame.

    Returns:
        tuple: A tuple containing full_name and school_name.
    """
    try:
        # Load df1a from the session
        df1a = pd.read_json(StringIO(session['df1a']))

        # Filter the Content column to remove NaN and whitespace
        filtered_content = df1a['Content'].dropna().str.strip()

        # Identify name candidates allowing for names with more than two words
        name_candidates = filtered_content[
            filtered_content.apply(
                lambda x: re.match(r'^[\p{L}]+(?:[-\s][\p{L}]+)+$', x, flags=re.UNICODE) is not None
            ) &
            (filtered_content.str.len() >= 6)  # Minimum length of 6 characters
        ]

        # Find the most common string among the candidates
        most_common_string = Counter(name_candidates).most_common(1)

        full_name = most_common_string[0][0] if most_common_string else ""

        # Extract school name by searching for rows starting with 'IES'
        school_name_row = filtered_content[filtered_content.str.contains(r'^IES\s\w+', na=False)]
        school_name = school_name_row.iloc[0] if not school_name_row.empty else "Unknown School"

        # Save results to the session
        session['full_name'] = full_name
        session['school_name'] = school_name
        session['combined_name'] = f"{school_name} {full_name}" 



        return full_name, school_name

    except Exception as e:
        print(f"Error in get_names: {e}")
        return "", ""
