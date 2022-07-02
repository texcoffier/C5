"""
CPP compiler and interpreter based upon JSCPP

Very limited.
"""

self.window = window = {'document': 'fake'} # pylint: disable=undefined-variable,invalid-name
importScripts('xxx-JSCPP.js' + self.location.search) # pylint: disable=undefined-variable
JSCPP = self.window.JSCPP # pylint: disable=undefined-variable


class Compile_CPP(Compile): # pylint: disable=undefined-variable,invalid-name
    """CPP compiler and evaluator"""
    execution_result = ''
    execution_returns = None
    language = 'cpp'

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        if not source:
            return True
        try:
            def stdio(text):
                self.execution_returns += text
                self.post('executor', text)
            def error(text, code):
                self.post('executor', text + '\n$$$$$$$$$' + str(code))
            executable = JSCPP.run(
                source,
                '',
                {
                    'stdio': {'write': stdio},
                    'debug': True
                },
                error)
            self.post('compiler', 'Compilation sans erreur')
            return executable
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'compiler',
                '<error>'
                + self.escape(err.name) + '\n' + self.escape(err.message)
                + '</error>')
            return True
    def run_executor(self):
        """Execute the compiled code"""
        if self.executable is True:
            return
        try:
            self.execution_returns = ''
            for _ in range(100000):
                value = self.executable.next()
                if value is not False:
                    break
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'executor', '<error>'
                + self.escape(err.name) + '\n'
                + self.escape(err.message) + '</error>')
