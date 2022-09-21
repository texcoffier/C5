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
    bind = bind
    hljs = hljs
    window = window
    confirm = confirm
    millisecs = millisecs
    html = html
    Date = Date
    Math = Math
    record = record
    JSON = JSON
    LOGIN = LOGIN
    ANSWERS = ANSWERS
    TICKET = TICKET
    ADMIN = ADMIN
    SOCK = SOCK
    STOP = STOP
    CHECKPOINT = CHECKPOINT
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
            target.style.position = 'absolute'
            target.style.left = '-1000px'
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
    question = editor = overlay = tester = compiler = executor = time = None
    index = reset_button = popup_element = save_button = local_button = line_numbers = None
    stop_button = None
    top = None # Top page HTML element
    source = None # The source code to compile
    old_source = None
    oldScrollTop = None
    highlight_errors = {}
    question_done = {}
    question_original = {}
    last_answer = {}
    copied = None # Copy with ^C ou ^X
    state = "uninitalised"
    input_index = -1 # The input number needed
    current_question = -1 # The question on screen
    record_to_send = []
    record_last_time = 0
    record_start = 0
    popup_done = False
    compile_now = False
    editor_lines = []
    do_not_register_this_blur = False
    init_done = False
    seconds = 0
    do_not_clear = {}
    inputs = {} # User input in execution bloc
    options = {
        'language': 'javascript',
        'forbiden': "Coller du texte copié venant d'ailleurs n'est pas autorisé.",
        'close': "Voulez-vous vraiment quitter cette page ?",
        'allow_copy_paste': CP,
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
        course = None
        if window.location.pathname:
            path = str(window.location.pathname)
            if path[:2] == '/=':
                course = path[2:]
        if not course:
            course = 'JS=introduction'
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
            'WHERE': WHERE,
            'SEQUENTIAL': SEQUENTIAL,
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

    def create_gui(self):
        """The text editor container"""
        self.options['positions']['overlay'] = self.options['positions']['editor']
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
        if self.state == 'started':
            return # Compiler is running
        if (self.options['automatic_compilation'] or self.compile_now
           ) and self.source != self.old_source:
            self.compile_now = False
            self.old_source = self.source # Do not recompile the same thing
            self.clear_highlight_errors()
            self.unlock_worker()
            self.state = 'started'
            self.worker.postMessage(self.source) # Start compile/execute/test
        seconds = int(millisecs() / 1000)
        if self.seconds != seconds:
            self.seconds = seconds
            timer = document.getElementById('timer')
            if timer:
                delta = STOP - seconds # pylint: disable=undefined-variable
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
        self.options['automatic_compilation'] = True
        self.scheduler()
        self.options['automatic_compilation'] = False

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
    def coloring(self): # pylint: disable=too-many-statements
        """Coloring of the text editor with an overlay."""
        if self.editor.textContent == '' and self.question_original[self.current_question] != '':
            self.reset()
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
        self.source = ''.join(state['text'])
        self.overlay.innerHTML = html(self.source)
        self.overlay.className = 'overlay language-' + self.options['language']
        hljs.highlightElement(self.overlay)
        for line_char in self.highlight_errors:
            what = self.highlight_errors[line_char]
            line_nr, char_nr = line_char.split(':')
            self.add_highlight_errors(line_nr, char_nr, what)

        meter = document.createRange()
        line_height = 0
        for i, line in enumerate(self.editor_lines):
            if line.getBoundingClientRect:
                rect = line.getBoundingClientRect()
            else:
                meter.selectNodeContents(line)
                rect = meter.getBoundingClientRect()
            if not self.line_numbers.childNodes[i]:
                self.line_numbers.appendChild(document.createElement('DIV'))
                self.line_numbers.childNodes[i].textContent = i+1 
            if rect.top:
                top = rect.top + self.editor.scrollTop
            else:
                top = line.offsetTop
            self.line_numbers.childNodes[i].style.top = top + 'px'
            if line_height == 0:
                # Assume the first line is not wrapped
                line_height = rect.height * 1.1
                continue
            if rect.height < line_height:
                continue
            marker = document.createElement('DIV')
            marker.className = 'wrapped'
            marker.style.left = rect.left - self.overlay.offsetLeft + 'px'
            marker.style.top = rect.top + line_height + self.editor.scrollTop + 'px'
            marker.style.width = rect.width + 'px'
            marker.style.height = rect.height - line_height + 'px'
            self.overlay.appendChild(marker)
        self.overlay_show()

    def record(self, data, send_now=False):  # pylint: disable=no-self-use
        """Append event to record to 'record_to_send'"""
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
            # Record on the server
            do_post_data(
                {
                    'course': self.course,
                    'line': encodeURIComponent(JSON.stringify(self.record_to_send) + '\n'),
                }, 'log?ticket=' + TICKET)
            self.record_to_send = []
            self.record_last_time = 0

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
        self.editor.focus()
    def oncopy(self, event):
        """Copy"""
        if self.options['allow_copy_paste']:
            self.record('Copy')
            return
        text = window.getSelection().toString()
        if text not in self.source and text not in self.question.innerText:
            self.record('CopyRejected')
            self.popup_message(self.options['forbiden'])
            event.preventDefault(True)
            return
        self.record('CopyAllowed')
        self.copied = text

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
        if self.options['allow_copy_paste']:
            self.record('Paste')
            self.insert_text(event, text)
            return
        if text in self.source or text in self.question.innerText or text == self.copied:
            self.record('PasteOk')
            self.insert_text(event, text)
            return # auto paste allowed
        self.record('PasteRejected')
        self.popup_message(self.options['forbiden'])
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
        elif event.key == 's' and event.ctrlKey:
            self.save_unlock()
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
        elif event.key == 'Enter' and event.target is self.editor:
            # Fix Firefox misbehavior
            self.oldScrollTop = self.editor.scrollTop
        elif len(event.key) > 1 and event.key not in ('Delete', 'Backspace'):
            return # Do not hide overlay: its only a cursor move
        self.overlay_hide()
    def onkeyup(self, event):
        """Key up"""
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
            self.overlay.scrollTop = self.editor.scrollTop
    def oninput(self, event):
        """Send the input to the worker"""
        if event.key == 'Enter':
            self.inputs[self.current_question][event.target.input_index] = event.target.value
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
        if confirm(self.options['reset_confirm']):
            self.set_editor_content(self.question_original[self.current_question])

    def save(self):
        """Save the editor content"""
        source = self.editor.innerText.strip()
        if (not self.last_answer[self.current_question]
                or self.last_answer[self.current_question].strip() != source.strip()):
            self.save_button.style.transition = ''
            self.save_button.style.transform = 'scale(8)'
            self.save_button.style.opacity = 0.1
            def stop():
                self.save_button.style.transition = 'transform 1s, opacity 1s'
                self.save_button.style.transform = 'scale(1)'
                self.save_button.style.opacity = 1
            setTimeout(stop, 100)
            self.record(['save', self.current_question, source], send_now=True)
            self.worker.postMessage(['source', self.current_question, source])
            self.last_answer[self.current_question] = source
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
            self.save()
            record('/checkpoint/' + self.course + '/' + LOGIN + '/STOP')
            self.options['close'] = ''
            document.body.innerHTML = self.options['stop_done']

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
            self.source = self.editor.innerText.strip()
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
                    if document.activeElement and document.activeElement.tagName == 'INPUT':
                        span.focus()
                self.input_index += 1
            else:
                span = document.createElement('SPAN')
                span.innerHTML = value
                self.executor.appendChild(span) # pylint: disable=unsubscriptable-object
        elif what == 'index':
            if ADMIN: # pylint: disable=undefined-variable
                value += '<br><a href="javascript:window.location.pathname=\'/adm/home\'">#</a>'
            self[what].innerHTML = value # pylint: disable=unsubscriptable-object
        elif what == 'editor':
            # New question
            message = value + '\n\n\n'
            self.set_editor_content(message)
        elif what == 'default':
            self.question_original[value[0]] = value[1]
        elif what in ('tester', 'compiler', 'question', 'time'):
            self.clear_if_needed(what)
            if what == 'time':
                value += ' ' + self.state + ' ' + LOGIN
            span = document.createElement('DIV')
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

    def onbeforeunload(self, event):
        """Prevent page closing"""
        if self.options['close'] == '':
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
        self.top.oncut = bind(self.oncopy, self)
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
