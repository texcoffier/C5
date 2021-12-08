"""
Javascript compiler and interpreter
"""

class CCCCC_JS(CCCCC): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        self.post('compile', None)
        try:
            # pylint: disable=eval-used
            executable = eval('''function _tmp_(args)
            {
               function print(txt)
                  {
                     if ( txt )
                        {
                          CCCCC.current.execution_result += txt ;
                          txt = self.escape(txt) ;
                        }
                     else
                          txt = '' ;
                     self.post('run', txt + '\\n') ;
                 } ;
            ''' + source + '} ; _tmp_')
            self.post('compile', 'Compilation sans erreur')
            return executable
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'compile',
                '<error>'
                + self.escape(err.name) + '\n' + self.escape(err.message)
                + '</error>')
    def run_executor(self, args):
        """Execute the compiled code"""
        try:
            self.executable(args)
        except Error as err: # pylint: disable=undefined-variable
            self.post(
                'run', '<error>'
                + self.escape(err.name) + '\n'
                + self.escape(err.message) + '</error>')
