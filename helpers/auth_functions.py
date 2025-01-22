import sqlite3

def get_db_connection():
    """Establish and return a database connection."""
    connection = sqlite3.connect('user_data.db')  
    connection.row_factory = sqlite3.Row  
    return connection
