"""Racket compiler"""

import asyncio
import json
import websockets
from compilers import Compiler
import runner

NR_MAX_RACKET = 16 # The best is one per CPU core/thread
RACKETS = []
def get_free_runner():
    for racket_runner in RACKETS:
        if racket_runner.racket_free:
            return racket_runner
class Racket(Compiler):
    """Racket compiler"""
    name = 'racket'
    kill_if_too_much_data_is_sent = False
    # def before_compile(self, _session):
    #     """XXX Normaly cleanup old file before compile. Why not here ???"""
    #     return # Why not destroy files?
    async def run(self, session):
        """Evaluate a racket program"""
        session.log(('RACKET', len(RACKETS), session.runner))
        while session.runner:
            await asyncio.sleep(0.1)
        session.runner = get_free_runner()
        if not session.runner:
            if len(RACKETS) < NR_MAX_RACKET:
                session.log(('RACKET LAUNCH', len(RACKETS)))
                process = await asyncio.create_subprocess_exec(
                    '/usr/bin/racket', "compile_racket.rkt",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    close_fds=True,
                    env={'LC_ALL': 'C.utf8'},
                    )
                # This runner never stops
                session.runner = runner.Runner(session, process)
                RACKETS.append(session.runner)
            while not session.runner:
                await asyncio.sleep(0.2)
                session.runner = get_free_runner()

        session.runner.session = session
        session.runner.racket_free = False
        session.runner.process.stdin.write(session.source_file.encode('utf-8') + b'\n')
    def cancel_tasks(self, _session):
        """Do not cancel runner, it must stay because it is a pool"""
        return
    async def need_to_read_more(self, the_runner):
        """Wait the end of the racket output"""
        if the_runner.line == b'\001' or b'\001' not in the_runner.line:
            the_runner.keep = the_runner.line
            return True
        if b'\001\002RACKETFini !\001' in the_runner.line:
            if the_runner.session:
                the_runner.session.runner = None
            try:
                if the_runner.session:
                    await the_runner.session.websocket.send(json.dumps(
                        ['executor', the_runner.line.decode("utf-8", "replace")]))
                if the_runner.session:
                    await the_runner.session.websocket.send(json.dumps(['return', "\n"]))
            except websockets.exceptions.ConnectionClosed:
                pass
            the_runner.racket_free = True
            the_runner.log('RACKET DONE')
            the_runner.session = None
            return True
        return False
    def server_exit(self):
        """Cleanup pool on server exit""" 
        print("Racket pool size:", len(RACKETS))
        while RACKETS:
            RACKETS.pop().stop()
    def status(self, the_runner):
        return the_runner.racket_free
