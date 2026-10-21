"""
Pyodide

The SharedWorker is started by ccccc.py
"""

class Err:
    """Helper to create error message to send to the GUI"""
    def __init__(self):
        self.type = 'warning'
        self.line_number = 0
        self.backtrace_lines = []
        self.position = 0
        self.size = None
        self.source = ''
    def send(self):
        """Display the current error message in the editor"""
        if self.line_number:
            postMessage([self.type, [self.line_number, self.position, self.size]])
        self.__init__() # pylint: disable=unnecessary-dunder-call
class Session(Compile):
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None
    pyodide_globals = None
    shared_worker_asked = False
    run_tester_after_exec = False
    run_id = 0
    default_options = {'language': 'python', 'extension': 'py'}
    source = ''
    files = None

    def pyodide_message(self, event):
        """Analyse a message receive from the Pyodide shared worker"""
        if event.data[0] != self.run_id:
            return # old compilation result
        data = event.data[1:]
        if data[0] == 'globals':
            self.pyodide_globals = JSON.parse(data[1])
        elif data[0] == 'error':
            self.execution_result += data[1]
            errors = data[1].strip().split('\n')
            output = []
            state = ''
            pyodide_stack_start = None
            pyodide_stack_end = None
            error = Err()
            for line in errors:
                output.append(html(line))
                if not pyodide_stack_start and line.startswith('  File "/lib/python314.zip'):
                    pyodide_stack_start = len(output)
                if not pyodide_stack_end and 'File "__c5__.py"' in line:
                    pyodide_stack_end = len(output)
                if line.startswith('  File "__c5__.py", line '):
                    error.send()
                    error.line_number = int(line.split('line ')[1].split(',')[0])
                    state = 'source'
                    error.source = self.source.split('\n')[error.line_number - 1]
                    error.backtrace_lines.append(len(output)-1)
                    continue
                if state == 'source':
                    state = 'position'
                    if line.strip()[0] not in '^~':
                        error.source = line
                        error.backtrace_lines.append(len(output)-1)
                        continue
                if state == 'position':
                    state = ''
                    if line.strip()[0] in '^~':
                        indent = len(self.source.split('\n')[error.line_number-1]) - len(error.source)
                        error.position = indent + len(line) - len(line.strip()) + 1
                        error.size = len(line.strip())
                        error.backtrace_lines.append(len(output)-1)
                        continue
            if error.line_number:
                for i in error.backtrace_lines:
                    output[i] = '<b>' + output[i] + '</b>'
                error.type = 'error'
                error.send()
                output[-1] = '<b>' + output[-1] + '</b>'
            if pyodide_stack_start and pyodide_stack_end:
                # Rapydscript bug: use directly javascript function
                output.splice(pyodide_stack_start - 1, pyodide_stack_end - pyodide_stack_start)
            self.post('executor', '\n'.join(output))
        elif data[0] == 'stderr':
            self.execution_result += data[1]
            self.quest.tester_realtime_display(self.phase, self.nr_input, data[1])
            if self.phase != 0:
                return
            self.post('executor', data[1])
        elif data[0] == 'message':
            self.post('executor', data[1])
        elif data[0] == 'stdin':
            value = self.quest.tester_realtime_input(self.phase, self.nr_input)
            self.compiler_port.postMessage(value)
        elif data[0] == 'stdout':
            if data[1].startswith('data:image/png;base64,'):
                value = '<img style="width:100%" src="' + data[1][:-1] + '">\n'
            else:
                value = html(data[1])
            self.execution_result += data[1]
            self.quest.tester_realtime_display(self.phase, self.nr_input, data[1])
            if self.phase != 0:
                return
            self.post('executor', value)
        elif data[0] == 'return':
            self.execution_returns += data[1]
            self.quest.tester_realtime_exit(self.phase, self.nr_input, data[1])
        elif data[0] == 'file':
            self.files.append([data[1], data[2]])
        else:
            self.post('executor', 'Il y a un bug : ' + data)

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        if not self.compiler_port:
            if not self.shared_worker_asked:
                self.post('shared_worker', '/JS/pyodide.mjs')
                self.shared_worker_asked = True
            return 'fake executable'
        self.run_id += 1
        self.source = source
        self.pyodide_globals = {}
        return 'fake executable'

    def ask_pyodide(self):
        """Ask the Pyodide SharedWorker to execute the Python code"""
        self.compiler_port.postMessage([self.run_id, self.source,
            self.options['filetree_in'], self.options['filetree_out'],
            self.options['TICKET'], self.options['COURSE']])

    def run_executor(self):
        """Execute the Python program, needs to wait the SharedWorker startup"""
        self.execution_result = ''
        self.files = []
        self.post('executor', '')
        if self.compiler_port:
            self.ask_pyodide()
        else:
            def send():
                self.compiler_port.onmessage = bind(self.pyodide_message, self)
                self.compiler_port.start()
                self.ask_pyodide()
            setTimeout(send, 1000)

    def locals(self): # pylint: disable=no-self-use
        """Returns the local variable dict"""
        return self.pyodide_globals
