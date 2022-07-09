# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,self-assigning-variable

"""
To simplify the class contains the code for the GUI and the worker.

CCCCC          class manages the GUI
               It sends source code to the Compile worker with sendMessage
               It receives events to update the GUI
Compile        worker base class to manage the question list, compilation, execution
Compile_JS     subclass for Javascript compiler
Compile_CPP    subclass for C++ compiler
Compile_remote subclass for remote compiling
Question       base class for question definition
"""

def html(txt):
    """Escape < > &"""
    # pylint: disable=undefined-variable
    return txt.replace(RegExp('&', 'g'), '&amp;'
                      ).replace(RegExp('<', 'g'), '&lt;'
                               ).replace(RegExp('>', 'g'), '&gt;')


# Hide pylint warnings
try:
    document = document
    setInterval = setInterval
    setTimeout = setTimeout
    Number = Number
    bind = bind
    hljs = hljs
    window = window
    confirm = confirm
    Date = Date
    Math = Math
    JSON = JSON
    LOGIN = LOGIN
    ANSWERS = ANSWERS
    TICKET = TICKET
    ADMIN = ADMIN
    SOCK = SOCK
    STOP = STOP
    encodeURIComponent = encodeURIComponent
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

def two_digit(number):
    """ 6 → 06 """
    return ('0' + str(int(number)))[-2:]

def do_post_data(dictionary, url, target=None):
    """POST a dictionnary"""
    form = document.createElement("form")
    form.setAttribute("method", "post")
    form.setAttribute("action", url)
    form.setAttribute("enctype", "multipart/form-data")
    form.setAttribute("encoding", "multipart/form-data") # For IE
    if not target:
        target = document.getElementById('do_post_data')
        if not target:
            target = document.createElement("IFRAME")
            target.id = 'do_post_data'
            target.setAttribute('name', 'do_post_data')
            document.body.appendChild(target)
        target = 'do_post_data'
    form.setAttribute("target", target)

    for key in dictionary:
        hiddenField = document.createElement("input")
        hiddenField.setAttribute("type", "hidden")
        hiddenField.setAttribute("name", key)
        hiddenField.setAttribute("value", dictionary[key])
        form.appendChild(hiddenField)
    document.body.appendChild(form)
    form.submit()

