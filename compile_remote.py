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
        if self.connecting:
            return

        socket = eval('new WebSocket("wss://127.0.0.1:4200/hello", "1")')

        def event_message(event):
            data = JSON.parse(event.data)
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
                        except:
                            pass

            elif data[0] in ('executor', 'return'):
                self.post('executor', data[1])
                self.execution_returns += data[1]
                if data[0] == 'return':
                    self.post('state', "stopped")

        def event_open(_event):
            self.socket = socket
            self.connecting = False

        def event_error(event):
            print("Error", event)
            self.socket = None
            self.connecting = False

        socket.onopen = event_open
        socket.onmessage = event_message
        socket.onerror = event_error
        socket.onclose = event_error
        self.connecting = True

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        print('compile?')
        if not source:
            return True
        print('compile')
        if not self.socket:
            self.connect()
            self.post('compiler', 'On attend le serveur...<br>')
            def retry():
                self.run_compiler(source)
            setTimeout(retry, 100)
            return
        try:
            self.socket.send(JSON.stringify(['compile', source]))
            return
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'compiler',
                '<error>'
                + self.escape(err.name) + '\n' + self.escape(err.message)
                + '</error>')
            return eval("function _() {}") # pylint: disable=eval-used
    def run_executor(self):
        """Execute the compiled code"""
        print('execute')
        try:
            self.execution_returns = ''
            self.socket.send(JSON.stringify(['run', '']))
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'executor', '<error>'
                + self.escape(err.name) + '\n'
                + self.escape(err.message) + '</error>')
