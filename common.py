"""
Functions common to Python and Javascript

Overwrittable by xxx_local.py
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



POSSIBLE_GRADES = ":([?],)?[-0-9,.]+$"

try:
    import re
    re_match = re.match
    def re_sub(pattern, replacement, string):
        """Only first replacement"""
        return re.sub(pattern, replacement, string, 1)
except: # pylint: disable=bare-except
    def re_match(pattern, string):
        """As in Python"""
        return string.match(RegExp('^' + pattern))
    def re_sub(pattern, replacement, string):
        """Only first replacement"""
        return string.replace(RegExp(pattern), replacement)


def parse_notation(notation):
    """Returns a list or [text, grade_label, [grade_values]]"""
    content = []
    text = ''
    for i, item in enumerate(notation.split('{')):
        options = item.split('}')
        if len(options) == 1 or not re_match('.*' + POSSIBLE_GRADES, options[0]):
            if i != 0:
                text += '{'
            text += item
            continue
        grade_label = re_sub(POSSIBLE_GRADES, '', options[0])
        grade_values = re_sub('.*:', '', options[0]).split(',')
        content.append([text, grade_label, grade_values])
        text = '}'.join(options[1:])
    content.append([text, '', []])
    return content
