#!/usr/bin/python3
# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes

"""
To simplify the class contains the code for the GUI and the worker.

CCCCC       is the top class (mostly running GUI side)
CCCCC_JS    is a subclass for compiling and interpreting javascript (worker side)
CCCCC_JS_1  is a subclass defining an exercice

TODO : tester function

"""


try:
    # pylint: disable=undefined-variable,missing-docstring,too-few-public-methods
    print(str("Python"))
    in_python = True
    window = window
    document = document
    postMessage = postMessage
    Error = None
    @external
    class Worker:
        def postMessage(self, _message):
            pass
    def bind(fct, obj):
        """Bind the function to the object"""
        return fct.bind(obj)
except: # pylint: disable=bare-except,redefined-builtin
    in_python = False
    def str(txt):
        """Python like"""
        return txt.toString()
    def bind(fct, _obj):
        """Bind the function to the object: nothing to do in Python"""
        return fct

try:
    print(window.location)
    in_browser = True
except: # pylint: disable=bare-except
    in_browser = False

def html(txt):
    """Protect text to display it in HTML"""
    return str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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

class CCCCC:
    """Create the GUI and launch worker"""
    question_width = 30
    question_height = 30
    source_width = 40
    compiler_height = 30
    question = editor = tester = compiler = executor = None # HTML elements
    executable = None # Compilation result (worker side)
    top = None # Top page HTML element

    def __init__(self):
        self.worker = None
        if in_browser:
            self.worker = Worker('xxx-ccccc.js')
            self.worker.onmessage = bind(self.onmessage, self)
            self.worker.onmessageerror = bind(self.onmessage, self)
            self.worker.onerror = bind(self.onmessage, self)
            print(self.worker)

    def create_question(self):
        """The question text container: course and exercise"""
        e = new_element('DIV', 'question',
                        0, self.question_width,
                        0, self.question_height,
                        '#CFC')
        self.question = e
        e.innerHTML = self.question_initial_content()
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
        self.editor.focus()

    def create_compiler(self):
        """The compiler result container"""
        e = new_element('DIV', 'compiler',
                        self.question_width + self.source_width,
                        100 - self.question_width - self.source_width,
                        0, self.compiler_height,
                        '#CCF')
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

    def run(self, source):
        """This method runs in the worker"""
        self.executable = self.run_compiler(source)
        postMessage(['run', None])
        if self.executable:
            self.run_executor([])
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
        self.worker.postMessage(self.editor.textContent)
    def onkeypress(self, event):
        """Key press"""
        pass
    def onmessage(self, event):
        """Interprete messages from the worker"""
        if event.data[0] == 'run':
            e = self.executor
        else:
            e = self.compiler
        if event.data[1] is None:
            if event.data[0] == 'run':
                e.innerHTML = self.executor_initial_content()
            else:
                e.innerHTML = self.compiler_initial_content()
        else:
            e.innerHTML += event.data[1]

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

    def compiler_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "RESULTAT DE LA COMPILATION<hr>"
    def executor_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "RESULTAT DE L'EXÉCUTION<hr>"
    def question_initial_content(self): # pylint: disable=no-self-use
        """Used by the subclass"""
        return "Please redefined this function"
    def run_compiler(self, _source): # pylint: disable=no-self-use
        """Do the compilation"""
        postMessage(['compile', 'No compiler defined'])
    def run_executor(self, _args): # pylint: disable=no-self-use
        """Do the execution"""
        postMessage(['run', 'No executor defined'])

class CCCCC_JS(CCCCC):
    """JavaScript compiler and evaluator"""
    def run_compiler(self, source):
        postMessage(['compile', None])
        try:
            # pylint: disable=eval-used
            f = eval('''function _tmp_(args)
            {
               function print(txt)
                  {
                     if ( txt )
                          txt = html(txt) ;
                     else
                          txt = '' ;
                     postMessage(['run', txt + '<br>']) ;
                 } ;
            ''' + source + '} ; _tmp_')
            postMessage(['compile', 'Compilation sans erreur'])
            return f
        except Error as err:
            postMessage(['compile',
                         '<error>'
                         + html(err.name) + '<br>\n' + html(err.message)
                         + '</error>'])
    def run_executor(self, args):
        try:
            self.executable(args)
        except Error as err:
            postMessage(['run', '<error>'
                         + html(err.name) + '<br>\n'
                         + html(err.message) + '</error>'])

class CCCCC_JS_1(CCCCC_JS):
    """First exercise"""
    def question_initial_content(self):
        return """Pour afficher quelque chose, on tape :
<pre>
print(la_chose_a_afficher) ;
</pre>

<p>
Saisissez dans le zone blanche le programme qui affiche le nombre 42.
        """

ccccc = CCCCC_JS_1()

if in_browser:
    ccccc.create_html()
else:
    def onmessage(event):
        """Evaluate immediatly the function if in the worker"""
        ccccc.run(event.data.toString())

print("ok")
