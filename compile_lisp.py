"""
LISP compiler and interpreter
"""

def nothing():
    """Do nothing"""
    return {}

document = {
    'querySelectorAll': nothing,
    'documentElement': {},
    'addEventListener': nothing,
}
window = self # pylint: disable=undefined-variable

importScripts('node_modules/@jcubic/lips/src/lips.js')

class Session(Compile):
    """LISP compiler and evaluator"""
    execution_result = ''
    execution_returns = None
    environment = None
    run_tester_after_exec = False
    source = None

    def init(self):
        """Initialisations"""
        self.set_options({
            'language': 'lisp',
            'extension': 'rkt',
            'positions' : {
                'question': [1, 29, 0, 30, '#EFE'],
                'tester': [1, 29, 30, 70, '#EFE'],
                'editor': [30, 40, 0, 100, '#FFF'],
                'compiler': [100, 30, 0, 100, '#EEF'],
                'executor': [70, 30, 0, 100, '#EEF'],
                'time': [80, 20, 98, 2, '#0000'],
                'index': [0, 1, 0, 100, '#0000'],
                'line_numbers': [100, 1, 0, 100, '#EEE'], # Outside the screen by defaut
                }
            })

    def run_compiler(self, source):
        """All is done in executor"""
        self.source = source
        return nothing

    def run_executor(self):
        """Compile, display errors and return the executable"""
        source = self.source
        if not source:
            return None
        def stdout(txt):
            """Forward printing to GUI"""
            if txt[0] != '(':
                txt = txt[1:-1]
            self.execution_result += txt
            self.post('executor', html(txt))  # pylint: disable=undefined-variable
        def read(resolve): # pylint: disable=unused-variable
            resolve(self.read_input())
        def stdin():
            return eval('new Promise(read)') # pylint: disable=eval-used
        environment = {'stdout': {'write': stdout}, # pylint: disable=unused-variable
                       'stdin': {'read': stdin},
                      }
        self.environment = eval( # pylint: disable=eval-used
            "new window.lips.Environment(environment, window.lips.global_environment)")
        self.environment.set('=', self.environment.get('=='))
        def onerror(error):
            self.post('executor', '<error>' + str(error) + '<br>'
                      + html(str(error.code or '')) + '<error>') # pylint: disable=undefined-variable
        def done():
            self.post('state', "stopped")
            self.run_tester()
        self.execution_result = ''
        window.lips.exec(source, self.environment).catch(onerror).then(done, done) # pylint: disable=no-member

    def run_indent(self, _source):
        """LISP formatter"""
        code = eval("new window.lips.Formatter(source)") # pylint: disable=eval-used
        self.post('editor', code.format())
