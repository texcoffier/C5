#!/usr/bin/python3
"""
Send many requests to the compile server
"""

import json
import time
import asyncio
import random
import websockets
import utilities

NR_STUDENTS = 100
TICKET = 'ST-.........-cas.univ-lyon1.fr'
BROWSER = 'Mozilla/5.0 (X11) Gecko/20100101 Firefox/100.0'
COURSE = 'course_remote'

HEADERS = {'X-Forwarded-For': '127.0.0.1', 'User-Agent': BROWSER}
URL = f"wss://{utilities.C5_WEBSOCKET}/{TICKET}/{COURSE}"
SOURCE = """
using namespace std;
#include <iostream>

int main()
{
    cout << "Bonjour\\n";
}
"""

STATS = []

async def one_student():
    """Emulate one student work"""
    async with websockets.connect(URL, extra_headers=HEADERS) as websocket: # pylint: disable=no-member
        while True:
            await asyncio.sleep(1 + random.random())
            start = time.time()
            await websocket.send(json.dumps(['compile', [COURSE, '0', SOURCE]]))
            answer = await websocket.recv()
            assert 'Bravo' in answer
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
            print(len(STATS), average, (average2 - average ** 2)**0.5)
        else:
            print("No compile done!")
        STATS.clear()

async def main():
    """Create task list"""
    tasks = [one_student() for _ in range(NR_STUDENTS)]
    tasks.append(stats(10))
    await asyncio.gather(*tasks)

asyncio.run(main())
