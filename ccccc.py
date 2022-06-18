# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,self-assigning-variable

"""
To simplify the class contains the code for the GUI and the worker.

CCCCC       class manages the GUI
            It sends source code to the Compile worker with sendMessage
            It receives events to update the GUI
Compile     worker base class to manage the question list, compilation, execution
Compile_JS  subclass for Javascript compiler
Compile_CPP subclass for C++ compiler
Question    base class for question definition
"""

def html(txt):
    return txt.replace(RegExp('&', 'g'), '&amp;').replace(RegExp('<', 'g'), '&lt;').replace(RegExp('>', 'g'), '&gt;')

# Hide pylint warnings
try:
    document = document
    setInterval = setInterval
    setTimeout = setTimeout
    bind = bind
    hljs = hljs
    window = window
    @external
    class Worker: # pylint: disable=function-redefined,too-few-public-methods
        """Needed for rapydscript"""
        def postMessage(self, _message):
            """Send a message to the worker"""
except: # pylint: disable=bare-except
    pass

def popup_message(txt):
    """OK popup with the message"""
    alert(txt) # pylint: disable=undefined-variable

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
    e.background = background
    return e

class CCCCC: # pylint: disable=too-many-public-methods
    """Create the GUI and launch worker"""
    question_width = 30
    question_height = 30
    source_width = 40
    compiler_height = 30
    question = editor = overlay = tester = compiler = executor = time = index = None # HTML elements
    top = None # Top page HTML element
    source = None # The source code to compile
    messages = {'time': 1}
    messages_previous = {}
    old_source = None
    first_time = True
    language = 'javascript' # For highlighting
    oldScrollTop = None

    def __init__(self):
        print("GUI: start")
        if window.location.hash:
            course = window.location.hash.substr(1)
        else:
            course = 'course_js.js'
        self.worker = Worker(course)
        self.worker.onmessage = bind(self.onmessage, self)
        self.worker.onmessageerror = bind(self.onmessage, self)
        self.worker.onerror = bind(self.onmessage, self)
        setInterval(bind(self.scheduler, self), 200)
        self.create_html()
        print("GUI: init done")

    def create_question(self):
        """The question text container: course and exercise"""
        e = new_element('DIV', 'question',
                        1, self.question_width - 1,
                        0, self.question_height,
                        '#EFE')
        self.question = e
        self.top.appendChild(e)

    def create_tester(self):
        """The regression test container"""
        e = new_element('DIV', 'regtests',
                        1, self.question_width - 1,
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
        e.spellcheck = False
        e.autocorrect = False
        e.autocapitalize = False
        e.autocomplete = False
        e.onscroll = bind(self.onscroll, self)

        self.editor = e
        self.top.appendChild(e)
        self.editor.focus()
        # The overlay with coloring
        e = new_element('DIV', 'overlay',
                        self.question_width, self.source_width,
                        0, 100,
                        '#0000')
        self.overlay = e
        self.top.appendChild(e)

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

    def create_index(self):
        """The question list displayer"""
        e = new_element('DIV', 'index', 0, 1, 0, 100, '#0000')
        self.index = e
        self.top.appendChild(e)

    def scheduler(self):
        """Send a new job if free and update the screen"""
        if 'time' not in self.messages:
            return # Compiler is running

        for k in ['tester', 'executor', 'compiler', 'time', 'editor', 'question', 'index']:
            message = self.messages[k]
            if not message and message != '':
                continue
            if k == 'editor':
                # New question
                if self.first_time:
                    self.first_time = False
                else:
                    popup_message('Bravo !')
                # Many \n at the bug (browser problem when inserting a final \n)
                message += '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n'
                self.overlay_hide()
                self.editor.innerText = message
                self.editor.scrollTop = 0
                # document.getSelection().collapse(self.editor, self.editor.childNodes.length)
                self.coloring()
            elif self.messages_previous[k] != message:
                element = self[k] # pylint: disable=unsubscriptable-object
                element.innerHTML = message
                if '<error' in message:
                    element.style.background = '#FAA'
                else:
                    element.style.background = element.background
                self.messages_previous[k] = message

        source = self.editor.innerText
        if source != self.old_source:
            self.old_source = source # Do not recompile the same thing
            self.worker.postMessage(source) # Start compile/execute/test
            self.messages = {}

    def overlay_hide(self):
        """The editor and the overlay are no synchronized"""
        self.overlay.style.visibility = 'hidden'
    def overlay_show(self):
        """The editor and the overlay are synched"""
        self.onscroll()
        self.overlay.style.visibility = 'visible'
    def coloring(self):
        """Coloring of the text editor with an overlay."""
        self.overlay.innerHTML = html(self.editor.innerText)
        self.overlay.className = 'overlay language-' + self.language
        hljs.highlightElement(self.overlay)
        self.overlay_show()
    def onmousedown(self, _event):
        """Mouse down"""
        self.editor.focus()
    def onpaste(self, event):
        """Mouse down"""
        if (event.clipboardData or event.dataTransfer).getData("text") in self.editor.innerText:
            self.overlay_hide()
            setTimeout(bind(self.coloring, self), 100)
            return # auto paste allowed
        popup_message("Interdit !")
        event.preventDefault(True)
    def onkeydown(self, event):
        """Key down"""
        if event.key == 'Tab':
            document.execCommand('insertHTML', False, '    ')
            event.preventDefault(True)
        elif event.key == 'Enter' and event.target is self.editor:
            # Fix Firefox misbehavior
            self.oldScrollTop = self.editor.scrollTop
            # Do not want <br> inserted, so prevent default
            document.execCommand('insertHTML', False, '\n')
            event.preventDefault(True)
        elif len(event.key) > 1 and event.key not in ('Delete', 'Backspace'):
            return # Do not hide overlay: its only a cursor move
        self.overlay_hide()
    def onkeyup(self, event):
        """Key up"""
        if event.key not in ('Left', 'Right', 'Up', 'Down'):
            self.coloring()
    def onkeypress(self, event):
        """Key press"""
    def onscroll(self, _event=None):
        """To synchronize syntax highlighting"""
        if self.oldScrollTop is not None:
            # Fix Firefox misbehavior
            self.editor.scrollTop = self.oldScrollTop
            self.oldScrollTop = None
        else:
            self.overlay.scrollTop = self.editor.scrollTop
    def onmessage(self, event):
        """Interprete messages from the worker: update self.messages"""
        what = event.data[0]
        if what == 'language':
            self.language = event.data[1]
            return
        if what == 'first_time':
            self.first_time = True
            return
        if what not in self.messages:
            self.messages[what] = ''
        self.messages[what] += event.data[1]

    def create_html(self):
        """Create the page content"""
        self.top = document.createElement('DIV')
        self.top.onmousedown = bind(self.onmousedown, self)
        self.top.onpaste = bind(self.onpaste, self)
        self.top.ondrop = bind(self.onpaste, self)
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
        self.create_index()

ccccc = CCCCC()
