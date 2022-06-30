"""
Javascript compiler and interpreter
"""

PREAMBLE = """
function _tmp_()
{
    Compile.worker.execution_result = '';
    function print()
        {
            var txt = '';
            for(var i in arguments)
                txt += ' '  + arguments[i];
            if ( txt )
                txt = self.escape(txt) ;
            else
                txt = '' ;
            txt += '\\n' ;
            Compile.worker.execution_result += txt;
            self.post('executor', txt) ;
        } ;
    function prompt(txt)
        {
            print(txt);
            return Compile.worker.read_input();
        }
"""

OFFSET = len(PREAMBLE) - 1

class Compile_JS(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        try:
            # pylint: disable=eval-used
            executable = eval(PREAMBLE + source + ';\n'
                              + self.quest.append_to_source_code() + '} ; _tmp_')
            self.post('compiler', 'Compilation sans erreur')
            return executable
        except Error as err: # pylint: disable=undefined-variable
            try:
                self.post(
                    'compiler',
                    '<error>'
                    + self.escape(err.name) + '\n' + self.escape(err.message)
                    + '</error>')
                # self.post('error', [err.lineno - OFFSET, err.colno])
                return None
            except: # pylint: disable=bare-except
                return None
    def run_executor(self):
        """Execute the compiled code"""
        try:
            self.execution_returns = self.executable()
        except Error as err: # pylint: disable=undefined-variable
            try:
                self.post(
                    'executor', '<error>'
                    + self.escape(err.name) + '\n'
                    + self.escape(err.message) + '</error>')
                # self.post('error', [err.lineno - OFFSET, err.colno])
            except: # pylint: disable=bare-except
                self.post('executor', '<error>BUG</error>')
