def format_time(value):
    """Format time strings to HH:MM without dates or seconds."""
    try:
        if isinstance(value, str) and ":" in value:
            hours, minutes = value.split(":")[:2]
            return f"{int(hours):02d}:{int(minutes):02d}"
        return value  # Return as-is if not a valid time string
    except Exception as e:
        return value  # Fallback in case of errors
