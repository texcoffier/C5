"""
Base class for compiler
"""

COURSE_OPTIONS = {}

def onmessage(event):
    """Evaluate immediatly the function if in the worker"""
    if event.data.splice:
        if event.data[0] == 'goto':
            Compile.worker.goto(event.data[1])
        elif event.data[0] == 'array':
            Compile.worker.shared_buffer = event.data[1]
        elif event.data[0] == 'source':
            Compile.worker.questions[event.data[1]].last_answer = event.data[2]
            Compile.worker.source = event.data[2]
        elif event.data[0] == 'indent':
            Compile.worker.run_indent(event.data[1])
        elif event.data[0] == 'config':
            init_needed = len(Compile.worker.options) == 0
            Compile.worker.set_config(event.data[1])
            if init_needed:
                Compile.worker.start_question()
                Compile.worker.init()
                print("Worker: init done. current_question_max=",
                      Compile.worker.current_question_max)

    else:
        if Compile.worker.shared_buffer:
            Compile.worker.shared_buffer[0] = 0
        Compile.worker.run(event.data.toString())

class Compile: # pylint: disable=too-many-instance-attributes,too-many-public-methods
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
    stop_after_compile = True
    previous_source = None
    shared_buffer = []
    current_question_max = 0
    run_tester_after_exec = True
    options = {}
    default_options = {} # Default options for the compiler can be defined here

    def __init__(self, questions):
        print("Worker: start")
        Compile.worker = self
        self.questions = questions
        self.allow_tip = True
        self.allow_goto = True

    def init(self):
        """Your own compiler init, for example:

             self.popup('Hello!')
        """

    def set_options(self, options):
        """Set course options and send them"""
        for key in options:
            self.options[key] = options[key]

    def send_options(self):
        """Send current options to the GUI"""
        self.post('options', self.options)

    def popup(self, message):
        """Display a popup (only one per load)"""
        self.post('eval', 'ccccc.popup(' + JSON.stringify(message) + ')')

    def set_config(self, config):
        """Record config, update old question answer, jump to the last question"""
        for key in config:
            if key not in self.options:
                self.options[key] = config[key]
        self.set_options(self.options)
        self.send_options()
        for question in self.options['ANSWERS']:
            question = Number(question)
            if self.questions[question] and self.options['ANSWERS'][question]:
                self.questions[question].last_answer = self.options['ANSWERS'][question][0]
                if question >= self.current_question and self.options['ANSWERS'][question][1]:
                    if self.questions[question + 1]:
                        # Only if not after the last question
                        self.current_question_max = question + 1
        for i, quest in enumerate(self.questions):
            quest.worker = self
            self.post('default', [i, quest.default_answer()])
        self.current_question = self.current_question_max
        if self.current_question != 0 or self.questions[self.current_question].last_answer:
            self.source = (self.questions[self.current_question].last_answer
                           or self.questions[self.current_question].default_answer())
            self.start_question()

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
                self.start_time = millisecs()
                self.source = source
                self.post('compiler', self.compiler_initial_content())
                self.executable = self.run_compiler(source)
                if self.executable:
                    self.run_after_compile()
        finally:
            if self.stop_after_compile:
                self.post('state', "stopped")

    def run_after_compile(self):
        """If the compilation was successful, run the execution"""
        self.execution_result = ''
        self.execution_returns = None
        self.post('executor', self.executor_initial_content())
        self.post('state', "running")
        self.run_executor()
        self.post('tester', self.tester_initial_content())
        if self.run_tester_after_exec:
            self.run_tester()
        self.post('time', self.time_initial_content())

    def run_compiler(self, _source): # pylint: disable=no-self-use
        """Do the compilation"""
        self.post('compile', 'No compiler defined')
        return 'No compiler defined'
    def run_executor(self): # pylint: disable=no-self-use
        """Do the execution"""
        self.post('run', 'No executor defined')
    def run_indent(self, _source):
        """Indent the source"""
        self.post('run', 'No indenter defined')
    def start_question(self):
        """Start a new question"""
        # print("START QUESTION", self.current_question, '/', self.current_question_max)
        if self.current_question < 0:
            return
        self.post('current_question', self.current_question)
        self.post('allow_edit', '0')
        if self.quest:
            self.quest.last_answer = self.source
        if self.current_question > self.current_question_max:
            self.current_question_max = self.current_question
        self.quest = self.questions[self.current_question]
        if self.quest and hasattr(self.quest, 'last_answer'):
            self.source = self.quest.last_answer
        else:
            self.source = self.quest.default_answer()
        self.previous_source += 'force recompilation'
        self.post('question', self.question_initial_content())
        self.post('question', self.quest.question())
        self.post('index', self.index_initial_content())
        self.send_options()
        self.post('editor', self.source)
        self.post('allow_edit', '1')

    def goto(self, question):
        """Change question"""
        self.current_question = question
        self.start_question()
    def run_tester(self):
        """Do the regression tests"""
        current_question = self.current_question
        self.quest.all_tests_are_fine = True
        try:
            self.quest.tester()
        except:
            print("Il y a un bug dans le testeur de la question " + current_question)
            self.current_question = current_question # Keep same question
            return
        if (current_question != self.current_question # Question has been solved now
                and not self.question_yet_solved(current_question)
           ):
            self.post("good", self.source)
            self.options['ANSWERS'][current_question] = [self.source, 1]
            self.start_question()
        else:
            self.current_question = current_question # Keep same question

    def question_yet_solved(self, question):
        """Return True if the current question has been correctly answered"""
        # print(question, self.options['ANSWERS'])
        if not self.options['ANSWERS'][question]:
            return False
        return self.options['ANSWERS'][question][1]

    def read_input(self, hide=False):
        """Ask the webpage some input text, wait the answer."""
        if not self.shared_buffer:
            return "SharedArrayBuffer not allowed by HTTP server"
        if not hide:
            self.post('executor', '\001\002INPUT\001')
        self.post('state', "input")
        while self.shared_buffer[0] == 0:
            Atomics.wait(self.shared_buffer, 0, 0, 100) # pylint: disable=undefined-variable
        self.post('state', "inputdone")
        if self.shared_buffer[0] == 2:
            self.post('state', "stopped")
            return '\000KILL'
            # raise ValueError('canceled')
        string = ''
        for i in self.shared_buffer[1:]:
            if i > 0:
                string += String.fromCharCode(i) # pylint: disable=undefined-variable
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
        return html(text)

    ###########################################################################

    def question_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        title = '<h2>' + self.options['question_title']
        if not self.options['GRADING'] and self.options['checkpoint'] and not self.options['feedback']:
            title += (' <tt id="stop_button" class="stop_button" onclick="ccccc.stop()">'
                + self.options['icon_stop'] + '</tt>')
        if not self.options['GRADING'] and self.options['display_timer'] and not self.options['feedback']:
            title += ' <div class="timer"><span id="timer"></span>⏱</div>'
        title += '</h2>'
        return title
    def tester_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "<h2>" + self.options['tester_title'] + "</h2>"
    def executor_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        if self.options['positions'] and (
                self.options['positions']['compiler'][0] >= 100
                or self.options['positions']['compiler'][2] >= 100
                ) and self.options['display_compile_run']:
            more = (' <label onclick="ccccc.user_compilation=true;ccccc.compilation_run()">'
                    + self.options['executor_title_button'] + '</label>')
        else:
            more = ''
        more += '<span ondblclick="ccccc.send_mail()" style="float:right; background: #CCF; margin-right: 0.3em;">'
        if self.options['GRADING']:
            more += (
            '<a style="font-family:emoji;text-decoration:none" href="mailto:'
            + self.options['INFOS']['mail']
            + '?subject=' + self.options['COURSE']
            # + '&amp;body=Bonjour.%0A%0AVotre devoir corrigé : '
            # + self.options['BASE XXX'] + '/=' + self.options['COURSE']
            # + '%0A%0ACordialement.'
            + '">✉</a>'
            )
        # Keep <!-- --> explanation is in ccccc.py
        # about : The first space is replaced by an unsecable space
        return ("<h2><!-- -->" + self.options['executor_title']
            + more
            + '<tt class="truncate_sn">' + self.options['INFOS']['sn'].upper() + '</tt>'
            + ' '
            + '<tt class="truncate_fn">' + self.options['INFOS']['fn'].lower() + '</tt>'
            + "</span></h2>")
    def compiler_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        if self.options['automatic_compilation']:
            more = ('<label type="checkbox" id="automatic_compilation" '
                    + ' onclick="ccccc.compilation_toggle(this)"'
                    + ' class="checked">'
                    + self.options['compiler_title_toggle'] + '</label>')
        else:
            if self.options['display_compile_run']:
                more = ('<label onclick="ccccc.user_compilation=true;ccccc.compilation_run()">'
                        + self.options['compiler_title_button'] + '</label>')
            else:
                more = ''
        return ('<h2>' + self.options['compiler_title'] + ' '
                + more + '</h2>')
    def time_initial_content(self):
        """The message terminate the job. It indicates the worker time"""
        more = ' ' + self.current_question_max
        if self.allow_goto:
            more += 'G'
        return '#' + self.nr_eval + ' ' + (millisecs() - self.start_time) + 'ms' + more
    def index_initial_content(self):
        """Used by the subclass"""
        texts = ['<style></style>']
        tips = []
        for i, _ in enumerate(self.questions):
            if self.allow_goto:
                link = 'onclick="ccccc.goto_question(' + i + ')"'
            else:
                link = ''
            html_class = []
            if i == self.current_question:
                html_class.append('current')
                link = 'onclick="ccccc.record([\'click-same\'])"'
            if self.question_yet_solved(i):
                html_class.append('good')
            else:
                if (i <= self.current_question_max
                        or not self.options['sequential']
                        or self.options['GRADING']
                        or self.options['ANSWERS'][i]):
                    html_class.append('possible')
                else:
                    link = ''
            if self.allow_tip:
                tips.append('<div>' + self.escape(self.questions[i].__doc__) + '</div>')
            texts.append('<div class="' + ' '.join(html_class) + '" ' + link + '>'
                + str(i+1) + '</div>')
        return ('<div class="questions"><div class="tips">' + ''.join(tips) + '</div>'
            + ''.join(texts) + '</div>')
