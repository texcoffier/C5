
"""
Helper to create 'COMPILE_.../session.json' file containing questionnary information.
"""

def millisecs():
    """Fake"""
    return 0

PREAMBLE = ''

def load(filename):
    try:
        with open(f'SRC/{filename}', 'r', encoding='utf-8')  as file:
            return file.read()
    except FileNotFoundError:
        return ''

LOAD_GRADING = load
class Session(Session): # pylint: disable=too-few-public-methods
    """Create a session with all the questions"""
    def __init__(self, questions):
        question_classes.clear()
        for question in questions:
            question_classes.append(question.__class__)

question_classes = []
class Question: # pylint: disable=too-few-public-methods
    """Create the list of created question."""
    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        question_classes.append(cls)
    def grading_ladder(self):
        return ''
    def version(self):
        return self._version
