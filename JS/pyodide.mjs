var C5 = `
import pyodide.http
import base64
import sys
import io
import asyncio
import pathlib
import builtins

def get_globals():
    i = 1
    while 'TICKET' not in sys._getframe(i).f_globals:
        i += 1
    return sys._getframe(i).f_globals

async def read_data():
    stdin = pathlib.Path('__stdin__')
    while True:
        if stdin.exists():
            content = stdin.read_text()
            if content.startswith('\\000KILL'):
                sys.exit(1)
            stdin.unlink()
            return content
        await asyncio.sleep(0.01)

async def input():
    get_globals()['__ask__']() # Ask for user input
    return await read_data()

async def wait_input():
    get_globals()['__ask2__']() # Wait for user input (for Grapic)
    return await read_data()

async def read(filename, course=None, bytes=False):
    """Read data from a C5 media"""
    g = get_globals()
    TICKET = g['TICKET']
    if course is None:
        course = g['COURSE']
    url = f'../media/{course}/{filename}?ticket={TICKET}'
    request = await pyodide.http.pyfetch(url)
    if bytes:
        return await request.bytes()
    return await request.text()

def display_png(data):
    """Display binary data as a PNG image"""
    builtins.print("data:image/png;base64,"
        + base64.b64encode(data).decode("ascii"))

def display_plot(fig=None):
    import matplotlib.pyplot as plt # Here to not increase the loading time
    if fig is None:
        fig = plt.gcf()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    display_png(buf.getvalue())

# Grapic library
SDLK_UP = "ArrowUp"
SDLK_DOWN = "ArrowDown"
SDLK_LEFT = "ArrowLeft"
SDLK_RIGHT = "ArrowRight"
SDL_BUTTON_LEFT = 0
SDL_BUTTON_MIDDLE = 2
SDL_BUTTON_RIGHT = 3
SDL_FLIP_NONE = 0
SDL_FLIP_HORIZONTAL = 1
SDL_FLIP_VERTICAL = 2
class Grapic:
    x = y = 0
    key = ''
    button = ''
    width = height = 0
def grapic(text):
    builtins.print('\\001\\002EVALG.' + text + '\\001', end='')
def winInit(_title, width, height, posx=None, posy=None, fullscreen=None):
    Grapic.width = width
    Grapic.height = height
    grapic(f'init({width},{height})')
def backgroundColor(r, g, b):
    grapic(f'backgroundColor({r},{g},{b})')
def fontSize(size):
    grapic(f'fontSize({size})')
def rectangleFill(x1, y1, x2, y2):
    grapic(f'rectangleFill({x1},{y1},{x2},{y2})')
def rectangle(x1, y1, x2, y2):
    grapic(f'rectangle({x1},{y1},{x2},{y2})')
def circle(x, y, r):
    grapic(f'circle({x},{y},{r})')
def circleFill(x, y, r):
    grapic(f'circleFill({x},{y},{r})')
def line(x1, y1, x2, y2):
    grapic(f'line({x1},{y1},{x2},{y2})')
def triangle(x1, y1, x2, y2, x3, y3):
    grapic(f'triangle({x1},{y1},{x2},{y2},{x3},{y3})')
def triangleFill(x1, y1, x2, y2, x3, y3):
    grapic(f'triangleFill({x1},{y1},{x2},{y2},{x3},{y3})')
def ellipseFill(x1, y1, rx, ry):
    grapic(f'ellipseFill({x1},{y1},{rx},{ry})')
def ellipse(x1, y1, rx, ry):
    grapic(f'ellipse({x1},{y1},{rx},{ry})')
def polygon(points):
    grapic(f'polygon({points})')
def polygonFill(points):
    grapic(f'polygonFill({points})')
def grid(x1, y1, x2, y2, nx, ny):
    grapic(f'grid({x1},{y1},{x2},{y2},{nx},{ny})')
def color(r, g, b, a=255):
    grapic(f'color({r},{g},{b},{a})')
def winClear():
    grapic(f'clear()')
def put_pixel(x, y, r, g, b, a=255):
    grapic(f'putPixel({x},{y},{r},{g},{b},{a})')
def put_pixel(x, y, r, g, b, a=255):
    grapic(f'putPixel({x},{y},{r},{g},{b},{a})')
def print(x, y, text):
    grapic(f'print({x},{y},{repr(text)})')
async def winDisplay():
    builtins.print("\\001\\002WAITD\\001")
    i = await wait_input()
    if 'KILL' in i:
        raise ValueError('Killed')
    i = i.split('\\n')
    Grapic.button, Grapic.x, Grapic.y = [int(v) for v in i[1:4]]
    Grapic.y = Grapic.height - Grapic.y
    Grapic.key = i[0][1:]
def delay(millisecs):
    time.sleep(millisec / 1000)
async def pressSpace():
    builtins.print(10, 10, "Press a key")
    builtins.print("\\001\\002WAITK\\001")
    i = await wait_input()
def isKeyPressed(key):
    return key == Grapic.key
def isMousePressed(button):
    return button == Grapic.button
def mousePos():
    return Grapic.x, Grapic.y
mousePosGlobal = mousePos
def winQuit():
    grapic('quit()')
def winHasFinished():
    return 0

def not_implemented(text):
    fontSize(40)
    color(0, 0, 0)
    print(10, 10, text)
    color(255, 255, 255)
    print(10, 60, text)
def menu_add        (*args,**kargs): not_implemented('menu_add')
def menu_nr_items   (*args,**kargs): not_implemented('menu_nr_items')
def menu_draw       (*args,**kargs): not_implemented('menu_draw')
def menu_select     (*args,**kargs): not_implemented('menu_select')
def setKeyrepeatMode(*args,**kargs): not_implemented('setKeyrepeatMode')
def plot_setSize    (*args,**kargs): not_implemented('plot_setSize')
def plot_add        (*args,**kargs): not_implemented('plot_add')
def plot_draw       (*args,**kargs): not_implemented('plot_draw')
def image           (*args,**kargs): not_implemented('image')
def image_printInfo (*args,**kargs): not_implemented('image_printInfo')
def image_draw      (*args,**kargs): not_implemented('image_draw')
def image_width     (*args,**kargs): not_implemented('image_width')
def image_height    (*args,**kargs): not_implemented('image_height')
def draw_arrow      (*args,**kargs): not_implemented('draw_arrow')

`;
function Runner() {
    // Only one execution at one in the browser.
    // Starting a an execution stops the other.
    this.pyodide = undefined;
    this.port = undefined;    // The client
    this.run_id = undefined;  // The execution number for the client
    this.wait_input = 0;
    this.pending_kill = 0;
    this.ports = [];
}

