# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,self-assigning-variable,len-as-condition

"""
To simplify the class contains the code for the GUI and the worker.

CCCCC          class manages the GUI
               It sends source code to the Compile worker with sendMessage
               It receives events to update the GUI
Compile        worker base class to manage the question list, compilation, execution
Question       base class for question definition
"""

try:
    # pylint: disable=undefined-variable,self-assigning-variable,invalid-name
    document = document
    setInterval = setInterval
    setTimeout = setTimeout
    Number = Number
    RegExp = RegExp
    bind = bind
    hljs = hljs
    window = window
    screen = screen
    confirm = confirm
    millisecs = millisecs
    html = html
    Date = Date
    Math = Math
    record = record
    parse_grading = parse_grading
    alert = alert
    COURSE = COURSE
    GRADING = GRADING
    STUDENT = STUDENT
    NOTATION = NOTATION
    JSON = JSON
    LOGIN = LOGIN
    ANSWERS = ANSWERS
    TICKET = TICKET
    ADMIN = ADMIN
    SOCK = SOCK
    STOP = STOP
    CHECKPOINT = CHECKPOINT
    VERSIONS = VERSIONS
    CP = CP
    SAVE_UNLOCK = SAVE_UNLOCK
    SEQUENTIAL = SEQUENTIAL
    WHERE = WHERE
    INFOS = INFOS
    encodeURIComponent = encodeURIComponent
    @external
    class Worker: # pylint: disable=function-redefined,too-few-public-methods
        """Needed for rapydscript"""
        def postMessage(self, _message):
            """Send a message to the worker"""
except: # pylint: disable=bare-except
    pass

