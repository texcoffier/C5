"""C/C++ compiler"""

import resource
import os
import asyncio
import json
import shutil
import pathlib
from compilers import Compiler
import runner


ALWAYS_ALLOWED = {  # Allowed system call for cargo project
                "execve", "brk", "mmap", "access", "openat", "fstat", "close", "read", "pread64",
                "arch_prctl", "set_tid_address", "set_robust_list", "rseq", "mprotect", "prlimit64",
                "getrandom", "munmap", "poll", "rt_sigaction", "lseek", "sched_getaffinity", "sigaltstack",
                "gettid", "write", "exit_group", "newfstatat"
                }


def set_compiler_limits() -> None:
    """Do not allow big processes"""
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_DATA, (200*1024*1024, 200*1024*1024))

# File tree of a cargo project
# - name_projet
#     - src
#         - main.rs
#         - ....rs
#     - target
#         - debug
#             - ...
#     - Cargo.lock
#     - Cargo.toml

# Cargo commands
# cargo build             => compile the project
# ./target/debug/name.exe => run the executable
# cargo run               => compile and run then project
# cargo check             => compile without generating the object code

class Cargo(Compiler):
    """Rust compiler via cargo"""
    name = 'cargo'
    source_file = 'source.rs'

    async def compile(self, session):
        """Compile with cargo — crée la structure projet puis compile"""
        shutil.rmtree(session.home, ignore_errors=True)
        session.log(('COMPILE', session))
        project_dir = pathlib.Path(session.home)
        project_name = project_dir.name
        project_path = project_dir.parent / project_name

        process = await asyncio.create_subprocess_exec(
            'cargo', 'new', '--bin', project_name,
            cwd=project_dir.parent
        )

        await process.wait()

        if not (project_path / "src").exists():
            raise RuntimeError("Cargo project creation failed")

        # Rename the project using lowercase to avoid the snake_case warning (user warning/error).
        cargo_toml = project_path / "Cargo.toml"
        content = cargo_toml.read_text()
        content = content.replace(f'name = "{project_name}"', 'name = "home"')
        cargo_toml.write_text(content)

        # replace main.rs with the code in source_file
        src_file = pathlib.Path(session.dir) / self.source_file
        dst_dir = project_path / "src"
        dst_dir.mkdir(parents=True, exist_ok=True)
        os.rename(src_file, dst_dir / "main.rs")

        session.allowed_str = ':'.join(list(ALWAYS_ALLOWED) + session.allowed)

        process = await asyncio.create_subprocess_exec(
            'cargo', 'build', '--quiet',
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=set_compiler_limits,
            close_fds=True,
            cwd=session.home,
            env = {
                'CARGO_NET_OFFLINE': 'true',
                'PATH': '/usr/bin:/bin',
                'HOME': session.home,
            }
        )

        stderr_bytes = await process.stderr.read()
        await process.wait()

        project_name = pathlib.Path(session.home).name
        session.binary_path = pathlib.Path(session.home) / "target" / "debug" / "home"

        if stderr_bytes:
            stderr = stderr_bytes.decode('utf-8')
        else:
            stderr = "Bravo, il n'y a aucune erreur"

        await session.websocket.send(json.dumps(['compiler', stderr]))
        session.log(("ERRORS", stderr.count('error'), stderr.count('warning')))

    async def run(self, session):
        """Execute the compiled file using the launcher sandbox."""
        session.log(('RUN', session, session.runner))
        await session.cancel_tasks()
        if not session.binary_path.exists():
            session.log("RUN nothing")
            await session.websocket.send(json.dumps(['return', "Rien à exécuter"]))
            return
        if not session.allowed_str:
            session.log("RUNNING not allowed")
            return


        session.log(
            f'./launcher {session.allowed_str} {session.uid} '
            f'{session.home} {session.max_time} {session.binary_path}'
        )

        # Tests
        print("DEBUG launcher args:")
        print(f"  allowed_str={session.allowed_str}")
        print(f"  uid={session.uid}")
        print(f"  home={session.home}")
        print(f"  max_time={session.max_time}")
        print(f"  binary={session.binary_path}", flush=True)

        # Same as GCC
        pathlib.Path(session.home).mkdir(exist_ok=True)
        for filename, content in session.filetree_in:
            filename = pathlib.Path(f"{session.home}/{filename}")
            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_text(content, encoding='utf8')
        last_allowed = session.allowed_str.rsplit(':')[-1]

        process = await asyncio.create_subprocess_exec(
            "./launcher",
            session.allowed_str,
            str(session.uid),
            session.home,
            str(session.max_time),
            "target/debug/home",
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            close_fds=True,
        )

        session.runner = runner.Runner(session, process,
            canary=f' {last_allowed} to the process seccomp filter (allow)\n'.encode('ascii'),
            stdin=process.stdin)
