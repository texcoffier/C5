 # pylint: disable=undefined-variable
"""
Question base class
"""
class Question:
    """A question"""
    all_tests_are_fine = True
    to_test = []
    to_test_index = 0
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
        if index < len(self.worker.questions):
            self.worker.current_question = index
    def set_options(self, options):
        """Change options"""
        self.worker.set_options(options)
    def next_question(self):
        """Next question"""
        self.set_question(self.worker.current_question + 1)
    def question(self):
        """Display the question"""
        self.display("No question defined")
    def default_answer(self): # pylint: disable=no-self-use
        """The initial edit content"""
        return "// Saisissez votre programme au dessous :\n\n\n"
    def tester(self):
        """Test worker.source and worker.execution_result"""
        self.display("No test defined")
    def expectations(self):
        """
        If the function returns an empty list of tests
        then 'tester' is called one the first execution is done.

        The returned list of test may contains items of these types:
            ['EXIT', "a message.", a_boolean_function],
                   The parameter contain process exit informations and files.
            ['IN'  , "a message.", a_string_function],
                   The process input is feed with the returned string 
            ['OUT' , "a message.", a_boolean_function],
                   The parameter contains a chunk of the process output.
            ['MSG' , "a message (not to be colored)"],

        All the messages are displayed BEFORE starting the execution.
        The messages are green tagged on True return (red on False).
        On False return: self.all_tests_are_fine = False

        self.next_question() is called if final EXIT keeps all_tests_are_fine True.
        """
        return []
    def mark(self, i, good):
        t = '<style>#test-' + i + ":before {"
        if good:
            t += "content:'☑'; color: #080"
        else:
            t += "content:'☒'; color: #F00"
            self.all_tests_are_fine = False
        t += '}</style>'
        self.display(t)
    def next_test(self):
        while True:
            self.to_test_index += 1
            if not self.to_test[self.to_test_index]:
                return None
            if self.to_test[self.to_test_index][0] != 'MSG':
                return self.to_test[self.to_test_index]
    def get_test(self):
        return self.all_tests_are_fine and self.to_test[self.to_test_index]
    def tester_realtime_init(self):
        """
        Initialize realtime tester.
        For example display the future tests in gray and color then later.
        Use « self.display() » to display
        """
        self.to_test = self.expectations()
        self.to_test_index = 0
        t = ["""
            <style>
            LI.tester { display: block; }
            LI.tester:before { content: '☐'; ;margin-right: 0.5em }
            </style>
            """]
        for i, test in enumerate(self.to_test):
            what = test[0]
            if what == 'MSG':
                t.append('<p id="test-' + i + '">' + test[1])
            elif what in ('IN', 'OUT', 'EXIT'):
                t.append('<li id="test-' + i + '" class="tester">' + test[1])
            else:
                alert('Bug: ' + what)
        self.worker.post('tester', ''.join(t))
        return
    def tester_realtime_exit(self, phase, nr_inputs, data):
        """The process stopped.
        'data' contains the exit informations.
        """
        if len(self.to_test) == 0:
            self.worker.run_tester()
            return
        test = self.get_test()
        if not test:
            return
        if test[0] == 'EXIT':
            self.mark(self.to_test_index, test[2](data))
            if self.next_test():
                self.next_phase()
            else:
                if self.all_tests_are_fine:
                    self.next_question()
            return
        if test[0] == 'IN' and phase != 0:
            self.mark(self.to_test_index, False)
    def tester_realtime_input(self, phase, nr_inputs):
        """The process asks an input, this function return the value to provide.
        'nr_inputs' start at 0.
        """
        test = self.get_test()
        if not test:
            return 'no input defined in «tester»'
        if test[0] == 'IN':
            self.mark(self.to_test_index, True)
            value = test[2]()
            self.next_test()
            return value
        if test[0] == 'OUT':
            self.next_test()
            return 'no input defined in «tester»'
        if test[0] == 'EXIT' and phase != 0:
            self.mark(self.to_test_index, False)
    def tester_realtime_display(self, phase, nr_input, string):
        """'string' is the data sent by the process"""
        test = self.get_test()
        if not test:
            return
        if test[0] == 'OUT':
            self.mark(self.to_test_index, test[2](string))
            test = self.next_test()
            if test[0] == 'OUT':
                self.tester_realtime_display(phase, nr_input, string)
            return
        if test[0] == 'EXIT' and phase != 0:
            self.mark(self.to_test_index, False)

    def expected_answer(self):
        """For grader and may be student"""
        return ''
    def grading_ladder(self):
        """For grader and may be student"""
        return ''
    def append_to_source_code(self): # pylint: disable=no-self-use
        """Add this to the user source code"""
        return ""
    def placement(self):
        """Return [Building, coord_x, coord_y]"""
        building, coord_x, coord_y = self.worker.options.WHERE[2].split(',')[:3]
        return (building, int(coord_x), int(coord_y))
    def version(self):
        """Return 'a' or 'b'"""
        return self.worker.options.WHERE[2].split(',')[3] or 'a'
    def teacher(self):
        """Room managing Teacher"""
        return self.worker.options.WHERE[1]
    def next_phase(self):
        """Start a new execution"""
        self.worker.nr_input = 0
        self.worker.restart()

def LOAD_QUESTION(filename):
    return "LOAD_QUESTION(" + filename + ") # Missing file"
def LOAD_DEFAULT(filename):
    return "LOAD_DEFAULT(" + filename + ") # Missing file"
def LOAD_GRADING(filename):
    return "LOAD_GRADING(" + filename + ") # Missing file"
def LOAD_ANSWER(filename):
    return "LOAD_ANSWER(" + filename + ") # Missing file"
