from flask import request

def collect_frametime_input(request):
    """
    Collects and validates frametime data from the frontend.

    Args:
        request: Flask request object containing POST data.

    Returns:
        A list of dictionaries with day, start_time, and end_time.
    """
    try:
        frametime_data = request.get_json().get('frametime', [])
        validated_data = []

        for entry in frametime_data:
            day = entry.get('day')
            start_time = entry.get('start_time')
            end_time = entry.get('end_time')

            # Validate day, start_time, and end_time
            if not day or not start_time or not end_time:
                raise ValueError(f"Invalid frametime entry: {entry}")

            validated_data.append({
                'day': day,
                'start_time': start_time,
                'end_time': end_time
            })

        return validated_data

    except Exception as e:
        raise ValueError(f"Error collecting frametime input: {e}")
