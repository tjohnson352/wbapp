import os

class Config:
    SECRET_KEY = os.urandom(24)
    # Add database configuration here if needed
