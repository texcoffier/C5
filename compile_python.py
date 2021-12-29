"""
Python compiler and interpreter
"""

importScripts('node_modules/brython/brython.js')

preamble = '''
__outputs__ = ''
def print(*args):
    global __outputs__
    __outputs__ += ' '.join(str(arg) for arg in args) + '\\n'
'''

class Compile_Python(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None
    language = "python"

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        try:
            # pylint: disable=eval-used
            x = __BRYTHON__.py2js(
                preamble + source + '\n' + self.quest.append_to_source_code(), 'ZZZ', 'ZZZ')
            self.post('compiler', 'Compilation sans erreur.')
            return x
        except Error as err: # pylint: disable=undefined-variable
            print(err)
            self.post('compiler', 'compile error\n')
            self.post(
                'compiler',
                '<error>'
                + self.escape(err.name) + '\n' + self.escape(err.message)
                + '</error>')
            return eval("function _() {}") # pylint: disable=eval-used
    def run_executor(self):
        """Execute the compiled code"""
        try:
            eval('var $locals_ZZZ = {}')
            eval(self.executable.to_js())
            self.execution_returns = eval('$locals_ZZZ.__outputs__')
            self.post('executor', self.execution_returns)
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'executor', '<error>'
                + self.escape(err.name) + '\n'
                + self.escape(err.message) + '</error>')
