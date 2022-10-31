"""
LISP compiler and interpreter
"""

# pylint: disable=self-assigning-variable,eval-used,len-as-condition

importScripts('xxx-lips.min.js') # pylint: disable=undefined-variable

class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """LISP compiler and evaluator"""
    execution_result = ''
    execution_returns = None

    def init(self):
        """Initialisations"""
        self.set_options({'language': 'lisp', 'extension': 'rkt'})

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        try:
            self.execution_result = ''
            lips.exec(source)
            return ''
        except Error as err: # pylint: disable=undefined-variable
            #for k in err:
            #    print(k, err[k])
            self.post(
                'compiler',
                '<error>'
                + self.escape(err.msg) + '\n'
                + 'Ligne ' + self.escape(err.lineno - OFFSET) + ' :\n'
                + '<b>' + self.escape(err.text) + '</b>\n'
                + '</error>')
            self.post('error', [err.lineno - OFFSET, err.offset])
            return True
