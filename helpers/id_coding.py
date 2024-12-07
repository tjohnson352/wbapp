# these functions are used to code the school and teacher names

import base64

def generate_unique_id(last_name, first_name, school_name):
    """
    Generate a Base64 encoded ID from the school name, last name, and first name.

    Args:
        last_name (str): Last name.
        first_name (str): First name.
        school_name (str): School name.

    Returns:
        str: Base64 encoded unique ID.
    """
    combined_name = school_name + ": " + last_name + ", " + first_name
    unique_id = base64.urlsafe_b64encode(combined_name.encode()).decode('utf-8')
    return unique_id

def decode_unique_id(unique_id):
    """
    Decode the Base64 encoded ID back to the original string.

    Args:
        unique_id (str): Base64 encoded ID.

    Returns:
        str: Original combined string.
    """
    decoded_string = base64.urlsafe_b64decode(unique_id.encode()).decode('utf-8')
    return decoded_string
