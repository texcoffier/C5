#!/usr/bin/python3
"""
Compiling and executing server
"""

import json
import asyncio
import os
import resource
import websockets
import utilities

def set_limits():
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_NOFILE, (10, 10))
    resource.setrlimit(resource.RLIMIT_DATA, (1000000, 1000000))
    resource.setrlimit(resource.RLIMIT_STACK, (1000000, 1000000))

class Process:
    """A websocket session"""
    def __init__(self, websocket):
        self.websocket = websocket
        self.conid = str(id(websocket))
        self.process = None
        self.tasks = ()
        self.wait_input = False
    def cleanup(self, erase_executable=False):
        """Close connection"""
        print("cleanup")
        if erase_executable:
            try:
                os.unlink(self.conid)
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
        self.cleanup(erase_executable=True)
        with open("c.cpp", "w") as file:
            file.write(source)
        self.process = await asyncio.create_subprocess_exec(
            'g++', '-Wall', 'c.cpp', '-o', self.conid,
            stderr=asyncio.subprocess.PIPE)

        stderr = await self.process.stderr.read()
        if not stderr:
            stderr = "Bravo, il n'y a aucune erreur"
        else:
            stderr = stderr.decode('utf-8')
        await self.websocket.send(json.dumps(['compiler', stderr]))
    async def run(self):
        """Launch process"""
        if not os.path.exists(self.conid):
            await self.websocket.send(json.dumps(['return', "Rien à exécuter"]))
            return
        self.process = await asyncio.create_subprocess_exec(
            './' + self.conid,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            # stderr=subprocess.PIPE,
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

    process = Process(websocket)
    try:
        async for message in websocket:
            action, data = json.loads(message)
            print("ACTION", action)
            if action == 'compile':
                await process.compile(data)
            elif action == 'kill':
                process.cleanup()
            elif action == 'input':
                process.send_input(data)
            elif action == 'run':
                await process.run()
            else:
                await websocket.send(json.dumps(['compiler', 'bug']))
            print("ACTION DONE")
    finally:
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
