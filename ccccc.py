#!/usr/bin/python3
# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,self-assigning-variable

"""
To simplify the class contains the code for the GUI and the worker.

CCCCC       is the top class (mostly running GUI side)
CCCCC_JS    is a subclass for compiling and interpreting javascript (worker side)
CCCCC_JS_1  is a subclass defining an exercice

The interface send to the worker the source code to compile and execute
with the method: «self.worker.postMessage»

The worker return one of these answers with the «postMessage» function:
  * ['compile', 'compilation result']
  * ['run', 'execution result']
  * ['tester', 'regtest results']


TODO : tester function

"""

# Hide pylint warnings
try:
    window = window
    document = document
    postMessage = postMessage
    Object = Object
    Array = Array
    RegExp = RegExp
    Date = Date
    setInterval = setInterval
    @external
    class Worker: # pylint: disable=function-redefined,too-few-public-methods
        """Needed for rapydscript"""
        def postMessage(self, _message):
            """Send a message to the worker"""
except:  # pylint: disable=bare-except
    pass

try:
    # pylint: disable=undefined-variable,missing-docstring,too-few-public-methods
    str(42)
    in_python = True
    in_worker = False
    Error = None
    def bind(fct, _obj):
        """Bind the function to the object"""
        return fct
    class Worker: # pylint: disable=function-redefined
        """JS compatibility"""
        def postMessage(self, _message):
            """Send a message to the worker"""
except: # pylint: disable=bare-except,redefined-builtin
    in_python = False
    in_worker = not window or not window.document or not document
    def str(txt):
        """Python like"""
        return txt.toString()
    def bind(fct, _obj):
        """Bind the function to the object: nothing to do in Python"""
        return fct
    Object.defineProperty(Array.prototype, 'append',
                          {'enumerable': False, 'value': Array.prototype.push})

def html(txt):
    """Protect text to display it in HTML"""
    return str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def millisecs():
    """Current time in milli seconds"""
    return Date().getTime()

def new_element(htmltype, htmlclass, left, width, top, height, background):
    """Create a DOM element"""
    e = document.createElement(htmltype)
    e.className = htmlclass
    e.style.position = 'absolute'
    e.style.left = left + '%'
    e.style.right = (100 - left - width) + '%'
    e.style.top = top + '%'
    e.style.bottom = (100 - top - height) + '%'
    e.style.background = background
    e.style.overflow = 'auto'
    return e