EXPLAIN = {0: "Sauvegardée", 1: "Validée", 2: "Compilée", 3: "Dernière seconde"}

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
        target = document.createElement("IFRAME")
        target.id = 'do_post_data' + millisecs()
        target.setAttribute('name', target.id)
        target.style.position = 'absolute'
        target.style.left = '-1000px'
        document.body.appendChild(target)
    form.setAttribute("target", target.id)

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
    question = editor = overlay = tester = compiler = executor = time = None
    index = reset_button = popup_element = save_button = local_button = line_numbers = None
    stop_button = fullscreen = comments = None
    top = None # Top page HTML element
    source = None # The source code to compile
    old_source = None
    oldScrollTop = None
    highlight_errors = {}
    question_done = {}
    question_original = {}
    last_answer = {}
    last_answer_cursor = {}
    copied = None # Copy with ^C ou ^X
    state = "uninitalised"
    input_index = -1 # The input number needed
    current_question = -1 # The question on screen
    record_to_send = []
    record_last_time = 0
    record_start = 0
    last_record_to_send = []
    popup_done = False
    compile_now = False
    last_compile = {}
    editor_lines = []
    do_not_register_this_blur = False
    init_done = False
    seconds = 0
    start_time = 0
    do_not_clear = {}
    inputs = {} # User input in execution bloc
    grading_history = ''
    all_comments = {}
    focus_on_next_input = False
    options = {
        'language': 'javascript',
        'forbiden': "Coller du texte copié venant d'ailleurs n'est pas autorisé.",
        'close': "Voulez-vous vraiment quitter cette page ?",
        'allow_copy_paste': CP or GRADING,
        'save_unlock': SAVE_UNLOCK,
        'display_reset': True,
        'positions' : {
            'question': [1, 29, 0, 30, '#EFE'],
            'tester': [1, 29, 30, 70, '#EFE'],
            'editor': [30, 40, 0, 100, '#FFF'],
            'compiler': [70, 30, 0, 30, '#EEF'],
            'executor': [70, 30, 30, 70, '#EEF'],
            'time': [80, 20, 98, 2, '#0000'],
            'index': [0, 1, 0, 100, '#0000'],
            'reset_button': [68, 2, 0, 2, '#0000'],
            'save_button': [66, 2, 0, 2, '#0000'],
            'local_button': [64, 2, 0, 2, '#0000'],
            'stop_button': [61, 2, 0, 2, '#0000'],
            'line_numbers': [100, 1, 0, 100, '#EEE'], # Outside the screen by defaut
            }
    }

    def __init__(self):
        print("GUI: start")
        self.start_time = millisecs()
        self.course = COURSE
        self.worker = Worker(COURSE + "?ticket=" + TICKET) # pylint: disable=undefined-variable
        self.worker.onmessage = bind(self.onmessage, self)
        self.worker.onmessageerror = bind(self.onerror, self)
        self.worker.onerror = bind(self.onerror, self)
        self.worker.postMessage(['config', {
            'TICKET': TICKET,
            'GRADING': GRADING,
            'LOGIN': LOGIN,
            'SOCK': SOCK,
            'ADMIN': ADMIN,
            'STOP': STOP,
            'ANSWERS': ANSWERS,
            'COURSE': COURSE,
            'WHERE': WHERE,
            'SEQUENTIAL': SEQUENTIAL and not GRADING,
            'INFOS': INFOS,
            }])
        try:
            self.shared_buffer = eval('new Int32Array(new SharedArrayBuffer(1024))') # pylint: disable=eval-used
        except: # pylint: disable=bare-except
            self.shared_buffer = None
        self.worker.postMessage(['array', self.shared_buffer])
        print("GUI: wait worker")

    def terminate_init(self):
        """Only terminate init when the worker started"""
        if self.init_done:
            return
        self.init_done = True
        self.create_html()
        for question in ANSWERS:
            question = Number(question)
            self.last_answer[question] = ANSWERS[question][0]
            if ANSWERS[question][1]:
                self.question_done[question] = True

        self.inputs = {} # Indexed by the question number
        self.do_not_clear = {}
        self.seconds = int(millisecs() / 1000)
        print("GUI: init done")

    def popup_message(self, txt):
        """OK popup with the message"""
        self.do_not_register_this_blur = True
        alert(txt) # pylint: disable=undefined-variable

    def send_input(self, string):
        """Send the input value to the worker"""
        if not self.shared_buffer:
            print("SharedArrayBuffer not allowed by HTTP server")
            return
        for i in range(len(string)):
            self.shared_buffer[i+1] = string.charCodeAt(i)
        self.shared_buffer[len(string) + 1] = -1 # String end
        self.shared_buffer[0] = 1

    def update_gui(self):
        """Set the bloc position and background"""
        self.options['positions']['overlay'] = self.options['positions']['editor']
        self.options['positions']['overlay'][4] = '#0000'
        if GRADING:
            left, width, top, height, background = self.options['positions']['editor']
            self.options['positions']['comments'] = [
                left + width, 100 - (left + width), top, height]
        for key in self.options['positions']:
            left, width, top, height, background = self.options['positions'][key]
            e = self[key] # pylint: disable=unsubscriptable-object
            if not e:
                continue
            e.style.left = left + '%'
            e.style.right = (100 - left - width) + '%'
            e.style.top = top + '%'
            e.style.bottom = (100 - top - height) + '%'
            e.style.background = background
            e.background = background
        if self.options['display_reset']:
            self.reset_button.style.display = 'block'
        else:
            self.reset_button.style.display = 'none'
        self.reset_button.innerHTML = self.options['icon_reset']
        self.save_button.innerHTML = self.options['icon_save']
        self.local_button.innerHTML = self.options['icon_local']
        if self.stop_button:
            self.stop_button.innerHTML = self.options['icon_stop']
        if GRADING:
            self.save_button.style.display = 'none'
            self.reset_button.style.display = 'none'
            self.stop_button.style.display = 'none'
    def create_gui(self):
        """The text editor container"""
        self.options['positions']['overlay'] = self.options['positions']['editor']
        if GRADING:
            self.options['positions']['comments'] = [] # Filled by update_gui()
        for key in self.options['positions']:
            if key == 'stop_button' and not CHECKPOINT:
                continue
            e = document.createElement('DIV')
            e.className = key
            e.style.position = 'absolute'
            self.top.appendChild(e)
            self[key] = e # pylint: disable=unsupported-assignment-operation

        self.editor.contentEditable = True
        self.editor.spellcheck = False
        self.editor.autocorrect = False
        self.editor.autocapitalize = False
        self.editor.autocomplete = False
        self.editor.onscroll = bind(self.onscroll, self)
        self.editor.focus()

        self.reset_button.style.fontFamily = 'emoji'
        self.reset_button.onclick = bind(self.reset, self)
        self.save_button.style.fontFamily = 'emoji'
        self.save_button.onclick = bind(self.save_unlock, self)
        if self.stop_button:
            self.stop_button.style.fontFamily = 'emoji'
            self.stop_button.onclick = bind(self.stop, self)
        self.local_button.onclick = bind(self.save_local, self)

        self.fullscreen = document.createElement('DIV')
        self.fullscreen.className = 'fullscreen'
        self.fullscreen.innerHTML = """Appuyez sur la touche F11 pour passer en plein écran.<br>
        <small>Mettez le curseur sur <span>⏱</span> pour voir le temps restant</small>
        """
        self.top.appendChild(self.fullscreen)

    def save_local(self):
        """Save the source on a local file"""
        bb = eval('new Blob([' + JSON.stringify(self.source) + '], {"type": "text/plain"})')
        a = document.createElement('a')
        a.download = (self.course.split('=')[1] + '_' + (self.current_question + 1)
            + '.' + (self.options['extension'] or 'txt'))
        a.href = window.URL.createObjectURL(bb)
        a.click()

    def scheduler(self): # pylint: disable=too-many-branches
        """Send a new job if free and update the screen"""
        if (not GRADING
                and not self.options['allow_copy_paste']
                and screen.height != max(window.innerHeight, window.outerHeight)
           ):
            self.fullscreen.style.display = 'block'
        else:
            self.fullscreen.style.display = 'none'

        if self.state == 'started':
            return # Compiler is running
        if (self.options['automatic_compilation'] and self.source != self.old_source
            or self.compile_now):
            print('compile')
            self.compile_now = False
            self.old_source = self.source # Do not recompile the same thing
            self.clear_highlight_errors()
            self.unlock_worker()
            self.state = 'started'
            self.worker.postMessage(self.source) # Start compile/execute/test
            self.last_compile[self.current_question] = self.source
        seconds = int(millisecs() / 1000)
        if self.seconds != seconds:
            self.seconds = seconds
            timer = document.getElementById('timer')
            if timer:
                delta = STOP - seconds # pylint: disable=undefined-variable
                if delta == 10:
                    self.record_now()
                if delta == 5:
                    if ((not self.last_answer[self.current_question]
                            or self.question_original[self.current_question].strip()
                                == self.last_answer[self.current_question].strip()
                        )
                        and self.question_original[self.current_question].strip()
                            == self.last_compile[self.current_question].strip()
                    ):
                        # The student never saved nor compiled the source
                        self.record(['snapshot', self.current_question, self.source], send_now=True)
                if delta < 0:
                    timer.className = "done"
                    message = self.options['time_done']
                    delta = -delta
                else:
                    message = self.options['time_running']
                secs = two_digit(delta % 60)
                mins = two_digit((delta/60) % 60)
                hours = two_digit((delta/3600) % 24)
                days = int(delta/86400)
                opts = self.options
                if delta < 60:
                    delta = str(delta) + ' ' + opts['time_seconds']
                    if timer.className != 'done':
                        timer.className = "minus60"
                elif delta < 120:
                    delta = mins + opts['time_m'] + secs
                    if timer.className != 'done':
                        timer.className = "minus120"
                elif delta < 3600:
                    if delta < 300 and timer.className != 'done':
                        timer.className = "minus300"
                    delta = mins + opts['time_m'] + secs
                elif delta < 24*60*60:
                    delta = hours + opts['time_h'] + mins + opts['time_m']
                elif delta < 10*24*60*60:
                    delta = days + opts['time_d'] + hours + opts['time_h']
                else:
                    delta = days + opts['time_days']
                timer.innerHTML = message + '<br>' + delta

    def compilation_toggle(self, element):
        """Toggle the automatic compilation flag"""
        if self.options['automatic_compilation']:
            # The False value is for course deactivated automatic compilation
            self.options['automatic_compilation'] = None
            element.className = 'unchecked'
        else:
            self.options['automatic_compilation'] = True
            element.className = 'checked'

    def compilation_run(self):
        """Run one compilation"""
        self.compile_now = True
        self.scheduler()

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
    def update_source(self):
        def clear_text(state):
            if state.node.tagName == 'DIV':
                if len(state.text) and state.text[-1] != '\n':
                    state.editor_lines.append(state.last)
                    state.text.append('\n')
                    state.last = None
                for state.node in state.node.childNodes:
                    clear_text(state)
                if len(state.text) and state.text[-1] != '\n':
                    state.editor_lines.append(state.last)
                    state.text.append('\n')
                    state.last = None
            elif state.node.tagName == 'BR':
                if state.last:
                    state.editor_lines.append(state.last)
                else:
                    state.editor_lines.append(state.node)
                state.text.append('\n')
                state.last = None
            elif state.node.tagName == 'SPAN':
                state.text.append(state.node.innerText)
            else:
                state.text.append(state.node.nodeValue)
                state.last = state.node
        self.editor_lines = []
        state = {
            'node': self.editor,
            'text': [],
            'last': None,
            'editor_lines': self.editor_lines
        }
        clear_text(state)
        if state['last']:
            self.editor_lines.append(state['last'])
        self.source_with_newlines = ''.join(state['text'])
        while state['text'][-1] == '\n':
            state['text'].pop()
        self.source = ''.join(state['text'])

    def coloring(self): # pylint: disable=too-many-statements
        """Coloring of the text editor with an overlay."""
        self.update_source()
        if self.source == '' and self.question_original[self.current_question] != '':
            self.reset()
        self.overlay.innerHTML = html(self.source_with_newlines)
        self.overlay.className = 'overlay language-' + self.options['language']
        hljs.highlightElement(self.overlay)
        for line_char in self.highlight_errors:
            what = self.highlight_errors[line_char]
            line_nr, char_nr = line_char.split(':')
            self.add_highlight_errors(line_nr, char_nr, what)

        meter = document.createRange()
        line_height = 1000
        comments = self.all_comments[self.current_question] or {}
        comments = comments[self.version] or {}
        for i, line in enumerate(self.editor_lines):
            if line.getBoundingClientRect:
                rect = line.getBoundingClientRect()
            else:
                meter.selectNodeContents(line)
                rect = meter.getBoundingClientRect()
            if rect.top:
                top = rect.top + self.editor.scrollTop
            else:
                top = line.offsetTop
            if not self.line_numbers.childNodes[i]:
                self.line_numbers.appendChild(document.createElement('DIV'))
                self.line_numbers.childNodes[i].textContent = i+1
            if GRADING:
                if not self.comments.childNodes[i]:
                    comment = document.createElement('TEXTAREA')
                    comment.line = i
                    comment.style.top = top + 'px'
                    self.comments.appendChild(comment)
                self.comments.childNodes[i].textContent = comments[i] or ''
                self.comments.childNodes[i].className = comments[i] and 'filled' or 'empty'

            self.line_numbers.childNodes[i].style.top = top + 'px'
            if rect.height and rect.height < line_height:
                line_height = rect.height
                continue
            if rect.height < line_height * 1.8:
                continue
            marker = document.createElement('DIV')
            marker.className = 'wrapped'
            marker.style.left = rect.left - self.overlay.offsetLeft + 'px'
            marker.style.top = rect.top + line_height + self.editor.scrollTop + 'px'
            marker.style.width = rect.width + 'px'
            marker.style.height = rect.height - line_height + 'px'
            self.overlay.appendChild(marker)
        self.overlay_show()

    def record_now(self):
        """Record on the server"""
        if len(self.record_to_send) == 0:
            return
        do_post_data(
            {
                'course': self.course,
                'line': encodeURIComponent(JSON.stringify(self.record_to_send) + '\n'),
            }, 'log?ticket=' + TICKET)
        self.last_record_to_send = self.record_to_send
        self.record_to_send = []
        self.record_last_time = 0

    def record(self, data, send_now=False):
        """Append event to record to 'record_to_send'"""
        if GRADING:
            return
        time = Math.floor(Date().getTime()/1000)
        if time != self.record_last_time:
            if len(self.record_to_send):
                self.record_to_send.append(time - self.record_last_time)
            else:
                self.record_to_send.append(time)
                self.record_start = time
            self.record_last_time = time
        self.record_to_send.append(data)
        if send_now or time - self.record_start > 60:
            self.record_now()

    def record_done(self):
        """The server saved the recorded value"""
        for item in self.last_record_to_send:
            if item[0] == 'save':
                self.save_button.style.transition = 'transform 1s, opacity 1s'
                self.save_button.style.transform = 'scale(1)'
                self.save_button.style.opacity = 1
                if self.do_stop:
                    record('/checkpoint/' + self.course + '/' + LOGIN + '/STOP', send_now=True)
                    self.options['close'] = ''
                    document.body.innerHTML = self.options['stop_done']

    def add_highlight_errors(self, line_nr, char_nr, what):
        """Add the error or warning"""
        box = document.createRange()
        def insert(element, class_name, move_right=0):
            """Set the element to the same place than the range"""
            rect = box.getBoundingClientRect()
            if move_right:
                move_right = rect.width
            element.style.top = (rect.top - self.editor.offsetTop + self.editor.scrollTop) + 'px'
            element.style.height = rect.height + 'px'
            element.style.left = 'calc(' + (
                rect.left - self.editor.offsetLeft + move_right) + 'px - var(--pad))'
            element.style.width = rect.width + 'px'
            element.className = class_name
            self.overlay.appendChild(element)
        line = self.editor_lines[line_nr - 1]
        box.selectNode(line)
        error = document.createElement('DIV')
        insert(error, 'ERROR ' + what)
        try:
            if char_nr >= (line.nodeValue or line.innerText).length:
                char_nr -= 1
                move_right = 1
            else:
                move_right = 0
            box.setStart(line, char_nr-1)
            box.setEnd(line, char_nr)
            char = document.createElement('DIV')
            insert(char, what + ' char ERROR', move_right)
        except: # pylint: disable=bare-except
            pass

    def onmousedown(self, event):
        """Mouse down"""
        if self.close_popup(event):
            return
        self.record('MouseDown')
    def oncopy(self, event, what='Copy'):
        """Copy"""
        if self.options['allow_copy_paste']:
            self.record(what)
            return
        text = window.getSelection().toString().replace(RegExp('\r', 'g'), '')
        if text.strip() not in self.source and text not in self.question.innerText:
            self.record(what + 'Rejected')
            self.popup_message(self.options['forbiden'])
            event.preventDefault(True)
            return
        self.record(what + 'Allowed')
        self.copied = text
    def oncut(self, event):
        """Cut"""
        self.oncopy(event, 'Cut')
        setTimeout(bind(self.coloring, self), 100)
    def insert_text(self, event, text):
        """Insert the pasted text"""
        self.overlay_hide()
        if event.type == 'drop':
            setTimeout(bind(self.coloring, self), 100)
        else:
            document.execCommand('insertText', False, text)
            event.preventDefault(True)
            self.coloring()

    def onpaste(self, event):
        """Mouse down"""
        text = (event.clipboardData or event.dataTransfer).getData("text")
        text = text.replace(RegExp('\r', 'g'), '')
        if self.options['allow_copy_paste']:
            self.record('Paste')
            self.insert_text(event, text)
            return
        if text.strip() in self.source or text.strip() in self.question.innerText or text == self.copied:
            self.record('PasteOk')
            self.insert_text(event, text)
            return # auto paste allowed
        self.record('PasteRejected')
        self.popup_message(self.options['forbiden'])
        event.preventDefault(True)

    def save_cursor(self):
        """Save the cursor position"""
        self.last_answer_cursor[self.current_question] = [self.editor.scrollTop]

    def onkeydown(self, event):
        """Key down"""
        if self.close_popup(event):
            return
        if event.target.tagName == 'INPUT' and event.key not in ('F8', 'F9'):
            return
        self.record(event.key or 'null')
        self.clear_highlight_errors()
        if event.key == 'Tab':
            document.execCommand('insertHTML', False, '    ')
            event.preventDefault(True)
        elif event.key == 's' and event.ctrlKey:
            self.save_unlock()
            # self.save_local() # No more local save with Ctrl+S
            event.preventDefault(True)
        elif event.key == 'F9':
            if self.options['automatic_compilation'] == False: # pylint: disable=singleton-comparison
                self.compilation_run()
            elif self.options['automatic_compilation']:
                document.getElementById('automatic_compilation').className = 'unchecked'
                self.options['automatic_compilation'] = None
            else:
                document.getElementById('automatic_compilation').className = 'checked'
                self.options['automatic_compilation'] = True
            event.preventDefault(True)
        elif event.key == 'F8':
            self.unlock_worker()
            self.save_cursor()
            self.worker.postMessage(['indent', self.source.strip()])
        elif event.key == 'Enter' and event.target is self.editor:
            # Fix Firefox misbehavior
            self.oldScrollTop = self.editor.scrollTop
        elif len(event.key) > 1 and event.key not in ('Delete', 'Backspace'):
            return # Do not hide overlay: its only a cursor move
        self.overlay_hide()
    def onkeyup(self, event):
        """Key up"""
        if event.target.tagName == 'TEXTAREA':
            # The teacher enter a comment
            return
        if event.key not in ('Left', 'Right', 'Up', 'Down'):
            self.coloring()
    def onkeypress(self, event):
        """Key press"""
    def onblur(self, _event):
        """Window blur"""
        if self.do_not_register_this_blur:
            self.do_not_register_this_blur = False
            return
        self.record('Blur')
    def onscroll(self, _event=None):
        """To synchronize syntax highlighting"""
        if self.oldScrollTop is not None:
            # Fix Firefox misbehavior
            self.editor.scrollTop = self.oldScrollTop
            self.oldScrollTop = None
        else:
            self.line_numbers.scrollTop = self.editor.scrollTop
            if GRADING:
                self.comments.scrollTop = self.editor.scrollTop
            self.overlay.scrollTop = self.editor.scrollTop
    def oninput(self, event):
        """Send the input to the worker"""
        if event.key == 'Enter':
            self.focus_on_next_input = True
            if self.options['forget_input']:
                event.target.disabled = True
            else:
                inputs = event.target.parentNode.getElementsByTagName('INPUT')
                for value in inputs:
                    if value == inputs[-1] and len(value.value) == 0:
                        continue
                    self.inputs[self.current_question][value.input_index] = value.value
            if event.target.run_on_change:
                self.old_source = ''
                self.unlock_worker()
                self.compilation_run() # Force run even if deactivated
            else:
                self.send_input(event.target.value)
                event.target.run_on_change = True

    def clear_if_needed(self, box):
        """Clear only once the new content starts to come"""
        if box in self.do_not_clear:
            return
        self.do_not_clear[box] = True
        self[box].innerHTML = '' # pylint: disable=unsubscriptable-object

    def onerror(self, event): # pylint: disable=no-self-use
        """When the worker die?"""
        print(event)

    def reset(self):
        """Reset the editor to the first displayed value"""
        if millisecs() - self.start_time < 1000:
            return # Hide a bug: do not display reset on start
        if confirm(self.options['reset_confirm']):
            self.set_editor_content(self.question_original[self.current_question])

    def save(self):
        """Save the editor content"""
        self.update_source()
        if (not self.last_answer[self.current_question]
                or self.last_answer[self.current_question].strip() != self.source.strip()):
            self.save_button.style.transition = ''
            self.save_button.style.transform = 'scale(8)'
            self.save_button.style.opacity = 0.1
            self.record(['save', self.current_question, self.source], send_now=True)
            self.worker.postMessage(['source', self.current_question, self.source])
            self.last_answer[self.current_question] = self.source
            return True
        return False

    def save_unlock(self):
        """Saving the last question allowed question open the next one"""
        if self.save() and self.options['save_unlock']:
            if not self.last_answer[self.current_question + 1]:
                # Unlock the next question
                self.unlock_worker()
                self.worker.postMessage(['goto', self.current_question + 1])

    def stop(self):
        """The student stop its session"""
        if confirm(self.options['stop_confirm']):
            self.do_stop = True
            if not self.save():
                record('/checkpoint/' + self.course + '/' + LOGIN + '/STOP', send_now=True)

    def update_comments(self, comments):
        """Fill comments"""
        for infos in comments.split('\n'):
            if not infos:
                continue
            _timestamp, _login, question, version, line, comment = JSON.parse(infos)
            if question not in self.all_comments:
                self.all_comments[question] = {}
            if version not in self.all_comments[question]:
                self.all_comments[question][version] = {}
            self.all_comments[question][version][line] = comment
        self.coloring()

    def update_grading(self, history=None):
        """Colorize buttons"""
        if history:
            self.grading_history = history
        buttons = document.getElementById('grading')
        if not buttons:
            setTimeout(bind(self.update_grading, self), 100)
            return
        grading = parse_grading(self.grading_history)
        grading_sum = 0
        nr_grades = 0
        for button in buttons.getElementsByTagName('BUTTON'):
            g = button.getAttribute('g')
            if g in grading and button.innerText == grading[g][0]:
                button.title = grading[g][1]
                button.className = 'grade_selected'
                grading_sum += Number(grading[g][0])
                nr_grades += 1
            else:
                button.className = 'grade_unselected'
        element = document.getElementById('grading_sum')
        element.textContent = 'Envoyer un mail Σ=' + grading_sum
        element.onclick = bind(self.send_mail, self)
        if self.nr_grades == nr_grades:
            element.style.background = "#0F0"
            element.style.color = "#000"
        else:
            element.style.background = "#FFF"
            element.style.color = "#0F0"

    def send_mail(self):
        """Send a mail to the student"""
        width = 0
        for line in self.source.split("\n"):
            width = max(width, len(line))
        content = ['<pre>']
        to_fill = []
        for i, line in enumerate(self.source.split("\n")):
            content.append(html(line))
            for _ in range(width - len(line)):
                content.append(' ')
            content.append('//')
            comment = self.all_comments[self.current_question]
            if comment:
                comment = comment[self.version]
                if comment:
                    comment = comment[i]
                    if comment:
                        for comment_line in comment.split('\n'):
                            to_fill.append(comment_line)
            if len(to_fill):
                content.append(html(to_fill[0]))
                to_fill.splice(0, 1)
            content.append('\n')
        content.append("</pre>")

        window.location = ("mailto:" + INFOS['mail']
            + "?subject=" + encodeURIComponent(COURSE.split('=')[1])
            + "&html-body="
            + encodeURIComponent(''.join(content))
            )


    def get_grading(self):
        """HTML of the grading interface"""
        content = ['<pre id="grading" onclick="grade(event)">',
                    'Version <select style="background:#FF0" onchange="version_change(this)">',
                     ]
        now = Date()
        for i, version in enumerate(VERSIONS[self.current_question]):
            self.version = ANSWERS[self.current_question][1]
            content.append('<option')
            if ANSWERS[self.current_question][1] == i:
                content.append(' selected')
            if not version:
                content.append(' disabled')
            content.append('>')
            content.append(EXPLAIN[i])
            if version:
                now.setTime(version[2] * 1000)
                content.append(' ')
                content.append(two_digit(now.getHours()))
                content.append(':')
                content.append(two_digit(now.getMinutes()))
                content.append(':')
                content.append(two_digit(now.getSeconds()))
            content.append('</option>')
        content.append('</select>')

        i = 0
        for item in NOTATION.split('{'):
            options = item.split('}')
            if len(options) == 1 or not options[0].match(RegExp('^.*:[-0-9,.]+$')):
                if i != 0:
                    content.append('{')
                content.append(html(item))
                continue
            values = options[0].replace(RegExp('.*:'), '')
            label = options[0].replace(RegExp(':[-0-9,.]+$'), '')
            content.append('<span>' + html(label))
            for choice in values.split(','):
                content.append('<button g="' + i + '">' + choice + '</button>')
            content.append('</span>')
            j = 0
            for after in options[1:]:
                if j:
                    content.append('}')
                j = 1
                content.append(html(after))
            i += 1
        self.nr_grades = i
        content.append('<span id="grading_sum"></span></pre>')
        return ''.join(content)

    def onmessage(self, event): # pylint: disable=too-many-branches,too-many-statements
        """Interprete messages from the worker: update self.messages"""
        what = event.data[0]
        # print(millisecs(), self.state, what, str(event.data[1])[:10])
        value = event.data[1]
        if what == 'options':
            for key in value:
                self.options[key] = value[key]
            self.terminate_init()
            self.update_gui()
        elif what == 'current_question':
            self.compile_now = True
            self.old_source += 'force recompile'
            self.do_not_clear = {}
            self.update_source()
            self.save_cursor()
            if (self.current_question >= 0 and value != self.current_question
                    and (
                        not self.last_answer[self.current_question]
                        or self.last_answer[self.current_question].strip() != self.source.strip()
                    )
               ):
                self.save()
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
                self.last_answer[self.current_question] = value.strip()
                messages = self.options['good']
                self.popup_message(messages[millisecs() % len(messages)])
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
                    if self.focus_on_next_input:
                        self.focus_on_next_input = False
                        span.focus()
                self.input_index += 1
            else:
                span = document.createElement('DIV')
                # The first space is replaced by an unsecable space
                # in order to display it on span start <span> foo</span>
                span.innerHTML = value.replace(' ', ' ')
                self.executor.appendChild(span) # pylint: disable=unsubscriptable-object
        elif what == 'index':
            content = ('<div class="questions"><a href="/' + window.location.search + '">🏠</a>'
                + '<div class="tips">Accueil C5</div></div><br>')
            if GRADING:
                content += '<div class="version">' + WHERE[2].split(',')[3].replace('a', 'Ⓐ').replace('b', 'Ⓑ') + '</div>'
            content += value
            if ADMIN: # pylint: disable=undefined-variable
                content += '<br><a href="javascript:window.location.pathname=\'/adm/home\'">#</a>'
            self[what].innerHTML = content # pylint: disable=unsubscriptable-object
        elif what == 'editor':
            # New question
            message = value + '\n\n\n'
            self.set_editor_content(message)
        elif what == 'default':
            self.question_original[value[0]] = value[1]
        elif what in ('tester', 'compiler', 'question', 'time'):
            self.clear_if_needed(what)
            if what == 'question' and GRADING and self[what].childNodes.length == 0: # pylint: disable=unsubscriptable-object
                value = self.get_grading() + value
            if what == 'time':
                value += ' ' + self.state + ' ' + LOGIN
            span = document.createElement('DIV')
            span.innerHTML = value
            if '<error' in value:
                self[what].style.background = '#FAA' # pylint: disable=unsubscriptable-object
            else:
                self[what].style.background = self[what].background # pylint: disable=unsubscriptable-object
            self[what].appendChild(span)  # pylint: disable=unsubscriptable-object
            if what == 'question' and GRADING:
                self.update_grading()
        elif what == 'eval':
            eval(value) # pylint: disable=eval-used
        elif what == 'stop':
            alert("La session est terminée, rechargez la page pour la réactiver")
            window.location = window.location

    def set_editor_content(self, message):
        """Set the editor content (question change or reset)"""
        self.overlay_hide()
        self.editor.innerText = message
        if self.last_answer_cursor[self.current_question]:
            scrollpos = self.last_answer_cursor[self.current_question]
            self.editor.scrollTop = scrollpos
            # document.getSelection().collapse(self.editor, self.editor.childNodes.length)
        else:
            self.editor.scrollTop = 0
        # document.getSelection().collapse(self.editor, self.editor.childNodes.length)
        self.coloring()

    def onbeforeunload(self, event):
        """Prevent page closing"""
        if self.options['close'] == '' or GRADING:
            return None
        self.record("Close", send_now=True)
        event.preventDefault()
        event.returnValue = self.options['close']
        return event.returnValue

    def create_html(self):
        """Create the page content"""
        self.top = document.createElement('DIV')
        self.top.onmousedown = bind(self.onmousedown, self)
        self.top.oncopy = bind(self.oncopy, self)
        self.top.oncut = bind(self.oncut, self)
        self.top.onpaste = bind(self.onpaste, self)
        self.top.ondrop = bind(self.onpaste, self)
        self.top.onkeydown = bind(self.onkeydown, self)
        self.top.onkeyup = bind(self.onkeyup, self)
        self.top.onkeypress = bind(self.onkeypress, self)
        window.onbeforeunload = bind(self.onbeforeunload, self)
        window.onblur = bind(self.onblur, self)
        document.getElementsByTagName('BODY')[0].appendChild(self.top)
        self.create_gui()
        self.update_gui()
        setInterval(bind(self.scheduler, self), 200)
        if GRADING:
            self.comments.onclick = bind(self.add_comment, self)
            self.comments.onblur = bind(self.save_comment, self)
            # Get grades
            do_post_data({'student': STUDENT}, 'record_grade/' + COURSE + '?ticket=' + TICKET)
            do_post_data({'student': STUDENT}, 'record_comment/' + COURSE + '?ticket=' + TICKET)

    def add_comment(self, event):
        """Clic on a comment"""
        if event.target.tagName == 'TEXTAREA':
            event.target.onchange = bind(self.save_comment, self)
    def save_comment(self, event):
        """Save a comment"""
        do_post_data(
            {
                'question': self.current_question,
                'line': event.target.line,
                'comment': event.target.value,
                'student': STUDENT,
                'version': self.version,
            }, 'record_comment/' + COURSE + '?ticket=' + TICKET)
        event.target.className = "saving"

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

def grade(event):
    """Set the grade"""
    if 'grade_selected' in event.target.className:
        value = ''
    else:
        value = event.target.textContent
    grade_id = event.target.getAttribute('g')
    if grade_id is None:
        return
    do_post_data(
        {
            'grade': grade_id,
            'value': value,
            'student': STUDENT,
        }, 'record_grade/' + COURSE + '?ticket=' + TICKET)

def version_change(select):
    """Change the displayed version"""
    source, _what, _time = VERSIONS[ccccc.current_question][select.selectedIndex]
    ccccc.version = select.selectedIndex
    ccccc.save_cursor()
    ccccc.set_editor_content(source)

ccccc = CCCCC()
