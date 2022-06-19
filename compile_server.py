#!/usr/bin/python3
"""
Generate certificates

mkdir SSL
cd SSL
openssl req -x509 -nodes -new -sha256 -days 1024 -newkey rsa:2048 -keyout RootCA.key -out RootCA.pem -subj "/C=US/CN=Example-Root-CA"
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

"""

import json
import asyncio
import ssl
import os
import resource
import websockets

CERT = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
CERT.load_cert_chain(certfile="SSL/localhost.crt", keyfile="SSL/localhost.key")

def set_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_NOFILE, (10, 10))
    resource.setrlimit(resource.RLIMIT_DATA, (1000000, 1000000))
    resource.setrlimit(resource.RLIMIT_STACK, (1000000, 1000000))

async def echo(websocket, _path):
    """Analyse the requests from one websocket connection"""
    conid = str(id(websocket))
    def cleanup():
        try:
            os.unlink(conid)
        except FileNotFoundError:
            pass
    try:
        async for message in websocket:
            action, data = json.loads(message)
            if action == 'compile':
                print('compile')
                cleanup()
                with open("c.cpp", "w") as file:
                    file.write(data)
                process = await asyncio.create_subprocess_exec(
                    'g++', '-Wall', 'c.cpp', '-o', conid,
                    stderr=asyncio.subprocess.PIPE)

                stderr = await process.stderr.read()
                if not stderr:
                    stderr = "Bravo, il n'y a aucune erreur"
                else:
                    stderr = stderr.decode('utf-8')
                await websocket.send(json.dumps(['compiler', stderr]))
            elif action == 'run':
                print('run')
                if not os.path.exists(conid):
                    await websocket.send(json.dumps(['return', "Rien à exécuter"]))
                    continue
                process = await asyncio.create_subprocess_exec(
                    './' + conid,
                    stdout=asyncio.subprocess.PIPE,
                    # stderr=subprocess.PIPE,
                    preexec_fn=set_limits,
                    )
                async for line in process.stdout:
                    await websocket.send(json.dumps(['executor', line.decode("utf-8")]))
                await websocket.send(json.dumps(
                    ['return', "Code de fin d'exécution = " + str(await process.wait())]))
            else:
                await websocket.send(json.dumps(['compiler', 'bug']))
    finally:
        cleanup()

async def main():
    """Answer compilation requests"""
    async with websockets.serve(echo, "127.0.0.1", 4200, ssl=CERT):
        await asyncio.Future()  # run forever

asyncio.run(main())
