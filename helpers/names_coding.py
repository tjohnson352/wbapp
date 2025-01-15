import pandas as pd
from collections import Counter
from flask import session
import regex as re
from io import StringIO
import sqlite3
import random
import string

def generate_id():
    """
    Generate a random 10-character string using uppercase letters and numbers.
    """
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

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


def db_save_user_into():
        
    school_name = session['school_name']
    full_name = session['full_name']

    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Check if the combination of school_name and full_name already exists
    cursor.execute("""
    SELECT id FROM users WHERE school_name = ? AND user_name = ?;
    """, (school_name, full_name))
    existing_record = cursor.fetchone()

    if existing_record:
        # Use the existing ID
        id = existing_record[0]
    else:
        # Generate a new ID and insert it into the database
        id = generate_id()
        cursor.execute("""
        INSERT INTO users (school_name, user_name, id)
        VALUES (?, ?, ?);
        """, (school_name, full_name, id))

    conn.commit()
    conn.close()

    # Save data to the session
    session['id'] = id

    print("User data processed and saved successfully.")


def decrypt():
    """
    Retrieve the school name and user name from the database using the given id from the session.
    """
    try:
        # Read the ID from the session
        id = session.get('id', None)

        # Ensure the ID exists in the session
        if not id:
            raise ValueError("ID is missing from the session.")

        # Query the database for school_name and user_name
        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()
        cursor.execute("""
        SELECT school_name, user_name FROM users WHERE id = ?;
        """, (id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            school_name, user_name = result
            print(f"Found record: School Name: {school_name}, User Name: {user_name}")
            return {
                "school_name": school_name,
                "user_name": user_name,
                "id": id
            }
        else:
            raise ValueError(f"No record found for ID: {id}")

    except Exception as e:
        print(f"Error finding name by ID: {e}")
        return None
