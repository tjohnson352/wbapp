import sqlite3
import os
import pandas as pd
from flask import session
from io import StringIO
import logging

def setup_database():
    """
    Set up the SQLite database and create tables only if they do not already exist.
    """
    try:
        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()

        # Create meta1 table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta1 (
            id TEXT PRIMARY KEY,
            school_name TEXT,
            middle_manager TEXT,
            ft_days TEXT,
            off_days TEXT
        );
        """)

        # Create meta2 table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta2 (
            id TEXT PRIMARY KEY,
            work_percent INTEGER,
            planning_time REAL,
            frametime_issue_count INTEGER,
            gap_issues_count INTEGER,
            breaks_time REAL,
            general_time REAL,
            contract_teachtime REAL,
            assigned_teachtime REAL,
            contract_frametime REAL,
            assigned_frametime REAL,
            over_teachtime REAL,
            over_frametime REAL,
            total_overtime REAL
        );
        """)

        # Create schedule table (simplified with id and schedule_string)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id TEXT PRIMARY KEY,
            schedule_string TEXT
        );
        """)

        # Create schools table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schools (
            school_id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT UNIQUE NOT NULL
        );
        """)

        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            school_id INTEGER NOT NULL,
            consent BOOLEAN NOT NULL CHECK (consent IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(school_id)
        );
        """)

        # Create auth user_auth
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_auth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            password_hash TEXT NOT NULL,
            security_question_1 TEXT NOT NULL,
            security_answer_1 TEXT NOT NULL,
            security_question_2 TEXT NOT NULL,
            security_answer_2 TEXT NOT NULL,
            security_question_3 TEXT NOT NULL,
            security_answer_3 TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_users_updated_at
        AFTER UPDATE ON users
        FOR EACH ROW
        BEGIN
            UPDATE users
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = OLD.id;
        END;
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS survey_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_q1 TEXT NOT NULL,
            review_q2 INTEGER NOT NULL,
            review_q3 TEXT
        );
        """)

        conn.commit()
        conn.close()
        print("Database setup completed successfully.")

    except Exception as e:
        print(f"Error setting up database: {e}")

