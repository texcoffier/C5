"""
SQL compiler and interpreter
"""

importScripts('node_modules/alasql/dist/alasql.js') # pylint: disable=undefined-variable

class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """SQL compiler and evaluator"""
    execution_result = ''
    execution_returns = None

    def init(self):
        """Initialisations"""
        self.set_options({'language': 'SQL', 'extension': 'sql'})

    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        try:
            # pylint: disable=eval-used
            executable = eval('alasql(' + JSON.stringify(source) + ')')
            self.post('compiler', 'Compilation sans erreur')
            return executable
        except Error as err: # pylint: disable=undefined-variable
            try:
                line = err.message.split('Parse error on line ')
                if len(line) > 1:
                    self.post('error', [int(line[1].split(':')[0]), 1])
                self.post(
                    'compiler',
                    '<error>'
                    + self.escape(err.name) + '\n' + self.escape(err.message)
                    + '</error>')
                return None
            except: # pylint: disable=bare-except
                return None
    def run_executor(self):
        """Execute the compiled code"""
        try:
            content = []
            for result in self.executable:
                if isNaN(result):
                    content.append('<table border>\n')
                    columns = {}
                    for line in result:
                        for key in line:
                            columns[key] = 1
                    content.append('<tr>')
                    for key in columns:
                        content.append('<th>' + html(key) + '</th>')
                    content.append('</tr>')
                    for line in result:
                        content.append('<tr>')
                        for key in columns:
                            content.append('<td>' + html(str(line[key])) + '</td>')
                        content.append('</tr>\n')
                    content.append('</table>\n')
                else:
                    content.append('Command return value: ' + html(str(result)) + '\n')
            self.execution_returns = ''.join(content)
            self.post('executor', self.execution_returns)
        except Error as err: # pylint: disable=undefined-variable
            try:
                self.post(
                    'executor', '<error>'
                    + self.escape(err.name) + '\n'
                    + self.escape(err.message) + '</error>')
            except: # pylint: disable=bare-except
                self.post('executor', '<error>BUG</error>')
