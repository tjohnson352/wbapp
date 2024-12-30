# these functions are used to code the school and teacher names

import base64
from flask import session
import pandas as pd
from cryptography.fernet import Fernet

# Save the key securely and use it for encryption/decryption
key = b'MxidiEHZyR17Q00eGem1T0Q0ya01MAfvgnck3-Z6hxM='
cipher = Fernet(base64.urlsafe_b64encode(key[:32]))  # Use only the first 32 bytes of the key


def encrypt():
    """
    Encrypt the combined name from the session using the app's secret key
    and save the encrypted name back into the session.
    """
    try:
        # Read combined_name from session
        combined_name = session.get('combined_name', None)

        # Ensure combined_name exists
        if not combined_name:
            raise ValueError("Combined name is missing from the session")

        # Encrypt the combined name
        encrypted_name = cipher.encrypt(combined_name.encode())

        # Save encrypted name back into the session
        session['encrypted_name'] = encrypted_name.decode()  # Store as a string for JSON compatibility

        return encrypted_name.decode()  # Return the encrypted name
    except Exception as e:
        print(f"Error during encryption: {e}")
        return None

def decrypt():
    """
    Read the encrypted name from the session, decrypt it using the app's secret key,
    and save the decrypted name back into the session.
    """
    try:
        # Read encrypted_name from session
        encrypted_name = session.get('encrypted_name', None)

        # Ensure encrypted_name exists
        if not encrypted_name:
            raise ValueError("Encrypted name is missing from the session")

        # Decrypt the encrypted name
        decrypted_name = cipher.decrypt(encrypted_name.encode()).decode()  # Convert to plain text

        # Save the decrypted name back into the session
        session['decrypted_name'] = decrypted_name

        return decrypted_name  # Return the decrypted name
    except Exception as e:
        print(f"Error during decryption: {e}")
        return None


