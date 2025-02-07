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

        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,  -- user_id will match the user_id in user_auth
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            login_id TEXT UNIQUE NOT NULL,  -- login_id corresponds to the email address
            school_id INTEGER NOT NULL,
            consent BOOLEAN NOT NULL CHECK (consent IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(school_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)
        

        # Create user_auth table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_auth (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Autoincrement ID for authentication
            login_id TEXT UNIQUE NOT NULL,  -- Login ID (email address)
            password_hash TEXT NOT NULL,
            security_question_1 TEXT NOT NULL,
            security_answer_1 TEXT NOT NULL,
            security_question_2 TEXT NOT NULL,
            security_answer_2 TEXT NOT NULL,
            security_question_3 TEXT NOT NULL,
            security_answer_3 TEXT NOT NULL,
            question_index INTEGER DEFAULT 0,
            login_attempts INTEGER DEFAULT 0,
            temp_password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE

        );
        """)

        # Create sl_member_level table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sl_member_level (
            user_id INTEGER PRIMARY KEY,  -- Make user_id the primary key
            sl_member INTEGER DEFAULT 0,
            lokalombud INTEGER DEFAULT 0,
            skyddsombud INTEGER DEFAULT 0,
            forhandlingsombud INTEGER DEFAULT 0,
            huvudskyddsombud INTEGER DEFAULT 0,
            styrelseledamot INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)

        # Create verify_officer table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS verify_officer (
            user_id INTEGER PRIMARY KEY,  -- Make user_id the primary key
            lokalombud INTEGER DEFAULT 0,
            skyddsombud INTEGER DEFAULT 0,
            forhandlingsombud INTEGER DEFAULT 0,
            huvudskyddsombud INTEGER DEFAULT 0,
            styrelseledamot INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,  -- 0 = Not verified, 1 = Verified
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)

        
        # Create meta1 table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta1 (
            user_id INTEGER PRIMARY KEY,  -- user_id matches user_auth.user_id
            school_name TEXT,
            middle_manager TEXT,
            ft_days TEXT,
            off_days TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
                       
        """)
        # Create reset_tokens table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """)

        # Create meta2 table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta2 (
            user_id INTEGER PRIMARY KEY,  -- user_id matches user_auth.user_id
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
            total_overtime REAL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)

        # Create schedule table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            user_id INTEGER PRIMARY KEY,  -- user_id matches user_auth.user_id
            schedule_string TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)

        # Create schools table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schools (
            school_id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT UNIQUE NOT NULL
        );
        """)

        # Create survey_responses table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS survey_responses (
            user_id INTEGER PRIMARY KEY,  -- user_id matches user_auth.user_id
            review_q1 TEXT NOT NULL,
            review_q2 INTEGER NOT NULL,
            review_q3 TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)

        # Commit changes and close connection
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
        # Ensure session contains the required 'user_id'
        user_id = session.get('user_id')
        if not user_id:
            raise ValueError("Session user_id is missing or invalid.")

        # Connect to the database
        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()

        # Save meta1 data
        cursor.execute("""
        INSERT OR REPLACE INTO meta1 (user_id, school_name, middle_manager, ft_days, off_days)
        VALUES (?, ?, ?, ?, ?);
        """, (
            user_id,
            session.get('school_name', 'Unknown'),
            session.get('middle_manager', 'No'),
            session.get('ft_days', 'Unknown'),
            session.get('off_days', 'Unknown')
        ))

        # Save meta2 data
        cursor.execute("""
        INSERT OR REPLACE INTO meta2 (
            user_id, work_percent, planning_time, frametime_issue_count, gap_issues_count, 
            breaks_time, general_time, contract_teachtime, assigned_teachtime, 
            contract_frametime, assigned_frametime, over_teachtime, over_frametime, 
            total_overtime
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            user_id,
            session.get('work_percent', 0),
            session.get('planning_time', 0.0),
            session.get('frametime_issue_count', 0),
            session.get('gap_issues_count', 0),
            session.get('breaks_time', 0.0),
            session.get('general_time', 0.0),
            session.get('contract_teachtime', 0.0),
            session.get('assigned_teachtime', 0.0),
            session.get('contract_frametime', 0.0),
            session.get('assigned_frametime', 0.0),
            session.get('over_teachtime', 0.0),
            session.get('over_frametime', 0.0),
            session.get('total_overtime', 0.0)
        ))

        # Save schedule_string if available
        schedule_string = session.get('schedule_string', '')
        if schedule_string:
            cursor.execute("""
            INSERT OR REPLACE INTO schedule (user_id, schedule_string)
            VALUES (?, ?);
            """, (user_id, schedule_string))

        # Commit changes and close connection
        conn.commit()
        conn.close()
        print("User data saved successfully.")

    except ValueError as ve:
        print(f"Validation Error: {ve}")
    except sqlite3.Error as se:
        print(f"SQLite Error: {se}")
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

        # Display the content of each table
        for table_name, in tables:
            print(f"\nContents of table '{table_name}':")
            df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
            
            if df.empty:
                print("--- E M P T Y ---")
            else:
                print(df)


        conn.close()

    except Exception as e:
        print(f"Error viewing database: {e}")


def get_user_data():
    """
    Retrieve user data from SQLite database using the user_id stored in the session.
    """
    try:
        # Retrieve user_id from session and validate
        user_id = session.get('user_id')
        if not user_id:
            raise ValueError("user_id is missing from the session")
        if not isinstance(user_id, int):
            raise ValueError("Invalid user_id format in the session")

        # Connect to the database
        with sqlite3.connect("user_data.db") as conn:
            cursor = conn.cursor()

            # Fetch meta1 data
            cursor.execute("SELECT * FROM meta1 WHERE user_id = ?", (user_id,))
            meta1 = cursor.fetchone()

            # Fetch meta2 data
            cursor.execute("SELECT * FROM meta2 WHERE user_id = ?", (user_id,))
            meta2 = cursor.fetchone()

            # Fetch schedule_string
            cursor.execute("SELECT schedule_string FROM schedule WHERE user_id = ?", (user_id,))
            schedule = cursor.fetchone()

        # Return results as a structured dictionary
        return {
            'meta1': meta1 if meta1 else None,
            'meta2': meta2 if meta2 else None,
            'schedule_string': schedule[0] if schedule else None
        }

    except ValueError as e:
        # Handle missing or invalid user_id gracefully
        logging.error(f"Validation Error: {e}")
        return None
    except sqlite3.Error as db_error:
        # Handle database-related errors
        logging.error(f"Database Error: {db_error}")
        return None
    except Exception as e:
        # Log unexpected errors
        logging.error(f"Unexpected Error: {e}")
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
