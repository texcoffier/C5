"""
Functions common to Python and Javascript
"""

def normalize_login(login):
    """In order to have a uniq login string"""
    return login.lower()

def normalize_logins(logins):
    """Normalize logins in a string with separators [ \n\t]"""
    result = ''
    login = ''
    for char in logins:
        if char in ' \n\t':
            result += normalize_login(login) + char
            login = ''
        else:
            login += char
    return result + normalize_login(login)

def student_id(login):
    """Returns the student ID"""
    return login
