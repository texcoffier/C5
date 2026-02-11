"""C/C++ compiler"""

import resource
import os
import re
import asyncio
import json
import shutil
import pathlib
from compilers import Compiler
import runner

ALWAYS_ALLOWED = {"fstat", "newfstatat", "write", "read",
                  "lseek", "futex", "exit_group", "exit",
                  "clock_gettime", "openat", "mmap","munmap", "close"}
ALLOWABLE = {'brk', 'access', 'arch_prctl',
             'clone',
             'clone3', 'execve', 'getrandom', 'madvise',
             'mprotect', 'pread64', 'prlimit64',
             'rseq', 'rt_sigaction', 'rt_sigprocmask', 'sched_yield',
             'set_robust_list', 'set_tid_address', 'getpid', 'gettid', 'tgkill',
             'getppid',
             'wait4', # uwed by waipid
             'clock_nanosleep', 'pipe',
             'open'}

def set_compiler_limits() -> None:
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_DATA, (200*1024*1024, 200*1024*1024))

class GCC(Compiler):
    """C/C++ compiler"""
    name = 'gcc'
    async def compile(self, session):
        """Compile with gcc or g++"""        
        session.log(('COMPILE', session))
        stderr = ''
        forbiden = re.findall(r'(^\s*#.*(((/\.|\./|</|"/).*)|\\)$)', session.source, re.MULTILINE)
        if forbiden:
            stderr += f'Ligne interdite : «{forbiden[0][0]}»\n'
        for option in session.compile_options:
            if option not in ('-Wall', '-pedantic', '-pthread', '-std=c++11', '-std=c++20'):
                stderr += f'Option de compilation non autorisée : «{option}»\n'
        for option in session.ld_options:
            if option not in ('-lm',):
                stderr += f"Option d'édition des liens non autorisée : «{option}»\n"
        for option in session.allowed:
            if option not in ALLOWABLE and option not in ALWAYS_ALLOWED:
                stderr += f"Appel système non autorisé : «{option}»\n"
        if stderr:
            session.allowed_str = ''
        else:
            session.allowed_str = ':'.join(list(ALWAYS_ALLOWED) + session.allowed)
            process = await asyncio.create_subprocess_exec(
                session.compiler, *session.compile_options,
                '-I', '../../../..', '-I', '../../MEDIA',
                session.conid + '.cpp', *session.ld_options, '-o', session.conid,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=set_compiler_limits,
                close_fds=True,
                cwd=session.dir
                )
            assert process.stderr
            stderr_bytes = await process.stderr.read()
            if stderr_bytes:
                stderr = stderr_bytes.decode('utf-8').replace(session.conid, 'c5')
            else:
                stderr = "Bravo, il n'y a aucune erreur"
        await session.websocket.send(json.dumps(['compiler', stderr]))
        session.log(("ERRORS", stderr.count(': error:'), stderr.count(': warning:')))
        os.unlink(session.source_file)

    async def run(self, session):
        """Execute the compiled file using the launcher sandbox."""
        session.log(('RUN', session, session.runner))
        self.cancel_tasks(session)
        if not os.path.exists(session.exec_file):
            session.log("RUN nothing")
            await session.websocket.send(json.dumps(['return', "Rien à exécuter"]))
            return
        if not session.allowed_str:
            session.log("RUNNING not allowed")
            return
        session.log(f'./launcher {session.allowed} {session.uid} {session.home} '
                    f'{session.max_time} ../{session.conid}')
        shutil.rmtree(session.home, ignore_errors=True)
        pathlib.Path(session.home).mkdir(exist_ok=True)
        for filename, content in session.filetree_in:
            filename = pathlib.Path(f"{session.home}/{filename}")
            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_text(content, encoding='utf8')
        last_allowed = session.allowed[-1]
        process = await asyncio.create_subprocess_exec(
            "./launcher",
            session.allowed_str,
            str(session.uid),
            session.home,
            str(session.max_time),
            '../' + session.conid,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            close_fds=True,
            )
        session.runner = runner.Runner(session, process,
            canary=f' {last_allowed} to the process seccomp filter (allow)\n'.encode('ascii'),
            stdin=process.stdin)

class GPP(GCC):
    """Only the compiler name change."""
    name = 'g++'
