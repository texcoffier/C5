#!/usr/bin/python3
"""
Compiling and executing server

To detect that a process is reading its standard input :
   * \r is sent to its standard input
   * The \r is not taken into account by 'cin >> char'
   * FIONREAD allow to check if the process readed the \r
     and so need an INPUT to be displayed.

"""

from typing import Union, List, Tuple, Optional
import json
import asyncio
# original_sleep = asyncio.sleep
# async def sleep(seconds, loop=None, result=None):
#     print("sleep", seconds, flush=True)
#     if seconds == 0:
#         seconds = 0.01
#     return await original_sleep(seconds, result=result)
# asyncio.sleep = sleep
import os
import sys
import atexit
import signal
import time
import resource
import traceback
import subprocess
import urllib.request
import array
import fcntl
import termios
import pathlib
import shutil
import gc
import collections
import websockets
import re
import utilities

MIN_TIME_BETWEEN_CONNECT = 0.2 # Racket start time
PROCESSES = []
UID_MIN = int(utilities.C5_COMPILE_UID)
FREE_USERS = list(range(UID_MIN, UID_MIN+1000))

ALWAYS_ALLOWED = {"fstat", "newfstatat", "write", "read",
                  "lseek", "futex", "exit_group", "exit",
                  "clock_gettime", "openat", "mmap","munmap", "close"}
ALLOWABLE = {'brk', 'access', 'arch_prctl',
             'clone',
             'clone3', 'execve', 'getrandom', 'madvise',
             'mprotect', 'pread64', 'prlimit64',
             'rseq', 'rt_sigaction', 'rt_sigprocmask', 'sched_yield',
             'set_robust_list', 'set_tid_address', 'getpid', 'gettid', 'tgkill',
             'getppid',
             'wait4', # uwed by waipid
             'clock_nanosleep', 'pipe',
             'open'}

resource.setrlimit(resource.RLIMIT_NOFILE, (10000, 10000))

RACKETS = [] # Pool of racket processes

def set_compiler_limits() -> None:
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_DATA, (200*1024*1024, 200*1024*1024))

def set_racket_limits() -> None:
    """These limits should never be reached because enforced by racket sandbox itself"""
    # resource.setrlimit(resource.RLIMIT_CPU, (3600, 3600))
    resource.setrlimit(resource.RLIMIT_DATA, (200*1024*1024, 200*1024*1024))

