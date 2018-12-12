try:
    window
    in_browser = True
    @external
    class Worker:
        pass
except:
    in_browser = False

def new_element(htmltype, htmlclass, left, width, top, height, background):
    e = document.createElement(htmltype)
    e.className = htmlclass
    e.style.position = 'absolute'
    e.style.left = left + '%'
    e.style.right = (100 - left - width) + '%'
    e.style.top = top + '%'
    e.style.bottom = (100 - top - height) + '%'
    e.style.background = background
    return e

class CCCCC:
    question_width = 30
    question_height = 30
    source_width = 40
    compiler_height = 30
    
    def __init__(self):
        try:
            self.worker = Worker('xxx-ccccc.js')
            self.worker.onmessage = self.onmessage.bind(self)
            self.worker.onmessageerror = self.onmessage.bind(self)
            self.worker.onerror = self.onmessage.bind(self)
            print(self.worker)
        except:
            self.worker = None

    def create_question(self):
        e = new_element('DIV', 'question',
                        0, self.question_width,
                        0, self.question_height,
                        '#CFC')
        self.question = e
        self.top.appendChild(e)

    def create_tester(self):
        e = new_element('DIV', 'question',
                        0, self.question_width,
                        self.question_height, 100 - self.question_height,
                        '#EFE')
        self.tester = e
        self.top.appendChild(e)

    def create_editor(self):
        e = new_element('DIV', 'editor',
                        self.question_width, self.source_width,
                        0, 100,
                        '#FFF')
        e.contentEditable = true
        self.editor = e
        self.top.appendChild(e)
        self.editor.focus()

    def create_compiler(self):
        e = new_element('DIV', 'compiler',
                        self.question_width + self.source_width,
                        100 - self.question_width + self.source_width,
                        0, self.compiler_height,
                        '#CCF')
        self.compiler = e
        self.top.appendChild(e)

    def create_executor(self):
        e = new_element('DIV', 'executor',
                        self.question_width + self.source_width,
                        100 - self.question_width + self.source_width,
                        self.compiler_height, 100 - self.compiler_height,
                        '#EEF')
        self.executor = e
        self.top.appendChild(e)

    def run_executor(self, source):
        if source == '':
            return ''
        return JSON.parse(source).toString()

    def onmousedown(self, event):
        print("mouse down")
        self.editor.focus()
        event.preventDefault(True)

    def onkeydown(self, event):
        print("key down")

    def onkeyup(self, event):
        print("key up")
        self.worker.postMessage(self.editor.textContent)

    def onkeypress(self, event):
        print("key press")
       
    def onmessage(self, event):
        print(event)
        self.executor.textContent = event.data.toString()

    def create_html(self):
        self.top = document.createElement('DIV')
        self.top.onmousedown = self.onmousedown.bind(self)
        self.top.onkeydown = self.onkeydown.bind(self)
        self.top.onkeyup = self.onkeyup.bind(self)
        self.top.onkeypress = self.onkeypress.bind(self)
        document.getElementsByTagName('BODY')[0].appendChild(self.top)
        self.create_question()
        self.create_tester()
        self.create_editor()
        self.create_compiler()
        self.create_executor()

try:
    postMessage("Nothing to compile")
    def onmessage(event):
        postMessage('(' + event.data.toString() + ')')
    print("In the worker")
except:
    ccccc = CCCCC()
    if in_browser:
        ccccc.create_html()
    else:
        if ccccc.worker:
            ccccc.worker.postMessage("hello")
            
print("ok")

