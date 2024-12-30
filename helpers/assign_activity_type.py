def assign_activity_type(df2a_activities):
    # Ensure df2_activities is a string
    if not isinstance(df2a_activities, str):
        return ''  # or an appropriate default value
    
    # Load type mappings from file
    file_path = './helpers/activity_type_mapping.txt'
    type_mapping = []
    try:
        with open(file_path, 'r') as file:
            current_type = None
            for line in file:
                line = line.strip()
                if line.endswith(':'):
                    current_type = line[:-1]  # Remove colon
                elif current_type and line:
                    substrings = [item.strip() for item in line.split(',')]
                    type_mapping.extend((substring, current_type) for substring in substrings)
                elif line == "":
                    current_type = None
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return 'ERROR'

    # Iterate through type mapping and return corresponding activity type
    for substring, activity_type in type_mapping:
        if substring.lower() in df2a_activities.lower():
            return activity_type
    
    return 'Teaching'  # or 'UNKNOWN', depending on what you need
