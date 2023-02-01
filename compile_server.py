#!/usr/bin/python3
"""
Compiling and executing server
"""

import json
import asyncio
import os
import sys
import atexit
import signal
import time
import resource
import traceback
import urllib.request
import psutil
import websockets
import utilities

PROCESSES = []

def set_limits():
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_DATA, (100*1024*1024, 100*1024*1024))

def set_compiler_limits():
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_DATA, (200*1024*1024, 200*1024*1024))

def set_racket_limits():
    """These limits should never be reached because enforced by racket sandbox itself"""
    resource.setrlimit(resource.RLIMIT_CPU, (3600, 3600))
    resource.setrlimit(resource.RLIMIT_DATA, (200*1024*1024, 200*1024*1024))

class Process: # pylint: disable=too-many-instance-attributes
    """A websocket session"""
    def __init__(self, websocket, login, course):
        self.websocket = websocket
        self.conid = str(id(websocket))
        self.process = None
        self.allowed = None
        self.waiting = False
        self.tasks = ()
        self.input_done = None
        self.login = login
        self.course = utilities.CourseConfig.get(utilities.get_course(course))
        course = self.course.dirname
        self.dir = f"{course}/{login}"
        if not os.path.exists(self.dir):
            if not os.path.exists(course):
                os.mkdir(course)
            os.mkdir(f"{course}/{login}")
        self.log_file = f"{self.dir}/compile_server.log"
        self.exec_file = f"{self.dir}/{self.conid}"
        self.source_file = f"{self.dir}/{self.conid}.cpp"
        self.compiler = None

    def log(self, more):
        """Log action to COURSE/login/compile_server.log"""
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(repr((int(time.time()), self.conid, more)) + '\n')

    def course_running(self):
        """Check if the course is running for the user"""
        return self.course.running(self.login, None)

    def cleanup(self, erase_executable=False, kill=False):
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
            for task in self.tasks:
                self.log("CANCEL")
                task.cancel()
        self.tasks = []
        self.waiting = False
        if self.process:
            if self.compiler != 'racket' or erase_executable or kill:
                # Racket process must not be killed each time
                try:
                    self.process.kill()
                    self.log("ProcessKilled")
                except ProcessLookupError:
                    pass
                self.process = None
    def send_input(self, data):
        """Send the data to the running process standard input"""
        self.log(("INPUT", data))
        if self.process and self.process.stdin:
            self.process.stdin.write(data.encode('utf-8') + b'\n')
        self.input_done.set()

    async def timeout(self):
        """May ask for input"""
        # pylint: disable=cell-var-from-loop
        self.input_done = asyncio.Event()
        process_info = psutil.Process(self.process.pid)
        period = 0.05
        state = (-1, 0, -1)
        nr_bad = 0
        while True:
            times = process_info.cpu_times()
            await asyncio.sleep(period)
            if self.waiting:
                if self.waiting == "done":
                    self.waiting = False
                continue
            if not self.process:
                return
            times = process_info.cpu_times()
            new_state = (times.user + times.system + times.children_user + times.children_system,
                         process_info.io_counters().write_count,
                         process_info.num_ctx_switches())
            if process_info.is_running() and new_state == state:
                nr_bad += 1
                if nr_bad == 1: # Increase to 2 if unexpected INPUT are displayed
                    self.log("ASK")
                    await self.websocket.send(json.dumps(['input', '']))
                    await self.input_done.wait()
                    self.input_done.clear()
                    nr_bad = 0
            else:
                nr_bad = 0
            state = new_state

    async def runner(self):
        """Pass the process output to the socket"""
        size = 0
        keep = b''
        while True:
            line = keep + await self.process.stdout.read(10000000)
            keep = b''
            if not line:
                break
            if line == b'\001':
                keep = line
                continue
            if b"\002WAIT" in line:
                self.waiting = True
            if b'\001' in line and not line.endswith(b'\001'):
                line, keep = line.rsplit(b'\001', 1)
                line += b'\001'
            await self.websocket.send(json.dumps(['executor', line.decode("utf-8", "replace")]))
            if b"\002WAIT" in line:
                await self.input_done.wait()
                self.input_done.clear()
                self.waiting = "done"
            size += len(line)
            if size > 10000000: # Maximum allowed output
                self.process.kill()
                break
            self.log(("RUN", line[:100]))
            if b'\001\002RACKETFini !\001' in line:
                self.log(("EXIT", 0))
                await self.websocket.send(json.dumps(['return', "\n"]))
                continue # For Racket (no cleanup)
        if self.process:
            return_value = await self.process.wait()
            self.log(("EXIT", return_value))
            if return_value < 0:
                more = f'\n⚠️{signal.strsignal(-return_value)}'
                if return_value == -9:
                    more += "\nVotre programme utilise plus d'une seconde,\n" \
                            "avez-vous fait une boucle infinie ?"
                self.process = None
            else:
                more = ''
            await self.websocket.send(json.dumps(
                ['return', f"\nCode de fin d'exécution = {return_value}{more}"]))
            self.cleanup()
    async def compile(self, data):
        """Compile"""
        _course, _question, compiler, compile_options, ld_options, allowed, source = data
        self.compiler = compiler
        self.log(("COMPILE", data))
        if compiler != 'racket':
            self.cleanup(erase_executable=True)
        with open(self.source_file, "w", encoding="utf-8") as file:
            file.write(source)
        if compiler == 'racket':
            await self.websocket.send(json.dumps(['compiler', "Bravo, il n'y a aucune erreur"]))
            return
        stderr = ''
        if compiler not in ('gcc', 'g++'):
            stderr += f'Compilateur non autorisé : «{compiler}»\n'
        for option in compile_options:
            if option not in ('-Wall', '-pedantic', '-pthread', '-std=c++11', '-std=c++20'):
                stderr += f'Option de compilation non autorisée : «{option}»\n'
        for option in ld_options:
            if option not in ('-lm',):
                stderr += f"Option d'édition des liens non autorisée : «{option}»\n"
        for option in allowed:
            if option not in ('brk', 'access', 'arch_prctl', 'clock_nanosleep',
                    'clone',
                    'clone3', 'close', 'execve', 'getrandom', 'madvise', 'mmap',
                    'mprotect', 'munmap', 'newfstatat', 'openat', 'pread64', 'prlimit64',
                    'rseq', 'rt_sigaction', 'rt_sigprocmask', 'sched_yield',
                    'set_robust_list', 'set_tid_address', 'getpid', 'gettid', 'tgkill',
                    'clock_nanosleep'):
                stderr += f"Appel système non autorisé : «{option}»\n"
        if not stderr:
            self.allowed = ':'.join(["fstat", "newfstatat", "write", "read",
                                     "lseek", "futex", "exit_group", "exit",
                                     "clock_gettime", "openat", "mmap","munmap", "close"] + allowed)
            self.process = await asyncio.create_subprocess_exec(
                compiler, *compile_options, '-I', '.',
                self.source_file, *ld_options, '-o', self.exec_file,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=set_compiler_limits,
                close_fds=True,
                )
            stderr = await self.process.stderr.read()
            if not stderr:
                stderr = "Bravo, il n'y a aucune erreur"
            else:
                stderr = stderr.decode('utf-8')
        await self.websocket.send(json.dumps(['compiler', stderr]))
        self.log(("ERRORS", stderr.count(': error:'), stderr.count(': warning:')))
        os.unlink(self.source_file)
    async def indent(self, data):
        """Indent"""
        process = await asyncio.create_subprocess_exec(
                'astyle',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                )
        process.stdin.write(data.encode('utf-8'))
        process.stdin.close()
        indented = await process.stdout.read()
        await self.websocket.send(json.dumps(['indented', indented.decode('utf-8')]))
    async def run(self):
        """Launch process"""
        if not hasattr(self, 'compiler'):
            self.log("UNCOMPILED")
            await self.websocket.send(json.dumps(['return', "Non compilé"]))
            return
        self.cleanup()
        if self.compiler == 'racket':
            self.log("RUN RACKET")
            if not self.process:
                self.log("LAUNCH-RACKET")
                self.process = await asyncio.create_subprocess_exec(
                    self.compiler, "compile_racket.rkt",
                stdout=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                preexec_fn=set_racket_limits,
                close_fds=True,
                )
                self.tasks = [asyncio.ensure_future(self.runner())]
            self.process.stdin.write(self.source_file.encode('utf-8') + b'\n')
            return
        if not os.path.exists(self.exec_file):
            self.log("RUN nothing")
            await self.websocket.send(json.dumps(['return', "Rien à exécuter"]))
            return
        print(f"LD_PRELOAD=sandbox/libsandbox.so "
              f"SECCOMP_SYSCALL_ALLOW={self.allowed} "
              f"{self.course.dirname}/{self.login}/{self.conid}", flush=True)
        self.process = await asyncio.create_subprocess_exec(
            f"{self.course.dirname}/{self.login}/{self.conid}",
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            # stderr=subprocess.PIPE,
            env={'LD_PRELOAD': 'sandbox/libsandbox.so',
                 'SECCOMP_SYSCALL_ALLOW': self.allowed,
                },
            close_fds=True,
            preexec_fn=set_limits,
            )
        self.tasks = [
            asyncio.ensure_future(self.timeout()),
            asyncio.ensure_future(self.runner())
        ]

