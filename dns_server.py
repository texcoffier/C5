#!/usr/bin/python3
"""
Translate IP as hostname.

Never die except if 'stdin' file is no more readable.
"""

import sys
import json
import time
import traceback
import socket

sys.stderr.close()
sys.stderr = open('dns_server.log', 'a', encoding="utf-8") # pylint: disable=consider-using-with
print(f"\nStart at {time.ctime()}", file=sys.stderr)

def analyse():
    """Answer to stdin questions"""
    for line in sys.stdin:
        start = time.time()
        addr = line.strip()
        print("About:", addr, file=sys.stderr)
        if addr.replace('.', '').isdigit():
            name = socket.getnameinfo((addr, 0), 0)[0]
            if not name:
                name = "?"
        else:
            name = addr
        print("Name:", name, file=sys.stderr)
        sys.stdout.write(json.dumps([addr, {'name': name.lower(), 'time': int(start)}]) + '\n')
        sys.stdout.flush()
        print(f"Done in {time.time() - start:6.3f} seconds\n", file=sys.stderr)
    print("stdin closed", file=sys.stderr)
    sys.exit(0) # stdin closed

while True:
    try:
        analyse()
    except KeyboardInterrupt:
        print(f"Stop at {time.ctime()} keyboard interrupt", file=sys.stderr)
        break
    except: # pylint: disable=bare-except
        print("EXCEPTION!", file=sys.stderr)
        traceback.print_exc()
        time.sleep(0.01) # Do not overload LDAP server
