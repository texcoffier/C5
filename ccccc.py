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

# Coaching code is now in coach.py and will be concatenated by py2js
# No import needed because py2js concatenates: compatibility.py + xxx_local.py + options.py + coach.py + ccccc.py

DEPRECATED = ('save_button', 'local_button', 'stop_button', 'reset_button', 'line_numbers')

REAL_GRADING = GRADING
if not COURSE_CONFIG['display_grading']:
    GRADING = False

SHARED_WORKER, JOURNAL = create_shared_worker(LOGIN)
EDITMODE = ['', ''] # Journals without and with comments

IS_TEACHER = SESSION_LOGIN != STUDENT

NR_COMMON_COMMENTS = 5

MEDIA.sort()

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

flat_map = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿AAAAAAACEEEEIIIIDNOOOOOOOUUUUYÞßaaaaaaaceeeeiiiiðnooooooouuuuyþy'

def char_flat(c):
    return flat_map.substr(c.charCodeAt(0),1)

def flat(txt):
    """é → e É → E ..."""
    return txt.replace(RegExp('[\\x80-\\xFF]', 'g'), char_flat)

WALK_DEBUG = False

def get_bubble(event):
    bubble = event.target
    while bubble.className != 'bubble_content':
        bubble = bubble.parentNode
    return bubble

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
    old_source = None
    highlight_errors = {}
    question_original = {}
    copied = None # Copy with ^C ou ^X
    state = "uninitalised"
    input_index = -1 # The input number needed
    current_question = -1 # The question on screen
    compile_now = False
    editor_lines = []
    init_done = False
    seconds = 0
    start_time = 0
    do_not_clear = {}
    inputs = {} # User input in execution bloc
    grading_history = ''
    focus_on_next_input = False
    cursor_position = 0
    do_coloring = "default"
    do_update_cursor_position = True
    mouse_pressed = -1
    mouse_position = [0, 0]
    worker_url = None
    hover_bubble = None
    moving_bubble = None
    add_comments = GRADING
     # These options are synchronized between GUI and compiler/session
    options = {}
    last_save = 0
    allow_edit = 0
    version = 0 # version being graded
    nr_grades = None
    grading = None
    current_key = None
    meter = document.createRange()
    span_highlighted = None # Racket eval result line highlighted
    need_grading_update = True
    dialog_on_screen = False
    completion_running = False
    to_complete = ''
    last_scroll = 0 # Last scroll position sent to journal in seconds
    old_scroll_top = 0
    user_compilation = user_execution = False
    journal_question = None
    old_delta = None
    eval_error_recorded = False
    content_old = None
    wait_indent = False
    disable_on_paste = 0
    coach = None
    coach_previous_position = 0
    current_selection = ''

    def init(self):
        self.options = options = COURSE_CONFIG
        # Initialize coach with adapter for platform independence
        self.coach = create_coach(self.options, self)

        # Fix missing bloc position
        for infos in DEFAULT_COURSE_OPTIONS:
            if infos[0] == 'positions':
                for key in infos[1]:
                    if key not in options['positions']:
                        options['positions'][key] = [100, 1, 100, 1, '#0000']
                break

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

        print("GUI: start")
        window.onerror = bind(self.onJSerror, self)
        self.start_time = millisecs()
        self.course = COURSE
        JOURNAL.stop_timestamp = STOP   # Normal end session timestamp
        JOURNAL.tt = TT                 # True if TT

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
        if options['language'] == 'lisp':
            self.name_chars = '[a-zA-Z0-9!$%&*+-./:<=>?@^_~]'
            self.name_first = RegExp(self.name_chars)
        else:
            self.name_chars = '[a-zA-Z_0-9]'
            self.name_first = RegExp('[a-zA-Z_]')
        self.not_name_chars = '[^' + self.name_chars[1:]
        self.name = RegExp(self.name_chars)

        print("GUI: wait worker")
        if options['state'] == 'Ready':
            self.add_comments = 0

    def coach_analyse(self, event, previous_position):
        """Analyse event for coaching (called from onmouseup and onkeydown)"""
        if not self.coach or not self.coach.coach_tip_level:
            return

        prev_pos = previous_position or self.coach_previous_position or 0

        result = self.coach.analyse(event, self.source or '', self.cursor_position or 0, prev_pos)

        if result:
            # Handle actions immediately
            if 'actions' in result:
                actions = result['actions']
                if 'restore_cursor_position' in actions:
                    self.set_cursor_position(actions['restore_cursor_position'])
                    self.coach_previous_position = actions['restore_cursor_position']
            if 'message' in result and not self.dialog_on_screen:
                message = result['message']
                if message:
                    # setTimeout defers popup to prevent keystroke loss during onkeydown
                    self_ref = self
                    def show_popup():
                        if not self_ref.dialog_on_screen:
                            self_ref.popup_message(message)
                    setTimeout(show_popup, 0)

        self.coach_previous_position = self.cursor_position or 0

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

    def popup_message(self, txt, cancel='', ok='OK', callback=None, add_input=False, init=None, title=None): # pylint: disable=no-self-use
        """For Alert and Prompt"""
        if self.dialog_on_screen:
            return
        self.dialog_on_screen = True
        lastFocusedElement = document.activeElement
        popup = document.createElement('DIALOG')
        txt = '<div class="dialog_content">' + txt + '</div>'
        if title:
            txt = '<div class="dialog_title">' + title + '</div>' + txt
        if callback and add_input:
            txt += '<br><input id="popup_input"'
            if init:
                txt += ' value="' + html(init).replace(RegExp('"', 'g'), '&#34;') + '"'
            txt += '>'
        if cancel != '':
            txt += '<button id="popup_cancel">' + cancel + '</button>'
        if ok:
            txt += '<button id="popup_ok">' + ok + '</button>'
        popup.innerHTML = txt
        document.body.appendChild(popup)

        def close(event):
            """Close the dialog"""
            self.dialog_on_screen = False
            try:
                document.body.removeChild(popup)
                lastFocusedElement.focus()
            except: # pylint: disable=bare-except
                # On examination termination : body.innerHTLM = ''
                pass
            if event:
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
        if ok:
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
        self.char_width = None
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
            version_height = '11vh'
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
        self.canvas.height = "200px"
        self.canvas.width = self.canvas.offsetWidth
    def insert_media(self, event):
        """Insert the name of the cliked media"""
        tr = event.target
        while tr.tagName != 'TR':
            tr = tr.parentNode
        self.set_editor_content(
            JOURNAL.content[:self.cursor_position]
            + tr.lastChild.textContent
            + JOURNAL.content[self.cursor_position:])
        document.getElementById('popup_cancel').onclick()
        self.editor.focus()
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

        if len(MEDIA) and not GRADING and self.options['display_media_list']:
            def show_media():
                options = [
                    '<table class="media" onclick="ccccc.insert_media(event)">'
                ]
                for i in MEDIA:
                    options.append('<tr><td><img src="media/' + COURSE
                        + '/' + i + '?ticket=' + TICKET + '"><td><div>' + i + '</div></tr>')
                options.append('</table>')
                self.popup_message(''.join(options), "Annuler", None,
                    title="Cliquez pour inserrer le nom de l'image dans le code source.")

            self.media_button = document.createElement('SPAN')
            self.media_button.innerHTML = '📷'
            self.media_button.onclick = show_media
            self.media_button.style.marginLeft = "0.2vw"
            self.media_button.style.cursor = "pointer"
            self.editor_title.firstChild.appendChild(self.media_button)

        if self.options['display_local_save']:
            self.local_button = document.createElement('TT')
            self.local_button.innerHTML = ' ' + self.options['icon_local']
            self.local_button.onclick = bind(self.save_local, self)
            self.editor_title.firstChild.appendChild(self.local_button)

        self.canvas = document.createElement('CANVAS')
        self.canvas.className = 'canvas'
        def canvas_event(event):
            JOURNAL.tree_canvas(this, event)
        self.canvas.onmousemove = canvas_event
        self.canvas.onmousedown = canvas_event
        self.canvas.onmouseup = canvas_event
        def leave_version_tree():
            self.version_feedback.style.display = 'none'
        self.canvas.onmouseout = leave_version_tree

        self.editor_title.insertBefore(self.canvas, self.editor_title.firstChild)

        self.fullscreen = document.createElement('DIV')
        self.fullscreen.className = 'fullscreen'
        self.fullscreen.innerHTML = """
        ATTENTION
        <p>
        Tout ce que vous faites est enregistré et pourra être
        retenu contre vous en cas de tricherie.
        <p>
        Si une autre personne a utilisé vos identifiants,<br>
        c'est vous qui serez tenu comme responsable de ses crimes.
        <p>
        Le temps restant est affiché dans la colonne de gauche.
        <div style="text-align:center">
        <p style="background:#000;display:inline-block;margin:auto">
        Enlevez vos capuches, casquettes, oreillettes.<br>
        Rangez tous vos objets connectés dans votre sac :<br>
        téléphones, montres, lunettes...
        </div>
        <p>
        Cliquez sur
        →<button onclick="ccccc.start_fullscreen()"
        >plein écran</button>←
        pour commencer à travailler.
        N'utilisez pas la touche «F11».
        <p style="font-size:80%">
        Si cet encart ne disparaît pas après avoir cliqué sur le bouton :<br>
        quittez complètement ce navigateur Web et lancez Firefox.<br>
        </p>
        """
        self.top.appendChild(self.fullscreen)

        self.search_input = document.createElement('INPUT')
        self.search_input.id = 'search_input'
        self.top.appendChild(self.search_input)

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
                if line:
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
                if document.body.nextSibling:
                    element = document.body.nextSibling
                    content = ''
                    while element:
                        content += JSON.stringify(element.outerHTML)
                        element = element.nextsibling
                    if content != self.content_old:
                        self.content_old = content
                        self.record_error('BuG ' + content)

        if not (GRADING or self.options['allow_copy_paste'] or self.options['feedback'] or not self.options['checkpoint']):
            # EXAM MODE because not grading, no copy/paste no feedback and a checkpoint
            is_fullscreen = (
                    window.innerHeight * window.devicePixelRatio + 30 > screen.height
                and window.innerHeight * window.devicePixelRatio - 10 <= screen.height
                and window.innerWidth  * window.devicePixelRatio + 40 > screen.width
                and window.innerWidth  * window.devicePixelRatio - 10 <= screen.width
                or  window.innerHeight == screen.height
                and window.innerWidth  == screen.width
                )
            if is_fullscreen or JOURNAL.fullscreen_disabled:
                self.fullscreen.style.display = 'none'
            else:
                self.fullscreen.style.display = 'block'
            if (is_fullscreen or JOURNAL.fullscreen_disabled) and document.hasFocus():
                SHARED_WORKER.focus()
            else:
                SHARED_WORKER.blur()

        if self.do_update_cursor_position:
            # print('do_update_cursor_position', self.do_update_cursor_position)
            self.update_source()
            self.save_current_selection()
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
            if self.timer_day:
                delta = JOURNAL.stop_timestamp - seconds + self.server_time_delta # pylint: disable=undefined-variable
                delta += JOURNAL.bonus_time or 0
                if JOURNAL.tt:
                    delta += int((JOURNAL.stop_timestamp - START) / 3)
                if delta < 0:
                    if self.timer_day.className != 'done':
                        self.timer_day.className = "done"
                        stop_button = document.getElementById('stop_button')
                        if stop_button:
                            stop_button.style.display = 'none'
                    if (SESSION_LOGIN != self.options['creator']
                        and SESSION_LOGIN not in CONFIG['masters']
                        and SESSION_LOGIN not in self.options['admins']
                        and SESSION_LOGIN not in self.options['graders']
                        and SESSION_LOGIN not in self.options['proctors']):
                        self.do_stop()
                    name = 'done'
                    self.timer_day.className = name
                    self.timer_hour.className = name
                    self.timer_min.className = name
                    self.timer_sec.className = name
                    return
                secs = two_digit(delta % 60)
                mins = two_digit((delta/60) % 60)
                hours = two_digit((delta/3600) % 24)
                days = int(delta/86400)
                opts = self.options

                if delta < 60:
                    name = "minus60" # Background big red
                elif delta < 120:
                    name = "minus120" # text big red
                elif delta < 300:
                    name = "minus300" # text black
                else:
                    name = 'longtime'

                if int(delta) != self.old_delta and days < 100:
                    self.old_delta = int(delta)
                    self.timer_day.innerHTML = days or '⏱'
                    self.timer_hour.innerHTML = hours
                    self.timer_min.innerHTML = mins
                    self.timer_sec.innerHTML = secs
                    self.timer_day.className = name
                    self.timer_hour.className = name
                    self.timer_min.className = name
                    self.timer_sec.className = name

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

        for b in document.getElementsByClassName('coq'):
            b.innerHTML = 'Relancez la compilation pour voir les buts.'
    def set_editor_visibility(self, visible):
        """Show/hide editor without changing its content"""
        if visible:
            visible = ''
        else:
            visible = 'none'
        self.editor.style.display = self.overlay.style.display = \
            self.comments.style.display = self.line_numbers.style.display = visible
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
        if WALK_DEBUG:
            self.executor.innerText = self.editor.innerHTML + '\n' + cleaned + '\n' + self.cursor_position
        if cleaned != original:
            self.update_cursor_position_now()
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
        if WALK_DEBUG:
            texts = ''
            for i, line in enumerate(self.editor_lines):
                texts += '[' + i + '] = ' + (line.outerHTML or line.nodeValue) + ' '
            print(texts)
        self.source = ''.join(state['text'])
        self.send_diff_to_journal()

        if cleaned != original:
            self.set_cursor_position(self.cursor_position)

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
        if COURSE_CONFIG.state in ('Grade', 'Done', 'Archive'):
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

    def choose_comment(self, event):
        p = event.target
        while p.tagName != 'P':
            p = p.parentNode
        if p.parentNode.tagName == 'COMMENTS':
            p.parentNode.bubble.value = p.firstChild.textContent
            p.parentNode.bubble.focus()

    def coloring(self): # pylint: disable=too-many-statements,too-many-branches
        """Coloring of the text editor with an overlay."""
        self.update_source()
        self.overlay.innerHTML = html(self.source)
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
            for rect in self.meter.getClientRects():
                top = self.get_layer_y(rect['top'])
                left = self.get_layer_x(rect['left'])
                marker = document.createElement('DIV')
                marker.className = 'bubble_target'
                marker.style.left = 'calc(' + left + 'px - var(--target_feedback_width))'
                marker.style.top = top + 'px'
                marker.style.width = rect['width'] + 'px'
                marker.style.height = 'calc(' + rect['height'] + 'px - var(--target_feedback_width))'
                # marker.onmouseenter = enter_bubble # Does not works: event not received
                marker.bubble = bubble_elm
                self.comments.appendChild(marker)

        def bubble_move(event):
            if event.target.tagName == 'SPAN':
                event.target.disable_delete = True
                return
            self.moving_bubble.style.left = self.get_layer_x(event.clientX) - self.moving_bubble.dx + 'px'
            self.moving_bubble.style.top = self.get_layer_y(event.clientY) - 4 + 'px'
            stop_event(event)
        def bubble_move_stop(event):
            event.target.onmouseup = ''
            self.layered.onmousemove = ''
            if event.target.tagName == 'SPAN':
                bubble_delete(event)
                stop_event(event)
                return
            x, y = self.moving_bubble.relative_to
            self.record_pending_goto()
            SHARED_WORKER.bubble_position(
                self.moving_bubble.bubble_index,
                ((self.moving_bubble.offsetTop - y) / self.line_height).toFixed(2),
                ((self.moving_bubble.offsetLeft - x) / self.char_width).toFixed(2))
            self.do_coloring = 'bubble_move'

            if JOURNAL.bubbles[self.moving_bubble.bubble_index].comment:
                width = 0
                lines = JOURNAL.bubbles[self.moving_bubble.bubble_index].comment.split('\n')
                for line in lines:
                    width = max(width, len(line))
                if (width < JOURNAL.bubbles[self.moving_bubble.bubble_index].width
                        and len(lines) < JOURNAL.bubbles[self.moving_bubble.bubble_index].height):
                    SHARED_WORKER.bubble_size(self.moving_bubble.bubble_index,
                        0.8 * width + 2, 0.85 * len(lines) + 0.6)

            stop_event(event)
        def comment_change(event):
            if event.target.disable_next_change:
                event.target.disable_next_change = False # See 'goto_line'
            else:
                bubble_index = get_bubble(event).bubble_index
                comment = event.target.value.strip()
                if comment != JOURNAL.bubbles[bubble_index].comment:
                    self.record_pending_goto()
                    SHARED_WORKER.bubble_comment(bubble_index, comment)
                    if event.target.value != '':
                        comments = JSON.parse(localStorage['comments:' + COURSE] or '{}')
                        comments[comment] = (comments[comment] or 0) + 1
                        localStorage['comments:' + COURSE] = JSON.stringify(comments)

        def create_comment_select_list(bubble_element, start=''):
            comments = JSON.parse(localStorage['comments:' + COURSE] or '{}')
            if len(comments) == 0:
                return
            start = flat(start.lower())
            nbrs = [1000000+i
                    for comment, i in comments.Items()
                    if flat(comment.lower()).startswith(start)
                    ]
            nbrs.sort()
            if len(nbrs) <= NR_COMMON_COMMENTS:
                trigger = 0
            else:
                trigger = nbrs[len(nbrs) - NR_COMMON_COMMENTS] - 1000000
            items = []
            for comment, nbr in comments.Items():
                if not flat(comment.lower()).startswith(start):
                    continue
                if nbr >= trigger:
                    key = 'A' + str(999999 - nbr)
                    html_class = ' class="first_quartile"'
                else:
                    key = 'B' + flat(comment.lower())
                    html_class = ''
                value = '<P' + html_class + '><span>' + html(comment) + '</span><span>' + nbr + '</span>'
                items.append([key, value])
            if not items:
                return
            def cmp(a, b):
                """a and b can't be equal"""
                if a[0] > b[0]:
                    return 1
                else:
                    return -1
            items.sort(cmp)

            bubble = JOURNAL.bubbles[bubble_element.bubble_index]
            select = document.createElement('COMMENTS')
            select.style.top = bubble.height * self.line_height + 'px'
            select.onclick = bind(self.choose_comment, self)
            select.bubble = event.target
            select.innerHTML = ''.join([i[1] for i in items])
            bubble_element.appendChild(select)

        def focus_bubble(event):
            for i in document.getElementsByTagName('COMMENTS'):
                i.remove()
            bubble_element = get_bubble(event)
            if bubble_element.getElementsByTagName('TEXTAREA')[0].value == '':
                create_comment_select_list(bubble_element)

        def comment_list_update(event):
            if (not event.target.nextSibling
                    or event.target.nextSibling.tagName != 'COMMENTS') and event.target.value != '':
                return
            bubble_element = get_bubble(event)
            if bubble_element.previous_value == event.target.value:
                return
            if event.target.nextSibling:
                event.target.nextSibling.remove()
            create_comment_select_list(bubble_element, event.target.value)
            bubble_element.previous_value = event.target.value

        def bubble_move_start(event):
            self.bubble_save_change()
            self.layered.onmousemove = bubble_move
            event.target.onmouseup = bubble_move_stop
            self.moving_bubble = get_bubble(event)
            self.moving_bubble.dx = self.get_layer_x(event.clientX) - self.moving_bubble.offsetLeft
            stop_event(event)

        def bubble_delete(event):
            if event.target.disable_delete:
                event.target.disable_delete = False
                return
            SHARED_WORKER.bubble_delete(get_bubble(event).bubble_index)
            self.moving_bubble = None # Not necessary?
            self.record_pending_goto()
            self.do_coloring = 'bubble_delete'

        def textarea_size(event):
            return [
                (event.target.offsetWidth / self.char_width).toFixed(2),
                ((event.target.offsetHeight + event.target.previousSibling.offsetHeight)
                 / self.line_height).toFixed(2)
                ]

        def textarea_mouse_up(event):
            if not event.target.old_size:
                return
            new_size = textarea_size(event)
            if new_size[0] == event.target.old_size[0] and new_size[1] == event.target.old_size[1] :
                return
            self.bubble_save_change()
            SHARED_WORKER.bubble_size(get_bubble(event).bubble_index, new_size[0], new_size[1])
            self.do_coloring = 'bubble_resize'

        def textarea_mouse_down(event):
            event.target.old_size = textarea_size(event)

        self.comments.innerHTML = ''
        for j, bubble in enumerate(JOURNAL.bubbles):
            if not bubble.login:
                continue # Deleted bubble
            bubble_elm = document.createElement('DIV')
            bubble_elm.className = 'bubble_content'
            bubble_elm.innerHTML = '''<DIV>Drag me<SPAN>×</SPAN></DIV><TEXTAREA placeholder="Indiquez votre commentaire ici.
Tirez le bas droite pour agrandir."></TEXTAREA>'''
            line1, column1 = self.get_line_column(bubble.pos_start)
            line2, column2 = self.get_line_column(bubble.pos_end)
            if line1 == line2:
                add_marker(column1, line1, column2)
            else:
                add_marker(column1, line1, -1)
                for line in range(line1+1, line2):
                    add_marker(0, line, -1)
                add_marker(0, line2, column2)
            if line2 == 0:
                top = 0
            else:
                last_line = self.line_numbers.childNodes[line2-1] or self.line_numbers.lastChild
                top = last_line.offsetTop + self.line_height
            bubble_elm.relative_to = [
                min(column1, column2) * self.char_width,
                top
            ]
            left = (bubble_elm.relative_to[0] + bubble.column * self.char_width) % self.editor.offsetWidth
            left = min(left, self.editor.offsetWidth - 100)
            top = bubble_elm.relative_to[1] + bubble.line * self.line_height
            width = bubble.width * self.char_width
            width = min(width, self.editor.offsetWidth - left) # MUST NOT OVERFLOW
            bubble_elm.style.left = left + 'px'
            bubble_elm.style.top = top + 'px'
            bubble_elm.style.width = width + 'px'
            bubble_elm.style.height = bubble.height * self.line_height + 'px'
            bubble_elm.bubble_index = j
            bubble_elm.bubble = self.comments.lastChild
            bubble_elm.onmouseenter = enter_bubble
            bubble_elm.lastChild.onfocus = focus_bubble
            # Title bar
            bubble_elm.firstChild.onmousedown = bubble_move_start
            # TEXTAREA configure
            textarea = bubble_elm.lastChild
            textarea.onchange = comment_change
            textarea.onblur = comment_change
            textarea.onkeyup = comment_list_update
            if bubble.login != SESSION_LOGIN:
                textarea.setAttribute('readonly', 1)
            if bubble.comment:
                textarea.innerHTML = html(bubble.comment)
            textarea.onmousedown = textarea_mouse_down
            textarea.onmouseup = textarea_mouse_up

            self.comments.appendChild(bubble_elm)
            if not bubble.comment and JOURNAL.lines[JOURNAL.lines.length-1].startswith('b+'):
                textarea.focus()

        for i in range(i+1, len(self.line_numbers.childNodes)):
            self.line_numbers.childNodes[i].style.top = '-10em'

        if self.options['diff'] and self.journal_question:
            sep = RegExp('[ \t]', 'g')
            old = self.journal_question.first_source or self.question_original[self.current_question]
            if not REAL_GRADING and not self.options['diff_original']:
                old = self.journal_question.last_tagged_source or old
            diffs = compute_diffs([i.strip() for i in old.split('\n')],
                                  [i.strip() for i in self.source.split('\n')], False)
            for number in self.line_numbers.childNodes:
                number.style.background = ""
            for insert, position, _value in diffs:
                if insert:
                    if self.line_numbers.childNodes[position]:
                        self.line_numbers.childNodes[position].style.background = '#0F0'

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
            top = rect['top'] + 'px'
            left = 'calc(' + (rect['left'] + move_right) + 'px - var(--pad))'
            if class_name == 'error char ERROR':
                # Draw border outside the char
                top = 'calc(' + top + ' - var(--char-border))'
                left = 'calc(' + left + ' - var(--char-border))'
            element.style.top = top
            element.style.height = rect['height'] + 'px'
            element.style.left = left
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
        if self.options['forbid_question_copy'] and self.question.contains(event.target):
            stop_event(event)
        self.mouse_pressed = event.button
        self.stop_completion()

    def get_current_selection(self):
        return replace_all(window.getSelection().toString(), '\r\n', '\n')

    def save_current_selection(self):
        new_selection = self.get_current_selection()
        if new_selection:
            self.current_selection = new_selection

    def onmouseup(self, event):
        """Mouse up"""
        # Save event for coach analysis
        self.coach_last_event = event
        self.coach_last_event_type = 'mouseup'

        self.mouse_pressed = -1
        selection = window.getSelection()
        if not self.editor.contains(selection.anchorNode) or not self.editor.contains(event.target):
            return
        # Selection in source code
        if event.button == 1:
            if self.allow_edit and (self.options['allow_copy_paste'] or self.text_allowed(self.current_selection)):
                self.update_cursor_position_now()
                source = self.source[:self.cursor_position] + self.current_selection + self.source[self.cursor_position:]
                self.set_editor_content(source, self.cursor_position + len(self.current_selection))
                self.update_source()
                self.update_cursor_position_now()
            self.disable_on_paste = millisecs()
            stop_event(event)
            return
        self.save_current_selection()

        self.update_cursor_position_now()
        if REAL_GRADING and self.add_comments:
            pos_end = self.cursor_position
            pos_start = pos_end - len(self.get_current_selection())
            if pos_start != pos_end:
                self.record_pending_goto()
                SHARED_WORKER.bubble(SESSION_LOGIN, pos_start, pos_end, 0, 0, 30, 2.3, '')

        # Coach analysis for mouse events
        self.coach_analyse(event, self.coach_previous_position or 0)

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
        text = cleanup(self.get_current_selection())
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
        if millisecs() - self.disable_on_paste < 100:
            # Texte pasted from middle button
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
        start_comment, start_string, start_comment_bloc, end_comment_bloc = \
            language_delimiters(self.options['language'])
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

    def highlight_word(self, word=None):
        """Highlight the current word in the text"""
        if word is None:
            char = self.name
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
            word = self.source[start + 1:end]
            # Will not find word if first in the source
            name = RegExp(self.not_name_chars + protect_regexp(word) + self.not_name_chars, 'g')
            delta = 2
        else:
            if word == '':
                return
            name = RegExp(protect_regexp(word), 'g')
            delta = 1

        items = self.source.matchAll(name)
        while True:
            match = items.next()
            if not match.value:
                break
            line_word, column_word = self.get_line_column(match.value.index + delta)
            key = line_word + ':' + column_word + ':' + len(word)
            self.highlight_errors[key] = 'cursorword'
        return word

    def clear_cursor_markers(self):
        """Remove highlighted word and parenthesis"""
        for key, error in self.highlight_errors.Items():
            if error and error.startswith('cursor'):
                self.highlight_errors[key] = None

    def update_cursor_position_now(self):
        """Set the cursor position from screen position

        To check is all works : WALK_DEBUG=1
        and
        ccccc.editor.innerHTML =
            '<div>a</div><div>b</div>' // a \n b
            + '<div>c</div><div></div><div>d</div>' // c \n d
            + '<div>e</div><div><br></div><div>f</div>' // e \n \n f
            + '<div>g<br></div><div></div><div>h</div>' // g \n h
            + '<div>i</div><div></div><div><br>j</div>' // i \n \n j
            + '<div>k</div><br><div></div><div>l</div>' // k \n \n l
            + '<div>m</div><div></div><br><div>n</div>' // m \n \n n
            + '<div>o</div><div><br></div><br><div>p</div>' // o \n \n \n p
            + '<div>q</div><br><div><br></div><div>r</div>' // q \n \n \n r
            + '<div>s<br></div><br><div><br></div><br><div><br>t</div>' // s \n \n \n \n \n t
            ;
        And move one by one from start to end to verify that pos is incremented.
        With Firefox there is a bug after 'k' and 'q' the Selection.toString does not work.

        """
        if self.completion_running:
            return
        self.clear_cursor_markers()
        self.do_coloring = "update_cursor_position_now"
        self.cursor_position = self.get_cursor_position()

        self.highlight_unbalanced()
        try:
            self.highlight_word()
        except: # pylint: disable=bare-except
            pass # May happen when text deletion and the cursor is outside source
        self.highlight_error()
        self.highlight_coq()
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

    def highlight_coq(self):
        """More efficient way to highlight thing on cursor move"""
        style = document.getElementById('highlight_style')
        if not style:
            style = document.createElement('STYLE')
            style.id = 'highlight_style'
            document.body.appendChild(style)
        line, column = self.get_line_column(self.cursor_position)
        lines = self.source.split('\n')
        while line > 0 and lines[line-1].strip() == '':
            line -= 1
        css = '.coq { display: none; color: #0A0 } #coq' + str(line-1) + '{ display: block }'
        style.textContent = css

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
        self.wait_indent = True # Indent will trigger compile
        self.unlock_worker()
        self.worker.postMessage(['indent', self.source])

    def try_completion(self):
        """Check possible completion"""
        i = self.cursor_position - 1
        while i > 0 and self.name.exec(self.source[i]):
            i -= 1
        if self.cursor_position - i == 1:
            return # Nothing
        if not self.name_first.exec(self.source[i+1]):
            return # Do not start by an allowed letter
        self.to_complete = self.source[i+1:self.cursor_position]
        matches = self.source.matchAll(RegExp('\\b' + self.to_complete + self.name_chars + '+' + self.not_name_chars , 'g'))
        uniqs = []
        while True:
            i = matches.next().value
            if not i:
                break
            i = i[0]
            if i in uniqs:
                continue
            if i[:-1] not in uniqs:
                uniqs.append(i[:-1])
        uniqs.sort()
        self.record_error('to_complete=«' + self.to_complete
            + '» cursor_position=' + self.cursor_position
            + ' journal_line=' + len(JOURNAL.lines)
            + ' uniq=' + str(uniqs))
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
        if document.activeElement and document.activeElement.tagName == 'TEXTAREA' and document.activeElement.onchange:
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
            self.search_input.style.display = 'none'
            self.search_input.last_value = None
            self.completion.style.display = 'none'
            self.completion_running = False

    def start_search(self):
        """Ctrl+F"""
        self.search_input.last_value = None
        def update_search():
            value = self.search_input.value
            if value == self.search_input.last_value:
                return
            self.search_input.last_value = value
            self.clear_cursor_markers()
            self.highlight_word(value)
            lines = []
            if len(value) > 0:
                for i, line in enumerate(self.source.split('\n')):
                    if value in line:
                        lines.append('<option value="' + i + '">'
                            + html(line[:60]) + '</option>')
                        if len(lines) > 200:
                            break
            self.completion.innerHTML = ''.join(lines)
            self.completion.style.display = 'block'
            if len(lines):
                self.completion.firstChild.className = 'active_completion'
                self.goto_source_line(self.completion.firstChild.value)
            self.completion.style.left = self.search_input.offsetLeft + 'px'
            self.completion.style.top = self.search_input.offsetTop + self.search_input.offsetHeight + 'px'
            self.active_completion = 0
            self.completion_running = 'search'
        if self.completion_running == 'search':
            self.search_input.select()
        else:
            self.search_input.style.display = 'block'
            self.search_input.onkeyup = update_search
            self.search_input.value = self.highlight_word() or ''
            editor_left = self.options['positions']['editor'][0]
            editor_right = editor_left + self.options['positions']['editor'][1]
            if editor_left >= 100 - editor_right:
                left = 1
                width = editor_left
            else:
                left = editor_right
                width = 100 - editor_right
            self.search_input.style.left = left + 'vw'
            self.search_input.style.width = width - 2 + 'vw'

            self.search_input.line, self.search_input.column = self.get_line_column(self.cursor_position)
            self.search_input.scroll = self.layered.scrollTop
            update_search()
        self.search_input.focus()

    def onkeydown(self, event): # pylint: disable=too-many-branches
        """Key down"""
        if not self.allow_edit or event.key == 'F12' or event.key == 'F11' and not GRADING and self.options['checkpoint']:
            stop_event(event)
            return
        self.current_key = event.key
        self.coach_analyse(event, 0)
        if event.target.tagName == 'INPUT' and event.key not in ('F8', 'F9') and self.completion_running != 'search':
            return
        if self.completion_running == 'search' or self.completion_running and event.target is self.editor:
            if event.key == 'ArrowUp':
                direction = -1
            elif event.key == 'ArrowDown':
                direction = 1
            elif event.key == 'Enter':
                option = self.completion.childNodes[self.active_completion]
                if self.completion_running == 'search':
                    line = self.editor_lines[option.value]
                    document.getSelection().collapse(line,
                        (line.innerHTML or line.nodeValue).indexOf(self.search_input.value)
                        )
                else:
                    self.record_error('to_complete=«' + self.to_complete
                        + '» cursor_position=' + self.cursor_position
                        + ' journal_line=' + len(JOURNAL.lines)
                        + ' option=«' + str(option.innerHTML))
                    document.execCommand('insertText', False,
                        option.innerHTML[len(self.to_complete):])
                self.stop_completion()
                stop_event(event)
                return
            else:
                direction = 0
            if direction:
                self.completion.childNodes[self.active_completion].className = ''
                self.active_completion += direction + len(self.completion.childNodes)
                self.active_completion = self.active_completion % len(self.completion.childNodes)
                if self.completion.childNodes[self.active_completion]:
                    self.completion.childNodes[self.active_completion].className = 'active_completion'
                stop_event(event)
                if self.completion_running == 'search':
                    self.goto_source_line(self.completion.childNodes[self.active_completion].value)
                return
            if self.completion_running == 'search' and event.key == 'Escape':
                document.getSelection().collapse(
                    self.editor_lines[self.search_input.line-1], self.search_input.column)
                self.layered.scrollTop = self.search_input.scroll
                self.editor.focus()
            if self.completion_running != 'search' or event.key == 'Escape':
                self.stop_completion()
        if event.target is self.editor and event.key not in (
                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'PageDown', 'PageUp', 'Home', 'End'):
            self.clear_highlight_errors()

        if event.target.tagName == 'TEXTAREA':
            # The teacher enter a comment
            return
        if self.add_comments and   event.key not in (
                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'PageDown', 'PageUp', 'F9', 'F11'
                ) and not (event.ctrlKey and event.key in  ('r', 'y', 'z', 'a', 'c', 'f')):
            stop_event(event)
            return

        if event.key == 'Tab':
            if event.shiftKey:
                self.update_source() # New because the scheduler may have not yet do its job.
                self.update_cursor_position_now()
                line, column = self.get_line_column(self.cursor_position)
                if self.source.split('\n')[line-1].startswith('    '):
                    # Remove the first 4 character of the line
                    line_start = self.cursor_position - column
                    self.set_editor_content(
                        self.source[:line_start] + self.source[line_start+4:],
                        self.cursor_position - min(4, column))
            else:
                document.execCommand('insertHTML', False, '    ')
            stop_event(event)
        elif event.key == 's' and event.ctrlKey:
            if GRADING or self.options['feedback']:
                self.popup_message("Vous n'avez pas le droit de sauvegarder un examen terminé.")
            else:
                self.save()
            stop_event(event)
        elif event.key == 'f' and event.ctrlKey:
            self.start_search()
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
        elif event.key == ' ' and event.ctrlKey:
            self.try_completion()
            return
        elif event.key == 'F9':
            if self.options['automatic_compilation'] == 0: # pylint: disable=singleton-comparison
                self.user_compilation = self.user_execution = True
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
        elif event.key == 'Enter' and event.target is self.editor:
            self.update_source() # New because the scheduler may have not yet do its job.
            self.update_cursor_position_now()
            to_insert = '\n'
            if not event.shiftKey:
                # Automatic indent
                i = self.cursor_position
                while i > 0 and self.source[i-1] != '\n':
                    i -= 1
                j = i
                while j < self.cursor_position and self.source[j] in '\t ':
                    j += 1
                if j != i:
                    to_insert += self.source[i:j]
            to_delete = len(self.get_current_selection())
            source = self.source[:self.cursor_position-to_delete] + to_insert + self.source[self.cursor_position:]
            self.set_editor_content(source, self.cursor_position + len(to_insert) - to_delete)
            self.update_source()
            self.update_cursor_position_now()
            stop_event(event)
            if self.options['compiler'] == 'coqc': # Automatic compilation on Enter
                i = self.cursor_position - 1
                while self.source[i] in (' ', '\n'):
                    i -= 1
                if self.source[i] == '.':
                    self.compile_now = True
            return
        elif not self.options['allow_copy_paste'] and (
                event.key == 'OS'
                or len(event.key) > 1 and event.key.startswith('F') and event.key not in ('F8', 'F9', 'F11')
                or event.ctrlKey and event.key in ('b', 'h')
                ):
            # Disables these keys to not lost focus
            stop_event(event)
            return
        elif event.key == 'Home' and not event.ctrlKey and not event.shiftKey:
            i = self.cursor_position - 1
            while i >= 0 and self.source[i] != '\n':
                i -= 1
            if i == self.cursor_position - 1 or self.source[i:self.cursor_position].strip() != '':
                # Yet at the line beginning
                # or some non-spaces on the left.
                # Move to the text start (if there is one)
                i += 1
                while self.source[i] in ' \t':
                    i += 1
                if self.source[i] != '\n' and self.source[i]:
                    self.set_cursor_position(i)
            else:
                # Only spaces left: move to the line start
                self.set_cursor_position(i+1)
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
        self.do_coloring = "onkeyup"
        if JOURNAL.pending_goto:
            JOURNAL.version_tree_show(self.canvas, int(JOURNAL.lines[-1][1:]))
        else:
            JOURNAL.version_tree_show(self.canvas, len(JOURNAL.lines))
    def onkeypress(self, event):
        """Key press"""
    def onblur(self, _event):
        """Window blur"""
        if not GRADING and self.options['checkpoint']:
            self.record_pending_goto()
    def onfocus(self, _event):
        """Window focus"""
        if not GRADING and self.options['checkpoint'] and self.fullscreen.style.display == 'none':
            self.record_pending_goto()
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
        """Clear only once the new content starts to come
        Returns True if a clear was done
        """
        if box in self.do_not_clear:
            return False
        self.do_not_clear[box] = True
        if self[box]: # pylint: disable=unsubscriptable-object
            self[box].innerHTML = '' # pylint: disable=unsubscriptable-object
            self[box].content_size = 0
        return True

    def onerror(self, event): # pylint: disable=no-self-use
        """When the worker die?"""
        print(event)

    def change_history(self, event):
        """Put an old version in the editor"""
        choosen = event.target.selectedOptions[0].innerHTML
        JOURNAL.offset_x = None
        if choosen == 'Version mise à jour':
            index = self.journal_question.start + 1
            if JOURNAL.lines[index].startswith('I'):
                index += 1
            self.goto_line(index)
            self.set_editor_content(self.question_original[self.current_question])
        elif choosen == "Dernière version":
            if JOURNAL.pending_goto:
                self.goto_line(len(JOURNAL.lines)-1)
            else:
                self.popup_message("Bug: Dernière Version. Utilisez l'arbre pour la retrouver.")
        else:
            if choosen == "Version initiale":
                choosen = ''
            for tag, index in self.journal_question.tags:
                if tag == choosen:
                    self.goto_line(index)
                    # SHARED_WORKER.goto(index)
                    self.editor.focus()
                    break
        self.tree_canvas()

    def update_save_history(self):
        """The list of saved versions"""
        if self.update_save_history_running:
            return
        if self.save_history == document.activeElement:
            return
        content = ['<option selected>Retourner sur</option>']
        if JOURNAL.pending_goto and not JOURNAL.lines[-2].startswith('t'):
            content.append('<option>' + 'Dernière version' + '</option>')
        for tag in self.journal_question.tags[::-1]:
            content.append('<option>' + (html(tag[0] or "Version initiale")) + '</option>')
        original = self.question_original[self.current_question].strip() 
        if original != '' and original != self.journal_question.first_source.strip():
            content.append('<option>Version mise à jour</option>')
            if JOURNAL.content.strip() == '':
                # In some rare case, the default source code is not
                # displayed on screen.
                # But 'question_original' contains it.
                self.update_save_history_running = True
                self.set_editor_content(self.question_original[self.current_question])
                self.update_save_history_running = False
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
                if g.isdigit(): # Not a competence
                    if value != '?':
                        grading_sum += Number(value)
                    nr_real_grade += 1
                else:
                    if value >= 0:
                        competences.append(Number(value))
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
                <x style="border:0.02vw solid #000; background:#FFF;
                          padding: 0.02vw;font-size:''' + (size+20) + '''%">'''
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
            self.nr_grades = 0
            for grade in Grades(NOTATION).content:
                for line in grade.text_before.split('\r\n'):
                    line_clean = line.replace('▶', '').strip()
                    if (len(line) <= 5 # Too short line
                            or use_triangle and '▶' not in line # ▶ is required
                            or line_clean not in self.source # Not in source
                            or len(self.source.split(RegExp(
                                '\n *' + protect_regexp(line_clean) + ' *\n'))) != 2 # Duplicate line
                            ):
                        line = '<span>' + html(line) + '</span>'
                    else:
                        line = '''<span
                            onclick="ccccc.goto_source_line(this.textContent.replace('▶', '').strip())"
                            class="link">''' + html(line) + "</span>"
                    content.append(line)
                    content.append('\n')
                content.pop()
                if len(grade.label):
                    if grade.is_competence:
                        content.append('<span class="competence">')
                    else:
                        content.append('<span class="grade_value">')
                    self.nr_grades += 1
                    content.append(grade.label)
                    for choice in grade.grades:
                        content.append('<button g="' + grade.key + '" v="'
                                       + choice + '">' + choice + '</button>')
                    content.append('</span>')
                else:
                    content.append('\n')
            content.append('</pre>')
            self.grading.id = "grading"
            if GRADING:
                self.grading.onclick = bind(self.grade, self)
            self.grading.innerHTML = ''.join(content)
            self.update_grading(GRADES)
        else:
            self.question.innerHTML = ''.join(content)
        if GRADING:
            update_feedback(WHERE[10])

    def grade(self, event):
        """Set the grade"""
        if not self.grading_allowed():
            return
        if 'grade_selected' in event.target.className:
            value = ''
        else:
            value = event.target.textContent
        grade_id = event.target.getAttribute('g')
        if grade_id is None:
            return
        self.record_grade(grade_id, value)

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
        # print(event.data)
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
            if not self.journal_question:
                return
            if self.journal_question.start + 1 == self.journal_question.head:
                if not REAL_GRADING: # If not default answer: do set one
                    # Initialize with the default answer
                    self.set_editor_content(self.question_original[value])
            else:
                self.set_editor_content(JOURNAL.content)
            self.compilation_run()
            self.canvas.parentNode.scrollLeft = max(
                0, self.tree_canvas() - self.canvas.parentNode.offsetWidth + 40)
            self.need_grading_update = True # Need to recompute links in grading pane
            self.old_delta = 0 # Need to redisplay timer
            if (GRADING or self.options['feedback']):
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
            if self.options['compiler'] == 'coqc':
                if self.clear_if_needed(what) or not self.coqc_content:
                    self.coqc_content = ''
                self.coqc_content += value
                if "Code de fin d'exécution" in value:
                    header, content = self.coqc_content.split('</h2>')
                    self.executor.innerHTML = header + '</h2>'
                    output = document.createElement('DIV')
                    output.innerHTML = self.coqc(content)
                    self.executor.appendChild(output)
                return
            else:
                self.clear_if_needed(what)

            for value in value.split('\001'):
                if not value:
                    continue
                if value.startswith('\002EVAL'):
                    #print(value[5:])
                    try:
                        eval(value[5:]) # pylint: disable=eval-used
                    except Error as e: # pylint: disable=bare-except
                        if not self.eval_error_recorded:
                            self.record_error('EVAL ' + value[5:] + ' § ' + e + '\n'
                                + e.stack.toString())
                            self.eval_error_recorded = True
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
                        def onkeydown(event):
                            event.stopPropagation()
                        G.canvas.onkeydown = onkeydown
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
                    if '\033[2J' in value:
                        self.executor.innerHTML = self.executor.firstChild.outerHTML
                        self.executor.content_size = 0
                        value = value.split('\033[2J')[-1]
                    if self.executor.content_size > 1000000:
                        if self.executor.content_size == 1000001:
                            continue
                        self.executor.content_size = 1000001
                        value = 'Truncated...'
                    else:
                        self.executor.content_size += len(value)
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
                if self.options['GRADING']:
                    if WHERE[12] or WHERE[9] > 10:
                        links.append('🚨')
                    else:
                        links.append('👍')
                    tip = 'Placé par «' + WHERE[1] + '» dans «' + WHERE[2].split(',')[0] + '» (' + WHERE[6] + ')'
                    if WHERE[4]:
                        tip += '. ' + WHERE[4] + ' pertes de focus (' + WHERE[9] + 's)'
                    if WHERE[5]:
                        tip += '. ' + WHERE[5] + 'questions ok'
                    if WHERE[7]:
                        tip += '. ' + int(WHERE[7]/60) + 'm bonus'
                    if WHERE[11]:
                        tip += '. Encart rouge désactivé'
                    if WHERE[12]:
                        tip += (
                            '<div style="display: inline-block; font-size: 70%;'
                            + 'position:absolute; width:50em; border: 1px solid #000; background: #FDD">'
                            + replace_all(html(WHERE[12]), '\n', '<br>') + '</div>')
                    tips.append(tip)
                    # 'Dernière interaction : ' + nice_date(WHERE[3], True) + '<br>'
            if not self.options['GRADING'] and self.options['checkpoint'] and not self.options['feedback']:
                tips.append("Terminer l'examen")
                links.append('<a id="stop_button" class="stop_button" onclick="ccccc.stop()">'
                    + self.options['icon_stop'] + '</a>')
            if (not self.options['GRADING'] and self.options['display_timer']
                    and not self.options['feedback']
                    and JOURNAL.stop_timestamp - self.seconds < 86400 * 100):
                tips.append('Fin dans :')
                links.append(' ')
                tips.append('jours')
                links.append('<span id="timer_day"> </span>')
                tips.append('heures')
                links.append('<span id="timer_hour"> </span>')
                tips.append('minutes')
                links.append('<span id="timer_min"> </span>')
                tips.append(self.options['time_seconds'])
                links.append('<span id="timer_sec"> </span>')
            if self.options['display_local_zip']:
                tips.append("Sauvegarder un ZIP de toutes les questions sur la machine locale")
                links.append('<a target="_blank" href="zip/' + COURSE + window.location.search
                    + '">' + self.options['icon_local'] + '</a>')
            if False and self.options['display_local_git']:
                tips.append("Sauvegarder sur la machine locale avec l'historique dans GIT")
                links.append('<a target="_blank" href="git/' + COURSE + window.location.search
                     + '">' + self.options['icon_git'] + '</a>')
            if (GRADING or self.options['feedback']) and ',' in WHERE[2]:
                tips.append("Version du sujet. Cliquez pour voir le plan")
                links.append(
                    '<a class="version" target="_blank" href="/checkpoint/'
                    + COURSE + '?ticket=' + TICKET + '#{%22student%22:%22' + LOGIN + '%22}">'
                    + WHERE[2].split(',')[3].replace('a', 'Ⓐ').replace('b', 'Ⓑ')
                    + '</a>')
            tips.append(' ')
            links.append(' ')
            content = ['<div class="questions"><div class="tips">']
            for item in tips:
                content.append('<div>' + item + '</div>')
            content.append('</div>') # End tips
            for item in links:
                content.append('<div>' + item + '</div>')
            content.append('</div>') # End links
            content.append(value)
            if what in self: # pylint: disable=unsupported-membership-test
                self[what].innerHTML = ''.join(content) # pylint: disable=unsubscriptable-object
            self.timer_day = document.getElementById('timer_day')
            self.timer_hour = document.getElementById('timer_hour')
            self.timer_min = document.getElementById('timer_min')
            self.timer_sec = document.getElementById('timer_sec')
        elif what == 'editor':
            self.set_editor_content(value)
            if self.wait_indent:
                self.wait_indent = False
                self.user_compilation = True
                self.compilation_run()
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
            if (what == 'compiler'
                    and '<h2>' not in value
                    and not JOURNAL.pending_goto
                    and self.user_compilation
                    and self.options['compiler'] != 'racket'
                    ):
                self.user_execution = True
                self.user_compilation = False
                error = value.split('<error')
                if len(error) == 2:
                    error = error[1].split('>')[0].split(' ')
                    if len(error) == 3: # <error 1 4> for example
                        nr_errors = int(error[1])
                        nr_warnings = int(error[2])
                    else:
                        nr_errors = 0
                        nr_warnings = 1
                else:
                    nr_errors = nr_warnings = 0
                SHARED_WORKER.compile(nr_errors, nr_warnings)
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
        elif what == 'wait':
            self.executor.innerHTML += value
            self.compiler.innerHTML += value
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
        if element.offsetWidth == 0:
            return {'top': element.offsetTop, 'left': element.offsetLeft,
                    'width': element.offsetWidth, 'height': element.offsetHeight}
        self.meter.setStart(element, 0)
        self.meter.setEnd(element, 0)
        return self.get_rect(self.meter)

    def goto_source_line(self, target_line):
        """Scroll the indicated source line to the window top"""
        element = self.editor_lines[target_line]
        if not element:
            for element in self.editor_lines:
                if (element.nodeValue or element.textContent).strip() == target_line:
                    break
        self.layered.scrollTo({'top':self.get_element_box(element)['top'], 'behavior': 'smooth'})

    def display_selection(self):
        """For debug purpose"""
        if WALK_DEBUG:
            try:
                range = document.getSelection().getRangeAt(0)
                print('Ancestor:', range.commonAncestorContainer.tagName or range.commonAncestorContainer.nodeValue,
                'Start:', range.startOffset, range.startContainer.tagName or range.startContainer.nodeValue,
                'End:', range.endOffset, range.endContainer.tagName or range.endContainer.nodeValue)
            except:
                print('No selection')

    def get_cursor_position(self):
        """Get cursor position"""
        self.display_selection()
        selection = document.getSelection()
        try:
            original_range = selection.getRangeAt(0)
        except:
            return 1
        # Save original selection
        anchorNode = selection.anchorNode
        anchorOffset = selection.anchorOffset
        focusNode = selection.focusNode
        focusOffset = selection.focusOffset
        selection.removeAllRanges()
        range_from_start = original_range.cloneRange()
        range_from_start.setStart(self.editor, 0)
        selection.addRange(range_from_start)
        if WALK_DEBUG:
            self.compiler.textContent = JSON.stringify(selection.toString())
        position = len(self.get_current_selection())
        # Restore original selection
        selection.removeAllRanges()
        selection.collapse(anchorNode, anchorOffset)
        selection.extend(focusNode, focusOffset)

        return position

    def set_cursor_position(self, position):
        """Change the onscreen position"""
        self.display_selection()
        if not self.editor_lines[0]:
            return # Empty source
        line, column = self.get_line_column(position)
        if not self.editor_lines[line-1]: # Cursor after the end
            line = len(self.editor_lines)
            column = len(self.editor_lines[line-1])
        if self.editor_lines[line-1].tagName == 'BR':
            for i, element in enumerate(self.editor.childNodes):
                if element is self.editor_lines[line-1]:
                    document.getSelection().collapse(self.editor, i)
        else:
            document.getSelection().collapse(self.editor_lines[line-1], column)

        if self.get_cursor_position() != position:
            print('********************************** want', position,
                'get', self.get_cursor_position(), 'line', line, 'column', column)

    def set_editor_content(self, message, position=None): # pylint: disable=too-many-branches,too-many-statements
        """Set the editor content (question change or reset)"""
        self.overlay_hide()
        self.editor.innerText = message
        self.update_source()
        current_line = self.editor_lines[JOURNAL.scroll_line]
        if current_line:
            top = self.get_element_box(current_line)['top']
        else:
            top = 0
        if abs(self.layered.scrollTop - top) > self.line_height:
            self.old_scroll_top = self.layered.scrollTop = top
        self.set_cursor_position(position or JOURNAL.position)
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
        document.getElementsByTagName('BODY')[0].appendChild(self.top)
        self.create_gui()
        window.onkeydown = bind(self.onkeydown, self)
        window.onkeyup = bind(self.onkeyup, self)
        window.onkeypress = bind(self.onkeypress, self)
        window.onblur = bind(self.onblur, self)
        window.onfocus = bind(self.onfocus, self)
        def do_coloring():
            self.update_gui()
            self.do_coloring = "onresize"
            JOURNAL.offset_x = None
            self.tree_canvas()
        window.onresize = do_coloring
        setInterval(bind(self.scheduler, self), 200)
        if GRADING:
            # Get grades
            do_post_data({'student': STUDENT}, 'record_grade/' + COURSE + '?ticket=' + TICKET)
        self.completion = document.createElement('DATALIST')
        document.getElementsByTagName('BODY')[0].appendChild(self.completion)
        self.completion.className = 'completion'
        self.completion.style.display = 'none'
        self.update_gui()

    def coqc(self, lines):
        html = []
        forger_line = False
        for line in lines.split('\n'):
            show = line.split('     = "lInE ')
            if len(show) == 2:
                forget_line = True
                line_number = int(show[1].split('"')[0])
                html.append('<B class="coq" id="coq' + line_number + '">')
            elif line == '     = "dOnE"':
                forget_line = True
                html.append('</B>')
            elif 'Error:' in line:
                html.append('</B>')
                html.append(line)
                forget_line = False
            else:
                if forget_line:
                    forget_line = False
                else:
                    html.append(line + '\n')
        return ''.join(html)

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
            if self.user_execution:
                self.user_execution = False
                nr_errors = len(self.executor.textContent.split('struct:exn:fail:')) - 1
                SHARED_WORKER.compile(nr_errors, 0)
                self.tree_canvas()
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

    def grading_allowed(self):
        """Returns True if grading is allowed"""
        if COURSE_CONFIG.state == 'Grade':
            return True
        self.popup_message(
            "Notation non autorisée pour l'instant.<br>"
            + "Le responsable de la session doit la passer en mode «Grade»"
            )
        return False

    def set_all_grades(self, index):
        """Set all grades to the first value"""
        if not self.grading_allowed():
            return
        graded = {}
        for button in self.grading.getElementsByTagName('BUTTON'):
            if 'grade_selected' in button.className:
                graded[button.getAttribute('g')] = True

        for grade in Grades(NOTATION).grades:
            if grade.key not in graded:
                if index == 1:
                    if grade.grades[0] >= 0 or grade.grades[0] == '?':
                        self.record_grade(grade.key, grade.grades[0])
                elif index == 0:
                    self.record_grade(grade.key, grade.grades[0])
                elif index == -1:
                    self.record_grade(grade.key, grade.grades[-1])
                else:
                    raise ValueError('set_all_grades index=' + index)
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
        img.src = BASE + '/media/' + url + window.location.search
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
