"""
Javascript compiler and interpreter
"""

class Compile_JS(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        try:
            # pylint: disable=eval-used
            executable = eval('''function _tmp_()
            {
               Compile.worker.execution_result = '';
               function print(txt)
                  {
                     if ( txt )
                          txt = self.escape(txt) ;
                     else
                          txt = '' ;
                     txt += '\\n' ;
                     Compile.worker.execution_result += txt;
                     self.post('executor', txt) ;
                 } ;
            ''' + source + ';\n' + self.quest.append_to_source_code() + '} ; _tmp_')
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
            self.execution_returns = self.executable()
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'executor', '<error>'
                + self.escape(err.name) + '\n'
                + self.escape(err.message) + '</error>')