def set_coq_limits() -> None:
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_DATA, (600*1024*1024, 600*1024*1024))
class Process: # pylint: disable=too-many-instance-attributes
    """A websocket session"""
    def __init__(self, websocket, login:str, course:str,
                 launcher:int) -> None:
        self.websocket = websocket
        self.conid = str(id(websocket))
        self.process:Optional[asyncio.subprocess.Process] = None
        self.allowed = ''
        self.waiting:Union[bool,str] = False
        self.tasks:List[asyncio.Task] = []
        self.input_done = asyncio.Event()
        self.login = login
        self.launcher = launcher
        self.course = utilities.CourseConfig.get(utilities.get_course(course))
        self.feedback = self.course.get_feedback(login)
        self.dir = f"{self.course.dir_log}/{login}"
        self.home = f"{self.dir}/HOME"
        if not os.path.exists(self.dir):
            if not os.path.exists(self.course.dir_log):
                os.mkdir(self.course.dir_log)
            os.mkdir(self.dir)
        self.exec_file = f"{self.dir}/{self.conid}"
        self.source_file = f"{self.dir}/{self.conid}.cpp"
        self.compiler = None
        self.canary = b''
        self.stdin_w:int = 0
        self.stdout:Optional[asyncio.StreamReader] = None
        self.filetree_in = ()
        self.filetree_out = ()
        self.use_pool = False # True if compile option 'use_pool'

    def log(self, more:Union[str,Tuple]) -> None:
        """Log"""
        if self.feedback:
            return
        print(f"{time.strftime('%Y%m%d%H%M%S')} {self.conid} {more}")

    def course_running(self) -> bool:
        """Check if the course is running for the user"""
        return self.course.running(self.login) or self.feedback

    def kill(self):
        """Kill all the processes of the process group"""
        self.log(("BeforeProcessKill", self.launcher))
        if self.compiler == 'racket':
            try:
                self.process.kill()
                self.log("RacketKilled")
            except ProcessLookupError:
                self.log("RacketDoesNotExists")
            self.process = None
            return
        try:
            with open(f"/sys/fs/cgroup/C5_{self.launcher}/cgroup.kill", "w",
                        encoding="ascii") as file:
                file.write('1')
            self.log("Killed")
        except FileNotFoundError:
            self.log("YetDead")
        except PermissionError:
            self.log("NotAllowed")
        self.close_fildes()
        self.process = None

    def close_fildes(self) -> None:
        """Close remaining pipe"""
        if self.stdin_w:
            self.log("CLOSE stdin_w")
            try:
                os.close(self.stdin_w)
            except (BrokenPipeError, OSError):
                pass
            self.stdin_w = 0

    def cancel_tasks(self):
        """Stop reading data"""
        for task in self.tasks:
            self.log("CANCEL")
            task.cancel()
        self.tasks = []

    def cleanup(self, erase_executable:bool=False, kill:bool=False) -> None:
        """Close connection"""
        self.log('CLEANUP')
        if erase_executable:
            try:
                os.unlink(self.exec_file)
            except FileNotFoundError:
                pass
            try:
                os.unlink(self.source_file)
            except FileNotFoundError:
                pass

        if self.compiler != 'racket' or erase_executable or kill:
            self.cancel_tasks()
        self.close_fildes()
        self.waiting = False
        if self.process:
            if self.compiler != 'racket' or erase_executable or kill:
                # Racket process must not be killed each time
                self.kill()
    def send_input(self, data:str) -> None:
        """Send the data to the running process standard input"""
        # self.log(("INPUT", data))
        if self.process and self.stdin_w:
            os.write(self.stdin_w, data.encode('utf-8') + b'\n')
        self.input_done.set()

    async def timeout(self) -> None:
        """May ask for input"""
        # pylint: disable=cell-var-from-loop
        to_check = self.process
        self.input_done.clear()
        if not self.process:
            self.log("NO_PROCESS_TIMOUT")
            return
        period = 0.05
        buffer = array.array('l', [0])
        while True:
            await asyncio.sleep(period)
            if self.waiting:
                if self.waiting == "done":
                    self.waiting = False
                continue
            if self.process is not to_check:
                return # The process changed and this task was not canceled!
            error = fcntl.ioctl(self.stdin_w, termios.FIONREAD, buffer, True) # pylint: disable=protected-access
            if not error and buffer[0] == 0:
                await asyncio.sleep(period) # Let the runner display the message
                self.log("ASK")
                if self.keep:
                    flush = self.keep.decode("utf-8", "replace")
                    self.keep = b''
                    await self.websocket.send(json.dumps(['executor', flush]))
                await self.websocket.send(json.dumps(['input', '']))
                await self.input_done.wait()
                self.input_done.clear()
                os.write(self.stdin_w, b'\r')

    async def runner(self) -> None: # pylint: disable=too-many-branches,too-many-statements
        """Pass the process output to the socket"""
        to_check = self.process
        if not self.process:
            self.log("NO_PROCESS_RUNNER")
            await self.websocket.send(json.dumps(
                ['return', "\nIl y a un problème..."]))
            self.cleanup()
            return
        size = 0
        self.keep = b''
        do_not_read = False
        self.log("RUNNER_START")
        assert self.stdout
        if self.compiler != 'racket':
            # Wait sandbox start message
            while True:
                line = await self.stdout.read(1000000)
                if not line:
                    break
                if self.canary in line:
                    self.keep = line.split(self.canary, 1)[1]
                    if self.keep:
                        do_not_read = True
                    break
            # If the process is not displaying: we assume it is reading
            # And so display an INPUT to the user.
            self.tasks.append(asyncio.ensure_future(self.timeout()))
        self.log("RUNNER_START_REAL")
        while True:
            if do_not_read:
                line = self.keep
                do_not_read = False
            else:
                to_add = await self.stdout.read(10000000)
                if to_add:
                    line = self.keep + to_add
                else:
                    if self.keep:
                        line = self.keep + b'\n\001\002RACKETFini !\001'
                    else:
                        break # Never here
            self.keep = b''
            if self.compiler == 'racket' and (line == b'\001' or b'\001' not in line):
                # cout << '\001' : freeze the server
                self.keep = line
                continue
            if b"\002WAIT" in line:
                self.waiting = True
            if b'\001' in line and not line.endswith(b'\001'):
                line, self.keep = line.rsplit(b'\001', 1)
                line += b'\001'
            if not self.keep and not line.endswith((b'\n', b'\001')) and b'\n' in line:
                # To not truncate a line in 2 DIV browser side.
                line, self.keep = line.rsplit(b'\n', 1)
                line += b'\n'
            if to_check is not self.process:
                return
            await self.websocket.send(json.dumps(['executor', line.decode("utf-8", "replace")]))
            if b"\002WAIT" in line:
                await self.input_done.wait()
                self.input_done.clear()
                self.waiting = "done"
            size += len(line)
            if size > self.max_data: # Maximum allowed output
                await self.websocket.send(json.dumps(['executor', "\nTrop de données envoyées au navigateur web"]))
                self.kill()
                break
            # self.log(("RUN", line[:100]))
            if b'\001\002RACKETFini !\001' in line:
                self.log(("EXIT", 0))
                await self.websocket.send(json.dumps(['return', "\n"]))
                if self.use_pool:
                    self.process.racket_free = True
                    self.process = None
                    self.cancel_tasks()
                    self.close_fildes()
                    break
                else:
                    continue # For Racket (no cleanup)
        if self.process:
            return_value = await self.process.wait()
            self.log(("EXIT", return_value))
            if return_value < 0:
                more = f'\n⚠️{signal.strsignal(-return_value)}'
                if return_value in (-6, -9):
                    more += f"\nVotre programme utilise plus de {self.max_time} sec. CPU,\n" \
                            "avez-vous fait une boucle/récursion infinie ?"
                self.process = None
            else:
                more = ''
            files = []
            for filename in self.filetree_out:
                file = pathlib.Path(f'{self.home}/{filename}')
                if file.exists():
                    files.append((filename, file.read_text('utf8')))
            await self.websocket.send(json.dumps(
                ['return', f"\nCode de fin d'exécution = {return_value}{more}", files]))
            self.cleanup()
    async def compile(self, data:Tuple) -> None:
        """Compile"""
        _course, _question, compiler, compile_options, ld_options, allowed, source = data
        self.use_pool = 'use_pool' in compile_options
        self.compiler = compiler
        self.log(("COMPILE", data[:6]))
        if compiler != 'racket':
            self.cleanup(erase_executable=True)
        with open(self.source_file, "w", encoding="utf-8") as file:
            file.write(source)
        if compiler in ('racket', 'coqc'):
            await self.websocket.send(json.dumps(['compiler', "Bravo, il n'y a aucune erreur"]))
            return
        stderr = ''
        forbiden = re.findall(r'(^\s*#.*(((/\.|\./|</|"/).*)|\\)$)', source, re.MULTILINE)
        if forbiden:
            stderr += f'Ligne interdite : «{forbiden[0][0]}»\n'
        if compiler not in ('gcc', 'g++'):
            stderr += f'Compilateur non autorisé : «{compiler}»\n'
        for option in compile_options:
            if option not in ('-Wall', '-pedantic', '-pthread', '-std=c++11', '-std=c++20',
                              'use_pool'):
                stderr += f'Option de compilation non autorisée : «{option}»\n'
        for option in ld_options:
            if option not in ('-lm',):
                stderr += f"Option d'édition des liens non autorisée : «{option}»\n"
        for option in allowed:
            if option not in ALLOWABLE and option not in ALWAYS_ALLOWED:
                stderr += f"Appel système non autorisé : «{option}»\n"
        if not stderr:
            self.allowed = ':'.join(list(ALWAYS_ALLOWED) + allowed)
            last_allowed = self.allowed.rsplit(':',1)[-1]
            self.canary = (
                f'adding {last_allowed} to the process seccomp filter (allow)\n'
                .encode('ascii'))
            self.process = await asyncio.create_subprocess_exec(
                compiler, *compile_options, '-I', '../../../..', '-I', '../../MEDIA',
                self.conid + '.cpp', *ld_options, '-o', self.conid,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=set_compiler_limits,
                close_fds=True,
                cwd=self.dir
                )
            assert self.process.stderr
            stderr_bytes = await self.process.stderr.read()
            if stderr_bytes:
                stderr = stderr_bytes.decode('utf-8').replace(self.conid, 'c5')
            else:
                stderr = "Bravo, il n'y a aucune erreur"
        await self.websocket.send(json.dumps(['compiler', stderr]))
        self.log(("ERRORS", stderr.count(': error:'), stderr.count(': warning:')))
        os.unlink(self.source_file)
    async def indent(self, data:str) -> None:
        """Indent"""
        process = await asyncio.create_subprocess_exec(
                'astyle',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                )
        assert process.stdin
        process.stdin.write(data.encode('utf-8'))
        process.stdin.close()
        assert process.stdout
        indented = await process.stdout.read()
        await self.websocket.send(json.dumps(['indented', indented.decode('utf-8')]))
    async def run(self, data) -> None:
        """Launch process"""
        self.filetree_in, self.filetree_out, self.max_time, self.max_data = data
        self.max_time = min(10, self.max_time)
        self.max_data = min(200000, self.max_data) * 1024
        if not hasattr(self, 'compiler'):
            self.log("UNCOMPILED")
            await self.websocket.send(json.dumps(['return', "Non compilé"]))
            return
        self.cleanup()
        if self.compiler == 'coqc':
            # Should use a runner in order to read values
            try:
                os.unlink(self.dir + '/test.v')
            except FileNotFoundError:
                pass
            os.symlink(self.conid + '.cpp', self.dir + '/test.v')
            self.process = await asyncio.create_subprocess_exec(
                'coqc', 'test.v',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                preexec_fn=set_coq_limits,
                close_fds=True,
                cwd=self.dir
                )
            assert self.process.stdout
            while True:
                line = await self.process.stdout.readline()
                if line:
                    await self.websocket.send(json.dumps(['executor', line.decode("utf-8", "replace")]))
                else:
                    break
            await self.websocket.send(json.dumps(
                ['return', f"\nCode de fin d'exécution = {await self.process.wait()}"]))
            self.cleanup()
            return
        if self.compiler == 'racket':
            self.log("RUN RACKET")
            if self.use_pool:
                for process in RACKETS:
                    if process.racket_free:
                        self.process = process
                        process.racket_free = False
                        self.stdout = self.process.stdout
                        self.tasks = [asyncio.ensure_future(self.runner())]
                        break
            if not self.process:
                self.log("LAUNCH-RACKET")
                self.process = await asyncio.create_subprocess_exec(
                    '/usr/bin/racket', "compile_racket.rkt",
                stdout=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                preexec_fn=set_racket_limits,
                close_fds=True,
                # ChatGPT suggest this to use less memory 2% less when I tried.
                env={'PLT_GC_VARIABLES': 'usemmap=no;generations=1;trim=yes',
                     # 'PLT_RACKET_NO_JIT': '1'
                    }
                )
                self.stdout = self.process.stdout
                self.tasks = [asyncio.ensure_future(self.runner())]
                if self.use_pool:
                    self.process.racket_free = False
                    RACKETS.append(self.process)
            assert self.process.stdin
            self.process.stdin.write(self.source_file.encode('utf-8') + b'\n')
            return
        if not os.path.exists(self.exec_file):
            self.log("RUN nothing")
            await self.websocket.send(json.dumps(['return', "Rien à exécuter"]))
            return
        self.log(f'./launcher {self.allowed} {self.launcher} {self.home} {self.max_time} ../{self.conid}')
        stdin_r, stdin_w = os.pipe()
        stdout_r, stdout_w = os.pipe()
        shutil.rmtree(self.home, ignore_errors=True)
        pathlib.Path(self.home).mkdir(exist_ok=True)
        for filename, content in self.filetree_in:
            filename = pathlib.Path(f"{self.home}/{filename}")
            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_text(content, encoding='utf8')

        self.process = await asyncio.create_subprocess_exec(
            "./launcher",
            self.allowed,
            str(self.launcher),
            self.home,
            str(self.max_time),
            '../' + self.conid,
            stdout=stdout_w,
            stdin=stdin_r,
            stderr=asyncio.subprocess.STDOUT,
            close_fds=True,
            )
        os.close(stdout_w)
        os.close(stdin_r)

        self.stdout = asyncio.StreamReader()
        read_protocol = asyncio.StreamReaderProtocol(self.stdout)
        await asyncio.get_running_loop().connect_read_pipe(
            lambda: read_protocol, os.fdopen(stdout_r, "rb"))

        self.stdin_w = stdin_w
        try:
            os.write(self.stdin_w, b'\r')
        except BrokenPipeError:
            os.close(self.stdin_w)
            self.stdin_w = 0
        self.tasks = [asyncio.ensure_future(self.runner())]

