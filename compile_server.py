#!/usr/bin/python3
"""
Compiling and executing server

To detect that a process is reading its standard input :
   * \r is sent to its standard input
   * The \r is not taken into account by 'cin >> char'
   * FIONREAD allow to check if the process readed the \r
     and so need an INPUT to be displayed.

"""

from typing import Union, Tuple
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
import gc
import collections
import websockets
import utilities
import compiler_gcc    # pylint: disable=unused-import
import compiler_racket # pylint: disable=unused-import
import compiler_prolog # pylint: disable=unused-import
import compiler_coqc   # pylint: disable=unused-import
from compilers import COMPILERS

MIN_TIME_BETWEEN_CONNECT = 0.2 # Racket start time
PROCESSES = []
UID_MIN = int(utilities.C5_COMPILE_UID)
FREE_USERS = list(range(UID_MIN, UID_MIN+1000))

resource.setrlimit(resource.RLIMIT_NOFILE, (10000, 10000))

class Process: # pylint: disable=too-many-instance-attributes
    """A websocket session"""
    cmp = runner = compiler = None
    filetree_in = filetree_out = None
    max_time = max_data = None
    compile_options = ld_options = allowed = source = None
    def __init__(self, websocket, login:str, course:str,
                 uid:int) -> None:
        self.websocket = websocket
        self.conid = str(id(websocket))
        self.allowed = ''
        self.login = login
        self.uid = uid
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

    def log(self, more:Union[str,Tuple]) -> None:
        """Log"""
        if self.feedback:
            return
        print(f"{time.strftime('%Y%m%d%H%M%S')} {self.conid} {more}", flush=True)

    def course_running(self) -> bool:
        """Check if the course is running for the user"""
        return self.course.running(self.login) or self.feedback

    async def compile(self, data:Tuple) -> None:
        """Compile"""
        (_course, _question, self.compiler, self.compile_options,
         self.ld_options, self.allowed, source) = data
        if not self.cmp:
            self.cmp = COMPILERS[self.compiler]
        self.log(("COMPILE", data[:6]))
        self.source = self.cmp.patch_source(source)
        with open(self.source_file, "w", encoding="utf-8") as file:
            file.write(self.source)
        await self.cmp.compile(self)
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
        await self.cmp.run(self)

async def bad_session(websocket) -> None:
    """Tail the browser that the session is bad"""
    await websocket.send(json.dumps(['stop', 'Session expired']))
    await asyncio.sleep(10)

OBJECTS = {}

def search_leak():
    """Uncomment the call to this function to search leak on session close"""
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

async def echo(websocket) -> None: # pylint: disable=too-many-branches,too-many-statements
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

    session = await utilities.Session.get(websocket, ticket,
        allow_ip_change='load_testing' in sys.argv)
    if not session:
        await bad_session(websocket)
        return

    login = session.login
    course = urllib.parse.unquote(course)

    process = Process(websocket, login, course, FREE_USERS.pop())
    PROCESSES.append(process)
    try:
        process.log(("START", ticket, login, course, process.uid))
        async for message in websocket:
            action, data = json.loads(message)
            if action != 'input': # To many logs (Grapic)
                process.log(('ACTION', action))
            if (not session.is_admin()
                    and not process.course_running()
                    and not session.is_grader(process.course)):
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
                if process.runner:
                    process.runner.stop()
                    process.runner = None
            elif action == 'input':
                if process.runner:
                    if data == '\000KILL':
                        process.runner.stop()
                        process.runner = None
                    else:
                        process.runner.send_input(data)
            elif action == 'run':
                await process.run(data)
            else:
                process.log(("BUG", action, data))
                await websocket.send(json.dumps(['compiler', 'bug']))
    except (asyncio.exceptions.CancelledError, websockets.exceptions.ConnectionClosed):
        pass
    except: # pylint: disable=bare-except
        process.log(("EXCEPTION", traceback.format_exc()))
    finally:
        process.log(("STOP", len(PROCESSES), len(FREE_USERS)))
        if process.cmp:
            process.cmp.cancel_tasks(process)
            process.cmp.erase_files(process)
        PROCESSES.remove(process)
        FREE_USERS.append(process.uid)
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
    print("STOP SERVER: kill killer")
    KILLER.kill()
    print("STOP SERVER: Erase files")
    for process in PROCESSES:
        if process.cmp:
            process.cmp.erase_files(process)
    print("STOP SERVER: cleanup compilers")
    for cmp in COMPILERS.values():
        cmp.server_exit()
    print("STOP SERVER: bye bye")

KILLER = subprocess.Popen("./killer") # pylint: disable=consider-using-with
atexit.register(clean)
asyncio.run(main())
