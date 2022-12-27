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
    prompt = prompt
    nice_date = nice_date
    two_digit = two_digit
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
    COLORING = COLORING
    ALL_SAVES = ALL_SAVES
    encodeURIComponent = encodeURIComponent
    @external
    class Worker: # pylint: disable=function-redefined,too-few-public-methods
        """Needed for rapydscript"""
        def postMessage(self, _message):
            """Send a message to the worker"""
except: # pylint: disable=bare-except
    pass

EXPLAIN = {0: "Sauvée", 1: "Validée", 2: "Compilée", 3: "Dernière seconde"}

DEPRECATED = ('save_button', 'local_button', 'stop_button', 'reset_button')

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

def cleanup(txt):
    """Remove character badly handled by browser with getSelection().toString()"""
    return txt.replace(RegExp('[  \n\r\t]', 'g'), '')

class CCCCC: # pylint: disable=too-many-public-methods
    """Create the GUI and launch worker"""
    question = editor = overlay = tester = compiler = executor = time = None
    index = popup_element = save_button = local_button = line_numbers = None
    stop_button = fullscreen = comments = save_history = editor_title = None
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
    cursor_position = 0
    insert_on_keyup = None
    do_coloring = True
    do_update_cursor_position = True
    mouse_pressed = -1
    mouse_position = [0, 0]
    options = {
        'language': 'javascript',
        'forbiden': "Coller du texte copié venant d'ailleurs n'est pas autorisé.",
        'close': "Voulez-vous vraiment quitter cette page ?",
        'allow_copy_paste': CP or GRADING,
        'save_unlock': SAVE_UNLOCK,
        'coloring': COLORING,
        'display_local_save': 0,
        'positions' : {
            'question': [1, 29, 0, 30, '#EFE'],
            'tester': [1, 29, 30, 70, '#EFE'],
            'editor': [30, 40, 0, 100, '#FFF'],
            'compiler': [70, 30, 0, 30, '#EEF'],
            'executor': [70, 30, 30, 70, '#EEF'],
            'time': [80, 20, 98, 2, '#0000'],
            'index': [0, 1, 0, 100, '#0000'],
            'line_numbers': [100, 1, 0, 100, '#EEE'], # Outside the screen by defaut
            'editor_title': [30, 40, 0, 1, '#FFF'], # Overrided by current editor
            }
    }
    stop_timestamp = 0
    last_save = 0
    in_past_history = 0
    allow_edit = 0

    def __init__(self):
        print("GUI: start")
        self.start_time = millisecs()
        self.course = COURSE
        self.stop_timestamp = STOP
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
        if GRADING:
            self.options['positions']['grading'] = [0, 1, 0, 75, '#FFF8']
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
        self.options['positions']['editor_title'] = self.options['positions']['editor']
        self.options['positions']['overlay'] = self.options['positions']['editor']
        self.options['positions']['overlay'][4] = '#0000'
        if GRADING:
            left, width, top, height, background = self.options['positions']['editor']
            self.options['positions']['comments'] = [
                left + width, 100 - (left + width), top, height]
            left, width, top, height, background = self.options['positions']['question']
            self.options['positions']['question'][2] = 75
            self.options['positions']['question'][3] = 25
            self.options['positions']['grading'] = [left, width, 0, 75, '#FFF8']

        for key in self.options['positions']:
            if key in DEPRECATED:
                continue # No more used button
            left, width, top, height, background = self.options['positions'][key]
            e = self[key] # pylint: disable=unsubscriptable-object
            if not e:
                continue
            if left >= 100 or top >= 100:
                e.style.display = 'none'
            else:
                e.style.display = 'block'
            e.style.left = left + '%'
            e.style.right = (100 - left - width) + '%'
            if key in ('editor', 'overlay'):
                e.style.top = 'calc(' + top + '% + var(--header_height))'
                e.style.bottom = 'calc(' + (100 - top - height) + '% - var(--header_height))' 
            else:
                e.style.top = top + '%'
                e.style.bottom = (100 - top - height) + '%'
            if key == 'editor_title':
                e.style.bottom = 'calc(100% - var(--header_height))'
            e.style.background = background
            e.background = background
        self.save_history.onchange = bind(self.change_history, self)
        if GRADING:
            self.save_button.style.display = 'none'
            if self.stop_button:
                self.stop_button.style.display = 'none'
        self.update_save_history()
    def create_gui(self):
        """The text editor container"""
        self.options['positions']['overlay'] = self.options['positions']['editor']
        if GRADING:
            self.options['positions']['comments'] = [] # Filled by update_gui()
        for key in self.options['positions']:
            if key == 'stop_button' and not CHECKPOINT:
                continue
            if key in DEPRECATED:
                print(key, "this block position is no more used")
                continue # No more used button
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
        self.editor.onmouseup = bind(self.update_cursor_position, self)
        self.editor.onkeyup = bind(self.update_cursor_position, self)
        self.editor.focus()

        self.editor_title.innerHTML = "<h2>Code source </h2>"

        self.save_button = document.createElement('TT')
        self.save_button.innerHTML = self.options['icon_save']
        self.save_button.style.fontFamily = 'emoji'
        self.save_button.onclick = bind(self.save_unlock, self)
        self.save_button.className = 'save_button'
        self.editor_title.firstChild.appendChild(self.save_button)

        self.save_history = document.createElement('SELECT')
        self.editor_title.firstChild.appendChild(self.save_history)

        self.tag_button = document.createElement('TT')
        self.tag_button.innerHTML = self.options['icon_tag']
        self.tag_button.style.fontFamily = 'emoji'
        self.tag_button.onclick = bind(self.record_tag, self)
        self.tag_button.className = 'tag_button'
        self.editor_title.firstChild.appendChild(self.tag_button)

        if GRADING:
            self.save_history.style.display = 'none'
            self.tag_button.style.display = 'none'

        if self.options['display_local_save']:
            self.local_button = document.createElement('TT')
            self.local_button.innerHTML = ' ' + self.options['icon_local']
            self.local_button.onclick = bind(self.save_local, self)
            self.editor_title.firstChild.appendChild(self.local_button)

        if CHECKPOINT:
            self.stop_button = document.createElement('TT')
            self.stop_button.innerHTML = self.options['icon_stop']
            self.stop_button.style.fontFamily = 'emoji'
            self.stop_button.onclick = bind(self.stop, self)
            self.stop_button.className = 'stop_button'
            self.editor_title.firstChild.appendChild(self.stop_button)

        self.fullscreen = document.createElement('DIV')
        self.fullscreen.className = 'fullscreen'
        self.fullscreen.innerHTML = """Appuyez sur la touche F11 pour passer en plein écran.<br>
        <small>Mettez le curseur sur <span>⏱</span> pour voir le temps restant</small>
        """
        self.top.appendChild(self.fullscreen)

    def record_tag(self):
        """Replace tag on current saved version"""
        timestamp = self.in_past_history
        if (timestamp == 0
                and ALL_SAVES[self.current_question]
                and len(ALL_SAVES[self.current_question])):
            timestamp = ALL_SAVES[self.current_question][-1][0]
        if timestamp <= 10:
            self.popup_message("Rien à nommer, il faut d'abord sauvegarder.")
            return
        self.do_not_register_this_blur = True
        tag = prompt("Nom de la sauvegarde :")
        if not tag or tag == 'null':
            return
        self.record(['tag', self.current_question, timestamp, tag], True)
        for item in ALL_SAVES[self.current_question]:
            if item[0] == timestamp:
                item[2] = tag
                break
        self.update_save_history()

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
        if not self.allow_edit:
            return
        if (not GRADING
                and not self.options['allow_copy_paste']
                and screen.height != max(window.innerHeight, window.outerHeight)
           ):
            self.fullscreen.style.display = 'block'
        else:
            self.fullscreen.style.display = 'none'

        if self.do_update_cursor_position:
            self.update_source()
            self.update_cursor_position_now()
            self.do_update_cursor_position = False

        if self.do_coloring:
            self.coloring()
            self.do_coloring = False

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
            if self.seconds % 5 == 0:
                self.update_save_history()
            if self.need_save():
                self.save_button.style.opacity = 1
            else:
                self.save_button.style.opacity = 0.2
            self.seconds = seconds
            timer = document.getElementById('timer')
            if timer:
                delta = self.stop_timestamp - seconds # pylint: disable=undefined-variable
                if delta == 10:
                    if seconds - self.last_save > 60 :
                        # The student has not saved in the last minute
                        self.record(['snapshot', self.current_question, self.source], send_now=True)
                    else:
                        self.record_now()
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
    def clear_highlight_errors(self, update_cursor=True):
        """Make space fo the new errors"""
        for key in self.highlight_errors:
            if self.highlight_errors[key] and not self.highlight_errors[key].startswith('cursor'):
                self.highlight_errors[key] = None
        while (self.overlay.lastChild
               and self.overlay.lastChild.className
               and 'ERROR' in self.overlay.lastChild.className):
            self.overlay.removeChild(self.overlay.lastChild)
        if update_cursor:
            self.update_cursor_position()
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
        self.overlay.innerHTML = html(self.source_with_newlines)
        self.overlay.className = 'overlay language-' + self.options['language']
        if self.options.coloring:
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
                comment = self.comments.childNodes[i]
                if not comment:
                    comment = document.createElement('TEXTAREA')
                    comment.line = i
                    comment.style.top = top + 'px'
                    self.comments.appendChild(comment)
                comment.textContent = (comments[i] or '').strip()
                comment.className = comments[i] and 'filled' or 'empty'
                if comments[i]:
                    lines = comments[i].strip().split('\n')
                    comment.rows = len(lines)
                    comment.cols = min(max([len(line) for line in lines]), 50)
                else:
                    comment.rows = 3
                    comment.cols = 40

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

    def record_done(self, stop_timestamp):
        """The server saved the recorded value"""
        self.stop_timestamp = stop_timestamp
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
        if not what:
            return
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
        # Goto first text element of the line
        while line.previousSibling and not line.previousSibling.tagName:
            line = line.previousSibling
        # Search the text element containing the column
        while char_nr > len(line.nodeValue or line.innerText):
            if line.nextSibling.tagName:
                print('BUG')
                char_nr = len(line.nodeValue or line.innerText)
                break
            char_nr -= len(line.nodeValue or line.innerText)
            line = line.nextSibling
        box.selectNode(line)
        error = document.createElement('DIV')
        if not what.startswith('cursor'):
            insert(error, 'ERROR ' + what)
        try:
            if char_nr > (line.nodeValue or line.innerText).length:
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
        self.mouse_pressed = event.button
        if self.close_popup(event):
            return
        self.record('MouseDown')
    def onmouseup(self, event):
        """Mouse up"""
        self.mouse_pressed = -1
    def onmousemove(self, event):
        """Mouse move"""
        if event.target.tagName == 'CANVAS':
            self.mouse_position = [event.offsetX, event.offsetY]
    def oncopy(self, event, what='Copy'):
        """Copy"""
        if self.options['allow_copy_paste']:
            self.record(what)
            return
        text = cleanup(window.getSelection().toString())
        if text not in cleanup(self.source) and text not in cleanup(self.question.innerText):
            self.record(what + 'Rejected')
            self.popup_message(self.options['forbiden'])
            event.preventDefault(True)
            return
        self.record(what + 'Allowed')
        self.copied = text
    def oncut(self, event):
        """Cut"""
        if not self.allow_edit:
            self.record(['allow_edit', 'oncut'])
            event.preventDefault(True)
            return
        self.oncopy(event, 'Cut')
        self.do_coloring = self.do_update_cursor_position = True
    def insert_text(self, event, text):
        """Insert the pasted text"""
        self.overlay_hide()
        if event.type == 'drop':
            self.do_coloring = self.do_update_cursor_position = True
        else:
            document.execCommand('insertText', False, text)
            event.preventDefault(True)
            self.do_coloring = self.do_update_cursor_position = True

    def onpaste(self, event):
        """Text paste"""
        if not self.allow_edit:
            self.record(['allow_edit', 'onpaste'])
            event.preventDefault(True)
            return
        text = (event.clipboardData or event.dataTransfer).getData("text")
        text_clean = cleanup(text)
        if self.options['allow_copy_paste']:
            self.record('Paste')
            self.insert_text(event, text)
            return
        if (text_clean in cleanup(self.source)
            or text_clean in cleanup(self.question.innerText)
            or text_clean == self.copied):
            self.record('PasteOk')
            self.insert_text(event, text)
            return # auto paste allowed
        self.record('PasteRejected')
        self.popup_message(self.options['forbiden'])
        event.preventDefault(True)

    def get_line_column(self, position):
        """Get the cursor coordinates from the text"""
        lines = self.source[:position].split('\n')
        return len(lines), len(lines[-1])

    def highlight_bloc(self):
        """Highlight first inner parenthesis containing the cursor"""
        start = self.cursor_position - 1
        counters = {'{': 0, '(': 0, '[': 0}
        while start >= 0:
            if self.source[start] in '{[(':
                if counters[self.source[start]] == 0:
                    break
                counters[self.source[start]] -= 1
            elif self.source[start] in '}])':
                counters[{'}': '{', ')': '(', ']': '['}[self.source[start]]] += 1
            start -= 1
        if start == -1:
            return
        stop = start + 1
        opening = self.source[start]
        closing = {'{': '}', '(': ')', '[': ']'}[opening]
        nr = 1
        while nr and stop and stop < len(self.source):
            char = self.source[stop]
            if char == opening:
                nr += 1
            elif char == closing:
                nr -= 1
            stop += 1
        if nr == 0:
            line_open, column_open = self.get_line_column(start + 1)
            self.highlight_errors[line_open + ':' + column_open] = 'cursor'
            line_close, column_close = self.get_line_column(stop)
            self.highlight_errors[line_close + ':' + column_close] = 'cursor'

    def highlight_unbalanced(self, close='', start=0):
        """Highlight unbalanced parenthesis. Returns the next character to check"""
        origin = start
        while start < len(self.source):
            if self.source[start] in ')}]':
                if self.source[start] == close:
                    return start + 1
                line_bad, column_bad = self.get_line_column(start + 1)
                self.highlight_errors[line_bad + ':' + column_bad] = 'cursorbad'
                if close:
                    return start
            elif self.source[start] in '([{':
                start = self.highlight_unbalanced(
                    close={'{': '}', '(': ')', '[': ']'}[self.source[start]],
                    start=start+1)
                continue
            start += 1
        if close:
            line_bad, column_bad = self.get_line_column(origin)
            self.highlight_errors[line_bad + ':' + column_bad] = 'cursorbad'
        return start

    def update_cursor_position_now(self):
        """Get the cursor position
        pos = [current_position, do_div_br_collapse]
        """
        # Remove old cursor position
        for key in self.highlight_errors:
            if self.highlight_errors[key] and self.highlight_errors[key].startswith('cursor'):
                self.highlight_errors[key] = None
        self.do_coloring = True
        cursor = document.getSelection().getRangeAt(0).cloneRange()
        cursor.setStart(self.editor.firstChild, 0)
        def walk(node, pos):
            for child in node.childNodes:
                if child.tagName == 'BR':
                    #print('BR', pos, '+1')
                    pos[0] += 1
                    pos[1] = True
                elif child.tagName: # DIV so newline
                    #print('DIV before', pos)
                    walk(child, pos)
                    #print('DIV after', pos)
                    if not pos[1]:
                        pos[0] += 1
                else:
                    #print('TEXT', pos, '+' + child.textContent.length , child.textContent)
                    pos[0] += child.textContent.length
                    if child.textContent.length:
                        pos[1] = False
        pos = [0, False]
        left = cursor.cloneContents()
        walk(left, pos)
        if left.lastChild and left.lastChild.tagName == 'DIV':
            pos[0] -= 1
        self.cursor_position = pos[0]
        self.highlight_unbalanced()
        self.highlight_bloc()

    def update_cursor_position(self):
        """Queue cursor update position"""
        self.do_update_cursor_position = True

    def save_cursor(self):
        """Save the cursor position"""
        self.last_answer_cursor[self.current_question] = [
            self.editor.scrollTop,
            self.cursor_position,
            self.source[:self.cursor_position]
            ]
    def onkeydown(self, event):
        """Key down"""
        if not self.allow_edit:
            self.record(['allow_edit', 'onkeydown'])
        if not self.allow_edit:
            event.preventDefault(True)
            return
        self.current_key = event.key
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
            self.update_source()
            self.update_cursor_position_now()
            i = self.cursor_position
            while i > 0 and self.source[i-1] != '\n':
                i -= 1
            j = i
            while j < self.cursor_position and self.source[j] in '\t ':
                j += 1
            if j != i:
                self.insert_on_keyup = self.source[i:j]
        elif len(event.key) > 1 and event.key not in ('Delete', 'Backspace'):
            return # Do not hide overlay: its only a cursor move
        if event.target.tagName == 'TEXTAREA':
            # The teacher enter a comment
            return
        self.overlay_hide()
    def onkeyup(self, event):
        """Key up"""
        if not self.allow_edit:
            self.record(['allow_edit', 'onkeyup'])
            event.preventDefault(True)
            return
        self.current_key = ''
        if event.target.tagName == 'TEXTAREA':
            # The teacher enter a comment
            return
        if event.key not in ('Left', 'Right', 'Up', 'Down'):
            if self.insert_on_keyup:
                document.execCommand('insertHTML', False, self.insert_on_keyup)
                self.insert_on_keyup = None
            self.do_coloring = True
        #print("CURSOR", self.cursor_position,
        #    JSON.stringify(self.source[self.cursor_position-10:self.cursor_position]),
        #    JSON.stringify(self.source[self.cursor_position:self.cursor_position+10]))
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

    def change_history(self, event):
        """Put an old version in the editor"""
        if not self.in_past_history:
            self.save()
        choosen = event.target.selectedOptions[0].getAttribute('timestamp')
        if choosen:
            choosen = int(choosen)
            if choosen == 1:
                self.set_editor_content(self.question_original[self.current_question])
                self.in_past_history = 1
            else:
                for (timestamp, source, _tag) in ALL_SAVES[self.current_question]:
                    if timestamp == choosen:
                        self.set_editor_content(source)
                        if timestamp == ALL_SAVES[self.current_question][-1][0]:
                            self.in_past_history = 0 # Back to the present
                        else:
                            self.in_past_history = timestamp
                            self.editor.focus()
                            self.update_save_history()
                        break

    def update_save_history(self):
        """The list of saved versions"""
        if self.save_history == document.activeElement:
            return
        content = []
        now = millisecs() / 1000
        for (timestamp, _source, tag) in (ALL_SAVES[self.current_question] or [])[::-1]:
            delta = int( (now - timestamp) / 10 ) * 10
            content.append('<option timestamp="' + timestamp + '"')
            if self.in_past_history == timestamp:
                content.append(' selected')
            content.append('>')
            if delta < 10:
                content.append("Sauvé à l'instant")
            elif delta < 60:
                content.append('Sauvé il y a ' + delta + 's')
            elif delta < 60*60:
                content.append('Sauvé il y a ' + delta//60 + 'm' + two_digit(delta%60))
            elif delta < 10*60*60:
                content.append('Sauvé il y a ' + delta//60//60 + 'h' + two_digit((delta//60)%60))
            else:
                date = Date()
                date.setTime(1000 * timestamp)
                content.append(nice_date(timestamp))
            if tag != '':
                content[-1] = tag # + ' ' + content[-1]
            content.append('</option>')
        if len(content) == 0:
            content.append('<option>JAMAIS SAUVEGARDÉ</option>')
            self.save_history.style.color = "#F00"
        else:
            self.save_history.style.color = "#000"
        content.append('<option timestamp="1">Version initiale</option>')
        if self.in_past_history == 1:
            content[-1] = content[-1].replace('<option', '<option selected')
        self.save_history.innerHTML = ''.join(content)

    def need_save(self):
        return (not self.last_answer[self.current_question]
                or self.last_answer[self.current_question].strip() != self.source.strip())

    def save(self):
        """Save the editor content"""
        if not self.allow_edit:
            self.record(['allow_edit', 'save'])
            return
        self.update_source()
        if self.need_save():
            self.save_button.style.transition = ''
            self.save_button.style.transform = 'scale(8)'
            self.save_button.style.opacity = 0.1
            self.record(['save', self.current_question, self.source], send_now=True)
            self.worker.postMessage(['source', self.current_question, self.source])
            self.last_answer[self.current_question] = self.source
            self.last_save = millisecs() / 1000
            if not ALL_SAVES[self.current_question]:
                ALL_SAVES[self.current_question] = []
            ALL_SAVES[self.current_question].append([int(self.last_save), self.source, ''])
            self.in_past_history = 0
            self.update_save_history()
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
        if self.need_save() and confirm(self.options['stop_confirm']):
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
        self.do_coloring = True

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
        element.innerHTML = '<i style="color:#00F">Préparer mail</i> Σ=' + grading_sum
        element.onclick = bind(self.send_mail, self)
        if self.nr_grades == nr_grades:
            element.style.background = "#0F0"
            element.style.color = "#000"
        else:
            element.style.background = "#FFF"
            element.style.color = "#0F0"

    def get_comment(self, line_number):
        """Get the actual line comment"""
        comment = self.all_comments[self.current_question]
        if comment:
            comment = comment[self.version]
            if comment:
                comment = comment[line_number]
        return comment

    def send_mail_right(self):
        """Send a mail to the student"""
        width = 0
        for line in self.source.split("\n"):
            width = max(width, len(line))
        content = ['<pre>']
        for i, line in enumerate(self.source.split("\n")):
            content.append(html(line))
            for _ in range(width - len(line)):
                content.append(' ')
            content.append('//')
            comment = self.get_comment(i)
            if comment:
                add_blank = False
                for comment_line in comment.strip().split('\n'):
                    if add_blank:
                        content.append('\n')
                        for _ in range(width):
                            content.append(' ')
                        content.append('//')
                    content.append(html(comment_line))
                    add_blank = True
            content.append('\n')
        content.append("</pre>")
        return content

    def send_mail_top(self):
        """Send a mail to the student"""
        content = ['<pre>']
        for i, line in enumerate(self.source.split("\n")):
            comment = self.get_comment(i)
            if comment:
                content.append('\n')
                for comment_line in comment.strip().split('\n'):
                    content.append('// ' + LOGIN + ' : ')
                    content.append(html(comment_line))
                    content.append('\n')
            content.append(html(line))
            content.append('\n')
        content.append("</pre>")
        return content

    def send_mail(self, right=True):
        """Prepare mail for student"""
        if confirm('''OK pour mettre les commentaires à droite des lignes.

CANCEL pour les mettre au dessus des lignes de code.'''):
            content = self.send_mail_right()
        else:
            content = self.send_mail_top()
        window.location = ("mailto:" + INFOS['mail']
            + "?subject=" + encodeURIComponent(COURSE.split('=')[1])
            + "&html-body="
            + encodeURIComponent(''.join(content))
            )

    def add_grading(self):
        """HTML of the grading interface"""
        content = [
            '''<div><h2>
            Noter <select style="background:#FF0" onchange="version_change(this)">
            '''
            ]
        now = Date()
        for i, version in enumerate(VERSIONS[self.current_question] or []):
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
                content.append(two_digit(now.getDate()))
                content.append('/')
                content.append(two_digit(now.getMonth() + 1))
                content.append(' ')
                content.append(two_digit(now.getHours()))
                content.append(':')
                content.append(two_digit(now.getMinutes()))
                content.append(':')
                content.append(two_digit(now.getSeconds()))
            content.append('</option>')
        content.append('</select>')
        content.append('<span id="grading_sum"></span>')
        content.append('</h2></div><pre>')
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
        content.append('</pre>')
        self.nr_grades = i
        self.grading.id = "grading"
        self.grading.onclick = grade
        self.grading.innerHTML = ''.join(content)

    def onmessage(self, event): # pylint: disable=too-many-branches,too-many-statements
        """Interprete messages from the worker: update self.messages"""
        what = event.data[0]
        # print(millisecs(), self.state, what, str(event.data[1])[:10])
        value = event.data[1]
        if what == 'options':
            for key in value:
                if key == 'positions':
                    for subkey in value[key]:
                        self.options[key][subkey] = value[key][subkey]
                else:
                    self.options[key] = value[key]
            self.terminate_init()
            self.update_gui()
        elif what == 'current_question':
            self.do_not_clear = {}
            self.update_source()
            self.save_cursor()
            if (self.current_question >= 0 and value != self.current_question
                    and self.need_save() and not self.in_past_history):
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
            for value in value.split('\001'):
                if not value:
                    continue
                if value.startswith('\002EVAL'):
                    #print(value[5:])
                    eval(value[5:])
                elif value.startswith('\002RACKET'):
                    self.racket(value[7:])
                elif value.startswith('\002WAIT'):
                    #print(value)
                    if value[5] == 'T':
                        def answer():
                            self.send_input('WAITDONE')
                        setTimeout(answer, int(value[6:]))
                    if value[5] == 'D':
                        key = (self.current_key or 'None')
                        key += '\n' + self.mouse_pressed
                        key += '\n' + self.mouse_position[0]
                        key += '\n' + self.mouse_position[1]
                        key += '\n' + ''.join([' '+i.width+' '+i.height for i in G.images if i])
                        self.send_input(key)
                    if value[5] == 'K':
                        def onkeypress(event):
                            self.send_input(event.key)
                            G.canvas.onkeyup = None
                            event.stopPropagation()
                            event.preventDefault()
                        G.canvas.onkeyup = onkeypress
                elif value == '\002INPUT':
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
                    if value[-1] not in '>\n':
                        span.style.float = 'left'
                    self.executor.appendChild(span) # pylint: disable=unsubscriptable-object
        elif what == 'index':
            content = ('<div class="questions">'
                + '<a href="/' + window.location.search + '">🏠</a>'
                + '<div class="tips">Accueil C5</div></div><br>'
                + '<div class="questions">'
                + '<a target="_blank" href="/zip/' + COURSE + window.location.search + '">'
                + self.options['icon_local'] + '</a>'
                + '<div class="questions">'
                + '<a target="_blank" href="/git/' + COURSE + window.location.search + '">'
                + self.options['icon_git'] + '</a>'
                + '<div class="tips">GIT de vos réponses</div></div><br>')
            if GRADING and ',' in WHERE[2]:
                content += '<div class="version">' + WHERE[2].split(',')[3].replace('a', 'Ⓐ').replace('b', 'Ⓑ') + '</div>'
            content += value
            self[what].innerHTML = content # pylint: disable=unsubscriptable-object
        elif what == 'editor':
            # New question
            self.compile_now = True
            message = value + '\n\n\n'
            self.set_editor_content(message)
        elif what == 'default':
            self.question_original[value[0]] = value[1]
        elif what in ('tester', 'compiler', 'question', 'time'):
            self.clear_if_needed(what)
            if what == 'time':
                value += ' ' + self.state + ' ' + LOGIN
            if what == 'question' and GRADING and self[what].childNodes.length == 0: # pylint: disable=unsubscriptable-object
                self.add_grading()
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
        elif what == 'allow_edit':
            self.allow_edit = int(value)

    def goto_question(self, index):
        """Indicate the new question to the worker"""
        if self.allow_edit:
            self.unlock_worker()
            self.worker.postMessage(['goto', index])
        else:
            self.record(['allow_edit', 'goto_question'])

    def set_editor_content(self, message):
        """Set the editor content (question change or reset)"""
        self.overlay_hide()
        self.editor.innerText = message
        if self.last_answer_cursor[self.current_question]:
            scrollpos, cursorpos, left = self.last_answer_cursor[self.current_question]
            if message[:cursorpos] != left:
                def nr_letters(txt):
                    return len(txt.replace(RegExp('[ \t\n]', 'g'), ''))
                nr_letters_old = nr_letters(left)
                nr_letters_new = nr_letters(message[:cursorpos])
                i = cursorpos
                size = len(message)
                while True: # Search position not using white space
                    if nr_letters_old > nr_letters_new:
                        if message[i] not in ' \t\n':
                            nr_letters_new += 1
                        i += 1
                    elif nr_letters_old < nr_letters_new:
                        i -= 1
                        if i < size and message[i] not in ' \t\n':
                            nr_letters_new -= 1
                    else:
                        break
                while i > 0 and message[i-1] in ' \t\n':
                    i -= 1
                # Search the good line
                nr_newline_before = 0
                for char in left[::-1]:
                    if char == '\n':
                        nr_newline_before += 1
                    elif char not in ' \t':
                        break
                while nr_newline_before and i < size and message[i] in ' \t\n':
                    if message[i] == '\n':
                        nr_newline_before -= 1
                    i += 1
                # Search the good space
                nr_space_before = 0
                for char in left[::-1]:
                    if char in ' \t':
                        nr_space_before += 1
                    else:
                        break
                while nr_space_before and i < size and message[i] in ' \t':
                    nr_space_before -= 1
                    i += 1
                cursorpos = i

            self.editor.scrollTop = scrollpos
            for line in self.editor.childNodes:
                if line.tagName:
                    cursorpos -= 1
                    if cursorpos < 0:
                        document.getSelection().collapse(line, 0)
                        break
                    continue
                cursorpos -= len(line.textContent)
                if cursorpos < 0:
                    document.getSelection().collapse(line, cursorpos + len(line.textContent))
                    break
        else:
            self.editor.scrollTop = 0
        # document.getSelection().collapse(self.editor, self.editor.childNodes.length)
        self.highlight_errors = {}
        self.do_coloring = True

    def onbeforeunload(self, event):
        """Prevent page closing"""
        if self.options['close'] == '' or GRADING:
            return None
        # self.record("Close", send_now=True) # The form cannot be submited
        event.preventDefault()
        event.returnValue = self.options['close']
        return event.returnValue

    def create_html(self):
        """Create the page content"""
        self.top = document.createElement('DIV')
        self.top.onmousedown = bind(self.onmousedown, self)
        self.top.onmouseup = bind(self.onmouseup, self)
        self.top.onmousemove = bind(self.onmousemove, self)
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
        setInterval(bind(self.scheduler, self), 200)
        if GRADING:
            self.comments.onclick = bind(self.add_comment, self)
            self.comments.onblur = bind(self.save_comment, self)
            # Get grades
            do_post_data({'student': STUDENT}, 'record_grade/' + COURSE + '?ticket=' + TICKET)
            do_post_data({'student': STUDENT}, 'record_comment/' + COURSE + '?ticket=' + TICKET)
        self.update_gui()

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

    def racket(self, text):
        text = text.split('\n')
        if ':::' in text[0]:
            position = int(text[0].split(':::')[1].split(' ')[0])
        else:
            text = ['', text[0]]
        def highlight(event):
            line, column = self.get_line_column(position)
            self.add_highlight_errors(line, column, 'eval')
            event.target.style.background = "#FF0"
            line_number = document.createElement("VAR")
            line_number.textContent = 'Ligne ' + line
            event.target.appendChild(line_number)
        def unhighlight(event):
            event.target.style.background = ""
            self.clear_highlight_errors(False)
            event.target.removeChild(event.target.lastChild)
        span = document.createElement('DIV')
        span.innerHTML = '\n'.join(text[1:])
        span.onmouseenter = highlight
        span.onmouseleave = unhighlight
        self.executor.appendChild(span) # pylint: disable=unsubscriptable-object



class Plot:
    def __init__(self, ctx, height, bcolor):
        self.max = 10000
        self.curves = []
        self.ctx = ctx
        self.height = height
        self.bcolor = bcolor

    def set_size(self, nb):
        """Maximum number of points"""
        self.max = nb

    def add(self, x, y, curve=0):
        """Add a point on the curve"""
        points = self.curves[curve]
        if not points:
            self.curves[curve] = points = []
        if len(points) == self.max:
            points.splice(0, 1)
        points.append([x, y])

    def minmax(self):
        """Size of plots"""
        xmin = ymin = 1e100
        xmax = ymax = -1e100
        for curve in self.curves:
            for x, y in curve:
                if x < xmin:
                    xmin = x
                if x > xmax:
                    xmax = x
                if y < ymin:
                    ymin = y
                if y > ymax:
                    ymax = y
        return xmin, xmax, ymin, ymax

    def draw(self, x1, y1, x2, y2, clear):
        """Display the curves"""
        if clear:
            save_color = self.ctx.fillStyle
            self.ctx.fillStyle = self.bcolor
            self.ctx.fillRect(x1, self.height - y2, x2 - x1, y2 - y1)
            self.ctx.fillStyle = save_color

        xmin, xmax, ymin, ymax = self.minmax()
        def X(x):
            return (x - xmin) / (xmax - xmin) * (x2 - x1) + x1
        def Y(y):
            return self.height - ((y - ymin) / (ymax - ymin) * (y2 - y1) + y1)
        for curve in self.curves:
            self.ctx.beginPath()
            self.ctx.moveTo(X(curve[0][0]), Y(curve[0][1]))
            for x, y in curve[1:]:
                self.ctx.lineTo(X(x), Y(y))
            self.ctx.stroke()
        self.ctx.beginPath()
        self.ctx.moveTo(x1, self.height - y1)
        self.ctx.lineTo(x1, self.height - y2)
        self.ctx.stroke()
        self.ctx.beginPath()
        self.ctx.moveTo(x1, self.height - y1)
        self.ctx.lineTo(x2, self.height - y1)
        self.ctx.stroke()
        self.ctx.fillText(xmin, x1, self.height - y1 + 15)
        self.ctx.fillText(xmax, x2 - 50, self.height - y1 + 15)
        self.ctx.fillText(ymin, x1 - 30, self.height - y1)
        self.ctx.fillText(ymax, x1 - 30, self.height - y2)

class Grapic:
    """For the Grapic library emulator"""
    canvas = bcolor = ctx = height = width = None
    bcolor = '#000'
    plots = []
    images = []
    def __init__(self, cccc):
        self.ccccc = cccc

    def init(self, width, height):
        """Create the CANVAS"""
        self.canvas = document.createElement('CANVAS')
        self.canvas.tabIndex = 0
        self.bcolor = '#FFF'
        self.height = height
        self.width = width
        self.canvas.width = width
        self.canvas.height = height
        self.canvas.style.width = width + 'px'
        self.canvas.style.height = height + 'px'
        self.canvas.style.background = '#FFF'
        self.ccccc.executor.appendChild(self.canvas)
        self.ctx = self.canvas.getContext('2d')
        self.plots = []
        self.images = []
        self.ctxs = []
        self.canvas.onmouseenter = bind(self.canvas.focus, self.canvas)

    def quit(self):
        """Remove canvas"""
        if self.canvas and self.canvas.parentNode:
            self.canvas.parentNode.removeChild(self.canvas)

    def backgroundColor(self, r, v, b, a):
        """Set background color for erasing window"""
        n = 256*(256*(256+r) + v) + b # Starts with 1
        if a:
            n = 256*n + a
        self.bcolor = '#' + n.toString(16)[1:] # Remove the 1

    def color(self, r, v, b):
        """Set foreground coloe"""
        n = 256*(256*(256+r) + v) + b # Starts with 1
        self.ctx.fillStyle = self.ctx.strokeStyle = '#' + n.toString(16)[1:] # Remove the 1

    def clear(self):
        """Clear canvas"""
        save_color = self.ctx.fillStyle
        self.ctx.fillStyle = self.bcolor
        self.ctx.fillRect(0, 0, 10000, 10000)
        self.ctx.fillStyle = save_color

    def fontSize(self, size):
        """Set the font size"""
        self.ctx.font = size + 'px sans-serif'

    def print(self, x, y, text):
        """Display text"""
        self.ctx.fillText(text, x, self.height - y)

    def rectangle(self, xmin, ymin, xmax, ymax):
        """Rectangle"""
        self.ctx.strokeRect(xmin, self.height - ymax, xmax - xmin, ymax - ymin)

    def rectangleFill(self, xmin, ymin, xmax, ymax):
        """Filled rectangle"""
        self.ctx.fillRect(xmin, self.height - ymax, xmax - xmin, ymax - ymin)

    def circle(self, x, y, radius):
        """Circle"""
        self.ctx.beginPath()
        self.ctx.arc(x, self.height - y, radius, 0, 2*Math.PI)
        self.ctx.closePath()
        self.ctx.stroke()

    def circleFill(self, x, y, radius):
        """Disc"""
        self.ctx.beginPath()
        self.ctx.arc(x, self.height - y, radius, 0, 2*Math.PI)
        self.ctx.closePath()
        self.ctx.fill()

    def ellipse(self, x, y, rx, ry):
        """Ellipse"""
        self.ctx.beginPath()
        self.ctx.ellipse(x, self.height - y, rx, ry, 0, 0, 2*Math.PI)
        self.ctx.closePath()
        self.ctx.stroke()

    def ellipseFill(self, x, y, rx, ry):
        """Ellipse"""
        self.ctx.beginPath()
        self.ctx.ellipse(x, self.height - y, rx, ry, 0, 0, 2*Math.PI)
        self.ctx.closePath()
        self.ctx.fill()

    def line(self, x1, y1, x2, y2):
        """A segment"""
        self.ctx.beginPath()
        self.ctx.moveTo(x1, self.height - y1)
        self.ctx.lineTo(x2, self.height - y2)
        self.ctx.stroke()

    def triangle(self, x1, y1, x2, y2, x3, y3):
        """Triangle"""
        self.ctx.beginPath()
        self.ctx.moveTo(x1, self.height - y1)
        self.ctx.lineTo(x2, self.height - y2)
        self.ctx.lineTo(x3, self.height - y3)
        self.ctx.closePath()
        self.ctx.stroke()

    def triangleFill(self, x1, y1, x2, y2, x3, y3):
        """Triangle"""
        self.ctx.beginPath()
        self.ctx.moveTo(x1, self.height - y1)
        self.ctx.lineTo(x2, self.height - y2)
        self.ctx.lineTo(x3, self.height - y3)
        self.ctx.closePath()
        self.ctx.fill()

    def path(self, points):
        """Create a path"""
        self.ctx.beginPath()
        self.ctx.moveTo(points[0][0], self.height - points[0][1])
        for x, y in points[1:]:
            self.ctx.lineTo(x, self.height - y)
        self.ctx.closePath()

    def polygon(self, points):
        """Polygon"""
        self.path(points)
        self.ctx.stroke()

    def polygonFill(self, points):
        """Polygon"""
        self.path(points)
        self.ctx.fill()

    def grid(self, x1, y1, x2, y2, nx, ny):
        """A Grid"""
        # Horizontals
        for i in range(ny+1):
            self.ctx.beginPath()
            self.ctx.moveTo(x1, self.height - y1 - i * (y2 - y1)/ny)
            self.ctx.lineTo(x2, self.height - y1 - i * (y2 - y1)/ny)
            self.ctx.stroke()
        # Verticals
        for i in range(nx+1):
            self.ctx.beginPath()
            self.ctx.moveTo(x1 + i * (x2 - x1)/nx, self.height - y1)
            self.ctx.lineTo(x1 + i * (x2 - x1)/nx, self.height - y2)
            self.ctx.stroke()

    def plot(self, nr):
        """Add a new plot"""
        if nr == 0:
            self.plots = []
        self.plots.append(Plot(self.ctx, self.height, self.bcolor))

    def new_image(self, url, h):
        """Image from web"""
        if h:
            canvas = eval('new OffscreenCanvas(' + url + ',' + h + ')')  # pylint: disable=eval-used
            self.images.append(canvas)
            self.ctxs.append(canvas.getContext('2d'))
            return
        def onload():
            canvas = eval('new OffscreenCanvas(' + img.width + ',' + img.height + ')')  # pylint: disable=eval-used
            self.images[img_index] = canvas
            self.ctxs[img_index] = canvas.getContext('2d')
            self.ctxs[img_index].drawImage(img, 0, 0)
        img_index = len(self.images)
        self.images.append(None)
        img = eval('new Image') # pylint: disable=eval-used
        img.src = '/media/' + COURSE + '/' + url + window.location.search
        img.onload = onload

    def image_draw(self, image_id, x, y, w, h, angle, flip):
        """Put image on canvas"""
        if not self.images[image_id]:
            return
        width, height = self.images[image_id].width, self.images[image_id].height
        y = self.height - y
        if w < 0:
            w = width
        if h < 0:
            h = height
        self.ctx.save()
        self.ctx.translate(x + w/2, y - h/2)
        if flip & 1:
            self.ctx.scale(-1, 1)
            angle *= -1
        if flip & 2:
            self.ctx.scale(1, -1)
            angle *= -1
        self.ctx.rotate(angle)
        self.ctx.drawImage(self.images[image_id], -w/2, -h/2, w, h)
        self.ctx.restore()
    def image_set(self, image_id, x, y, r, g, b, a):
        """Put pixel in the image"""
        if not self.ctxs[image_id]:
            return
        self.ctxs[image_id].fillStyle = "rgba("+r+","+g+","+b+","+(a/255)+")"
        self.ctxs[image_id].fillRect(x, y, 1, 1)

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
    ccccc.update_source()
    ccccc.compile_now = True

ccccc = CCCCC()
G = Grapic(ccccc)
