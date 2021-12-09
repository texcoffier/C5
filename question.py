# pymlint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,self-assigning-variable

"""
Question base class
"""
class Question:
    """Define question and expected result"""
    def __init__(self):
        self.worker = None
    def display(self, message): # pylint: disable=no-self-use
        """Display the message in the student feedback"""
        postMessage(['tester', message])
    def check(self, text, needle_message):
        """Append a message in 'output' for each needle_message"""
        results = []
        for needle, message in needle_message:
            if text.match(RegExp(needle)):
                html_class = 'test_ok'
            else:
                html_class = 'test_bad'
            results.append(html_class)
            self.display('<li class="' + html_class + '">' + message + '</li>')
        return results
    def set_question(self, index):
        """Change question"""
        self.worker.current_question = index
        self.worker.quest = self.worker.questions[self.worker.current_question]
    def next_question(self):
        """Next question"""
        self.set_question(self.worker.current_question + 1)

    def question(self):
        """Display the question"""
        self.display("No test defined")
    def default_answer(self): # pylint: disable=no-self-use
        """The initial edit content"""
        return "// Saisissez votre programme au dessous (souris interdite) :\n\n"
    def tester(self):
        """Test worker.source and worker.execution_result"""
        self.display("No test defined")
