"""Prolog compiler"""

import traceback
import asyncio
import os
from compilers import Compiler
class Prolog(Compiler):
    """Prolog runner"""
    name = 'prolog'
    def patch_source(self, source):
        return source + '\nccinqquery(Goal) :- forall(Goal, writeln(Goal)).\n'
    async def run(self, session):
        """Run the compiler to get prolog result"""
        # Should use a runner in order to read values
        try:
            os.mkdir(session.home)
        except FileExistsError:
            pass
        # Protection appels système
        args = [
            "./launcher",
            'access:'
            'arch_prctl:'
            'brk:'
            'clock_gettime:'
            'close:'
            'execve:'
            'exit_group:'
            'fcntl:'
            'fstat:'
            'futex:'
            'getcwd:'
            'getdents64:'
            'getpid:'
            'gettid:'
            'ioctl:'
            'lseek:'
            'mmap:'
            'mprotect:'
            'munmap:'
            'newfstatat:'
            'openat:'
            'pread64:'
            'prlimit64:'
            'read:'
            'readlink:'
            'rseq:'
            'rt_sigaction:'
            'rt_sigprocmask:'
            'set_robust_list:'
            'set_tid_address:'
            'sigaltstack:'
            'sysinfo:'
            'write',
            str(session.uid),
            session.home,
            str(session.max_time),
            '/usr/bin/swipl', '--no-tty', '--no-packs', '--quiet', '-t', 'halt',
            ]
        for i in session.source.split('\n%% ')[1:]:
            query = i.split('\n')[0]
            safe = query.replace('"', '\\"')
            args.append('-g')
            args.append(f'writeln("\\n🟩{safe}🟩")')
            args.append('-g')
            args.append(f'consult(user),ccinqquery({query})')
        args.append('-')
        session.log(f"SWI-PROLOG {' '.join(args)}")
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                close_fds=True,
                )
        except: # pylint: disable=bare-except
            for i in traceback.format_exc().split('\n'):
                session.log(("EXCEPTION", i))
        process.stdin.write(session.source.encode('utf-8'))
        process.stdin.close()
        await self.send_output_browser(session, process,
                                       ignore_if_start_by=(b'adding ', b'initializing '))
        await self.report_exit_code(session, process)
