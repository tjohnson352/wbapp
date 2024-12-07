# Function to assign 'type' based on substring
def assign_activity_type(df2a_activities):
    # Ensure df2_activities is a string
    if not isinstance(df2a_activities, str):
        return ''  # or an appropriate default value
    
    # Define substrings and their corresponding types
    type_mapping = [
        ('meet', 'GENERAL/DUTY'),
        ('tutorial', 'GENERAL/DUTY'),
        ('break', 'BREAK'),
        ('Mentor', 'GENERAL/DUTY'),
        ('cover', 'TEACHING'),
        ('sub', 'TEACHING'),
        ('hall', 'GENERAL/DUTY'),
        ('lunch', 'GENERAL/DUTY')
    ]
    
    # Iterate through type mapping and return corresponding activity type
    for substring, activity_type in type_mapping:
        if substring.lower() in df2a_activities.lower():
            return activity_type
            
    # Default return value if no match is found
    return 'TEACHING'  # or 'UNKNOWN', depending on what you need
