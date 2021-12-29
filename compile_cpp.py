"""
CPP compiler and interpreter

NOT WORKING
"""

# print("before")
# window = self
# importScripts('JSCPP.es5.min.js')
# for k in window:
#     print('==', k, window[k])
# print("after", JSCPP)
# importScripts('JSCPP.es5.min.js')
# JSCPP = require "JSCPP.es5.min.js"



class Compile_CPP(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None
    language = 'cpp'

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        try:
            # pylint: disable=eval-used
            self.post('compiler', 'look:')
            self.post('compiler', JSCPP)
            self.post('compiler', 'done')
            # ''' + source + ';\n' + self.quest.append_to_source_code() + '} ; _tmp_')
            # self.post('compiler', 'Compilation sans erreur')
            return eval("function _() {}")
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
            self.execution_returns = self.executable()
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'executor', '<error>'
                + self.escape(err.name) + '\n'
                + self.escape(err.message) + '</error>')
