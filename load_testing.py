#!/usr/bin/python3
"""
Send many requests to the compile server
   . PIPENV/bin/activate ; . 127 ; python3 compile_server.py load_testing # In a window
   . PIPENV/bin/activate ; . 127 ; python3 load_testing.py [racket]       # In another window

"""

import sys
import json
import time
import asyncio
import random
import ssl
import websockets
import utilities

NR_STUDENTS = 100

if 'racket' in sys.argv:
    COURSE = 'REMOTE=racket'
    SOURCE = """
(require racket/math)
(display "Bonjour")
"""
    COMPILER = ['compile', [COURSE, '0', 'racket', ['use_pool'], [], [], SOURCE]]
    def check_exec(answer):
        return 'Bonjour' in answer and 'RACKETFini' in answer
else:
    COURSE = 'REMOTE=test'
    SOURCE = """
    using namespace std;
    #include <iostream>
    int main()
    {
        cout << "Bonjour\\n";
    }
    """
    COMPILER = ['compile', [COURSE, '0', 'g++', [], [], [], SOURCE]]
    def check_exec(answer):
        return 'Bonjour' in answer and 'cution = 0' in answer and 'return' in answer

async def wait(socket, fct):
    answer = await socket.recv()
    for _ in range(10):
        if fct(answer):
            return
        answer += await socket.recv()
    raise ValueError(f"wait {fct} failed with {answer}")

TICKET = 'FAKETICKET'
BROWSER = 'Mozilla/5.0 (X11) Gecko/20100101 Firefox/100.0'
URL = f"wss://{utilities.C5_HOST}:{utilities.C5_SOCK}/{TICKET}/{COURSE}"
HEADERS = {'X-Forwarded-For': '127.0.0.1', 'User-Agent': BROWSER}
CERT = ssl.SSLContext(
        protocol=ssl.PROTOCOL_SSLv23,
        verify_mode=ssl.CERT_NONE,
        cert_reqs=ssl.CERT_NONE,
        check_hostname=False)

with open(f'TICKETS/{TICKET}', 'w', encoding="ascii") as _:
    _.write(repr(('localhost', BROWSER, 'X', time.time(), {'fn': 'FN', 'sn': 'SN'})))

STATS = []

def check_compile(answer):
    return 'Bravo' in answer

async def one_student():
    """Emulate one student work"""
    async with websockets.connect(URL, additional_headers=HEADERS, ssl=CERT) as websocket: # pylint: disable=no-member
        while True:
            await asyncio.sleep(10 + 30*random.random())
            start = time.time()
            await websocket.send(json.dumps(COMPILER))
            await wait(websocket, check_compile)
            await websocket.send(json.dumps(['run', [[], [], 1000, 100000]]))
            await wait(websocket, check_exec)
            # print(f'{name}:{time.time()-start:.1f} ', end='', flush=True)
            STATS.append(time.time() - start)

async def stats(time_span):
    """Display compile time stats every 'time_span' seconds"""
    print(f'Average compile time for the last {time_span} seconds')
    while True:
        await asyncio.sleep(time_span)
        if STATS:
            nbr = len(STATS)
            average = sum(STATS) / nbr
            average2 = sum(i*i for i in STATS) / nbr
            stddev = (average2 - average ** 2)**0.5
            print(f'{len(STATS)} tests, avg: {average}s, stddev: {stddev}')
        else:
            print("No compile done!")
        STATS.clear()

async def main():
    """Create task list"""
    tasks = [one_student() for _ in range(NR_STUDENTS)]
    tasks.append(stats(10))
    await asyncio.gather(*tasks)

asyncio.run(main())
