"""
Javascript compiler and interpreter
"""

class Compile_JS(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        try:
            # pylint: disable=eval-used
            executable = eval('''function _tmp_(args)
            {
               Compile.worker.execution_result = '';
               function print(txt)
                  {
                     if ( txt )
                          txt = self.escape(txt) ;
                     else
                          txt = '' ;
                     Compile.worker.execution_result += txt;
                     self.post('executor', txt + '\\n') ;
                 } ;
            ''' + source + '} ; _tmp_')
            self.post('compiler', 'Compilation sans erreur')
            return executable
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'compiler',
                '<error>'
                + self.escape(err.name) + '\n' + self.escape(err.message)
                + '</error>')
    def run_executor(self, args):
        """Execute the compiled code"""
        try:
            self.executable(args)
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'executor', '<error>'
                + self.escape(err.name) + '\n'
                + self.escape(err.message) + '</error>')
