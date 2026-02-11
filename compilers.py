"""Base class for compiler definition.

Only singleton are created.

The state is in the session because on one compilation/execution at the same time
"""

import os
import json
class Compiler:
    """Base class for compiler definition"""
    name = None
    def __init_subclass__(cls):
        """Update the compiler dictionnary"""
        COMPILERS[cls.name] = cls() # Singleton
    def patch_source(self, source):
        """In some case the source must be modified before compiled"""
        return source
    async def compile(self, session):
        """Compile the modifier source"""
        await session.websocket.send(json.dumps(['compiler', "Bravo, il n'y a aucune erreur"]))
    def cancel_tasks(self, session):
        """Stop reading data"""
        if session.runner:
            session.log('CANCEL RUNNER')
            session.runner.stop(session.uid)
            session.runner = None
    def erase_files(self, session):
        """Erase files before the compilation or on session close"""
        try:
            os.unlink(session.exec_file)
        except FileNotFoundError:
            pass
        try:
            os.unlink(session.source_file)
        except FileNotFoundError:
            pass
    async def need_to_read_more(self, _the_runner):
        """Do not send the output to the browser, wait more data"""
        return False
    def server_exit(self):
        """Cleanup on server exit"""
        return
    async def send_output_browser(self, session, process, ignore_if_start_by=()):
        """Verbatim copy of the process output to the browser"""
        if ignore_if_start_by:
            while True:
                line = await process.stdout.readline()
                if not line:
                    return
                if line.startswith(ignore_if_start_by):
                    continue
                break
        else:
            line = await process.stdout.readline()
        while line:
            await session.websocket.send(json.dumps(
                ['executor', line.decode("utf-8", "replace")]))
            line = await process.stdout.readline()

    async def report_exit_code(self, session, process):
        """Send the process return value to the browser"""
        await session.websocket.send(json.dumps(
            ['return', f"\nCode de fin d'exécution = {await process.wait()}"]))

    def status(self, _the_runner):
        """Information to append to the runner dump"""
        return ''

    def kill_if_too_much_data_is_sent(self, _the_runner):
        return True

COMPILERS = {}
