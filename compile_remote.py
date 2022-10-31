"""
Run the compilation and execution on a remote server
"""

class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None
    socket = None
    connecting = False
    stop_after_compile = False
    run_tester_after_exec = False
    nr_errors = nr_warnings = 0
    stoped = False

    def init(self):
        """Your own compiler init"""
        self.connect()
        self.set_options({
            'compiler': 'g++', # or 'gcc'
            'compile_options': ['-Wall'], # -pedantic -pthread
            'ld_options': [],
            'allowed': [],
            'language': 'cpp',
            'extension': 'cpp',
            })
        if self.config.GRADING:
            return
        self.popup("""
        <p>
        ATTENTION
        <p>
        Tout ce que vous faites est enregistré et pourra être
        retenu contre vous en cas de tricherie.
        <p>
        Si une autre personne a utilisé vos identifiants, c'est vous qui
        serez tenu comme responsable de ses crimes.
        """)

    def connect(self): # pylint: disable=too-many-statements
        """Connect to the remote compiler/executor with a WebSocket"""
        print('connect', self.connecting)
        if self.connecting or self.stoped:
            return
        # pylint: disable=eval-used
        course = self.config.COURSE
        url = self.config.SOCK + "/" + self.config.TICKET + "/" + course  # pylint: disable=unused-variable
        socket = eval('new WebSocket(url)')

        def event_message(event): # pylint: disable=too-many-branches
            data = JSON.parse(event.data) # pylint: disable=undefined-variable
            if data[0] == 'compiler':
                self.nr_errors = 0
                self.nr_warnings = 0
                self.run_after_compile()
                message = data[1]
                if 'Bravo, il' not in message:
                    message = '<error>' + self.escape(message) + '</error>'
                else:
                    message = self.escape(message)
                self.post('compiler', message)
                for line in data[1].split('\n'):
                    line = line.split(':')
                    if line[0][-4:] == '.cpp':
                        try:
                            line_nr = int(line[1])
                            char_nr = int(line[2])
                            if 'error' in line[3]:
                                self.post('error', [line_nr, char_nr])
                                self.nr_errors += 1
                            elif 'warning' in line[3]:
                                self.post('warning', [line_nr, char_nr])
                                self.nr_warnings += 1
                        except: # pylint: disable=bare-except
                            pass

            elif data[0] in ('executor', 'return'):
                self.post('executor', self.escape(data[1]))
                if data[0] == 'executor':
                    self.execution_result += data[1]
                else:
                    self.execution_returns += data[1]
                if data[0] == 'return':
                    self.post('state', "stopped")
                    self.run_tester()
            elif data[0] == 'input':
                try:
                    line = self.read_input()
                    self.socket.send(JSON.stringify(['input', line])) # pylint: disable=undefined-variable
                except ValueError:
                    self.socket.send(JSON.stringify(['kill', ''])) # pylint: disable=undefined-variable
            elif data[0] == 'indented':
                self.post('editor', data[1])
            elif data[0] == 'stop':
                self.post('stop', data[1])
                self.stoped = True

        def event_open(_event):
            print('Socket opened')
            self.socket = socket
            self.connecting = False

        def event_error(event):
            print("Error", event)
            self.socket = None
            self.connecting = False
            self.post('state', "stopped")
            def reconnect():
                print('reconnect')
                self.connect()
            setTimeout(reconnect, 1000) # pylint: disable=undefined-variable

        socket.onopen = event_open
        socket.onmessage = event_message
        socket.onerror = event_error
        socket.onclose = event_error
        self.connecting = True

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        if not source:
            self.post('compiler', 'Rien à compiler.')
            self.post('tester', self.tester_initial_content())
            self.post('executor', self.executor_initial_content())
            self.post('executor', 'Rien à exécuter')
            self.execution_result = ''
            self.execution_returns = None
            self.post('state', "stopped")
            self.run_tester()
            return None
        try:
            if not self.socket:
                self.connect()
                def retry():
                    self.run_compiler(source)
                setTimeout(retry, 1000)
                return eval("function _() {}") # pylint: disable=eval-used
            self.socket.send(JSON.stringify( # pylint: disable=undefined-variable
                ['compile', [
                    self.config.COURSE,
                    self.current_question,
                    self.options['compiler'],
                    self.options['compile_options'],
                    self.options['ld_options'],
                    self.options['allowed'],
                    source]]))
            return None
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'compiler',
                '<error>'
                + self.escape(err.name) + '\n' + self.escape(err.message)
                + '</error>')
            return eval("function _() {}") # pylint: disable=eval-used
    def run_executor(self):
        """Execute the compiled code"""
        if self.executable is True:
            self.execution_returns = ''
            return
        try:
            self.execution_returns = ''
            self.socket.send(JSON.stringify(['run', ''])) # pylint: disable=undefined-variable
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'executor', '<error>'
                + self.escape(err.name) + '\n'
                + self.escape(err.message) + '</error>')

    def run_indent(self, source):
        """Indent the source"""
        self.socket.send(JSON.stringify(['indent', source]))
