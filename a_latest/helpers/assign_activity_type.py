# Function to assign 'type' based on substring
def assign_activity_type(df1a):
    # Define substrings and their corresponding types
    type_mapping = [
        ("meeting", "GENERAL"),
        ("tutorial", "GENERAL"),
        ("break", "BREAK"),
        ("cover", "TEACHING"),
        ("hall", "GENERAL"),
        ("sub", "TEACHING")
    ]
    
    # Create a new column 'type' initialized with None
    df1a["type"] = None
    
    # Assign values to 'type' based on the presence of substrings in 'activities' (case insensitive)
    for substring, activity_type in type_mapping:
        df1a.loc[df1a["activities"].str.contains(substring, case=False, na=False), "type"] = activity_type
    
    return df1a
