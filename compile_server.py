#!/usr/bin/python3
"""

"""

import json
import asyncio
import ssl
import os
import resource
import websockets

if not os.path.exists("SSL"):
    os.system("""
mkdir SSL
cd SSL
openssl req -x509 -nodes -new -sha256 -days 1024 -newkey rsa:2048 -keyout RootCA.key -out RootCA.pem -subj "/C=US/CN=_______C5_______"
openssl x509 -outform pem -in RootCA.pem -out RootCA.crt
echo '
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = localhost:4200
DNS.2 = 127.0.0.1:4200
DNS.3 = 192.168.0.1:4200
' >domains.ext
openssl req -new -nodes -newkey rsa:2048 -keyout localhost.key -out localhost.csr -subj "/C=US/ST=YourState/L=YourCity/O=Example-Certificates/CN=localhost.local"
openssl x509 -req -sha256 -days 1024 -in localhost.csr -CA RootCA.pem -CAkey RootCA.key -CAcreateserial -extfile domains.ext -out localhost.crt
""")
    print("""
    ********************************************************************
    ********************************************************************
    You must indicate to the browser to add a security exception
    ********************************************************************
    ********************************************************************
    With Firefox:
        * about:preferences
        * Search «certificate»
        * Click on the button «View certificates»
        * Goto on tab «Servers»
        * Click on «Add exception»
        * Add : «https:127.0.0.1:4200»
        * Confirm
    ********************************************************************
""")

CERT = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
CERT.load_cert_chain(certfile="SSL/localhost.crt", keyfile="SSL/localhost.key")

def set_limits():
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_NOFILE, (10, 10))
    resource.setrlimit(resource.RLIMIT_DATA, (1000000, 1000000))
    resource.setrlimit(resource.RLIMIT_STACK, (1000000, 1000000))

class Process:
    def __init__(self, websocket):
        self.websocket = websocket
        self.conid = str(id(websocket))
        self.process = None
        self.tasks = ()
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

async def echo(websocket, _path):
    """Analyse the requests from one websocket connection"""
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
    async with websockets.serve(echo, "127.0.0.1", 4200, ssl=CERT):
        await asyncio.Future()  # run forever

asyncio.run(main())
