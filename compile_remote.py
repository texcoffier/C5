"""
Run the compilation and execution on a remote server
"""

class Compile_remote(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None
    language = 'cpp'
    socket = None
    connecting = False
    stop_after_compile = False

    def connect(self):
        """Connect to the remote compiler/executor with a WebSocket"""
        print('connect', self.connecting)
        if self.connecting:
            return
        # pylint: disable=eval-used
        course = self.config.COURSE[:-3]
        socket = eval('new WebSocket(self.config.SOCK + "/" + self.config.TICKET + "/" + course, "1")')

        def event_message(event):
            data = JSON.parse(event.data) # pylint: disable=undefined-variable
            if data[0] == 'compiler':
                self.run_after_compile()
                message = data[1]
                if 'Bravo, il' not in message:
                    message = '<error>' + message + '<error>'
                self.post('compiler', message)
                for line in data[1].split('\n'):
                    line = line.split(':')
                    if line[0] == 'c.cpp':
                        try:
                            line_nr = int(line[1])
                            char_nr = int(line[2])
                            if 'error' in line[3]:
                                self.post('error', [line_nr, char_nr])
                            elif 'warning' in line[3]:
                                self.post('warning', [line_nr, char_nr])
                        except: # pylint: disable=bare-except
                            pass

            elif data[0] in ('executor', 'return'):
                self.post('executor', data[1])
                self.execution_returns += data[1]
                if data[0] == 'return':
                    self.post('state', "stopped")
            elif data[0] == 'input':
                try:
                    line = self.read_input()
                    self.socket.send(JSON.stringify(['input', line])) # pylint: disable=undefined-variable
                except ValueError:
                    self.socket.send(JSON.stringify(['kill', ''])) # pylint: disable=undefined-variable

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
        print('sock', '__SOCK__', self.socket, 'src', len(source or ''))
        if not source:
            self.post('compiler', 'Rien à compiler')
            self.post('state', "stopped")
            return True
        if not self.socket:
            print('call connect')
            self.connect()
            self.post('compiler', 'On attend le serveur...<br>')
            def retry():
                print('retry')
                self.run_compiler(source)
            setTimeout(retry, 100) # pylint: disable=undefined-variable
            return None
        try:
            self.socket.send(JSON.stringify( # pylint: disable=undefined-variable
                ['compile', [self.config.COURSE, self.current_question, source]]))
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
        print('execute', self.executable)
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
