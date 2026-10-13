var pyodide = undefined;

var RUNNING = 0;


async function onmessage(event) {
    var port = event.ports[0];
    if (!pyodide) {
        port.postMessage([0, 'message', "<p>Chargement de l'environnement.<br>Attendez une minute</p>\n"]);
        var [base, _search, _hash] = event.data;
        var module = await import(base + "/JS/pyodide/pyodide.mjs");
        pyodide = await (await module.loadPyodide());
    }
    function Stdin() {
    }
    Stdin.prototype.stdin = function () {
        port.postMessage(['stdin']);
        return '1234';
    };

    port.onmessage = async function (event) {
        var run_id = event.data[0]

        if (RUNNING) {
            port.postMessage([run_id, 'message', "<p>Le programme précédent est en cours d'exécution.<br>Relancez l'exécution plus tard.<br>Si cela persiste :<ul><li>modifiez votre programme<br>pour qu'il prenne moins de temps<li>puis rechargez la page.</ul></p>\n"]);
            return;
        }
        RUNNING = 1;

        function stdout(txt) {
            if (txt == 'No new packages to load')
                return;
            if (txt.includes('already loaded from default channel'))
                return;
            port.postMessage([run_id, 'stdout', txt + '\n']);
        }
        function stderr(txt) {
            port.postMessage([run_id, 'stderr', txt + '\n']);
        }
        pyodide.setStdout({ batched: stdout });
        pyodide.setStderr({ batched: stderr });
        pyodide.setStdin(new Stdin());
        let namespace = pyodide.globals.get("dict")();
        namespace.set('TICKET', event.data[4])
        namespace.set('COURSE', event.data[5])
        await pyodide.loadPackagesFromImports(event.data[1]);
        for (var [filename, content] of event.data[2])
            pyodide.FS.writeFile(filename, content, { encoding: "utf8" });
        pyodide.FS.writeFile('c5.py', `
import pyodide.http
import base64
import sys
import io

async def read(filename, course=None, bytes=False):
    """Read data from a C5 media"""
    i = 1
    while 'TICKET' not in sys._getframe(i).f_globals:
        i += 1
    TICKET = sys._getframe(i).f_globals['TICKET']
    if course is None:
        course = sys._getframe(i).f_globals['COURSE']
    url = f'../media/{course}/{filename}?ticket={TICKET}'
    request = await pyodide.http.pyfetch(url)
    if bytes:
        return await request.bytes()
    return await request.text()

def display_png(data):
    """Display binary data as a PNG image"""
    print("data:image/png;base64,"
        + base64.b64encode(data).decode("ascii"))

def display_plot(fig=None):
    import matplotlib.pyplot as plt # Here to not increase the loading time
    if fig is None:
        fig = plt.gcf()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    display_png(buf.getvalue())
`)
        try {
            await pyodide.runPythonAsync(event.data[1], { filename: "c5.py", globals: namespace });
            port.postMessage([run_id, "globals", JSON.stringify(namespace.toJs())]);
            for (var filename of event.data[3]) {
                try {
                    content = pyodide.FS.readFile(filename, { encoding: "utf8" });
                    port.postMessage([run_id, 'file', filename, content])
                } catch(e) {
                }
            }
            port.postMessage([run_id, 'return', pyodide.exitStatus])
        } catch (error) {
            console.log(error.message);
            port.postMessage([run_id, 'error', error.message]);
        }
        namespace.destroy();
        RUNNING = 0;
    };
    port.start();
};

self.onconnect = function (event) {
    event.ports[0].onmessage = onmessage;
}