async def bad_session(websocket):
    """Tail the browser that the session is bad"""
    await websocket.send(json.dumps(['stop', 'Session expired']))
    await asyncio.sleep(10)

async def echo(websocket, path): # pylint: disable=too-many-branches
    """Analyse the requests from one websocket connection"""
    print(path, flush=True)

    _, ticket, course = path.split('/')
    if not os.path.exists('TICKETS/' + ticket):
        await bad_session(websocket)
        return

    session = await utilities.Session.get(websocket, ticket)
    if not session:
        await bad_session(websocket)
        return

    login = session.login
    course = urllib.request.unquote(course)

    process = Process(websocket, login, course)
    PROCESSES.append(process)
    try:
        process.log(("START", ticket))
        async for message in websocket:
            action, data = json.loads(message)
            process.log(('ACTION', action))
            if not session.is_admin() and not process.course_running():
                if action == 'compile':
                    await process.websocket.send(json.dumps(
                        ['compiler', "La session est terminée"]))
                if action == 'run':
                    await process.websocket.send(json.dumps(
                        ['return', "La session est terminée"]))
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
                await process.run()
            else:
                process.log(("BUG", action, data))
                await websocket.send(json.dumps(['compiler', 'bug']))
    except: # pylint: disable=bare-except
        process.log(("EXCEPTION", traceback.format_exc()))
    finally:
        process.log("STOP")
        process.cleanup(erase_executable=True)
        PROCESSES.remove(process)

async def main():
    """Answer compilation requests"""
    await utilities.DNS.start()
    async with websockets.serve(echo, utilities.C5_IP, utilities.C5_SOCK, ssl=CERT): # pylint: disable=no-member
        print(f"compile_server running {utilities.C5_IP}:{utilities.C5_SOCK}", flush=True)
        await asyncio.Future()  # run forever

CERT = utilities.get_certificate()
signal.signal(signal.SIGHUP, lambda signal, stack: sys.exit(0))
signal.signal(signal.SIGINT, lambda signal, stack: sys.exit(0))
signal.signal(signal.SIGQUIT, lambda signal, stack: sys.exit(0))
signal.signal(signal.SIGTERM, lambda signal, stack: sys.exit(0))
def clean():
    """Erase executables"""
    for process in PROCESSES:
        process.cleanup(erase_executable=True)

atexit.register(clean)
asyncio.run(main())
