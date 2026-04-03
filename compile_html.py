"""
HTML editor
"""

class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """HTML editor"""
    default_options = {'language': 'html', 'extension': 'html'}

    def run_compiler(self, source):
        """Nothing to do"""
        self.post('compiler', 'ok')
        return source
    def run_executor(self):
        """Execute the compiled code"""
        self.post('executor', self.executable)
