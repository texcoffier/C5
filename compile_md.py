"""
MD compiler
"""

try:
    importScripts('node_modules/marked/lib/marked.umd.js') # pylint: disable=undefined-variable
except NameError:
    pass # Called from Makefile




class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """MD compiler"""
    default_options = {'language': 'markdown', 'extension': 'md'}

    def run_compiler(self, source):
        """Nothing to do"""
        self.post('compiler', 'ok')
        return source
    def run_executor(self):
        """Execute the compiled code"""
        html = """<style>
DIV { white-space: wrap; font-family: sans-serif }
</style>
"""
        html += marked.parse(self.executable)

        self.post('executor', html)
