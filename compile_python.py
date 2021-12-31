"""
Python compiler and interpreter
"""

# pylint: disable=self-assigning-variable,eval-used,len-as-condition

importScripts('brython/brython.js') # pylint: disable=undefined-variable
importScripts('brython/brython_stdlib.js') # pylint: disable=undefined-variable

__BRYTHON__ = __BRYTHON__ # pylint: disable=undefined-variable
brython = brython # pylint: disable=undefined-variable,invalid-name
Number = Number # pylint: disable=undefined-variable,invalid-name

brython({'debug': 1})

PREAMBLE = '''
def print(*args, sep=' ', end='\\n'):
    __outputs__.append(sep.join(str(arg) for arg in args) + end)
class __eRRor__:
    def write(self, txt):
        console.log(txt)
import _sys
_sys.stderr = __eRRor__()
'''

class Compile_Python(Compile): # pylint: disable=undefined-variable,invalid-name
    """JavaScript compiler and evaluator"""
    execution_result = ''
    execution_returns = None
    language = 'python'

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        try:
            # pylint: disable=eval-used
            compiled = __BRYTHON__.python_to_js(
                PREAMBLE + source + '\n' + self.quest.append_to_source_code())
            self.post('compiler', 'Compilation sans erreur.')
            return compiled
        except Error as err: # pylint: disable=undefined-variable
            # for k in err:
            #     print(k, err[k])
            self.post(
                'compiler',
                '<error>'
                + self.escape(err.msg) + '\n'
                + 'Ligne ' + self.escape(err.lineno) + ' :\n'
                + '<b>' + self.escape(err.text) + '</b>\n'
                + '</error>')
            return eval("function _() {}") # pylint: disable=eval-used
    def run_executor(self):
        """Execute the compiled code"""
        try:
            __BRYTHON__.mylocals = {'__outputs__': []}
            eval(self.executable.replace(
                'var $locals___main__ = {}',
                'var $locals___main__ = __BRYTHON__.mylocals ;'))
            self.execution_returns = __BRYTHON__.mylocals.__outputs__.join('')
            self.post('executor', self.execution_returns)
        except Error as err: # pylint: disable=undefined-variable
            message = self.escape(err.__class__['$infos'].__qualname__) + ' : '
            if len(err.args):
                message += err.args[0]
            else:
                message += err.name
            line = Number(err['$line_info'].split(',')[0]) - len(PREAMBLE.split('\n'))
            message += '\nLigne : ' + (line + 1) + '\n'
            message += '<b>' + self.escape(self.source.split('\n')[line]) + '</b>\n'
            self.post(
                'executor', '<error>' + message + '</error>')
