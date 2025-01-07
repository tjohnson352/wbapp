import sqlite3
import pandas as pd
from flask import session
from io import StringIO


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

        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            school_name TEXT,
            user_name TEXT,
            id TEXT PRIMARY KEY,
            UNIQUE(school_name, user_name)
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
        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()

        # Retrieve data from session
        id = session.get('id', 'Unknown')

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
        id = session.get('id', None)
        if not id:
            raise ValueError("ID is missing from the session")

        conn = sqlite3.connect("user_data.db")
        cursor = conn.cursor()

        # Fetch meta1 data
        cursor.execute("SELECT * FROM meta1 WHERE id = ?", (id,))
        meta1 = cursor.fetchone()

        # Fetch meta2 data
        cursor.execute("SELECT * FROM meta2 WHERE id = ?", (id,))
        meta2 = cursor.fetchone()

        # Fetch schedule_string
        cursor.execute("SELECT schedule_string FROM schedule WHERE id = ?", (id,))
        schedule_string = cursor.fetchone()

        conn.close()

        return {
            'meta1': meta1,
            'meta2': meta2,
            'schedule_string': schedule_string[0] if schedule_string else None
        }

    except Exception as e:
        print(f"Error retrieving user data: {e}")
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
