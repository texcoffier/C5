"""
Base class for compiler
"""

def onmessage(event):
    """Evaluate immediatly the function if in the worker"""
    if event.data.splice:
        if event.data[0] == 'goto':
            Compile.worker.goto(event.data[1])
        elif event.data[0] == 'array':
            Compile.worker.shared_buffer = event.data[1]
    else:
        if Compile.worker.shared_buffer:
            Compile.worker.shared_buffer[0] = 0
        Compile.worker.run(event.data.toString())

class Compile: # pylint: disable=too-many-instance-attributes
    """Create the GUI and launch worker"""
    questions = []
    current_question = 0
    quest = None
    source = None
    executable = None
    execution_result = None
    execution_returns = None
    nr_eval = 0
    start_time = None
    language = 'javascript'
    stop_after_compile = True
    previous_source = None

    def __init__(self, questions):
        print("Worker: start")
        Compile.worker = self
        self.questions = questions
        self.allow_tip = True
        self.allow_goto = True
        for quest in questions:
            quest.worker = self
        if '127.0.0.1' in str(location): # pylint: disable=undefined-variable
            self.current_question_max = len(questions)
        else:
            self.current_question_max = 0
        self.start_question()
        self.post('language', self.language)
        print("Worker: init done. current_question_max=", self.current_question_max)

    def disable_goto(self):
        """Call to disable goto"""
        self.allow_goto = False

    def disable_tip(self):
        """Call to disable index tips"""
        self.allow_tip = False

    def run(self, source):
        """Get the source code and do all the jobs"""
        self.post('state', "started")
        try:
            if source == self.previous_source:
                self.run_after_compile()
            else:
                self.previous_source = source
                self.nr_eval += 1
                self.start_time = self.millisecs()
                self.source = source
                self.post('compiler', self.compiler_initial_content())
                self.executable = self.run_compiler(source)
                if self.executable:
                    self.run_after_compile()
        finally:
            if self.stop_after_compile:
                self.post('state', "stopped")

    def run_after_compile(self):
        self.execution_result = ''
        self.execution_returns = None
        self.post('executor', self.executor_initial_content())
        self.run_executor()
        self.post('tester', self.tester_initial_content())
        self.run_tester()
        self.post('time', self.time_initial_content())

    def millisecs(self):  # pylint: disable=no-self-use
        """Current time in milli seconds"""
        return Date().getTime() # pylint: disable=undefined-variable

    def run_compiler(self, _source): # pylint: disable=no-self-use
        """Do the compilation"""
        self.post('compile', 'No compiler defined')
        return 'No compiler defined'
    def run_executor(self): # pylint: disable=no-self-use
        """Do the execution"""
        self.post('run', 'No executor defined')
    def start_question(self):
        """Start a new question"""
        if self.quest:
            self.quest.last_answer = self.source
        if self.current_question > self.current_question_max:
            self.current_question_max = self.current_question
        self.quest = self.questions[self.current_question]
        self.post('current_question', self.current_question)
        if hasattr(self.quest, 'last_answer'):
            self.post('editor', self.quest.last_answer)
        else:
            self.post('editor', self.quest.default_answer())
        self.post('question', self.question_initial_content())
        self.post('question', self.quest.question())
        self.post('index', self.index_initial_content())
    def goto(self, question):
        """Change question"""
        if question > self.current_question_max:
            return
        self.current_question = question
        self.start_question()
    def run_tester(self):
        """Do the regression tests"""
        current_question = self.current_question
        self.quest.all_tests_are_fine = True
        self.quest.tester()
        if current_question != self.current_question and self.current_question != self.current_question_max:
            self.post("good", "")
            if current_question == self.current_question_max - 1:
                self.start_question()


    def read_input(self):
        if not self.shared_buffer:
            return "SharedArrayBuffer not allowed by HTTP server"
        self.post('executor', '\000INPUT')
        self.post('state', "input")
        while self.shared_buffer[0] == 0:
            Atomics.wait(self.shared_buffer, 0, 0, 100)
        self.post('state', "inputdone")
        if self.shared_buffer[0] == 2:
            raise ValueError('canceled')
        string = ''
        for i in self.shared_buffer[1:]:
            if i > 0:
                string += String.fromCharCode(i)
            elif i < 0:
                break
        self.shared_buffer[0] = 0
        return string

    ###########################################################################

    def post(self, destination, message): # pylint: disable=no-self-use
        """Send a message to a worker"""
        postMessage([destination, message]) # pylint: disable=undefined-variable

    def escape(self, text): # pylint: disable=no-self-use
        """Escape HTML chars"""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    ###########################################################################

    def question_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "<h2>Question</h2>"
    def tester_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "<h2>Les buts de vous devez atteindre</h2>"
    def executor_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "<h2>Exécution</h2>"
    def compiler_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "<h2>Compilation</h2>"
    def time_initial_content(self):
        """The message terminate the job. It indicates the worker time"""
        return '#' + self.nr_eval + ' ' + (self.millisecs() - self.start_time) + 'ms'
    def index_initial_content(self): # pylint: disable=no-self-use,invalid-name
        """Used by the subclass"""
        texts = '''<style></style>'''
        tips = []
        for i, _ in enumerate(self.questions):
            if self.allow_goto:
                link = ' onclick="ccccc.unlock_worker();ccccc.worker.postMessage([\'goto\',' + i + '])"'
            else:
                link = ''
            if i == self.current_question:
                attr = ' class="current"'
            elif i <= self.current_question_max:
                attr = ' class="possible"'
            else:
                attr = ''
                link = ''
            if self.allow_tip:
                tips.append('<div>' + self.escape(self.questions[i].__doc__) + '</div>')
            texts += '<div' + attr + link + '>' + str(i+1) + '</div>'
        return '<div class="i">' + tips.join('') + '</div>' + texts  # pylint: disable=no-member
