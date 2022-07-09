 # pylint: disable=undefined-variable
"""
Question base class
"""
class Question:
    """A question"""
    all_tests_are_fine = True
    def __init__(self):
        self.worker = None
        self.__doc__ = self.__doc__ # Fix RapydScript problem
    def display(self, message):
        """Display the message in the student feedback"""
        self.worker.post('tester', message)
    def message(self, is_fine, txt):
        """Display the message in the tester"""
        if is_fine:
            html_class = 'test_ok'
        else:
            html_class = 'test_bad'
            self.all_tests_are_fine = False
        self.display(
            '<li class="' + html_class + '">' + txt + '</li>')
    def check(self, text, needle_message):
        """Append a message in 'output' for each needle_message"""
        for needle, message in needle_message:
            self.message(text.match(RegExp(needle)), message)
    def set_question(self, index):
        """Change question"""
        self.worker.current_question = index
    def set_options(self, options):
        """Change options"""
        self.worker.set_options(options)
    def next_question(self):
        """Next question"""
        self.set_question(self.worker.current_question + 1)
    def question(self):
        """Display the question"""
        self.display("No test defined")
    def default_answer(self): # pylint: disable=no-self-use
        """The initial edit content"""
        return "// Saisissez votre programme au dessous :\n\n\n"
    def tester(self):
        """Test worker.source and worker.execution_result"""
        self.display("No test defined")
    def append_to_source_code(self): # pylint: disable=no-self-use
        """Add this to the user source code"""
        return ""