class CCCCC: # pylint: disable=too-many-public-methods
    """Create the GUI and launch worker"""
    question_width = 30
    question_height = 30
    source_width = 40
    compiler_height = 30
    question = editor = tester = compiler = executor = time = None # HTML elements
    executable = None # Compilation result (worker side)
    top = None # Top page HTML element
    source = None # The source code to compile
    execution_result = None # The result of the execution (what is displayed)
    routes = None # The message routes
    start_time = None # Start time of the evaluation
    nr_eval = 0
    messages = {}
    old_source = ''

    def __init__(self):
        self.worker = None
        if not in_worker:
            self.worker = Worker('xxx-ccccc.js')
            self.worker.onmessage = bind(self.onmessage, self)
            self.worker.onmessageerror = bind(self.onmessage, self)
            self.worker.onerror = bind(self.onmessage, self)
            setInterval(bind(self.scheduler, self), 200)

    def create_question(self):
        """The question text container: course and exercise"""
        e = new_element('DIV', 'question',
                        0, self.question_width,
                        0, self.question_height,
                        '#EFE')
        self.question = e
        e.innerHTML = self.question_initial_content() + self.run_question()
        self.top.appendChild(e)

    def create_tester(self):
        """The regression test container"""
        e = new_element('DIV', 'regtests',
                        0, self.question_width,
                        self.question_height, 100 - self.question_height,
                        '#EFE')
        self.tester = e
        self.top.appendChild(e)

    def create_editor(self):
        """The text editor container"""
        e = new_element('DIV', 'editor',
                        self.question_width, self.source_width,
                        0, 100,
                        '#FFF')
        e.contentEditable = True
        self.editor = e
        self.top.appendChild(e)
        self.editor.innerText = self.editor_initial_content()
        self.editor.focus()
        document.getSelection().collapse(self.editor, self.editor.childNodes.length)

    def create_compiler(self):
        """The compiler result container"""
        e = new_element('DIV', 'compiler',
                        self.question_width + self.source_width,
                        100 - self.question_width - self.source_width,
                        0, self.compiler_height,
                        '#EEF')
        self.compiler = e
        self.top.appendChild(e)

    def create_executor(self):
        """The execution result container"""
        e = new_element('DIV', 'executor',
                        self.question_width + self.source_width,
                        100 - self.question_width - self.source_width,
                        self.compiler_height, 100 - self.compiler_height,
                        '#EEF')
        self.executor = e
        self.top.appendChild(e)

    def create_time(self):
        """The worker time displayer"""
        e = new_element('DIV', 'time', 90, 10, 98, 2, '#0000')
        self.time = e
        self.top.appendChild(e)

    def run(self, source):
        """This method runs in the worker"""
        start_time = millisecs()
        self.source = source
        self.executable = self.run_compiler(source)
        postMessage(['run', None])
        postMessage(['tester', None])
        self.execution_result = ''
        if self.executable:
            self.run_executor([])
        self.run_tester([])
        postMessage(['time', (millisecs() - start_time) + 'ms'])

    def scheduler(self):
        """Send a new job if free and update the screen"""
        for k in self.messages:
            self.routes[k][0].innerHTML = self.messages[k]
        if not self.start_time:
            source = self.editor.innerText
            if source != self.old_source:
                self.old_source = source # Do not recompile the same thing
                self.start_time = millisecs()
                self.worker.postMessage(source) # Start compile/execute/test
                self.nr_eval += 1
                self.messages = {}

    def onmousedown(self, event):
        """Mouse down"""
        self.editor.focus()
        event.preventDefault(True)
    def onkeydown(self, event): # pylint: disable=no-self-use
        """Key down"""
        if event.key == 'Tab':
            event.preventDefault(True)
    def onkeyup(self, _event):
        """Key up"""
    def onkeypress(self, event):
        """Key press"""
    def onmessage(self, event):
        """Interprete messages from the worker: update self.messages"""
        what = event.data[0]
        if self.messages[what]:
            self.messages[what] += event.data[1]
        else:
            self.messages[what] = self.routes[what][1](event.data[1])

    def create_html(self):
        """Create the page content"""
        self.top = document.createElement('DIV')
        self.top.onmousedown = bind(self.onmousedown, self)
        self.top.onkeydown = bind(self.onkeydown, self)
        self.top.onkeyup = bind(self.onkeyup, self)
        self.top.onkeypress = bind(self.onkeypress, self)
        document.getElementsByTagName('BODY')[0].appendChild(self.top)
        self.create_question()
        self.create_tester()
        self.create_editor()
        self.create_compiler()
        self.create_executor()
        self.create_time()
        # pylint: disable=bad-whitespace
        self.routes = {
            'run'    : [self.executor, bind(self.executor_initial_content, self)],
            'compile': [self.compiler, bind(self.compiler_initial_content, self)],
            'tester' : [self.tester  , bind(self.tester_initial_content  , self)],
            'time'   : [self.time    , bind(self.time_initial_content    , self)],
        }

    def question_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "<h2>Question</h2>"
    def editor_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "// Saisissez votre programme au dessous (souris interdite) :\n\n"
    def compiler_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "<h2>Compilation</h2>"
    def executor_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "<h2>Exécution</h2>"
    def tester_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "<h2>Les buts de vous devez atteindre</h2>"
    def time_initial_content(self, t):
        """The message terminate the job. It indicates the worker time"""
        t = '#' + self.nr_eval + ' ' + (millisecs() - self.start_time) + 'ms ' +  t
        self.start_time = None # To allow a new job
        return t

    def run_compiler(self, _source): # pylint: disable=no-self-use
        """Do the compilation"""
        postMessage(['compile', 'No compiler defined'])
        return 'No compiler defined'
    def run_executor(self, _args): # pylint: disable=no-self-use
        """Do the execution"""
        postMessage(['run', 'No executor defined'])
    def run_tester(self, _args): # pylint: disable=no-self-use
        """Do the regression tests"""
        postMessage(['tester', 'No tester defined'])
    def run_question(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "No question defined"
    def display(self, message):
        postMessage(['tester', message])
    def check(self, text, needle_message):
        """Append a message in 'output' for each needle_message"""
        for needle, message in needle_message:
            if text.match(RegExp(needle)):
                html_class = 'test_ok'
            else:
                html_class = 'test_bad'
            self.display('<li class="' + html_class + '">' + message + '</li>')

class CCCCC_JS(CCCCC):
    """JavaScript compiler and evaluator"""
    execution_result = ''

    def run_compiler(self, source):
        postMessage(['compile', None])
        try:
            # pylint: disable=eval-used
            f = eval('''function _tmp_(args)
            {
               function print(txt)
                  {
                     if ( txt )
                        {
                          ccccc.execution_result += txt ;
                          txt = html(txt) ;
                        }
                     else
                          txt = '' ;
                     postMessage(['run', txt + '\\n']) ;
                 } ;
            ''' + source + '} ; _tmp_')
            postMessage(['compile', 'Compilation sans erreur'])
            return f
        except Error as err:
            postMessage(['compile',
                         '<error>'
                         + html(err.name) + '\n' + html(err.message)
                         + '</error>'])
    def run_executor(self, args):
        try:
            self.executable(args)
        except Error as err:
            postMessage(['run', '<error>'
                         + html(err.name) + '\n'
                         + html(err.message) + '</error>'])
