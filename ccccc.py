# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,len-as-condition

"""
To simplify the class contains the code for the GUI and the worker.

CCCCC          class manages the GUI
               It sends source code to the Compile worker with sendMessage
               It receives events to update the GUI
Compile        worker base class to manage the question list, compilation, execution
Question       base class for question definition
"""
try:
    @external
    class Worker: # pylint: disable=function-redefined,too-few-public-methods
        """Needed for rapydscript"""
        onmessage = onmessageerror = onerror = None
        def postMessage(self, _message):
            """Send a message to the worker"""
except: # pylint: disable=bare-except
    pass

DEPRECATED = ('save_button', 'local_button', 'stop_button', 'reset_button', 'line_numbers')

NAME_CHARS = '[a-zA-Z_0-9]'
NAME = RegExp(NAME_CHARS)
NAME_FIRST = RegExp('[a-zA-Z_]')

REAL_GRADING = GRADING
if not COURSE_CONFIG['display_grading']:
    GRADING = False

SHARED_WORKER, JOURNAL = create_shared_worker(LOGIN)
EDITMODE = ['', ''] # Journals without and with comments

IS_TEACHER = SESSION_LOGIN != STUDENT

def get_xhr_data(event):
    """Evaluate the received javascript"""
    if event.target.readyState == 4:
        try:
            if event.target.status == 200:
                if event.target.responseText.startswith('<'):
                    alert(event.target.responseText.split('<h1>')[1].split('</h1>'))
                else:
                    eval(event.target.responseText) # pylint: disable=eval-used
            else:
                eval(event.target.responseText.replace( # pylint: disable=eval-used
                    RegExp('//.*', 'g'), '').replace(RegExp('\n', 'g'), ' '))
        except: # pylint: disable=bare-except
            ccccc.record_error('BUG get_xhr_data ' + event.target.responseText)
        event.target.abort()

def get_xhr_error(event):
    """Display received error or timeout."""
    ccccc.record_error('BUG get_xhr_error ' + str(event))

def do_post_data(dictionary, url):
    """POST a dictionnary"""
    xhr = eval('new XMLHttpRequest()') # pylint: disable=eval-used
    xhr.addEventListener('readystatechange', get_xhr_data, False)
    xhr.addEventListener('error', get_xhr_error, False)
    xhr.addEventListener('timeout', get_xhr_error, False)
    xhr.responseType = 'text'
    xhr.open("POST", url, True)
    formData = eval('new FormData()') # pylint: disable=eval-used
    for key, value in dictionary.Items():
        formData.append(key, value)
    xhr.send(formData)

def cleanup(txt):
    """Remove character badly handled by browser with getSelection().toString()"""
    return txt.replace(RegExp('[  \n\r\t]', 'g'), '')

def walk(node, pos=None, depth=0):
    """Count the number of characters.
    pos[0] = current position.
    pos[1] is True if we are on a newline
    """
    if pos is None:
        pos = [0, True]
        # print(''.join([(i.outerHTML or i.textContent)  for i in node.childNodes]))
    for child in node.childNodes:
        # print('        '[:4*depth+1], '=' + str(pos),
        #       '/// Tag=' + child.tagName,
        #       '/// HTML=' + child.innerHTML,
        #       '/// Text=' + child.textContent)
        if child.tagName == 'BR':
            # print('        '[:4*depth+1], 'BR+1')
            pos[0] += 1
            pos[1] = True
        elif child.tagName == 'DIV':
            if not pos[1]:
                # print('        '[:4*depth+1], 'DIV+1')
                pos[0] += 1
            walk(child, pos, depth + 1)
        else:
            # print('        '[:4*depth+1], 'TEXT+' + child.textContent.length)
            pos[0] += child.textContent.length
            pos[1] = False # child.textContent[-1] == '\n'
    return pos[0]

def walk_regtests():
    """To debug walk"""
    div = document.createElement('DIV')
    for innerHTML, expected in [
        ["", 0],
        ["a", 1],
        ["<br>", 1],
        ["<br>#", 1],
        ["<br>a", 2],
        ["<div>a<br></div><div></div>", 2],
        ["<div>a<br></div><div>b</div>", 3],
        ["<div>a</div><div>b</div>", 3],
        ["a<div>b</div>", 3],
        ['a<span>b</span><div><span>c</span></div>', 4],
        ]:
        div.innerHTML = innerHTML
        if innerHTML[-1] == '#':
            div.childNodes[-1].textContent = ''
        computed = walk(div)
        if computed != expected:
            print("=======================================================")
            print("Found " + computed + " in place of " + expected)
            print("=======================================================")

walk_regtests()

def bubble_resize_do(event):
    ccccc.bubble_save_change()
    SHARED_WORKER.bubble_size(event.target.bubble_index,
                              (event.target.offsetWidth / ccccc.char_width).toFixed(2),
                              (event.target.offsetHeight / ccccc.line_height).toFixed(2))
    event.target.onmouseup = ''
    ccccc.do_coloring = 'bubble_resize'

def bubble_resize(entries):
    """Send bubble size change"""
    if not ccccc.resize_observer_active:
        return
    for entry in entries:
        if entry.target.nextSibling and entry.target.nextSibling.className == 'bubble_close':
            entry.target.nextSibling.remove()
        entry.target.onmouseup = bubble_resize_do

def stop_event(event):
    """Stop the event"""
    event.preventDefault(True)
    event.stopPropagation()
    event.stopImmediatePropagation()

