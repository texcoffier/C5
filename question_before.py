
def millisecs():
    return 0

PREAMBLE = ''

class Session:
    def __init__(self, questions):
        question_classes.clear()
        for question in questions:
            question_classes.append(question.__class__)

question_classes = []
class Question:
    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        question_classes.append(cls)