class CCCCC: # pylint: disable=too-many-public-methods
    """Create the GUI and launch worker"""
    question_width = 30
    question_height = 30
    source_width = 40
    compiler_height = 30
    question = editor = overlay = tester = compiler = executor = time = None
    index = reset_button = popup_element = None # HTML elements
    top = None # Top page HTML element
    source = None # The source code to compile
    old_source = None
    oldScrollTop = None
    highlight_errors = {}
    question_done = {}
    question_original = {}
    last_answer = {}
    copied = None # Copy with ^C ou ^X
    automatic_compile = True
    state = "uninitalised"
    input_index = -1 # The input number needed
    current_question = -1 # The question on screen
    record_to_send = []
    record_last_time = 0
    record_start = 0
    popup_done = False
    options = {} # sent by the compiler

    def __init__(self):
        print("GUI: start")
        course = None
        if window.location.pathname:
            path = str(window.location.pathname)
            if path[:2] == '/=':
                course = path[2:]
        if not course:
            course = 'course_js.js'
        self.course = course
        self.worker = Worker(course + "?ticket=" + TICKET) # pylint: disable=undefined-variable
        self.worker.onmessage = bind(self.onmessage, self)
        self.worker.onmessageerror = bind(self.onerror, self)
        self.worker.onerror = bind(self.onerror, self)
        self.worker.postMessage(['config', {
            'TICKET': TICKET,
            'LOGIN': LOGIN,
            'SOCK': SOCK,
            'ADMIN': ADMIN,
            'STOP': STOP,
            'ANSWERS': ANSWERS,
            'COURSE': course,
            }])
        setInterval(bind(self.scheduler, self), 200)
        self.create_html()
        for question in ANSWERS:
            question = Number(question)
            self.last_answer[question] = ANSWERS[question]
            self.question_done[question] = True
        try:
            self.shared_buffer = eval('new Int32Array(new SharedArrayBuffer(1024))') # pylint: disable=eval-used
        except: # pylint: disable=bare-except
            self.shared_buffer = None
        self.worker.postMessage(['array', self.shared_buffer])

        self.inputs = {} # Indexed by the question number
        self.do_not_clear = {}
        self.seconds = int(millisecs() / 1000) # pylint: disable=undefined-variable
        print("GUI: init done")

    def send_input(self, string):
        """Send the input value to the worker"""
        if not self.shared_buffer:
            print("SharedArrayBuffer not allowed by HTTP server")
            return
        for i in range(len(string)):
            self.shared_buffer[i+1] = string.charCodeAt(i)
        self.shared_buffer[len(string) + 1] = -1 # String end
        self.shared_buffer[0] = 1

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

        e = new_element('DIV', 'reset',
                        self.question_width + self.source_width - 2, 2,
                        0, 2,
                        '#0000')
        e.textContent = '🗑'
        e.style.fontFamily = 'emoji'
        e.onclick = bind(self.reset, self)
        self.reset_button = e
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
        e = new_element('DIV', 'time', 80, 20, 98, 2, '#0000')
        self.time = e
        self.top.appendChild(e)

    def create_index(self):
        """The question list displayer"""
        e = new_element('DIV', 'index', 0, 1, 0, 100, '#0000')
        self.index = e
        self.top.appendChild(e)

    def scheduler(self): # pylint: disable=too-many-branches
        """Send a new job if free and update the screen"""
        if self.state == 'started':
            return # Compiler is running
        source = self.editor.innerText
        if self.automatic_compile and source != self.old_source:
            self.old_source = source # Do not recompile the same thing
            self.clear_highlight_errors()
            self.unlock_worker()
            self.state = 'started'
            print("send to compiler")
            self.worker.postMessage(source) # Start compile/execute/test
        seconds = int(millisecs() / 1000) # pylint: disable=undefined-variable
        if self.seconds != seconds:
            self.seconds = seconds
            timer = document.getElementById('timer')
            if timer:
                delta = STOP - seconds # pylint: disable=undefined-variable
                if delta < 0:
                    timer.className = "done"
                    message = "Fini depuis"
                    delta = -delta
                else:
                    message = "Fini dans"
                if delta < 60:
                    delta = str(delta) + ' secondes'
                    if timer.className != 'done':
                        timer.className = "minus60"
                elif delta < 3600:
                    if delta < 300 and timer.className != 'done':
                        timer.className = "minus300"
                    delta = int(delta/60) + ' m ' + two_digit(delta % 60) + ' s'
                elif delta < 24*60*60:
                    delta = int(delta/3600) + ' h ' + two_digit((delta/60) % 60) + ' m'
                elif delta < 10*24*60*60:
                    delta = int(delta/86400) + ' j ' + two_digit((delta/3600) % 24) + ' h'
                else:
                    delta = int(delta/86400) + ' jours'
                timer.innerHTML = message + '<br>' + delta

    def unlock_worker(self):
        """ Unlock worker on input waiting to finish MessageEvent"""
        if self.shared_buffer:
            self.shared_buffer[0] = 2

    def overlay_hide(self):
        """The editor and the overlay are no synchronized"""
        self.overlay.style.visibility = 'hidden'
    def overlay_show(self):
        """The editor and the overlay are synched"""
        self.onscroll()
        self.overlay.style.visibility = 'visible'
    def clear_highlight_errors(self):
        """Make space fo the new errors"""
        self.highlight_errors = {}
        while (self.overlay.lastChild
               and self.overlay.lastChild.className
               and 'ERROR' in self.overlay.lastChild.className):
            self.overlay.removeChild(self.overlay.lastChild)
    def coloring(self):
        """Coloring of the text editor with an overlay."""
        self.overlay.innerHTML = html(self.editor.innerText)
        self.overlay.className = 'overlay language-' + self.options['language']
        hljs.highlightElement(self.overlay)
        for line_char in self.highlight_errors:
            what = self.highlight_errors[line_char]
            line_nr, char_nr = line_char.split(':')
            self.add_highlight_errors(line_nr, char_nr, what)
        self.overlay_show()

    def record(self, data, send_now=False):  # pylint: disable=no-self-use
        """Append event to record to 'record_to_send'"""
        time = Math.floor(Date().getTime()/1000)
        if time != self.record_last_time:
            if len(self.record_to_send): # pylint: disable=len-as-condition
                self.record_to_send.append(time - self.record_last_time)
            else:
                self.record_to_send.append(time)
                self.record_start = time
            self.record_last_time = time
        self.record_to_send.append(data)
        if send_now or time - self.record_start > 60:
            # Record on the server
            do_post_data(
                {
                    'course': self.course[:-3],
                    'line': encodeURIComponent(JSON.stringify(self.record_to_send) + '\n'),
                }, 'log?ticket=' + TICKET)
            self.record_to_send = []
            self.record_last_time = 0

    def add_highlight_errors(self, line_nr, char_nr, what):
        """Add the error or warning"""
        error = document.createElement('DIV')
        error.className = 'ERROR ' + what
        error.style.top = (line_nr - 1) * 1.18 + 'vw'
        self.overlay.appendChild(error)
        char = document.createElement('DIV')
        char.className = what + ' char ERROR'
        char.style.top = error.style.top
        char.style.left = (char_nr - 1) + 'ch'
        char.style.width = '1ch'
        self.overlay.appendChild(char)

    def onmousedown(self, event):
        """Mouse down"""
        if self.close_popup(event):
            return
        self.record('MouseDown')
        self.editor.focus()
    def oncopy(self, event):
        """Copy"""
        if self.options.allow_copy_paste:
            self.record('Copy')
            return
        text = window.getSelection().toString()
        if text not in self.editor.innerText:
            self.record('CopyRejected')
            popup_message(self.options['forbiden'])
            event.preventDefault(True)
            return
        self.record('CopyAllowed')
        self.copied = text

    def onpaste(self, event):
        """Mouse down"""
        if self.options.allow_copy_paste:
            self.record('Paste')
            return
        text = (event.clipboardData or event.dataTransfer).getData("text")
        if text in self.editor.innerText or text == self.copied:
            self.record('PasteOk')
            self.overlay_hide()
            setTimeout(bind(self.coloring, self), 100)
            return # auto paste allowed
        self.record('PasteRejected')
        popup_message(self.options['forbiden'])
        event.preventDefault(True)

    def onkeydown(self, event):
        """Key down"""
        if self.close_popup(event):
            return
        if event.target.tagName == 'INPUT':
            return
        self.record(event.key)
        self.clear_highlight_errors()
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
    def oninput(self, event):
        """Send the input to the worker"""
        if event.key == 'Enter':
            self.inputs[self.current_question][event.target.input_index] = event.target.value
            if event.target.run_on_change:
                self.old_source = ''
                self.unlock_worker()
            else:
                self.send_input(event.target.value)
                event.target.run_on_change = True

    def clear_if_needed(self, box):
        """Clear ony once the new content starts to come"""
        if box in self.do_not_clear:
            return
        self.do_not_clear[box] = True
        self[box].innerHTML = '' # pylint: disable=unsubscriptable-object

    def onerror(self, event): # pylint: disable=no-self-use
        """When the worker die?"""
        print(event)

    def reset(self):
        """Reset the editor to the first displayed value"""
        if confirm('Vous voulez vraiment revenir à la version de départ ?'):
            self.set_editor_content(self.question_original[self.current_question])

    def onmessage(self, event): # pylint: disable=too-many-branches,too-many-statements
        """Interprete messages from the worker: update self.messages"""
        what = event.data[0]
        # print(self.state, what, str(event.data[1])[:10])
        value = event.data[1]
        if what == 'options':
            self.options = value
            if value['display_reset']:
                self.reset_button.style.display = 'block'
            else:
                self.reset_button.style.display = 'none'
        elif what == 'current_question':
            self.do_not_clear = {}
            source = self.editor.innerText.strip()
            if (self.current_question >= 0 and value != self.current_question
                    and self.last_answer[self.current_question] != source
               ):
                self.last_answer[self.current_question] = source
            self.current_question = value
            self.record(['question', self.current_question])
        elif what in ('error', 'warning'):
            self.highlight_errors[value[0] + ':' + value[1]] = what
            self.add_highlight_errors(value[0], value[1], what)
        elif what == 'state':
            self.state = value
            if self.state == "started":
                self.input_index = 0
                self.do_not_clear = {}
            if self.state == "inputdone":
                self.state = "started"
        elif what == 'good':
            if self.current_question not in self.question_done:
                self.record(['answer', self.current_question, value.strip()], True)
                self.question_done[self.current_question] = True
                popup_message('Bravo !')
        elif what == 'executor':
            self.clear_if_needed(what)
            if value == '\000INPUT':
                span = document.createElement('INPUT')
                span.onkeypress = bind(self.oninput, self)
                span.input_index = self.input_index
                if not self.inputs[self.current_question]:
                    self.inputs[self.current_question] = {}
                self.executor.appendChild(span)
                if self.input_index in self.inputs[self.current_question]:
                    span.value = self.inputs[self.current_question][self.input_index]
                    self.send_input(span.value)
                    span.run_on_change = True
                else:
                    if document.activeElement and document.activeElement.tagName == 'INPUT':
                        span.focus()
                self.input_index += 1
            else:
                span = document.createElement('SPAN')
                span.innerHTML = value
                self.executor.appendChild(span) # pylint: disable=unsubscriptable-object
        elif what == 'index':
            if ADMIN: # pylint: disable=undefined-variable
                value += '<br><a href="javascript:window.location.pathname=\'adm_home\'">#</a>'
            self[what].innerHTML = value # pylint: disable=unsubscriptable-object
        elif what == 'editor':
            # New question
            # Many \n at the bug (browser problem when inserting a final \n)
            message = value + '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n'
            self.set_editor_content(message)
        elif what == 'default':
            self.question_original[value[0]] = value[1]
        elif what in ('tester', 'compiler', 'question', 'time'):
            self.clear_if_needed(what)
            if what == 'time':
                value += ' ' + self.state + ' ' + LOGIN
            span = document.createElement('SPAN')
            span.innerHTML = value
            if '<error' in value:
                self[what].style.background = '#FAA' # pylint: disable=unsubscriptable-object
            else:
                self[what].style.background = self[what].background # pylint: disable=unsubscriptable-object
            self[what].appendChild(span)  # pylint: disable=unsubscriptable-object
        elif what == 'eval':
            eval(value) # pylint: disable=eval-used

    def set_editor_content(self, message):
        """Set the editor content (question change or reset)"""
        self.overlay_hide()
        self.editor.innerText = message
        self.editor.scrollTop = 0
        # document.getSelection().collapse(self.editor, self.editor.childNodes.length)
        self.coloring()

    def create_html(self):
        """Create the page content"""
        self.top = document.createElement('DIV')
        self.top.onmousedown = bind(self.onmousedown, self)
        self.top.oncopy = bind(self.oncopy, self)
        self.top.oncut = bind(self.oncopy, self)
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

    def close_popup(self, event):
        """Returns True if the popup was closed"""
        if not self.popup_element:
            return False
        self.popup_element.parentNode.removeChild(self.popup_element)
        self.popup_element = None
        self.popup_done = True
        event.stopPropagation()
        event.preventDefault()
        return True

    def popup(self, content):
        """Display a popup with html content"""
        if self.popup_done:
            return
        div = document.createElement('DIV')
        div.className = 'popup'
        div.innerHTML = content
        self.top.appendChild(div)
        self.popup_element = div

ccccc = CCCCC()