async function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

Runner.prototype.log = function (txt) {
    console.log(`PI=${this.port ? this.port.port_id : 'U'} RI=${this.run_id === undefined ? 'U' : this.run_id} WI=${this.wait_input} PK=${this.pending_kill} ${txt}`);
};
// Comment the line to activate the traces
Runner.prototype.log = function (_txt) {} ;

Runner.prototype.kill = async function () {
    if (!this.port) {
        this.log('YET KILLED');
        return;
    }
    this.log('KILL START');
    this.pending_kill = 1;
    if (this.run_id !== undefined)
        this.port.postMessage([this.run_id, 'message', "Arrête le programme en train de s'exécuter"]);
    while (this.port) {
        // Boucle infini dans certain cas avec 2 fenêtres, mais pas tout le temps.
        this.log('KILLING');
        this.pyodide.FS.writeFile('__stdin__', '\x00KILL', { encoding: "utf8" });
        await sleep(100);
    }
    this.pending_kill = 0;
    this.log('KILL DONE');
};
Runner.prototype.exited = function () {
    this.log('EXITED');
    this.port = undefined;
    this.run_id = undefined;
    this.wait_input = 0;
    this.namespace.destroy();
};
Runner.prototype.new_client = async function (event) {
    this.log('NEW CLIENT START');
    var port = event.ports[0];
    if (!this.pyodide) {
        this.log('PYODIDE LOAD START');
        port.postMessage([0, 'message',
            "<p>Chargement de l'environnement.<br>Attendez une minute</p>\n"]);
        var [base, search, _hash] = event.data;
        var module = await import(base + "/JS/pyodide/pyodide.mjs" + search);
        this.pyodide = await (await module.loadPyodide());
        this.pyodide.setStdout({ batched: this.stdout.bind(this) });
        this.pyodide.setStderr({ batched: this.stderr.bind(this) });
        this.log('PYODIDE LOAD DONE');
    }
    this.ports.push(port);
    port.port_id = this.ports.length;
    port.onmessage = this.onmessage.bind(this);
    port.start();
    this.log('NEW CLIENT DONE');
};
Runner.prototype.stdout = function (txt) {
    if (txt == 'No new packages to load')
        return;
    if (txt.includes('already loaded from default channel'))
        return;
    if(txt.charAt(0) != '\x01')
        txt += '\n'
    this.port.postMessage([this.run_id, 'stdout', txt]);
};
Runner.prototype.stderr = function (txt) {
    this.port.postMessage([this.run_id, 'stderr', txt + '\n']);
};
Runner.prototype.init_globals = function () {
    this.log('INIT GLOBALS START');
    var namespace = this.pyodide.globals.get("dict")();
    namespace.set('TICKET', this.ticket);
    namespace.set('COURSE', this.course);
    var THIS = this;
    namespace.set('__ask__',
        function () {
            THIS.log('ASK INPUT');
            THIS.wait_input = 1;
            THIS.port.postMessage([THIS.run_id, 'stdin']);
        });
    namespace.set('__ask2__',
        function () {
            THIS.log('WAIT INPUT');
            THIS.wait_input = 1;
        });
    this.log('INIT GLOBALS DONE');
    return namespace;
};
Runner.prototype.init_files = function () {
    this.log('INIT FILES START');
    var files = this.pyodide.FS.readdir('.');
    for (var filename of files)
        if (filename != '.' && filename != '..')
            try {
                this.pyodide.FS.unlink(filename);
            } catch (e) { }
    this.pyodide.FS.writeFile('c5.py', C5);
    for (var [filename, content] of this.file_in)
        this.pyodide.FS.writeFile(filename, content, { encoding: "utf8" });
    this.log('INIT FILES DONE');
};
Runner.prototype.send_final_state = function (exit_code) {
    this.log('SEND FINAL STATE');
    this.port.postMessage([this.run_id, "globals", JSON.stringify(this.namespace.toJs())]);
    for (var filename of this.file_out) {
        var content = '?';
        try {
            content = this.pyodide.FS.readFile(filename, { encoding: "utf8" });
            this.port.postMessage([this.run_id, 'file', filename, content])
        } catch (e) {
        }
    }
    this.port.postMessage([this.run_id, 'return', exit_code])
};

