"""
Redefine for customizing C5
"""

def normalize_login(login):
    """In order to have a uniq login string"""
    if login:
        login = login.lower()
        # Special case for Lyon 1
        if login[0] == '1':
            return 'p' + login[1:]
        return login
    return ''

def student_id(login):
    """Returns the student ID"""
    if login[0] == 'p':
        return '1' + login[1:]
    return login
