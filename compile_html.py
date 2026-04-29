"""
HTML editor
"""

class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """HTML editor"""
    default_options = {'language': 'html', 'extension': 'html'}

    def run_compiler(self, source):
        """Nothing to do"""
        self.post('compiler', 'ok')
        return '<div style="white-space:initial;font-family:sans-serif">' + source + '</div>'
    def run_executor(self):
        """Execute the compiled code"""
        self.post('executor', self.executable)
    def run_indent(self, source):
        """Indent the source"""
        need_space = 0
        indenting = True
        depth = 0
        txt = []
        for i, char in enumerate(source):
            if indenting:
                if char == ' ':
                    if need_space == 0:
                        continue # Remove space
                    need_space -= 1
                else:
                    while need_space:
                        txt.append(' ')
                        need_space -= 1
                    indenting = False
            if char != ' ':
                indenting = False
                if char == '<':
                    if source[i+1] == '/':
                        depth -= 2
                        if depth < 0:
                            depth = 0
                    else:
                        if source[i+1:i+4].upper() not in ('IMG', 'BR>', 'BR/', 'HR>', 'HR/', 'INP'):
                            depth += 2
            txt.append(char)
            if char == '\n':
                indenting = True
                need_space = depth
        self.post('editor', ''.join(txt))