Runner.prototype.onmessage = async function (event) {
    var port = event.target;
    var run_id = event.data[0];
    this.log('RECEIVE CLIENT MESSAGE PI=' + port.port_id + ' RI=' + run_id);
    while (this.pending_kill)
        await sleep(100);
    if (this.wait_input && event.data[1] == '\x00KILL') {
        this.log('KILL RECEIVED');
        await this.kill();
        return;
    }
    while (this.port && port !== this.port // Not same client
        || this.run_id !== undefined && run_id !== this.run_id) // Not same execution 
        await this.kill();
    if (this.wait_input) {
        this.log('INPUT RECEIVED');
        this.pyodide.FS.writeFile('__stdin__', event.data[1], { encoding: "utf8" });
        this.log('INPUT STORED');
        this.wait_input = 0;
        return;
    }
    // No Python programm is currently running, starts one.
    this.port = port;
    this.run_id = event.data[0];
    this.source = event.data[1];
    this.file_in = event.data[2];
    this.file_out = event.data[3];
    this.ticket = event.data[4];
    this.course = event.data[5];
    this.namespace = this.init_globals();
    await this.pyodide.loadPackagesFromImports(this.source);
    this.init_files();
    try {
        this.log("START RUN");
        await this.pyodide.runPythonAsync(this.source, { filename: "__c5__.py", globals: this.namespace });
        this.send_final_state(0);
    } catch (error) {
        console.log(error.message);
        try {
            if(!this.pending_kill) {
                port.postMessage([event.data[0], 'error', error.message]);
                this.send_final_state(1);
            }
        } catch (e) { }
    }
    this.exited();
};

var RUNNER = new Runner();
self.onconnect = function (event) {
    event.ports[0].onmessage = RUNNER.new_client.bind(RUNNER);
}
