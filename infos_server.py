#!/usr/bin/python3
"""
Get informations about users.

Never die
"""

import os
import sys
import json
import time
import traceback
import ldap

C5_LDAP = os.getenv('C5_LDAP')
C5_LDAP_LOGIN = os.getenv('C5_LDAP_LOGIN')
C5_LDAP_PASSWORD = os.getenv('C5_LDAP_PASSWORD')
C5_LDAP_BASE = os.getenv('C5_LDAP_BASE') # As DC=univ-lyon1,DC=fr
C5_LDAP_ENCODING = os.getenv('C5_LDAP_ENCODING') or 'utf-8'

sys.stderr.close()
sys.stderr = open('infos_server.log', 'a')
print(f"\nStart at {time.ctime()}", file=sys.stderr)

while True:
    try:
        LDAP = ldap.ldapobject.ReconnectLDAPObject(
            C5_LDAP,
            retry_max=10,
            retry_delay=5.,
            trace_stack_limit=0)
        LDAP.set_option(ldap.OPT_TIMELIMIT, 10)
        LDAP.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        LDAP.set_option(ldap.OPT_REFERRALS, 0)
        LDAP.set_option(ldap.OPT_X_KEEPALIVE_IDLE, True)
        LDAP.simple_bind_s(C5_LDAP_LOGIN, C5_LDAP_PASSWORD)

        for line in sys.stdin:
            login = line.strip()
            print("About:", login, file=sys.stderr)
            infos = LDAP.search_s(
                C5_LDAP_BASE, ldap.SCOPE_SUBTREE,
                f'(sAMAccountName={login})',
                ('givenName', 'sn'))
            for item in infos:
                print(item, file=sys.stderr)
            print(file=sys.stderr)
            if infos[0][0] is None or 'givenName' not in infos[0][1] or 'sn' not in infos[0][1]:
                sys.stdout.write(json.dumps([login, {'fn': 'fn', 'sn': 'sn'}]) + '\n')
                sys.stdout.flush()
            else:
                infos = infos[0][1]
                infos = {
                    'fn': infos['givenName'][0].decode(C5_LDAP_ENCODING, errors='replace').title(),
                    'sn': infos['sn'][0].decode(C5_LDAP_ENCODING, errors='replace').upper(),
                    }
                sys.stdout.write(json.dumps([login, infos]) + '\n')
                sys.stdout.flush()

        break # stdin closed
    except KeyboardInterrupt:
        break
    except: # pylint: disable=bare-except
        traceback.print_exc()
        time.sleep(1) # Do not overload LDAP server
