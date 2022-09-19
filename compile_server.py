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
import websockets
import utilities

PROCESSES = []

def set_limits():
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_NOFILE, (10, 10))
    resource.setrlimit(resource.RLIMIT_DATA, (1000000, 1000000))
    resource.setrlimit(resource.RLIMIT_STACK, (1000000, 1000000))

def set_compiler_limits():
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_DATA, (100000000, 100000000))
    resource.setrlimit(resource.RLIMIT_STACK, (1000000, 1000000))


class Process: # pylint: disable=too-many-instance-attributes
    """A websocket session"""
    def __init__(self, websocket, login, course):
        self.websocket = websocket
        self.conid = str(id(websocket))
        self.process = None
        self.allowed = None
        self.tasks = ()
        self.wait_input = False
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
        self.log("START")

    def log(self, more):
        """Log action to COURSE/login/compile_server.log"""
        with open(self.log_file, "a") as file:
            file.write(repr((int(time.time()), self.conid, more)) + '\n')

    def course_running(self):
        """Check if the course is running for the user"""
        return self.course.running(self.login)

    def cleanup(self, erase_executable=False):
        """Close connection"""
        print("cleanup")
        if erase_executable:
            try:
                os.unlink(self.exec_file)
            except FileNotFoundError:
                pass
        if self.process:
            for task in self.tasks:
                task.cancel()
            self.tasks = []
            try:
                self.process.kill()
            except ProcessLookupError:
                pass
            self.process = None
    def send_input(self, data):
        """Send the data to the running process standard input"""
        self.log(("INPUT", data))
        self.process.stdin.write(data.encode('utf-8') + b'\n')
        self.wait_input = False

    async def timeout(self):
        """May ask for input"""
        # pylint: disable=cell-var-from-loop
        self.wait_input = False
        while True:
            await asyncio.sleep(0.5)
            if self.wait_input:
                continue
            print("TIMEOUT", self.process)
            if not self.process:
                return
            await self.websocket.send(json.dumps(['input', '']))
            self.wait_input = True
    async def runner(self):
        """Pass the process output to the socket"""
        size = 0
        async for line in self.process.stdout:
            await self.websocket.send(json.dumps(['executor', line.decode("utf-8")]))
            size += len(line)
            if size > 10000: # Maximum allowed output
                self.process.kill()
                break
        if self.process:
            await self.websocket.send(json.dumps(
                ['return', "\nCode de fin d'exécution = " + str(await self.process.wait())]))
            self.cleanup()
    async def compile(self, data):
        """Compile"""
        _course, _question, compiler, compile_options, ld_options, allowed, source = data
        self.log(("COMPILE", data))
        self.cleanup(erase_executable=True)
        with open(self.source_file, "w") as file:
            file.write(source)
        stderr = ''
        if compiler not in ('gcc', 'g++'):
            stderr += f'Compilateur non autorisé : «{compiler}»\n'
        for option in compile_options:
            if option not in ('-Wall', '-pedantic', '-pthread'):
                stderr += f'Option de compilation non autorisée : «{option}»\n'
        for option in ld_options:
            if option not in ('-lm',):
                stderr += f"Option d'édition des liens non autorisée : «{option}»\n"
        for option in allowed:
            if option not in ('brk',):
                stderr += f"Appel système non autorisé : «{option}»\n"
        if not stderr:
            self.allowed = ':'.join(["fstat", "newfstatat", "write", "read",
                                     "lseek", "futex", "exit_group"] + allowed)
            self.process = await asyncio.create_subprocess_exec(
                compiler, *compile_options, self.source_file, *ld_options, '-o', self.exec_file,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=set_compiler_limits,
                )
            stderr = await self.process.stderr.read()
            if not stderr:
                stderr = "Bravo, il n'y a aucune erreur"
            else:
                stderr = stderr.decode('utf-8')
        await self.websocket.send(json.dumps(['compiler', stderr]))
        os.unlink(self.source_file)
    async def run(self):
        """Launch process"""
        if not os.path.exists(self.exec_file):
            self.log("RUN nothing")
            await self.websocket.send(json.dumps(['return', "Rien à exécuter"]))
            return
        self.log("RUN")
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

async def echo(websocket, path): # pylint: disable=too-many-branches
    """Analyse the requests from one websocket connection"""
    print(path, flush=True)

    _, ticket, course = path.split('/')
    if not os.path.exists('TICKETS/' + ticket):
        return

    session = await utilities.Session.get(websocket, ticket)
    login = session.login

    process = Process(websocket, login, course)
    PROCESSES.append(process)
    try:
        async for message in websocket:
            print(message, flush=True)
            action, data = json.loads(message)
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
            elif action == 'kill':
                process.log("KILL")
                process.cleanup()
            elif action == 'input':
                process.send_input(data)
            elif action == 'run':
                await process.run()
            else:
                process.log(("BUG", action, data))
                await websocket.send(json.dumps(['compiler', 'bug']))
            print("ACTION DONE")
    finally:
        process.log("STOP")
        process.cleanup(erase_executable=True)
        PROCESSES.remove(process)

async def main():
    """Answer compilation requests"""
    async with websockets.serve(echo, utilities.C5_IP, utilities.C5_SOCK, ssl=CERT):
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
