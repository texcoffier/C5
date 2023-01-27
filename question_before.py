
"""
Helper to create 'COMPILE_.../session.json' file containing questionnary information.
"""

def millisecs():
    """Fake"""
    return 0

PREAMBLE = ''

class Session: # pylint: disable=too-few-public-methods
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
