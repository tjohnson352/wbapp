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

        print("School extracted:", school_name)

        # Create name_combo
        name_combo = f"{school_name} {full_name}"

        # Second method to double-check school name 
        # Find a school in the school_list.txt file that
        # matches the school in the schedule
        school_name2 = school_name
        try:
            with open('helpers/school_list.txt', 'r', encoding='utf-8') as f:
                schools = [line.strip() for line in f.readlines()]

            for school in schools:
                # Remove 'IES' and get the last term of the school name
                parts = school.replace('IES ', '').split()
                search_term = parts[-1] if parts else ""

                # Search for the last term in filtered_content
                if any(search_term in line for line in filtered_content):
                    school_name2 = school
                    break

        except Exception as e:
            print(f"Error reading school list: {e}")

        print("School name (second method):", school_name2)

        school_name = school_name2

        # Find school_id for school_name2 from the table schools
        school_id = None
        try:
            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT school_id FROM schools WHERE school_name = ?", (school_name,))
            result = cursor.fetchone()
            if result:
                school_id = result[0]
            conn.close()
        except Exception as e:
            print(f"Error retrieving school_id: {e}")

        # Store results in session
        session['full_name'] = full_name
        session['school_name'] = school_name
        session['school_id'] = school_id
        session['name_combo'] = name_combo
    except Exception as e:
        print(f"Error in get_names: {e}")



def validate_names() -> bool:
    """
    Validates that all parts of the consent_full_name exist in the full_name.
    Reads both values directly from the session.

    Returns:
        bool: True if all parts of consent_full_name exist in full_name, False otherwise.
    """
    # Retrieve names from session with default empty strings to avoid errors
    full_name = session.get('full_name', '').strip().lower()
    consent_full_name = session.get('consent_full_name', '').strip().lower()

    # If either name is empty, validation fails
    if not full_name or not consent_full_name:
        return False

    # Normalize and split names into lowercase parts
    full_name_parts = full_name.split()
    consent_name_parts = consent_full_name.split()

    # Check if every part of consent_full_name is present in full_name
    return all(part in full_name_parts for part in consent_name_parts)

import sqlite3
from flask import session

import sqlite3
from flask import session

def update_user_school_id():
    """Update the user's school_id if necessary."""
    is_own_schedule = session.get('is_own_schedule')
    print(f"Checking schedule status: {is_own_schedule}")

    # Only proceed if user is working with their own schedule
    if is_own_schedule == 1:
        try:
            # Establish database connection
            with sqlite3.connect('user_data.db') as conn:
                cursor = conn.cursor()
                user_id = session.get('user_id')
                new_school_id = session.get('school_id')

                if user_id is None or new_school_id is None:
                    print("Missing user_id or school_id2 in session")
                    return

                # Retrieve current school_id from database
                cursor.execute("SELECT school_id FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()

                if result is None:
                    print(f"No user found with user_id: {user_id}")
                    return

                current_school_id = result[0]
                session['stored_school_id'] = current_school_id

                # Check and update school_id if necessary
                if current_school_id != new_school_id:
                    print(f"Mismatch found: current school_id {current_school_id}, new school_id {new_school_id}")
                    cursor.execute("UPDATE users SET school_id = ? WHERE user_id = ?", (new_school_id, user_id))
                    conn.commit()
                    print(f"Updated school_id for user_id {user_id} to {new_school_id}")
                else:
                    print("No update needed for school_id.")

        except sqlite3.Error as e:
            print(f"SQLite error while updating user school_id: {e}")
        except Exception as e:
            print(f"Unexpected error updating user school_id: {e}")


def is_own_school():
    try:
        # Retrieve school_id from the session
        user_id = session.get('user_id')
        current_school_id = session.get('school_id')
        if current_school_id is None:
            print("No school_id found in session")
            session['is_own_school'] = 0
            return 0

        # Connect to the database and check if the school_id exists in the users table
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT school_id FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        stored_school_id = result[0]
        if current_school_id == stored_school_id:
            session['is_own_school'] = 1
            return 1
        else:
            session['is_own_school'] = 0
            return 0

    except Exception as e:
        print(f"Error in is_own_school: {e}")
        session['is_own_school'] = 0
        return 0

