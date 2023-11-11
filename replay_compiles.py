#!/usr/bin/python3
"""
Parameters:
   * YYYYMMDDHHMM start
   * YYYYMMDDHHMM stop
   * Protected Directory Pattern with student logs as 'COMPILE_REMOTE/LIFAPI*'

Full trace is displayed on stderr. So redirect it in a file.

This script generate big log files, they must be cleaned:

    rm -r COMPILE_*/*/none

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

NR_TASKS = 3

TODO = []
START_SECOND = time.mktime(time.strptime(sys.argv[1], '%Y%m%d%H%M'))
STOP_SECOND = time.mktime(time.strptime(sys.argv[2], '%Y%m%d%H%M'))
START_SECOND_STR = f'({START_SECOND},'
STOP_SECOND_STR = f'({STOP_SECOND},'

async def replay_one(file, name):
    """Replay the work of one student"""
    compiler, course_name, login, _  = file.split('/')
    if login == 'none':
        return
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
            if line < START_SECOND_STR:
                return
            if line > STOP_SECOND_STR:
                break
            if not websocket:
                compile_ok = False
                running = False
                src = ''
                websocket = await websockets.connect(
                    f'wss://{utilities.C5_WEBSOCKET}/{ticket}/{course}',
                    ssl=ssl_context)
            line = eval(line) # pylint: disable=eval-used
            try:
                if line[2][0] == 'COMPILE':
                    print(name, end='', flush=True)
                    print(course, login, 'COMPILE', line[2][1][-1], file=sys.stderr)
                    src = line[2][1]
                    await websocket.send(json.dumps(('compile', src)) + '\n')
                    while True:
                        response = json.loads(await websocket.recv())
                        print(course, login, 'COMPILE=', response, file=sys.stderr)
                        if response[0] == 'compiler':
                            if 'error' in response[0]:
                                compile_ok = False
                            else:
                                compile_ok = True
                            break
                elif line[2] == ('ACTION', 'indent'):
                    print(course, login, 'INDENT', file=sys.stderr)
                    await websocket.send(json.dumps(('indent', src)) + '\n')
                    response = json.loads(await websocket.recv())
                    print(course, login, 'INDENT=', response, file=sys.stderr)
                elif line[2] == ('ACTION', 'run'):
                    if compile_ok:
                        print(course, login, 'RUN', file=sys.stderr)
                        await websocket.send(json.dumps(('run', None)) + '\n')
                        response = json.loads(await websocket.recv())
                        #if 'WAITD' in response[1]:
                        #    print(course, login, 'Grapic: giveup replay', file=sys.stderr)
                        #    await websocket.close()
                        #    return
                        print(course, login, 'RUN=', file=sys.stderr)
                elif line[2][0] == 'INPUT':
                    print(course, login, "INPUT", repr(line[2][1]), file=sys.stderr)
                    #if line[2][1].startswith('None\n'):
                    #    print(course, login, 'Grapic: giveup replay', file=sys.stderr)
                    #    await websocket.close()
                    #    return
                    await websocket.send(json.dumps(('input', line[2][1])) + '\n')
                    if compile_ok and running:
                        while True:
                            response = json.loads(await websocket.recv())
                            print(course, login, 'INPUT=', response, file=sys.stderr)
                            if response[0] in ('input', 'return'):
                                break
                        print(course, login, 'INPUT DONE', file=sys.stderr)
                elif line[2] == 'BeforeProcessKill' or line == 'Killed':
                    running = False
                elif line == 'RUNNER_START_REAL':
                    running = True
                else:
                    #print(line)
                    pass
            except websockets.exceptions.ConnectionClosedOK:
                websocket = None
    if websocket:
        await websocket.close()

async def replay_task(name):
    """Replay file in the queue"""
    try:
        while True:
            await replay_one(TODO.pop(), name)
    except IndexError:
        pass

async def replay(directories):
    """
    Assume that the compile server is running.
    Use the 'none' login.
    """
    for file in glob.glob(directories + '/*/compile_server.log'):
        if os.path.getmtime(file) < START_SECOND:
            continue
        TODO.append(file)
    for i in range(NR_TASKS):
        asyncio.ensure_future(replay_task('ABCDEFGHIJKLMNOPQRSTUVWXYZ'[i]))
    print("#students_todo / #tasks / Compiles")
    while TODO:
        print('\n', len(TODO), len(asyncio.all_tasks()), end=' ', flush=True)
        await asyncio.sleep(1)
    sys.exit(0)

def create_ticket():
    """Create a fake ticket"""
    python = f'{sys.version_info.major}.{sys.version_info.minor}'
    browser = f'Python/{python} websockets/{websockets.version.version}'
    if utilities.C5_LOCAL:
        host_ip = utilities.local_ip()
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

asyncio.get_event_loop().run_until_complete(replay(sys.argv[3]))
