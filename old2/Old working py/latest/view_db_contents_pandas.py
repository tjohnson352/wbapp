import sqlite3
import pandas as pd

# List of database files to be checked
database_files = ["database.db", "permanent_files.db", "temporary_files.db"]

def view_database_contents(db_file):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Get the list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if tables:
            print(f"\nContents of {db_file}:\n" + "-"*50)
            for table_name in tables:
                table_name = table_name[0]
                print(f"\nTable: {table_name}\n" + "-"*25)
                
                # Load the table into a Pandas DataFrame
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                
                # Display the table using Pandas
                print(df.to_string(index=False))  # Display without the index column
                
                print("\n")
        else:
            print(f"\n{db_file} has no tables.")

        # Close the connection
        conn.close()

    except sqlite3.Error as e:
        print(f"An error occurred while connecting to {db_file}: {e}")

if __name__ == "__main__":
    for db_file in database_files:
        view_database_contents(db_file)
