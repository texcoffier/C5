#!/usr/bin/python3
"""
Compiling and executing server
"""

import json
import asyncio
import os
import time
import resource
import websockets
import utilities

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


class Process:
    """A websocket session"""
    def __init__(self, websocket, login):
        self.websocket = websocket
        self.conid = str(id(websocket))
        self.process = None
        self.tasks = ()
        self.wait_input = False
        self.login = login
        try:
            os.mkdir(f"USERS/{login}")
        except OSError:
            pass
        self.exec_file = f"USERS/{self.login}/{self.conid}"
        self.log_file = f"USERS/{self.login}/log"
        self.log("START")

    def log(self, more):
        with open(self.log_file, "a") as file:
            file.write(repr((int(time.time()), self.conid, more)) + '\n')

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
        async for line in self.process.stdout:
            await self.websocket.send(json.dumps(['executor', line.decode("utf-8")]))
        if self.process:
            await self.websocket.send(json.dumps(
                ['return', "Code de fin d'exécution = " + str(await self.process.wait())]))
            self.cleanup()
    async def compile(self, source):
        """Compile"""
        self.log(("COMPILE", source))
        self.cleanup(erase_executable=True)
        source_file = f"USERS/{self.login}/{self.conid}.cpp"
        with open(source_file, "w") as file:
            file.write(source)
        self.process = await asyncio.create_subprocess_exec(
            'g++', '-Wall', source_file, '-o', self.exec_file,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=set_compiler_limits,
            )
        stderr = await self.process.stderr.read()
        if not stderr:
            stderr = "Bravo, il n'y a aucune erreur"
        else:
            stderr = stderr.decode('utf-8')
        await self.websocket.send(json.dumps(['compiler', stderr]))
        os.unlink(source_file)
    async def run(self):
        """Launch process"""
        if not os.path.exists(self.exec_file):
            self.log("RUN nothing")
            await self.websocket.send(json.dumps(['return', "Rien à exécuter"]))
            return
        self.log("RUN")
        self.process = await asyncio.create_subprocess_exec(
            f"USERS/{self.login}/{self.conid}",
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            # stderr=subprocess.PIPE,
            env={'LD_PRELOAD': 'sandbox/libsandbox.so',
                 'SECCOMP_SYSCALL_ALLOW': "fstat:write:read:lseek:exit_group" # brk
                },
            close_fds=True,
            preexec_fn=set_limits,
            )
        self.tasks = [
            asyncio.ensure_future(self.timeout()),
            asyncio.ensure_future(self.runner())
        ]

async def echo(websocket, path):
    """Analyse the requests from one websocket connection"""
    print(path)
    ticket = f'TICKETS/{path[1:]}'
    if not os.path.exists(ticket):
        return
    with open(ticket, 'r') as file:
        ip, browser, login = eval(file.read())

    client_ip = websocket.request_headers.get('x-forwarded-for', '')
    if client_ip:
        client_ip = client_ip.split(",")[0]
    else:
        client_ip, _port = websocket.remote_address
    assert ip == client_ip

    process = Process(websocket, login)
    try:
        async for message in websocket:
            action, data = json.loads(message)
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

async def main():
    """Answer compilation requests"""
    async with websockets.serve(echo, utilities.local_ip(), utilities.C5_SOCK, ssl=CERT):
        print("compile_server running", flush=True)
        await asyncio.Future()  # run forever

CERT = utilities.get_certificate()
if CERT:
    asyncio.run(main())

print("""
======================================================
The remote compiling works only on secure connection.
To create the certificate, use one of the two commands:

    * ./utilities.py SSL-SS
    * ./utilities.py SSL-LE
======================================================
""")
