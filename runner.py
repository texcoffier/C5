"""
The runner copy a process output to the websocket.
If the process want to read: send the information to the websocket
"""

import asyncio
import fcntl
import termios
import array
import json
import os
import pathlib
import signal
import traceback
import websockets

RUNNERS = set()
class Runner: # pylint: disable=too-many-instance-attributes
    """Manage a process input and output"""
    session = None
    waiting = False
    stdin = None
    keep = None
    line = None
    waiting = False
    def __init__(self, session, process, canary=b'', stdin=None):
        self.session = session # The session may change in the future
        self.process = process # The process does not change
        self.canary = canary
        self.max_data = self.session.max_data

        self.input_done = asyncio.Event()
        self.log(("RUNNER_START", self.max_data))
        self.tasks = [asyncio.ensure_future(self.runner())]
        # If the process is not displaying: we assume it is reading
        # And so display an INPUT to the user.
        if stdin:
            try:
                self.stdin = stdin.transport.get_extra_info('pipe').fileno()
                os.write(self.stdin, b'\r')
            except ValueError:
                self.log("SOCKET CLOSED BEFORE START")
                return
            except BrokenPipeError:
                self.log("PROCESS DEAD BEFORE START")
                return
            self.tasks.append(asyncio.ensure_future(self.test_if_process_is_reading()))
        RUNNERS.add(self)

    def stop(self, uid=None):
        """Stop the process.
        After calling this function no more 'await' is possible.
        """
        if self not in RUNNERS:
            return
        for task in self.tasks:
            task.cancel()
        if uid:
            try:
                with open(f"/sys/fs/cgroup/C5_{uid}/cgroup.kill", "w",
                            encoding="ascii") as file:
                    file.write('1')
            except FileNotFoundError:
                self.log("YetDead")
            except PermissionError:
                self.log("NotAllowed")
        try:
            self.process.kill()
        except (ProcessLookupError, PermissionError):
            pass
        self.waiting = False
        RUNNERS.remove(self)

    def log(self, data):
        """Only log if somebody is reading process output"""
        if self.session:
            self.session.log(data)

    def send_input(self, data:str) -> None:
        """Send the data to the running process standard input"""
        # self.log(("INPUT", data))
        if self.stdin:
            try:
                os.write(self.stdin, data.encode('utf-8') + b'\n')
            except OSError:
                pass # Dead process
        self.input_done.set()

    async def test_if_process_is_reading(self) -> None:
        """May ask for input"""
        # pylint: disable=cell-var-from-loop
        self.input_done.clear()
        if not self.session:
            return
        period = 0.05
        buffer = array.array('l', [0])
        while True:
            await asyncio.sleep(period)
            # Check if the process is reading its standard input
            error = fcntl.ioctl(self.stdin, termios.FIONREAD, buffer, True) # pylint: disable=protected-access
            if error or buffer[0]:
                continue
            if self.waiting:
                # The process asked something itself.
                # No need the ask a second time to the browser
                if self.waiting == 'done':
                    self.waiting = False
                continue
            await asyncio.sleep(period) # Let the runner display the message
            self.log("ASK")
            if self.keep:
                flush = self.keep.decode("utf-8", "replace")
                self.keep = b''
                if self.session:
                    await self.session.websocket.send(json.dumps(['executor', flush]))
            if self.session:
                await self.session.websocket.send(json.dumps(['input', '']))
            await self.input_done.wait() # Wait browser input
            self.input_done.clear()
            self.waiting = False
            os.write(self.stdin, b'\r')

    async def read_preambule(self):
        """Wait sandbox start message.
        Returns a string containing the execution output start
        """
        if not self.canary:
            return b''
        keep = b''
        while True:
            line = await self.process.stdout.read(1000000)
            if not line:
                break
            if self.canary in line:
                keep = line.split(self.canary, 1)[1]
                break
        return keep

    def dump(self):
        """Dump the state of all runners"""
        for runner in RUNNERS:
            if runner.session:
                s = runner.session
                session = f'{s.login:10.10} {s.course.course:10.10} {s.uid:4}'
            else:
                session = ' '*26
            print(session, str(runner.waiting)[:5], int(runner.input_done.is_set()),
                runner.session.cmp.status(runner) if runner.session and runner.session.cmp else "")

    async def runner(self) -> None:
        """Helper"""
        try:
            await self.runner_()
        except asyncio.exceptions.CancelledError:
            if self.session:
                self.stop(self.session.uid)
        except: # pylint: disable=bare-except
            traceback.print_exc()

    async def runner_(self) -> None: # pylint: disable=too-many-branches,too-many-statements
        """Pass the process output to the socket"""
        self.size = 0
        self.keep = await self.read_preambule()
        self.log(('RUNNER_START_REAL', self.process, self.keep))
        need_to_read_more = self.session.cmp.need_to_read_more
        kill_if_too_much_data_is_sent = self.session.cmp.kill_if_too_much_data_is_sent
        while True:
            to_add = await self.process.stdout.read(10000000)
            self.line = line = self.keep + to_add
            self.keep = b''
            if await need_to_read_more(self):
                continue
            if b"\002WAIT" in line: # Process asks to wait
                self.waiting = "process"
            if b'\001' in line and not line.endswith(b'\001'):
                line, self.keep = line.rsplit(b'\001', 1)
                line += b'\001'
            if not self.keep and not line.endswith((b'\n', b'\001')) and b'\n' in line:
                # To not truncate a line in 2 DIV browser side.
                line, self.keep = line.rsplit(b'\n', 1)
                line += b'\n'
            if self.session:
                try:
                    await self.session.websocket.send(json.dumps(
                        ['executor', line.decode("utf-8", "replace")]))
                except websockets.exceptions.ConnectionClosed:
                    pass # The run must continue for Racket
            if b"\002WAIT" in line: # Wait browser answer
                await self.input_done.wait()
                self.input_done.clear()
                self.waiting = 'done'
            self.size += len(line)
            if self.size > self.max_data: # Maximum allowed output
                if self.session:
                    try:
                        await self.session.websocket.send(json.dumps(
                            ['executor', "\nTrop de données envoyées au navigateur web"]))
                    except websockets.exceptions.ConnectionClosed:
                        pass # The run must continue for Racket
                if kill_if_too_much_data_is_sent(self):
                    break
            if not to_add:
                break # Process ended (closed stdout)
        exit_value = await self.process.wait()
        if not self.session:
            return
        self.log(("EXIT", exit_value))
        if exit_value < 0:
            more = f'\n⚠️{signal.strsignal(-exit_value)}'
            if exit_value in (-6, -9):
                more += "\nVotre programme utilise trop de temps CPU,\n" \
                        "avez-vous fait une boucle/récursion infinie ?"
            elif exit_value == -11:
                more += "\nVotre programme utilise trop de mémoire."
        else:
            more = ''
        files = []
        for filename in self.session.filetree_out:
            file = pathlib.Path(f'{self.session.home}/{filename}')
            if file.exists():
                files.append((filename, file.read_text('utf8')))
        await self.session.websocket.send(json.dumps(
            ['return', f"\nCode de fin d'exécution = {exit_value}{more}", files]))
        self.stop(self.session.uid)
