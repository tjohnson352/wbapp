import os

def load_schools():
    """
    Load school names from the school_list.txt file with proper encoding.
    """
    school_list_path = os.path.join(os.getcwd(), "helpers/school_list.txt")
    try:
        print(f"Looking for school_list.txt at: {school_list_path}")
        # Open the file with UTF-8 encoding
        with open(school_list_path, "r", encoding="utf-8") as file:
            schools = [line.strip() for line in file if line.strip()]
        print(f"Loaded schools: {schools}")
        return schools
    except FileNotFoundError:
        print(f"Error: {school_list_path} was not found.")
        return []
    except Exception as e:
        print(f"Error loading schools: {e}")
        return []
