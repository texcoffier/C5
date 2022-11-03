"""
Python compiler and interpreter
"""

# pylint: disable=self-assigning-variable,eval-used,len-as-condition

importScripts('node_modules/brython/brython.js') # pylint: disable=undefined-variable
importScripts('node_modules/brython/brython_stdlib.js') # pylint: disable=undefined-variable

if False: # pylint: disable=using-constant-test
    # pylint: disable=undefined-variable,invalid-name
    __BRYTHON__ = __BRYTHON__
    brython = brython
    Number = Number
    millisecs = millisecs
    html = html
    Question = Question

brython({'debug': 1})

PREAMBLE = '''
def print(*args, sep=' ', end='\\n'):
    __print__(sep.join(str(arg) for arg in args) + end)
def input():
    return __input__()
class __eRRor__:
    def write(self, txt):
        console.log(txt)
import _sys
_sys.stderr = __eRRor__()
'''

OFFSET = len(PREAMBLE.split('\n')) - 1

class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None

    def init(self):
        """Initialisations"""
        self.set_options({'language': 'python', 'extension': 'py'})

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        try:
            # pylint: disable=eval-used
            compiled = __BRYTHON__.python_to_js(
                PREAMBLE + source + '\n' + self.quest.append_to_source_code())
            self.post('compiler', 'Compilation sans erreur.')
            return compiled
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
    def run_executor(self):
        """Execute the compiled code"""
        if self.executable is True:
            return
        try:
            outputs = []
            def __print__(txt):
                outputs.append(txt)
                self.post('executor', txt)
            def __input__():
                return self.read_input()

            __BRYTHON__.mylocals = {'__print__': __print__, '__input__': __input__,
                                    '__worker__': self, '__millisecs__': millisecs,
                                    '__html__': html, '__Question__': Question}
            eval(self.executable.replace(
                'var $locals___main__ = {}',
                'var $locals___main__ = __BRYTHON__.mylocals ;'))
            self.execution_result = outputs.join('')  # pylint: disable=no-member

        except Error as err: # pylint: disable=undefined-variable
            try:
                message = self.escape(err.__class__['$infos'].__qualname__) + ' : '
                if len(err.args):
                    message += err.args[0]
                else:
                    message += err.name
                line = Number(err['$line_info'].split(',')[0]) - OFFSET
                message += '\nLigne : ' + (line + 1) + '\n'
                message += '<b>' + self.escape(self.source.split('\n')[line]) + '</b>\n'
                self.post('executor', '<error>' + message + '</error>')
                self.post('error', [line, err.offset])
            except: # pylint: disable=bare-except
                pass

    def locals(self): # pylint: disable=no-self-use
        """Returns the local variable dict"""
        return __BRYTHON__.mylocals
