#!/usr/bin/python3
"""
Translate IP as hostname.

Never die
"""

import sys
import json
import time
import traceback
import socket

sys.stderr.close()
sys.stderr = open('dns_server.log', 'a', encoding="utf-8") # pylint: disable=consider-using-with
print(f"\nStart at {time.ctime()}", file=sys.stderr)

while True:
    try:
        for line in sys.stdin:
            start = time.time()
            ip = line.strip()
            print("About:", ip, file=sys.stderr)
            name = socket.getnameinfo((ip, 0), 0)[0]
            if not name:
                name = "?"
            print("Name:", name, file=sys.stderr)
            sys.stdout.write(json.dumps([ip, {'name': name.lower()}]) + '\n')
            sys.stdout.flush()
            print(f"Done in {time.time() - start:6.3f} seconds\n", file=sys.stderr)
        break # stdin closed
    except KeyboardInterrupt:
        break
    except: # pylint: disable=bare-except
        traceback.print_exc()
        time.sleep(0.01) # Do not overload LDAP server
