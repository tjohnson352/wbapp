# these functions are used to code the school and teacher names

import base64

# Function to generate an alphanumeric ID that can be decoded
# Base64 encode a combined string of school_name and full_name using '|' as separator
def generate_unique_id(full_name):
    # Encode the combined string to base64
    unique_id = base64.urlsafe_b64encode(full_name.encode()).decode('utf-8')
    return unique_id

# Function to decode the unique ID back to the original combined string
def decode_unique_id(unique_id):
    decoded_string = base64.urlsafe_b64decode(unique_id.encode()).decode('utf-8')
    return decoded_string