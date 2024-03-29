#!/usr/bin/python3
"""
Send many requests to the compile server
   . 127 ; ./compile_server.py  # In a window
   . 127 ; ./load_testing.py   # In another window
"""

import json
import time
import asyncio
import random
import ssl
import websockets
import utilities

NR_STUDENTS = 100

TICKET = 'FAKETICKET'
BROWSER = 'Mozilla/5.0 (X11) Gecko/20100101 Firefox/100.0'
COURSE = 'REMOTE=test'
SOURCE = """
using namespace std;
#include <iostream>
int main()
{
    cout << "Bonjour\\n";
}
"""
URL = f"wss://{utilities.C5_HOST}:{utilities.C5_SOCK}/{TICKET}/{COURSE}"
HEADERS = {'X-Forwarded-For': '127.0.0.1', 'User-Agent': BROWSER}

with open(f'TICKETS/{TICKET}', 'w', encoding="ascii") as _:
    _.write(repr(('localhost', BROWSER, 'X', time.time(), {'fn': 'FN', 'sn': 'SN'})))

STATS = []

async def one_student():
    """Emulate one student work"""
    async with websockets.connect(URL, extra_headers=HEADERS, ssl=ssl.SSLContext()) as websocket: # pylint: disable=no-member
        while True:
            await asyncio.sleep(1 + 10*random.random())
            start = time.time()
            await websocket.send(json.dumps(
                ['compile', [COURSE, '0', 'g++', [], [], [], SOURCE]]))
            answer = await websocket.recv()
            assert 'Bravo' in answer # Compilation successful
            await websocket.send(json.dumps(['run', '']))
            answer = await websocket.recv()
            assert 'Bonjour' in answer # Execution output is fine
            answer = await websocket.recv()
            if 'cution = 0' not in answer:
                answer += await websocket.recv()
            assert 'return' in answer and 'cution = 0' in answer # Return value is fine
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
