#!/usr/bin/python3

"""
Clear garbage from regression tests
"""

import os
import glob
import shutil

def cleanup_c5():
    """Cleanup c5.cf"""
    print('Cleanup c5.cf')
    with open('c5.cf', 'r+', encoding='utf-8') as file:
        pos = 0
        line = 'start'
        while line:
            line = file.readline()
            if 'Anon_' in line:
                file.truncate(pos)
                break
            pos = file.tell()

def remove_tickets():
    """Remove tickets"""
    print('Remove tickets: ', end='')
    for filename in glob.glob('TICKETS/[1-9]*[0-9]'):
        print('*', end='')
        os.unlink(filename)
    print()

def remove_log_dirs():
    """Remove log dirs"""
    print('Remove log dirs: ', end='')
    for dirname in glob.glob('COMPILE_*/*/LOGS/Anon_*'):
        print('*', end='')
        shutil.rmtree(dirname)
    print()

def cleanup_session_config():
    """Cleanup session configs"""
    print('Clear session configs: ', end='')
    for cfname in glob.glob('COMPILE_*/*/session.cf'):
        with open(cfname, 'r+', encoding='utf-8') as file:
            pos = 0
            line = 'start'
            while line:
                line = file.readline()
                if 'Anon_' in line or line.startswith("('proctors', 'REGTESTS"):
                    print(cfname, end=' ')
                    file.truncate(pos)
                    break
                pos = file.tell()
    print()

cleanup_c5()
remove_tickets()
remove_log_dirs()
cleanup_session_config()