async def bad_session(websocket) -> None:
    """Tail the browser that the session is bad"""
    await websocket.send(json.dumps(['stop', 'Session expired']))
    await asyncio.sleep(10)

OBJECTS = {}

def search_leak():
    print('New objects from the first call')
    gc.collect()
    numbers = collections.defaultdict(int)
    for obj in gc.get_objects():
        numbers[type(obj)] += 1
    if OBJECTS:
        for k, nr in numbers.items():
            diff = nr - OBJECTS.get(k, 0)
            if diff:
                print(f'{k} {diff}')
    else:
        OBJECTS.clear()
        OBJECTS.update(numbers)
    print(flush=True)

async def echo(websocket) -> None: # pylint: disable=too-many-branches
    """Analyse the requests from one websocket connection"""
    try:
        path = websocket.request.path
    except AttributeError:
        path = websocket.path
    print(time.strftime('%Y%m%d%H%M%S'), path, flush=True)

    if time.time() < echo.next_allowed_start_time:
        wait = echo.next_allowed_start_time - time.time()
        echo.next_allowed_start_time += MIN_TIME_BETWEEN_CONNECT
        if wait > 0.5:
            await websocket.send(json.dumps(['wait',
                f"""Vous êtes dans la file d'attente.
Le programme s'exécutera dans {wait:.1f} secondes.
N'actualisez PAS la page."""]))
        await asyncio.sleep(wait)
    else:
        echo.next_allowed_start_time = time.time() + MIN_TIME_BETWEEN_CONNECT

    _, ticket, course = path.split('/')
    if not os.path.exists('TICKETS/' + ticket):
        await bad_session(websocket)
        return

    session = await utilities.Session.get(websocket, ticket, allow_ip_change='load_testing' in sys.argv)
    if not session:
        await bad_session(websocket)
        return

    login = session.login
    course = urllib.parse.unquote(course)

    process = Process(websocket, login, course, FREE_USERS.pop())
    PROCESSES.append(process)
    try:
        process.log(("START", ticket, login, course, process.launcher))
        async for message in websocket:
            action, data = json.loads(message)
            if action != 'input': # To many logs (Grapic)
                process.log(('ACTION', action))
            if not session.is_admin() and not process.course_running() and not session.is_grader(process.course):
                if action == 'compile':
                    await process.websocket.send(json.dumps(
                        ['compiler', f"La session est terminée pour {login}"]))
                if action == 'run':
                    await process.websocket.send(json.dumps(
                        ['return', f"La session est terminée pour {login}"]))
                continue
            if action == 'compile':
                await process.compile(data)
            elif action == 'indent':
                await process.indent(data)
            elif action == 'kill':
                process.cleanup(kill=True)
            elif action == 'input':
                if data == '\000KILL':
                    process.cleanup(kill=True)
                else:
                    process.send_input(data)
            elif action == 'run':
                await process.run(data)
            else:
                process.log(("BUG", action, data))
                await websocket.send(json.dumps(['compiler', 'bug']))
    except: # pylint: disable=bare-except
        if process.process:
            process.log(("EXCEPTION", traceback.format_exc()))
        else:
            process.log(("EXCEPTION", 'Because killed'))
    finally:
        process.log(("STOP", len(PROCESSES), len(FREE_USERS)))
        #process.cleanup(erase_executable=True)
        PROCESSES.remove(process)
        FREE_USERS.append(process.launcher)
    # search_leak()
echo.next_allowed_start_time = 0

async def main() -> None:
    """Answer compilation requests"""
    async with websockets.serve(echo, utilities.C5_IP, utilities.C5_SOCK, ssl=CERT): # pylint: disable=no-member
        print(f'Start using UID from {UID_MIN}')
        print(f"compile_server running {utilities.C5_IP}:{utilities.C5_SOCK}", flush=True)
        await asyncio.Future()  # run forever

CERT = utilities.get_certificate()
signal.signal(signal.SIGHUP, lambda signal, stack: sys.exit(0))
signal.signal(signal.SIGINT, lambda signal, stack: sys.exit(0))
signal.signal(signal.SIGQUIT, lambda signal, stack: sys.exit(0))
signal.signal(signal.SIGTERM, lambda signal, stack: sys.exit(0))
def clean():
    """Erase executables"""
    KILLER.kill()
    for process in PROCESSES:
        process.cleanup(erase_executable=True)

KILLER = subprocess.Popen("./killer") # pylint: disable=consider-using-with
atexit.register(clean)
asyncio.run(main())
