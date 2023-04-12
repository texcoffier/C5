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
        def postMessage(self, _message):
            """Send a message to the worker"""
except: # pylint: disable=bare-except
    pass

EXPLAIN = {0: "Sauvée", 1: "Validée", 2: "Compilée", 3: "Dernière seconde"}

DEPRECATED = ('save_button', 'local_button', 'stop_button', 'reset_button')

def get_xhr_data(event):
    """Evaluate the received javascript"""
    if event.target.readyState == 4:
        if event.target.status == 200:
            if event.target.responseText.startswith('<'):
                alert(event.target.responseText.split('<h1>')[1].split('</h1>'))
            else:
                eval(event.target.responseText) # pylint: disable=eval-used
        else:
            eval(event.target.responseText.replace( # pylint: disable=eval-used
                RegExp('//.*', 'g'), '').replace(RegExp('\n', 'g'), ' '))
        event.target.abort()

def get_xhr_error(event):
    """Display received error or timeout."""
    print(event)

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

class CCCCC: # pylint: disable=too-many-public-methods
    """Create the GUI and launch worker"""
    server_time_delta = int(millisecs()/1000 - SERVER_TIME)
    question = editor = overlay = tester = compiler = executor = time = None
    index = popup_element = save_button = local_button = line_numbers = None
    stop_button = fullscreen = comments = save_history = editor_title = None
    tag_button = indent_button = layered = None
    top = None # Top page HTML element
    source = None # The source code to compile
    source_with_newlines = None
    old_source = None
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
    records_in_transit = []
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
    options = { # These options are synchronized between GUI and compiler/session
        # ---------------------
        # Frame screen position
        # ---------------------
        'positions' : { # X%, Width%, Y%, Heigth%, background color
            'question':    [ 1, 29, 0, 30,'#EFEF'], # LeftTop    : The question
            'tester':      [ 1, 29,30, 70,'#EFEF'], # LeftBottom : Goal checker
            'editor':      [30, 40, 0,100,'#FFFF'], # Middle     : Source editor
            'compiler':    [70, 30, 0, 30,'#EEFF'], # RightTop   : Compiler messages
            'executor':    [70, 30,30, 70,'#EEFF'], # RightBottom: Execution messages
            'time':        [80, 20,98,  2,'#0000'], # BottomRight: Debugger for admin
            'index':       [ 0,  1, 0,100,'#0000'], # Left       : Thin table of content
            'editor_title':[0 ,  0, 0,  0,'#FFFF'], # Only the color is used.
        },
        # --------------------------
        # Titles, label and messages
        # --------------------------
        'forbiden': "Coller du texte copié venant d'ailleurs n'est pas autorisé.",
        'close': "Voulez-vous vraiment quitter cette page ?",
        'question_title': 'Question',
        'editor_title': 'Code source',
        'editor_indent': 'Indent(F8)',
        'tester_title': 'Les buts que vous devez atteindre',
        'compiler_title': 'Compilation',
        'compiler_title_toggle': 'Automatique (F9)',
        'compiler_title_button': 'Maintenant ! (F9)',
        'executor_title_button': 'GO!(F9)',
        'executor_title': 'Exécution',
        'good': ["Bravo !", "Excellent !", "Super !", "Génial !", "Vous êtes trop fort !"],
        'icon_home': '🏠',
        'icon_save': '📩',
        'icon_local': '💾', # Used by session and question local save.
        'icon_git': '<b style="font-size:50%">GIT</b>',
        'icon_tag': 'TAG',
        'icon_stop': 'Terminer<br>Examen', # Only displayed if CHECKPOINT
        'stop_confirm': "Vous voulez vraiment terminer l'examen maintenant ?",
        'stop_done': "<h1>C'est fini.</h1>",
        'time_running': 'Fini dans',
        'time_done': "Fini depuis",
        'time_seconds': " secondes",
        'time_days': " jours",
        'time_d': " j ",
        'time_m': " m ",
        'time_h': " h ",
        # ------------------------------------
        # Default compiler and session options
        # ------------------------------------
        'allow_copy_paste': CP or GRADING or ADMIN, # True if copy/paste allowed
        'save_unlock': SAVE_UNLOCK,                 # True if saving a question unlock next
        'coloring': COLORING,                       # True if source highlighting is done
        'display_local_save': 0,                    # True if question 'icon_local' displayed
        'display_home': 1,                          # True if display 'icon_home'
        'display_local_git': 1,                     # True if question 'icon_git' displayed
        'display_local_zip': 1,                     # True if question 'icon_local' displayed
        'display_timer': 1,                         # True if the timer is displayed
        'display_compile_run': 1,                   # True if display the F9 button
        'display_tag': 1,                           # True if display 'icon_tag'
        'display_history': 1,                       # True if display version history
        'display_indent': 1,                        # True if display the F8 button
        'display_line_numbers': 0,                  # True if display line numbers
        'automatic_compilation': True,              # True if compilation is automatic
        # ------------------------------------
        # Options defined by the compiler used
        # ------------------------------------
        'compiler': '',        # 'g++' 'gcc' 'racket'
        'compile_options': [], # '-Wall' '-pedantic' '-pthread' '-std=c++11' '-std=c++20'
        'ld_options': [],      # '-lm'
        'language': '',        # Language to use for syntaxic coloring: 'cpp' 'python' ...
        'extension': '',       # Source code filename extension for ZIP and GIT: 'cpp', 'py'...
        # System call always allowed for g++/gcc, no need to specify them:
        #       clock_gettime close exit exit_group fstat futex lseek
        #       mmap munmap newfstatat openat read write
        # System calls allowable for g++/gcc:
        #       access arch_prctl brk clock_nanosleep
        #       clone clone3 execve getpid getrandom gettid madvise mprotect
        #       pipe pread64 prlimit64 rseq rt_sigaction rt_sigprocmask
        #       sched_yield set_robust_list set_tid_address tgkill
        'allowed': [],
        # -------------------------------
        # Unmodifiable session parameters
        # -------------------------------
        'COURSE': COURSE,                           # Course short name
        'TICKET': TICKET,                           # Session ticket: ?ticket=TICKET
        'LOGIN': LOGIN,                             # Login of the connected user
        'SOCK': SOCK,                               # Websocked for remote compilation
        'ANSWERS': ANSWERS,                         # All the questions/answers recorded
        'WHERE': WHERE,                             # See 'active_teacher_room' declaration
        'INFOS': INFOS,                             # Student identity
        'CHECKPOINT': CHECKPOINT,                   # True if checkpoint
        'GRADING': GRADING,                         # True if in grading mode
        'SEQUENTIAL': SEQUENTIAL and not GRADING,   # True if questions are sequential
        'ADMIN': ADMIN,                             # True if administrator
        'STOP': STOP,                               # True if the session is stopped
    }
    stop_timestamp = 0
    last_save = 0
    in_past_history = 0
    allow_edit = 0
    source_in_past = None
    records_last_retry = 0 # Wait before resending the form
    version = 0 # version being graded
    nr_grades = None
    grading = None
    current_key = None
    meter = document.createRange()

    def __init__(self):
        print("GUI: start")
        window.onerror = bind(self.onJSerror, self)
        self.start_time = millisecs()
        self.course = COURSE
        self.stop_timestamp = STOP
        self.worker = Worker(COURSE + "?ticket=" + TICKET) # pylint: disable=undefined-variable
        self.worker.onmessage = bind(self.onmessage, self)
        self.worker.onmessageerror = bind(self.onerror, self)
        self.worker.onerror = bind(self.onerror, self)
        self.worker.postMessage(['config', self.options])
        try:
            self.shared_buffer = eval('new Int32Array(new SharedArrayBuffer(1024))') # pylint: disable=eval-used
        except: # pylint: disable=bare-except
            self.shared_buffer = None
        self.worker.postMessage(['array', self.shared_buffer])
        if GRADING:
            # Will be updated after
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

    def popup_message(self, txt, cancel='', ok='OK', callback=None, add_input=False): # pylint: disable=no-self-use
        """For Alert and Prompt"""
        popup = document.createElement('DIALOG')
        if cancel != '':
            cancel = '<button id="popup_cancel">' + cancel + '</button>'
        if callback and add_input:
            input_value = '<br><input id="popup_input">'
        else:
            input_value = ''
        popup.innerHTML = txt + input_value + '<button id="popup_ok">' + ok + '</button>' + cancel
        document.body.appendChild(popup)

        def close():
            """Close the dialog"""
            document.body.removeChild(popup)

        def validate():
            if callback:
                if add_input:
                    callback(document.getElementById('popup_input').value)
                else:
                    callback()
            close()

        if cancel != '':
            document.getElementById('popup_cancel').onclick = close
        document.getElementById('popup_ok').onclick = validate

        def enter_escape(event):
            """Enter is OK escape is Cancel"""
            if event.key == 'Enter':
                validate()
            elif event.key == 'Escape':
                close()

        popup.onkeypress = enter_escape
        popup.showModal()

    def prompt(self, txt, callback): # pylint: disable=no-self-use
        """Replace browser prompt"""
        self.popup_message(txt, "Annuler", "OK", callback, True)

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
        self.record(['JS', message,
            url_error.split('?')[0].replace(window.location.origin, ''),
            lineNumber,
            navigator.userAgent,
            (error and error.stack or 'NoStack').toString(
                ).replace(RegExp('[?].*', 'g'), ')'
                ).replace(RegExp(window.location.origin, 'g'), '')
            ], True)
        return False

    def update_gui(self): # pylint: disable=too-many-branches,disable=too-many-statements
        """Set the bloc position and background"""
        if ('line_numbers' in self.options['positions']
            and self.options['positions']['line_numbers'][0] != 100):
            self.options['display_line_numbers'] = 1 # Compatibility with the past
        if self.options['display_line_numbers']:
            self.layered.setAttribute('display_line_numbers', 'yes')
        else:
            self.layered.setAttribute('display_line_numbers', 'no')
        self.options['positions']['editor_title'] = self.options['positions']['editor']
        if GRADING:
            left, width, top, height, background = self.options['positions']['editor']
            self.options['positions']['comments'] = [
                left + width, 100 - (left + width), top, height]
            left, width, top, height, background = self.options['positions']['question']
            self.options['positions']['question'][2] = 75
            self.options['positions']['question'][3] = 25
            self.options['positions']['grading'] = [left, width, 0, 75, '#FFF8']
            self.options['positions']['tester'][0] = 100 # Hide tester

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
                if GRADING:
                    if self.options['display_line_numbers']:
                        padding = self.line_numbers.offsetWidth + 5
                    else:
                        padding = 12
                    self.overlay.style.width = self.comments.offsetLeft - padding + 'px'
                    self.editor.style.width = self.comments.offsetLeft - padding + 'px'
                    self.overlay.style.left = self.editor.style.left = padding + 'px'
                else:
                    self.overlay.style.right = '0px'
                    self.editor.style.right = '0px'
            if not e:
                continue
            if left >= 100 or top >= 100:
                e.style.display = 'none'
            else:
                e.style.display = 'block'
            e.style.left = left + '%'
            if key == 'layered' and GRADING:
                e.style.right = '0px'
                self.comments.style.left = 100 * width / (100 - left) + '%'
                self.comments.style.right = '0px'
            else:
                e.style.right = (100 - left - width) + '%'
            if key == 'layered':
                e.style.top = 'calc(' + top + '% + var(--header_height))'
            else:
                e.style.top = top + '%'
            e.style.bottom = (100 - top - height) + '%'
            if key == 'editor_title':
                e.style.bottom = 'calc(100% - var(--header_height))'
            if key != 'layered':
                e.style.background = background
                e.background = background
        self.save_history.onchange = bind(self.change_history, self)
        if GRADING:
            self.save_button.style.display = 'none'
            if self.stop_button:
                self.stop_button.style.display = 'none'
    def create_gui(self): # pylint: disable=too-many-statements
        """The text editor container"""
        if GRADING:
            document.body.className = 'dograding'
        for key in self.options['positions']:
            if key == 'stop_button' and not CHECKPOINT:
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
                self.layered.appendChild(self.line_numbers)
                if GRADING:
                    self.comments = document.createElement('DIV')
                    self.comments.className = 'comments'
                    self.layered.appendChild(self.comments)
                e = self.layered
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

        self.editor_title.innerHTML = '<h2>' + self.options['editor_title'] + '</h2>'
        self.indent_button = document.createElement('LABEL')
        self.indent_button.innerHTML = self.options['editor_indent']
        self.indent_button.onclick = bind(self.do_indent, self)
        self.indent_button.className = 'indent_button'
        if self.options['display_indent']:
            self.editor_title.firstChild.appendChild(self.indent_button)

        self.save_button = document.createElement('TT')
        self.save_button.innerHTML = self.options['icon_save']
        self.save_button.style.fontFamily = 'emoji'
        self.save_button.onclick = bind(self.save_unlock, self)
        self.save_button.className = 'save_button'
        self.save_button.setAttribute('state', 'ok')
        self.save_button.setAttribute('enabled', 'false')
        self.editor_title.firstChild.appendChild(self.save_button)

        self.save_history = document.createElement('SELECT')
        if self.options['display_history']:
            self.save_history.className = 'save_history'
            self.editor_title.firstChild.appendChild(self.save_history)

        self.tag_button = document.createElement('LABEL')
        if self.options['display_tag']:
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
            self.popup_message("Rien à nommer :<br>il faut d'abord sauvegarder.")
            return

        def do_tagging(tag):
            """Record the tag"""
            self.record(['tag', self.current_question, timestamp, tag], True)
            for item in ALL_SAVES[self.current_question]:
                if item[0] == timestamp:
                    item[2] = tag
                    break
            self.update_save_history()
        self.prompt("Nom de la sauvegarde :", do_tagging)

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
        seconds = int(millisecs() / 1000)
        if (len(self.records_in_transit)
                and seconds - self.records_in_transit[0][0] > 5
                and seconds - self.records_last_retry > 5
           ):
            self.record_now()
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
            self.last_compile[self.current_question] = self.source
        if self.seconds != seconds:
            old_need_save = self.save_button.getAttribute('enabled') == 'true'
            need_save = self.need_save()
            if self.seconds % 5 == 0 or old_need_save != need_save:
                self.update_save_history()
            if old_need_save != need_save:
                self.save_button.setAttribute('enabled', need_save)
                try:
                    localStorage[COURSE + '/' + self.current_question] = self.source
                except: # pylint: disable=bare-except
                    pass
            self.seconds = seconds
            timer = document.getElementById('timer')
            if timer:
                delta = self.stop_timestamp - seconds + self.server_time_delta # pylint: disable=undefined-variable
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
                timer.innerHTML = message + '<br><div>' + delta + '</div>'

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
                if not state.last:
                    state.last = state.node
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

    def coloring(self): # pylint: disable=too-many-statements,too-many-branches
        """Coloring of the text editor with an overlay."""
        self.update_source()
        self.overlay.innerHTML = html(self.source_with_newlines)
        self.overlay.className = 'overlay language-' + self.options['language']
        if self.options['coloring']:
            hljs.highlightElement(self.overlay)
        for line_char, what in self.highlight_errors.Items():
            line_char = line_char.split(':')
            if len(line_char) == 2:
                line_nr, char_nr = line_char
                width = 1
            else:
                line_nr, char_nr, width = line_char
            self.add_highlight_errors(line_nr, char_nr, what, width)

        line_height = 1000
        comments = self.all_comments[self.current_question] or {}
        comments = comments[self.version] or {}
        i = 0
        for i, line in enumerate(self.editor_lines):
            rect = self.get_rect(line)
            if not self.line_numbers.childNodes[i]:
                self.line_numbers.appendChild(document.createElement('DIV'))
                self.line_numbers.childNodes[i].textContent = i+1
            if GRADING:
                comment = self.comments.childNodes[i]
                if not comment:
                    comment = document.createElement('TEXTAREA')
                    comment.line = i
                    self.comments.appendChild(comment)
                if comment.style.top != rect['top'] + 'px':
                    comment.style.top = rect['top'] + 'px'
                comment.value = (comments[i] or '').strip()
                if comments[i]:
                    comment.className = 'filled'
                else:
                    comment.className = 'empty'
                if comments[i]:
                    lines = comments[i].strip().split('\n')
                    comment.rows = len(lines)
                    comment.cols = min(max([len(line) for line in lines]), 50)
                else:
                    comment.rows = 3
                    comment.cols = 40

            self.line_numbers.childNodes[i].style.top = rect['top'] + 'px'
            if rect['height'] and rect['height'] < line_height:
                line_height = rect['height']
                continue
            if rect['height'] < line_height * 1.8:
                continue
            marker = document.createElement('DIV')
            marker.className = 'wrapped'
            marker.style.left = rect['left'] + 'px'
            marker.style.top = rect['top'] + line_height + 'px'
            marker.style.width = rect['width'] + 'px'
            marker.style.height = rect['height'] - line_height + 'px'
            self.overlay.appendChild(marker)
        for i in range(i+1, len(self.line_numbers.childNodes)):
            self.line_numbers.childNodes[i].style.top = '-10em'
        self.overlay_show()
        self.line_numbers.style.height = self.overlay.offsetHeight + 'px'
        if GRADING:
            self.comments.style.height = self.overlay.offsetHeight + 'px'

    def record_now(self):
        """Record on the server"""
        if len(self.record_to_send) == 0:
            if len(self.records_in_transit) == 0:
                return # Nothing to send
        else:
            self.records_in_transit.append(self.record_to_send)
            self.record_to_send = []
        self.record_last_time = 0
        self.records_last_retry = int(millisecs() / 1000)
        do_post_data(
            {
                'course': self.course,
                'line': encodeURIComponent(JSON.stringify(self.records_in_transit[0]) + '\n'),
            }, 'log?ticket=' + TICKET)

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

    def record_done(self, recorded_timestamp, stop_timestamp, server_time):
        """The server saved the recorded value"""
        if server_time:
            self.server_time_delta = int(millisecs()/1000 - server_time)
        self.stop_timestamp = stop_timestamp
        if self.records_in_transit[0] and recorded_timestamp == self.records_in_transit[0][0]:
            # Th expected recording has been done (in case of multiple retry)
            timestamp = 0
            for item in self.records_in_transit[0]:
                if item.toFixed:
                    timestamp += Number(item)
                    continue
                if item[0] in ('save', 'answer'):
                    current_question = item[1]
                    source = item[2]
                    self.last_save = timestamp
                    if not ALL_SAVES[current_question]:
                        ALL_SAVES[current_question] = []
                    ALL_SAVES[current_question].append([timestamp, source, ''])
                    self.update_save_history()
                    self.save_button.setAttribute('state', 'ok')
                    try:
                        del localStorage[COURSE + '/' + self.current_question]
                    except: # pylint: disable=bare-except
                        pass
            self.records_in_transit = self.records_in_transit[1:]
        if len(self.records_in_transit):
            self.record_now()

    def record_not_done(self, message):
        """The server can't save the data"""
        self.popup_message(message)
        self.records_in_transit = []

    def get_rect(self, element):
        """Get rectangle in self.layered coordinates"""
        if not element.getBoundingClientRect:
            self.meter.selectNodeContents(element)
            element = self.meter
        rect = element.getBoundingClientRect()
        return {
            'width': rect.width, 'height': rect.height,
            'top': rect.top - self.layered.offsetTop + self.layered.scrollTop,
            'left': rect.left - self.layered.offsetLeft - self.editor.offsetLeft
        }

    def add_highlight_errors(self, line_nr, char_nr, what, width=1):
        """Add the error or warning"""
        if not what:
            return
        box = document.createRange()
        def insert(element, class_name, move_right=0):
            """Set the element to the same place than the range"""
            rect = self.get_rect(box)
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
                    print('BUG', char_nr, line.nodeValue, line.innerText, line.nextSibling)
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
    def onmouseup(self, _event):
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
            clean = event.dataTransfer.getData('text/html').replace(
                RegExp('</?(span|div|br)', 'g'), '')
            if '<' in clean:
                self.popup_message("""Le glisser/déposer de balise HTML est impossible.<br>
                    Faites un copier/coller.""")
                event.preventDefault(True)
                return
            # def xxx():
            #     document.execCommand('undo', False)
            #     document.execCommand('insertText', False, text)
            # setTimeout(xxx, 500)
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
        text = (event.clipboardData or event.dataTransfer).getData("text/plain")
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
        self.do_coloring = True
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

    def update_cursor_position(self):
        """Queue cursor update position"""
        self.do_update_cursor_position = True

    def save_cursor(self):
        """Save the cursor position"""
        self.last_answer_cursor[self.current_question] = [
            self.layered.scrollTop,
            self.cursor_position,
            self.source[:self.cursor_position]
            ]
    def do_indent(self):
        """Formate the source code"""
        self.unlock_worker()
        self.save_cursor()
        self.worker.postMessage(['indent', self.source.strip()])

    def onkeydown(self, event): # pylint: disable=too-many-branches
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
        if event.target is self.editor and event.key not in (
                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'):
            self.clear_highlight_errors()
        if event.key == 'Tab':
            document.execCommand('insertHTML', False, '    ')
            event.preventDefault(True)
        elif event.key == 's' and event.ctrlKey:
            self.save_unlock()
            # self.save_local() # No more local save with Ctrl+S
            event.preventDefault(True)
        elif event.key == 'f' and event.ctrlKey:
            self.do_not_register_this_blur = True
            return
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
            self.do_indent()
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
        if self.insert_on_keyup:
            document.execCommand('insertHTML', False, self.insert_on_keyup)
            self.insert_on_keyup = None
        self.do_coloring = True
    def onkeypress(self, event):
        """Key press"""
    def onblur(self, _event):
        """Window blur"""
        if self.do_not_register_this_blur:
            self.do_not_register_this_blur = False
            return
        self.record('Blur')
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
        if self.in_past_history:
            saved = False
        else:
            saved = self.save()

        choosen = event.target.selectedOptions[0].getAttribute('timestamp')
        if not choosen:
            return
        choosen = int(choosen)
        if choosen == 1:
            source = self.question_original[self.current_question]
            self.in_past_history = 1
        else:
            for (timestamp, source, _tag) in ALL_SAVES[self.current_question]:
                if timestamp == choosen:
                    if not saved and timestamp == ALL_SAVES[self.current_question][-1][0]:
                        self.in_past_history = 0 # Back to the present
                    else:
                        self.in_past_history = timestamp
                    break
        self.source_in_past = source
        self.set_editor_content(source)
        self.editor.focus()
        self.update_save_history()

    def update_save_history(self):
        """The list of saved versions"""
        if self.save_history == document.activeElement:
            return
        content = []
        if self.need_save():
            content.append('<option>Non sauvegardé</option>')
            self.save_history.style.color = "#F00"
            self.in_past_history = 0
            self.tag_button.style.opacity = 0.3
            self.tag_button.style.pointerEvents = 'none'
        else:
            self.tag_button.style.opacity = 1
            self.tag_button.style.pointerEvents = 'all'
            self.save_history.style.color = "#000"
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
        content.append('<option timestamp="1">Version initiale</option>')
        if self.in_past_history == 1:
            content[-1] = content[-1].replace('<option', '<option selected')
        self.save_history.innerHTML = ''.join(content)

    def need_save(self):
        """Does the source file has changed?"""
        if self.in_past_history and self.source_in_past.strip() == self.source.strip():
            # Do not save again source from the past if they are unmodified
            return False
        return (self.last_answer[self.current_question]
            or self.question_original[self.current_question]).strip() != self.source.strip()

    def save(self, what='save'):
        """Save the editor content"""
        if not self.allow_edit:
            self.record(['allow_edit', 'save'])
            return False
        self.update_source()
        if self.need_save():
            self.save_button.setAttribute('state', 'wait')
            self.record([what, self.current_question, self.source], send_now=True)
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
        self.save()
        if confirm(self.options['stop_confirm']): # Let some time to execute the save
            record('/checkpoint/' + self.course + '/' + LOGIN + '/STOP', send_now=True)
            document.body.innerHTML = self.options['stop_done']

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
            ANSWERS[question][1] = version # Want to see the commented version
        self.do_coloring = True
        self.update_grading_select()

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
            if g not in grading or grading[g][0] == '':
                button.className = 'grade_unselected grade_undefined'
            elif button.innerText == grading[g][0]:
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
        else:
            element.style.background = "#FF0"

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

    def send_mail(self):
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

    def update_grading_select(self):
        """Upgrade the select choice with the good number of comments"""
        content = []
        now = Date()
        for i, version in enumerate(VERSIONS[self.current_question] or []): # pylint: disable=too-many-nested-blocks
            content.append('<option')
            if self.version == i:
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
                comments = self.all_comments[self.current_question]
                if comments:
                    comments = comments[i]
                    if comments:
                        nr = 0
                        for _line, comment in comments.Items():
                            if comment:
                                nr += 1
                        if nr:
                            content.append(' (' + nr + ' commentaires)')
            content.append('</option>')
        document.getElementById('grading_select').innerHTML = ''.join(content)

    def add_grading(self):
        """HTML of the grading interface"""
        self.version = (ANSWERS[self.current_question] or [0, 0])[1]
        content = [
            '''<div><h2>
            Noter <select id="grading_select" style="background:#FF0"
                          onchange="version_change(this)">
            '''
            ]
        content.append('</select>')
        content.append('<span id="grading_sum"></span>')
        content.append('</h2></div><pre>')

        i = 0
        for text, grade_label, values in parse_notation(NOTATION):
            content.append(html(text))
            if len(grade_label):
                content.append('<span>' + html(grade_label))
                for choice in values:
                    content.append('<button g="' + i + '">' + choice + '</button>')
                content.append('</span>')
            i += 1
        content.append('</pre>')
        self.nr_grades = i - 1
        self.grading.id = "grading"
        self.grading.onclick = grade
        self.grading.innerHTML = ''.join(content)

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
            self.do_not_clear = {}
            self.update_source()
            self.save_cursor()
            if (self.current_question >= 0 and value != self.current_question
                    and self.need_save() and not self.in_past_history):
                self.save()
            self.current_question = value
            self.record(['question', self.current_question])
            self.in_past_history = 0
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
            if self.current_question not in self.question_done:
                self.save('answer')
                self.question_done[self.current_question] = True
                messages = self.options['good']
                self.popup_message(messages[millisecs() % len(messages)])
        elif what == 'executor':
            self.clear_if_needed(what)
            for value in value.split('\001'):
                if not value:
                    continue
                if value.startswith('\002EVAL'):
                    #print(value[5:])
                    eval(value[5:]) # pylint: disable=eval-used
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
            links = []
            tips = []
            if self.options['display_home']:
                tips.append("Aller à l'accueil C5 listant toutes les sessions.")
                links.append('<a href="/' + window.location.search + '">'
                    + self.options['icon_home'] + '</a>')
                tips.append(' ')
                links.append(' ')
            if self.options['display_local_zip']:
                tips.append("Sauvegarder un ZIP de toutes les questions sur la machine locale")
                links.append('<a target="_blank" href="/zip/' + COURSE + window.location.search
                    + '">' + self.options['icon_local'] + '</a>')
            if self.options['display_local_git']:
                tips.append("Sauvegarder sur la machine locale avec l'historique dans GIT")
                links.append('<a target="_blank" href="/git/' + COURSE + window.location.search
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
            if GRADING and ',' in WHERE[2]:
                content.append(
                    '<div class="version">'
                    + WHERE[2].split(',')[3].replace('a', 'Ⓐ').replace('b', 'Ⓑ')
                    + '</div>')
            content.append(value)
            self[what].innerHTML = ''.join(content) # pylint: disable=unsubscriptable-object
        elif what == 'editor':
            # New question
            self.compile_now = True
            message = value + '\n\n\n'
            self.set_editor_content(message)
            try:
                old_version = localStorage[COURSE + '/' + self.current_question]
            except: # pylint: disable=bare-except
                old_version = None
            if not GRADING and old_version and old_version.strip() != message.strip():
                def get_old_version():
                    self.set_editor_content(old_version)
                self.popup_message(
                    "Une version non sauvegardée a été trouvée.",
                    'Effacer définitivement', ok='Continuer avec',
                    callback=get_old_version)
                del localStorage[COURSE + '/' + self.current_question]
        elif what == 'default':
            self.question_original[value[0]] = value[1]
        elif what in ('tester', 'compiler', 'question', 'time'):
            if not value:
                return
            self.clear_if_needed(what)
            if what == 'time':
                value += ' ' + self.state + ' ' + LOGIN
            need_update_grading_select = False
            if what == 'question' and GRADING and self[what].childNodes.length == 0: # pylint: disable=unsubscriptable-object
                self.add_grading()
                need_update_grading_select = True
            span = document.createElement('DIV')
            span.innerHTML = value
            if need_update_grading_select:
                self.update_grading_select()
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
            if self.in_past_history:
                # No changes were done in past, come back to present
                self.worker.postMessage(['source', self.current_question,
                    ALL_SAVES[self.current_question][-1][1]])
            else:
                self.worker.postMessage(['source', self.current_question, self.source])
            self.worker.postMessage(['goto', index])
        else:
            self.record(['allow_edit', 'goto_question'])

    def set_editor_content(self, message): # pylint: disable=too-many-branches,too-many-statements
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

            self.layered.scrollTop = scrollpos
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
            self.layered.scrollTop = 0
        # document.getSelection().collapse(self.editor, self.editor.childNodes.length)
        self.highlight_errors = {}
        self.do_coloring = True
        self.source = message
        self.update_save_history()

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
        window.onkeydown = bind(self.onkeydown, self)
        window.onkeyup = bind(self.onkeyup, self)
        window.onkeypress = bind(self.onkeypress, self)
        window.onbeforeunload = bind(self.onbeforeunload, self)
        window.onblur = bind(self.onblur, self)
        def do_coloring():
            self.do_coloring = True
        window.onresize = do_coloring
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
        """Parse messages from the Racket remote compiler"""
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
        span.innerHTML = '\n'.join(text[1:]).replace(
            RegExp('^([^ ]*) (.*) (#&lt;continuation-mark-set&gt;.*)$', 's'),
                '<i style="opacity:0.3">$1</i><br><b>$2</b><br><i style="opacity:0.3">$3</i>')
        span.onmouseenter = highlight
        span.onmouseleave = unhighlight
        self.executor.appendChild(span) # pylint: disable=unsubscriptable-object



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
    ccccc.compile_now = True

ccccc = CCCCC()
G = Grapic(ccccc)