def save_user_data():
    """
    Save user data from session into SQLite database.
    """
    try:
        # Ensure session contains the required 'id'
        id = session.get('id')
        if not id:
            raise ValueError("Session ID is missing or invalid.")

        # Connect to the database
        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()

        # Save meta1 data
        cursor.execute("""
        INSERT OR REPLACE INTO meta1 (id, school_name, middle_manager, ft_days, off_days)
        VALUES (?, ?, ?, ?, ?);
        """, (
            id,
            session.get('school_name', 'Unknown'),
            session.get('middle_manager', 'No'),
            session.get('ft_days', 'Unknown'),
            session.get('off_days', 'Unknown')
        ))

        # Save meta2 data
        cursor.execute("""
        INSERT OR REPLACE INTO meta2 (
            id, work_percent, planning_time, frametime_issue_count, gap_issues_count, 
            breaks_time, general_time, contract_teachtime, assigned_teachtime, 
            contract_frametime, assigned_frametime, over_teachtime, over_frametime, 
            total_overtime
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            id,
            session.get('work_percent', 0),
            session.get('planning_time', 0.0),
            session.get('frametime_issue_count', 0),
            session.get('gap_issues_count', 0),
            session.get('breaks', 0.0),
            session.get('general', 0.0),
            session.get('contract_teachtime', 0.0),
            session.get('assigned_teachtime', 0.0),
            session.get('contract_frametime', 0.0),
            session.get('assigned_frametime', 0.0),
            session.get('over_teachtime', 0.0),
            session.get('over_framtime', 0.0),
            session.get('total_overtime', 0.0)
        ))

        # Save schedule_string
        schedule_string = session.get('schedule_string', '')
        if schedule_string:
            cursor.execute("""
            INSERT OR REPLACE INTO schedule (id, schedule_string)
            VALUES (?, ?);
            """, (id, schedule_string))

        conn.commit()
        conn.close()
        print("User data saved successfully.")

    except Exception as e:
        print(f"Error saving user data: {e}")

def view_database():
    """
    View the contents of all tables in the SQLite database.
    """
    try:
        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in the database:", tables)

        # Display the content of each table
        for table_name, in tables:
            print(f"\nContents of table '{table_name}':")
            df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
            print(df)

        conn.close()

    except Exception as e:
        print(f"Error viewing database: {e}")


def get_user_data():
    """
    Retrieve user data from SQLite database using the id stored in the session.
    """
    try:
        # Retrieve ID from session and validate
        id = session.get('id')
        if not id:
            raise ValueError("ID is missing from the session")
        if not isinstance(id, str):
            raise ValueError("Invalid ID format in the session")

        # Connect to the database
        with sqlite3.connect("user_data.db") as conn:
            cursor = conn.cursor()

            # Fetch meta1 data
            cursor.execute("SELECT * FROM meta1 WHERE id = ?", (id,))
            meta1 = cursor.fetchone()

            # Fetch meta2 data
            cursor.execute("SELECT * FROM meta2 WHERE id = ?", (id,))
            meta2 = cursor.fetchone()

            # Fetch schedule_string
            cursor.execute("SELECT schedule_string FROM schedule WHERE id = ?", (id,))
            schedule = cursor.fetchone()

        # Return results as a structured dictionary
        return {
            'meta1': meta1 if meta1 else None,
            'meta2': meta2 if meta2 else None,
            'schedule_string': schedule[0] if schedule else None
        }

    except ValueError as e:
        # Handle missing or invalid ID gracefully
        logging.error(f"Validation Error: {e}")
        return None
    except Exception as e:
        # Log unexpected errors
        logging.error(f"Error retrieving user data: {e}")
        return None

def clear_all_tables():
    """
    Delete all tables from the SQLite database.
    """
    try:
        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()

        # Fetch all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Drop each table
        for table_name, in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            print(f"Dropped table: {table_name}")

        conn.commit()
        conn.close()
        print("All tables deleted successfully.")

    except Exception as e:
        print(f"Error deleting tables: {e}")

def save_review():
    """
    Save review responses stored in the session to the database.
    Assumes the session contains 'review_q1', 'review_q2', and 'review_q3'.
    """
    try:
        # Retrieve responses from session
        review_q1 = session.get('review_q1', None)
        review_q2 = session.get('review_q2', None)
        review_q3 = session.get('review_q3', "")  # Optional field

        # Ensure required fields are present
        if not review_q1 or not review_q2:
            raise ValueError("Required review fields are missing.")

        # Connect to the database and insert the review
        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO survey_responses (review_q1, review_q2, review_q3)
            VALUES (?, ?, ?)
        """, (review_q1, review_q2, review_q3))
        conn.commit()
        conn.close()

        print("Review saved successfully.")

    except Exception as e:
        print(f"Error saving review: {e}")


def setup_school_table():
    """
    Create the schools table and populate it with names from school_list.txt.
    Only add new schools that are not already in the table.
    Existing school_id values for existing schools will not be changed.
    """
    try:
        # Construct the absolute path to the school_list.txt file
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the current script
        school_list_path = os.path.join(base_dir, "school_list.txt")

        # Check if the file exists
        if not os.path.exists(school_list_path):
            raise FileNotFoundError(f"{school_list_path} not found. Please ensure the file exists.")

        # Read school names from the file with UTF-8 encoding
        with open(school_list_path, "r", encoding="utf-8") as file:
            school_names = [line.strip() for line in file.readlines() if line.strip()]

        # Connect to the database
        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()

        # Create the schools table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schools (
            school_id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT UNIQUE NOT NULL
        );
        """)

        # Get the existing school names from the database
        cursor.execute("SELECT school_name FROM schools;")
        existing_schools = {row[0] for row in cursor.fetchall()}

        # Identify new schools to add
        new_schools = [school for school in school_names if school not in existing_schools]

        # Insert only the new schools
        for school_name in new_schools:
            try:
                cursor.execute("INSERT INTO schools (school_name) VALUES (?);", (school_name,))
            except sqlite3.IntegrityError as e:
                print(f"Error inserting school: {school_name} - {e}")

        conn.commit()
        conn.close()

        print("Schools table created and updated successfully.")
        print(f"New schools added: {len(new_schools)}")

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

        print(f"Error setting up schools table: {e}")