class CCCCC: # pylint: disable=too-many-public-methods
    """Create the GUI and launch worker"""
    course = worker = shared_buffer = line_height = char_width = active_completion = completion = None
    grading_sum = competence_average = editmode = None
    server_time_delta = int(millisecs()/1000 - SERVER_TIME)
    question = editor = overlay = tester = compiler = executor = time = None
    index = save_button = local_button = line_numbers = None
    stop_button = fullscreen = comments = save_history = editor_title = None
    indent_button = layered = canvas = None
    top = None # Top page HTML element
    source = None # The source code to compile
    source_with_newlines = None
    old_source = None
    highlight_errors = {}
    question_original = {}
    copied = None # Copy with ^C ou ^X
    state = "uninitalised"
    input_index = -1 # The input number needed
    current_question = -1 # The question on screen
    compile_now = False
    editor_lines = []
    do_not_register_this_blur = False
    init_done = False
    seconds = 0
    start_time = 0
    do_not_clear = {}
    inputs = {} # User input in execution bloc
    grading_history = ''
    focus_on_next_input = False
    cursor_position = 0
    insert_on_keyup = None
    do_coloring = "default"
    do_update_cursor_position = True
    mouse_pressed = -1
    mouse_position = [0, 0]
    worker_url = None
    hover_bubble = None
    moving_bubble = None
    resize_observer_active = False
    add_comments = GRADING
     # These options are synchronized between GUI and compiler/session
    options = {}
    stop_timestamp = 0
    last_save = 0
    allow_edit = 0
    version = 0 # version being graded
    nr_grades = None
    grading = None
    current_key = None
    meter = document.createRange()
    span_highlighted = None # Racket eval result line highlighted
    first_F11 = True
    need_grading_update = True
    dialog_on_screen = False
    completion_running = False
    to_complete = ''
    last_scroll = 0 # Last scroll position sent to journal in seconds
    old_scroll_top = 0
    wait_indentation = False
    user_compilation = False
    journal_question = None
    old_delta = None

    def init(self):
        self.options = options = COURSE_CONFIG

        answers = {}
        for question_index, question in JOURNAL.questions.Items():
            answers[question_index] = [question.source, question.good]

        # XXX to remove
        options['allow_copy_paste'] = options.allow_copy_paste or GRADING or ADMIN
        options['COURSE'] = COURSE                         # Course short name
        options['TICKET'] = TICKET                         # Session ticket: ?ticket=TICKET
        options['LOGIN'] = LOGIN                           # Login of the connected user
        options['SOCK'] = SOCK                             # Websocked for remote compilation
        options['ANSWERS'] = answers                       # All the questions/answers recorded
        options['WHERE'] = WHERE                           # See 'active_teacher_room' declaration
        options['INFOS'] = INFOS                           # Student identity
        options['GRADING'] = GRADING                       # True if in grading mode
        options['ADMIN'] = ADMIN                           # True if administrator
        options['STOP'] = STOP                             # True if the session is stopped

        print("GUI: start")
        window.onerror = bind(self.onJSerror, self)
        self.start_time = millisecs()
        self.course = COURSE
        self.stop_timestamp = STOP
        self.worker_url = BASE + '/' + COURSE + "?ticket=" + TICKET
        if REAL_GRADING:
            self.worker_url += '&login=' + LOGIN
        self.worker = Worker(self.worker_url)
        self.worker.onmessage = bind(self.onmessage, self)
        self.worker.onmessageerror = bind(self.onerror, self)
        self.worker.onerror = bind(self.onSocketError, self)
        self.worker.postMessage(['config', self.options])
        try:
            self.shared_buffer = eval('new Int32Array(new SharedArrayBuffer(1024))') # pylint: disable=eval-used
        except: # pylint: disable=bare-except
            self.shared_buffer = None
        self.worker.postMessage(['array', self.shared_buffer])
        if GRADING or self.options['feedback'] >= 5:
            # Will be updated after
            self.options['positions']['grading'] = [0, 1, 0, 75, '#FFF8']

        self.resize_observer = eval('new ResizeObserver(bubble_resize)')
        print("GUI: wait worker")
        if options['state'] == 'Ready':
            self.add_comments = 0

    def onSocketError(self):
        """Can't start the worker"""
        window.location = self.worker_url # Because it contains the error message

    def terminate_init(self):
        """Only terminate init when the worker started"""
        if self.init_done:
            return
        self.init_done = True
        self.create_html()
        self.inputs = {} # Indexed by the question number
        self.do_not_clear = {}
        self.seconds = int(millisecs() / 1000)
        EDITMODE[0] = EDITMODE[1] = '\n'.join(JOURNAL.lines)
        print("GUI: init done")

    def popup_message(self, txt, cancel='', ok='OK', callback=None, add_input=False, init=None): # pylint: disable=no-self-use
        """For Alert and Prompt"""
        if self.dialog_on_screen:
            return
        self.dialog_on_screen = True
        popup = document.createElement('DIALOG')
        if callback and add_input:
            txt += '<br><input id="popup_input"'
            if init:
                txt += ' value="' + html(init).replace(RegExp('"', 'g'), '&#34;') + '"'
            txt += '>'
        if cancel != '':
            txt += '<button id="popup_cancel">' + cancel + '</button>'
        txt += '<button id="popup_ok">' + ok + '</button>'
        popup.innerHTML = txt
        document.body.appendChild(popup)

        def close(event):
            """Close the dialog"""
            self.dialog_on_screen = False
            try:
                document.body.removeChild(popup)
            except: # pylint: disable=bare-except
                # On examination termination : body.innerHTLM = ''
                pass
            stop_event(event)

        def validate(event):
            if callback:
                if add_input:
                    callback(document.getElementById('popup_input').value)
                else:
                    callback()
            close(event)

        if cancel != '':
            document.getElementById('popup_cancel').onclick = close
        document.getElementById('popup_ok').onclick = validate

        def enter_escape(event):
            """Enter is OK escape is Cancel"""
            if event.key == 'Enter':
                if event.target.tagName == 'INPUT' or event.target.id == 'popup_ok':
                    validate(event)
            elif event.key == 'Escape':
                close(event)
        popup.onkeydown = enter_escape
        popup.showModal()

    def prompt(self, txt, callback, init=None): # pylint: disable=no-self-use
        """Replace browser prompt"""
        self.popup_message(txt, "Annuler", "OK", callback, True, init)

    def send_input(self, string):
        """Send the input value to the worker"""
        if not self.shared_buffer:
            print("SharedArrayBuffer not allowed by HTTP server")
            return
        for i in range(len(string)):
            self.shared_buffer[i+1] = string.charCodeAt(i)
        self.shared_buffer[len(string) + 1] = -1 # String end
        self.shared_buffer[0] = 1

    def onJSerror(self, message, url_error, lineNumber, _column_number, error):
        """Send the JS error to the server"""
        def nothing():
            pass
        window.onerror = nothing # Only first error
        self.record_error('JS' + JSON.stringify([message,
            url_error.split('?')[0].replace(window.location.origin, ''),
            lineNumber,
            navigator.userAgent,
            (error and error.stack or 'NoStack').toString(
                ).replace(RegExp('[?].*', 'g'), ')'
                ).replace(RegExp(window.location.origin, 'g'), '')
            ]))
        return False

    def update_gui(self): # pylint: disable=too-many-branches,disable=too-many-statements
        """Set the bloc position and background"""
        if self.options['display_line_numbers']:
            self.layered.setAttribute('display_line_numbers', 'yes')
        else:
            self.layered.setAttribute('display_line_numbers', 'no')
        if self.add_comments:
            self.indent_button.style.opacity = 0.2
        else:
            self.indent_button.style.opacity = 1
        self.options['positions']['editor_title'] = self.options['positions']['editor']
        if GRADING or self.options['feedback'] >= 5:
            left, width, top, height, background = self.options['positions']['editor']
            self.options['positions']['comments'] = [
                left + width, 100 - (left + width), top, height]
            left, width, top, height, background = self.options['positions']['question']
            if COURSE_CONFIG['display_grading']:
                height = 75
            else:
                height = 20
            self.options['positions']['question'][2] = height
            self.options['positions']['question'][3] = 100 - height
            self.options['positions']['grading'] = [left, width, 0, height, '#FFF8']
            self.options['positions']['tester'][0] = 100 # Hide tester

        if document.body.classList.contains('versions'):
            version_height = '4em'
        else:
            version_height = '0px'

        for key in self.options['positions']:
            if key in DEPRECATED:
                continue # No more used button
            if key in ('line_numbers', 'comments'):
                continue
            left, width, top, height, background = self.options['positions'][key]
            e = self[key] # pylint: disable=unsubscriptable-object
            if key == 'editor':
                key = 'layered'
                e = self.layered
                self.overlay.style.right = '0px'
                self.editor.style.right = '0px'
                self.editor.style.paddingBottom = self.comments.style.paddingBottom = 0.9*self.layered.offsetHeight + 'px'
                self.editor.style.background = background
            if not e:
                continue
            if left >= 100 or top >= 100:
                e.style.display = 'none'
            else:
                e.style.display = 'block'
            e.style.left = left + '%'
            e.style.right = (100 - left - width) + '%'
            if key == 'layered':
                e.style.top = 'calc(' + top + '% + var(--header_height) + ' + version_height + ')'
            else:
                e.style.top = top + '%'
            e.style.bottom = (100 - top - height) + '%'
            if key == 'editor_title':
                e.style.bottom = 'calc(100% - var(--header_height) - ' + version_height + ')'
                e.firstChild.style.height = version_height
            if key != 'layered':
                e.style.background = background
                e.background = background
        self.save_history.onchange = bind(self.change_history, self)
        if GRADING or self.options['feedback']:
            self.save_button.style.display = 'none'
            if self.stop_button:
                self.stop_button.style.display = 'none'
        self.line_height = self.line_numbers.firstChild.offsetHeight
        self.canvas.height = self.canvas.parentNode.offsetHeight
        self.canvas.width = self.canvas.offsetWidth
    def create_gui(self): # pylint: disable=too-many-statements
        """The text editor container"""
        classes = []
        if GRADING:
            classes.append('dograding')
        if (self.options['version_for_teachers'] and IS_TEACHER
            or self.options['version_for_students'] and not IS_TEACHER):
            classes.append('versions')
        self.version_feedback = document.createElement('DIV')
        self.version_feedback.className = 'version_feedback'
        document.body.appendChild(self.version_feedback)
        document.body.className = ' '.join(classes)
        self.options['positions']['editor_title'] = self.options['positions']['editor']
        for key in self.options['positions']:
            if key == 'stop_button':
                continue
            if key in DEPRECATED:
                print(key, "this block position is no more used")
                continue # No more used button
            e = document.createElement('DIV')
            e.className = key
            e.style.position = 'absolute'
            self[key] = e # pylint: disable=unsupported-assignment-operation
            if key == 'editor':
                self.layered = document.createElement('DIV')
                self.layered.appendChild(e)
                self.layered.className = 'layered'
                self.overlay = document.createElement('DIV')
                self.overlay.className = 'overlay'
                self.layered.appendChild(self.overlay)
                self.line_numbers = document.createElement('DIV')
                self.line_numbers.className = 'line_numbers'
                def toggle_diff():
                    self.options['diff'] = not self.options['diff']
                    if self.options['diff']:
                        self.do_coloring = 'diff_enabled'
                    else:
                        for number in self.line_numbers.childNodes:
                            number.style.background = ''
                self.line_numbers.onclick = toggle_diff
                self.line_numbers.appendChild(document.createElement('DIV'))
                self.line_numbers.firstChild.textContent = '1'
                self.layered.appendChild(self.line_numbers)
                self.comments = document.createElement('DIV')
                self.comments.className = 'comments'
                self.layered.appendChild(self.comments)
                e = self.layered
            if GRADING and key in ('executor', 'compiler'):
                e.style.position = 'fixed'
                self.layered.appendChild(e)
            else:
                self.top.appendChild(e)
        self.editor.contentEditable = True
        self.editor.spellcheck = False
        self.editor.autocorrect = False
        self.editor.autocapitalize = False
        self.editor.autocomplete = False
        self.editor.onmouseup = bind(self.update_cursor_position, self)
        self.editor.onkeyup = bind(self.update_cursor_position, self)
        # self.editor.setAttribute('dropzone', 'copy s:text/plain')
        # self.editor.dropzone = 'copy s:text/plain'
        self.editor.focus()

        if self.options['display_version_toggle']:
            tree = ('<span onclick="ccccc.display_version_toggle()" style="cursor:pointer">'
                + self.options['icon_version_toggle'] + '</span>')
        else:
            tree = ''
        self.editor_title.innerHTML = '<h2>' + tree + self.options['editor_title'] + '</h2>'
        self.indent_button = document.createElement('LABEL')
        self.indent_button.innerHTML = self.options['editor_indent']
        self.indent_button.onclick = bind(self.do_indent, self)
        self.indent_button.className = 'indent_button'
        if self.options['display_indent']:
            self.editor_title.firstChild.appendChild(self.indent_button)

        self.save_button = document.createElement('TT')
        self.save_button.innerHTML = self.options['icon_save']
        self.save_button.style.fontFamily = 'emoji'
        self.save_button.onclick = bind(self.save, self)
        self.save_button.className = 'save_button'
        self.save_button.setAttribute('state', 'ok')
        self.editor_title.firstChild.appendChild(self.save_button)

        self.save_history = document.createElement('SELECT')
        if self.options['display_history']:
            self.save_history.className = 'save_history'
            self.editor_title.firstChild.appendChild(self.save_history)

        if GRADING:
            self.editmode = document.createElement('SELECT')
            self.editmode.className = 'editmode'
            if self.add_comments:
                opt1 = ''
                opt2 = ' selected'
            else:
                opt1 = ' selected'
                opt2 = ''
            self.editmode.innerHTML = (
                '<option' + opt1 + '>Bidouiller le code source</option>'
                + '<option' + opt2 + '>Commenter en sélectionnant</option>')
            self.editmode.onchange = bind(self.update_editmode, self)
            self.editor_title.firstChild.appendChild(self.editmode)

        if self.options['display_local_save']:
            self.local_button = document.createElement('TT')
            self.local_button.innerHTML = ' ' + self.options['icon_local']
            self.local_button.onclick = bind(self.save_local, self)
            self.editor_title.firstChild.appendChild(self.local_button)

        canvas = document.createElement('DIV')
        canvas.className = 'canvas'
        self.canvas = document.createElement('CANVAS')
        def canvas_event(event):
            JOURNAL.tree_canvas(this, event)
        self.canvas.onmousemove = canvas_event
        self.canvas.onmousedown = canvas_event
        def leave_version_tree():
            self.version_feedback.style.display = 'none'
        self.canvas.onmouseout = leave_version_tree

        canvas.appendChild(self.canvas)
        self.editor_title.insertBefore(canvas, self.editor_title.firstChild)

        self.fullscreen = document.createElement('DIV')
        self.fullscreen.className = 'fullscreen'
        self.fullscreen.innerHTML = """
        ATTENTION
        <p>
        Tout ce que vous faites est enregistré et pourra être
        retenu contre vous en cas de tricherie.
        <p>
        Si une autre personne a utilisé vos identifiants, c'est vous qui
        serez tenu comme responsable de ses crimes.
        <p>
        Mettez le curseur sur <span>⏱</span> pour voir le temps restant.
        <p>
        Cliquez sur
        <button onclick="ccccc.start_fullscreen()"
        >plein écran</button>
        pour commencer à travailler.
        <p style="font-size:80%">
        Si cet encart ne disparaît pas après avoir cliqué sur le bouton :<br>
        quittez complètement ce navigateur Web et lancez Firefox.
        </p>
        """
        self.top.appendChild(self.fullscreen)

    def set_editmode(self, value):
        """Toggle between edit source code and comment it"""
        EDITMODE[self.add_comments] = '\n'.join(JOURNAL.lines)
        self.add_comments = value
        JOURNAL.__init__(EDITMODE[self.add_comments] + '\n')
        self.unlock_worker()
        self.worker.postMessage(['goto', JOURNAL.question])

    def update_editmode(self, event):
        """Toggle between edit source code and comment it"""
        self.set_editmode(event.target.selectedIndex)

    def save_local(self):
        """Save the source on a local file"""
        bb = eval('new Blob([' + JSON.stringify(self.source) + '], {"type": "text/plain"})') # pylint: disable=eval-used
        a = document.createElement('a')
        a.download = (self.course.split('=')[1] + '_' + (self.current_question + 1)
            + '.' + (self.options['extension'] or 'txt'))
        a.href = window.URL.createObjectURL(bb)
        a.click()

    def scheduler(self): # pylint: disable=too-many-branches,too-many-statements
        """Send a new job if free and update the screen"""
        if not self.allow_edit:
            return

        remote_scroll = False
        if JOURNAL.remote_update:
            JOURNAL.remote_update = False
            if self.current_question != JOURNAL.question:
                self.unlock_worker()
                self.worker.postMessage(['goto', JOURNAL.question])
                return
            if not self.journal_question.created_now: # Not the first time
                self.set_editor_content(JOURNAL.content)
            self.journal_question.created_now = False
            if JOURNAL.old_scroll_line != JOURNAL.scroll_line:
                # Remote scroll
                line = (self.line_numbers.childNodes[JOURNAL.scroll_line]
                    or self.editor.childNodes[JOURNAL.scroll_line])
                top = line.offsetTop
                self.layered.scrollTo({'top': top, 'behavior': 'instant'}) # NOT SMOOTH REQUIRED
                remote_scroll = True
                JOURNAL.old_scroll_line = JOURNAL.scroll_line
                self.old_scroll_top = self.layered.scrollTop

        seconds = int(millisecs() / 1000)

        if (self.old_scroll_top != self.layered.scrollTop # Do not record if no change
                and not remote_scroll
                and seconds != self.last_scroll # No more than one position per second
                ):
            # Send scroll position to server
            if not JOURNAL.pending_goto:
                for line_number in self.line_numbers.childNodes:
                    if line_number.offsetTop >= self.layered.scrollTop:
                        line = int(line_number.textContent) - 1
                        if line != JOURNAL.scroll_line:
                            SHARED_WORKER.scroll_line(
                                line, 1+int(self.layered.offsetHeight / self.line_height))
                        break
                JOURNAL.old_scroll_line = JOURNAL.scroll_line
                self.last_scroll = seconds
                self.old_scroll_top = self.layered.scrollTop

        if (not GRADING
                and not self.options['allow_copy_paste']
                and max(window.innerHeight, window.outerHeight) + 8 < screen.height
                and not self.options['feedback']
           ):
            if self.fullscreen.style.display != 'block':
                self.fullscreen.style.display = 'block'
                if not self.first_F11:
                    SHARED_WORKER.blur()
        else:
            if self.fullscreen.style.display != 'none':
                self.fullscreen.style.display = 'none'
                self.first_F11 = False
                if not GRADING and self.options['checkpoint']:
                    SHARED_WORKER.focus()

        if self.do_update_cursor_position:
            # print('do_update_cursor_position', self.do_update_cursor_position)
            self.update_source()
            self.update_cursor_position_now()
            self.do_update_cursor_position = False

        if self.do_coloring:
            # print('do_coloring', self.do_coloring )
            self.do_coloring = False
            self.coloring()

        if self.state == 'started':
            return # Compiler is running
        if self.options['automatic_compilation'] and self.state == 'running':
            return # Program is running
        if (self.options['automatic_compilation'] and self.source != self.old_source
            or self.compile_now):
            print('compile')
            self.compile_now = False
            self.old_source = self.source # Do not recompile the same thing
            self.clear_highlight_errors()
            self.unlock_worker()
            self.state = 'started'
            self.worker.postMessage(self.source) # Start compile/execute/test
        if self.seconds != seconds:
            self.seconds = seconds
            timer = document.getElementById('timer')
            if timer:
                delta = self.stop_timestamp - seconds + self.server_time_delta # pylint: disable=undefined-variable
                if delta < 0:
                    if timer.className != 'done':
                        timer.className = "done"
                        stop_button = document.getElementById('stop_button')
                        if stop_button:
                            stop_button.style.display = 'none'
                    message = self.options['time_done']
                    delta = -delta
                    if (SESSION_LOGIN != self.options['creator']
                        and SESSION_LOGIN not in self.options['admins'].split(' ')
                        and SESSION_LOGIN not in self.options['graders'].split(' ')
                        and SESSION_LOGIN not in self.options['proctors'].split(' ')):
                        self.do_stop()
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
                if delta != self.old_delta:
                    timer.innerHTML = message + '<br><div>' + delta + '</div>'
                    self.old_delta = delta

    def compilation_toggle(self, element):
        """Toggle the automatic compilation flag"""
        if self.options['automatic_compilation']:
            # The False value is for course deactivated automatic compilation
            self.options['automatic_compilation'] = None
            element.className = 'unchecked'
        else:
            self.options['automatic_compilation'] = True
            element.className = 'checked'

    def compilation_run(self, memorize_input=True):
        """Run one compilation"""
        if memorize_input:
            self.memorize_inputs()
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
        self.overlay.style.visibility = 'visible'
    def clear_highlight_errors(self, update_cursor=True):
        """Make space fo the new errors"""
        for key, what in self.highlight_errors.Items():
            if what and not what.startswith('cursor'):
                self.highlight_errors[key] = None
        while (self.overlay.lastChild
               and self.overlay.lastChild.className
               and 'ERROR' in self.overlay.lastChild.className):
            self.overlay.removeChild(self.overlay.lastChild)
        if update_cursor:
            self.update_cursor_position()
    def update_source(self):
        """Extract the textContent of the DIV with the good \n"""
        def clear_text(state):
            if state.node.tagName == 'DIV':
                if len(state.text) and state.text[-1][-1] != '\n':
                    state.editor_lines.append(state.last)
                    state.text.append('\n')
                    state.last = None
                for state.node in state.node.childNodes:
                    clear_text(state)
                if len(state.text) and state.text[-1][-1] != '\n':
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
            else:
                if state.node.nodeValue:
                    state.text.append(state.node.nodeValue)
                state.last = state.node
        self.editor_lines = []
        original = self.editor.innerHTML
        cleaned = replace_all(original, '\r', '')
        cleaned = replace_all(cleaned, '\n', '<br>') # All element must be on a single line
        cleaned = cleaned.replace(RegExp('<([a-zA-Z]+)[^>]*>', 'g'), '<$1>') # Remove tag attributes
        cleaned = cleaned.replace(RegExp('</?span>', 'gi'), '') # Remove <span> tags
        if cleaned != original:
            self.editor.innerHTML = cleaned
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
        self.send_diff_to_journal()

    def record_pending_goto(self):
        """Must be recorded because action in the past"""
        if JOURNAL.pending_goto:
            # Validate the pending goto
            JOURNAL.clear_pending_goto()
            SHARED_WORKER.post(JOURNAL.pop())

    def send_diff_to_journal(self):
        """Compute differences, returns a list of:
              * [True, position, text]    For insertion
              * [False, position, number] For deletion
        """
        if JOURNAL.remote_update:
            # SHARED_WORKER.debug("Diff not done because remote update")
            return
        # SHARED_WORKER.debug("Diff begin")
        old = JOURNAL.content
        replace = self.source
        if old == replace:
            return
        self.record_pending_goto()
        rep = replace
        for what, position, value in compute_diffs(old, rep):
            if what:
                SHARED_WORKER.insert(position, value)
            else:
                SHARED_WORKER.delete_nr(position, value)
        if replace != JOURNAL.content:
            raise ValueError('Bug ' + replace + '!=' + JOURNAL.content)
        # SHARED_WORKER.debug("Diff end")

    def coloring(self): # pylint: disable=too-many-statements,too-many-branches
        """Coloring of the text editor with an overlay."""
        self.update_source()
        self.overlay.innerHTML = html(self.source_with_newlines)
        self.overlay.className = 'overlay language-' + self.options['language']
        if self.options['coloring']:
            del self.overlay.dataset.highlighted
            hljs.highlightElement(self.overlay)
        for line_char, what in self.highlight_errors.Items():
            line_char = line_char.split(':')
            if len(line_char) == 2:
                line_nr, char_nr = line_char
                width = 1
            else:
                line_nr, char_nr, width = line_char
            self.add_highlight_errors(line_nr, char_nr, what, width)

        i = 0
        for i, line in enumerate(self.editor_lines):
            rect = self.get_rect(line)
            if not self.line_numbers.childNodes[i]:
                self.line_numbers.appendChild(document.createElement('DIV'))
                self.line_numbers.childNodes[i].textContent = i+1
            self.line_numbers.childNodes[i].style.top = rect['top'] + 'px'
            if not self.char_width:
                nr_chars = len(line.textContent)
                if nr_chars:
                    self.char_width = rect['width'] / nr_chars
            if rect['height'] < self.line_height * 1.8:
                continue
            marker = document.createElement('DIV')
            marker.className = 'wrapped'
            marker.style.left = rect['left'] + 'px'
            marker.style.top = rect['top'] + self.line_height + 'px'
            marker.style.width = rect['width'] + 'px'
            marker.style.height = rect['height'] - self.line_height + 'px'
            self.overlay.appendChild(marker)

        def set_hovered(bubble, value):
            line = bubble.bubble
            while line and line.className == 'bubble_target':
                line.setAttribute('hovered', value)
                line = line.previousSibling
            bubble.setAttribute('hovered', value)

        def enter_bubble(event):
            if self.hover_bubble:
                set_hovered(self.hover_bubble, '0')
            self.hover_bubble = event.target
            set_hovered(self.hover_bubble, '1')

        def add_marker(column, line, column_stop):
            line = self.editor_lines[line-1]
            if not line:
                return

            self.meter.setStart(line, column)
            if column_stop < 0:
                column_stop = len(line.textContent)
            self.meter.setEnd(line, column_stop)
            rect = self.get_rect(self.meter)
            marker = document.createElement('DIV')
            marker.className = 'bubble_target'
            marker.style.left = rect['left'] + 'px'
            marker.style.top = rect['top'] + 'px'
            marker.style.width = rect['width'] + 'px'
            marker.style.height = rect['height'] + 'px'
            # marker.onmouseenter = enter_bubble # Does not works: event not received
            marker.bubble = bubble_elm
            self.comments.appendChild(marker)

        def bubble_move(event):
            self.moving_bubble.style.left = self.get_layer_x(event.clientX) - self.moving_bubble.dx + 'px'
            self.moving_bubble.style.top = self.get_layer_y(event.clientY) - 8 + 'px'
            if self.moving_bubble.nextSibling and self.moving_bubble.nextSibling.className == 'bubble_close':
                self.moving_bubble.nextSibling.remove()
            stop_event(event)
        def bubble_move_stop(event):
            event.target.onmouseup = ''
            self.layered.onmousemove = ''
            x, y = event.target.relative_to
            self.record_pending_goto()
            SHARED_WORKER.bubble_position(
                self.moving_bubble.bubble_index,
                (self.moving_bubble.offsetTop / self.line_height - y).toFixed(2),
                (self.moving_bubble.offsetLeft / self.char_width - x).toFixed(2))
            self.do_coloring = 'bubble_move'
            stop_event(event)
        def comment_change(event):
            if event.target.disable_next_change:
                event.target.disable_next_change = False # See 'goto_line'
            else:
                bubble_index = event.target.bubble_index
                if event.target.value != JOURNAL.bubbles[bubble_index].comment:
                    self.record_pending_goto()
                    SHARED_WORKER.bubble_comment(bubble_index, event.target.value)

        def bubble_move_start(event):
            self.resize_observer_active = True
            if self.get_layer_y(event.clientY) - event.target.offsetTop < 16:
                self.bubble_save_change()
                self.layered.onmousemove = bubble_move
                event.target.onmouseup = bubble_move_stop
                event.target.dx = self.get_layer_x(event.clientX) - event.target.offsetLeft
                self.moving_bubble = event.target
                stop_event(event)

        def bubble_delete(event):
            print('Delete bubble ', event.target.previousSibling.bubble_index)
            SHARED_WORKER.bubble_delete(event.target.previousSibling.bubble_index)
            self.moving_bubble = None # Not necessary?
            self.record_pending_goto()
            self.do_coloring = 'bubble_delete'

        self.resize_observer_active = False
        self.comments.innerHTML = ''
        for j, bubble in enumerate(JOURNAL.bubbles):
            if not bubble.login:
                continue # Deleted bubble
            bubble_elm = document.createElement('TEXTAREA')
            line1, column1 = self.get_line_column(bubble.pos_start)
            line2, column2 = self.get_line_column(bubble.pos_end)
            if line1 == line2:
                add_marker(column1, line1, column2)
            else:
                add_marker(column1, line1, -1)
                for line in range(line1+1, line2):
                    add_marker(0, line, -1)
                add_marker(0, line2, column2)

            bubble_elm.className = 'bubble_content'
            bubble_elm.relative_to = [
                min(column1, column2),
                1 + self.line_numbers.childNodes[line2-1].offsetTop / self.line_height]
            left = (bubble_elm.relative_to[0] + bubble.column) * self.char_width
            left = min(left % self.editor.offsetWidth, self.editor.offsetWidth - 100)
            top = (bubble_elm.relative_to[1] + bubble.line) * self.line_height
            width = bubble.width * self.char_width
            bubble_elm.style.left = left + 'px'
            bubble_elm.style.top = top + 'px'
            bubble_elm.style.width = width + 'px'
            bubble_elm.style.height = bubble.height * self.line_height + 'px'
            bubble_elm.bubble_index = j
            bubble_elm.bubble = self.comments.lastChild
            bubble_elm.onmousedown = bubble_move_start
            bubble_elm.onmouseenter = enter_bubble
            bubble_elm.onchange = comment_change
            bubble_elm.placeholder = "Indiquez votre commentaire ici."
            if bubble.login != SESSION_LOGIN:
                bubble_elm.setAttribute('readonly', 1)
            if bubble.comment:
                bubble_elm.innerHTML = html(bubble.comment)
            self.comments.appendChild(bubble_elm)
            self.resize_observer.observe(bubble_elm)

            bubble_close = document.createElement('DIV')
            bubble_close.className = 'bubble_close'
            bubble_close.style.left = left + width - 20 + 'px'
            bubble_close.style.right = left + width + 'px'
            bubble_close.style.top = top + 'px'
            bubble_close.innerHTML = '×'
            bubble_close.onclick = bubble_delete
            if not bubble.comment and JOURNAL.lines[JOURNAL.lines.length-1].startswith('b+'):
                bubble_elm.focus()
            self.comments.appendChild(bubble_close)

        for i in range(i+1, len(self.line_numbers.childNodes)):
            self.line_numbers.childNodes[i].style.top = '-10em'

        if self.options['diff']:
            default_answer = {}
            sep = RegExp('[ \t]', 'g')
            old = self.question_original[self.current_question]
            if not REAL_GRADING:
                old = JOURNAL.questions[JOURNAL.question].last_tagged_source or old
            for line in old.split('\n'):
                default_answer[line.replace(sep, '')] = True
            for number, line in zip(self.line_numbers.childNodes, self.source.split('\n')):
                if default_answer[line.replace(sep, '')]:
                    number.style.background = ""
                else:
                    number.style.background = "#0F0"

        self.overlay_show()
        self.line_numbers.style.height = self.comments.style.height = self.overlay.offsetHeight + 'px'
        self.tree_canvas()

    def tree_canvas(self):
        """Display the version tree"""
        return JOURNAL.tree_canvas(self.canvas)

    def get_layer_x(self, x):
        """From screen coordinate to layer coordinates"""
        return x - self.layered.offsetLeft - self.editor.offsetLeft

    def get_layer_y(self, y):
        """From screen coordinate to layer coordinates"""
        return y - self.layered.offsetTop + self.layered.scrollTop

    def get_rect(self, element):
        """Get rectangle in self.layered coordinates"""
        if not element.getBoundingClientRect:
            self.meter.selectNodeContents(element)
            element = self.meter
        rect = element.getBoundingClientRect()
        return {
            'width': rect.width, 'height': rect.height,
            'top': self.get_layer_y(rect.top),
            'left': self.get_layer_x(rect.left)
        }

    def add_highlight_errors(self, line_nr, char_nr, what, width=1):
        """Add the error or warning"""
        if not what:
            return
        def insert(element, class_name, move_right=0):
            """Set the element to the same place than the range"""
            rect = self.get_rect(self.meter)
            if move_right:
                move_right = rect['width']
            element.style.top = rect['top'] + 'px'
            element.style.height = rect['height'] + 'px'
            element.style.left = 'calc(' + (rect['left'] + move_right) + 'px - var(--pad))'
            element.style.width = width * rect['width'] + 'px'
            element.className = class_name
            self.overlay.appendChild(element)
        line = self.editor_lines[line_nr - 1]
        if not line:
            # The line number is bad: assumes the source code was modified
            # so clear all the errors.
            self.clear_highlight_errors()
            return
        # Goto first text element of the line
        while line.previousSibling and not line.previousSibling.tagName:
            line = line.previousSibling
        # Search the text element containing the column
        while char_nr > len(line.nodeValue or line.innerText):
            if not line.nextSibling or (
                    line.nextSibling.tagName and line.nextSibling.tagName != 'SPAN'):
                if char_nr > len(line.nodeValue or line.innerText) + 1:
                    self.record_error('BUG overflow ' + char_nr + ' ' + line.nodeValue
                        + ' ' + line.innerText + ' ' + line.nextSibling)
                    try:
                        self.record_error('line(from 1)=' + line_nr)
                        self.record_error('EDITOR: ' + JSON.stringify(self.editor.innerHTML))
                    except:
                        pass
                    char_nr = len(line.nodeValue or line.innerText)
                break
            char_nr -= len(line.nodeValue or line.innerText)
            line = line.nextSibling
        try:
            self.meter.selectNode(line)
        except: # pylint: disable=bare-except
            self.record_error('BUG self.meter.selectNode ' + str(line))
            return
        error = document.createElement('DIV')
        if not what.startswith('cursor'):
            insert(error, 'ERROR ' + what)
        try:
            if char_nr > (line.nodeValue or line.innerText).length:
                char_nr -= 1
                move_right = 1
            else:
                move_right = 0
            self.meter.setStart(line, char_nr-1)
            self.meter.setEnd(line, char_nr)
            char = document.createElement('DIV')
            insert(char, what + ' char ERROR', move_right)
        except: # pylint: disable=bare-except
            pass

    def onmousedown(self, event):
        """Mouse down"""
        self.mouse_pressed = event.button
        self.stop_completion()

    def onmouseup(self, event):
        """Mouse up"""
        self.mouse_pressed = -1
        selection = window.getSelection()
        if not self.editor.contains(selection.anchorNode) or not self.editor.contains(event.target):
            return
        # Selection in source code
        self.update_cursor_position_now()
        if REAL_GRADING and self.add_comments:
            pos_end = self.cursor_position
            pos_start = pos_end - len(selection.toString())
            if pos_start != pos_end:
                self.record_pending_goto()
                SHARED_WORKER.bubble(SESSION_LOGIN, pos_start, pos_end, 0, 0, 20, 2, '')
    def onmousemove(self, event):
        """Mouse move"""
        if event.target.tagName == 'CANVAS':
            self.mouse_position = [event.offsetX, event.offsetY]
    def text_allowed(self, text):
        """Check if the copy or paste is allowed"""
        return (text in cleanup(self.source)
            or text in cleanup(self.question.innerText)
            or text in cleanup(self.tester.innerText)
            or text in cleanup(self.executor.innerText)
            or text == self.copied)

    def oncopy(self, event, what='Copy'):
        """Copy"""
        if self.options['allow_copy_paste']:
            return
        text = cleanup(window.getSelection().toString())
        if not self.text_allowed(text):
            self.popup_message(self.options['forbiden'])
            stop_event(event)
            return
        self.copied = text
    def oncut(self, event):
        """Cut"""
        if event.target.tagName == 'TEXTAREA':
            return # Grading comment
        if not self.allow_edit:
            stop_event(event)
            return
        if self.add_comments:
            stop_event(event)
            return
        self.oncopy(event, 'Cut')
        self.clear_highlight_errors()
        self.do_coloring = self.do_update_cursor_position = "oncut"
    def insert_text(self, event, text):
        """Insert the pasted text"""
        self.overlay_hide()
        if event.type == 'drop':
            clean = event.dataTransfer.getData('text/html').replace(
                RegExp('</?(span|div|br)', 'g'), '')
            if '<' in clean:
                self.popup_message("""Le glisser/déposer de balise HTML est impossible.<br>
                    Faites un copier/coller.""")
                stop_event(event)
                return
            # def xxx():
            #     document.execCommand('undo', False)
            #     document.execCommand('insertText', False, text)
            # setTimeout(xxx, 500)
        else:
            document.execCommand('insertText', False, replace_all(text, '\r', ''))
            stop_event(event)
        self.clear_highlight_errors()
        self.do_coloring = self.do_update_cursor_position = "insert_text"

    def onpaste(self, event):
        """Text paste"""
        if event.target.tagName == 'TEXTAREA':
            return # Grading comment
        if not self.allow_edit:
            stop_event(event)
            return
        if self.add_comments:
            stop_event(event)
            return
        text = (event.clipboardData or event.dataTransfer).getData("text/plain")
        text_clean = cleanup(text)
        if self.options['allow_copy_paste']:
            self.insert_text(event, text)
            return
        if self.text_allowed(text_clean):
            self.insert_text(event, text)
            return # auto paste allowed
        self.popup_message(self.options['forbiden'])
        stop_event(event)

    def get_line_column(self, position):
        """Get the cursor coordinates from the text"""
        lines = self.source[:position].split('\n')
        return len(lines), len(lines[-1])

    def highlight_unbalanced(self): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """Highlight unbalanced parenthesis. Returns the next character to check"""
        highlight_stack = [] # stack of [cursor position, '({[']
        in_string = False
        in_comment = False
        in_comment_bloc = False
        if self.options['language'] in ('python', 'shell'):
            start_comment = '#'
            start_string = '"\''
            start_comment_bloc = '\001'
        elif self.options['language'] in ('cpp', 'javascript'):
            start_comment = '//'
            start_string = '"\''
            start_comment_bloc = '/*'
            end_comment_bloc = '*/'
        elif self.options['language'] == 'lisp':
            start_comment = ';'
            start_string = '"'
            start_comment_bloc = '\001'
        elif self.options['language'] == 'SQL':
            start_comment = '--'
            start_string = "'"
            start_comment_bloc = '\001'
        else:
            start_comment = '\001'
            start_string = '"'
            start_comment_bloc = '\001'
        cursor_position_min = self.cursor_position
        while self.source[cursor_position_min-1] in ' \t\n':
            cursor_position_min -= 1
        cursor_position_max = self.cursor_position
        while self.source[cursor_position_max] in ' \t\n':
            cursor_position_max += 1
        highlight_start = -1
        for start, char in enumerate(self.source):
            if start == self.cursor_position:
                if len(highlight_stack):
                    highlight_start = highlight_stack[-1][0]
                    line_open, column_open = self.get_line_column(highlight_start+1)
                    self.highlight_errors[line_open + ':' + column_open] = 'cursor'
                else:
                    highlight_start = -1
            start_pos = -1
            if in_string:
                if char == in_string:
                    in_string = False
            elif in_comment:
                if char == '\n':
                    in_comment = False
            elif in_comment_bloc:
                if end_comment_bloc.startswith(char):
                    if self.source[start+1] == end_comment_bloc[1]:
                        in_comment_bloc = False
            elif char == start_comment[0] and (
                    not start_comment[1] or self.source[start+1] == start_comment[1]):
                in_comment = True
            elif char == start_comment_bloc[0]:
                if self.source[start+1] == start_comment_bloc[1]:
                    in_comment_bloc = True
            elif char in ')}]':
                if len(highlight_stack) == 0:
                    line_bad, column_bad = self.get_line_column(start + 1)
                    self.highlight_errors[line_bad + ':' + column_bad] = 'cursorbad'
                else:
                    start_pos, start_char = highlight_stack.pop()
                    if char == {'{': '}', '(': ')', '[': ']'}[start_char]:
                        if start_pos == highlight_start:
                            # The cursor is just inside this closing block
                            line_open, column_open = self.get_line_column(start+1)
                            self.highlight_errors[line_open + ':' + column_open] = 'cursor'
                        if start == cursor_position_min - 1:
                            # The cursor is after the closing parenthesis
                            line_open, column_open = self.get_line_column(start_pos + 1)
                            self.highlight_errors[line_open + ':' + column_open] = 'cursor_after'
                            line_open, column_open = self.get_line_column(start + 1)
                            self.highlight_errors[line_open + ':' + column_open] = 'cursor_after'
                        if start_pos == cursor_position_max:
                            # The cursor is before the opening parenthesis
                            line_open, column_open = self.get_line_column(start_pos + 1)
                            self.highlight_errors[line_open + ':' + column_open] = 'cursor_after'
                            line_open, column_open = self.get_line_column(start + 1)
                            self.highlight_errors[line_open + ':' + column_open] = 'cursor_after'
                    else:
                        line_bad, column_bad = self.get_line_column(start + 1)
                        self.highlight_errors[line_bad + ':' + column_bad] = 'cursorbad'
            elif char in '([{':
                highlight_stack.append([start, char])
            elif char in start_string:
                in_string = char
        for start_pos, _start_char in highlight_stack:
            line_bad, column_bad = self.get_line_column(start_pos + 1)
            self.highlight_errors[line_bad + ':' + column_bad] = 'cursorbad'

    def highlight_word(self):
        """Highlight the current word in the text"""
        char = RegExp('[a-zA-Z0-9_]')
        start = self.cursor_position
        if (not self.source[start].match(char)
                and self.source[start-1] and self.source[start-1].match(char)):
            start -= 1
        while self.source[start] and self.source[start].match(char):
            start -= 1
        if start == self.cursor_position:
            return # Not on a word
        end = self.cursor_position
        while self.source[end] and self.source[end].match(char):
            end += 1

        name = RegExp('\\b' + self.source[start + 1:end] + '\\b', 'g')

        items = self.source.matchAll(name)
        while True:
            match = items.next()
            if not match.value:
                break
            line_word, column_word = self.get_line_column(match.value.index + 1)
            key = line_word + ':' + column_word + ':' + (end - start - 1)
            self.highlight_errors[key] = 'cursorword'

    def update_cursor_position_now(self):
        """Get the cursor position
        pos = [current_position, do_div_br_collapse]
        """
        # Remove old cursor position
        for key, error in self.highlight_errors.Items():
            if error and error.startswith('cursor'):
                self.highlight_errors[key] = None
        self.do_coloring = "update_cursor_position_now"
        try:
            cursor = document.getSelection().getRangeAt(0).cloneRange()
        except: # pylint: disable=bare-except
            self.cursor_position = 0
            return
        if not self.editor.firstChild:
            self.cursor_position = 0
            return
        cursor.setStart(self.editor.firstChild, 0)
        left = cursor.cloneContents()
        self.cursor_position = walk(left)
        self.highlight_unbalanced()
        try:
            self.highlight_word()
        except: # pylint: disable=bare-except
            pass # May happen when text deletion and the cursor is outside source
        self.highlight_error()
        if self.options['compiler'] == 'racket' and self.old_source == self.source:
            self.highlight_output()

    def highlight_error(self):
        """Highlight the error in the compiler output"""
        line, _column = self.get_line_column(self.cursor_position)
        errors = self.compiler.innerHTML.replace(
            '</b>', '').replace('<b style="color:#FFF;background:#F00">', '')
        for error_position, what in self.highlight_errors.Items():
            if what in ('warning', 'error'):
                error_line, _error_column = error_position.split(':')
                if line == int(error_line):
                    errors = errors.replace(
                        RegExp('([^\n>]*:' + error_position + '[^\n<]*)'),
                        '<b style="color:#FFF;background:#F00">$1</b>')
        if errors != self.compiler.innerHTML:
            self.compiler.innerHTML = errors

    def highlight_output(self):
        """Highlight the error in the compiler output"""
        line, _column = self.get_line_column(self.cursor_position)
        span = document.getElementById('executor_line_' + line)
        if span:
            span.style.background = '#FF0'
        if self.span_highlighted and self.span_highlighted != span:
            self.span_highlighted.style.background = ''
        self.span_highlighted = span
    def update_cursor_position(self):
        """Queue cursor update position"""
        self.do_update_cursor_position = "update_cursor_position"

    def do_indent(self):
        """Formate the source code"""
        if self.add_comments:
            return
        self.user_compilation = True # Indent trigger compile
        self.unlock_worker()
        self.wait_indentation = True
        self.worker.postMessage(['indent', self.source.strip()])

    def try_completion(self):
        """Check possible completion"""
        i = self.cursor_position - 1
        while i > 0 and NAME.exec(self.source[i]):
            i -= 1
        if self.cursor_position - i == 1:
            return # Nothing
        if not NAME_FIRST.exec(self.source[i+1]):
            return # Do not start by an allowed letter
        self.to_complete = self.source[i+1:self.cursor_position]
        matches = self.source.matchAll(RegExp('\\b' + self.to_complete + NAME_CHARS + '+\\b', 'g'))
        uniqs = []
        while True:
            i = matches.next().value
            if not i:
                break
            i = i[0]
            if i in uniqs:
                continue
            uniqs.append(i)
        uniqs.sort()
        self.record_error('to_complete=«' + self.to_complete + '» uniq=' + str(uniqs))
        if len(uniqs) == 0:
            return
        if len(uniqs) == 1:
            found = uniqs[0]
            if len(self.to_complete) != len(found):
                document.execCommand('insertText', False, found[len(self.to_complete):])
            return
        html = ['']
        for i in uniqs:
            html.append('<option>' + i + '</option>')
        self.completion.innerHTML = ''.join(html)

        line, column = self.get_line_column(self.cursor_position)
        line_elm = self.editor_lines[line-1]
        self.meter.selectNode(line_elm)
        self.meter.setStart(line_elm, column-1)
        self.meter.setEnd(line_elm, column)
        rect = self.get_rect(self.meter)
        self.completion.style.left = rect['left'] + rect['width'] + self.layered.offsetLeft + self.editor.offsetLeft + 'px'
        self.completion.style.top = rect['top'] + rect['height'] + self.layered.offsetTop + self.editor.offsetTop - self.layered.scrollTop + 'px'
        self.completion.style.display = 'block'
        self.completion.firstChild.className = 'active_completion'
        self.active_completion = 0
        self.completion_running = True

    def bubble_save_change(self):
        """The bubble texte content must be saved"""
        if document.activeElement and document.activeElement.tagName == 'TEXTAREA':
            document.activeElement.onchange({'target': document.activeElement})
            document.activeElement.disable_next_change = True

    def goto_line(self, line):
        """Goto in the past"""
        if line <= 0:
            return
        self.bubble_save_change()
        self.unlock_worker()
        JOURNAL.see_past(line)
        self.set_editor_content(JOURNAL.content)

    def stop_completion(self):
        """Close completion menu"""
        if self.completion_running:
            self.completion.style.display = 'none'
            self.completion_running = False

    def onkeydown(self, event): # pylint: disable=too-many-branches
        """Key down"""
        if not self.allow_edit:
            stop_event(event)
            return
        self.current_key = event.key
        if event.target.tagName == 'INPUT' and event.key not in ('F8', 'F9'):
            return
        if self.completion_running and event.target is self.editor:
            if event.key == 'ArrowUp':
                direction = -1
            elif event.key == 'ArrowDown':
                direction = 1
            elif event.key == 'Enter':
                document.execCommand('insertText', False,
                    self.completion.childNodes[self.active_completion].innerHTML[
                        len(self.to_complete):])
                self.stop_completion()
                stop_event(event)
                return
            else:
                direction = 0
            if direction:
                self.completion.childNodes[self.active_completion].className = ''
                self.active_completion += direction + len(self.completion.childNodes)
                self.active_completion = self.active_completion % len(self.completion.childNodes)
                self.completion.childNodes[self.active_completion].className = 'active_completion'
                stop_event(event)
                return
            self.stop_completion()
        if event.target is self.editor and event.key not in (
                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'):
            self.clear_highlight_errors()

        if event.target.tagName == 'TEXTAREA':
            # The teacher enter a comment
            return
        if self.add_comments and   event.key not in (
                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'PageDown', 'PageUp', 'F9'
                ) and not (event.ctrlKey and event.key in  ('r', 'y', 'z', 'a', 'c')):
            stop_event(event)
            return

        if event.key == 'Tab':
            document.execCommand('insertHTML', False, '    ')
            stop_event(event)
        elif event.key == 's' and event.ctrlKey:
            self.save()
            stop_event(event)
        elif event.key in 'yz' and event.ctrlKey:
            stop_event(event)
            if event.key == 'z':
                if JOURNAL.pending_goto:
                    JOURNAL.pending_goto_history.append(JOURNAL.pending_goto)
                else:
                    JOURNAL.pending_goto_history.append(len(JOURNAL.lines))
                if JOURNAL.pending_goto_history[-1] == JOURNAL.pending_goto_history[-2]:
                    JOURNAL.pending_goto_history.pop()
                else:
                    self.goto_line(JOURNAL.parent_position(JOURNAL.pending_goto_history[-1]))
            else:
                if not JOURNAL.pending_goto:
                    # ^Y without ^Z
                    return
                if len(JOURNAL.pending_goto_history):
                    self.goto_line(JOURNAL.pending_goto_history.pop())
                else:
                    self.goto_line(JOURNAL.pending_goto + 1)
        elif event.key == 'f' and event.ctrlKey:
            self.do_not_register_this_blur = True
            return
        elif event.key == ' ' and event.ctrlKey:
            self.try_completion()
            return
        elif event.key == 'F9':
            if self.options['automatic_compilation'] == 0: # pylint: disable=singleton-comparison
                self.user_compilation = True
                self.compilation_run()
            elif self.options['automatic_compilation']:
                document.getElementById('automatic_compilation').className = 'unchecked'
                self.options['automatic_compilation'] = None
            else:
                document.getElementById('automatic_compilation').className = 'checked'
                self.options['automatic_compilation'] = True
            stop_event(event)
        elif event.key == 'F8':
            self.do_indent()
        elif event.key == 'F11':
            if self.first_F11:
                self.first_F11 = False
                SHARED_WORKER.focus()
        elif event.key == 'Enter' and event.target is self.editor:
            # Automatic indent
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
        elif not self.options['allow_copy_paste'] and (
                event.key == 'OS'
                or len(event.key) > 1 and event.key.startswith('F') and event.key not in ('F8', 'F9', 'F11')
                or event.ctrlKey and event.key in ('b', 'h')
                ):
            # Disables these keys to not lost focus
            stop_event(event)
            return
        elif len(event.key) > 1 and event.key not in ('Delete', 'Backspace'):
            return # Do not hide overlay: its only a cursor move
        self.overlay_hide()
    def onkeyup(self, event):
        """Key up"""
        if not self.allow_edit:
            stop_event(event)
            return
        self.current_key = ''
        if event.target.tagName == 'TEXTAREA':
            # The teacher enter a comment
            return
        if self.insert_on_keyup:
            document.execCommand('insertHTML', False, self.insert_on_keyup)
            self.insert_on_keyup = None
        self.do_coloring = "onkeyup"
    def onkeypress(self, event):
        """Key press"""
    def onblur(self, _event):
        """Window blur"""
        if self.do_not_register_this_blur:
            self.do_not_register_this_blur = False
            return
        if not GRADING and self.options['checkpoint']:
            self.record_pending_goto()
            SHARED_WORKER.blur()
    def onfocus(self, _event):
        """Window focus"""
        if not GRADING and self.options['checkpoint'] and self.fullscreen.style.display == 'none':
            self.record_pending_goto()
            SHARED_WORKER.focus()
    def memorize_inputs(self):
        """Record all input values"""
        if not self.inputs[self.current_question]:
            # In some case INPUT are displayed for the bad question
            # So they are unexpected
            return
        inputs = self.executor.getElementsByTagName('INPUT')
        for value in inputs:
            if value == inputs[-1] and len(value.value) == 0:
                continue
            self.inputs[self.current_question][value.input_index] = value.value
    def oninput(self, event):
        """Send the input to the worker"""
        if event.key == 'Enter':
            self.focus_on_next_input = True
            if self.options['forget_input']:
                event.target.disabled = True
            else:
                self.memorize_inputs()
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
        if self[box]: # pylint: disable=unsubscriptable-object
            self[box].innerHTML = '' # pylint: disable=unsubscriptable-object

    def onerror(self, event): # pylint: disable=no-self-use
        """When the worker die?"""
        print(event)

    def change_history(self, event):
        """Put an old version in the editor"""
        choosen = event.target.selectedOptions[0].innerHTML
        if choosen == "Version initiale":
            choosen = ''
        for tag, index in self.journal_question.tags:
            if tag == choosen:
                self.goto_line(index)
                # SHARED_WORKER.goto(index)
                self.editor.focus()
                break

    def update_save_history(self):
        """The list of saved versions"""
        if self.save_history == document.activeElement:
            return
        content = ['<option selected>Retourner sur</option>']
        for tag in self.journal_question.tags[::-1]:
            content.append('<option>' + (html(tag[0] or "Version initiale")) + '</option>')
        self.save_history.innerHTML = ''.join(content)

    def save(self):
        """Saving the last question allowed question open the next one"""
        if self.allow_edit:
            self.update_source()
            def do_tag(tag):
                for old_tag, _index in self.journal_question.tags:
                    if old_tag == tag:
                        do_tag(tag+'*')
                        return
                self.record_pending_goto()
                self.save_button.setAttribute('state', 'wait')
                SHARED_WORKER.tag(tag)
                self.update_save_history()
                if self.options['save_unlock']:
                    if not JOURNAL.questions[self.current_question + 1]:
                        # Unlock the next question
                        self.unlock_worker()
                        self.worker.postMessage(['goto', self.current_question + 1])
                self.set_editor_content(JOURNAL.content) # Put the cursor at the right place
                setTimeout(bind(self.editor.focus, self.editor), 100)
            self.prompt("Nommez votre sauvegarde :", do_tag, len(self.journal_question.tags))

    def start_fullscreen(self):
        """TRY TO start full screen mode"""
        if document.body.requestFullscreen:
            document.body.requestFullscreen({'navigationUI':'hide'})
        else:
            self.popup_message("Votre ordinateur n'autorise pas le plein écran.")
    def do_stop(self):
        """Really stop the session"""
        record('checkpoint/' + self.course + '/' + LOGIN + '/STOP', send_now=True)
        SHARED_WORKER.close()
        document.body.innerHTML = self.options['stop_done']
        document.exitFullscreen()
    def stop(self):
        """The student stop its session"""
        self.popup_message(
            self.options['stop_confirm'], 'Non !', "Oui, et je quitte silencieusement la salle",
            bind(self.do_stop, self))

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
        competences = []
        nr_grades = 0
        nr_real_grade = 0
        for button in buttons.getElementsByTagName('BUTTON'):
            g = button.getAttribute('g')
            if button.nextSibling is None:
                span = button.parentNode
                span.className = span.className.replace(RegExp(' grade_undefined', 'g'), '')
                if g not in grading or grading[g][0] == '':
                    span.className += ' grade_undefined'
            if g not in grading or grading[g][0] == '':
                button.className = 'grade_unselected grade_undefined'
            elif button.innerText == grading[g][0]:
                if GRADING:
                    button.title = grading[g][1]
                else:
                    button.title = grading[g][1].split('\n')[-1]
                button.className = 'grade_selected'
                value = grading[g][0]
                if int(button.getAttribute('c')):
                    if value >= 0:
                        competences.append(Number(value))
                else:
                    if value != '?':
                        grading_sum += Number(value)
                    nr_real_grade += 1
                nr_grades += 1
            else:
                button.className = 'grade_unselected'
        self.grading_sum = grading_sum
        self.competence_average = (sum(competences)/len(competences)).toFixed(1)
        element = document.getElementById('grading_value')
        if element:
            if nr_real_grade:
                element.parentNode.style.display = 'initial'
            element.innerHTML = grading_sum
            element2 = document.getElementById('competence_value')
            if len(competences):
                element2.parentNode.style.display = 'initial'
                element2.innerHTML = self.competence_average
            else:
                element2.innerHTML = '?'

            element = document.getElementById('grading_sum')
            button = document.getElementById('grading_feedback')
            if self.nr_grades == nr_grades:
                element.style.background = "#0F0"
                if button:
                    button.style.opacity = 1
                    button.style.pointerEvents = 'all'
            else:
                element.style.background = "#FF0"
                if button and button.feedback != 5:
                    button.style.opacity = 0.3
                    button.style.pointerEvents = 'none'

    def add_grading(self):
        """HTML of the grading interface"""
        self.version = 0 # (ANSWERS[self.current_question] or [0, 0])[1]
        content = ['<div><h2>',
            GRADING and 'Noter' or '',
            ]
        if GRADING:
            content.append('<span style="vertical-align: bottom" id="grading_sum">')
            if self.options['grading_done']:
                content.append('<label style="margin:0.2em;padding: 0.2em;width:15em;text-align:center;vertical-align:bottom" id="grading_feedback" onclick="grading_toggle(this)"></label> ')
            else:
                content.append('<small>Retour étudiant via C5:<br>')
                content.append('<select id="grading_feedback" onchange="feedback_change(this)">')
                for level, label in FEEDBACK_LEVEL.Items():
                    content.append('<option value="' + level + '">' + label + '</option>')
                content.append('</select> </small>')
            content.append('<var style="display:none">Σ=<tt id="grading_value"></tt></var><br><var style="display:none">C=<tt id="competence_value"></tt></var></span>')
        elif self.options['feedback'] >= 4 and GRADE:
            if self.options['feedback'] == 4:
                size = 60
            else:
                size = 80
            content.append(
                '''
                <x style="font-size:''' + size + '''%; font-weight:normal;
                          margin-left:0.3em; margin-right:0.1em; display:inline-block; 
                          text-align:right; line-height:1em;vertical-align:middle">
                Note<br>temporaire</x>
                <x style="border:0.2em solid #000; background:#FFF;
                          padding: 0.2em;font-size:''' + (size+20) + '''%">'''
                + (self.grading_sum or GRADE[0]) + '/' + self.options.notation_max + '</x>')
        content.append('</h2></div>')
        if GRADING or NOTATION:
            if GRADING and self.options.display_global_grading:
                content.append("Cocher les ")
                content.append('<button onclick="ccccc.set_all_grades(0)">premières cases</button> ')
                content.append('<button onclick="ccccc.set_all_grades(1)">premières cases sauf malus</button> ')
                content.append('<button onclick="ccccc.set_all_grades(-1)">dernières cases</button>')
            content.append('<pre>')
            use_triangle = '▶' in NOTATION
            i = 0
            for text, grade_label, values in parse_notation(NOTATION):
                for line in text.split('\r\n'):
                    line = line.trimEnd()
                    line_clean = line.replace('▶', '')
                    if (len(line) <= 5 # Too short line
                            or use_triangle and '▶' not in line # ▶ is required
                            or line_clean not in self.source # Not in source
                            or len(self.source.split('\n' + line_clean + '\n')) != 2 # Duplicate line
                            ):
                        line = html(line)
                    else:
                        line = '''<span
                            onclick="ccccc.goto_source_line(this.textContent.replace('▶', ''))"
                            class="link">''' + html(line) + "</span>"
                    content.append(line)
                    content.append('\n')
                content.pop()
                if len(grade_label):
                    competence = ':' in grade_label and 1 or 0
                    # Remove competence key at the end of the grade label
                    grade_label = html(grade_label.replace(RegExp(':[a-z0-9+]*$'), ''))
                    if '?' in values:
                        content.append('<span class="competence">')
                    else:
                        content.append('<span class="grade_value">')
                    content.append(grade_label)
                    for choice in values:
                        content.append('<button g="' + i + '" v="'
                                       + choice + '" c="'
                                       + competence
                                       + '">' + choice + '</button>')
                    content.append('</span>')
                else:
                    content.append('\n')
                i += 1
            content.append('</pre>')
            self.nr_grades = i - 1
            self.grading.id = "grading"
            if GRADING:
                self.grading.onclick = grade
            self.grading.innerHTML = ''.join(content)
            self.update_grading(GRADES)
        else:
            self.question.innerHTML = ''.join(content)
        if GRADING:
            update_feedback(WHERE[10])

    def clear_input(self, the_question, the_index):
        """Clear student answers"""
        answers = self.inputs[the_question]
        while the_index in answers:
            del answers[the_index]
            the_index += 1
        self.old_source = ''
        self.unlock_worker()
        self.compilation_run(memorize_input=False) # Force run even if deactivated

    def onmessage(self, event): # pylint: disable=too-many-branches,too-many-statements,too-many-locals
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
            if JOURNAL.pending_goto:
                JOURNAL.pop()
                JOURNAL.pending_goto_history = []
            self.do_not_clear = {}
            self.current_question = value
            # self.record_pending_goto() # Record pending goto because if ^Z
            SHARED_WORKER.question(value)
            self.journal_question = JOURNAL.questions[value]
            self.set_editor_content(JOURNAL.content)
            self.compilation_run()
            self.canvas.parentNode.scrollLeft = max(
                0, self.tree_canvas() - self.canvas.parentNode.offsetWidth + 40)
            self.need_grading_update = True # Need to recompute links in grading pane
            if (GRADING or self.options['feedback']) and self.source != '':
                self.add_grading()
                self.need_grading_update = False
                if self.options['feedback'] >= 5 and GRADES:
                    self.update_grading(GRADES)
        elif what in ('error', 'warning'):
            self.highlight_errors[value[0] + ':' + value[1]] = what
            self.add_highlight_errors(value[0], value[1], what)
        elif what == 'state':
            self.state = value
            if self.state == "started":
                self.input_index = 0
                self.do_not_clear = {}
            if self.state == "inputdone":
                self.state = "running"
        elif what == 'good':
            if not self.journal_question.good:
                messages = self.options['good']
                self.popup_message(messages[millisecs() % len(messages)])
                SHARED_WORKER.good()
                self.tree_canvas() # Here because scheduler do not call coloring
        elif what == 'executor':
            self.clear_if_needed(what)
            for value in value.split('\001'):
                if not value:
                    continue
                if value.startswith('\002EVAL'):
                    #print(value[5:])
                    try:
                        eval(value[5:]) # pylint: disable=eval-used
                    except: # pylint: disable=bare-except
                        self.record_error('EVAL ' + value[5:])
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
                            stop_event(event)
                        G.canvas.onkeyup = onkeypress
                elif value == '\002INPUT':
                    if (self.executor.lastChild.tagName not in ('BR', 'DIV')
                            or self.executor.lastChild.style.float == 'left'):
                        self.executor.appendChild(document.createElement('BR'))
                    span = document.createElement('INPUT')
                    span.onkeypress = bind(self.oninput, self)
                    span.input_index = self.input_index
                    if not self.inputs[self.current_question]:
                        self.inputs[self.current_question] = {}
                    self.executor.appendChild(span)
                    clear = document.createElement('BUTTON')
                    clear.textContent = '×'
                    clear.tabIndex = -1
                    clear.setAttribute('onclick',
                        "ccccc.clear_input(" + self.current_question + ',' + self.input_index + ')')
                    if not self.options.forget_input:
                        self.executor.appendChild(clear)
                    self.executor.appendChild(document.createElement('BR'))
                    if not self.options.forget_input and self.input_index in self.inputs[self.current_question]:
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
                    if value[0] == '\n':
                        span.style.clear = 'left'
                    self.executor.appendChild(span) # pylint: disable=unsubscriptable-object
        elif what == 'index':
            links = []
            tips = []
            if self.options['display_home']:
                tips.append("Aller à l'accueil C5 listant toutes les sessions.")
                links.append('<a onclick="ccccc.goto_home()">'
                    + self.options['icon_home'] + '</a>')
                tips.append(' ')
                links.append(' ')
            if self.options['display_local_zip']:
                tips.append("Sauvegarder un ZIP de toutes les questions sur la machine locale")
                links.append('<a target="_blank" href="zip/' + COURSE + window.location.search
                    + '">' + self.options['icon_local'] + '</a>')
            if False and self.options['display_local_git']:
                tips.append("Sauvegarder sur la machine locale avec l'historique dans GIT")
                links.append('<a target="_blank" href="git/' + COURSE + window.location.search
                     + '">' + self.options['icon_git'] + '</a>')
            tips.append(' ')
            links.append(' ')
            content = ['<div class="questions"><div class="tips">']
            for item in tips:
                content.append('<div>' + item + '</div>')
            content.append('</div>') # End tips
            for item in links:
                content.append('<div>' + item + '</div>')
            content.append('</div>') # End links
            if (GRADING or self.options['feedback']) and ',' in WHERE[2]:
                content.append(
                    '<div class="version">'
                    + WHERE[2].split(',')[3].replace('a', 'Ⓐ').replace('b', 'Ⓑ')
                    + '</div>')
            content.append(value)
            if what in self: # pylint: disable=unsupported-membership-test
                self[what].innerHTML = ''.join(content) # pylint: disable=unsubscriptable-object
        elif what == 'editor':
            # New question
            question = self.journal_question
            self.compile_now = True
            if not question or question.created_now or self.wait_indentation:
                message = value
                if not self.wait_indentation:
                    message += '\n\n\n' # XXX
                self.set_editor_content(message)
                self.wait_indentation = False
            else:
                self.set_editor_content(JOURNAL.content)
        elif what == 'default':
            print("DEFAULT", value)
            self.question_original[value[0]] = value[1]
        elif what in ('tester', 'compiler', 'question', 'time'):
            if not value:
                return
            if not self[what]: # pylint: disable=unsubscriptable-object
                return # Display bloc does not exists
            self.clear_if_needed(what)
            if what == 'time':
                value += ' ' + self.state + ' ' + LOGIN
            span = document.createElement('DIV')
            span.innerHTML = value
            if '<error' in value:
                self[what].style.background = '#FAA' # pylint: disable=unsubscriptable-object
            else:
                self[what].style.background = self[what].background # pylint: disable=unsubscriptable-object
            if what == 'compiler' and '<h2>' not in value and not JOURNAL.pending_goto and self.user_compilation:
                self.user_compilation = False
                SHARED_WORKER.compile('<error' in value)
                self.tree_canvas() # Here because scheduler do not call coloring
            self[what].appendChild(span)  # pylint: disable=unsubscriptable-object
            if what == 'question' and self.journal_question:
                self.question.onscroll = "" # To not change scrollTop when erased
                def spy_onscroll():
                    def onscroll():
                        self.journal_question.scrollTop = self.question.scrollTop
                    self.question.onscroll = onscroll
                setTimeout(spy_onscroll, 100)
                self.question.scrollTop = self.journal_question.scrollTop or 0
        elif what == 'eval':
            try:
                eval(value) # pylint: disable=eval-used
            except: # pylint: disable=bare-except
                self.record_error('eval ' + value)
        elif what == 'stop':
            self.popup_message(
                "La compilation ne fonctionne plus :"
                + "<ul>"
                + "<li>Sauvegardez votre source."
                + "<li>Attendez que l'enveloppe passe au vert."
                + "<li>Rechargez la page pour la réactiver."
                + "</ul>")
        elif what == 'allow_edit':
            self.allow_edit = int(value)
        elif what == 'recompile':
            self.compilation_run()

    def goto_question(self, index):
        """Indicate the new question to the worker"""
        if self.allow_edit:
            self.unlock_worker()
            #if self.in_past_history:
            #    JOURNAL.pop()
            #self.worker.postMessage(['source', self.current_question, JOURNAL.content])
            self.worker.postMessage(['goto', index])

    def get_element_box(self, element):
        self.meter.setStart(element, 0)
        self.meter.setEnd(element, 0)
        return self.get_rect(self.meter)

    def goto_source_line(self, target_line):
        """Scroll the indicated source line to the window top"""
        for element in self.editor_lines:
            if (element.nodeValue or element.textContent) == target_line:
                self.layered.scrollTo({'top':self.get_element_box(element)['top'], 'behavior': 'smooth'})
                break

    def set_editor_content(self, message): # pylint: disable=too-many-branches,too-many-statements
        """Set the editor content (question change or reset)"""
        self.overlay_hide()
        self.editor.innerText = message

        cursorpos = JOURNAL.position
        left = JOURNAL.content[:JOURNAL.position]
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

        if message != '':
            top = self.get_element_box(self.editor.childNodes[JOURNAL.scroll_line])['top']
        else:
            top = 0
        self.old_scroll_top = self.layered.scrollTop = top

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
        # document.getSelection().collapse(self.editor, self.editor.childNodes.length)
        self.highlight_errors = {}
        self.do_coloring = "set_editor_content"
        self.source = message
        self.update_save_history()

    def record_error(self, data):
        """Record an error"""
        do_post_data({'data': data}, 'error/' + COURSE + '?ticket=' + TICKET)

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
        window.onkeydown = bind(self.onkeydown, self)
        window.onkeyup = bind(self.onkeyup, self)
        window.onkeypress = bind(self.onkeypress, self)
        window.onblur = bind(self.onblur, self)
        window.onfocus = bind(self.onfocus, self)
        def do_coloring():
            self.update_gui()
            self.do_coloring = "onresize"
        window.onresize = do_coloring
        document.getElementsByTagName('BODY')[0].appendChild(self.top)
        self.create_gui()
        setInterval(bind(self.scheduler, self), 200)
        if GRADING:
            # Get grades
            do_post_data({'student': STUDENT}, 'record_grade/' + COURSE + '?ticket=' + TICKET)
        self.completion = document.createElement('DATALIST')
        document.getElementsByTagName('BODY')[0].appendChild(self.completion)
        self.completion.className = 'completion'
        self.completion.style.display = 'none'
        self.update_gui()

    def racket(self, text):
        """Parse messages from the Racket remote compiler"""
        text = text.split('\n')
        if ':::' in text[0]:
            position = int(text[0].split(':::')[1].split(' ')[0])
        else:
            text = ['', text[0]]
            line = 0
        line, column = self.get_line_column(position)
        def highlight(event):
            if self.old_source != self.source:
                return
            self.add_highlight_errors(line, column, 'eval')
            event.target.style.background = "#FF0"
            line_number = document.createElement("VAR")
            line_number.textContent = 'Ligne ' + line
            event.target.appendChild(line_number)
        def unhighlight(event):
            if self.old_source != self.source:
                return
            event.target.style.background = ""
            self.clear_highlight_errors(False)
            event.target.removeChild(event.target.lastChild)
        span = document.createElement('DIV')
        span.id = 'executor_line_' + line
        if text[-1] == '#&lt;void&gt;':
            text[-1] = '<span style="color:#BBB">' + text[-1] + '</span>'
        span.innerHTML = '\n'.join(text[1:]).replace(
            RegExp('^([^ ]*) (.*) (#&lt;continuation-mark-set&gt;.*)$', 's'),
                '<i style="opacity:0.3">$1</i><br><b>$2</b><br><i style="opacity:0.3">$3</i>')
        if text == ['', 'Fini !']:
            span.style.marginTop = '1em'
        span.onmouseenter = highlight
        span.onmouseleave = unhighlight
        self.executor.appendChild(span) # pylint: disable=unsubscriptable-object

    def goto_home(self):
        """Goto C5 home"""
        setTimeout("window.location = window.location.search", 200)

    def record_grade(self, grade_id, value):
        """Record one student grade"""
        do_post_data(
            {
                'grade': grade_id,
                'value': value,
                'student': STUDENT,
            }, 'record_grade/' + COURSE + '?ticket=' + TICKET)

    def set_all_grades(self, index):
        """Set all grades to the first value"""
        i = 0
        graded = {}
        for button in self.grading.getElementsByTagName('BUTTON'):
            if 'grade_selected' in button.className:
                graded[button.getAttribute('g')] = True

        for _text, grade_label, values in parse_notation(NOTATION):
            if i not in graded and len(grade_label) and values:
                if index == 1:
                    if values[0] >= 0 or values[0] == '?':
                        self.record_grade(i, values[0])
                elif index == 0:
                    self.record_grade(i, values[0])
                elif index == -1:
                    self.record_grade(i, values[-1])
                else:
                    raise ValueError('set_all_grades index=' + index)
            i += 1
    def send_mail_right(self):
        """Send a mail to the student"""
        width = 0
        for line in self.source.split("\n"):
            width = max(width, len(line))
        content = []
        for i, line in enumerate(self.source.split("\n")):
            content.append(line)
            for _ in range(width - len(line)):
                content.append(' ')
            content.append(COMMENT_STRING)
            comment = self.get_comment(i)
            if comment:
                add_blank = False
                for comment_line in comment.strip().split('\n'):
                    if add_blank:
                        content.append('\n')
                        for _ in range(width):
                            content.append(' ')
                        content.append(COMMENT_STRING)
                    content.append(comment_line)
                    add_blank = True
            content.append('\n')
        return content

    def send_mail_top(self):
        """Send a mail to the student"""
        content = []
        for i, line in enumerate(self.source.split("\n")):
            comment = self.get_comment(i)
            if comment:
                content.append('\n')
                for comment_line in comment.strip().split('\n'):
                    content.append(COMMENT_STRING + ' ' + LOGIN + ' : ')
                    content.append(comment_line)
                    content.append('\n')
            content.append(line)
            content.append('\n')
        return content

    def send_mail(self):
        """Prepare mail for student"""
        if confirm('''OK pour mettre les commentaires à droite des lignes.

CANCEL pour les mettre au dessus des lignes de code.'''):
            content = self.send_mail_right()
        else:
            content = self.send_mail_top()
        base = document.getElementsByTagName('BASE')[0].href
        w = window.open()
        w.document.write('<!DOCTYPE html>\n<html>'
            + '<link rel="stylesheet" href="' + base + 'HIGHLIGHT/a11y-light.css?ticket=' + TICKET + '">'
            + '<h1>'
            + INFOS['mail'] + '<br>'
            + COURSE.split('=')[1] + '\n</h1><pre>'
            + hljs.highlight(''.join(content), { language: self.options['language'] }).value
            )
        w.document.close()

    def display_version_toggle(self):
        """Toggle the display of the version tree"""
        self.options['version_for_teachers'] = not self.options['version_for_teachers']
        self.options['version_for_students'] = not self.options['version_for_students']
        document.body.classList.toggle('versions')
        self.update_gui()
        self.tree_canvas()
class Plot:
    """Grapic state and utilities"""
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

    def draw(self, x1, y1, x2, y2, clear): # pylint: disable=too-many-locals
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

class Grapic: # pylint: disable=too-many-public-methods
    """For the Grapic library emulator"""
    canvas = bcolor = ctx = ctxs = height = width = None
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
        if not self.ctx:
            self.ccccc.record_error('BUG noctx')
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
        if '/' not in url:
            url = COURSE + '/' + url
        img.src = '/media/' + url + window.location.search
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
    ccccc.record_grade(grade_id, value)

def feedback_change(element):
    """The grader changed the feedback level"""
    record('record_feedback/' + COURSE + '/' + STUDENT + '/' + element.value)

def update_feedback(feedback):
    """Update the feedback from server answer"""
    element = document.getElementById('grading_feedback')
    if ccccc.options['grading_done']:
        element.feedback = feedback
        if feedback != 5:
            element.innerHTML = "Cliquer ici pour indiquer que vous avez fini de corriger."
        else:
            element.innerHTML = "Les notes et commentaires sont peut-être affichés."
    else:
        element.value = feedback

def grading_toggle(element):
    """Grading done or not"""
    if element.feedback != 5:
        record('record_feedback/' + COURSE + '/' + STUDENT + '/5')
    else:
        record('record_feedback/' + COURSE + '/' + STUDENT + '/1')

ccccc = CCCCC()
G = Grapic(ccccc)
