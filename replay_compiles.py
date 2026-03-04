#!/usr/bin/python3
"""
Currently only working for Racket compilation

Parameters:
   * Protected Directory Pattern with student logs as 'COMPILE_REMOTE/LIFAPI*'

Full trace is displayed on stderr. So redirect it in a file.

This script generate many files, they must be cleaned:

    rm -r COMPILE_*/*/LOGS/none

"""

import glob
import asyncio
import sys
import time
import json
import ssl
import os
import websockets
import requests
import utilities
import common
import c5

TIME_BETWEEN_STUDENTS = 1
TIME_BETWEEN_COMPILE = 40

async def replay_journal(file):
    """Replay the work of one student"""
    print(file)
    compiler, course_name, _, login, _  = file.split('/')
    if login == 'none':
        return
    journal = common.Journal()
    dirname = compiler.split('COMPILE_')[1]
    course = f'{dirname}={course_name}'
    ticket = 'none'
    ssl_context = ssl.SSLContext(
        protocol=ssl.PROTOCOL_SSLv23,
        verify_mode=ssl.CERT_NONE,
        cert_reqs=ssl.CERT_NONE,
        check_hostname=False)
    websocket = None
    with open(file, 'r', encoding="utf-8") as stream:
        for line in stream:
            journal.append(line[:-1])
            if not line.startswith('c'):
                continue
            if not websocket:
                websocket = await websockets.connect(
                    f'wss://{utilities.C5_WEBSOCKET}/{ticket}/{course}',
                    ssl=ssl_context)
            try:
                await websocket.send(json.dumps(('compile', ('c?', 'q?', 'racket', (), (), '', journal.content))) + '\n')
                answer = ''
                while True:
                    response = json.loads(await websocket.recv())
                    # print(course, login, 'COMPILE=', response, file=sys.stderr)
                    if response[0] == 'compiler':
                        break
                    answer += str(response)
                await websocket.send(json.dumps(('run', ((),(),1,1000000))) + '\n')
                while True:
                    response = json.loads(await websocket.recv())
                    if response != ['executor', '\x01\x02RACKETFini !\x01']:
                        print(course, login, 'RUN=', response, file=sys.stderr)
                    if 'RACKETFini !' in response[1]:
                        break
            except websockets.exceptions.ConnectionClosedOK:
                websocket = None
            await asyncio.sleep(TIME_BETWEEN_COMPILE)
    if websocket:
        await websocket.close()

async def replay(directories):
    """
    Assume that the compile server is running.
    Use the 'none' login.
    """
    tasks = []
    for file in glob.glob(directories + '/LOGS/*/journal.log'):
        tasks.append(asyncio.ensure_future(replay_journal(file)))
        await asyncio.sleep(TIME_BETWEEN_STUDENTS)
    await asyncio.wait(tasks)

def create_ticket():
    """Create a fake ticket"""
    python = f'{sys.version_info.major}.{sys.version_info.minor}'
    browser = f'Python/{python} websockets/{websockets.version.version}'
    if utilities.C5_LOCAL:
        host_ip = c5.local_ip()
    else:
        response = requests.get('https://ipinfo.io/')
        host_ip = response.json()['ip']
    now = time.time()
    name = "{'fn': 'fn', 'sn': 'sn'}"
    print(f"IP:{host_ip} Browser:{browser}", utilities.C5_WEBSOCKET)
    with open('TICKETS/none', 'w', encoding="utf-8") as file:
        file.write(f"('{host_ip}', '{browser}', 'none', {now-100}, {name})")
    if not utilities.C5_LOCAL:
        print("Copy ticket to remote host")
        os.system(f'scp TICKETS/none {utilities.C5_LOGIN}@{utilities.C5_URL}:{utilities.C5_DIR}/TICKETS')
        print("Done")

create_ticket()
asyncio.run(replay(sys.argv[1]))
