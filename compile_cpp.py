"""
CPP compiler and interpreter based upon JSCPP

Very limited.
"""

self.window = window = {'document': 'fake'}
importScripts('xxx-JSCPP.js')
JSCPP = self.window.JSCPP


class Compile_CPP(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None
    language = 'cpp'

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
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
            return eval("function _() {}") # pylint: disable=eval-used
    def run_executor(self):
        """Execute the compiled code"""
        try:
            self.execution_returns = ''
            for _ in range(100000):
                value = self.executable.next()
                if value != False:
                    break
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'executor', '<error>'
                + self.escape(err.name) + '\n'
                + self.escape(err.message) + '</error>')
