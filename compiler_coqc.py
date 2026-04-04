"""CoqC compiler"""

import os
import resource
import asyncio
from compilers import Compiler

def set_coq_limits() -> None:
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_DATA, (600*1024*1024, 600*1024*1024))

class CoqC(Compiler):
    """CocC compiler"""
    name = 'coqc'
    source_file = 'source.v'
    async def run(self, session):
        """Run a coqc program"""
        # Should use a runner in order to read values
        process = await asyncio.create_subprocess_exec(
            'coqc', self.source_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            preexec_fn=set_coq_limits,
            close_fds=True,
            cwd=session.dir
            )
        await self.send_output_browser(session, process)
        await self.report_exit_code(session, process)
