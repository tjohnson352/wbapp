import pandas as pd
import re
from flask import session
from collections import Counter
from io import StringIO

def get_names():
    """
    Extract the teacher's full name and school name from the DataFrame,
    and save them along with a unique ID to the session and database.
    If the name_combo already exists in the database, use the preexisting ID.
    """
    try:
        import sqlite3
        import pandas as pd
        from io import StringIO
        import re
        from collections import Counter
        from flask import session

        # Load df1a from the session
        df1a_json = session.get('df1a')
        if not df1a_json:
            raise ValueError("df1a not found in session.")

        df1a = pd.read_json(StringIO(df1a_json))

        # Filter the Content column to remove NaN and whitespace
        filtered_content = df1a['Content'].dropna().str.strip()

        # Identify name candidates allowing for names with more than two words
        name_candidates = filtered_content[
            filtered_content.apply(
                lambda x: re.match(r'^[\w\s-]+$', x, flags=re.UNICODE) is not None
            ) & (filtered_content.str.len() >= 6)  # Minimum length of 6 characters
        ]

        # Find the most common string among the candidates
        most_common_string = Counter(name_candidates).most_common(1)
        full_name = most_common_string[0][0] if most_common_string else ""

        # Extract school name by searching for rows starting with 'IES'
        school_name_row = filtered_content[filtered_content.str.contains(r'^IES\s\w+', na=False)]
        school_name = school_name_row.iloc[0] if not school_name_row.empty else "Unknown School"

        # Create name_combo
        name_combo = f"{school_name} {full_name}"

        session['full_name'] = full_name
        session['school_name'] = school_name
        session['name_combo'] = name_combo

    except Exception as e:
        print(f"Error in get_names: {e}")


def validate_names(full_name: str, consent_full_name: str) -> bool:
    """
    Validates that all parts of the consent_full_name exist in the full_name.

    Args:
        full_name (str): The complete name of the user from session (e.g., "John Doe").
        consent_full_name (str): The name provided for consent (e.g., "John D.").

    Returns:
        bool: True if all parts of consent_full_name exist in full_name, False otherwise.
    """
    # Normalize and split names into lowercase parts
    full_name_parts = [part.strip().lower() for part in full_name.split()]
    consent_name_parts = [part.strip().lower() for part in consent_full_name.split()]

    # Check if every part of consent_full_name is present in full_name
    return all(part in full_name_parts for part in consent_name_parts)
