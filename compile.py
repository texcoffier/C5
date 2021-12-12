"""
Base class for compiler
"""

def onmessage(event):
    """Evaluate immediatly the function if in the worker"""
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

    def __init__(self, questions):
        print("Worker: start")
        Compile.worker = self
        self.questions = questions
        for quest in questions:
            quest.worker = self
        self.start_question()
        print("Worker: init done")

    def run(self, source):
        """Get the source code and do all the jobs"""
        self.nr_eval += 1
        self.start_time = self.millisecs()
        self.source = source
        self.post('compiler', self.compiler_initial_content())
        self.executable = self.run_compiler(source)
        self.execution_result = ''
        self.execution_returns = None
        self.post('executor', self.executor_initial_content())
        if self.executable:
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
        self.quest = self.questions[self.current_question]
        self.post('editor', self.quest.default_answer())
        self.post('question', self.question_initial_content())
        self.post('question', self.quest.question())
        self.post('index', self.index_initial_content())
    def run_tester(self):
        """Do the regression tests"""
        current_question = self.current_question
        self.quest.tester()
        if current_question != self.current_question:
            self.start_question()

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
        texts = ''
        for i, _ in enumerate(self.questions):
            if i < self.current_question:
                attr = ' class="done"'
            elif i == self.current_question:
                attr = ' class="current"'
            else:
                attr = ''
            texts += '<div' + attr + '>' + str(i+1) + '</div>'
        return texts
