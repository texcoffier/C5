try:
    window
    in_browser = True
    @external
    class Worker:
        pass
except:
    in_browser = False

def html(txt):
    return str(txt).replace("&", "&amp;").replace("<","&lt;").replace(">","&gt;")

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
        self.worker = None
        if in_browser:
            try:
                self.worker = Worker('xxx-ccccc.js')
                self.worker.onmessage = self.onmessage.bind(self)
                self.worker.onmessageerror = self.onmessage.bind(self)
                self.worker.onerror = self.onmessage.bind(self)
                print(self.worker)
            except:
                pass

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

    def run(self, source):
        c = self.run_compiler(source)
        if c:
            postMessage(['run', None])
            self.run_executor(c, [])

    def onmousedown(self, event):
        print("mouse down")
        self.editor.focus()
        event.preventDefault(True)
    def onkeydown(self, event):
        if event.key == 'Tab':
            event.preventDefault(True)
    def onkeyup(self, event):
        self.worker.postMessage(self.editor.textContent)
    def onkeypress(self, event):
        pass
    def onmessage(self, event):
        if event.data[0] == 'run':
            e = self.executor
        else:
            e = self.compiler
        if event.data[1] is None:
            if event.data[0] == 'run':
                e.innerHTML = self.executor_initial_content()
            else:
                e.innerHTML = self.compiler_initial_content()
        else:
            e.innerHTML += event.data[1]

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

    def compiler_initial_content(self):
        return "RESULTAT DE LA COMPILATION<hr>"
    def executor_initial_content(self):
        return "RESULTAT DE L'EXÉCUTION<hr>"

class CCCCC_JS(CCCCC):
    def run_compiler(self, source):
        postMessage(['compile', None])
        try:
            f = eval('''function _tmp_(args)
            {
               function print(txt)
                  {
                     if ( txt )
                          txt = html(txt) ;
                     else
                          txt = '' ;
                     postMessage(['run', txt + '<br>']) ;
                 } ;
            ''' + source + '} ; _tmp_')
            postMessage(['compile', 'Compilation sans erreur'])
            return f
        except as err:
            postMessage(['compile',
                   '<error>'
                    + html(err.name) + '<br>\n' + html(err.message)
                    + '</error>'])
            postMessage(['run', None])
    def run_executor(self, fct, args):
        try:
            fct(args)
        except as err:
            postMessage(['run', '<error>'
                    + html(err.name) + '<br>\n'
                    + html(err.message) + '</error>'])


ccccc = CCCCC_JS()
if in_browser:
    ccccc.create_html()
else:
    def onmessage(event):
        ccccc.run(event.data.toString())
            
print("ok")

